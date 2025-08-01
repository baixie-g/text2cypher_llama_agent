from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.core.workflow import (
    Context,
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)

from cypher_workflows.shared.neo4j_fewshot_manager import Neo4jFewshotManager
from cypher_workflows.shared.local_fewshot_manager import LocalFewshotManager
from cypher_workflows.shared.sse_event import SseEvent
from cypher_workflows.steps.naive_text2cypher import (
    generate_cypher_step,
    get_naive_final_answer_prompt,
)

# 导入日志工具
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.utils import get_llm_logger


class SummarizeEvent(Event):
    question: str
    cypher: str
    context: str


class ExecuteCypherEvent(Event):
    question: str
    cypher: str


class NaiveText2CypherFlow(Workflow):
    def __init__(self, llm, db, embed_model, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.llm = llm
        self.graph_store = db["graph_store"]
        # 优先用Neo4jFewshotManager，否则用本地parquet
        self.neo4j_fewshot_manager = Neo4jFewshotManager()
        if self.neo4j_fewshot_manager.graph_store:
            # 需要传入embed_model
            self.fewshot_retriever = lambda question, db_name: self.neo4j_fewshot_manager.retrieve_fewshots(question, db_name, embed_model)
        else:
            self.local_fewshot_manager = LocalFewshotManager()
            self.fewshot_retriever = lambda question, db_name: self.local_fewshot_manager.get_fewshot_examples(question, db_name)
        self.db_name = db["name"]

    @step
    async def generate_cypher(self, ctx: Context, ev: StartEvent) -> ExecuteCypherEvent:
        question = ev.input

        fewshot_examples = self.fewshot_retriever(question, self.db_name)

        cypher_query = await generate_cypher_step(
            self.llm,
            self.graph_store,
            question,
            fewshot_examples,
        )

        ctx.write_event_to_stream(
            SseEvent(
                label="Cypher generation",
                message=f"Generated Cypher: {cypher_query}",
            )
        )

        # Return for the next step
        return ExecuteCypherEvent(question=question, cypher=cypher_query)

    @step
    async def execute_query(
        self, ctx: Context, ev: ExecuteCypherEvent
    ) -> SummarizeEvent:
        print(f"[DEBUG] 执行 Cypher 查询: {ev.cypher}")
        try:
            database_output = str(self.graph_store.structured_query(ev.cypher)[:100])
            print(f"[DEBUG] 查询结果: {database_output}")
        except Exception as e:
            print(f"[ERROR] 查询 Neo4j 主库失败: {e}")
            database_output = str(e)
        ctx.write_event_to_stream(
            SseEvent(
                message=f"Database output: {database_output}", label="Database output"
            )
        )
        return SummarizeEvent(
            question=ev.question, cypher=ev.cypher, context=database_output
        )

    @step
    async def summarize_answer(self, ctx: Context, ev: SummarizeEvent) -> StopEvent:
        # 获取日志记录器
        logger = get_llm_logger()
        
        naive_final_answer_prompt = get_naive_final_answer_prompt()
        
        # 准备发送给LLM的提示词
        prompt_messages = naive_final_answer_prompt.format_messages(
            context=ev.context, question=ev.question, cypher_query=ev.cypher
        )
        
        # 记录发送给LLM的提示词
        context = {
            "question": ev.question,
            "cypher_query": ev.cypher,
            "database_context": ev.context
        }
        logger.log_prompt("生成最终答案(简单流程)", prompt_messages, context)
        
        # 发送给LLM并获取流式回应
        gen = await self.llm.astream_chat(prompt_messages)
        final_answer = ""
        async for response in gen:
            final_answer += response.delta
            ctx.write_event_to_stream(
                SseEvent(
                    label="Final answer",
                    message=response.delta,
                )
            )
        
        # 记录LLM的完整回应
        logger.log_response("生成最终答案(简单流程)", final_answer, context)

        stop_event = StopEvent(
            result={
                "cypher": ev.cypher,
                "question": ev.question,
                "answer": final_answer,
            }
        )

        # Return the final result
        return stop_event

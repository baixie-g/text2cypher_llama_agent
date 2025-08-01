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

from cypher_workflows.shared.local_fewshot_manager import LocalFewshotManager
from cypher_workflows.shared.sse_event import SseEvent
from cypher_workflows.steps.naive_text2cypher import (
    correct_cypher_step,
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


class CorrectCypherEvent(Event):
    question: str
    cypher: str
    error: str


class NaiveText2CypherRetryFlow(Workflow):
    max_retries = 1

    def __init__(self, llm, db, embed_model, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.llm = llm
        self.graph_store = db["graph_store"]
        self.fewshot_retriever = LocalFewshotManager()
        self.db_name = db["name"]

    @step
    async def generate_cypher(self, ctx: Context, ev: StartEvent) -> ExecuteCypherEvent:
        # Init global vars
        await ctx.set("retries", 0)

        question = ev.input

        fewshot_examples = self.fewshot_retriever.get_fewshot_examples(
            question, self.db_name
        )

        cypher_query = await generate_cypher_step(
            self.llm,
            self.graph_store,
            question,
            fewshot_examples,
        )

        # Return for the next step
        return ExecuteCypherEvent(question=question, cypher=cypher_query)

    @step
    async def execute_query(
        self, ctx: Context, ev: ExecuteCypherEvent
    ) -> SummarizeEvent | CorrectCypherEvent:
        # Get global var
        retries = await ctx.get("retries")

        ctx.write_event_to_stream(
            SseEvent(message=f"Executing Cypher: {ev.cypher}", label="Cypher Execution")
        )

        try:
            # Hard limit to 100 records
            database_output = str(self.graph_store.structured_query(ev.cypher)[:100])
        except Exception as e:
            database_output = str(e)
            # Retry
            if retries < self.max_retries:
                await ctx.set("retries", retries + 1)
                return CorrectCypherEvent(
                    question=ev.question, cypher=ev.cypher, error=database_output
                )

        ctx.write_event_to_stream(
            SseEvent(
                message=f"Database output: {database_output}", label="Database output"
            )
        )

        return SummarizeEvent(
            question=ev.question, cypher=ev.cypher, context=database_output
        )

    @step
    async def correct_cypher_step(
        self, ctx: Context, ev: CorrectCypherEvent
    ) -> ExecuteCypherEvent:
        results = await correct_cypher_step(
            llm=self.llm,
            graph_store=self.graph_store,
            subquery=ev.question,
            cypher=ev.cypher,
            errors=ev.error,
        )

        return ExecuteCypherEvent(question=ev.question, cypher=results)

    @step
    async def summarize_answer(self, ctx: Context, ev: SummarizeEvent) -> StopEvent:
        # 获取日志记录器
        logger = get_llm_logger()
        
        naive_final_answer_prompt = get_naive_final_answer_prompt()

        # 准备发送给LLM的提示词
        prompt_messages = naive_final_answer_prompt.format_messages(
            context=ev.context,
            question=ev.question,
            cypher_query=ev.cypher,
        )
        
        # 记录发送给LLM的提示词
        context = {
            "question": ev.question,
            "cypher_query": ev.cypher,
            "database_context": ev.context
        }
        logger.log_prompt("生成最终答案(重试流程)", prompt_messages, context)

        # 发送给LLM并获取流式回应
        gen = await self.llm.astream_chat(prompt_messages)

        final_answer = ""
        async for response in gen:
            final_answer += response.delta
            ctx.write_event_to_stream(
                SseEvent(message=response.delta, label="Final answer")
            )
        
        # 记录LLM的完整回应
        logger.log_response("生成最终答案(重试流程)", final_answer, context)

        stop_event = StopEvent(
            result={
                "cypher": ev.cypher,
                "question": ev.question,
                "answer": final_answer,
            }
        )

        # Return the final result
        return stop_event

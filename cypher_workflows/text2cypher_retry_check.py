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
from cypher_workflows.shared.neo4j_fewshot_manager import Neo4jFewshotManager
from cypher_workflows.shared.sse_event import SseEvent
from cypher_workflows.shared.utils import check_ok
from cypher_workflows.steps.naive_text2cypher import (
    correct_cypher_step,
    evaluate_database_output_step,
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
    evaluation: str


class ExecuteCypherEvent(Event):
    question: str
    cypher: str


class CorrectCypherEvent(Event):
    question: str
    cypher: str
    error: str


class EvaluateEvent(Event):
    question: str
    cypher: str
    context: str


class NaiveText2CypherRetryCheckFlow(Workflow):
    max_retries = 2

    def __init__(self, llm, db, embed_model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = llm
        self.graph_store = db["graph_store"]
        self.embed_model = embed_model
        self.db_name = db["name"]

        # Fewshot graph store allows for self learning loop by storing new examples
        self.fewshot_manager = Neo4jFewshotManager()
        if self.fewshot_manager.graph_store:
            self.fewshot_retriever = self.fewshot_manager.retrieve_fewshots
        else:
            # self.fewshot_retriever = LocalFewshotManager().retrieve_fewshot
            # Create a wrapper to match the interface of retrieve_fewshots
            local_manager = LocalFewshotManager()
            self.fewshot_retriever = lambda question, database, embed_model: local_manager.get_fewshot_examples(question, database)

    @step
    async def generate_cypher(self, ctx: Context, ev: StartEvent) -> ExecuteCypherEvent:
        # 获取日志记录器
        logger = get_llm_logger()
        
        # 记录步骤开始
        logger.log_workflow_step("步骤开始", "开始生成Cypher查询", {"question": ev.input})
        
        # Init global vars
        await ctx.set("retries", 0)

        question = ev.input

        fewshot_examples = self.fewshot_retriever(
            question, self.db_name, self.embed_model
        )

        cypher_query = await generate_cypher_step(
            llm=self.llm,
            graph_store=self.graph_store,
            subquery=question,
            fewshot_examples=fewshot_examples,
        )
        
        # 记录步骤完成
        logger.log_workflow_step("步骤完成", "Cypher查询生成完成", {"cypher": cypher_query})
        
        # Return for the next step
        return ExecuteCypherEvent(question=question, cypher=cypher_query)

    @step
    async def execute_query(
        self, ctx: Context, ev: ExecuteCypherEvent
    ) -> EvaluateEvent | CorrectCypherEvent:
        # 获取日志记录器
        logger = get_llm_logger()
        
        # 记录步骤开始
        logger.log_workflow_step("步骤开始", "开始执行Cypher查询", {"cypher": ev.cypher})
        
        # Get global var
        retries = await ctx.get("retries")

        ctx.write_event_to_stream(
            SseEvent(message=f"Executing Cypher: {ev.cypher}", label="Cypher execution")
        )
        try:
            print(f"[INFO] 即将查询数据库: {self.db_name}")
            # Hard limit to 100 records
            database_output = str(self.graph_store.structured_query(ev.cypher)[:100])
            logger.log_workflow_step("步骤完成", "Cypher查询执行成功", {"output_length": len(database_output)})
        except Exception as e:
            database_output = str(e)
            logger.log_workflow_step("步骤错误", "Cypher查询执行失败", {"error": database_output})
            ctx.write_event_to_stream(
                SseEvent(
                    message=f"Cypher Execution error: {database_output}",
                    label="Cypher execution error",
                )
            )
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
        return EvaluateEvent(
            question=ev.question, cypher=ev.cypher, context=database_output
        )

    @step
    async def evaluate_context(
        self, ctx: Context, ev: EvaluateEvent
    ) -> SummarizeEvent | CorrectCypherEvent:
        # 获取日志记录器
        logger = get_llm_logger()
        
        # 记录步骤开始
        logger.log_workflow_step("步骤开始", "开始评估数据库输出", {"context_length": len(ev.context)})
        
        # Get global var
        retries = await ctx.get("retries")
        evaluation = await evaluate_database_output_step(
            self.llm, ev.question, ev.cypher, ev.context
        )
        
        # 记录评估结果
        logger.log_workflow_step("步骤完成", "数据库输出评估完成", {"evaluation": evaluation})
        
        if retries < self.max_retries and not evaluation == "Ok":
            await ctx.set("retries", retries + 1)
            return CorrectCypherEvent(
                question=ev.question, cypher=ev.cypher, error=evaluation
            )
        return SummarizeEvent(
            question=ev.question,
            cypher=ev.cypher,
            context=ev.context,
            evaluation=evaluation,
        )

    @step
    async def correct_cypher_step(
        self, ctx: Context, ev: CorrectCypherEvent
    ) -> ExecuteCypherEvent:
        # 获取日志记录器
        logger = get_llm_logger()
        
        # 记录步骤开始
        logger.log_workflow_step("步骤开始", "开始修正Cypher查询", {"error": ev.error})
        
        ctx.write_event_to_stream(
            SseEvent(
                message=f"Error: {ev.error}",
                label="Cypher correction",
            )
        )
        results = await correct_cypher_step(
            self.llm,
            self.graph_store,
            ev.question,
            ev.cypher,
            ev.error,
        )
        
        # 记录步骤完成
        logger.log_workflow_step("步骤完成", "Cypher查询修正完成", {"corrected_cypher": results})
        
        return ExecuteCypherEvent(question=ev.question, cypher=results)

    @step
    async def summarize_answer(self, ctx: Context, ev: SummarizeEvent) -> StopEvent:
        # 获取日志记录器
        logger = get_llm_logger()
        
        retries = await ctx.get("retries")
        
        if retries > 0:
            # If retry was successful:
            if check_ok(ev.evaluation):
                # print(f"Learned new example: {ev.question}, {ev.cypher}")
                self.fewshot_manager.store_fewshot_example(
                    question=ev.question,
                    cypher=ev.cypher,
                    llm=self.llm.model,
                    embed_model=self.embed_model,
                    database=self.db_name,
                )
            else:
                self.fewshot_manager.store_fewshot_example(
                    question=ev.question,
                    cypher=ev.cypher,
                    llm=self.llm.model,
                    embed_model=self.embed_model,
                    database=self.db_name,
                    success=False
                )

        naive_final_answer_prompt = get_naive_final_answer_prompt()
        
        # 准备发送给LLM的提示词
        prompt_messages = naive_final_answer_prompt.format_messages(
            context=ev.context, question=ev.question, cypher_query=ev.cypher
        )
        
        # 记录发送给LLM的提示词
        context = {
            "question": ev.question,
            "cypher_query": ev.cypher,
            "database_context": ev.context,
            "evaluation": ev.evaluation
        }
        logger.log_prompt("生成最终答案", prompt_messages, context)
        
        # 发送给LLM并获取流式回应
        gen = await self.llm.astream_chat(prompt_messages)
        final_answer = ""
        async for response in gen:
            final_answer += response.delta
            ctx.write_event_to_stream(
                SseEvent(message=response.delta, label="Final answer")
            )
        
        # 记录LLM的完整回应
        logger.log_response("生成最终答案", final_answer, context)

        stop_event = StopEvent(
            result={
                "cypher": ev.cypher,
                "question": ev.question,
                "answer": final_answer,
            }
        )

        # Return the final result
        return stop_event

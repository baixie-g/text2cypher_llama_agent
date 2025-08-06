from typing import Optional
from llama_index.core import ChatPromptTemplate

# 导入日志工具
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from app.utils import get_llm_logger
from app.prompt_service import PromptService
from app.prompt_models import PromptType
from app.api_models import PromptConfig

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
EVALUATE_ANSWER_SYSTEM_TEMPLATE = """You are a helpful assistant that must determine if the provided database output (from a Cypher query) is sufficient and relevant to answer a given question. You will receive three inputs:
1. question – The user's question.
2. cypher – The Cypher query used.
3. database_output – The query results.
Your task is:
* Check if the database_output is enough to answer the question meaningfully.
* If sufficient, reply with "Ok".
* If insufficient, explain what's wrong (e.g., missing data, incorrect query structure, irrelevant results) and how to fix the Cypher query (or approach) so it would produce the necessary answer."""

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
EVALUATE_ANSWER_USER_TEMPLATE = """You are given the following information:
Question:
{question}
Cypher Query:
{cypher}
Database Output:
{context}
Analyze whether the provided database output is adequate to answer the question.
* If the context is sufficient, return "Ok".
* Otherwise, describe in detail what the error or shortcoming is, and how to correct the Cypher query (or the approach).
"""


async def evaluate_database_output_step(llm, subquery, cypher, context, prompt_config: Optional[PromptConfig] = None):
    # 获取日志记录器
    logger = get_llm_logger()
    
    # 获取提示词服务
    prompt_service = PromptService()
    
    # 从提示词管理系统获取提示词
    system_prompt, user_prompt = prompt_service.get_workflow_step_prompts(
        system_prompt_type=PromptType.NAIVE_EVALUATE_ANSWER_SYSTEM,
        user_prompt_type=PromptType.NAIVE_EVALUATE_ANSWER_USER,
        prompt_config=prompt_config
    )
    
    # 如果获取失败，抛出异常
    if not system_prompt or not user_prompt:
        raise ValueError("无法从提示词管理系统获取必要的提示词模板")
    
    evaluate_answer_messages = [
        ("system", system_prompt),
        ("user", user_prompt),
    ]

    evaluate_answer_prompt = ChatPromptTemplate.from_messages(evaluate_answer_messages)
    
    # 准备发送给LLM的提示词
    prompt_messages = evaluate_answer_prompt.format_messages(
        question=subquery, cypher=cypher, context=context
    )
    
    # 记录发送给LLM的提示词
    context_info = {
        "question": subquery,
        "cypher": cypher,
        "database_output": context
    }
    logger.log_prompt("评估数据库输出", prompt_messages, context_info)
    
    # 发送给LLM并获取回应
    response = await llm.achat(prompt_messages)
    
    # 记录LLM的完整回应
    logger.log_response("评估数据库输出", response.message.content, context_info)
    
    return response.message.content

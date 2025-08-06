import sys
from typing import Optional
from llama_index.core import ChatPromptTemplate
from cypher_workflows.shared.utils import get_neo4j_schema_str
import os

# 导入日志工具
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from app.utils import get_llm_logger, get_optimized_schema
from app.prompt_service import PromptService
from app.prompt_models import PromptType
from app.api_models import PromptConfig

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
CORRECT_CYPHER_SYSTEM_TEMPLATE = """You are a Cypher expert reviewing a statement written by a junior developer.
You need to correct the Cypher statement based on the provided errors. No pre-amble."
Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"""

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
CORRECT_CYPHER_USER_TEMPLATE = """Check for invalid syntax or semantics and return a corrected Cypher statement.

Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not wrap the response in any backticks or anything else.
Respond with a Cypher statement only!

Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.

The question is:
{question}

The Cypher statement is:
{cypher}

The errors are:
{errors}

Corrected Cypher statement: """


async def correct_cypher_step(llm, graph_store, subquery, cypher, errors, prompt_config: Optional[PromptConfig] = None):
    # 获取日志记录器
    logger = get_llm_logger()
    
    # 使用优化的schema函数
    schema = get_optimized_schema(graph_store, exclude_types=["Actor", "Director"])
    print(f"-> 成功获取优化corrector schema为: {schema}")
    
    # 获取提示词服务
    prompt_service = PromptService()
    
    # 从提示词管理系统获取提示词
    system_prompt, user_prompt = prompt_service.get_workflow_step_prompts(
        system_prompt_type=PromptType.NAIVE_CORRECT_CYPHER_SYSTEM,
        user_prompt_type=PromptType.NAIVE_CORRECT_CYPHER_USER,
        prompt_config=prompt_config
    )
    
    # 如果获取失败，抛出异常
    if not system_prompt or not user_prompt:
        raise ValueError("无法从提示词管理系统获取必要的提示词模板")

    correct_cypher_messages = [
        ("system", system_prompt),
        ("user", user_prompt),
    ]

    correct_cypher_prompt = ChatPromptTemplate.from_messages(correct_cypher_messages)
    
    # 准备发送给LLM的提示词
    prompt_messages = correct_cypher_prompt.format_messages(
        question=subquery, schema=schema, errors=errors, cypher=cypher
    )
    
    # 记录发送给LLM的提示词
    context = {
        "question": subquery,
        "schema": schema,
        "errors": errors,
        "cypher": cypher
    }
    logger.log_prompt("修正Cypher查询", prompt_messages, context)
    
    # 发送给LLM并获取回应
    response = await llm.achat(prompt_messages)
    
    # 记录LLM的完整回应
    logger.log_response("修正Cypher查询", response.message.content, context)
    
    return response.message.content

    # prompt_content = correct_cypher_prompt.format_messages(
    #     question=subquery, schema=schema, errors=errors, cypher=cypher
    # )
    # print("\n===== 最终发送给LLM的Cypher修正提示词 22=====\n")
    # print(prompt_content)
    # sys.exit(0)

    # return ""

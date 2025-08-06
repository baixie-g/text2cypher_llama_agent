from llama_index.core import ChatPromptTemplate
from app.prompt_service import PromptService
from app.prompt_models import PromptType
from app.api_models import PromptConfig
import os

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
GENERATE_SYSTEM_TEMPLATE = """Given an input question, convert it to a Cypher query. No pre-amble.
Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"""

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
GENERATE_USER_TEMPLATE = """You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.
Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!
Here is the schema information
{schema}

Below are a number of examples of questions and their corresponding Cypher queries.

{fewshot_examples}

User input: {question}
Cypher query:"""


async def generate_cypher_step(llm, graph_store, subquery, fewshot_examples, schema):
    # 获取提示词服务
    prompt_service = PromptService()
    
    # 从提示词管理系统获取提示词
    system_prompt, user_prompt = prompt_service.get_workflow_step_prompts(
        system_prompt_type=PromptType.ITERATIVE_GENERATE_CYPHER_SYSTEM,
        user_prompt_type=PromptType.ITERATIVE_GENERATE_CYPHER_USER if "iterative_generate_cypher_user" != "None" else None,
        prompt_config=prompt_config
    )
    
    # 如果获取失败，抛出异常
    if not system_prompt:
        raise ValueError("无法从提示词管理系统获取必要的提示词模板")
    
    msgs = [
        ("system", system_prompt),
        ("user", user_prompt),
    ]
    text2cypher_prompt = ChatPromptTemplate.from_messages(generate_cypher_msgs)
    response = await llm.achat(
        text2cypher_prompt.format_messages(
            question=subquery,
            schema=schema,
            fewshot_examples=fewshot_examples,
        )
    )
    return response.message.content

from llama_index.core import ChatPromptTemplate
from typing import Optional

# 导入日志工具
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from app.prompt_service import PromptService
from app.prompt_models import PromptType
from app.api_models import PromptConfig
from typing import Dict, Any

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
FINAL_ANSWER_SYSTEM_TEMPLATE = """
You are a highly intelligent assistant trained to provide concise and accurate answers.
You will be given a context that has been retrieved from a Neo4j database using a specific Cypher query.
Your task is to analyze the context and answer the user’s question based on the information provided in the context.
If the context lacks sufficient information, inform the user and suggest what additional details are needed.

Focus solely on the context provided from the Neo4j database to form your response.
Avoid making assumptions or using external knowledge unless explicitly stated in the context.
Ensure the final answer is clear, relevant, and directly addresses the user’s question.
If the question is ambiguous, ask clarifying questions to ensure accuracy before proceeding.
"""

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
FINAL_ANSWER_USER_TEMPLATE = """
Based on this context retrieved from a Neo4j database using the following Cypher query:
`{cypher_query}`

The context is:
{context}

Answer the following question:
<question>
{question}
</question>

Please provide your answer based on the context above, explaining your reasoning.
If clarification or additional information is needed, explain why and specify what is required.
"""


def get_naive_final_answer_prompt(prompt_config: Optional[Dict[str, Any]] = None):
    # 获取提示词服务
    prompt_service = PromptService()
    
    # 从提示词管理系统获取提示词
    system_prompt, user_prompt = prompt_service.get_workflow_step_prompts(
        workflow_type="naive_text2cypher",
        step_name="summarize_answer",
        prompt_config=prompt_config
    )
    
    # 如果获取失败，抛出异常
    if not system_prompt or not user_prompt:
        raise ValueError("无法从提示词管理系统获取必要的提示词模板")
    
    final_answer_msgs = [
        ("system", system_prompt),
        ("user", user_prompt),
    ]

    return ChatPromptTemplate.from_messages(final_answer_msgs)

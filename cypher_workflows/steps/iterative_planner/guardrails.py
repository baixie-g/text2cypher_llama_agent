from typing import Literal, Optional

from llama_index.core import ChatPromptTemplate
from app.prompt_service import PromptService
from app.prompt_models import PromptType
from app.api_models import PromptConfig
from pydantic import BaseModel, Field


class Guardrail(BaseModel):
    """Guardrail"""

    decision: Literal["movie", "end"] = Field(
        description="Decision on whether the question is related to movies"
    )


GUARDRAILS_SYSTEM_PROMPT_TEMPLATE = """As an intelligent assistant, your primary objective is to decide whether a given question is related to movies or not.
If the question is related to movies, output "movie". Otherwise, output "end".
To make this decision, assess the content of the question and determine if it refers to any movie, actor, director, film industry,
or related topics. Provide only the specified output: "movie" or "end"."""


async def guardrails_step(llm, question, prompt_config: Optional[PromptConfig] = None):
    # 获取提示词服务
    prompt_service = PromptService()
    
    # 从提示词管理系统获取提示词
    system_prompt, user_prompt = prompt_service.get_workflow_step_prompts(
        system_prompt_type=PromptType.ITERATIVE_GUARDRAILS_SYSTEM,
        user_prompt_type=PromptType.ITERATIVE_GUARDRAILS_USER,
        prompt_config=prompt_config
    )
    
    # 如果获取失败，抛出异常
    if not system_prompt:
        raise ValueError("无法从提示词管理系统获取必要的提示词模板")
    
    # Refine Prompt
    chat_refine_msgs = [
        ("system", system_prompt),
        ("user", "The question is: {question}"),
    ]

    guardrails_template = ChatPromptTemplate.from_messages(chat_refine_msgs)

    guardrails_output = await llm.as_structured_llm(Guardrail).acomplete(
        guardrails_template.format(question=question)
    )
    guardrails_output = guardrails_output.raw.decision

    if guardrails_output == "end":
        context = "The question is not about movies or their case, so I cannot answer this question"
        return {
            "next_event": "generate_final_answer",
            "arguments": {"context": context, "question": question},
        }

    return {"next_event": "generate_plan", "arguments": {}}

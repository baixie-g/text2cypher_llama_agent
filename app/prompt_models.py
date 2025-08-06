from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class PromptType(str, Enum):
    """提示词类型枚举，对应不同的代码位置"""
    # Naive Text2Cypher 工作流
    NAIVE_GENERATE_CYPHER_SYSTEM = "naive_generate_cypher_system"
    NAIVE_GENERATE_CYPHER_USER = "naive_generate_cypher_user"
    NAIVE_CORRECT_CYPHER_SYSTEM = "naive_correct_cypher_system"
    NAIVE_CORRECT_CYPHER_USER = "naive_correct_cypher_user"
    NAIVE_EVALUATE_ANSWER_SYSTEM = "naive_evaluate_answer_system"
    NAIVE_EVALUATE_ANSWER_USER = "naive_evaluate_answer_user"
    NAIVE_SUMMARIZE_ANSWER_SYSTEM = "naive_summarize_answer_system"
    NAIVE_SUMMARIZE_ANSWER_USER = "naive_summarize_answer_user"
    
    # Iterative Planner 工作流
    ITERATIVE_INITIAL_PLAN_SYSTEM = "iterative_initial_plan_system"
    ITERATIVE_GENERATE_CYPHER_SYSTEM = "iterative_generate_cypher_system"
    ITERATIVE_GENERATE_CYPHER_USER = "iterative_generate_cypher_user"
    ITERATIVE_VALIDATE_CYPHER_SYSTEM = "iterative_validate_cypher_system"
    ITERATIVE_VALIDATE_CYPHER_USER = "iterative_validate_cypher_user"
    ITERATIVE_INFORMATION_CHECK_SYSTEM = "iterative_information_check_system"
    ITERATIVE_INFORMATION_CHECK_USER = "iterative_information_check_user"
    ITERATIVE_GUARDRAILS_SYSTEM = "iterative_guardrails_system"
    ITERATIVE_GUARDRAILS_USER = "iterative_guardrails_user"
    ITERATIVE_FINAL_ANSWER_SYSTEM = "iterative_final_answer_system"
    ITERATIVE_FINAL_ANSWER_USER = "iterative_final_answer_user"
    ITERATIVE_CORRECT_CYPHER_SYSTEM = "iterative_correct_cypher_system"
    ITERATIVE_CORRECT_CYPHER_USER = "iterative_correct_cypher_user"


class PromptTemplate(BaseModel):
    """提示词模板数据模型"""
    id: str = Field(..., description="模板唯一标识")
    name: str = Field(..., description="模板名称")
    prompt_type: PromptType = Field(..., description="提示词类型")
    content: str = Field(..., description="提示词内容")
    description: str = Field(..., description="模板描述")
    version: str = Field(default="1.0.0", description="版本号")
    is_default: bool = Field(default=False, description="是否为默认模板")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class PromptConfig(BaseModel):
    """提示词配置模型，用于工作流执行时指定使用的模板"""
    system_template: Optional[str] = Field(None, description="系统提示词模板ID")
    user_template: Optional[str] = Field(None, description="用户提示词模板ID")
    assistant_template: Optional[str] = Field(None, description="助手提示词模板ID")


# API请求响应模型
class PromptTypeInfo(BaseModel):
    """提示词类型信息"""
    type: PromptType = Field(..., description="提示词类型")
    name: str = Field(..., description="类型名称")
    description: str = Field(..., description="类型描述")
    workflow: str = Field(..., description="所属工作流")
    step: str = Field(..., description="所属步骤")


class TemplateListRequest(BaseModel):
    """获取模板列表请求"""
    prompt_type: Optional[PromptType] = Field(None, description="提示词类型过滤")
    is_active: Optional[bool] = Field(None, description="是否激活过滤")
    is_default: Optional[bool] = Field(None, description="是否默认模板过滤")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页大小")
    search: Optional[str] = Field(None, description="搜索关键词")


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    templates: List[PromptTemplate] = Field(..., description="模板列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class CreateTemplateRequest(BaseModel):
    """创建模板请求"""
    name: str = Field(..., description="模板名称")
    prompt_type: PromptType = Field(..., description="提示词类型")
    content: str = Field(..., description="提示词内容")
    description: str = Field(..., description="模板描述")
    is_default: bool = Field(default=False, description="是否为默认模板")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class UpdateTemplateRequest(BaseModel):
    """更新模板请求"""
    name: Optional[str] = Field(None, description="模板名称")
    content: Optional[str] = Field(None, description="提示词内容")
    description: Optional[str] = Field(None, description="模板描述")
    is_default: Optional[bool] = Field(None, description="是否为默认模板")
    is_active: Optional[bool] = Field(None, description="是否激活")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class CopyTemplateRequest(BaseModel):
    """复制模板请求"""
    new_name: str = Field(..., description="新模板名称")
    description: Optional[str] = Field(None, description="新模板描述")


# 提示词类型描述映射
PROMPT_TYPE_DESCRIPTIONS = {
    PromptType.NAIVE_GENERATE_CYPHER_SYSTEM: {
        "name": "Naive生成Cypher系统提示词",
        "description": "用于简单文本转Cypher工作流中生成Cypher查询的系统提示词",
        "workflow": "naive_text2cypher",
        "step": "generate_cypher"
    },
    PromptType.NAIVE_GENERATE_CYPHER_USER: {
        "name": "Naive生成Cypher用户提示词",
        "description": "用于简单文本转Cypher工作流中生成Cypher查询的用户提示词",
        "workflow": "naive_text2cypher",
        "step": "generate_cypher"
    },
    PromptType.NAIVE_CORRECT_CYPHER_SYSTEM: {
        "name": "Naive修正Cypher系统提示词",
        "description": "用于简单文本转Cypher工作流中修正Cypher查询的系统提示词",
        "workflow": "naive_text2cypher",
        "step": "correct_cypher"
    },
    PromptType.NAIVE_CORRECT_CYPHER_USER: {
        "name": "Naive修正Cypher用户提示词",
        "description": "用于简单文本转Cypher工作流中修正Cypher查询的用户提示词",
        "workflow": "naive_text2cypher",
        "step": "correct_cypher"
    },
    PromptType.NAIVE_EVALUATE_ANSWER_SYSTEM: {
        "name": "Naive评估答案系统提示词",
        "description": "用于简单文本转Cypher工作流中评估答案的系统提示词",
        "workflow": "naive_text2cypher",
        "step": "evaluate_answer"
    },
    PromptType.NAIVE_EVALUATE_ANSWER_USER: {
        "name": "Naive评估答案用户提示词",
        "description": "用于简单文本转Cypher工作流中评估答案的用户提示词",
        "workflow": "naive_text2cypher",
        "step": "evaluate_answer"
    },
    PromptType.NAIVE_SUMMARIZE_ANSWER_SYSTEM: {
        "name": "Naive总结答案系统提示词",
        "description": "用于简单文本转Cypher工作流中总结答案的系统提示词",
        "workflow": "naive_text2cypher",
        "step": "summarize_answer"
    },
    PromptType.NAIVE_SUMMARIZE_ANSWER_USER: {
        "name": "Naive总结答案用户提示词",
        "description": "用于简单文本转Cypher工作流中总结答案的用户提示词",
        "workflow": "naive_text2cypher",
        "step": "summarize_answer"
    },
    PromptType.ITERATIVE_INITIAL_PLAN_SYSTEM: {
        "name": "迭代规划初始规划系统提示词",
        "description": "用于迭代规划工作流中初始规划的系统提示词",
        "workflow": "iterative_planner",
        "step": "initial_plan"
    },
    PromptType.ITERATIVE_GENERATE_CYPHER_SYSTEM: {
        "name": "迭代规划生成Cypher系统提示词",
        "description": "用于迭代规划工作流中生成Cypher查询的系统提示词",
        "workflow": "iterative_planner",
        "step": "generate_cypher"
    },
    PromptType.ITERATIVE_GENERATE_CYPHER_USER: {
        "name": "迭代规划生成Cypher用户提示词",
        "description": "用于迭代规划工作流中生成Cypher查询的用户提示词",
        "workflow": "iterative_planner",
        "step": "generate_cypher"
    },
    PromptType.ITERATIVE_VALIDATE_CYPHER_SYSTEM: {
        "name": "迭代规划验证Cypher系统提示词",
        "description": "用于迭代规划工作流中验证Cypher查询的系统提示词",
        "workflow": "iterative_planner",
        "step": "validate_cypher"
    },
    PromptType.ITERATIVE_VALIDATE_CYPHER_USER: {
        "name": "迭代规划验证Cypher用户提示词",
        "description": "用于迭代规划工作流中验证Cypher查询的用户提示词",
        "workflow": "iterative_planner",
        "step": "validate_cypher"
    },
    PromptType.ITERATIVE_INFORMATION_CHECK_SYSTEM: {
        "name": "迭代规划信息检查系统提示词",
        "description": "用于迭代规划工作流中信息检查的系统提示词",
        "workflow": "iterative_planner",
        "step": "information_check"
    },
    PromptType.ITERATIVE_INFORMATION_CHECK_USER: {
        "name": "迭代规划信息检查用户提示词",
        "description": "用于迭代规划工作流中信息检查的用户提示词",
        "workflow": "iterative_planner",
        "step": "information_check"
    },
    PromptType.ITERATIVE_GUARDRAILS_SYSTEM: {
        "name": "迭代规划防护栏系统提示词",
        "description": "用于迭代规划工作流中防护栏的系统提示词",
        "workflow": "iterative_planner",
        "step": "guardrails"
    },
    PromptType.ITERATIVE_GUARDRAILS_USER: {
        "name": "迭代规划防护栏用户提示词",
        "description": "用于迭代规划工作流中防护栏的用户提示词",
        "workflow": "iterative_planner",
        "step": "guardrails"
    },
    PromptType.ITERATIVE_FINAL_ANSWER_SYSTEM: {
        "name": "迭代规划最终答案系统提示词",
        "description": "用于迭代规划工作流中生成最终答案的系统提示词",
        "workflow": "iterative_planner",
        "step": "final_answer"
    },
    PromptType.ITERATIVE_FINAL_ANSWER_USER: {
        "name": "迭代规划最终答案用户提示词",
        "description": "用于迭代规划工作流中生成最终答案的用户提示词",
        "workflow": "iterative_planner",
        "step": "final_answer"
    },
    PromptType.ITERATIVE_CORRECT_CYPHER_SYSTEM: {
        "name": "迭代规划修正Cypher系统提示词",
        "description": "用于迭代规划工作流中修正Cypher查询的系统提示词",
        "workflow": "iterative_planner",
        "step": "correct_cypher"
    },
    PromptType.ITERATIVE_CORRECT_CYPHER_USER: {
        "name": "迭代规划修正Cypher用户提示词",
        "description": "用于迭代规划工作流中修正Cypher查询的用户提示词",
        "workflow": "iterative_planner",
        "step": "correct_cypher"
    }
} 
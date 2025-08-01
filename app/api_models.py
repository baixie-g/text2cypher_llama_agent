from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowType(str, Enum):
    TEXT2CYPHER_WITH_RETRY_AND_CHECK = "text2cypher_with_1_retry_and_output_check"
    NAIVE_TEXT2CYPHER = "naive_text2cypher"
    NAIVE_TEXT2CYPHER_WITH_RETRY = "naive_text2cypher_with_1_retry"


class DatabaseStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class LLMStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


# 基础响应模型
class BaseResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


# 错误响应模型
class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


# 模型信息模型
class LLMInfo(BaseModel):
    name: str = Field(..., description="模型名称")
    status: LLMStatus = Field(..., description="模型状态")
    provider: str = Field(..., description="模型提供商")
    model_type: str = Field(..., description="模型类型")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    temperature: Optional[float] = Field(None, description="温度参数")


# 数据库信息模型
class DatabaseInfo(BaseModel):
    name: str = Field(..., description="数据库名称")
    status: DatabaseStatus = Field(..., description="数据库状态")
    uri: str = Field(..., description="数据库连接URI")
    schema_count: int = Field(..., description="模式数量")
    node_types: List[str] = Field(..., description="节点类型列表")
    relationship_types: List[str] = Field(..., description="关系类型列表")


# 工作流信息模型
class WorkflowInfo(BaseModel):
    name: str = Field(..., description="工作流名称")
    type: WorkflowType = Field(..., description="工作流类型")
    description: str = Field(..., description="工作流描述")
    parameters: Dict[str, Any] = Field(..., description="工作流参数")


# 工作流执行请求模型
class WorkflowExecuteRequest(BaseModel):
    llm_name: str = Field(..., description="要使用的LLM模型名称")
    database_name: str = Field(..., description="要使用的数据库名称")
    workflow_type: WorkflowType = Field(..., description="工作流类型")
    input_text: str = Field(..., description="输入文本")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文信息")
    timeout: Optional[int] = Field(60, description="超时时间（秒）")


# 工作流执行响应模型
class WorkflowEvent(BaseModel):
    event_type: str = Field(..., description="事件类型")
    label: str = Field(..., description="事件标签")
    message: str = Field(..., description="事件消息")
    timestamp: str = Field(..., description="时间戳")


class WorkflowExecuteResponse(BaseModel):
    success: bool = Field(..., description="执行是否成功")
    events: List[WorkflowEvent] = Field(..., description="执行事件列表")
    result: Optional[Any] = Field(None, description="执行结果")
    execution_time: float = Field(..., description="执行时间（秒）")


# 系统状态模型
class SystemStatus(BaseModel):
    service_status: str = Field(..., description="服务状态")
    llm_count: int = Field(..., description="可用LLM数量")
    database_count: int = Field(..., description="可用数据库数量")
    workflow_count: int = Field(..., description="可用工作流数量")
    memory_usage: Dict[str, Any] = Field(..., description="内存使用情况")
    uptime: str = Field(..., description="服务运行时间")


# 健康检查响应
class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="健康状态")
    timestamp: str = Field(..., description="检查时间")
    version: str = Field(..., description="服务版本")
    components: Dict[str, str] = Field(..., description="组件状态")


# 批量执行请求
class BatchWorkflowRequest(BaseModel):
    requests: List[WorkflowExecuteRequest] = Field(..., description="批量请求列表")
    max_concurrent: Optional[int] = Field(5, description="最大并发数")


# 批量执行响应
class BatchWorkflowResponse(BaseModel):
    total_count: int = Field(..., description="总请求数")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    results: List[WorkflowExecuteResponse] = Field(..., description="执行结果列表")


# 配置更新请求
class ConfigUpdateRequest(BaseModel):
    llm_config: Optional[Dict[str, Any]] = Field(None, description="LLM配置")
    database_config: Optional[Dict[str, Any]] = Field(None, description="数据库配置")
    workflow_config: Optional[Dict[str, Any]] = Field(None, description="工作流配置")


# 统计信息模型
class StatisticsInfo(BaseModel):
    total_executions: int = Field(..., description="总执行次数")
    successful_executions: int = Field(..., description="成功执行次数")
    failed_executions: int = Field(..., description="失败执行次数")
    average_execution_time: float = Field(..., description="平均执行时间")
    popular_workflows: List[Dict[str, Any]] = Field(..., description="热门工作流")
    popular_llms: List[Dict[str, Any]] = Field(..., description="热门LLM")
    daily_stats: List[Dict[str, Any]] = Field(..., description="每日统计") 
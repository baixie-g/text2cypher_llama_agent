import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
import psutil

from app.api_models import (
    BaseResponse, ErrorResponse, LLMInfo, DatabaseInfo, WorkflowInfo,
    WorkflowExecuteRequest, WorkflowExecuteResponse, WorkflowEvent,
    SystemStatus, HealthCheckResponse, BatchWorkflowRequest, BatchWorkflowResponse,
    ConfigUpdateRequest, StatisticsInfo, WorkflowType, LLMStatus, DatabaseStatus
)
from app.resource_manager import ResourceManager
from app.settings import WORKFLOW_MAP
from app.workflow_service import WorkflowService
from app.prompt_routes import router as prompt_router

# 创建路由器
router = APIRouter(prefix="/api/v1", tags=["Text2Cypher API"])

# 包含提示词管理路由
router.include_router(prompt_router)

# 全局变量
resource_manager = None
workflow_service = None
start_time = None
execution_stats = {
    "total_executions": 0,
    "successful_executions": 0,
    "failed_executions": 0,
    "execution_times": [],
    "workflow_usage": {},
    "llm_usage": {}
}


def get_resource_manager():
    global resource_manager
    if resource_manager is None:
        resource_manager = ResourceManager()
    return resource_manager
@router.post("/databases/refresh", response_model=BaseResponse)
async def refresh_databases_from_nacos(payload: Dict[str, Any] | None = None):
    """从 Nacos 重新拉取并注册数据库（仅 Neo4j 类型）
    可在请求体中传入可选覆盖字段：server, username, password, bearer_token, namespace, group, data_id, auth_method
    """
    try:
        rm = get_resource_manager()
        before = len(rm.databases)
        rm.load_databases_from_nacos(overrides=payload or {})
        after = len(rm.databases)
        return BaseResponse(success=True, message=f"Refreshed databases from Nacos: {before} -> {after}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh databases failed: {str(e)}")



def get_workflow_service():
    global workflow_service
    if workflow_service is None:
        workflow_service = WorkflowService(get_resource_manager())
    return workflow_service


# 健康检查
@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """健康检查接口"""
    try:
        rm = get_resource_manager()
        components = {
            "llm_service": "healthy" if rm.llms else "unhealthy",
            "database_service": "healthy" if rm.databases else "unhealthy",
            "embedding_service": "healthy" if rm.embed_model else "unhealthy"
        }
        
        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="4.0.0",
            components=components
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# 系统状态
@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    try:
        rm = get_resource_manager()
        memory = psutil.virtual_memory()
        
        global start_time
        if start_time is None:
            start_time = datetime.now()
        
        uptime = datetime.now() - start_time
        
        return SystemStatus(
            service_status="running",
            llm_count=len(rm.llms),
            database_count=len(rm.databases),
            workflow_count=len(WORKFLOW_MAP),
            memory_usage={
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            uptime=str(uptime)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


# 获取可用LLM列表
@router.get("/llms", response_model=BaseResponse)
async def get_available_llms():
    """获取所有可用的LLM模型"""
    try:
        rm = get_resource_manager()
        llms = []
        seen_names = set()  # 用于去重
        
        for name, model in rm.llms:
            # 去重检查
            if name in seen_names:
                continue
            seen_names.add(name)
            
            # 尝试确定模型提供商和类型
            provider = "unknown"
            model_type = "unknown"
            max_tokens = None
            temperature = None
            
            # 调试信息
            print(f"Debug: Processing model {name}, model.model = {getattr(model, 'model', 'N/A')}")
            
            if hasattr(model, 'model'):
                model_id = model.model
                if 'gpt' in model_id:
                    provider = "OpenAI"
                    model_type = "GPT"
                elif 'claude' in model_id:
                    provider = "Anthropic"
                    model_type = "Claude"
                elif 'gemini' in model_id:
                    provider = "Google"
                    model_type = "Gemini"
                elif 'mistral' in model_id:
                    provider = "Mistral"
                    model_type = "Mistral"
                elif 'deepseek' in model_id:
                    provider = "DeepSeek"
                    model_type = "Custom"
                elif 'ep-' in model_id or 'doubao' in model_id:
                    provider = "ARK"
                    model_type = "Custom"
            
            # 基于模型名称的识别（作为备用）
            if provider == "unknown":
                if 'ark' in name or 'doubao' in name:
                    provider = "ARK"
                    model_type = "Custom"
                elif 'gpt' in name:
                    provider = "OpenAI"
                    model_type = "GPT"
                elif 'claude' in name:
                    provider = "Anthropic"
                    model_type = "Claude"
                elif 'gemini' in name:
                    provider = "Google"
                    model_type = "Gemini"
                elif 'mistral' in name:
                    provider = "Mistral"
                    model_type = "Mistral"
                elif 'deepseek' in name:
                    provider = "DeepSeek"
                    model_type = "Custom"
            
            if hasattr(model, 'max_tokens'):
                max_tokens = model.max_tokens
            if hasattr(model, 'temperature'):
                temperature = model.temperature
            
            print(f"Debug: Final result for {name}: provider={provider}, model_type={model_type}")
            
            llms.append(LLMInfo(
                name=name,
                status=LLMStatus.AVAILABLE,
                provider=provider,
                model_type=model_type,
                max_tokens=max_tokens,
                temperature=temperature
            ))
        
        return BaseResponse(
            success=True,
            message=f"Found {len(llms)} available LLMs",
            data=llms
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get LLMs: {str(e)}")


# 获取可用数据库列表
@router.get("/databases", response_model=BaseResponse)
async def get_available_databases():
    """获取所有可用的数据库"""
    try:
        rm = get_resource_manager()
        databases = []
        
        for name, db_info in rm.databases.items():
            graph_store = db_info["graph_store"]
            schema = graph_store.get_schema()
            
            node_types = list(schema.get("node_types", {}).keys())
            relationship_types = [rel["type"] for rel in schema.get("relationships", [])]
            
            # 获取数据库URI，如果没有url属性则使用默认值
            try:
                uri = graph_store.url if hasattr(graph_store, 'url') else "bolt://localhost:7687"
            except:
                uri = "bolt://localhost:7687"
            
            databases.append(DatabaseInfo(
                id=db_info.get("id"),
                name=name,
                status=DatabaseStatus.CONNECTED,
                uri=uri,
                schema_count=len(schema.get("relationships", [])),
                node_types=node_types,
                relationship_types=relationship_types
            ))
        
        return BaseResponse(
            success=True,
            message=f"Found {len(databases)} available databases",
            data=databases
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get databases: {str(e)}")


# 获取可用工作流列表
@router.get("/workflows", response_model=BaseResponse)
async def get_available_workflows():
    """获取所有可用的工作流"""
    try:
        workflows = []
        
        workflow_descriptions = {
            "text2cypher_with_1_retry_and_output_check": "Text2Cypher with retry and output check workflow",
            "naive_text2cypher": "Naive text2cypher workflow",
            "naive_text2cypher_with_1_retry": "Naive text2cypher with retry workflow"
        }
        
        for name, workflow_class in WORKFLOW_MAP.items():
            workflows.append(WorkflowInfo(
                name=name,
                type=WorkflowType(name),
                description=workflow_descriptions.get(name, "No description available"),
                parameters={
                    "timeout": 60,
                    "max_retries": 1 if "retry" in name else 0
                }
            ))
        
        return BaseResponse(
            success=True,
            message=f"Found {len(workflows)} available workflows",
            data=workflows
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")


# 执行单个工作流
@router.post("/workflow/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(request: WorkflowExecuteRequest):
    """执行单个工作流"""
    start_time = time.time()
    events = []
    
    try:
        # 更新统计信息
        execution_stats["total_executions"] += 1
        execution_stats["workflow_usage"][request.workflow_type.value] = \
            execution_stats["workflow_usage"].get(request.workflow_type.value, 0) + 1
        execution_stats["llm_usage"][request.llm_name] = \
            execution_stats["llm_usage"].get(request.llm_name, 0) + 1
        
        ws = get_workflow_service()
        # 解析数据库：优先使用 database_id，其次 database_name
        rm = get_resource_manager()
        chosen_db_name = None
        if request.database_id:
            chosen_db_name = rm.get_database_name_by_id(request.database_id)
            if not chosen_db_name:
                raise HTTPException(status_code=404, detail=f"Database id '{request.database_id}' not found")
        else:
            if not request.database_name:
                raise HTTPException(status_code=400, detail="Either database_id or database_name must be provided")
            chosen_db_name = request.database_name

        result = await ws.execute_workflow(
            llm_name=request.llm_name,
            database_name=chosen_db_name,
            workflow_type=request.workflow_type.value,
            input_text=request.input_text,
            context=request.context or {},
            timeout=request.timeout,
            prompt_config=request.prompt_config.dict() if request.prompt_config else None
        )
        
        execution_time = time.time() - start_time
        execution_stats["successful_executions"] += 1
        execution_stats["execution_times"].append(execution_time)
        
        return WorkflowExecuteResponse(
            success=True,
            events=events,
            result=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        execution_stats["failed_executions"] += 1
        
        events.append(WorkflowEvent(
            event_type="error",
            label="Error",
            message=str(e),
            timestamp=datetime.now().isoformat()
        ))
        
        return WorkflowExecuteResponse(
            success=False,
            events=events,
            result=None,
            execution_time=execution_time
        )


# 流式执行工作流
@router.post("/workflow/execute/stream")
async def execute_workflow_stream(request: WorkflowExecuteRequest):
    """流式执行工作流（Server-Sent Events）"""
    async def generate():
        try:
            ws = get_workflow_service()
            rm = get_resource_manager()
            chosen_db_name = None
            if request.database_id:
                chosen_db_name = rm.get_database_name_by_id(request.database_id)
                if not chosen_db_name:
                    raise HTTPException(status_code=404, detail=f"Database id '{request.database_id}' not found")
            else:
                if not request.database_name:
                    raise HTTPException(status_code=400, detail="Either database_id or database_name must be provided")
                chosen_db_name = request.database_name

            async for event in ws.execute_workflow_stream(
                llm_name=request.llm_name,
                database_name=chosen_db_name,
                workflow_type=request.workflow_type.value,
                input_text=request.input_text,
                context=request.context or {},
                timeout=request.timeout,
                prompt_config=request.prompt_config.dict() if request.prompt_config else None
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            error_event = {
                "event_type": "error",
                "label": "Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# 批量执行工作流
@router.post("/workflow/execute/batch", response_model=BatchWorkflowResponse)
async def execute_workflow_batch(request: BatchWorkflowRequest):
    """批量执行工作流"""
    try:
        ws = get_workflow_service()
        results = await ws.execute_workflow_batch(
            requests=request.requests,
            max_concurrent=request.max_concurrent
        )
        
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count
        
        return BatchWorkflowResponse(
            total_count=len(results),
            success_count=success_count,
            failed_count=failed_count,
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch execution failed: {str(e)}")


# 获取统计信息
@router.get("/statistics", response_model=StatisticsInfo)
async def get_statistics():
    """获取系统统计信息"""
    try:
        avg_time = 0
        if execution_stats["execution_times"]:
            avg_time = sum(execution_stats["execution_times"]) / len(execution_stats["execution_times"])
        
        # 获取热门工作流
        popular_workflows = [
            {"name": name, "count": count}
            for name, count in sorted(
                execution_stats["workflow_usage"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]
        
        # 获取热门LLM
        popular_llms = [
            {"name": name, "count": count}
            for name, count in sorted(
                execution_stats["llm_usage"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]
        
        return StatisticsInfo(
            total_executions=execution_stats["total_executions"],
            successful_executions=execution_stats["successful_executions"],
            failed_executions=execution_stats["failed_executions"],
            average_execution_time=avg_time,
            popular_workflows=popular_workflows,
            popular_llms=popular_llms,
            daily_stats=[]  # 可以扩展为每日统计
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# 测试LLM连接
@router.post("/llms/{llm_name}/test")
async def test_llm_connection(llm_name: str):
    """测试LLM连接"""
    try:
        rm = get_resource_manager()
        llm = rm.get_model_by_name(llm_name)
        
        if not llm:
            raise HTTPException(status_code=404, detail=f"LLM '{llm_name}' not found")
        
        # 发送测试消息
        test_message = "Hello, this is a test message."
        response = await llm.acomplete(test_message)
        
        return BaseResponse(
            success=True,
            message=f"LLM '{llm_name}' connection test successful",
            data={"response": response.text if hasattr(response, 'text') else str(response)}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM test failed: {str(e)}")


# 测试数据库连接
@router.post("/databases/{database_name}/test")
async def test_database_connection(database_name: str):
    """测试数据库连接"""
    try:
        rm = get_resource_manager()
        if database_name not in rm.databases:
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
        
        db_info = rm.databases[database_name]
        graph_store = db_info["graph_store"]
        
        # 执行简单查询测试
        test_query = "MATCH (n) RETURN count(n) as count LIMIT 1"
        result = graph_store.query(test_query)
        
        return BaseResponse(
            success=True,
            message=f"Database '{database_name}' connection test successful",
            data={"node_count": result[0]["count"] if result else 0}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database test failed: {str(e)}")


# 获取数据库模式
@router.get("/databases/{database_name}/schema")
async def get_database_schema(database_name: str):
    """获取数据库模式信息"""
    try:
        rm = get_resource_manager()
        if database_name not in rm.databases:
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
        
        db_info = rm.databases[database_name]
        graph_store = db_info["graph_store"]
        schema = graph_store.get_schema()
        
        return BaseResponse(
            success=True,
            message=f"Schema for database '{database_name}'",
            data=schema
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {str(e)}")


# 重置统计信息
@router.post("/statistics/reset")
async def reset_statistics():
    """重置统计信息"""
    global execution_stats
    execution_stats = {
        "total_executions": 0,
        "successful_executions": 0,
        "failed_executions": 0,
        "execution_times": [],
        "workflow_usage": {},
        "llm_usage": {}
    }
    
    return BaseResponse(
        success=True,
        message="Statistics reset successfully"
    ) 
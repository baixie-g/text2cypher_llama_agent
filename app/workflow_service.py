import json
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from llama_index.core.workflow import Workflow

from app.resource_manager import ResourceManager
from app.settings import WORKFLOW_MAP
from app.api_models import WorkflowExecuteResponse, WorkflowEvent
from app.utils import get_llm_logger


class WorkflowService:
    def __init__(self, resource_manager: ResourceManager):
        self.resource_manager = resource_manager

    async def execute_workflow(
        self,
        llm_name: str,
        database_name: str,
        workflow_type: str,
        input_text: str,
        context: Dict[str, Any] = None,
        timeout: int = 60,
        prompt_config: Dict[str, Any] = None
    ) -> Any:
        """执行单个工作流"""
        # 获取日志记录器
        logger = get_llm_logger()
        
        try:
            # 记录工作流开始
            logger.log_workflow_step(
                "工作流开始", 
                f"开始执行工作流: {workflow_type}",
                {
                    "llm_name": llm_name,
                    "database_name": database_name,
                    "workflow_type": workflow_type,
                    "input_text": input_text,
                    "timeout": timeout
                }
            )
            
            # 获取工作流类
            workflow_class = WORKFLOW_MAP.get(workflow_type)
            if not workflow_class:
                raise ValueError(f"Workflow '{workflow_type}' is not recognized.")

            # 获取LLM和数据库
            selected_llm = self.resource_manager.get_model_by_name(llm_name)
            if not selected_llm:
                raise ValueError(f"LLM '{llm_name}' not found.")

            selected_database = self.resource_manager.get_database_by_name(database_name)
            if not selected_database:
                raise ValueError(f"Database '{database_name}' not found.")

            # 准备上下文
            if context is None:
                context = {}
            
            # 添加输入文本到上下文
            context["input"] = input_text
            
            # 添加提示词配置到上下文
            if prompt_config:
                context["prompt_config"] = prompt_config

            # 创建工作流实例
            workflow_instance = workflow_class(
                llm=selected_llm,
                db=selected_database,
                embed_model=self.resource_manager.embed_model,
                timeout=timeout,
            )

            # 执行工作流
            handler = workflow_instance.run(**context)
            result = await handler
            
            # 记录工作流完成
            logger.log_workflow_step(
                "工作流完成", 
                f"工作流执行成功: {workflow_type}",
                {
                    "result": result,
                    "execution_time": "completed"
                }
            )

            return result

        except Exception as e:
            # 记录工作流错误
            logger.log_workflow_step(
                "工作流错误", 
                f"工作流执行失败: {workflow_type}",
                {
                    "error": str(e),
                    "workflow_type": workflow_type
                }
            )
            raise Exception(f"Workflow execution failed: {str(e)}")

    async def execute_workflow_stream(
        self,
        llm_name: str,
        database_name: str,
        workflow_type: str,
        input_text: str,
        context: Dict[str, Any] = None,
        timeout: int = 60,
        prompt_config: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式执行工作流"""
        try:
            # 获取工作流类
            workflow_class = WORKFLOW_MAP.get(workflow_type)
            if not workflow_class:
                raise ValueError(f"Workflow '{workflow_type}' is not recognized.")

            # 获取LLM和数据库
            selected_llm = self.resource_manager.get_model_by_name(llm_name)
            if not selected_llm:
                raise ValueError(f"LLM '{llm_name}' not found.")

            selected_database = self.resource_manager.get_database_by_name(database_name)
            if not selected_database:
                raise ValueError(f"Database '{database_name}' not found.")

            # 准备上下文
            if context is None:
                context = {}
            
            # 添加输入文本到上下文
            context["input"] = input_text
            
            # 添加提示词配置到上下文
            if prompt_config:
                context["prompt_config"] = prompt_config

            # 创建工作流实例
            workflow_instance = workflow_class(
                llm=selected_llm,
                db=selected_database,
                embed_model=self.resource_manager.embed_model,
                timeout=timeout,
            )

            # 执行工作流并流式返回事件
            handler = workflow_instance.run(**context)

            async for event in handler.stream_events():
                if type(event).__name__ != "StopEvent":
                    event_data = {
                        "event_type": type(event).__name__,
                        "label": event.label,
                        "message": event.message,
                        "timestamp": datetime.now().isoformat()
                    }
                    yield event_data

            # 返回最终结果
            result = await handler
            yield {
                "event_type": "result",
                "label": "Result",
                "message": "Workflow completed successfully",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            yield {
                "event_type": "error",
                "label": "Error",
                "message": f"Workflow execution failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def execute_workflow_batch(
        self,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[WorkflowExecuteResponse]:
        """批量执行工作流"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single(request):
            async with semaphore:
                start_time = datetime.now()
                events = []
                
                try:
                    # 兼容 database_id / database_name
                    def _get(obj, key):
                        if isinstance(obj, dict):
                            return obj.get(key)
                        return getattr(obj, key, None)

                    db_id = _get(request, "database_id")
                    db_name = _get(request, "database_name")
                    chosen_db_name = None
                    if db_id:
                        chosen_db_name = self.resource_manager.get_database_name_by_id(db_id)
                        if not chosen_db_name:
                            raise ValueError(f"Database id '{db_id}' not found")
                    else:
                        if not db_name:
                            raise ValueError("Either database_id or database_name must be provided")
                        chosen_db_name = db_name

                    result = await self.execute_workflow(
                        llm_name=_get(request, "llm_name"),
                        database_name=chosen_db_name,
                        workflow_type=_get(request, "workflow_type"),
                        input_text=_get(request, "input_text"),
                        context=(request.get("context", {}) if isinstance(request, dict) else (_get(request, "context") or {})),
                        timeout=(request.get("timeout", 60) if isinstance(request, dict) else (_get(request, "timeout") or 60)),
                        prompt_config=(request.get("prompt_config") if isinstance(request, dict) else _get(request, "prompt_config"))
                    )
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    return WorkflowExecuteResponse(
                        success=True,
                        events=events,
                        result=result,
                        execution_time=execution_time
                    )
                    
                except Exception as e:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
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

        # 并发执行所有请求
        tasks = [execute_single(request) for request in requests]
        results = await asyncio.gather(*tasks)
        
        return results

    def get_workflow_info(self, workflow_type: str) -> Optional[Dict[str, Any]]:
        """获取工作流信息"""
        workflow_class = WORKFLOW_MAP.get(workflow_type)
        if not workflow_class:
            return None
        
        return {
            "name": workflow_type,
            "class": workflow_class.__name__,
            "module": workflow_class.__module__,
            "description": getattr(workflow_class, '__doc__', 'No description available')
        }

    def list_available_workflows(self) -> List[str]:
        """列出所有可用的工作流"""
        return list(WORKFLOW_MAP.keys())

    def validate_workflow_request(
        self,
        llm_name: str,
        database_name: str,
        workflow_type: str
    ) -> bool:
        """验证工作流请求参数"""
        # 检查工作流是否存在
        if workflow_type not in WORKFLOW_MAP:
            return False
        
        # 检查LLM是否存在
        if not self.resource_manager.get_model_by_name(llm_name):
            return False
        
        # 检查数据库是否存在
        if database_name not in self.resource_manager.databases:
            return False
        
        return True 
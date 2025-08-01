import json
from typing import Type

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from llama_index.core.workflow import Workflow
from pydantic import BaseModel

from app.resource_manager import ResourceManager
from app.settings import WORKFLOW_MAP
from app.utils import urlx_for
from app.api_routes import router as api_router

load_dotenv()

templates = Jinja2Templates(directory="app/templates")
templates.env.globals["url_for"] = urlx_for

app = FastAPI(
    title="Text2Cypher Llama Agent API",
    description="A comprehensive API for Text2Cypher workflows with LLM integration",
    version="4.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 包含API路由
app.include_router(api_router)

resource_manager = ResourceManager()


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Web界面首页"""
    workflows = list(WORKFLOW_MAP.keys())
    llms_list = [name for name, _ in resource_manager.llms]
    databases_list = list(resource_manager.databases.keys())

    return templates.TemplateResponse(
        request=request,
        name="pages/index.html",
        context={
            "workflows": workflows,
            "llms": llms_list,
            "databases": databases_list,
        },
    )


class WorkflowPayload(BaseModel):
    llm: str
    database: str
    workflow: str
    context: str


@app.post("/workflow/")
async def workflow(payload: WorkflowPayload):
    """原有的Web界面工作流执行接口"""
    llm = payload.llm
    database = payload.database
    workflow = payload.workflow
    context_input = payload.context

    try:
        context = json.loads(context_input)
    except json.JSONDecodeError:
        context = {"input": context_input}

    return StreamingResponse(
        run_workflow(llm=llm, database=database, workflow=workflow, context=context),
        media_type="text/event-stream",
    )


# Main workflow runner function
async def run_workflow(llm: str, database: str, workflow: str, context: dict):
    """原有的工作流执行函数"""
    try:
        workflow_class: Type[Workflow] = WORKFLOW_MAP.get(workflow)
        if not workflow_class:
            raise ValueError(f"Workflow '{workflow}' is not recognized.")

        selected_llm = resource_manager.get_model_by_name(llm)
        selected_database = resource_manager.get_database_by_name(database)
        # 修复类型拼接问题
        print(f"!!!!1 {selected_database}")

        workflow_instance = workflow_class(
            llm=selected_llm,
            db=selected_database,
            embed_model=resource_manager.embed_model,
            timeout=60,
        )

        handler = workflow_instance.run(**context)

        async for event in handler.stream_events():
            if type(event).__name__ != "StopEvent":
                event_data = json.dumps(
                    {
                        "event_type": type(event).__name__,
                        "label": event.label,
                        "message": event.message,
                    }
                )
                yield f"data: {event_data}\n\n"

        result = await handler

        yield f"data: {json.dumps({'result': result})}\n\n"

    except Exception as ex:
        error = json.dumps(
            {
                "event_type": "error",
                "label": "Error",
                "message": f"Failed to run workflow.\n\n{ex}",
            }
        )
        yield f"data: {error}\n\n"


# 添加根路径的API信息
@app.get("/api")
async def api_info():
    """API信息页面"""
    return {
        "service": "Text2Cypher Llama Agent API",
        "version": "4.0.0",
        "description": "A comprehensive API for Text2Cypher workflows with LLM integration",
        "endpoints": {
            "web_interface": "/",
            "api_documentation": "/api/docs",
            "health_check": "/api/v1/health",
            "system_status": "/api/v1/status",
            "available_llms": "/api/v1/llms",
            "available_databases": "/api/v1/databases",
            "available_workflows": "/api/v1/workflows",
            "execute_workflow": "/api/v1/workflow/execute",
            "stream_workflow": "/api/v1/workflow/execute/stream",
            "batch_workflow": "/api/v1/workflow/execute/batch",
            "statistics": "/api/v1/statistics"
        },
        "features": [
            "Multiple LLM support (OpenAI, Anthropic, Google, Mistral, ARK)",
            "Neo4j database integration",
            "Multiple workflow types",
            "Real-time streaming execution",
            "Batch processing",
            "Comprehensive monitoring and statistics",
            "Health checks and system status",
            "RESTful API design"
        ]
    }

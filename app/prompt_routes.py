from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from app.prompt_models import (
    PromptType, PromptTemplate, PromptTypeInfo, TemplateListRequest, TemplateListResponse,
    CreateTemplateRequest, UpdateTemplateRequest, CopyTemplateRequest
)
from app.prompt_manager import PromptManager
from app.api_models import BaseResponse

# 创建路由器
router = APIRouter(prefix="/prompts", tags=["Text2Cypher API"])

# 全局提示词管理器实例
prompt_manager = None


def get_prompt_manager():
    """获取提示词管理器实例"""
    global prompt_manager
    if prompt_manager is None:
        prompt_manager = PromptManager()
    return prompt_manager


@router.get("/types", response_model=BaseResponse)
async def get_prompt_types():
    """获取所有提示词类型"""
    try:
        pm = get_prompt_manager()
        types_info = pm.get_prompt_types()
        
        return BaseResponse(
            success=True,
            message=f"获取到 {len(types_info)} 个提示词类型",
            data=types_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提示词类型失败: {str(e)}")


@router.get("/templates", response_model=TemplateListResponse)
async def get_templates(
    prompt_type: Optional[PromptType] = Query(None, description="提示词类型过滤"),
    is_active: Optional[bool] = Query(None, description="是否激活过滤"),
    is_default: Optional[bool] = Query(None, description="是否默认模板过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取模板列表（支持分页过滤）"""
    try:
        pm = get_prompt_manager()
        templates, total = pm.list_templates(
            prompt_type=prompt_type,
            is_active=is_active,
            is_default=is_default,
            search=search,
            page=page,
            page_size=page_size
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return TemplateListResponse(
            templates=templates,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/templates/detail/{template_id}", response_model=BaseResponse)
async def get_template_detail(template_id: str):
    """获取指定模板的详细信息"""
    try:
        pm = get_prompt_manager()
        template = pm.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"模板 '{template_id}' 不存在")
        
        return BaseResponse(
            success=True,
            message="获取模板详情成功",
            data=template
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")


@router.post("/templates", response_model=BaseResponse)
async def create_template(request: CreateTemplateRequest):
    """创建新模板"""
    try:
        pm = get_prompt_manager()
        template = pm.create_template(request)
        
        return BaseResponse(
            success=True,
            message="模板创建成功",
            data=template
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")


@router.put("/templates/{template_id}", response_model=BaseResponse)
async def update_template(template_id: str, request: UpdateTemplateRequest):
    """更新指定模板"""
    try:
        pm = get_prompt_manager()
        template = pm.update_template(template_id, request)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"模板 '{template_id}' 不存在")
        
        return BaseResponse(
            success=True,
            message="模板更新成功",
            data=template
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新模板失败: {str(e)}")


@router.delete("/templates/{template_id}", response_model=BaseResponse)
async def delete_template(template_id: str):
    """删除指定模板"""
    try:
        pm = get_prompt_manager()
        success = pm.delete_template(template_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"模板 '{template_id}' 不存在或无法删除")
        
        return BaseResponse(
            success=True,
            message="模板删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除模板失败: {str(e)}")


@router.post("/templates/{template_id}/copy", response_model=BaseResponse)
async def copy_template(template_id: str, request: CopyTemplateRequest):
    """复制现有模板"""
    try:
        pm = get_prompt_manager()
        new_template = pm.copy_template(template_id, request)
        
        if not new_template:
            raise HTTPException(status_code=404, detail=f"模板 '{template_id}' 不存在")
        
        return BaseResponse(
            success=True,
            message="模板复制成功",
            data=new_template
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"复制模板失败: {str(e)}")


@router.get("/templates/default/{prompt_type}", response_model=BaseResponse)
async def get_default_template(prompt_type: PromptType):
    """获取指定类型的默认模板"""
    try:
        pm = get_prompt_manager()
        template = pm.get_default_template(prompt_type)
        
        if not template:
            raise HTTPException(status_code=404, detail=f"类型 '{prompt_type.value}' 没有默认模板")
        
        return BaseResponse(
            success=True,
            message="获取默认模板成功",
            data=template
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取默认模板失败: {str(e)}")


@router.get("/templates/by-type/{prompt_type}", response_model=BaseResponse)
async def get_templates_by_type(
    prompt_type: PromptType,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小")
):
    """获取指定类型的所有模板"""
    try:
        pm = get_prompt_manager()
        templates, total = pm.list_templates(
            prompt_type=prompt_type,
            page=page,
            page_size=page_size
        )
        
        total_pages = (total + page_size - 1) // page_size
        
        return BaseResponse(
            success=True,
            message=f"获取类型 '{prompt_type.value}' 的模板成功",
            data={
                "templates": templates,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取类型模板失败: {str(e)}")


@router.post("/templates/import", response_model=BaseResponse)
async def import_templates(templates_data: List[dict]):
    """批量导入模板"""
    try:
        pm = get_prompt_manager()
        imported_count = 0
        
        for template_data in templates_data:
            try:
                request = CreateTemplateRequest(**template_data)
                pm.create_template(request)
                imported_count += 1
            except Exception as e:
                print(f"导入模板失败: {e}")
                continue
        
        return BaseResponse(
            success=True,
            message=f"成功导入 {imported_count} 个模板",
            data={"imported_count": imported_count}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入模板失败: {str(e)}")


@router.get("/templates/export", response_model=BaseResponse)
async def export_templates():
    """导出所有模板"""
    try:
        pm = get_prompt_manager()
        templates, _ = pm.list_templates(page_size=1000)  # 获取所有模板
        
        export_data = [template.dict() for template in templates]
        
        return BaseResponse(
            success=True,
            message=f"导出 {len(export_data)} 个模板成功",
            data=export_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出模板失败: {str(e)}")


@router.get("/templates/files", response_model=BaseResponse)
async def get_template_files_info():
    """获取所有模板文件信息"""
    try:
        pm = get_prompt_manager()
        files_info = pm.get_template_files_info()
        
        return BaseResponse(
            success=True,
            message=f"获取到 {len(files_info)} 个模板文件信息",
            data=files_info
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板文件信息失败: {str(e)}") 
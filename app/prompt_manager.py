import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.prompt_models import (
    PromptTemplate, PromptType, PROMPT_TYPE_DESCRIPTIONS,
    CreateTemplateRequest, UpdateTemplateRequest, CopyTemplateRequest
)


class PromptManager:
    """提示词管理器，负责提示词模板的CRUD操作"""
    
    def __init__(self, storage_dir: str = "prompts"):
        """
        初始化提示词管理器
        
        Args:
            storage_dir: 模板存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.templates: Dict[str, PromptTemplate] = {}
        self._ensure_storage_dir()
        self._load_all_templates()
        self._init_default_templates()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_template_file_path(self, prompt_type: PromptType) -> Path:
        """获取指定提示词类型的模板文件路径"""
        return self.storage_dir / f"{prompt_type.value}.json"
    
    def _load_templates_from_file(self, prompt_type: PromptType):
        """从指定文件加载模板"""
        file_path = self._get_template_file_path(prompt_type)
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for template_data in data.get('templates', []):
                        template = PromptTemplate(**template_data)
                        self.templates[template.id] = template
            except Exception as e:
                print(f"加载模板文件 {file_path} 失败: {e}")
    
    def _load_all_templates(self):
        """从所有文件加载模板"""
        self.templates = {}
        for prompt_type in PromptType:
            self._load_templates_from_file(prompt_type)
        print(f"已加载 {len(self.templates)} 个提示词模板")
    
    def _save_templates_to_file(self, prompt_type: PromptType):
        """保存指定类型的模板到文件"""
        file_path = self._get_template_file_path(prompt_type)
        try:
            # 获取该类型的所有模板
            type_templates = [
                template for template in self.templates.values()
                if template.prompt_type == prompt_type
            ]
            
            # 手动构建可序列化的数据
            templates_data = []
            for template in type_templates:
                template_data = {
                    'id': template.id,
                    'name': template.name,
                    'prompt_type': template.prompt_type.value,
                    'content': template.content,
                    'description': template.description,
                    'version': template.version,
                    'is_default': template.is_default,
                    'is_active': template.is_active,
                    'created_at': template.created_at.isoformat(),
                    'updated_at': template.updated_at.isoformat(),
                    'metadata': template.metadata
                }
                templates_data.append(template_data)
            
            data = {
                'prompt_type': prompt_type.value,
                'templates': templates_data,
                'updated_at': datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存模板文件 {file_path} 失败: {e}")
    
    def _init_default_templates(self):
        """初始化默认模板"""
        if not self.templates:
            self._create_default_templates()
    
    def _create_default_templates(self):
        """创建默认模板"""
        # 简化的默认模板创建 - 只创建几个关键模板作为示例
        default_templates = [
            {
                "name": "默认Naive生成Cypher系统提示词",
                "prompt_type": PromptType.NAIVE_GENERATE_CYPHER_SYSTEM,
                "content": "Given an input question, convert it to a Cypher query. No pre-amble. Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!",
                "description": "默认的Naive生成Cypher系统提示词模板",
                "is_default": True
            },
            {
                "name": "默认Naive生成Cypher用户提示词",
                "prompt_type": PromptType.NAIVE_GENERATE_CYPHER_USER,
                "content": "You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run. Schema: {schema}, Examples: {fewshot_examples}, Question: {question}",
                "description": "默认的Naive生成Cypher用户提示词模板",
                "is_default": True
            },
            {
                "name": "默认迭代规划初始规划系统提示词",
                "prompt_type": PromptType.ITERATIVE_INITIAL_PLAN_SYSTEM,
                "content": "You are a query planning optimizer. Your task is to break down complex questions into efficient, parallel-optimized retrieval steps.",
                "description": "默认的迭代规划初始规划系统提示词模板",
                "is_default": True
            }
        ]
        
        for template_data in default_templates:
            self.create_template(CreateTemplateRequest(**template_data))
        
        print(f"已创建 {len(default_templates)} 个默认模板")
    
    def create_template(self, request: CreateTemplateRequest) -> PromptTemplate:
        """创建新模板"""
        template_id = str(uuid.uuid4())
        template = PromptTemplate(
            id=template_id,
            name=request.name,
            prompt_type=request.prompt_type,
            content=request.content,
            description=request.description,
            is_default=request.is_default,
            metadata=request.metadata
        )
        
        # 如果设置为默认模板，需要将同类型的其他模板设为非默认
        if request.is_default:
            self._unset_default_for_type(request.prompt_type)
        
        self.templates[template_id] = template
        self._save_templates_to_file(request.prompt_type)
        return template
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """获取指定模板"""
        return self.templates.get(template_id)
    
    def get_default_template(self, prompt_type: PromptType) -> Optional[PromptTemplate]:
        """获取指定类型的默认模板"""
        for template in self.templates.values():
            if template.prompt_type == prompt_type and template.is_default:
                return template
        return None
    
    def list_templates(
        self,
        prompt_type: Optional[PromptType] = None,
        is_active: Optional[bool] = None,
        is_default: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[PromptTemplate], int]:
        """列出模板"""
        filtered_templates = []
        
        for template in self.templates.values():
            # 类型过滤
            if prompt_type and template.prompt_type != prompt_type:
                continue
            
            # 激活状态过滤
            if is_active is not None and template.is_active != is_active:
                continue
            
            # 默认状态过滤
            if is_default is not None and template.is_default != is_default:
                continue
            
            # 搜索过滤
            if search:
                search_lower = search.lower()
                if (search_lower not in template.name.lower() and 
                    search_lower not in template.description.lower() and
                    search_lower not in template.content.lower()):
                    continue
            
            filtered_templates.append(template)
        
        # 排序：默认模板在前，然后按创建时间倒序
        filtered_templates.sort(key=lambda x: (not x.is_default, x.created_at), reverse=True)
        
        # 分页
        total = len(filtered_templates)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_templates = filtered_templates[start_idx:end_idx]
        
        return paginated_templates, total
    
    def update_template(self, template_id: str, request: UpdateTemplateRequest) -> Optional[PromptTemplate]:
        """更新模板"""
        template = self.templates.get(template_id)
        if not template:
            return None
        
        # 更新字段
        if request.name is not None:
            template.name = request.name
        if request.content is not None:
            template.content = request.content
        if request.description is not None:
            template.description = request.description
        if request.is_active is not None:
            template.is_active = request.is_active
        if request.metadata is not None:
            template.metadata = request.metadata
        
        # 处理默认模板设置
        if request.is_default is not None:
            if request.is_default:
                self._unset_default_for_type(template.prompt_type)
            template.is_default = request.is_default
        
        template.updated_at = datetime.now()
        self._save_templates_to_file(template.prompt_type)
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        template = self.templates.get(template_id)
        if not template:
            return False
        
        # 不允许删除默认模板
        if template.is_default:
            return False
        
        prompt_type = template.prompt_type
        del self.templates[template_id]
        self._save_templates_to_file(prompt_type)
        return True
    
    def copy_template(self, template_id: str, request: CopyTemplateRequest) -> Optional[PromptTemplate]:
        """复制模板"""
        source_template = self.templates.get(template_id)
        if not source_template:
            return None
        
        new_template = PromptTemplate(
            id=str(uuid.uuid4()),
            name=request.new_name,
            prompt_type=source_template.prompt_type,
            content=source_template.content,
            description=request.description or source_template.description,
            is_default=False,  # 复制的模板不会是默认模板
            metadata=source_template.metadata.copy()
        )
        
        self.templates[new_template.id] = new_template
        self._save_templates_to_file(source_template.prompt_type)
        return new_template
    
    def _unset_default_for_type(self, prompt_type: PromptType):
        """取消指定类型的默认模板设置"""
        for template in self.templates.values():
            if template.prompt_type == prompt_type and template.is_default:
                template.is_default = False
    
    def get_prompt_types(self) -> List[Dict[str, Any]]:
        """获取所有提示词类型信息"""
        types_info = []
        for prompt_type in PromptType:
            type_info = PROMPT_TYPE_DESCRIPTIONS.get(prompt_type, {})
            types_info.append({
                "type": prompt_type,
                "name": type_info.get("name", prompt_type.value),
                "description": type_info.get("description", ""),
                "workflow": type_info.get("workflow", ""),
                "step": type_info.get("step", "")
            })
        return types_info
    
    def get_template_files_info(self) -> List[Dict[str, Any]]:
        """获取所有模板文件信息"""
        files_info = []
        for prompt_type in PromptType:
            file_path = self._get_template_file_path(prompt_type)
            type_info = PROMPT_TYPE_DESCRIPTIONS.get(prompt_type, {})
            
            file_exists = file_path.exists()
            template_count = 0
            if file_exists:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        template_count = len(data.get('templates', []))
                except:
                    template_count = 0
            
            files_info.append({
                "prompt_type": prompt_type.value,
                "file_path": str(file_path),
                "file_exists": file_exists,
                "template_count": template_count,
                "name": type_info.get("name", prompt_type.value),
                "description": type_info.get("description", ""),
                "workflow": type_info.get("workflow", ""),
                "step": type_info.get("step", "")
            })
        
        return files_info 
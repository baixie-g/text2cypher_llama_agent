from typing import Dict, Any, Optional, Tuple, Union
from llama_index.core import ChatPromptTemplate

from app.prompt_models import PromptType, PromptConfig
from app.prompt_manager import PromptManager


class PromptService:
    """提示词服务，负责提示词模板的业务逻辑"""
    
    def __init__(self):
        self.prompt_manager = PromptManager()
    
    def get_prompt_template(
        self, 
        prompt_type: PromptType, 
        prompt_config: Optional[Union[PromptConfig, Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        获取指定类型的提示词模板内容
        
        Args:
            prompt_type: 提示词类型
            prompt_config: 提示词配置，如果指定了模板ID则使用指定模板，否则使用默认模板
            
        Returns:
            提示词模板内容
        """
        if prompt_config:
            # 根据提示词类型确定使用哪个模板ID
            template_id = None
            if "system" in prompt_type.value:
                template_id = prompt_config.get("system_template") if isinstance(prompt_config, dict) else prompt_config.system_template
            elif "user" in prompt_type.value:
                template_id = prompt_config.get("user_template") if isinstance(prompt_config, dict) else prompt_config.user_template
            elif "assistant" in prompt_type.value:
                template_id = prompt_config.get("assistant_template") if isinstance(prompt_config, dict) else prompt_config.assistant_template
            
            if template_id:
                template = self.prompt_manager.get_template(template_id)
                if template and template.is_active:
                    return template.content
        
        # 如果没有指定模板或模板不存在，使用默认模板
        default_template = self.prompt_manager.get_default_template(prompt_type)
        if default_template:
            return default_template.content
        
        return None
    
    def create_chat_prompt(
        self, 
        system_prompt_type: PromptType,
        user_prompt_type: PromptType,
        prompt_config: Optional[PromptConfig] = None,
        **kwargs
    ) -> ChatPromptTemplate:
        """
        创建聊天提示词模板
        
        Args:
            system_prompt_type: 系统提示词类型
            user_prompt_type: 用户提示词类型
            prompt_config: 提示词配置
            **kwargs: 其他参数
            
        Returns:
            ChatPromptTemplate实例
        """
        system_content = self.get_prompt_template(system_prompt_type, prompt_config)
        user_content = self.get_prompt_template(user_prompt_type, prompt_config)
        
        if not system_content or not user_content:
            raise ValueError(f"无法获取提示词模板: {system_prompt_type.value}, {user_prompt_type.value}")
        
        messages = [
            ("system", system_content),
            ("user", user_content),
        ]
        
        return ChatPromptTemplate.from_messages(messages)
    
    def get_workflow_step_prompts(
        self, 
        workflow_type: str, 
        step_name: str, 
        prompt_config: Optional[PromptConfig] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        获取工作流步骤的提示词
        
        Args:
            workflow_type: 工作流类型
            step_name: 步骤名称
            prompt_config: 提示词配置
            
        Returns:
            (system_prompt, user_prompt) 元组
        """
        # 根据工作流类型和步骤名称确定提示词类型
        prompt_type_mapping = {
            # Naive Text2Cypher 工作流
            ("naive_text2cypher", "generate_cypher"): (
                PromptType.NAIVE_GENERATE_CYPHER_SYSTEM,
                PromptType.NAIVE_GENERATE_CYPHER_USER
            ),
            ("naive_text2cypher", "correct_cypher"): (
                PromptType.NAIVE_CORRECT_CYPHER_SYSTEM,
                PromptType.NAIVE_CORRECT_CYPHER_USER
            ),
            ("naive_text2cypher", "evaluate_answer"): (
                PromptType.NAIVE_EVALUATE_ANSWER_SYSTEM,
                PromptType.NAIVE_EVALUATE_ANSWER_USER
            ),
            ("naive_text2cypher", "summarize_answer"): (
                PromptType.NAIVE_SUMMARIZE_ANSWER_SYSTEM,
                PromptType.NAIVE_SUMMARIZE_ANSWER_USER
            ),
            
            # Iterative Planner 工作流
            ("iterative_planner", "initial_plan"): (
                PromptType.ITERATIVE_INITIAL_PLAN_SYSTEM,
                None  # 初始规划只有系统提示词
            ),
            ("iterative_planner", "generate_cypher"): (
                PromptType.ITERATIVE_GENERATE_CYPHER_SYSTEM,
                PromptType.ITERATIVE_GENERATE_CYPHER_USER
            ),
            ("iterative_planner", "validate_cypher"): (
                PromptType.ITERATIVE_VALIDATE_CYPHER_SYSTEM,
                PromptType.ITERATIVE_VALIDATE_CYPHER_USER
            ),
            ("iterative_planner", "information_check"): (
                PromptType.ITERATIVE_INFORMATION_CHECK_SYSTEM,
                PromptType.ITERATIVE_INFORMATION_CHECK_USER
            ),
            ("iterative_planner", "guardrails"): (
                PromptType.ITERATIVE_GUARDRAILS_SYSTEM,
                PromptType.ITERATIVE_GUARDRAILS_USER
            ),
            ("iterative_planner", "final_answer"): (
                PromptType.ITERATIVE_FINAL_ANSWER_SYSTEM,
                PromptType.ITERATIVE_FINAL_ANSWER_USER
            ),
            ("iterative_planner", "correct_cypher"): (
                PromptType.ITERATIVE_CORRECT_CYPHER_SYSTEM,
                PromptType.ITERATIVE_CORRECT_CYPHER_USER
            ),
        }
        
        key = (workflow_type, step_name)
        if key not in prompt_type_mapping:
            return None, None
        
        system_type, user_type = prompt_type_mapping[key]
        system_prompt = self.get_prompt_template(system_type, prompt_config) if system_type else None
        user_prompt = self.get_prompt_template(user_type, prompt_config) if user_type else None
        
        return system_prompt, user_prompt
    
    def validate_prompt_config(self, prompt_config: PromptConfig) -> bool:
        """
        验证提示词配置的有效性
        
        Args:
            prompt_config: 提示词配置
            
        Returns:
            是否有效
        """
        if not prompt_config:
            return True
        
        # 检查指定的模板是否存在且激活
        for template_id in [prompt_config.system_template, prompt_config.user_template, prompt_config.assistant_template]:
            if template_id:
                template = self.prompt_manager.get_template(template_id)
                if not template or not template.is_active:
                    return False
        
        return True
    
    def get_prompt_config_summary(self, prompt_config: Optional[PromptConfig]) -> Dict[str, Any]:
        """
        获取提示词配置摘要信息
        
        Args:
            prompt_config: 提示词配置
            
        Returns:
            配置摘要
        """
        if not prompt_config:
            return {"using_default": True, "custom_templates": []}
        
        custom_templates = []
        for template_id in [prompt_config.system_template, prompt_config.user_template, prompt_config.assistant_template]:
            if template_id:
                template = self.prompt_manager.get_template(template_id)
                if template:
                    custom_templates.append({
                        "id": template.id,
                        "name": template.name,
                        "type": template.prompt_type.value
                    })
        
        return {
            "using_default": len(custom_templates) == 0,
            "custom_templates": custom_templates
        } 
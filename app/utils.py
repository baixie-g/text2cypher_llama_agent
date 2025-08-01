import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import Request
from jinja2 import pass_context


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llm_interactions.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class LLMLogger:
    """LLM交互日志记录器"""
    
    def __init__(self):
        self.logger = logging.getLogger('LLM_Logger')
        self.interaction_count = 0
    
    def log_prompt(self, step_name: str, prompt_content: Any, context: Dict[str, Any] = None):
        """记录发送给LLM的提示词"""
        self.interaction_count += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n{'='*80}")
        print(f"🔵 LLM交互 #{self.interaction_count} - {step_name}")
        print(f"⏰ 时间: {timestamp}")
        print(f"{'='*80}")
        
        if isinstance(prompt_content, list):
            print("📤 发送给LLM的提示词:")
            for i, msg in enumerate(prompt_content):
                if isinstance(msg, tuple) and len(msg) == 2:
                    role, content = msg
                    print(f"\n--- {role.upper()} ---")
                    print(content)
                else:
                    print(f"\n--- 消息 {i+1} ---")
                    print(msg)
        else:
            print("📤 发送给LLM的提示词:")
            print(prompt_content)
        
        if context:
            print(f"\n📋 上下文信息:")
            print(json.dumps(context, ensure_ascii=False, indent=2))
        
        print(f"{'='*80}\n")
        
        # 同时记录到日志文件
        self.logger.info(f"LLM交互 #{self.interaction_count} - {step_name} - 提示词已发送")
    
    def log_response(self, step_name: str, response_content: str, context: Dict[str, Any] = None):
        """记录LLM的完整回应"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n{'='*80}")
        print(f"🟢 LLM回应 #{self.interaction_count} - {step_name}")
        print(f"⏰ 时间: {timestamp}")
        print(f"{'='*80}")
        print("📥 LLM完整回应:")
        print(response_content)
        
        if context:
            print(f"\n📋 上下文信息:")
            print(json.dumps(context, ensure_ascii=False, indent=2))
        
        print(f"{'='*80}\n")
        
        # 同时记录到日志文件
        self.logger.info(f"LLM交互 #{self.interaction_count} - {step_name} - 回应已接收")
    
    def log_workflow_step(self, step_name: str, message: str, data: Any = None):
        """记录工作流步骤信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n{'='*60}")
        print(f"🔄 工作流步骤: {step_name}")
        print(f"⏰ 时间: {timestamp}")
        print(f"💬 消息: {message}")
        
        if data:
            print(f"📊 数据:")
            if isinstance(data, str):
                print(data)
            else:
                print(json.dumps(data, ensure_ascii=False, indent=2))
        
        print(f"{'='*60}\n")
        
        # 同时记录到日志文件
        self.logger.info(f"工作流步骤: {step_name} - {message}")

# 全局LLM日志记录器实例
llm_logger = LLMLogger()

def get_llm_logger() -> LLMLogger:
    """获取LLM日志记录器实例"""
    return llm_logger


def get_optimized_schema(graph_store, exclude_types: List[str] = None) -> str:
    """
    获取优化的schema信息，只包含node_props和relationships
    过滤掉Entity标签和其他不需要的信息
    """
    if exclude_types is None:
        exclude_types = ["Entity", "Actor", "Director"]
    else:
        exclude_types.extend(["Entity"])
    
    # 获取原始schema
    schema = graph_store.get_schema()
    
    # 过滤node_props，排除Entity和其他指定类型
    filtered_node_props = {}
    for node_type, props in schema.get("node_props", {}).items():
        if node_type not in exclude_types:
            # 只保留属性名称，不包含类型信息
            if isinstance(props, list):
                # 如果是字典列表格式
                prop_names = [prop.get('property', prop) if isinstance(prop, dict) else prop for prop in props]
            else:
                # 如果是字符串列表格式
                prop_names = props if isinstance(props, list) else []
            filtered_node_props[node_type] = prop_names
    
    # 过滤relationships，排除包含Entity的关系
    filtered_relationships = []
    for rel in schema.get("relationships", []):
        if isinstance(rel, dict):
            # 如果是字典格式
            start = rel.get("start", "")
            end = rel.get("end", "")
            rel_type = rel.get("type", "")
        else:
            # 如果是字符串格式，解析关系字符串
            # 格式: (:StartLabel)-[:RelType]->(:EndLabel)
            parts = str(rel).split(")-[:")
            if len(parts) == 2:
                start_part = parts[0].replace("(:", "")
                end_part = parts[1].split("]->(:")
                if len(end_part) == 2:
                    rel_type = end_part[0]
                    end = end_part[1].replace(")", "")
                else:
                    continue
            else:
                continue
        
        # 检查是否包含需要排除的标签
        if (start not in exclude_types and 
            end not in exclude_types and 
            rel_type not in exclude_types):
            filtered_relationships.append(rel)
    
    # 格式化输出
    node_props_str = []
    for node_type, props in filtered_node_props.items():
        if props:
            props_str = ", ".join(props)
            node_props_str.append(f"{node_type}: [{props_str}]")
        else:
            node_props_str.append(f"{node_type}: []")
    
    relationships_str = []
    for rel in filtered_relationships:
        if isinstance(rel, dict):
            rel_str = f"(:{rel['start']})-[:{rel['type']}]->(:{rel['end']})"
        else:
            rel_str = str(rel)
        relationships_str.append(rel_str)
    
    # 构建最终的schema字符串
    schema_parts = []
    
    if node_props_str:
        schema_parts.append("Node Properties:")
        schema_parts.extend(node_props_str)
    
    if relationships_str:
        schema_parts.append("Relationships:")
        schema_parts.extend(relationships_str)
    
    return "\n".join(schema_parts)


# force HTTPS in jinja templates
@pass_context
def urlx_for(
    context: dict,
    name: str,
    **path_params: Any,
) -> str:
    request: Request = context["request"]
    http_url = request.url_for(name, **path_params)
    if scheme := request.headers.get("x-forwarded-proto"):
        return http_url.replace(scheme=scheme)
    return http_url

from typing import List, Optional
from llama_index.core.embeddings import BaseEmbedding
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F


class BgeEmbedding(BaseEmbedding):
    def __init__(
        self,
        model_path: str,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        normalize: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # 直接赋值给实例属性而不是通过Pydantic
        self.device = device
        self.normalize = normalize
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path).to(self.device)
        self._model_dim = self.model.config.hidden_size  # 从模型配置中获取维度

    @classmethod
    def class_name(cls):
        return "BgeEmbedding"

    def _mean_pooling(self, token_embeddings, attention_mask):
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )
        return embeddings

    def _get_query_embedding(self, query: str):
        inputs = self.tokenizer(
            query,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = self._mean_pooling(
            outputs.last_hidden_state, inputs["attention_mask"]
        )
        if self.normalize:
            embeddings = F.normalize(embeddings, p=2, dim=1)
        return embeddings[0].cpu().tolist()

    def _get_text_embedding(self, text: str):
        return self._get_query_embedding(text)

    def _get_text_embeddings(self, texts: List[str]):
        return [self._get_text_embedding(text) for text in texts]

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> List[float]:
        return self._get_text_embedding(text)

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._get_text_embeddings(texts)

    @property
    def dimensions(self) -> int:
        """返回嵌入向量的维度"""
        return self._model_dim
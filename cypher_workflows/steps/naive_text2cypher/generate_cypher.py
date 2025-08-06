# from nt import system
import sys
from typing import Optional
from llama_index.core import ChatPromptTemplate
# from cypher_workflows.shared.utils import get_neo4j_schema_str
# import os

# 导入日志工具
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from app.utils import get_llm_logger, get_optimized_schema
from app.prompt_service import PromptService
from app.api_models import PromptConfig
from app.prompt_models import PromptType
from typing import Dict, Any

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
GENERATE_SYSTEM_TEMPLATE = """Given an input question, convert it to a Cypher query. No pre-amble.
Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"""

# # 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
GENERATE_USER_TEMPLATE = """You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.
# Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!
# Here is the schema information
# {schema}

# Below are a number of examples of questions and their corresponding Cypher queries.

# {fewshot_examples}

# User input: {question}
# Cypher query:"""

# # 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
GENERATE_USER_TEMPLATE = """You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.
# Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!
# Here is the schema information
# {schema}

# Note: When querying nested properties such as d.attributes.cause, you should use the syntax d.`attributes.cause`.

# Below are a number of examples of questions and their corresponding Cypher queries.

# {fewshot_examples}

# User input: {question}
# Cypher query:"""

# 注意：此硬编码提示词已被迁移到提示词管理系统
# 请使用 PromptService 获取提示词模板
GENERATE_USER_TEMPLATE = """You are a seasoned Neo4j expert. Your job is to generate a **syntactically correct, schema-compliant, and information-rich Cypher query** in response to a user's natural language question.

### 🧠 INTELLIGENT STRATEGIES TO ENHANCE QUERY QUALITY:
- **Use shortestPath or allShortestPaths** when the user's question implies connection or relationship between entities.
- Prefer **multi-hop patterns** to discover indirect connections (e.g., `-[*1..5]-`) rather than limiting to direct relationships.
- Employ **graph algorithms** (e.g., PageRank, community detection, node similarity) when questions involve influence, importance, or clustering.
- Use **pattern comprehensions** to filter or score substructures within a path.
- Apply **aggregation and ranking** (e.g., `ORDER BY count(*) DESC LIMIT 5`) when the question implies summarization or top-k results.
- Use **CALL {...} YIELD** to modularize queries if complex.
- In short, generalize as much as possible and use various algorithmic grammars to obtain more information when the grammar is correct.

**If the question relates to "how two entities are related", default to a shortest path query unless the schema clearly suggests a better alternative.**

### 📝 Schema:
{schema}

### 🧪 Few-shot Examples:
{fewshot_examples}
more:
MATCH p = SHORTESTPATH((n1:Label1 {property1: 'value1'})-[*]-(n2:Label2 {property2: 'value2'}))RETURN p;
MATCH (a:LabelA {name: 'NodeA'}), (b:LabelB {name: 'NodeB'}) WITH a, b, [r1 IN relationships((a)-[*1..2]->()) | type(r1)] AS a_rels, [n1 IN nodes((a)-[*1..2]->()) | n1] AS a_nodes WITH a, b, a_rels, a_nodes, [r2 IN relationships((b)-[*1..2]->()) | type(r2)] AS b_rels, [n2 IN nodes((b)-[*1..2]->()) | n2] AS b_nodes RETURN a, b, a_nodes, a_rels, b_nodes, b_rels

### 🧾 User Input:
{question}

### ✅ Cypher Query (error-free, ready to execute):"""


async def generate_cypher_step(llm, graph_store, subquery, fewshot_examples, prompt_config: Optional[Dict[str, Any]] = None):
    # 获取日志记录器
    logger = get_llm_logger()
    
    # 使用优化的schema函数
    schema = get_optimized_schema(graph_store, exclude_types=["Actor", "Director"])
    print(f"-> 成功获取优化schema为: {schema}")
    
    # 直接用环境变量获取数据库连接参数
    # uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    # username = os.getenv("NEO4J_USERNAME", "neo4j")
    # password = os.getenv("NEO4J_PASSWORD", "12345678")
    # database = os.getenv("NEO4J_DATABASE", "neo4j")
    # schema = get_neo4j_schema_str(uri, username, password, database, exclude_types=["Actor", "Director"])
    
    # schema = graph_store.get_schema_str(exclude_types=["Actor", "Director"])
    # print(f"-> 成功获取 schema 为: {schema}")
    # sys.exit(0)



    # schema = {
    #     'metadata': {
    #         'constraint': [],
    #         'index': []
    #     },
    #     'node_props': {
    #         'Check': ['type', 'aliases', 'name', 'definition'],
    #         'Department': ['type', 'aliases', 'name', 'definition'],
    #         'Disease': [
    #             'attributes.cured_prob',
    #             'definition',
    #             'attributes.cure_department',
    #             'type',
    #             'attributes.cure_lasttime',
    #             'attributes.cure_way',
    #             'attributes.easy_get',
    #             'attributes.cause',
    #             'name',
    #             'aliases',
    #             'attributes.prevent'
    #         ],
    #         'Drug': ['definition', 'type', 'aliases', 'name'],
    #         'Food': ['definition', 'type', 'aliases', 'name'],
    #         'Producer': ['aliases', 'name', 'definition', 'type'],
    #         'Symptom': ['type', 'aliases', 'name', 'definition']
    #     },
    #     'rel_props': {
    #         'acompany_with': ['name'],
    #         'belongs_to': ['name'],
    #         'common_drug': ['name'],
    #         'do_eat': ['name'],
    #         'drugs_of': ['name'],
    #         'has_symptom': ['name'],
    #         'need_check': ['name'],
    #         'no_eat': ['name'],
    #         'recommand_drug': ['name'],
    #         'recommand_eat': ['name']
    #     },
    #     'relationships': [
    #         '(:Disease)-[:recommand_eat]->(:Food)',
    #         '(:Disease)-[:no_eat]->(:Food)',
    #         '(:Disease)-[:do_eat]->(:Food)',
    #         '(:Department)-[:belongs_to]->(:Department)',
    #         '(:Disease)-[:common_drug]->(:Drug)',
    #         '(:Producer)-[:drugs_of]->(:Drug)',
    #         '(:Disease)-[:recommand_drug]->(:Drug)',
    #         '(:Disease)-[:need_check]->(:Check)',
    #         '(:Disease)-[:has_symptom]->(:Symptom)',
    #         '(:Disease)-[:acompany_with]->(:Disease)',
    #         '(:Disease)-[:belongs_to]->(:Department)'
    #     ]
    # }



    # 获取提示词服务
    prompt_service = PromptService()
    
    # 从提示词管理系统获取提示词
    system_prompt, user_prompt = prompt_service.get_workflow_step_prompts(
        workflow_type="naive_text2cypher",
        step_name="generate_cypher",
        prompt_config=prompt_config
    )
    
    # 如果获取失败，抛出异常
    if not system_prompt or not user_prompt:
        raise ValueError("无法从提示词管理系统获取必要的提示词模板")
    
    generate_cypher_msgs = [
        ("system", system_prompt),
        ("user", user_prompt),
    ]
    text2cypher_prompt = ChatPromptTemplate.from_messages(generate_cypher_msgs)

    # 准备发送给LLM的提示词
    prompt_messages = text2cypher_prompt.format_messages(
        question=subquery, schema=schema, fewshot_examples=fewshot_examples
    )
    
    # 记录发送给LLM的提示词
    context = {
        "question": subquery,
        "schema": schema,
        "fewshot_examples": fewshot_examples
    }
    logger.log_prompt("生成Cypher查询", prompt_messages, context)

    # 发送给LLM并获取回应
    response = await llm.achat(prompt_messages)
    
    # 记录LLM的完整回应
    logger.log_response("生成Cypher查询", response.message.content, context)

    return response.message.content
    
    # prompt_content = text2cypher_prompt.format_messages(
    #     question=subquery, schema=schema, fewshot_examples=fewshot_examples
    # )
    # print("\n===== 最终发送给LLM的Cypher提示词1 =====\n")
    # print(prompt_content)
    # sys.exit(0)

    # return ""
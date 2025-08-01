import sys
from llama_index.core import ChatPromptTemplate
from cypher_workflows.shared.utils import get_neo4j_schema_str
import os

# 导入日志工具
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from app.utils import get_llm_logger, get_optimized_schema

CORRECT_CYPHER_SYSTEM_TEMPLATE = """You are a Cypher expert reviewing a statement written by a junior developer.
You need to correct the Cypher statement based on the provided errors. No pre-amble."
Do not wrap the response in any backticks or anything else. Respond with a Cypher statement only!"""

CORRECT_CYPHER_USER_TEMPLATE = """Check for invalid syntax or semantics and return a corrected Cypher statement.

Schema:
{schema}

Note: Do not include any explanations or apologies in your responses.
Do not wrap the response in any backticks or anything else.
Respond with a Cypher statement only!

Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.

The question is:
{question}

The Cypher statement is:
{cypher}

The errors are:
{errors}

Corrected Cypher statement: """


async def correct_cypher_step(llm, graph_store, subquery, cypher, errors):
    # 获取日志记录器
    logger = get_llm_logger()
    
    # 使用优化的schema函数
    schema = get_optimized_schema(graph_store, exclude_types=["Actor", "Director"])
    print(f"-> 成功获取优化corrector schema为: {schema}")
    
    # schema = get_neo4j_schema_str(graph_store, exclude_types=["Actor", "Director"])
    # schema = graph_store.get_schema_str(exclude_types=["Actor", "Director"])
    # print(f"-> 成功获取 corrector schema 为: {schema}")
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

    correct_cypher_messages = [
        ("system", CORRECT_CYPHER_SYSTEM_TEMPLATE),
        ("user", CORRECT_CYPHER_USER_TEMPLATE),
    ]

    correct_cypher_prompt = ChatPromptTemplate.from_messages(correct_cypher_messages)
    
    # 准备发送给LLM的提示词
    prompt_messages = correct_cypher_prompt.format_messages(
        question=subquery, schema=schema, errors=errors, cypher=cypher
    )
    
    # 记录发送给LLM的提示词
    context = {
        "question": subquery,
        "schema": schema,
        "errors": errors,
        "cypher": cypher
    }
    logger.log_prompt("修正Cypher查询", prompt_messages, context)
    
    # 发送给LLM并获取回应
    response = await llm.achat(prompt_messages)
    
    # 记录LLM的完整回应
    logger.log_response("修正Cypher查询", response.message.content, context)
    
    return response.message.content

    # prompt_content = correct_cypher_prompt.format_messages(
    #     question=subquery, schema=schema, errors=errors, cypher=cypher
    # )
    # print("\n===== 最终发送给LLM的Cypher修正提示词 22=====\n")
    # print(prompt_content)
    # sys.exit(0)

    # return ""

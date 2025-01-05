from llama_index.core import ChatPromptTemplate
from pydantic import BaseModel, Field

from typing import List

from app.workflows.utils import llm

class SubqueriesOutput(BaseModel):
    """Defines the output format for transforming a question into parallel-optimized retrieval steps."""
    
    plan: List[List[str]] = Field(description=("""A list of query groups where:
        - Each group (inner list) contains queries that can be executed in parallel
        - Groups are ordered by dependency (earlier groups must be executed before later ones)
        - Each query must be a specific information retrieval request
        - No reasoning or comparison tasks, only data fetching queries"""))

subqueries_system = """You are a query planning optimizer. Your task is to break down complex questions into efficient, parallel-optimized retrieval steps. Focus ONLY on information retrieval queries, not analysis or reasoning steps.

Key Requirements:
- Group queries that can be executed in parallel into the same list
- Order groups based on data dependencies
- Include ONLY specific information retrieval queries
- Exclude reasoning tasks, comparisons, or analysis steps
- Prioritize queries that can be executed first and in parallel

For simple, directly answerable questions, return a single query in a single group.

Example 1:
User: "What was the impact of the 2008 financial crisis on Bank of America's stock price and employee count?"
Assistant: [
    # Group 1 - These can be fetched in parallel
    [
        "What was Bank of America's stock price history from 2007 to 2009?",
        "What was Bank of America's total employee count in 2007?",
        "What was Bank of America's total employee count in 2009?"
    ]
]

Example 2:
User: "Compare the performance of Tesla's Model 3 with BMW's competing models in terms of range and acceleration."
Assistant: [
    # Group 1 - Basic specs can be fetched in parallel
    [
        "What is the EPA range of the Tesla Model 3?",
        "What is the 0-60 mph acceleration time of the Tesla Model 3?",
        "What BMW models compete directly with the Tesla Model 3?"
    ],
    # Group 2 - Depends on knowing competing models from group 1
    [
        "What is the EPA range of each identified BMW competitor model?",
        "What is the 0-60 mph acceleration time of each identified BMW competitor model?"
    ]
]

Remember:
- Focus on data retrieval only
- Maximize parallel execution opportunities
- Maintain necessary sequential ordering
- Keep queries specific and self-contained
- Prioritize independent queries first"""

query_decompose_msgs = [
    ("system", subqueries_system),
    ("user", "{question}")
]

subquery_template = ChatPromptTemplate.from_messages(query_decompose_msgs)

def initial_plan_step(question):
    queries_output = (
        llm.as_structured_llm(SubqueriesOutput)
        .complete(subquery_template.format(question=question))
        .raw
    ).plan
    return {"next_event": "generate_cypher", "arguments": {"plan": queries_output, "question": question}}


import os
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from sentence_transformers import SentenceTransformer

# Neo4j 连接信息
USERNAME = "neo4j"
PASSWORD = "12345678" 
URI = "bolt://localhost:7688"

# 初始化 Neo4j 存储
graph_store = Neo4jPropertyGraphStore(
    username=USERNAME,
    password=PASSWORD,
    url=URI,
    refresh_schema=False,
    create_indexes=True,
    timeout=30,
)

# 初始化嵌入模型（推荐用 BAAI/bge-m3，速度快且免费）
embed_model = SentenceTransformer("BAAI/bge-m3")

def store_fewshot_example(question, database, cypher, llm, success=True):
    label = "Fewshot" if success else "Missing"
    node_id = question + llm + database
    print(f"正在连接到数据库: {URI}")
    # 检查是否已存在
    exists = graph_store.structured_query(
        f"MATCH (f:`{label}` {{id: $id}}) RETURN True",
        param_map={"id": node_id},
    )
    if exists:
        print("已存在，跳过")
        return
    # 真实计算 embedding
    embedding = embed_model.encode(question).tolist()
    # 存储
    graph_store.structured_query(
        f"""MERGE (f:`{label}` {{id: $id}})
SET f.cypher = $cypher, f.llm = $llm, f.created = datetime(), f.question = $question, f.database = $database
WITH f
CALL db.create.setNodeVectorProperty(f,'embedding', $embedding)""",
        param_map={
            "id": node_id,
            "question": question,
            "cypher": cypher,
            "embedding": embedding,
            "database": database,
            "llm": llm,
        },
    )
    print("写入成功")

# 示例用法
if __name__ == "__main__":
    store_fewshot_example(
        question="我似乎得了喘息样支气管炎，这是为什么，我应该怎么做？",
        database="neo4j",
        cypher="""MATCH (d:Disease {name: "喘息样支气管炎"}) OPTIONAL MATCH (d)-[:need_check]->(c:Check) OPTIONAL MATCH (d)-[:recommand_drug]->(drug:Drug) OPTIONAL MATCH (d)-[:recommand_eat]->(food:Food) OPTIONAL MATCH (d)-[:no_eat]->(nofood:Food) RETURN d.`attributes.cause` AS cause, d.`attributes.cure_way` AS cure_way, d.`attributes.prevent` AS prevent, d.`attributes.cure_lasttime` AS cure_lasttime, d.`attributes.cured_prob` AS cured_prob, d.`attributes.cure_department` AS cure_department, d.`attributes.easy_get` AS easy_get, collect(DISTINCT c.name) AS checks, collect(DISTINCT drug.name) AS drugs, collect(DISTINCT food.name) AS recommand_eat, collect(DISTINCT nofood.name) AS no_eat""",
        llm="ark-model",
        success=True
    )
    
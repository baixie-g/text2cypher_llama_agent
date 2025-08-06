import os

from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore


class Neo4jFewshotManager:
    graph_store = None

    def __init__(self):
        print("[DEBUG] FEWSHOT_NEO4J_URI:", os.getenv("FEWSHOT_NEO4J_URI"))
        print("[DEBUG] FEWSHOT_NEO4J_USERNAME:", os.getenv("FEWSHOT_NEO4J_USERNAME"))
        print("[DEBUG] FEWSHOT_NEO4J_PASSWORD:", os.getenv("FEWSHOT_NEO4J_PASSWORD"))
        if os.getenv("FEWSHOT_NEO4J_USERNAME"):
            try:
                self.graph_store = Neo4jPropertyGraphStore(
                    username=os.getenv("FEWSHOT_NEO4J_USERNAME"),
                    password=os.getenv("FEWSHOT_NEO4J_PASSWORD"),
                    url=os.getenv("FEWSHOT_NEO4J_URI"),
                    refresh_schema=False,
                    create_indexes=False,
                    timeout=30,
                )
                print("[DEBUG] 成功连接到 FEWSHOT_NEO4J 图数据库")
            except Exception as e:
                print(f"[ERROR] 连接 FEWSHOT_NEO4J 图数据库失败: {e}")
        else:
            print("[DEBUG] 未配置 FEWSHOT_NEO4J_USERNAME，未启用 Neo4j fewshot")

    def retrieve_fewshots(self, question, database, embed_model):
        if not self.graph_store:
            print("[DEBUG] graph_store 未初始化，无法查询 fewshot")
            return []
        print(f"[DEBUG] 开始查询 Neo4j fewshot，question: {question}, database: {database}")
        try:
            embedding = embed_model.encode(question)
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            print(f"[DEBUG] 计算得到 embedding，长度: {len(embedding)}")
        except Exception as e:
            print(f"[ERROR] 计算 embedding 失败: {e}")
            return []
        cypher = '''MATCH (f:Fewshot)\nWHERE f.database = $database\nWITH f, vector.similarity.cosine(f.embedding, $embedding) AS score\nORDER BY score DESC LIMIT 7\nRETURN f.question AS question, f.cypher AS cypher'''
        param_map = {"embedding": embedding, "database": database}
        # print(f"[DEBUG] 查询Cypher: {cypher}")
        # print(f"[DEBUG] 查询参数: {param_map}")
        try:
            examples = self.graph_store.structured_query(
                cypher,
                param_map=param_map,
            )
            print(f"[DEBUG] 查询结果类型: {type(examples)}，内容: {examples}")
            if not examples:
                print("[DEBUG] 查询结果为空！")
            else:
                print(f"[DEBUG] 查询到 {len(examples)} 条 fewshot 示例")
            return examples
        except Exception as e:
            print(f"[ERROR] 查询 Neo4j fewshot 失败: {e}")
            return []

    def store_fewshot_example(self, question, database, cypher, llm, embed_model, success = True):
        if not self.graph_store:
            return
        label = "Fewshot" if success else "Missing"
        # Check if already exists
        already_exists = self.graph_store.structured_query(
            f"MATCH (f:`{label}` {{id: $question + $llm + $database}}) RETURN True",
            param_map={"question": question, "llm": llm, "database":database},
        )
        if already_exists:
            return

        # Calculate embedding
        # embedding = embed_model.get_text_embedding(question)
        embedding = embed_model.encode(question)
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()

        # Store response
        self.graph_store.structured_query(
            f"""MERGE (f:`{label}` {{id: $question + $llm + $database}})
SET f.cypher = $cypher, f.llm = $llm, f.created = datetime(), f.question = $question, f.database = $database
WITH f
CALL db.create.setNodeVectorProperty(f,'embedding', $embedding)""",
            param_map={
                "question": question,
                "cypher": cypher,
                "embedding": embedding,
                "database": database,
                "llm": llm,
            },
        )
        return

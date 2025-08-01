# from neo4j import GraphDatabase, exceptions

# def get_neo4j_schema_str(uri, username, password, database, exclude_types=None):
#     exclude_types = set(exclude_types or [])
#     driver = GraphDatabase.driver(uri, auth=(username, password))
#     print(f"[INFO] Getting schema from Neo4j database: {uri}")

#     node_labels = []
#     node_props = []
#     rel_types = []
#     rel_props_dict = {}
#     rels_list = []

#     try:
#         with driver.session(database=database) as session:
#             print("[INFO] Connected to Neo4j")

#             # 获取节点标签
#             try:
#                 print("[DEBUG] Trying db.nodeLabels()")
#                 result = session.run("CALL db.nodeLabels()")
#                 node_labels = [record["label"] for record in result]
#             except Exception as e:
#                 print("[WARN] db.nodeLabels() failed, falling back. Error:", e)
#                 try:
#                     result = session.run("MATCH (n) RETURN DISTINCT labels(n) AS labels")
#                     node_labels_set = set()
#                     for record in result:
#                         labels = record.get("labels", [])
#                         if not labels:
#                             continue
#                         for label in labels:
#                             node_labels_set.add(label)
#                     node_labels = list(node_labels_set)
#                     print(f"[DEBUG] Fallback label extraction result: {node_labels}")
#                 except Exception as e2:
#                     print("[ERROR] Fallback label query failed:", e2)

#             node_labels = [label for label in node_labels if label not in exclude_types]
#             print(f"[INFO] Node labels: {node_labels}")

#             # 获取节点属性
#             try:
#                 print("[DEBUG] Trying db.propertyKeys()")
#                 result = session.run("CALL db.propertyKeys()")
#                 node_props = [record["propertyKey"] for record in result]
#             except Exception as e:
#                 print("[WARN] db.propertyKeys() failed, falling back. Error:", e)
#                 try:
#                     result = session.run("MATCH (n) UNWIND keys(n) AS k RETURN DISTINCT k")
#                     node_props = [record["k"] for record in result]
#                 except Exception as e2:
#                     print("[ERROR] Fallback property key query failed:", e2)
#             print(f"[INFO] Node properties: {node_props}")

#             # 获取关系类型
#             try:
#                 print("[DEBUG] Trying db.relationshipTypes()")
#                 result = session.run("CALL db.relationshipTypes()")
#                 rel_types = [record["relationshipType"] for record in result]
#             except Exception as e:
#                 print("[WARN] db.relationshipTypes() failed, falling back. Error:", e)
#                 try:
#                     result = session.run("MATCH ()-[r]->() RETURN DISTINCT type(r) AS t")
#                     rel_types = [record["t"] for record in result]
#                 except Exception as e2:
#                     print("[ERROR] Fallback relationship type query failed:", e2)

#             rel_types = [r for r in rel_types if r not in exclude_types]
#             print(f"[INFO] Relationship types: {rel_types}")

#             # 获取关系属性
#             try:
#                 print("[DEBUG] Running relationship property query")
#                 rel_props_query = """
#                     MATCH ()-[r]->() 
#                     WITH type(r) AS relType, keys(r) AS props
#                     UNWIND props AS prop
#                     RETURN relType, collect(DISTINCT prop) AS propList
#                 """
#                 result = session.run(rel_props_query)
#                 for record in result:
#                     rel_type = record["relType"]
#                     if rel_type in exclude_types:
#                         continue
#                     rel_props_dict[rel_type] = record["propList"]
#             except Exception as e:
#                 print("[ERROR] Relationship properties query failed:", e)

#             print(f"[INFO] Relationship properties: {rel_props_dict}")

#             # 获取关系结构（方向和标签）
#             try:
#                 print("[DEBUG] Running relationship structure query")
#                 rel_struct_query = """
#                     MATCH (a)-[r]->(b)
#                     RETURN DISTINCT labels(a) AS startLabels, type(r) AS relType, labels(b) AS endLabels
#                 """
#                 result = session.run(rel_struct_query)
#                 for record in result:
#                     rel_type = record["relType"]
#                     if rel_type in exclude_types:
#                         continue
#                     start = ":".join(record["startLabels"]) if record["startLabels"] else "?"
#                     end = ":".join(record["endLabels"]) if record["endLabels"] else "?"
#                     rels_list.append(f"(:{start})-[:{rel_type}]->(:{end})")
#             except Exception as e:
#                 print("[ERROR] Relationship structure query failed:", e)

#             print(f"[INFO] Relationship structures: {rels_list}")

#     except exceptions.ServiceUnavailable as e:
#         print(f"[FATAL] Could not connect to Neo4j at {uri}: {e}")
#         return "Neo4j connection failed."
#     except Exception as e:
#         print(f"[FATAL] Unexpected error: {e}")
#         return "Unexpected error occurred."
#     finally:
#         driver.close()
#         print("[INFO] Neo4j connection closed.")

#     # 格式化输出字符串
#     node_props_str = ", ".join(sorted(node_props)) or "None"
#     node_labels_str = ", ".join(sorted(node_labels)) or "None"
#     rel_props_str = ", ".join([f"{k} {{{', '.join(sorted(v))}}}" for k, v in sorted(rel_props_dict.items())]) or "None"
#     rel_types_str = ", ".join(sorted(rel_types)) or "None"
#     rels_str = ", ".join(sorted(rels_list)) or "None"

#     return "\n".join([
#         "Node labels:", node_labels_str,
#         "Node properties:", node_props_str,
#         "Relationship types:", rel_types_str,
#         "Relationship properties:", rel_props_str,
#         "The relationships are the following:", rels_str,
#     ])


# # ========================
# # ✅ 测试入口
# # ========================
# if __name__ == "__main__":
#     # 请根据实际情况修改为你本地的数据库地址和账户
#     uri = "bolt://localhost:7688"
#     username = "neo4j"
#     password = "12345678"
#     database = "neo4j"  # 默认库，可按实际调整

#     print("\n==== Running Schema Extraction Test ====\n")
#     result = get_neo4j_schema_str(uri, username, password, database)
#     print("\n==== Schema Output ====\n")
#     print(result)

from neo4j import GraphDatabase, exceptions

def get_neo4j_schema(uri, username, password, database, exclude_types=None):
    exclude_types = set(exclude_types or [])
    driver = GraphDatabase.driver(uri, auth=(username, password))
    print(f"[INFO] Getting schema from Neo4j database: {uri}")

    schema = {
        "node_props": {},
        "rel_props": {},
        "relationships": [],
        "metadata": {
            "constraint": [],
            "index": []
        }
    }

    try:
        with driver.session(database=database) as session:
            print("[INFO] Connected to Neo4j")

            # === 获取节点标签 ===
            node_labels = []
            try:
                print("[DEBUG] Trying db.nodeLabels()")
                result = session.run("CALL db.nodeLabels()")
                node_labels = [record["label"] for record in result]
            except Exception as e:
                print("[WARN] db.nodeLabels() failed, falling back. Error:", e)
                result = session.run("MATCH (n) RETURN DISTINCT labels(n) AS labels")
                node_labels_set = set()
                for record in result:
                    labels = record.get("labels", [])
                    for label in labels:
                        node_labels_set.add(label)
                node_labels = list(node_labels_set)
            node_labels = [label for label in node_labels if label not in exclude_types]
            print(f"[INFO] Node labels: {node_labels}")

            # === 获取节点属性 ===
            node_props = {}
            for label in node_labels:
                try:
                    print(f"[DEBUG] Querying properties for label: {label}")
                    result = session.run(f"MATCH (n:`{label}`) UNWIND keys(n) AS k RETURN DISTINCT k")
                    props = [record["k"] for record in result]
                    schema["node_props"][label] = props
                except Exception as e:
                    print(f"[WARN] Failed to get properties for label {label}: {e}")
                    schema["node_props"][label] = []

            # === 获取关系类型 ===
            rel_types = []
            try:
                print("[DEBUG] Trying db.relationshipTypes()")
                result = session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in result]
            except Exception as e:
                print("[WARN] db.relationshipTypes() failed, falling back. Error:", e)
                result = session.run("MATCH ()-[r]->() RETURN DISTINCT type(r) AS t")
                rel_types = [record["t"] for record in result]
            rel_types = [r for r in rel_types if r not in exclude_types]
            print(f"[INFO] Relationship types: {rel_types}")

            # === 获取关系属性 ===
            try:
                print("[DEBUG] Running relationship property query")
                rel_props_query = """
                    MATCH ()-[r]->() 
                    WITH type(r) AS relType, keys(r) AS props
                    UNWIND props AS prop
                    RETURN relType, collect(DISTINCT prop) AS propList
                """
                result = session.run(rel_props_query)
                for record in result:
                    rel_type = record["relType"]
                    if rel_type in exclude_types:
                        continue
                    schema["rel_props"][rel_type] = record["propList"]
            except Exception as e:
                print("[ERROR] Relationship properties query failed:", e)

            # === 获取关系结构 ===
            try:
                print("[DEBUG] Running relationship structure query")
                rel_struct_query = """
                    MATCH (a)-[r]->(b)
                    RETURN DISTINCT labels(a) AS startLabels, type(r) AS relType, labels(b) AS endLabels
                """
                result = session.run(rel_struct_query)
                for record in result:
                    rel_type = record["relType"]
                    if rel_type in exclude_types:
                        continue
                    start = ":".join(record["startLabels"]) if record["startLabels"] else "?"
                    end = ":".join(record["endLabels"]) if record["endLabels"] else "?"
                    schema["relationships"].append(f"(:{start})-[:{rel_type}]->(:{end})")
            except Exception as e:
                print("[ERROR] Relationship structure query failed:", e)

            # === 获取约束和索引（metadata） ===
            try:
                print("[DEBUG] Fetching constraints")
                result = session.run("CALL db.constraints()")
                schema["metadata"]["constraint"] = [
                    record._asdict() for record in result
                ]
            except Exception as e:
                print("[ERROR] Failed to fetch constraints:", e)

            try:
                print("[DEBUG] Fetching indexes")
                result = session.run("CALL db.indexes()")
                schema["metadata"]["index"] = [
                    record._asdict() for record in result
                ]
            except Exception as e:
                print("[ERROR] Failed to fetch indexes:", e)

    except exceptions.ServiceUnavailable as e:
        print(f"[FATAL] Could not connect to Neo4j at {uri}: {e}")
        return None
    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")
        return None
    finally:
        driver.close()
        print("[INFO] Neo4j connection closed.")

    return schema


# ========================
# ✅ 测试入口
# ========================
if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "12345678"
    database = "neo4j"

    print("\n==== Running Schema Extraction Test ====\n")
    schema = get_neo4j_schema(uri, username, password, database)
    if schema:
        import pprint
        pprint.pprint(schema)
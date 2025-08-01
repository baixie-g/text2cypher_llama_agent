import os
from neo4j import GraphDatabase

def check_ok(text):
    # Split the text into words
    words = text.strip().split()
    if not words:
        return False
    first_word = words[0]
    last_word = words[-1]
    return first_word in ["Ok.", "Ok"] or last_word in ["Ok.", "Ok"]


def get_neo4j_schema_str(uri, username, password, database, exclude_types=None):
    exclude_types = set(exclude_types or [])
    driver = GraphDatabase.driver(uri, auth=(username, password))
    print(f"[INFO] Getting schema from Neo4j database: {uri}")

    node_labels = []
    node_props = []
    rel_types = []
    rel_props_dict = {}
    rels_list = []

    try:
        with driver.session(database=database) as session:
            print("[INFO] Connected to Neo4j")

            # 获取节点标签
            try:
                print("[DEBUG] Trying db.nodeLabels()")
                result = session.run("CALL db.nodeLabels()")
                node_labels = [record["label"] for record in result]
            except Exception as e:
                print("[WARN] db.nodeLabels() failed, falling back. Error:", e)
                try:
                    result = session.run("MATCH (n) RETURN DISTINCT labels(n) AS labels")
                    node_labels = set()
                    for record in result:
                        for label in record["labels"]:
                            node_labels.add(label)
                    node_labels = list(node_labels)
                except Exception as e2:
                    print("[ERROR] Fallback label query failed:", e2)

            node_labels = [label for label in node_labels if label not in exclude_types]
            print(f"[INFO] Node labels: {node_labels}")

            # 获取节点属性
            try:
                print("[DEBUG] Trying db.propertyKeys()")
                result = session.run("CALL db.propertyKeys()")
                node_props = [record["propertyKey"] for record in result]
            except Exception as e:
                print("[WARN] db.propertyKeys() failed, falling back. Error:", e)
                try:
                    result = session.run("MATCH (n) UNWIND keys(n) AS k RETURN DISTINCT k")
                    node_props = [record["k"] for record in result]
                except Exception as e2:
                    print("[ERROR] Fallback property key query failed:", e2)
            print(f"[INFO] Node properties: {node_props}")

            # 获取关系类型
            try:
                print("[DEBUG] Trying db.relationshipTypes()")
                result = session.run("CALL db.relationshipTypes()")
                rel_types = [record["relationshipType"] for record in result]
            except Exception as e:
                print("[WARN] db.relationshipTypes() failed, falling back. Error:", e)
                try:
                    result = session.run("MATCH ()-[r]->() RETURN DISTINCT type(r) AS t")
                    rel_types = [record["t"] for record in result]
                except Exception as e2:
                    print("[ERROR] Fallback relationship type query failed:", e2)

            rel_types = [r for r in rel_types if r not in exclude_types]
            print(f"[INFO] Relationship types: {rel_types}")

            # 获取关系属性
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
                    prop_list = record["propList"]
                    # 修复：确保prop_list为list，否则转为字符串
                    if isinstance(prop_list, list):
                        rel_props_dict[rel_type] = [str(p) for p in prop_list]
                    else:
                        rel_props_dict[rel_type] = [str(prop_list)]
            except Exception as e:
                print("[ERROR] Relationship properties query failed:", e)

            print(f"[INFO] Relationship properties: {rel_props_dict}")

            # 获取关系结构（方向和标签）
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
                    rels_list.append(f"(:{start})-[:{rel_type}]->(:{end})")
            except Exception as e:
                print("[ERROR] Relationship structure query failed:", e)

            print(f"[INFO] Relationship structures: {rels_list}")

    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")
        return "Unexpected error occurred."
    finally:
        driver.close()
        print("[INFO] Neo4j connection closed.")

    # 格式化输出字符串
    node_props_str = ", ".join(sorted(node_props)) or "None"
    node_labels_str = ", ".join(sorted(node_labels)) or "None"
    # 修复：关系属性格式化时类型安全
    rel_props_str = ", ".join([
        f"{k} {{{', '.join([str(x) for x in v])}}}" if isinstance(v, list) else f"{k} {{{str(v)}}}"
        for k, v in sorted(rel_props_dict.items())
    ]) or "None"
    rel_types_str = ", ".join(sorted(rel_types)) or "None"
    rels_str = ", ".join(sorted(rels_list)) or "None"

    return "\n".join([
        "Node labels:", node_labels_str,
        "Node properties:", node_props_str,
        "Relationship types:", rel_types_str,
        "Relationship properties:", rel_props_str,
        "The relationships are the following:", rels_str,
    ])
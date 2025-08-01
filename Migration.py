from neo4j import GraphDatabase

# 源数据库配置
SOURCE_URI = "neo4j://localhost:7688"
SOURCE_USER = "neo4j"
SOURCE_PASSWORD = "12345678"

# 目标数据库配置
TARGET_URI = "neo4j://localhost:7687"
TARGET_USER = "neo4j"
TARGET_PASSWORD = "12345678"


def fetch_all_data(driver):
    with driver.session() as session:
        # 获取所有节点和关系
        result = session.run("""
            MATCH (n) 
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n, r, m
        """)
        return list(result)


def migrate_data(data, target_driver):
    with target_driver.session() as session:
        for record in data:
            node1 = record["n"]
            rel = record["r"]
            node2 = record["m"]

            # 获取节点label字符串
            labels1 = ":".join(node1.labels) if hasattr(node1, 'labels') else ""
            # 创建第一个节点（如果未创建），带label
            session.run(f"""
                MERGE (n1:{labels1} {{id: $id1}})
                SET n1 += $props1
            """, id1=node1.element_id, props1=dict(node1))

            # 如果存在关系和第二个节点，创建关系和目标节点
            if rel and node2:
                labels2 = ":".join(node2.labels) if hasattr(node2, 'labels') else ""
                session.run(f"""
                    MATCH (n1 {{id: $id1}})
                    MERGE (n2:{labels2} {{id: $id2}})
                    SET n2 += $props2
                    MERGE (n1)-[r:{rel.type}]->(n2)
                    SET r += $props_rel
                """, id1=node1.element_id, id2=node2.element_id,
                   props1=dict(node1), props2=dict(node2),
                   props_rel=dict(rel))


def main():
    # 连接到源数据库
    source_driver = GraphDatabase.driver(SOURCE_URI, auth=(SOURCE_USER, SOURCE_PASSWORD))
    # 连接到目标数据库
    target_driver = GraphDatabase.driver(TARGET_URI, auth=(TARGET_USER, TARGET_PASSWORD))

    print("Fetching data from source...")
    data = fetch_all_data(source_driver)

    print(f"Migrating {len(data)} records to target...")
    migrate_data(data, target_driver)

    print("Migration completed.")

    source_driver.close()
    target_driver.close()


if __name__ == "__main__":
    main()
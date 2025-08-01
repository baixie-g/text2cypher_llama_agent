#!/usr/bin/env python3
"""
Neo4j数据库初始化脚本
用于创建基本的图数据结构，使text2cypher系统能够正常工作
"""

import os
from neo4j import GraphDatabase

# Neo4j连接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "12345678"
NEO4J_DATABASE = "neo4j"

class Neo4jInitializer:
    def __init__(self, uri, username, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.database = database
    
    def close(self):
        self.driver.close()
    
    def create_sample_data(self):
        """创建示例电影数据"""
        with self.driver.session(database=self.database) as session:
            # 创建约束（如果需要）
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Movie) REQUIRE m.title IS UNIQUE")
            
            # 创建示例数据
            sample_data_queries = [
                # 创建人物节点
                """
                CREATE (tom:Person {name: 'Tom Hanks', born: 1956})
                CREATE (meg:Person {name: 'Meg Ryan', born: 1961})
                CREATE (nora:Person {name: 'Nora Ephron', born: 1941})
                CREATE (keanu:Person {name: 'Keanu Reeves', born: 1964})
                CREATE (laurence:Person {name: 'Laurence Fishburne', born: 1961})
                CREATE (carrie:Person {name: 'Carrie-Anne Moss', born: 1967})
                CREATE (wachowski:Person {name: 'Lana Wachowski', born: 1965})
                """,
                
                # 创建电影节点
                """
                CREATE (sleepless:Movie {title: 'Sleepless in Seattle', released: 1993, tagline: 'What if someone you never met, someone you never saw, someone you never knew was the only someone for you?'})
                CREATE (youveGotMail:Movie {title: "You've Got Mail", released: 1998, tagline: 'At odds in life... in love on-line.'})
                CREATE (matrix:Movie {title: 'The Matrix', released: 1999, tagline: 'Welcome to the Real World'})
                CREATE (forrest:Movie {title: 'Forrest Gump', released: 1994, tagline: 'Life is like a box of chocolates... you never know what you are gonna get.'})
                """,
                
                # 创建关系
                """
                MATCH (tom:Person {name: 'Tom Hanks'}), (sleepless:Movie {title: 'Sleepless in Seattle'})
                CREATE (tom)-[:ACTED_IN {roles: ['Sam Baldwin']}]->(sleepless)
                """,
                
                """
                MATCH (meg:Person {name: 'Meg Ryan'}), (sleepless:Movie {title: 'Sleepless in Seattle'})
                CREATE (meg)-[:ACTED_IN {roles: ['Annie Reed']}]->(sleepless)
                """,
                
                """
                MATCH (nora:Person {name: 'Nora Ephron'}), (sleepless:Movie {title: 'Sleepless in Seattle'})
                CREATE (nora)-[:DIRECTED]->(sleepless)
                """,
                
                """
                MATCH (tom:Person {name: 'Tom Hanks'}), (youveGotMail:Movie {title: "You've Got Mail"})
                CREATE (tom)-[:ACTED_IN {roles: ['Joe Fox']}]->(youveGotMail)
                """,
                
                """
                MATCH (meg:Person {name: 'Meg Ryan'}), (youveGotMail:Movie {title: "You've Got Mail"})
                CREATE (meg)-[:ACTED_IN {roles: ['Kathleen Kelly']}]->(youveGotMail)
                """,
                
                """
                MATCH (nora:Person {name: 'Nora Ephron'}), (youveGotMail:Movie {title: "You've Got Mail"})
                CREATE (nora)-[:DIRECTED]->(youveGotMail)
                """,
                
                """
                MATCH (keanu:Person {name: 'Keanu Reeves'}), (matrix:Movie {title: 'The Matrix'})
                CREATE (keanu)-[:ACTED_IN {roles: ['Neo']}]->(matrix)
                """,
                
                """
                MATCH (laurence:Person {name: 'Laurence Fishburne'}), (matrix:Movie {title: 'The Matrix'})
                CREATE (laurence)-[:ACTED_IN {roles: ['Morpheus']}]->(matrix)
                """,
                
                """
                MATCH (carrie:Person {name: 'Carrie-Anne Moss'}), (matrix:Movie {title: 'The Matrix'})
                CREATE (carrie)-[:ACTED_IN {roles: ['Trinity']}]->(matrix)
                """,
                
                """
                MATCH (wachowski:Person {name: 'Lana Wachowski'}), (matrix:Movie {title: 'The Matrix'})
                CREATE (wachowski)-[:DIRECTED]->(matrix)
                """,
                
                """
                MATCH (tom:Person {name: 'Tom Hanks'}), (forrest:Movie {title: 'Forrest Gump'})
                CREATE (tom)-[:ACTED_IN {roles: ['Forrest Gump']}]->(forrest)
                """,
            ]
            
            print("正在创建示例数据...")
            for query in sample_data_queries:
                session.run(query)
            
            print("示例数据创建完成！")
    
    def verify_data(self):
        """验证数据是否创建成功"""
        with self.driver.session(database=self.database) as session:
            # 查询统计信息
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            record = result.single()
            node_count = record["node_count"] if record else 0
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            record = result.single()
            rel_count = record["rel_count"] if record else 0
            
            print(f"数据库统计：")
            print(f"节点数量: {node_count}")
            print(f"关系数量: {rel_count}")
            
            # 查询schema
            try:
                result = session.run("CALL db.schema.visualization()")
                print("\n数据库schema创建成功！")
            except Exception as e:
                print(f"Schema查询失败: {e}")
                print("但基础数据已创建成功！")

def main():
    print("开始初始化Neo4j数据库...")
    print(f"连接地址: {NEO4J_URI}")
    print(f"数据库: {NEO4J_DATABASE}")
    
    initializer = Neo4jInitializer(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE)
    
    try:
        # 创建示例数据
        initializer.create_sample_data()
        
        # 验证数据
        initializer.verify_data()
        
        print("\n✅ Neo4j数据库初始化完成！")
        print("现在可以启动text2cypher应用程序了。")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
    finally:
        initializer.close()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
简化的schema优化功能测试
"""

import json
from typing import List, Dict, Any

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

def test_optimized_schema():
    """测试优化后的schema函数"""
    print("🔍 测试优化后的schema功能")
    print("=" * 60)
    
    # 模拟一个graph_store对象，用于测试
    class MockGraphStore:
        def get_schema(self):
            return {
                "node_props": {
                    "Entity": ["id", "name", "type"],  # 这个应该被过滤掉
                    "Disease": [
                        {"property": "name", "type": "STRING"},
                        {"property": "definition", "type": "TEXT"},
                        {"property": "attributes.cause", "type": "STRING"},
                        {"property": "attributes.cured_prob", "type": "FLOAT"}
                    ],
                    "Drug": [
                        {"property": "name", "type": "STRING"},
                        {"property": "definition", "type": "TEXT"}
                    ],
                    "Symptom": [
                        {"property": "name", "type": "STRING"},
                        {"property": "description", "type": "TEXT"}
                    ]
                },
                "rel_props": {
                    "has_symptom": [{"property": "severity", "type": "INTEGER"}],
                    "treats": [{"property": "effectiveness", "type": "FLOAT"}]
                },
                "relationships": [
                    {"start": "Disease", "type": "has_symptom", "end": "Symptom"},
                    {"start": "Drug", "type": "treats", "end": "Disease"},
                    {"start": "Entity", "type": "related_to", "end": "Disease"},  # 这个应该被过滤掉
                    {"start": "Disease", "type": "caused_by", "end": "Entity"}   # 这个应该被过滤掉
                ]
            }
    
    # 创建模拟的graph_store
    mock_graph_store = MockGraphStore()
    
    # 测试优化后的schema函数
    print("📋 原始schema:")
    original_schema = mock_graph_store.get_schema()
    print(f"Node props: {list(original_schema['node_props'].keys())}")
    relationships_str = [f"{r['start']}-{r['type']}->{r['end']}" for r in original_schema['relationships']]
    print(f"Relationships: {relationships_str}")
    print()
    
    print("✨ 优化后的schema:")
    optimized_schema = get_optimized_schema(mock_graph_store, exclude_types=["Actor", "Director"])
    print(optimized_schema)
    print()
    
    # 验证结果
    print("✅ 验证结果:")
    if "Entity" not in optimized_schema:
        print("✓ Entity标签已被成功过滤")
    else:
        print("✗ Entity标签未被过滤")
    
    if "Disease" in optimized_schema and "Drug" in optimized_schema:
        print("✓ 有效的节点类型被保留")
    else:
        print("✗ 有效的节点类型被错误过滤")
    
    if "has_symptom" in optimized_schema and "treats" in optimized_schema:
        print("✓ 有效的关系类型被保留")
    else:
        print("✗ 有效的关系类型被错误过滤")
    
    if "related_to" not in optimized_schema and "caused_by" not in optimized_schema:
        print("✓ 包含Entity的关系已被过滤")
    else:
        print("✗ 包含Entity的关系未被过滤")

if __name__ == "__main__":
    test_optimized_schema() 
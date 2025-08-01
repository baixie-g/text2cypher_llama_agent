#!/usr/bin/env python3
"""
测试优化后的schema功能
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.utils import get_optimized_schema

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
    print(f"Node props: {original_schema['node_props']}")
    print(f"Relationships: {original_schema['relationships']}")
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
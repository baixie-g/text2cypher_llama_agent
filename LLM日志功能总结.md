# LLM日志功能和Schema优化总结

## 项目概述
该项目是一个基于Neo4j的Text2Cypher系统，通过LLM将自然语言问题转换为Cypher查询，并在医疗知识图谱中查询相关信息。

## 完成的工作

### 1. LLM交互日志系统

#### 1.1 日志工具类 (`app/utils.py`)
- 创建了 `LLMLogger` 类，用于记录LLM交互过程
- 实现了三个主要方法：
  - `log_prompt()`: 记录发送给LLM的提示词
  - `log_response()`: 记录LLM的完整回应
  - `log_workflow_step()`: 记录工作流步骤信息

#### 1.2 日志功能特点
- **交互计数**: 自动为每次LLM交互分配唯一编号
- **时间戳**: 记录每次交互的精确时间
- **格式化输出**: 使用emoji和分隔线美化输出
- **双重记录**: 同时输出到控制台和日志文件
- **上下文信息**: 记录相关的上下文数据

### 2. 工作流日志集成

#### 2.1 修改的文件
1. **`cypher_workflows/steps/naive_text2cypher/generate_cypher.py`**
   - 在生成Cypher查询时记录提示词和回应

2. **`cypher_workflows/steps/naive_text2cypher/correct_cypher.py`**
   - 在修正Cypher查询时记录提示词和回应

3. **`cypher_workflows/steps/naive_text2cypher/evaluate_answer.py`**
   - 在评估数据库输出时记录提示词和回应

4. **`cypher_workflows/text2cypher_retry_check.py`**
   - 在最终答案生成时记录提示词和回应
   - 在每个工作流步骤开始时记录执行情况

5. **`cypher_workflows/naive_text2cypher.py`**
   - 在简单流程的最终答案生成时记录日志

6. **`cypher_workflows/naive_text2cypher_retry.py`**
   - 在重试流程的最终答案生成时记录日志

7. **`app/workflow_service.py`**
   - 在工作流开始、完成和错误时记录日志

### 3. Schema优化

#### 3.1 问题分析
原始的 `graph_store.get_schema_str()` 方法返回的信息过于冗余，包含：
- 节点属性（包含类型信息）
- 关系属性
- 关系结构
- 元数据信息

#### 3.2 优化方案
创建了 `get_optimized_schema()` 函数，特点：
- **精简内容**: 只保留 `node_props` 和 `relationships`
- **过滤Entity**: 自动过滤掉Entity标签（每个实体都有的通用标签）
- **属性简化**: 只保留属性名称，不包含类型信息
- **关系过滤**: 过滤掉包含Entity的关系

#### 3.3 优化效果
- **减少冗余**: 去除了不必要的类型信息和元数据
- **提高可读性**: 更清晰的格式，便于LLM理解
- **过滤噪音**: 自动过滤Entity等通用标签
- **保持完整性**: 保留所有必要的节点和关系信息

### 4. 日志输出示例

#### 4.1 LLM交互日志
```
================================================================================
🔵 LLM交互 #1 - 生成Cypher查询
⏰ 时间: 2024-01-15 14:30:25
================================================================================
📤 发送给LLM的提示词:

--- SYSTEM ---
Given an input question, convert it to a Cypher query...

--- USER ---
You are a seasoned Neo4j expert...

📋 上下文信息:
{
  "question": "糖尿病有哪些症状？",
  "schema": "Node Properties:\nDisease: [name, definition, attributes.cause...]",
  "fewshot_examples": "..."
}
================================================================================

================================================================================
🟢 LLM回应 #1 - 生成Cypher查询
⏰ 时间: 2024-01-15 14:30:28
================================================================================
📥 LLM完整回应:
MATCH (d:Disease {name: '糖尿病'})-[:has_symptom]->(s:Symptom) RETURN s.name
================================================================================
```

#### 4.2 工作流步骤日志
```
============================================================
🔄 工作流步骤: 步骤开始
⏰ 时间: 2024-01-15 14:30:25
💬 消息: 开始生成Cypher查询
📊 数据:
{
  "question": "糖尿病有哪些症状？"
}
============================================================
```

### 5. 系统工作流程

#### 5.1 基本流程
1. **查询主Neo4j数据库schema** → 使用优化的schema函数
2. **用户提出问题q** → 记录到日志
3. **向fewshot Neo4j数据库查询历史CQL** → 记录fewshot示例
4. **整合提示词+schema+问题q+历史cql** → 记录完整提示词
5. **发送给LLM** → 记录LLM交互
6. **LLM形成新的cql** → 记录LLM回应
7. **系统执行cql查询主Neo4j数据库** → 记录查询结果
8. **将查询结果发给LLM** → 记录最终答案生成
9. **LLM做出最终答疑** → 记录完整回应

#### 5.2 日志覆盖的环节
- ✅ 工作流开始和结束
- ✅ 每个步骤的执行情况
- ✅ 发送给LLM的所有提示词
- ✅ LLM的所有完整回应
- ✅ 数据库查询结果
- ✅ 错误和异常情况

### 6. 文件结构

```
app/
├── utils.py                    # 日志工具类和优化schema函数
├── workflow_service.py         # 工作流服务（已添加日志）
└── api_routes.py              # API路由（原有功能）

cypher_workflows/
├── steps/naive_text2cypher/
│   ├── generate_cypher.py     # 生成Cypher（已添加日志）
│   ├── correct_cypher.py      # 修正Cypher（已添加日志）
│   ├── evaluate_answer.py     # 评估答案（已添加日志）
│   └── summarize_answer.py    # 总结答案（提示词模板）
├── text2cypher_retry_check.py # 完整工作流（已添加日志）
├── naive_text2cypher.py       # 简单工作流（已添加日志）
└── naive_text2cypher_retry.py # 重试工作流（已添加日志）

test_schema_simple.py          # Schema优化测试脚本
LLM_interactions.log           # 日志文件（运行时生成）
```

### 7. 使用说明

#### 7.1 启动系统
系统启动后，所有LLM交互都会自动记录到：
- 控制台输出（带格式化的彩色显示）
- `llm_interactions.log` 文件

#### 7.2 查看日志
```bash
# 实时查看日志
tail -f llm_interactions.log

# 查看特定交互
grep "LLM交互 #1" llm_interactions.log
```

#### 7.3 测试Schema优化
```bash
python test_schema_simple.py
```

### 8. 优化效果

#### 8.1 日志功能
- **全面覆盖**: 每个LLM交互都有完整记录
- **易于调试**: 可以追踪每个步骤的执行情况
- **性能监控**: 可以分析LLM响应时间和成功率
- **问题定位**: 快速定位错误和异常

#### 8.2 Schema优化
- **减少token消耗**: 精简的schema减少LLM输入长度
- **提高准确性**: 去除噪音信息，提高Cypher生成准确性
- **更好的可读性**: 清晰的格式便于LLM理解
- **自动过滤**: 智能过滤不需要的标签和关系

### 9. 后续建议

1. **日志分析**: 可以基于日志数据分析LLM性能
2. **错误监控**: 可以设置告警机制监控异常情况
3. **性能优化**: 可以基于日志数据优化提示词
4. **A/B测试**: 可以对比不同提示词的效果

## 总结

通过添加全面的LLM日志功能和优化schema，我们实现了：
1. **完整的可观测性**: 每个环节都有详细记录
2. **高效的调试能力**: 快速定位和解决问题
3. **优化的性能**: 精简的schema提高LLM效率
4. **更好的用户体验**: 清晰的日志输出便于理解系统运行状态

这些改进使得系统更加健壮、可维护，并为后续的优化和扩展奠定了良好的基础。 
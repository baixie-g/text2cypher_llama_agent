# Text2Cypher API 文档

## 概述

Text2Cypher API 是一个基于 FastAPI 构建的 RESTful 服务，提供文本到 Cypher 查询的转换功能，支持多种 LLM 模型和 Neo4j 数据库。

## 基础信息

- **服务地址**: `http://localhost:8003`
- **API 版本**: v1
- **API 基础路径**: `/api/v1`
- **文档地址**: `/api/docs` (Swagger UI)
- **ReDoc 地址**: `/api/redoc`

## 认证

目前 API 不需要认证，但在生产环境中建议添加适当的认证机制。

## 响应格式

所有 API 响应都遵循统一的格式：

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": {...}
}
```

### 错误响应
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "error_message": "错误描述",
  "details": {...}
}
```

## API 端点

### 1. 健康检查

#### GET `/api/v1/health`

检查服务健康状态。

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "4.0.0",
  "components": {
    "llm_service": "healthy",
    "database_service": "healthy",
    "embedding_service": "healthy"
  }
}
```

### 2. 系统状态

#### GET `/api/v1/status`

获取系统运行状态和资源信息。

**响应示例**:
```json
{
  "service_status": "running",
  "llm_count": 1,
  "database_count": 1,
  "workflow_count": 3,
  "memory_usage": {
    "total": 8589934592,
    "available": 4294967296,
    "percent": 50.0,
    "used": 4294967296
  },
  "uptime": "0:02:30"
}
```

### 3. LLM 管理

#### GET `/api/v1/llms`

获取所有可用的 LLM 模型列表。

**响应示例**:
```json
{
  "success": true,
  "message": "Found 1 available LLMs",
  "data": [
    {
      "name": "ark-model",
      "status": "available",
      "provider": "ARK",
      "model_type": "Custom",
      "max_tokens": null,
      "temperature": null
    }
  ]
}
```

#### POST `/api/v1/llms/{llm_name}/test`

测试指定 LLM 的连接。

**响应示例**:
```json
{
  "success": true,
  "message": "LLM 'ark-model' connection test successful",
  "data": {
    "response": "Hello! I'm here to help you."
  }
}
```

### 4. 数据库管理

#### GET `/api/v1/databases`

获取所有可用的数据库列表。

**响应示例**:
```json
{
  "success": true,
  "message": "Found 1 available databases",
  "data": [
    {
      "name": "neo4j",
      "status": "connected",
      "uri": "bolt://localhost:7687",
      "schema_count": 8,
      "node_types": ["Entity", "技术", "组织"],
      "relationship_types": ["掌握技术", "毕业院校", "工作单位", "所在地"]
    }
  ]
}
```

#### POST `/api/v1/databases/{database_name}/test`

测试指定数据库的连接。

**响应示例**:
```json
{
  "success": true,
  "message": "Database 'neo4j' connection test successful",
  "data": {
    "node_count": 150
  }
}
```

#### GET `/api/v1/databases/{database_name}/schema`

获取指定数据库的模式信息。

**响应示例**:
```json
{
  "success": true,
  "message": "Schema for database 'neo4j'",
  "data": {
    "node_types": {
      "Entity": {...},
      "技术": {...},
      "组织": {...}
    },
    "relationships": [
      {
        "start": "Entity",
        "type": "掌握技术",
        "end": "技术"
      }
    ]
  }
}
```

### 5. 工作流管理

#### GET `/api/v1/workflows`

获取所有可用的工作流列表。

**响应示例**:
```json
{
  "success": true,
  "message": "Found 3 available workflows",
  "data": [
    {
      "name": "text2cypher_with_1_retry_and_output_check",
      "type": "text2cypher_with_1_retry_and_output_check",
      "description": "Text2Cypher with retry and output check workflow",
      "parameters": {
        "timeout": 60,
        "max_retries": 1
      }
    }
  ]
}
```

### 6. 工作流执行

#### POST `/api/v1/workflow/execute`

执行单个工作流。

**请求体**:
```json
{
  "llm_name": "ark-model",
  "database_name": "neo4j",
  "workflow_type": "text2cypher_with_1_retry_and_output_check",
  "input_text": "查询所有人员信息",
  "context": {
    "additional_info": "需要包含姓名和职位"
  },
  "timeout": 60
}
```

**响应示例**:
```json
{
  "success": true,
  "events": [],
  "result": {
    "cypher_query": "MATCH (p:Entity) RETURN p.name, p.position",
    "explanation": "查询所有人员的基本信息"
  },
  "execution_time": 2.5
}
```

#### POST `/api/v1/workflow/execute/stream`

流式执行工作流（Server-Sent Events）。

**请求体**: 同单个执行

**响应格式** (Server-Sent Events):
```
data: {"event_type": "start", "label": "开始执行", "message": "正在初始化工作流...", "timestamp": "2024-01-01T12:00:00"}

data: {"event_type": "processing", "label": "处理中", "message": "正在生成Cypher查询...", "timestamp": "2024-01-01T12:00:01"}

data: {"event_type": "result", "label": "完成", "message": "工作流执行成功", "result": {...}, "timestamp": "2024-01-01T12:00:02"}
```

#### POST `/api/v1/workflow/execute/batch`

批量执行工作流。

**请求体**:
```json
{
  "requests": [
    {
      "llm_name": "ark-model",
      "database_name": "neo4j",
      "workflow_type": "text2cypher_with_1_retry_and_output_check",
      "input_text": "查询所有人员信息",
      "timeout": 60
    },
    {
      "llm_name": "ark-model",
      "database_name": "neo4j",
      "workflow_type": "naive_text2cypher",
      "input_text": "查询技术专家",
      "timeout": 60
    }
  ],
  "max_concurrent": 5
}
```

**响应示例**:
```json
{
  "total_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "results": [
    {
      "success": true,
      "events": [],
      "result": {...},
      "execution_time": 2.5
    },
    {
      "success": true,
      "events": [],
      "result": {...},
      "execution_time": 1.8
    }
  ]
}
```

### 7. 统计信息

#### GET `/api/v1/statistics`

获取系统统计信息。

**响应示例**:
```json
{
  "total_executions": 100,
  "successful_executions": 95,
  "failed_executions": 5,
  "average_execution_time": 2.3,
  "popular_workflows": [
    {"name": "text2cypher_with_1_retry_and_output_check", "count": 60},
    {"name": "naive_text2cypher", "count": 30},
    {"name": "naive_text2cypher_with_1_retry", "count": 10}
  ],
  "popular_llms": [
    {"name": "ark-model", "count": 100}
  ],
  "daily_stats": []
}
```

#### POST `/api/v1/statistics/reset`

重置统计信息。

**响应示例**:
```json
{
  "success": true,
  "message": "Statistics reset successfully"
}
```

## 工作流类型

### 1. text2cypher_with_1_retry_and_output_check

最完整的工作流，包含重试机制和输出检查。

**特点**:
- 支持重试机制
- 输出验证和检查
- 错误处理和恢复
- 最稳定的执行结果

### 2. naive_text2cypher

基础的工作流，直接转换文本到Cypher。

**特点**:
- 简单直接
- 执行速度快
- 适合简单查询

### 3. naive_text2cypher_with_1_retry

带重试机制的基础工作流。

**特点**:
- 基础功能 + 重试
- 平衡性能和稳定性

## 错误代码

| 错误代码 | 描述 |
|---------|------|
| WORKFLOW_NOT_FOUND | 工作流不存在 |
| LLM_NOT_FOUND | LLM模型不存在 |
| DATABASE_NOT_FOUND | 数据库不存在 |
| CONNECTION_ERROR | 连接错误 |
| TIMEOUT_ERROR | 超时错误 |
| VALIDATION_ERROR | 参数验证错误 |
| EXECUTION_ERROR | 执行错误 |

## 使用示例

### cURL 示例

#### 健康检查
```bash
curl -X GET "http://localhost:8003/api/v1/health"
```

#### 执行工作流
```bash
curl -X POST "http://localhost:8003/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_name": "ark-model",
    "database_name": "neo4j",
    "workflow_type": "text2cypher_with_1_retry_and_output_check",
    "input_text": "查询所有人员信息",
    "timeout": 60
  }'
```

#### 流式执行
```bash
curl -X POST "http://localhost:8003/api/v1/workflow/execute/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_name": "ark-model",
    "database_name": "neo4j",
    "workflow_type": "text2cypher_with_1_retry_and_output_check",
    "input_text": "查询所有人员信息",
    "timeout": 60
  }'
```

### Python 示例

```python
import requests
import json

# 基础配置
BASE_URL = "http://localhost:8003/api/v1"

# 健康检查
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 执行工作流
workflow_data = {
    "llm_name": "ark-model",
    "database_name": "neo4j",
    "workflow_type": "text2cypher_with_1_retry_and_output_check",
    "input_text": "查询所有人员信息",
    "timeout": 60
}

response = requests.post(f"{BASE_URL}/workflow/execute", json=workflow_data)
result = response.json()
print(result)
```

## 性能优化建议

1. **批量处理**: 对于大量查询，使用批量执行接口
2. **超时设置**: 根据查询复杂度设置合适的超时时间
3. **并发控制**: 避免同时发送过多请求
4. **缓存**: 对于重复查询，考虑在客户端实现缓存
5. **连接复用**: 使用HTTP连接池

## 监控和日志

- 使用 `/api/v1/status` 监控系统状态
- 使用 `/api/v1/statistics` 查看执行统计
- 检查服务日志了解详细执行信息

## 故障排除

### 常见问题

1. **连接超时**: 检查网络连接和服务状态
2. **LLM错误**: 验证LLM配置和API密钥
3. **数据库错误**: 检查Neo4j连接和权限
4. **内存不足**: 监控系统资源使用情况

### 调试步骤

1. 执行健康检查确认服务状态
2. 测试LLM和数据库连接
3. 查看详细错误信息
4. 检查系统日志

## 版本历史

- **v4.0.0**: 完整API重构，支持多种LLM和数据库
- **v3.x**: 基础功能实现
- **v2.x**: 原型版本
- **v1.x**: 初始版本 
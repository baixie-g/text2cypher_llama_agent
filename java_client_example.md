# Text2Cypher API Java 客户端调用示例

## 概述

本文档提供了使用Java调用Text2Cypher API的完整示例，包括各种API端点的调用方法和示例代码。

## 基础配置

### Maven依赖

```xml
<dependencies>
    <!-- HTTP客户端 -->
    <dependency>
        <groupId>org.apache.httpcomponents</groupId>
        <artifactId>httpclient</artifactId>
        <version>4.5.13</version>
    </dependency>
    
    <!-- JSON处理 -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.15.2</version>
    </dependency>
    
    <!-- 异步HTTP客户端 -->
    <dependency>
        <groupId>org.asynchttpclient</groupId>
        <artifactId>async-http-client</artifactId>
        <version>2.12.3</version>
    </dependency>
</dependencies>
```

### 基础配置类

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;

public class Text2CypherClient {
    private static final String BASE_URL = "http://localhost:8003/api/v1";
    private final CloseableHttpClient httpClient;
    private final ObjectMapper objectMapper;
    
    public Text2CypherClient() {
        this.httpClient = HttpClients.createDefault();
        this.objectMapper = new ObjectMapper();
    }
    
    public void close() throws IOException {
        httpClient.close();
    }
}
```

## API调用示例

### 1. 健康检查

```java
public class HealthCheckExample {
    
    public void checkHealth() throws Exception {
        String url = BASE_URL + "/health";
        
        HttpGet request = new HttpGet(url);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                System.out.println("服务健康状态: " + responseBody);
            } else {
                System.err.println("健康检查失败: " + response.getStatusLine());
            }
        }
    }
}
```

### 2. 获取系统状态

```java
public class SystemStatusExample {
    
    public void getSystemStatus() throws Exception {
        String url = BASE_URL + "/status";
        
        HttpGet request = new HttpGet(url);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                JsonNode jsonNode = objectMapper.readTree(responseBody);
                System.out.println("服务状态: " + jsonNode.get("service_status").asText());
                System.out.println("可用LLM数量: " + jsonNode.get("llm_count").asInt());
                System.out.println("可用数据库数量: " + jsonNode.get("database_count").asInt());
                System.out.println("可用工作流数量: " + jsonNode.get("workflow_count").asInt());
            }
        }
    }
}
```

### 3. 获取可用LLM列表

```java
public class LLMExample {
    
    public List<String> getAvailableLLMs() throws Exception {
        String url = BASE_URL + "/llms";
        
        HttpGet request = new HttpGet(url);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                JsonNode jsonNode = objectMapper.readTree(responseBody);
                JsonNode data = jsonNode.get("data");
                
                List<String> llmNames = new ArrayList<>();
                for (JsonNode llm : data) {
                    llmNames.add(llm.get("name").asText());
                }
                return llmNames;
            }
        }
        return Collections.emptyList();
    }
}
```

### 4. 获取可用数据库列表

```java
public class DatabaseExample {
    
    public List<String> getAvailableDatabases() throws Exception {
        String url = BASE_URL + "/databases";
        
        HttpGet request = new HttpGet(url);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                JsonNode jsonNode = objectMapper.readTree(responseBody);
                JsonNode data = jsonNode.get("data");
                
                List<String> databaseNames = new ArrayList<>();
                for (JsonNode db : data) {
                    databaseNames.add(db.get("name").asText());
                }
                return databaseNames;
            }
        }
        return Collections.emptyList();
    }
}
```

### 5. 获取可用工作流列表

```java
public class WorkflowExample {
    
    public List<String> getAvailableWorkflows() throws Exception {
        String url = BASE_URL + "/workflows";
        
        HttpGet request = new HttpGet(url);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                JsonNode jsonNode = objectMapper.readTree(responseBody);
                JsonNode data = jsonNode.get("data");
                
                List<String> workflowNames = new ArrayList<>();
                for (JsonNode workflow : data) {
                    workflowNames.add(workflow.get("name").asText());
                }
                return workflowNames;
            }
        }
        return Collections.emptyList();
    }
}
```

### 6. 执行工作流

```java
public class WorkflowExecutionExample {
    
    public void executeWorkflow(String llmName, String databaseName, String workflowType, String inputText) throws Exception {
        String url = BASE_URL + "/workflow/execute";
        
        // 构建请求体
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("llm_name", llmName);
        requestBody.put("database_name", databaseName);
        requestBody.put("workflow_type", workflowType);
        requestBody.put("input_text", inputText);
        requestBody.put("timeout", 60);
        
        String jsonBody = objectMapper.writeValueAsString(requestBody);
        
        HttpPost request = new HttpPost(url);
        request.setHeader("Content-Type", "application/json");
        request.setEntity(new StringEntity(jsonBody));
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                JsonNode jsonNode = objectMapper.readTree(responseBody);
                boolean success = jsonNode.get("success").asBoolean();
                double executionTime = jsonNode.get("execution_time").asDouble();
                
                if (success) {
                    System.out.println("工作流执行成功，耗时: " + executionTime + "秒");
                    System.out.println("结果: " + jsonNode.get("result").toString());
                } else {
                    System.err.println("工作流执行失败");
                    JsonNode events = jsonNode.get("events");
                    for (JsonNode event : events) {
                        System.err.println("错误: " + event.get("message").asText());
                    }
                }
            } else {
                System.err.println("请求失败: " + response.getStatusLine());
            }
        }
    }
}
```

### 7. 流式执行工作流

```java
public class StreamingWorkflowExample {
    
    public void executeWorkflowStream(String llmName, String databaseName, String workflowType, String inputText) throws Exception {
        String url = BASE_URL + "/workflow/execute/stream";
        
        // 构建请求体
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("llm_name", llmName);
        requestBody.put("database_name", databaseName);
        requestBody.put("workflow_type", workflowType);
        requestBody.put("input_text", inputText);
        requestBody.put("timeout", 60);
        
        String jsonBody = objectMapper.writeValueAsString(requestBody);
        
        HttpPost request = new HttpPost(url);
        request.setHeader("Content-Type", "application/json");
        request.setEntity(new StringEntity(jsonBody));
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            InputStream inputStream = response.getEntity().getContent();
            BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
            
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.startsWith("data: ")) {
                    String jsonData = line.substring(6);
                    JsonNode event = objectMapper.readTree(jsonData);
                    
                    String eventType = event.get("event_type").asText();
                    String message = event.get("message").asText();
                    
                    System.out.println("事件类型: " + eventType + ", 消息: " + message);
                    
                    if ("result".equals(eventType)) {
                        System.out.println("最终结果: " + event.get("result").toString());
                        break;
                    } else if ("error".equals(eventType)) {
                        System.err.println("执行错误: " + message);
                        break;
                    }
                }
            }
        }
    }
}
```

### 8. 批量执行工作流

```java
public class BatchWorkflowExample {
    
    public void executeBatchWorkflows(List<WorkflowRequest> requests) throws Exception {
        String url = BASE_URL + "/workflow/execute/batch";
        
        // 构建批量请求体
        Map<String, Object> batchRequest = new HashMap<>();
        batchRequest.put("requests", requests);
        batchRequest.put("max_concurrent", 5);
        
        String jsonBody = objectMapper.writeValueAsString(batchRequest);
        
        HttpPost request = new HttpPost(url);
        request.setHeader("Content-Type", "application/json");
        request.setEntity(new StringEntity(jsonBody));
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                JsonNode jsonNode = objectMapper.readTree(responseBody);
                int totalCount = jsonNode.get("total_count").asInt();
                int successCount = jsonNode.get("success_count").asInt();
                int failedCount = jsonNode.get("failed_count").asInt();
                
                System.out.println("批量执行完成:");
                System.out.println("总请求数: " + totalCount);
                System.out.println("成功数: " + successCount);
                System.out.println("失败数: " + failedCount);
                
                JsonNode results = jsonNode.get("results");
                for (int i = 0; i < results.size(); i++) {
                    JsonNode result = results.get(i);
                    boolean success = result.get("success").asBoolean();
                    System.out.println("请求 " + (i + 1) + ": " + (success ? "成功" : "失败"));
                }
            }
        }
    }
    
    public static class WorkflowRequest {
        public String llm_name;
        public String database_name;
        public String workflow_type;
        public String input_text;
        public Map<String, Object> context;
        public Integer timeout;
        
        // 构造函数和getter/setter方法
    }
}
```

### 9. 获取统计信息

```java
public class StatisticsExample {
    
    public void getStatistics() throws Exception {
        String url = BASE_URL + "/statistics";
        
        HttpGet request = new HttpGet(url);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                JsonNode jsonNode = objectMapper.readTree(responseBody);
                
                System.out.println("统计信息:");
                System.out.println("总执行次数: " + jsonNode.get("total_executions").asInt());
                System.out.println("成功执行次数: " + jsonNode.get("successful_executions").asInt());
                System.out.println("失败执行次数: " + jsonNode.get("failed_executions").asInt());
                System.out.println("平均执行时间: " + jsonNode.get("average_execution_time").asDouble() + "秒");
                
                // 热门工作流
                JsonNode popularWorkflows = jsonNode.get("popular_workflows");
                System.out.println("热门工作流:");
                for (JsonNode workflow : popularWorkflows) {
                    System.out.println("  " + workflow.get("name").asText() + ": " + workflow.get("count").asInt() + "次");
                }
                
                // 热门LLM
                JsonNode popularLLMs = jsonNode.get("popular_llms");
                System.out.println("热门LLM:");
                for (JsonNode llm : popularLLMs) {
                    System.out.println("  " + llm.get("name").asText() + ": " + llm.get("count").asInt() + "次");
                }
            }
        }
    }
}
```

### 10. 测试连接

```java
public class ConnectionTestExample {
    
    public void testLLMConnection(String llmName) throws Exception {
        String url = BASE_URL + "/llms/" + llmName + "/test";
        
        HttpPost request = new HttpPost(url);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                JsonNode jsonNode = objectMapper.readTree(responseBody);
                System.out.println("LLM连接测试成功: " + jsonNode.get("message").asText());
                System.out.println("测试响应: " + jsonNode.get("data").get("response").asText());
            } else {
                System.err.println("LLM连接测试失败: " + response.getStatusLine());
            }
        }
    }
    
    public void testDatabaseConnection(String databaseName) throws Exception {
        String url = BASE_URL + "/databases/" + databaseName + "/test";
        
        HttpPost request = new HttpPost(url);
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            String responseBody = EntityUtils.toString(response.getEntity());
            
            if (response.getStatusLine().getStatusCode() == 200) {
                JsonNode jsonNode = objectMapper.readTree(responseBody);
                System.out.println("数据库连接测试成功: " + jsonNode.get("message").asText());
                System.out.println("节点数量: " + jsonNode.get("data").get("node_count").asInt());
            } else {
                System.err.println("数据库连接测试失败: " + response.getStatusLine());
            }
        }
    }
}
```

## 完整示例

```java
public class Text2CypherAPIClient {
    private static final String BASE_URL = "http://localhost:8003/api/v1";
    private final CloseableHttpClient httpClient;
    private final ObjectMapper objectMapper;
    
    public Text2CypherAPIClient() {
        this.httpClient = HttpClients.createDefault();
        this.objectMapper = new ObjectMapper();
    }
    
    public static void main(String[] args) {
        Text2CypherAPIClient client = new Text2CypherAPIClient();
        
        try {
            // 1. 健康检查
            client.checkHealth();
            
            // 2. 获取系统状态
            client.getSystemStatus();
            
            // 3. 获取可用资源
            List<String> llms = client.getAvailableLLMs();
            List<String> databases = client.getAvailableDatabases();
            List<String> workflows = client.getAvailableWorkflows();
            
            System.out.println("可用LLM: " + llms);
            System.out.println("可用数据库: " + databases);
            System.out.println("可用工作流: " + workflows);
            
            // 4. 执行工作流
            if (!llms.isEmpty() && !databases.isEmpty() && !workflows.isEmpty()) {
                client.executeWorkflow(
                    llms.get(0),
                    databases.get(0),
                    workflows.get(0),
                    "查询所有人员信息"
                );
            }
            
            // 5. 获取统计信息
            client.getStatistics();
            
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            try {
                client.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }
    
    // 实现上述所有方法...
}
```

## 错误处理

```java
public class ErrorHandler {
    
    public static void handleApiError(CloseableHttpResponse response) throws Exception {
        String responseBody = EntityUtils.toString(response.getEntity());
        JsonNode errorNode = objectMapper.readTree(responseBody);
        
        String errorCode = errorNode.get("error_code").asText();
        String errorMessage = errorNode.get("error_message").asText();
        
        System.err.println("API错误:");
        System.err.println("错误代码: " + errorCode);
        System.err.println("错误消息: " + errorMessage);
        
        if (errorNode.has("details")) {
            System.err.println("错误详情: " + errorNode.get("details").toString());
        }
    }
}
```

## 注意事项

1. **连接管理**: 确保正确关闭HTTP连接以避免资源泄漏
2. **错误处理**: 始终检查HTTP状态码并处理可能的错误
3. **超时设置**: 为长时间运行的工作流设置适当的超时时间
4. **并发控制**: 批量执行时注意控制并发数量
5. **JSON处理**: 使用ObjectMapper正确处理JSON序列化和反序列化
6. **流式处理**: 对于流式响应，需要正确处理Server-Sent Events格式
7. **安全性**: 在生产环境中，应该使用HTTPS和适当的认证机制 
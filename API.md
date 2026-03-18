# API 文档

> Enterprise QA Assistant REST API 参考文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 前缀**: `/api/v1`
- **认证**: 暂无 (Phase 1)

## 健康检查

### GET /health

基础健康检查。

**响应示例**:
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### GET /health/detail

详细健康检查，包含各依赖服务状态。

**响应示例**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "checks": {
    "postgres": {
      "status": "healthy",
      "latency_ms": 5.23
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 1.12
    },
    "milvus": {
      "status": "healthy",
      "latency_ms": 10.45
    }
  }
}
```

---

## 对话接口

### POST /api/v1/chat/completions

创建对话 (同步模式)。

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message | string | 是 | 用户消息 (1-10000 字符) |
| session_id | string | 否 | 会话 ID，不传则创建新会话 |
| collection | string | 否 | 知识库集合，默认 "default" |
| stream | boolean | 否 | 是否流式返回，默认 false |

**请求示例**:
```json
{
  "message": "公司的年假制度是什么？",
  "session_id": null,
  "collection": "hr_docs",
  "stream": false
}
```

**响应示例**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "根据公司制度，年假天数根据工龄不同而不同... [来源1]",
  "citations": [
    {
      "doc_id": "doc_abc123",
      "doc_title": "hr_policy.md",
      "content": "工龄1-5年: 5天年假...",
      "chunk_index": 0,
      "relevance_score": 0.85
    }
  ],
  "confidence": 0.85,
  "model_used": "gpt-4o",
  "fallback_used": false,
  "latency_ms": 1234.56,
  "tokens_used": 500
}
```

### POST /api/v1/chat/completions/stream

创建对话 (流式模式)。

**请求体**: 同 `POST /api/v1/chat/completions`

**响应**: Server-Sent Events (SSE)

**事件类型**:

| 事件 | 说明 | data 示例 |
|------|------|-----------|
| status | 处理状态 | `"processing"` |
| citation | 引用信息 | `[{"doc_id": "...", ...}]` |
| token | 回答片段 | `"这是"` |
| done | 完成信息 | `{"confidence": 0.85, ...}` |
| error | 错误信息 | `"error message"` |

**响应示例**:
```
event: status
data: "processing"

event: token
data: "根据"

event: token
data: "公司"

event: done
data: {"confidence": 0.85, "model_used": "gpt-4o", "tokens_used": 500}
```

---

## 文档管理

### POST /api/v1/documents/upload

上传文档。

**请求表单**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 上传的文件 |
| collection | string | 否 | 知识库集合，默认 "default" |

**支持的文件类型**: `.pdf`, `.docx`, `.md`, `.txt`

**响应示例**:
```json
{
  "doc_id": "doc_abc123456789",
  "filename": "hr_policy.md",
  "status": "processing"
}
```

### GET /api/v1/documents/{doc_id}

获取文档信息。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| doc_id | string | 文档 ID |

**响应示例**:
```json
{
  "doc_id": "doc_abc123456789",
  "filename": "hr_policy.md",
  "file_type": ".md",
  "file_size": 1024,
  "collection": "hr_docs",
  "status": "completed",
  "chunk_count": 5,
  "error_message": null,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:01:00Z"
}
```

**文档状态**:

| 状态 | 说明 |
|------|------|
| processing | 处理中 |
| completed | 已完成 |
| failed | 失败 |

### GET /api/v1/documents/

获取文档列表。

**查询参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| collection | string | "default" | 知识库集合 |
| page | integer | 1 | 页码 |
| page_size | integer | 20 | 每页数量 |

**响应示例**:
```json
{
  "documents": [
    {
      "doc_id": "doc_abc123456789",
      "filename": "hr_policy.md",
      "file_type": ".md",
      "file_size": 1024,
      "collection": "hr_docs",
      "status": "completed",
      "chunk_count": 5,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:01:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## 错误响应

### 错误格式

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "消息内容不能为空",
    "details": [
      {
        "field": "message",
        "message": "message is required"
      }
    ]
  },
  "request_id": "req_abc123"
}
```

### 错误代码

| HTTP 状态码 | 错误代码 | 说明 |
|-------------|----------|------|
| 400 | INVALID_REQUEST | 请求参数无效 |
| 404 | NOT_FOUND | 资源不存在 |
| 422 | VALIDATION_ERROR | 数据验证失败 |
| 429 | RATE_LIMITED | 请求过于频繁 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |

---

## 速率限制

暂无 (Phase 1)

---

## 注意事项

1. **Session 管理**: Session ID 在首次创建对话时生成，后续请求携带相同的 session_id 可以保持对话上下文。

2. **文档处理**: 文档上传后异步处理，通过 `GET /api/v1/documents/{doc_id}` 查询处理状态。

3. **引用来源**: RAG 回答中的 `[来源X]` 标记对应 `citations` 数组中的项。

4. **降级模式**: 当 RAG 检索质量不足或出错时，系统会自动降级到轻量模型 (FALLBACK_LLM_MODEL) 生成回答。

---

## 变更日志

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2024-01-15 | Phase 1 MVP 初版 |

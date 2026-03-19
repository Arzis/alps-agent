# Enterprise QA Assistant - Claude Code 开发指南

> **项目**: 企业级智能问答助手 (Enterprise QA Assistant)
> **版本**: Phase 1 MVP
> **文档维护**: 每次重大更新后同步此文件

------

## 1. 项目概述

### 1.1 项目定位

构建企业级智能问答助手平台，以 **RAG（检索增强生成）** 为核心，支持：
- 多智能体协作（LangGraph 编排）
- 工具调用（MCP 协议）
- 人工审查、可中断/恢复对话
- FastAPI 高并发服务接口
- RAG 降级至 Codex 兜底

### 1.2 系统架构

```
客户端层 → API 网关层 → FastAPI 服务层 → 对话编排引擎(LangGraph)
                                              ↓
                    ┌─────────────────────────┼─────────────────────────┐
                    ↓                         ↓                         ↓
              RAG 引擎层                记忆系统                  工具/MCP 层
              (LlamaIndex)          (短期/长期/语义)            (内置+外部)
                    ↓                         ↓                         ↓
              Milvus(向量)           PostgreSQL/Redis           MinIO(文档)
```

### 1.3 技术栈

| 层级 | 技术 |
|------|------|
| API 框架 | FastAPI 0.115+ / Uvicorn / SSE |
| 对话编排 | LangGraph / LangChain |
| RAG 引擎 | LlamaIndex |
| 向量数据库 | Milvus |
| 结构化数据 | PostgreSQL 16 / asyncpg |
| 缓存/会话 | Redis Stack |
| 文档存储 | MinIO |
| 异步任务 | ARQ |
| 日志 | Structlog |
| 数据验证 | Pydantic |

------

## 2. 项目结构

```
d:\arz\alps-agent\
├── src/
│   ├── api/                    # FastAPI 应用层
│   │   ├── main.py            # 应用入口、生命周期管理
│   │   ├── dependencies.py    # 依赖注入
│   │   ├── routers/           # API 路由
│   │   │   ├── health.py      # 健康检查
│   │   │   ├── chat.py        # 对话接口
│   │   │   └── documents.py   # 文档管理接口
│   │   └── middlewares/       # 中间件
│   │       ├── logging_middleware.py
│   │       └── error_handler.py
│   │
│   ├── core/                   # 核心业务层
│   │   ├── orchestrator/      # 对话编排 (LangGraph)
│   │   │   ├── engine.py      # 编排引擎
│   │   │   ├── state.py       # 状态定义
│   │   │   ├── graph.py       # 图构建
│   │   │   └── nodes/         # 节点实现
│   │   │       ├── query_understanding.py
│   │   │       ├── rag_agent.py
│   │   │       ├── codex_fallback.py
│   │   │       ├── quality_gate.py
│   │   │       └── response_synthesizer.py
│   │   │
│   │   ├── memory/            # 记忆系统
│   │   │   ├── short_term.py  # 短期记忆 (Redis)
│   │   │   └── manager.py     # 记忆管理器
│   │   │
│   │   └── rag/              # RAG 管道
│   │       ├── ingestion/    # 文档摄取
│   │       │   ├── parser.py  # 文档解析
│   │       │   ├── chunker.py # 分块策略
│   │       │   └── pipeline.py # 摄取管道
│   │       ├── retrieval/    # 检索
│   │       │   ├── dense.py   # 密集检索
│   │       │   └── retriever.py
│   │       └── synthesis/    # 答案合成
│   │           └── synthesizer.py
│   │
│   ├── infra/                 # 基础设施层
│   │   ├── config/
│   │   │   └── settings.py   # Pydantic Settings 配置
│   │   ├── database/
│   │   │   ├── postgres.py   # PostgreSQL 连接池
│   │   │   ├── redis_client.py
│   │   │   └── milvus_client.py
│   │   ├── logging/
│   │   │   └── logger.py     # Structlog 配置
│   │   └── queue/
│   │       └── task_queue.py # ARQ 任务队列
│   │
│   └── schemas/              # 数据模型 (Pydantic)
│       ├── common.py        # 通用响应模型
│       ├── chat.py          # 对话模型
│       └── document.py      # 文档模型
│
├── tests/                    # 测试目录
│   ├── unit/                # 单元测试
│   ├── integration/         # 集成测试
│   └── e2e/                 # 端到端测试
│
├── scripts/                  # 脚本
│   └── init_db.py           # 数据库初始化
│
├── docker/                   # Docker 配置
│   ├── docker-compose.yml
│   └── configs/
│       ├── postgres/
│       └── redis/
│
├── pyproject.toml           # Poetry 依赖
├── Makefile                 # 常用命令
└── .env.example            # 环境变量模板
```

------

## 3. 开发准则

### 3.1 代码规范

#### 中文注释要求
- **所有新增代码必须使用中文注释**
- 注释内容：描述「为什么这么做」而非「做了什么」
- 类和函数的 docstring 使用中文

```python
class ShortTermMemory:
    """
    短期记忆模块

    基于 Redis List 存储会话历史消息，支持 TTL 自动过期。
    用于在多轮对话中维护上下文上下文。

    设计考虑：
    - 使用 Redis List 保证消息顺序
    - TTL 自动清理过期会话，节省内存
    """

    async def add_message(self, session_id: str, role: MessageRole, content: str):
        """添加消息到会话历史

        Args:
            session_id: 会话唯一标识
            role: 消息角色 (user/assistant)
            content: 消息内容

        Note:
            消息以 JSON 格式存储，便于扩展元数据
        """
```

#### 类型注解
- 所有函数必须有类型注解
- 使用 Pydantic 模型进行请求/响应验证
- 复杂类型定义使用 TypeAlias

#### 日志规范
- 使用 structlog 进行结构化日志
- 必填字段：session_id, operation
- 日志级别：INFO（正常流程）、WARNING（可恢复错误）、ERROR（需处理错误）

```python
logger.info(
    "document_processing_started",
    doc_id=doc_id,
    file_type=file_type,
    collection=collection,
)

logger.error(
    "milvus_connection_failed",
    error=str(e),
    host=settings.MILVUS_HOST,
)
```

### 3.2 API 设计规范

#### URL 命名
- 使用小写 + 下划线
- 资源复数形式
- 版本前缀：`/api/v1`

```
GET    /api/v1/chat/sessions              # 获取会话列表
POST   /api/v1/chat/completions          # 创建对话
POST   /api/v1/chat/completions/stream   # 流式对话
GET    /api/v1/chat/sessions/{id}        # 获取会话详情
DELETE /api/v1/chat/sessions/{id}        # 删除会话

POST   /api/v1/documents/upload          # 上传文档
GET    /api/v1/documents/{doc_id}       # 获取文档信息
GET    /api/v1/documents                 # 文档列表

GET    /health                           # 健康检查
GET    /health/detail                    # 详细健康检查
```

#### 响应格式
```python
# 成功响应 (src/schemas/common.py)
class BaseResponse(BaseModel):
    """通用响应格式"""
    success: bool = True
    message: str = "操作成功"
    data: Any = None
    request_id: str | None = None

# 错误响应
class ErrorResponse(BaseModel):
    """错误响应格式"""
    success: bool = False
    error: ErrorDetail
    request_id: str | None = None
```

#### HTTP 状态码
| 场景 | 状态码 |
|------|--------|
| 成功 | 200 / 201 |
| 参数错误 | 400 |
| 未认证 | 401 |
| 无权限 | 403 |
| 资源不存在 | 404 |
| 限流 | 429 |
| 服务器错误 | 500 |

### 3.3 数据库规范

#### PostgreSQL
- 表名：小写 + 下划线
- 索引命名：`idx_{表名}_{字段名}`
- 使用 asyncpg 异步驱动
- 连接池管理见 `src/infra/database/postgres.py`

```sql
-- 示例表结构
CREATE TABLE conversation_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    title VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON conversation_sessions(user_id);
CREATE INDEX idx_sessions_created_at ON conversation_sessions(created_at);
```

#### Redis
- Key 命名：`{模块}:{功能}:{标识}`
- 会话历史：`memory:short_term:{session_id}`
- TTL：会话默认 24 小时

```
memory:short_term:550e8400-e29b-41d4-a716-446655440000
```

#### Milvus
- Collection：`knowledge_base`（可配置）
- 向量维度：3072（text-embedding-3-large）
- 索引类型：HNSW

### 3.4 配置管理

所有配置通过 `src/infra/config/settings.py` 的 Pydantic Settings 管理：

```python
class Settings(BaseSettings):
    """应用配置"""

    # 应用
    APP_NAME: str = "Enterprise QA Assistant"
    APP_VERSION: str = "0.1.0"
    ENV: Literal["development", "staging", "production"] = "development"

    # LLM
    OPENAI_API_KEY: str
    PRIMARY_LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 3072

    # RAG
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5
    RAG_MIN_CONFIDENCE: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = True
```

------

## 4. Phase 1 实施进度

### 4.1 当前进度

| 周次 | 模块 | 进度 | 状态 |
|------|------|------|------|
| Week 1 | 项目基础设施搭建 | 100% | 🟢 完成 |
| Week 2 | FastAPI 服务层 & 基础对话 | 100% | 🟢 完成 |
| Week 3 | LlamaIndex RAG 管道 | 0% | 🔴 待开始 |
| Week 4 | LangGraph 对话编排 | 0% | 🔴 待开始 |
| Week 5 | 集成联调 & 异步文档处理 | 0% | 🔴 待开始 |
| Week 6 | 测试 & 稳定化 | 0% | 🔴 待开始 |

### 4.2 Week 3 任务清单

```
3.1 文档解析器
    [ ] 3.1.1 创建 src/core/rag/ingestion/parser.py
          - PDF 解析 (pypdf)
          - Word 解析 (python-docx)
          - Markdown 解析
          - 纯文本解析

3.2 分块策略
    [ ] 3.2.1 创建 src/core/rag/ingestion/chunker.py
          - 递归字符分块 (RecursiveCharacterTextSplitter)
          - chunk_size / chunk_overlap 配置

3.3 Embedding & Milvus 向量索引
    [ ] 3.3.1 创建 src/core/rag/ingestion/pipeline.py
          - LlamaIndex IngestionPipeline
          - 转换链: Parser → Chunker → Embedding → Storage
    [ ] 3.3.2 实现 Milvus VectorStore 集成

3.4 基础检索 (Dense Retrieval)
    [ ] 3.4.1 创建 src/core/rag/retrieval/dense.py
    [ ] 3.4.2 创建 src/core/rag/retrieval/retriever.py

3.5 答案合成
    [ ] 3.5.1 创建 src/core/rag/synthesis/synthesizer.py
```

### 4.3 Week 4 任务清单

```
4.1 状态定义 & 基础图结构
    [ ] 4.1.1 创建 src/core/orchestrator/state.py
    [ ] 4.1.2 创建 src/core/orchestrator/graph.py

4.2 查询理解节点
    [ ] 4.2.1 创建 src/core/orchestrator/nodes/query_understanding.py

4.3 RAG Agent 节点
    [ ] 4.3.1 创建 src/core/orchestrator/nodes/rag_agent.py

4.4 Codex 降级兜底节点
    [ ] 4.4.1 创建 src/core/orchestrator/nodes/codex_fallback.py

4.5 基础置信度评估
    [ ] 4.5.1 创建 src/core/orchestrator/nodes/quality_gate.py

4.6 响应合成节点
    [ ] 4.6.1 创建 src/core/orchestrator/nodes/response_synthesizer.py

4.7 编排引擎封装
    [ ] 4.7.1 创建 src/core/orchestrator/engine.py
```

------

## 5. 开发工作流

### 5.1 任务认领与开发

1. **查看任务跟踪**: 阅读 `Phase-1-任务进度跟踪.md`
2. **认领任务**: 在任务列表对应任务前添加 `👤 {你的名字}`
3. **开发**: 按设计文档实现功能
4. **自测**: 运行单元测试验证
5. **提交**: 详细 commit 信息

### 5.2 Commit 信息格式

```
<类型>: <简短描述>

<可选的详细说明>

<可选的任务关联>
```

**类型**:
- `feat`: 新功能
- `fix`: 错误修复
- `refactor`: 重构
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具变更

**示例**:
```
feat: 实现文档解析器支持 PDF 和 DOCX

- 添加 pypdf 依赖用于 PDF 解析
- 添加 python-docx 依赖用于 Word 解析
- 实现 ParserFactory 统一接口
- 支持文件大小和类型校验

关联任务: #3.1.1
```

### 5.3 测试要求

```bash
# 运行所有测试
make test

# 运行单元测试
make test UNIT=1

# 运行集成测试
make test INTEGRATION=1

# 运行 E2E 测试
make test E2E=1

# 生成覆盖率报告
make test-cov
```

**覆盖率要求**: 核心业务模块 ≥ 80%

### 5.4 代码检查

```bash
# 代码格式化和导入排序
make format

# Lint 检查
make lint

# 类型检查
make typecheck

# 完整检查 (format + lint + typecheck)
make check
```

------

## 6. 常用命令

```bash
# 环境搭建
make setup          # 安装依赖 (poetry install)

# 开发运行
make dev            # 开发模式启动 (poetry run uvicorn)
make up             # 启动 Docker 服务
make down           # 停止 Docker 服务
make logs           # 查看 Docker 日志

# 测试
make test           # 运行测试
make test-cov       # 运行测试 + 覆盖率

# 代码质量
make format         # 代码格式化
make lint           # Lint 检查
make typecheck      # 类型检查
make check          # 完整检查

# 后台任务
make worker         # 启动 ARQ Worker

# 清理
make clean          # 清理缓存和构建产物
```

------

## 7. 环境变量

参考 `.env.example`:

```bash
# === 应用 ===
APP_NAME="Enterprise QA Assistant"
ENV="development"

# === OpenAI API ===
OPENAI_API_KEY=your-openai-api-key-here
PRIMARY_LLM_MODEL="gpt-4o"
EMBEDDING_MODEL="text-embedding-3-large"
EMBEDDING_DIMENSION=3072

# === PostgreSQL ===
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432
POSTGRES_USER="user"
POSTGRES_PASSWORD="pass"
POSTGRES_DB="qa_assistant"

# === Redis ===
REDIS_HOST="localhost"
REDIS_PORT=6379

# === Milvus ===
MILVUS_HOST="localhost"
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME="knowledge_base"

# === RAG ===
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=5
RAG_MIN_CONFIDENCE=0.7
```

------

## 8. 故障排查

### 8.1 Docker 服务无法启动

```bash
# 检查 Docker 状态
docker ps -a

# 查看服务日志
docker compose -f docker/docker-compose.yml logs postgres
docker compose -f docker/docker-compose.yml logs redis
docker compose -f docker/docker-compose.yml logs milvus

# 重启服务
docker compose -f docker/docker-compose.yml restart
```

### 8.2 数据库连接问题

```python
# PostgreSQL 连接测试
poetry run python -c "
import asyncpg
import os
async def test():
    conn = await asyncpg.connect(
        host='localhost', port=5432,
        user='user', password='pass',
        database='qa_assistant'
    )
    print(await conn.fetchval('SELECT 1'))
    await conn.close()
import asyncio; asyncio.run(test())
"
```

### 8.3 Milvus 连接问题

```python
# Milvus 连接测试
poetry run python -c "
from pymilvus import MilvusClient
client = MilvusClient(uri='http://localhost:19530')
print(client.list_collections())
"
```

------

## 9. 联系方式与资源

- **设计文档**: `设计文档.md`
- **Phase 1 任务跟踪**: `Phase-1-任务进度跟踪.md`
- **API 文档**: 启动服务后访问 `http://localhost:8000/docs`

------

*最后更新**: 2026-03-18*

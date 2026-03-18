# Phase 1 MVP 实施进度跟踪

> **目标**: 搭建可运行的核心对话 + 基础 RAG 系统
> **周期**: 4-6 周
> **交付物**: 可通过 API 进行多轮对话、支持文档上传与 RAG 问答、Codex 降级兜底的完整服务

------

## 总体进度看板

| 周次 | 模块 | 进度 | 状态 |
|------|------|------|------|
| Week 1 | 项目基础设施搭建 | 100% | 🟢 Completed |
| Week 2 | FastAPI 服务层 & 基础对话 | 100% | 🟢 Completed |
| Week 3 | LlamaIndex RAG 管道 | 0% | 🔴 Pending |
| Week 4 | LangGraph 对话编排 | 0% | 🔴 Pending |
| Week 5 | 集成联调 & 异步文档处理 | 0% | 🔴 Pending |
| Week 6 | 测试 & 稳定化 | 0% | 🔴 Pending |

------

## Week 1：项目基础设施搭建

### 1.1 项目脚手架 & 规范制定

- [x] **1.1.1** 创建目录结构（Phase 1 精简版）
  - `src/api/` - FastAPI 应用层
  - `src/core/` - 核心业务层
  - `src/infra/` - 基础设施层
  - `src/schemas/` - 数据模型
  - `tests/` - 测试目录
  - `scripts/` - 脚本目录
  - `docker/` - Docker 配置

- [x] **1.1.2** 创建 `pyproject.toml` 依赖配置文件
  - FastAPI / Uvicorn / SSE
  - LangChain / LangGraph / LlamaIndex
  - asyncpg / redis / pymilvus
  - structlog / pydantic / arq
  - pypdf / python-docx

- [x] **1.1.3** 创建 `Makefile` 常用命令
  - `setup` / `dev` / `up` / `down`
  - `test` / `lint` / `format` / `clean`
  - `worker` / `logs`

- [x] **1.1.4** 创建 `.gitignore` 和 `.env.example`

### 1.2 Docker Compose 开发环境

- [x] **1.2.1** 创建 `docker/docker-compose.yml`
  - PostgreSQL 16 (结构化数据)
  - Redis Stack (缓存/会话)
  - Milvus Standalone (向量数据库)
  - etcd (Milvus 依赖)
  - MinIO (对象存储)

- [x] **1.2.2** 创建 `docker/configs/redis/redis.conf`

### 1.3 配置管理 & 基础中间件

- [x] **1.3.1** 创建 `src/infra/config/settings.py` (Pydantic Settings)
  - 应用配置 (APP_NAME / VERSION / ENV)
  - LLM 配置 (OpenAI API Key / 模型 / Temperature)
  - PostgreSQL / Redis / Milvus 连接配置
  - RAG 配置 (chunk_size / top_k / threshold)
  - 并发控制配置

- [x] **1.3.2** 创建 `src/infra/logging/logger.py` (Structlog 配置)
  - JSON 格式日志
  - 请求上下文绑定

### 1.4 数据库初始化

- [x] **1.4.1** 创建 `docker/configs/postgres/init.sql`
  - `conversation_sessions` 表
  - `conversation_messages` 表
  - `documents` 表

- [x] **1.4.2** 创建 `scripts/init_db.py`
  - Milvus Collection 创建
  - 向量索引配置 (HNSW)
  - 连接验证

------

## Week 2：FastAPI 服务层 & 基础对话

### 2.1 API 接口开发

- [x] **2.1.1** 创建 `src/infra/database/postgres.py` (连接池管理)
- [x] **2.1.2** 创建 `src/infra/database/redis_client.py` (连接管理)
- [x] **2.1.3** 创建 `src/infra/database/milvus_client.py` (客户端初始化)

- [x] **2.1.4** 创建 `src/schemas/common.py` (基础响应模型)
- [x] **2.1.5** 创建 `src/schemas/chat.py` (对话请求/响应模型)
- [x] **2.1.6** 创建 `src/schemas/document.py` (文档模型)

- [x] **2.1.7** 创建 `src/api/routers/health.py` (健康检查接口)
- [x] **2.1.8** 创建 `src/api/routers/chat.py` (对话接口 - 同步)
- [x] **2.1.9** 创建 `src/api/routers/documents.py` (文档上传接口)

### 2.2 SSE 流式响应

- [x] **2.2.1** 在 `chat.py` 中实现 `/completions/stream` 端点
- [x] **2.2.2** 实现 `EventSourceResponse` 流式事件生成器
- [x] **2.2.3** 支持 `token` / `citation` / `status` / `done` / `error` 事件类型

### 2.3 短期记忆 (Redis 会话管理)

- [x] **2.3.1** 创建 `src/core/memory/short_term.py`
  - Redis List 存储会话历史
  - TTL 管理 (24小时)
  - 消息追加/读取

- [x] **2.3.2** 创建 `src/core/memory/manager.py`
  - 多层记忆统一接口
  - 上下文加载/保存

### 2.4 基础日志模块

- [x] **2.4.1** 创建 `src/api/middlewares/logging_middleware.py`
- [x] **2.4.2** 创建 `src/api/middlewares/error_handler.py`
- [x] **2.4.3** 创建 `src/api/main.py` (应用入口 & 生命周期)

------

## Week 3：LlamaIndex RAG 管道

### 3.1 文档解析器

- [ ] **3.1.1** 创建 `src/core/rag/ingestion/parser.py`
  - PDF 解析 (pypdf)
  - Word 解析 (python-docx)
  - Markdown 解析
  - 纯文本解析

### 3.2 分块策略

- [ ] **3.2.1** 创建 `src/core/rag/ingestion/chunker.py`
  - 递归字符分块 (RecursiveCharacterTextSplitter)
  - chunk_size / chunk_overlap 配置

### 3.3 Embedding & Milvus 向量索引

- [ ] **3.3.1** 创建 `src/core/rag/ingestion/pipeline.py`
  - LlamaIndex IngestionPipeline
  - 转换链: Parser → Chunker → Embedding → Storage

- [ ] **3.3.2** 实现 Milvus VectorStore 集成
  - Collection 管理
  - 向量插入

### 3.4 基础检索 (Dense Retrieval)

- [ ] **3.4.1** 创建 `src/core/rag/retrieval/dense.py`
  - MilvusDenseRetriever
  - top_k 检索

- [ ] **3.4.2** 创建 `src/core/rag/retrieval/retriever.py`
  - 检索器统一接口

### 3.5 答案合成

- [ ] **3.5.1** 创建 `src/core/rag/synthesis/synthesizer.py`
  - Context 加 LLM 生成答案
  - 引用提取

------

## Week 4：LangGraph 对话编排

### 4.1 状态定义 & 基础图结构

- [ ] **4.1.1** 创建 `src/core/orchestrator/state.py`
  - ConversationState 定义
  - 消息 / 上下文 / 意图 / RAG 结果

- [ ] **4.1.2** 创建 `src/core/orchestrator/graph.py`
  - StateGraph 构建
  - 节点注册
  - 边定义 (START → END)

### 4.2 查询理解节点

- [ ] **4.2.1** 创建 `src/core/orchestrator/nodes/query_understanding.py`
  - 查询改写 (Query Rewriting)
  - 意图识别 (Intent Detection)

### 4.3 RAG Agent 节点

- [ ] **4.3.1** 创建 `src/core/orchestrator/nodes/rag_agent.py`
  - 调用检索器
  - 调用答案合成器
  - 返回结果

### 4.4 Codex 降级兜底节点

- [ ] **4.4.1** 创建 `src/core/orchestrator/nodes/codex_fallback.py`
  - 检测 RAG 质量不足
  - 降级到轻量模型回答

### 4.5 基础置信度评估

- [ ] **4.5.1** 创建 `src/core/orchestrator/nodes/quality_gate.py`
  - 置信度评分
  - 阈值判断
  - 降级/通过/拒绝路由

### 4.6 响应合成节点

- [ ] **4.6.1** 创建 `src/core/orchestrator/nodes/response_synthesizer.py`
  - 最终答案组装
  - 引用格式化

### 4.7 编排引擎封装

- [ ] **4.7.1** 创建 `src/core/orchestrator/engine.py`
  - 封装 LangGraph 调用
  - 初始化 orchestrator

------

## Week 5：集成联调 & 异步文档处理

### 5.1 全链路串联

- [ ] **5.1.1** 串联 Chat API → Orchestrator → RAG → 响应
- [ ] **5.1.2** 串联 Document API → Ingestion Pipeline → Milvus
- [ ] **5.1.3** 联调 SSE 流式输出

### 5.2 异步文档处理队列 (ARQ)

- [ ] **5.2.1** 创建 `src/infra/queue/task_queue.py`
  - ARQ WorkerSettings
  - 文档处理任务

- [ ] **5.2.2** 在 Document API 中集成后台任务
  - `background_tasks.add_task()`

### 5.3 错误处理 & 重试机制

- [ ] **5.3.1** 为 LLM 调用添加 tenacity 重试
- [ ] **5.3.2** 为数据库操作添加错误处理
- [ ] **5.3.3** 实现优雅降级

### 5.4 基础健康检查 & 指标

- [ ] **5.4.1** 完善 `/health/detail` 端点
- [ ] **5.4.2** 添加基础 Prometheus 指标 (可选)

------

## Week 6：测试 & 稳定化

### 6.1 单元测试

- [ ] **6.1.1** 创建 `tests/conftest.py` (测试夹具)
- [ ] **6.1.2** 创建 `tests/unit/test_chunker.py`
- [ ] **6.1.3** 创建 `tests/unit/test_retriever.py`
- [ ] **6.1.4** 创建 `tests/unit/test_memory.py`
- [ ] **6.1.5** 创建 `tests/unit/test_orchestrator.py`

### 6.2 集成测试

- [ ] **6.2.1** 创建 `tests/integration/test_rag_pipeline.py`
- [ ] **6.2.2** 创建 `tests/integration/test_chat_api.py`
- [ ] **6.2.3** 创建 `tests/integration/test_document_api.py`

### 6.3 端到端测试

- [ ] **6.3.1** 创建 `tests/e2e/test_full_conversation.py`
  - 上传文档 → 提问 → 验证回答

### 6.4 文档 & Phase 2 准备

- [ ] **6.4.1** 完善 `README.md`
  - 项目介绍
  - 快速开始
  - API 文档链接

- [ ] **6.4.2** 创建 `API.md` (接口文档)
- [ ] **6.4.3** 评审 Phase 1 遗留问题
- [ ] **6.4.4** 制定 Phase 2 计划

------

## 任务统计

| 周次 | 任务数 | 完成数 | 进度 |
|------|--------|--------|------|
| Week 1 | 10 | 10 | 100% |
| Week 2 | 17 | 17 | 100% |
| Week 3 | 8 | 0 | 0% |
| Week 4 | 8 | 0 | 0% |
| Week 5 | 7 | 0 | 0% |
| Week 6 | 7 | 0 | 0% |
| **总计** | **55** | **27** | **49%** |

------

## 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-03-18 | 初始化 Phase 1 任务跟踪文档 |
| 2026-03-18 | Week 1 完成：项目基础设施搭建 |
| 2026-03-18 | Week 2 完成：FastAPI 服务层 & 基础对话 |

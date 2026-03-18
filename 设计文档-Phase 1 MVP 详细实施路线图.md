# Phase 1 MVP 详细实施路线图

> **目标**: 搭建可运行的核心对话 + 基础 RAG 系统
> **周期**: 4-6 周
> **交付物**: 可通过 API 进行多轮对话、支持文档上传与 RAG 问答、Codex 降级兜底的完整服务

------

## 一、Phase 1 任务分解总览

text



```
Phase 1 MVP (4-6周)
│
├── Week 1: 项目基础设施搭建
│   ├── 1.1 项目脚手架 & 规范制定
│   ├── 1.2 Docker Compose 开发环境
│   ├── 1.3 配置管理 & 基础中间件
│   └── 1.4 数据库初始化 (PostgreSQL + Redis + Milvus)
│
├── Week 2: FastAPI 服务层 & 基础对话
│   ├── 2.1 API 接口开发 (Chat + Document)
│   ├── 2.2 SSE 流式响应
│   ├── 2.3 短期记忆 (Redis 会话管理)
│   └── 2.4 基础日志模块 (Structlog)
│
├── Week 3: LlamaIndex RAG 管道
│   ├── 3.1 文档解析器 (PDF/Word/Markdown)
│   ├── 3.2 分块策略 (递归分块)
│   ├── 3.3 Embedding & Milvus 向量索引
│   └── 3.4 基础检索 (Dense Retrieval)
│
├── Week 4: LangGraph 对话编排
│   ├── 4.1 状态定义 & 基础图结构
│   ├── 4.2 查询理解节点
│   ├── 4.3 RAG Agent 节点
│   ├── 4.4 Codex 降级兜底节点
│   └── 4.5 基础置信度评估
│
├── Week 5: 集成联调 & 异步文档处理
│   ├── 5.1 全链路串联
│   ├── 5.2 异步文档处理队列 (ARQ)
│   ├── 5.3 错误处理 & 重试机制
│   └── 5.4 基础健康检查 & 指标
│
└── Week 6: 测试 & 稳定化
    ├── 6.1 单元测试 & 集成测试
    ├── 6.2 端到端测试
    ├── 6.3 性能基准测试
    └── 6.4 文档 & Phase 2 准备
```

------

## 二、Week 1：项目基础设施搭建

### 1.1 项目脚手架 & 规范制定

#### 目录结构（Phase 1 精简版）

text



```
enterprise-qa-assistant/
├── docker/
│   ├── docker-compose.yml          # 开发环境编排
│   ├── Dockerfile.api              # API服务镜像
│   ├── Dockerfile.worker           # 异步Worker镜像
│   └── configs/
│       ├── milvus/
│       │   └── embedEtcd.yaml
│       └── redis/
│           └── redis.conf
├── src/
│   ├── __init__.py
│   ├── api/                        # FastAPI 应用层
│   │   ├── __init__.py
│   │   ├── main.py                 # 应用入口
│   │   ├── dependencies.py         # 依赖注入
│   │   ├── middlewares/
│   │   │   ├── __init__.py
│   │   │   ├── logging_middleware.py
│   │   │   ├── error_handler.py
│   │   │   └── trace.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── chat.py             # 对话接口
│   │       ├── documents.py        # 文档管理
│   │       └── health.py           # 健康检查
│   ├── core/                       # 核心业务层
│   │   ├── __init__.py
│   │   ├── orchestrator/           # LangGraph编排
│   │   │   ├── __init__.py
│   │   │   ├── graph.py            # 主图定义
│   │   │   ├── state.py            # 状态定义
│   │   │   ├── engine.py           # 编排引擎(封装调用)
│   │   │   └── nodes/
│   │   │       ├── __init__.py
│   │   │       ├── query_understanding.py
│   │   │       ├── rag_agent.py
│   │   │       ├── codex_fallback.py
│   │   │       ├── quality_gate.py
│   │   │       └── response_synthesizer.py
│   │   ├── rag/                    # RAG引擎
│   │   │   ├── __init__.py
│   │   │   ├── ingestion/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── parser.py       # 文档解析
│   │   │   │   ├── chunker.py      # 分块策略
│   │   │   │   └── pipeline.py     # 摄取管道
│   │   │   ├── retrieval/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── dense.py        # 稠密检索
│   │   │   │   └── retriever.py    # 检索器统一接口
│   │   │   └── synthesis/
│   │   │       ├── __init__.py
│   │   │       └── synthesizer.py  # 答案合成
│   │   └── memory/                 # 记忆系统
│   │       ├── __init__.py
│   │       ├── short_term.py       # 短期记忆
│   │       └── manager.py          # 记忆管理
│   ├── infra/                      # 基础设施层
│   │   ├── __init__.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py         # 全局配置
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── postgres.py         # PG连接管理
│   │   │   ├── milvus_client.py    # Milvus连接
│   │   │   └── redis_client.py     # Redis连接
│   │   ├── logging/
│   │   │   ├── __init__.py
│   │   │   └── logger.py           # Structlog配置
│   │   └── queue/
│   │       ├── __init__.py
│   │       └── task_queue.py       # ARQ任务队列
│   └── schemas/                    # 数据模型
│       ├── __init__.py
│       ├── chat.py
│       ├── document.py
│       └── common.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # 测试夹具
│   ├── unit/
│   │   ├── test_chunker.py
│   │   ├── test_retriever.py
│   │   └── test_memory.py
│   ├── integration/
│   │   ├── test_rag_pipeline.py
│   │   ├── test_chat_api.py
│   │   └── test_document_api.py
│   └── e2e/
│       └── test_full_conversation.py
├── scripts/
│   ├── init_db.py                  # 数据库初始化
│   ├── seed_data.py                # 测试数据填充
│   └── test_upload.py              # 文档上传测试
├── pyproject.toml
├── .env.example
├── .gitignore
├── Makefile                        # 常用命令快捷方式
└── README.md
```

#### pyproject.toml

toml



```
[tool.poetry]
name = "enterprise-qa-assistant"
version = "0.1.0"
description = "Enterprise Intelligent QA Assistant with RAG"
python = "^3.11"

[tool.poetry.dependencies]
python = "^3.11"

# === Web框架 ===
fastapi = "^0.115.0"
uvicorn = { version = "^0.32.0", extras = ["standard"] }
uvloop = "^0.21.0"
httptools = "^0.6.0"
sse-starlette = "^2.1.0"       # SSE流式响应
python-multipart = "^0.0.12"   # 文件上传

# === LLM框架 ===
langchain-core = "^0.3.0"
langchain-openai = "^0.2.0"
langgraph = "^0.2.0"
langgraph-checkpoint-postgres = "^2.0.0"

# === RAG引擎 ===
llama-index-core = "^0.11.0"
llama-index-readers-file = "^0.3.0"
llama-index-embeddings-openai = "^0.2.0"
# llama-index-embeddings-huggingface = "^0.3.0"  # 本地Embedding可选

# === 数据库 ===
asyncpg = "^0.30.0"            # PostgreSQL异步驱动
redis = { version = "^5.0.0", extras = ["hiredis"] }
pymilvus = "^2.4.0"            # Milvus客户端

# === 基础设施 ===
pydantic = "^2.9.0"
pydantic-settings = "^2.6.0"
structlog = "^24.4.0"          # 结构化日志
python-json-logger = "^2.0.0"
arq = "^0.26.0"               # 异步任务队列
tenacity = "^9.0.0"           # 重试库
orjson = "^3.10.0"            # 高性能JSON

# === 文档解析 ===
pypdf = "^5.0.0"              # PDF解析
python-docx = "^1.1.0"        # Word解析
markdown = "^3.7"              # Markdown解析

# === 开发工具 ===
[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
pytest-cov = "^5.0.0"
httpx = "^0.27.0"             # 测试HTTP客户端
ruff = "^0.7.0"               # Linter + Formatter
mypy = "^1.13.0"
pre-commit = "^4.0.0"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "ANN", "B", "A", "SIM"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

#### Makefile

Makefile



```
.PHONY: help setup dev up down logs test lint clean

help:  ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## 首次项目初始化
	poetry install
	cp .env.example .env
	docker compose -f docker/docker-compose.yml up -d postgres redis milvus-standalone etcd minio
	sleep 10
	poetry run python scripts/init_db.py

dev:  ## 启动开发服务器(热重载)
	poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

up:  ## 启动所有Docker服务
	docker compose -f docker/docker-compose.yml up -d

down:  ## 停止所有Docker服务
	docker compose -f docker/docker-compose.yml down

logs:  ## 查看API服务日志
	docker compose -f docker/docker-compose.yml logs -f api

test:  ## 运行测试
	poetry run pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:  ## 运行单元测试
	poetry run pytest tests/unit/ -v

test-integration:  ## 运行集成测试
	poetry run pytest tests/integration/ -v

lint:  ## 代码检查
	poetry run ruff check src/ tests/
	poetry run ruff format --check src/ tests/
	poetry run mypy src/

format:  ## 代码格式化
	poetry run ruff format src/ tests/
	poetry run ruff check --fix src/ tests/

clean:  ## 清理
	docker compose -f docker/docker-compose.yml down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

worker:  ## 启动异步Worker
	poetry run arq src.infra.queue.task_queue.WorkerSettings
```

### 1.2 配置管理

Python



```
# src/infra/config/settings.py

from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr
from functools import lru_cache


class Settings(BaseSettings):
    """全局配置 - 从环境变量/.env加载"""

    # === 应用配置 ===
    APP_NAME: str = "Enterprise QA Assistant"
    APP_VERSION: str = "0.1.0"
    ENV: str = "development"  # development / staging / production
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # === 服务端口 ===
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1  # 开发环境1个worker, 生产环境根据CPU设置

    # === LLM 配置 ===
    OPENAI_API_KEY: SecretStr
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    
    # 主力模型
    PRIMARY_LLM_MODEL: str = "gpt-4o"
    PRIMARY_LLM_TEMPERATURE: float = 0.1
    PRIMARY_LLM_MAX_TOKENS: int = 4096
    
    # 降级模型 (Codex / 轻量模型)
    FALLBACK_LLM_MODEL: str = "gpt-4o-mini"
    FALLBACK_LLM_TEMPERATURE: float = 0.0
    
    # Embedding 模型
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 3072

    # === PostgreSQL ===
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: SecretStr = SecretStr("pass")
    POSTGRES_DB: str = "qa_assistant"
    POSTGRES_POOL_MIN: int = 5
    POSTGRES_POOL_MAX: int = 20

    @property
    def POSTGRES_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    @property
    def POSTGRES_ASYNC_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    # === Redis ===
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: SecretStr | None = None
    REDIS_POOL_MAX: int = 50

    @property
    def REDIS_URL(self) -> str:
        password_part = ""
        if self.REDIS_PASSWORD:
            password_part = f":{self.REDIS_PASSWORD.get_secret_value()}@"
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # === Milvus ===
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_TOKEN: str = ""
    MILVUS_DB_NAME: str = "default"
    MILVUS_COLLECTION_NAME: str = "knowledge_base"

    @property
    def MILVUS_URI(self) -> str:
        return f"http://{self.MILVUS_HOST}:{self.MILVUS_PORT}"

    # === RAG 配置 ===
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 10          # 召回数量
    RAG_SIMILARITY_THRESHOLD: float = 0.7  # 相似度阈值

    # === 对话配置 ===
    MAX_CONVERSATION_TURNS: int = 20  # 最大对话轮数
    SHORT_TERM_MEMORY_TTL: int = 86400  # 短期记忆TTL(秒) = 24小时
    MAX_SHORT_TERM_MESSAGES: int = 20  # 短期记忆最大消息数

    # === 质量控制 ===
    CONFIDENCE_THRESHOLD_PASS: float = 0.7     # 直接通过阈值
    CONFIDENCE_THRESHOLD_FALLBACK: float = 0.4  # 降级阈值

    # === 并发控制 ===
    MAX_LLM_CONCURRENT: int = 20         # LLM最大并发
    MAX_EMBEDDING_CONCURRENT: int = 50   # Embedding最大并发
    REQUEST_TIMEOUT: int = 120           # 请求超时(秒)
    LLM_TIMEOUT: int = 60               # LLM调用超时(秒)

    # === 日志 ===
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json / console

    # === 文件上传 ===
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".md", ".txt"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """获取全局配置单例"""
    return Settings()
```

Bash



```
# .env.example

# === 应用 ===
ENV=development
DEBUG=true

# === LLM ===
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
PRIMARY_LLM_MODEL=gpt-4o
FALLBACK_LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-large

# === PostgreSQL ===
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=qa_assistant

# === Redis ===
REDIS_HOST=localhost
REDIS_PORT=6379

# === Milvus ===
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 1.3 Docker Compose 开发环境

YAML



```
# docker/docker-compose.yml

services:
  # ============================================================
  # PostgreSQL - 结构化数据 + LangGraph Checkpoint
  # ============================================================
  postgres:
    image: postgres:16-alpine
    container_name: qa-postgres
    environment:
      POSTGRES_DB: qa_assistant
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./configs/postgres/init.sql:/docker-entrypoint-initdb.d/01-init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d qa_assistant"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - qa-network

  # ============================================================
  # Redis Stack - 缓存 + 会话 + (Phase2: 语义缓存向量搜索)
  # ============================================================
  redis:
    image: redis/redis-stack:latest
    container_name: qa-redis
    ports:
      - "6379:6379"
      - "8001:8001"    # RedisInsight Web UI
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - qa-network

  # ============================================================
  # Milvus Standalone - 向量数据库
  # ============================================================
  etcd:
    image: quay.io/coreos/etcd:v3.5.16
    container_name: qa-etcd
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - etcd_data:/etcd
    command: >
      etcd
      -advertise-client-urls=http://127.0.0.1:2379
      -listen-client-urls=http://0.0.0.0:2379
      --data-dir /etcd
    healthcheck:
      test: ["CMD", "etcdctl", "endpoint", "health"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - qa-network

  minio:
    image: minio/minio:RELEASE.2024-09-13T20-26-02Z
    container_name: qa-minio
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"    # MinIO Console
    volumes:
      - minio_data:/minio_data
    command: minio server /minio_data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - qa-network

  milvus:
    image: milvusdb/milvus:v2.4.13-hotfix
    container_name: qa-milvus
    command: ["milvus", "run", "standalone"]
    security_opt:
      - seccomp:unconfined
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
      MINIO_ACCESS_KEY_ID: minioadmin
      MINIO_SECRET_ACCESS_KEY: minioadmin
    ports:
      - "19530:19530"
      - "9091:9091"     # Metrics
    volumes:
      - milvus_data:/var/lib/milvus
    depends_on:
      etcd:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9091/healthz"]
      interval: 30s
      timeout: 20s
      retries: 3
    networks:
      - qa-network

volumes:
  postgres_data:
  redis_data:
  etcd_data:
  minio_data:
  milvus_data:

networks:
  qa-network:
    driver: bridge
```

### 1.4 数据库初始化

SQL



```
-- docker/configs/postgres/init.sql

-- 创建LangFuse数据库 (Phase 2 用)
-- CREATE DATABASE langfuse;

-- 对话历史表
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id              VARCHAR(64) PRIMARY KEY,
    user_id         VARCHAR(64) NOT NULL,
    title           VARCHAR(512),
    status          VARCHAR(32) DEFAULT 'active',  -- active / completed / archived
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_sessions_user_id ON conversation_sessions(user_id);
CREATE INDEX idx_sessions_status ON conversation_sessions(status);
CREATE INDEX idx_sessions_created_at ON conversation_sessions(created_at DESC);

-- 对话消息表
CREATE TABLE IF NOT EXISTS conversation_messages (
    id              BIGSERIAL PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL REFERENCES conversation_sessions(id),
    role            VARCHAR(16) NOT NULL,  -- user / assistant / system
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    -- RAG相关
    citations       JSONB DEFAULT '[]',
    confidence      FLOAT,
    model_used      VARCHAR(64),
    tokens_used     INTEGER,
    latency_ms      INTEGER,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_session_id ON conversation_messages(session_id);
CREATE INDEX idx_messages_created_at ON conversation_messages(created_at);

-- 文档管理表
CREATE TABLE IF NOT EXISTS documents (
    id              VARCHAR(64) PRIMARY KEY,
    collection      VARCHAR(128) NOT NULL,
    filename        VARCHAR(512) NOT NULL,
    file_type       VARCHAR(32) NOT NULL,
    file_size       BIGINT,
    file_path       VARCHAR(1024),          -- MinIO/本地路径
    status          VARCHAR(32) DEFAULT 'uploaded',  -- uploaded / processing / completed / failed
    chunk_count     INTEGER DEFAULT 0,
    error_message   TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_documents_collection ON documents(collection);
CREATE INDEX idx_documents_status ON documents(status);

-- LangGraph Checkpoint 表 (langgraph-checkpoint-postgres 自动创建, 但预留)
-- 由 AsyncPostgresSaver.setup() 自动创建
```

Python



```
# scripts/init_db.py

"""数据库初始化脚本 - 创建Milvus Collection + 验证连接"""

import asyncio
from pymilvus import MilvusClient

from src.infra.config.settings import get_settings


async def init_milvus():
    """初始化Milvus Collection"""
    settings = get_settings()
    client = MilvusClient(uri=settings.MILVUS_URI)

    collection_name = settings.MILVUS_COLLECTION_NAME

    # 检查是否已存在
    if client.has_collection(collection_name):
        print(f"Collection '{collection_name}' already exists, skipping.")
        return

    # 创建 Collection
    from pymilvus import CollectionSchema, FieldSchema, DataType

    schema = CollectionSchema(
        fields=[
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema("doc_id", DataType.VARCHAR, max_length=64),
            FieldSchema("chunk_index", DataType.INT64),
            FieldSchema("content", DataType.VARCHAR, max_length=65535),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),
            FieldSchema("doc_title", DataType.VARCHAR, max_length=512),
            FieldSchema("collection", DataType.VARCHAR, max_length=128),
            FieldSchema("created_at", DataType.INT64),
        ],
        description="Knowledge base document chunks",
    )

    client.create_collection(
        collection_name=collection_name,
        schema=schema,
    )

    # 创建向量索引
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="HNSW",
        metric_type="COSINE",
        params={"M": 16, "efConstruction": 256},
    )
    index_params.add_index(field_name="doc_id", index_type="Trie")
    index_params.add_index(field_name="collection", index_type="Trie")

    client.create_index(
        collection_name=collection_name,
        index_params=index_params,
    )

    # 加载Collection到内存
    client.load_collection(collection_name)

    print(f"Collection '{collection_name}' created and loaded successfully.")


async def verify_connections():
    """验证所有数据库连接"""
    settings = get_settings()

    # PostgreSQL
    import asyncpg
    try:
        conn = await asyncpg.connect(settings.POSTGRES_URL)
        version = await conn.fetchval("SELECT version()")
        print(f"✅ PostgreSQL connected: {version[:50]}")
        await conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")

    # Redis
    import redis.asyncio as aioredis
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        pong = await r.ping()
        print(f"✅ Redis connected: ping={pong}")
        await r.aclose()
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

    # Milvus
    try:
        client = MilvusClient(uri=settings.MILVUS_URI)
        collections = client.list_collections()
        print(f"✅ Milvus connected: collections={collections}")
    except Exception as e:
        print(f"❌ Milvus connection failed: {e}")


async def main():
    print("=" * 60)
    print("Initializing databases...")
    print("=" * 60)

    await verify_connections()
    print()
    await init_milvus()

    print()
    print("=" * 60)
    print("Initialization completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
```

------

## 三、Week 2：FastAPI 服务层 & 基础对话

### 2.1 应用入口 & 生命周期管理

Python



```
# src/infra/database/postgres.py

import asyncpg
from src.infra.config.settings import get_settings

_pool: asyncpg.Pool | None = None


async def init_postgres_pool() -> asyncpg.Pool:
    """创建PostgreSQL连接池"""
    global _pool
    settings = get_settings()
    _pool = await asyncpg.create_pool(
        dsn=settings.POSTGRES_URL,
        min_size=settings.POSTGRES_POOL_MIN,
        max_size=settings.POSTGRES_POOL_MAX,
        command_timeout=60,
    )
    return _pool


async def get_postgres_pool() -> asyncpg.Pool:
    """获取连接池"""
    if _pool is None:
        raise RuntimeError("PostgreSQL pool not initialized")
    return _pool


async def close_postgres_pool():
    """关闭连接池"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
```

Python



```
# src/infra/database/redis_client.py

import redis.asyncio as aioredis
from src.infra.config.settings import get_settings

_redis: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis:
    """创建Redis连接"""
    global _redis
    settings = get_settings()
    _redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=settings.REDIS_POOL_MAX,
    )
    # 验证连接
    await _redis.ping()
    return _redis


async def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized")
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
```

Python



```
# src/infra/database/milvus_client.py

from pymilvus import MilvusClient as _MilvusClient
from src.infra.config.settings import get_settings

_client: _MilvusClient | None = None


def init_milvus() -> _MilvusClient:
    """初始化Milvus客户端"""
    global _client
    settings = get_settings()
    _client = _MilvusClient(
        uri=settings.MILVUS_URI,
        token=settings.MILVUS_TOKEN or None,
        db_name=settings.MILVUS_DB_NAME,
    )
    return _client


def get_milvus() -> _MilvusClient:
    if _client is None:
        raise RuntimeError("Milvus client not initialized")
    return _client
```

Python



```
# src/api/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infra.config.settings import get_settings
from src.infra.database.postgres import init_postgres_pool, close_postgres_pool
from src.infra.database.redis_client import init_redis, close_redis
from src.infra.database.milvus_client import init_milvus
from src.infra.logging.logger import setup_logging
from src.api.middlewares.error_handler import register_exception_handlers
from src.api.middlewares.logging_middleware import RequestLoggingMiddleware
from src.api.routers import chat, documents, health

import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()

    # === 启动 ===
    setup_logging(settings)
    logger.info("application_starting", env=settings.ENV)

    # 初始化数据库连接
    pg_pool = await init_postgres_pool()
    logger.info("postgres_connected", pool_size=settings.POSTGRES_POOL_MAX)

    redis_client = await init_redis()
    logger.info("redis_connected")

    milvus_client = init_milvus()
    logger.info("milvus_connected")

    # 初始化LLM (验证API Key)
    from src.core.orchestrator.engine import init_orchestrator
    orchestrator = await init_orchestrator(
        pg_pool=pg_pool,
        redis_client=redis_client,
        milvus_client=milvus_client,
        settings=settings,
    )
    app.state.orchestrator = orchestrator
    logger.info("orchestrator_initialized")

    logger.info("application_started", version=settings.APP_VERSION)

    yield

    # === 关闭 ===
    logger.info("application_shutting_down")
    await close_postgres_pool()
    await close_redis()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # === 中间件 ===
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else ["https://your-domain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # === 异常处理 ===
    register_exception_handlers(app)

    # === 路由注册 ===
    app.include_router(health.router)
    app.include_router(chat.router, prefix=settings.API_PREFIX)
    app.include_router(documents.router, prefix=settings.API_PREFIX)

    return app


app = create_app()
```

### 2.2 中间件

Python



```
# src/api/middlewares/logging_middleware.py

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import structlog

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 - 记录每个请求的关键信息"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # 绑定到structlog上下文
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "request_completed",
                status_code=response.status_code,
                latency_ms=round(elapsed_ms, 2),
            )

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"

            return response

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "request_failed",
                error=str(e),
                error_type=type(e).__name__,
                latency_ms=round(elapsed_ms, 2),
            )
            raise
```

Python



```
# src/api/middlewares/error_handler.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import structlog

logger = structlog.get_logger()


class AppError(Exception):
    """应用异常基类"""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class RateLimitError(AppError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429, error_code="RATE_LIMITED")


class LLMError(AppError):
    def __init__(self, message: str = "LLM service error"):
        super().__init__(message, status_code=502, error_code="LLM_ERROR")


def register_exception_handlers(app: FastAPI):
    """注册全局异常处理器"""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning(
            "app_error",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        logger.warning("validation_error", errors=exc.errors())
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred" if not app.debug else str(exc),
                }
            },
        )
```

### 2.3 数据模型（Schemas）

Python



```
# src/schemas/common.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class BaseResponse(BaseModel):
    """基础响应"""
    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """错误响应"""
    error: dict[str, Any]
```

Python



```
# src/schemas/chat.py

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    session_id: str | None = Field(None, description="会话ID, 不传则创建新会话")
    collection: str = Field("default", description="知识库collection名称")
    stream: bool = Field(False, description="是否流式返回")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "公司的年假制度是什么？",
                    "session_id": None,
                    "collection": "hr_docs",
                    "stream": False,
                }
            ]
        }
    }


class CitationItem(BaseModel):
    """引用信息"""
    doc_id: str
    doc_title: str
    content: str = Field(description="引用的原文片段")
    chunk_index: int | None = None
    relevance_score: float


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """对话消息"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    message: str = Field(description="助手回复内容")
    citations: list[CitationItem] = Field(default_factory=list, description="引用来源")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="回答置信度")
    model_used: str = Field("", description="使用的模型")
    fallback_used: bool = Field(False, description="是否使用了降级模型")
    latency_ms: float = Field(0.0, description="处理耗时(毫秒)")
    tokens_used: int = Field(0, description="消耗的token数")


class StreamEvent(BaseModel):
    """SSE流式事件"""
    event: str  # token / citation / status / done / error
    data: str


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    title: str | None = None
    message_count: int = 0
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class ConversationHistory(BaseModel):
    """对话历史"""
    session_id: str
    messages: list[ChatMessage]
    total_count: int
```

Python



```
# src/schemas/document.py

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    doc_id: str
    filename: str
    status: DocumentStatus = DocumentStatus.UPLOADED
    message: str = "文档已上传，正在后台处理"


class DocumentInfo(BaseModel):
    """文档信息"""
    doc_id: str
    filename: str
    file_type: str
    file_size: int
    collection: str
    status: DocumentStatus
    chunk_count: int = 0
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: list[DocumentInfo]
    total: int
    page: int
    page_size: int
```

### 2.4 API 路由

Python



```
# src/api/routers/health.py

from fastapi import APIRouter
from src.infra.config.settings import get_settings
from src.infra.database.postgres import get_postgres_pool
from src.infra.database.redis_client import get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """基础健康检查"""
    return {"status": "ok", "version": get_settings().APP_VERSION}


@router.get("/health/detail")
async def detailed_health_check():
    """详细健康检查 - 检查所有依赖"""
    checks = {}

    # PostgreSQL
    try:
        pool = await get_postgres_pool()
        await pool.fetchval("SELECT 1")
        checks["postgres"] = {"status": "healthy"}
    except Exception as e:
        checks["postgres"] = {"status": "unhealthy", "error": str(e)}

    # Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # Milvus
    try:
        from src.infra.database.milvus_client import get_milvus
        client = get_milvus()
        client.list_collections()
        checks["milvus"] = {"status": "healthy"}
    except Exception as e:
        checks["milvus"] = {"status": "unhealthy", "error": str(e)}

    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
    }
```

Python



```
# src/api/routers/chat.py

import time
import uuid
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
import structlog

from src.schemas.chat import (
    ChatRequest, ChatResponse, ConversationHistory,
    SessionInfo, StreamEvent,
)
from src.core.orchestrator.engine import ConversationOrchestrator
from src.api.dependencies import get_orchestrator

logger = structlog.get_logger()
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator),
):
    """
    对话接口 - 同步模式
    
    - 不传 session_id 则创建新会话
    - 传 session_id 则继续已有会话(多轮对话)
    """
    start_time = time.perf_counter()

    # 如果没有session_id, 创建新会话
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    logger.info(
        "chat_request",
        session_id=session_id,
        message_length=len(request.message),
        collection=request.collection,
    )

    # 调用编排引擎
    result = await orchestrator.run(
        session_id=session_id,
        message=request.message,
        collection=request.collection,
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "chat_response",
        session_id=session_id,
        confidence=result.confidence,
        fallback_used=result.fallback_used,
        latency_ms=round(elapsed_ms, 2),
    )

    return ChatResponse(
        session_id=session_id,
        message=result.answer,
        citations=result.citations,
        confidence=result.confidence,
        model_used=result.model_used,
        fallback_used=result.fallback_used,
        latency_ms=round(elapsed_ms, 2),
        tokens_used=result.tokens_used,
    )


@router.post("/completions/stream")
async def chat_completion_stream(
    request: ChatRequest,
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator),
):
    """
    对话接口 - SSE流式模式
    
    事件类型:
    - token: 逐token输出
    - citation: 引用信息
    - status: 状态更新
    - done: 完成
    - error: 错误
    """
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    async def event_generator():
        try:
            # 发送会话ID
            yield {
                "event": "status",
                "data": f'{{"session_id": "{session_id}", "status": "processing"}}',
            }

            async for event in orchestrator.stream(
                session_id=session_id,
                message=request.message,
                collection=request.collection,
            ):
                yield {
                    "event": event.event,
                    "data": event.data,
                }

        except Exception as e:
            logger.exception("stream_error", session_id=session_id)
            yield {
                "event": "error",
                "data": f'{{"error": "{str(e)}"}}',
            }

    return EventSourceResponse(event_generator())


@router.get("/sessions/{session_id}/history", response_model=ConversationHistory)
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator),
):
    """获取对话历史"""
    history = await orchestrator.get_history(session_id, limit=limit)
    return history


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(
    page: int = 1,
    page_size: int = 20,
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator),
):
    """获取会话列表"""
    sessions = await orchestrator.list_sessions(page=page, page_size=page_size)
    return sessions


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    orchestrator: ConversationOrchestrator = Depends(get_orchestrator),
):
    """删除会话"""
    await orchestrator.delete_session(session_id)
    return {"message": "Session deleted", "session_id": session_id}
```

Python



```
# src/api/routers/documents.py

import uuid
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
import structlog

from src.schemas.document import (
    DocumentUploadResponse, DocumentInfo,
    DocumentListResponse, DocumentStatus,
)
from src.infra.config.settings import get_settings
from src.core.rag.ingestion.pipeline import IngestionPipeline

logger = structlog.get_logger()
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection: str = Form("default"),
):
    """
    上传文档
    
    支持格式: PDF, DOCX, MD, TXT
    上传后异步处理: 解析 → 分块 → Embedding → 向量索引
    """
    settings = get_settings()

    # 校验文件类型
    file_ext = f".{file.filename.rsplit('.', 1)[-1].lower()}" if '.' in file.filename else ""
    if file_ext not in settings.UPLOAD_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}. "
                   f"支持: {settings.UPLOAD_ALLOWED_EXTENSIONS}",
        )

    # 校验文件大小
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # 生成文档ID
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"

    # 保存原始文件
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    file_path = f"uploads/{collection}/{doc_id}{file_ext}"
    
    # 写入本地文件 (Phase2 改为 MinIO)
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    # 写入数据库记录
    await pool.execute(
        """INSERT INTO documents 
           (id, collection, filename, file_type, file_size, file_path, status)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        doc_id, collection, file.filename, file_ext,
        len(content), file_path, "processing",
    )

    logger.info(
        "document_uploaded",
        doc_id=doc_id,
        filename=file.filename,
        file_type=file_ext,
        file_size=len(content),
        collection=collection,
    )

    # 异步处理文档
    background_tasks.add_task(
        process_document_task,
        doc_id=doc_id,
        file_path=file_path,
        file_type=file_ext,
        collection=collection,
    )

    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=file.filename,
        status=DocumentStatus.PROCESSING,
    )


async def process_document_task(
    doc_id: str,
    file_path: str,
    file_type: str,
    collection: str,
):
    """异步文档处理任务"""
    from src.core.rag.ingestion.pipeline import get_ingestion_pipeline
    from src.infra.database.postgres import get_postgres_pool

    pool = await get_postgres_pool()

    try:
        pipeline = get_ingestion_pipeline()
        chunk_count = await pipeline.process(
            doc_id=doc_id,
            file_path=file_path,
            file_type=file_type,
            collection=collection,
        )

        await pool.execute(
            """UPDATE documents 
               SET status = $1, chunk_count = $2, updated_at = NOW() 
               WHERE id = $3""",
            "completed", chunk_count, doc_id,
        )

        logger.info(
            "document_processed",
            doc_id=doc_id,
            chunk_count=chunk_count,
        )

    except Exception as e:
        await pool.execute(
            """UPDATE documents 
               SET status = $1, error_message = $2, updated_at = NOW() 
               WHERE id = $3""",
            "failed", str(e), doc_id,
        )
        logger.error("document_processing_failed", doc_id=doc_id, error=str(e))


@router.get("/{doc_id}", response_model=DocumentInfo)
async def get_document(doc_id: str):
    """查询文档状态"""
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    row = await pool.fetchrow(
        "SELECT * FROM documents WHERE id = $1", doc_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentInfo(
        doc_id=row["id"],
        filename=row["filename"],
        file_type=row["file_type"],
        file_size=row["file_size"],
        collection=row["collection"],
        status=row["status"],
        chunk_count=row["chunk_count"] or 0,
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    collection: str = "default",
    page: int = 1,
    page_size: int = 20,
):
    """获取文档列表"""
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    offset = (page - 1) * page_size

    rows = await pool.fetch(
        """SELECT * FROM documents 
           WHERE collection = $1 
           ORDER BY created_at DESC 
           LIMIT $2 OFFSET $3""",
        collection, page_size, offset,
    )

    total = await pool.fetchval(
        "SELECT COUNT(*) FROM documents WHERE collection = $1",
        collection,
    )

    documents = [
        DocumentInfo(
            doc_id=row["id"],
            filename=row["filename"],
            file_type=row["file_type"],
            file_size=row["file_size"],
            collection=row["collection"],
            status=row["status"],
            chunk_count=row["chunk_count"] or 0,
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]

    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档及其向量索引"""
    from src.infra.database.postgres import get_postgres_pool
    from src.infra.database.milvus_client import get_milvus
    from src.infra.config.settings import get_settings

    pool = await get_postgres_pool()
    settings = get_settings()

    # 检查文档是否存在
    row = await pool.fetchrow("SELECT * FROM documents WHERE id = $1", doc_id)
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    # 删除Milvus中的向量
    milvus = get_milvus()
    milvus.delete(
        collection_name=settings.MILVUS_COLLECTION_NAME,
        filter=f'doc_id == "{doc_id}"',
    )

    # 删除数据库记录
    await pool.execute("DELETE FROM documents WHERE id = $1", doc_id)

    # 删除文件
    import os
    if row["file_path"] and os.path.exists(row["file_path"]):
        os.remove(row["file_path"])

    logger.info("document_deleted", doc_id=doc_id)
    return {"message": "Document deleted", "doc_id": doc_id}
```

### 2.5 依赖注入

Python



```
# src/api/dependencies.py

from fastapi import Request
from src.core.orchestrator.engine import ConversationOrchestrator


async def get_orchestrator(request: Request) -> ConversationOrchestrator:
    """获取编排引擎实例"""
    return request.app.state.orchestrator
```

### 2.6 日志模块

Python



```
# src/infra/logging/logger.py

import logging
import sys
import structlog
from src.infra.config.settings import Settings


def setup_logging(settings: Settings):
    """配置Structlog结构化日志"""

    # 共享处理器
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.LOG_FORMAT == "console" or settings.ENV == "development":
        # 开发环境 - 彩色控制台输出
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # 生产环境 - JSON格式 (方便Loki/ELK采集)
        renderer = structlog.processors.JSONRenderer(ensure_ascii=False)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 配置标准库logging
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # 降低第三方库日志级别
    for lib in ["uvicorn.access", "httpx", "httpcore", "pymilvus"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
```

### 2.7 短期记忆

Python



```
# src/core/memory/short_term.py

import json
from datetime import datetime
from redis.asyncio import Redis
import structlog

from src.schemas.chat import ChatMessage, MessageRole

logger = structlog.get_logger()


class ShortTermMemory:
    """
    短期记忆 - Redis实现
    
    存储当前会话的对话历史, 支持:
    - 追加消息
    - 获取最近N轮消息
    - 自动过期(TTL)
    - 消息数量限制
    """

    def __init__(self, redis: Redis, ttl: int = 86400, max_messages: int = 20):
        self.redis = redis
        self.ttl = ttl
        self.max_messages = max_messages

    def _key(self, session_id: str) -> str:
        return f"memory:short:{session_id}"

    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: dict | None = None,
    ):
        """添加一条消息"""
        key = self._key(session_id)
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        await self.redis.rpush(key, message.model_dump_json())
        await self.redis.expire(key, self.ttl)

        # 如果超过最大消息数, 裁剪前面的消息
        length = await self.redis.llen(key)
        if length > self.max_messages:
            await self.redis.ltrim(key, length - self.max_messages, -1)

    async def add_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        metadata: dict | None = None,
    ):
        """添加一轮对话(用户+助手)"""
        await self.add_message(session_id, MessageRole.USER, user_message)
        await self.add_message(
            session_id, MessageRole.ASSISTANT, assistant_message, metadata
        )

    async def get_messages(
        self, session_id: str, last_n: int | None = None
    ) -> list[ChatMessage]:
        """获取会话消息"""
        key = self._key(session_id)

        if last_n:
            raw_messages = await self.redis.lrange(key, -last_n, -1)
        else:
            raw_messages = await self.redis.lrange(key, 0, -1)

        return [ChatMessage.model_validate_json(raw) for raw in raw_messages]

    async def get_formatted_history(
        self, session_id: str, last_n_turns: int = 5
    ) -> list[dict[str, str]]:
        """
        获取格式化的对话历史 (用于LLM上下文)
        返回 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
        """
        messages = await self.get_messages(session_id, last_n=last_n_turns * 2)
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    async def clear(self, session_id: str):
        """清除会话记忆"""
        await self.redis.delete(self._key(session_id))

    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return await self.redis.exists(self._key(session_id)) > 0
```

Python



```
# src/core/memory/manager.py

from redis.asyncio import Redis
from src.core.memory.short_term import ShortTermMemory
from src.schemas.chat import ChatMessage, MessageRole
from src.infra.config.settings import Settings


class MemoryManager:
    """
    记忆管理器 - Phase 1 只实现短期记忆
    Phase 2+ 会扩展长期记忆和语义记忆
    """

    def __init__(self, redis: Redis, settings: Settings):
        self.short_term = ShortTermMemory(
            redis=redis,
            ttl=settings.SHORT_TERM_MEMORY_TTL,
            max_messages=settings.MAX_SHORT_TERM_MESSAGES,
        )

    async def load_context(
        self, session_id: str, max_turns: int = 5
    ) -> list[dict[str, str]]:
        """
        加载对话上下文
        Phase 1: 仅从短期记忆加载
        Phase 2+: 融合短期记忆 + 长期记忆 + 语义记忆
        """
        return await self.short_term.get_formatted_history(
            session_id, last_n_turns=max_turns
        )

    async def save_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        metadata: dict | None = None,
    ):
        """保存一轮对话"""
        await self.short_term.add_exchange(
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            metadata=metadata,
        )

    async def clear_session(self, session_id: str):
        """清除会话记忆"""
        await self.short_term.clear(session_id)
```

------

## 四、Week 3：LlamaIndex RAG 管道

### 3.1 文档解析 & 分块

Python



```
# src/core/rag/ingestion/parser.py

from pathlib import Path
import structlog

from llama_index.core import Document

logger = structlog.get_logger()


class DocumentParser:
    """文档解析器 - 将不同格式的文件解析为纯文本"""

    async def parse(self, file_path: str, file_type: str) -> list[Document]:
        """解析文档, 返回LlamaIndex Document列表"""

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        parser_map = {
            ".pdf": self._parse_pdf,
            ".docx": self._parse_docx,
            ".md": self._parse_markdown,
            ".txt": self._parse_text,
        }

        parser = parser_map.get(file_type)
        if not parser:
            raise ValueError(f"Unsupported file type: {file_type}")

        documents = await parser(path)

        logger.info(
            "document_parsed",
            file_path=file_path,
            file_type=file_type,
            num_pages=len(documents),
        )

        return documents

    async def _parse_pdf(self, path: Path) -> list[Document]:
        """解析PDF"""
        from pypdf import PdfReader
        import asyncio

        def _read_pdf():
            reader = PdfReader(str(path))
            documents = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    documents.append(
                        Document(
                            text=text.strip(),
                            metadata={
                                "page_number": i + 1,
                                "total_pages": len(reader.pages),
                                "source": path.name,
                            },
                        )
                    )
            return documents

        return await asyncio.get_event_loop().run_in_executor(None, _read_pdf)

    async def _parse_docx(self, path: Path) -> list[Document]:
        """解析Word文档"""
        from docx import Document as DocxDocument
        import asyncio

        def _read_docx():
            doc = DocxDocument(str(path))
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())

            return [
                Document(
                    text="\n\n".join(full_text),
                    metadata={"source": path.name},
                )
            ]

        return await asyncio.get_event_loop().run_in_executor(None, _read_docx)

    async def _parse_markdown(self, path: Path) -> list[Document]:
        """解析Markdown"""
        content = path.read_text(encoding="utf-8")
        return [
            Document(
                text=content,
                metadata={"source": path.name},
            )
        ]

    async def _parse_text(self, path: Path) -> list[Document]:
        """解析纯文本"""
        content = path.read_text(encoding="utf-8")
        return [
            Document(
                text=content,
                metadata={"source": path.name},
            )
        ]
```

Python



```
# src/core/rag/ingestion/chunker.py

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document
from llama_index.core.schema import TextNode
import structlog

logger = structlog.get_logger()


class DocumentChunker:
    """
    文档分块器
    
    Phase 1: 递归字符分块 (SentenceSplitter)
    Phase 2: 语义分块 (SemanticSplitterNodeParser)
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            paragraph_separator="\n\n",
            secondary_chunking_regex="[。！？\\.\\!\\?]",  # 中英文句子边界
        )

    def chunk(
        self,
        documents: list[Document],
        doc_id: str,
        collection: str,
    ) -> list[TextNode]:
        """将文档分块为TextNode"""

        nodes = self.splitter.get_nodes_from_documents(documents)

        # 注入元数据
        for i, node in enumerate(nodes):
            node.metadata.update({
                "doc_id": doc_id,
                "chunk_index": i,
                "collection": collection,
                "total_chunks": len(nodes),
            })
            # 设置node ID (用于Milvus主键)
            node.id_ = f"{doc_id}_chunk_{i:04d}"

        logger.info(
            "document_chunked",
            doc_id=doc_id,
            num_chunks=len(nodes),
            avg_chunk_size=sum(len(n.text) for n in nodes) // max(len(nodes), 1),
        )

        return nodes
```

### 3.2 摄取管道

Python



```
# src/core/rag/ingestion/pipeline.py

import asyncio
import time
from datetime import datetime
import structlog

from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding

from src.core.rag.ingestion.parser import DocumentParser
from src.core.rag.ingestion.chunker import DocumentChunker
from src.infra.config.settings import Settings, get_settings
from src.infra.database.milvus_client import get_milvus

logger = structlog.get_logger()

# 全局管道实例
_pipeline: "IngestionPipeline | None" = None


class IngestionPipeline:
    """
    文档摄取管道
    
    完整流程: 解析 → 分块 → Embedding → 写入Milvus
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.parser = DocumentParser()
        self.chunker = DocumentChunker(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        )
        self.embedding_model = OpenAIEmbedding(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            api_base=settings.OPENAI_API_BASE,
            dimensions=settings.EMBEDDING_DIMENSION,
        )
        self._embedding_semaphore = asyncio.Semaphore(
            settings.MAX_EMBEDDING_CONCURRENT
        )

    async def process(
        self,
        doc_id: str,
        file_path: str,
        file_type: str,
        collection: str,
    ) -> int:
        """
        完整的文档处理流程
        
        返回: 处理的chunk数量
        """
        start_time = time.perf_counter()

        # 1. 解析文档
        logger.info("ingestion_step", step="parsing", doc_id=doc_id)
        documents = await self.parser.parse(file_path, file_type)

        if not documents:
            logger.warning("no_content_parsed", doc_id=doc_id)
            return 0

        # 2. 分块
        logger.info("ingestion_step", step="chunking", doc_id=doc_id)
        nodes = self.chunker.chunk(documents, doc_id, collection)

        if not nodes:
            logger.warning("no_chunks_generated", doc_id=doc_id)
            return 0

        # 3. 批量Embedding
        logger.info(
            "ingestion_step",
            step="embedding",
            doc_id=doc_id,
            num_chunks=len(nodes),
        )
        embeddings = await self._batch_embed(nodes)

        # 4. 写入Milvus
        logger.info("ingestion_step", step="indexing", doc_id=doc_id)
        await self._upsert_to_milvus(nodes, embeddings, doc_id, collection)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "ingestion_completed",
            doc_id=doc_id,
            num_chunks=len(nodes),
            latency_ms=round(elapsed_ms, 2),
        )

        return len(nodes)

    async def _batch_embed(
        self, nodes: list[TextNode], batch_size: int = 20
    ) -> list[list[float]]:
        """批量计算Embedding (带并发控制)"""
        all_embeddings = []

        for i in range(0, len(nodes), batch_size):
            batch = nodes[i : i + batch_size]
            texts = [node.text for node in batch]

            async with self._embedding_semaphore:
                batch_embeddings = await self.embedding_model.aget_text_embedding_batch(
                    texts
                )
                all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def _upsert_to_milvus(
        self,
        nodes: list[TextNode],
        embeddings: list[list[float]],
        doc_id: str,
        collection: str,
    ):
        """写入Milvus向量数据库"""
        milvus = get_milvus()
        collection_name = self.settings.MILVUS_COLLECTION_NAME

        # 准备数据
        data = []
        for node, embedding in zip(nodes, embeddings):
            data.append({
                "id": node.id_,
                "doc_id": doc_id,
                "chunk_index": node.metadata.get("chunk_index", 0),
                "content": node.text,
                "embedding": embedding,
                "doc_title": node.metadata.get("source", ""),
                "collection": collection,
                "created_at": int(datetime.utcnow().timestamp()),
            })

        # 批量写入
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            milvus.upsert(
                collection_name=collection_name,
                data=batch,
            )

        logger.info(
            "milvus_upserted",
            doc_id=doc_id,
            num_vectors=len(data),
        )


def get_ingestion_pipeline() -> IngestionPipeline:
    """获取摄取管道实例"""
    global _pipeline
    if _pipeline is None:
        _pipeline = IngestionPipeline(get_settings())
    return _pipeline
```

### 3.3 Dense 检索器

Python



```
# src/core/rag/retrieval/dense.py

import asyncio
from dataclasses import dataclass
import structlog

from llama_index.embeddings.openai import OpenAIEmbedding
from pymilvus import MilvusClient

from src.infra.config.settings import Settings

logger = structlog.get_logger()


@dataclass
class RetrievedChunk:
    """检索到的文档块"""
    chunk_id: str
    doc_id: str
    content: str
    score: float
    doc_title: str
    chunk_index: int
    collection: str


class DenseRetriever:
    """
    稠密检索器 - Milvus向量相似度检索
    
    Phase 1: 纯Dense检索
    Phase 2: 增加Sparse检索 + 混合融合
    """

    def __init__(
        self,
        milvus_client: MilvusClient,
        embedding_model: OpenAIEmbedding,
        settings: Settings,
    ):
        self.milvus = milvus_client
        self.embedding = embedding_model
        self.settings = settings
        self.collection_name = settings.MILVUS_COLLECTION_NAME

    async def retrieve(
        self,
        query: str,
        collection: str = "default",
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """
        检索与query最相关的文档块
        """
        top_k = top_k or self.settings.RAG_TOP_K
        threshold = similarity_threshold or self.settings.RAG_SIMILARITY_THRESHOLD

        # 1. 计算query的embedding
        query_embedding = await self.embedding.aget_text_embedding(query)

        # 2. Milvus向量检索
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.milvus.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                filter=f'collection == "{collection}"',
                limit=top_k,
                output_fields=[
                    "content", "doc_id", "doc_title",
                    "chunk_index", "collection",
                ],
                search_params={
                    "metric_type": "COSINE",
                    "params": {"ef": 128},
                },
            ),
        )

        if not results or not results[0]:
            logger.info("no_results_found", query=query[:100], collection=collection)
            return []

        # 3. 过滤低分结果
        chunks = []
        for hit in results[0]:
            score = hit["distance"]  # Milvus COSINE返回的是相似度 (0-1)
            
            if score < threshold:
                continue

            chunks.append(
                RetrievedChunk(
                    chunk_id=hit["id"],
                    doc_id=hit["entity"]["doc_id"],
                    content=hit["entity"]["content"],
                    score=score,
                    doc_title=hit["entity"]["doc_title"],
                    chunk_index=hit["entity"]["chunk_index"],
                    collection=hit["entity"]["collection"],
                )
            )

        logger.info(
            "retrieval_completed",
            query=query[:100],
            collection=collection,
            total_hits=len(results[0]),
            filtered_hits=len(chunks),
            top_score=chunks[0].score if chunks else 0,
        )

        return chunks
```

Python



```
# src/core/rag/retrieval/retriever.py

from src.core.rag.retrieval.dense import DenseRetriever, RetrievedChunk


class RAGRetriever:
    """
    RAG检索器 - 统一检索接口
    
    Phase 1: 仅 Dense
    Phase 2: Dense + Sparse (BM25) + Rerank
    Phase 3: Dense + Sparse + KG + Rerank
    """

    def __init__(self, dense_retriever: DenseRetriever):
        self.dense = dense_retriever

    async def retrieve(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """
        检索文档
        
        Phase 1: 直接使用Dense检索
        """
        # Dense检索 (多取一些, 预留给后续Rerank)
        results = await self.dense.retrieve(
            query=query,
            collection=collection,
            top_k=top_k * 2,  # 多召回一些
        )

        # Phase 1: 直接截取top_k
        # Phase 2+: 这里会增加RRF融合 + Rerank
        return results[:top_k]
```

### 3.4 答案合成

Python



```
# src/core/rag/synthesis/synthesizer.py

import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.rag.retrieval.dense import RetrievedChunk
from src.schemas.chat import CitationItem
from src.infra.config.settings import Settings

logger = structlog.get_logger()

# === Prompt模板 ===

RAG_SYSTEM_PROMPT = """你是一个企业智能问答助手。请根据提供的参考资料回答用户的问题。

规则:
1. 只根据参考资料中的信息回答，不要编造信息
2. 如果参考资料中没有相关信息，请明确说"根据现有资料，我无法找到相关信息"
3. 回答时标注引用来源，使用 [来源X] 的格式
4. 回答要简洁、准确、专业
5. 如果问题不清晰，可以请求用户澄清

参考资料:
{context}
"""

RAG_USER_PROMPT = """用户问题: {question}

请根据参考资料回答上述问题。"""


class AnswerSynthesizer:
    """答案合成器 - 基于检索到的上下文生成回答"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.primary_llm = ChatOpenAI(
            model=settings.PRIMARY_LLM_MODEL,
            temperature=settings.PRIMARY_LLM_TEMPERATURE,
            max_tokens=settings.PRIMARY_LLM_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
            timeout=settings.LLM_TIMEOUT,
        )
        self.fallback_llm = ChatOpenAI(
            model=settings.FALLBACK_LLM_MODEL,
            temperature=settings.FALLBACK_LLM_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
            timeout=settings.LLM_TIMEOUT,
        )

    async def synthesize(
        self,
        query: str,
        retrieved_chunks: list[RetrievedChunk],
        conversation_history: list[dict] | None = None,
    ) -> SynthesisResult:
        """基于检索结果合成答案"""

        # 构建context
        context = self._build_context(retrieved_chunks)
        
        # 构建消息
        messages = []

        # System prompt
        messages.append(
            SystemMessage(content=RAG_SYSTEM_PROMPT.format(context=context))
        )

        # 历史对话 (多轮上下文)
        if conversation_history:
            for msg in conversation_history[-6:]:  # 最近3轮
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    from langchain_core.messages import AIMessage
                    messages.append(AIMessage(content=msg["content"]))

        # 当前问题
        messages.append(
            HumanMessage(content=RAG_USER_PROMPT.format(question=query))
        )

        # 调用LLM
        try:
            response = await self.primary_llm.ainvoke(messages)
            model_used = self.settings.PRIMARY_LLM_MODEL
        except Exception as e:
            logger.error("primary_llm_failed", error=str(e))
            raise

        # 提取引用
        citations = self._extract_citations(retrieved_chunks)

        # 估算token使用
        tokens_used = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

        return SynthesisResult(
            answer=response.content,
            citations=citations,
            model_used=model_used,
            tokens_used=tokens_used,
        )

    async def synthesize_with_codex(
        self,
        query: str,
        conversation_history: list[dict] | None = None,
    ) -> SynthesisResult:
        """
        Codex降级回答 (不使用RAG上下文)
        当RAG检索结果不好时使用
        """
        messages = [
            SystemMessage(
                content="你是一个企业智能问答助手。请根据你的知识回答用户的问题。"
                        "如果不确定，请明确说明。"
            ),
        ]

        if conversation_history:
            for msg in conversation_history[-6:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    from langchain_core.messages import AIMessage
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=query))

        response = await self.fallback_llm.ainvoke(messages)
        tokens_used = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

        return SynthesisResult(
            answer=response.content,
            citations=[],
            model_used=self.settings.FALLBACK_LLM_MODEL,
            tokens_used=tokens_used,
            is_fallback=True,
        )

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        """构建参考资料文本"""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[来源{i}] (文档: {chunk.doc_title}, 相关度: {chunk.score:.2f})\n"
                f"{chunk.content}\n"
            )
        return "\n---\n".join(context_parts)

    def _extract_citations(self, chunks: list[RetrievedChunk]) -> list[CitationItem]:
        """提取引用信息"""
        return [
            CitationItem(
                doc_id=chunk.doc_id,
                doc_title=chunk.doc_title,
                content=chunk.content[:200],  # 截取前200字符
                chunk_index=chunk.chunk_index,
                relevance_score=chunk.score,
            )
            for chunk in chunks
        ]


class SynthesisResult:
    """合成结果"""

    def __init__(
        self,
        answer: str,
        citations: list[CitationItem],
        model_used: str,
        tokens_used: int = 0,
        is_fallback: bool = False,
    ):
        self.answer = answer
        self.citations = citations
        self.model_used = model_used
        self.tokens_used = tokens_used
        self.is_fallback = is_fallback
```

------

## 五、Week 4：LangGraph 对话编排

### 4.1 状态定义

Python



```
# src/core/orchestrator/state.py

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from src.core.rag.retrieval.dense import RetrievedChunk
from src.schemas.chat import CitationItem


class ConversationState(TypedDict):
    """
    LangGraph 对话状态
    
    Phase 1 精简版 - 只保留核心字段
    """
    # === LangGraph 消息列表 ===
    messages: Annotated[list[BaseMessage], add_messages]

    # === 会话信息 ===
    session_id: str
    collection: str

    # === 查询 ===
    original_query: str
    rewritten_query: str          # Phase1: 直接使用原始query

    # === RAG ===
    retrieved_chunks: list[dict]  # 检索到的文档块
    context_text: str             # 格式化后的上下文

    # === 答案 ===
    answer: str
    citations: list[dict]
    confidence: float
    model_used: str
    tokens_used: int

    # === 控制 ===
    fallback_used: bool           # 是否使用了降级
    error: str | None             # 错误信息
```

### 4.2 节点实现

Python



```
# src/core/orchestrator/nodes/query_understanding.py

import structlog
from langchain_core.messages import HumanMessage
from src.core.orchestrator.state import ConversationState

logger = structlog.get_logger()


async def query_understanding_node(state: ConversationState) -> dict:
    """
    查询理解节点
    
    Phase 1: 简单实现 - 直接使用原始查询
    Phase 2: 增加指代消解、查询改写、意图识别
    """
    # 从最后一条用户消息获取查询
    original_query = state["original_query"]

    logger.info(
        "query_understanding",
        session_id=state["session_id"],
        query=original_query[:100],
    )

    # Phase 1: 直接使用原始查询
    # Phase 2: 这里会增加LLM改写 + 多轮指代消解
    rewritten_query = original_query

    return {
        "rewritten_query": rewritten_query,
    }
```

Python



```
# src/core/orchestrator/nodes/rag_agent.py

import structlog
from src.core.orchestrator.state import ConversationState
from src.core.rag.retrieval.retriever import RAGRetriever
from src.schemas.chat import CitationItem

logger = structlog.get_logger()


class RAGAgentNode:
    """RAG Agent节点 - 检索相关文档"""

    def __init__(self, retriever: RAGRetriever):
        self.retriever = retriever

    async def __call__(self, state: ConversationState) -> dict:
        """执行RAG检索"""
        query = state["rewritten_query"] or state["original_query"]
        collection = state["collection"]

        logger.info(
            "rag_retrieval_start",
            session_id=state["session_id"],
            query=query[:100],
            collection=collection,
        )

        # 检索
        chunks = await self.retriever.retrieve(
            query=query,
            collection=collection,
            top_k=5,
        )

        # 转为可序列化的dict
        chunks_data = [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "content": c.content,
                "score": c.score,
                "doc_title": c.doc_title,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        # 构建上下文文本
        context_parts = []
        for i, c in enumerate(chunks, 1):
            context_parts.append(
                f"[来源{i}] (文档: {c.doc_title}, 相关度: {c.score:.2f})\n{c.content}"
            )
        context_text = "\n\n---\n\n".join(context_parts)

        logger.info(
            "rag_retrieval_completed",
            session_id=state["session_id"],
            num_chunks=len(chunks),
            top_score=chunks[0].score if chunks else 0,
        )

        return {
            "retrieved_chunks": chunks_data,
            "context_text": context_text,
        }
```

Python



```
# src/core/orchestrator/nodes/quality_gate.py

import structlog
from src.core.orchestrator.state import ConversationState

logger = structlog.get_logger()


async def quality_gate_node(state: ConversationState) -> dict:
    """
    质量评估节点 - 决定是否需要降级到Codex
    
    Phase 1: 基于检索分数的简单评估
    Phase 2: 增加LLM-based的faithfulness检测
    """
    chunks = state["retrieved_chunks"]

    if not chunks:
        # 没有检索到任何文档 -> 降级
        confidence = 0.0
        logger.info(
            "quality_gate_no_results",
            session_id=state["session_id"],
        )
    else:
        # 基于top-k分数计算置信度
        scores = [c["score"] for c in chunks]
        top_score = max(scores)
        avg_score = sum(scores) / len(scores)

        # 简单加权: 60%最高分 + 40%平均分
        confidence = 0.6 * top_score + 0.4 * avg_score

    logger.info(
        "quality_gate_evaluated",
        session_id=state["session_id"],
        confidence=round(confidence, 3),
        num_chunks=len(chunks),
    )

    return {
        "confidence": confidence,
    }


def should_fallback(state: ConversationState) -> str:
    """条件路由: 是否降级到Codex"""
    from src.infra.config.settings import get_settings
    settings = get_settings()

    if state["confidence"] >= settings.CONFIDENCE_THRESHOLD_PASS:
        return "generate_answer"     # 置信度高, 用RAG生成
    else:
        return "codex_fallback"      # 置信度低, 降级到Codex
```

Python



```
# src/core/orchestrator/nodes/response_synthesizer.py

import structlog
from langchain_core.messages import AIMessage

from src.core.orchestrator.state import ConversationState
from src.core.rag.synthesis.synthesizer import AnswerSynthesizer

logger = structlog.get_logger()


class ResponseSynthesizerNode:
    """答案生成节点 - 使用RAG上下文生成回答"""

    def __init__(self, synthesizer: AnswerSynthesizer):
        self.synthesizer = synthesizer

    async def __call__(self, state: ConversationState) -> dict:
        """生成回答"""
        query = state["rewritten_query"] or state["original_query"]
        chunks = state["retrieved_chunks"]

        logger.info(
            "response_synthesis_start",
            session_id=state["session_id"],
            num_context_chunks=len(chunks),
        )

        # 从chunks重建RetrievedChunk对象
        from src.core.rag.retrieval.dense import RetrievedChunk
        retrieved = [
            RetrievedChunk(
                chunk_id=c["chunk_id"],
                doc_id=c["doc_id"],
                content=c["content"],
                score=c["score"],
                doc_title=c["doc_title"],
                chunk_index=c["chunk_index"],
                collection=state["collection"],
            )
            for c in chunks
        ]

        # 获取对话历史 (从state.messages)
        history = []
        for msg in state["messages"][:-1]:  # 排除当前消息
            history.append({
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content,
            })

        # 合成答案
        result = await self.synthesizer.synthesize(
            query=query,
            retrieved_chunks=retrieved,
            conversation_history=history if history else None,
        )

        citations_data = [c.model_dump() for c in result.citations]

        logger.info(
            "response_synthesis_completed",
            session_id=state["session_id"],
            model_used=result.model_used,
            tokens_used=result.tokens_used,
            answer_length=len(result.answer),
        )

        return {
            "answer": result.answer,
            "citations": citations_data,
            "model_used": result.model_used,
            "tokens_used": result.tokens_used,
            "fallback_used": False,
            "messages": [AIMessage(content=result.answer)],
        }
```

Python



```
# src/core/orchestrator/nodes/codex_fallback.py

import structlog
from langchain_core.messages import AIMessage, HumanMessage

from src.core.orchestrator.state import ConversationState
from src.core.rag.synthesis.synthesizer import AnswerSynthesizer

logger = structlog.get_logger()


class CodexFallbackNode:
    """Codex降级节点 - RAG效果差时使用"""

    def __init__(self, synthesizer: AnswerSynthesizer):
        self.synthesizer = synthesizer

    async def __call__(self, state: ConversationState) -> dict:
        """使用降级模型直接回答"""
        query = state["rewritten_query"] or state["original_query"]

        logger.info(
            "codex_fallback_triggered",
            session_id=state["session_id"],
            confidence=state["confidence"],
        )

        # 获取对话历史
        history = []
        for msg in state["messages"][:-1]:
            history.append({
                "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                "content": msg.content,
            })

        result = await self.synthesizer.synthesize_with_codex(
            query=query,
            conversation_history=history if history else None,
        )

        logger.info(
            "codex_fallback_completed",
            session_id=state["session_id"],
            model_used=result.model_used,
        )

        return {
            "answer": result.answer,
            "citations": [],
            "model_used": result.model_used,
            "tokens_used": result.tokens_used,
            "fallback_used": True,
            "messages": [AIMessage(content=result.answer)],
        }
```

### 4.3 主图定义

Python



```
# src/core/orchestrator/graph.py

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.core.orchestrator.state import ConversationState
from src.core.orchestrator.nodes.query_understanding import query_understanding_node
from src.core.orchestrator.nodes.rag_agent import RAGAgentNode
from src.core.orchestrator.nodes.quality_gate import quality_gate_node, should_fallback
from src.core.orchestrator.nodes.response_synthesizer import ResponseSynthesizerNode
from src.core.orchestrator.nodes.codex_fallback import CodexFallbackNode


def build_graph(
    rag_agent_node: RAGAgentNode,
    response_synthesizer_node: ResponseSynthesizerNode,
    codex_fallback_node: CodexFallbackNode,
) -> StateGraph:
    """
    构建Phase 1对话图
    
    流程:
    START → query_understanding → rag_agent → quality_gate 
        → (高置信) → generate_answer → END
        → (低置信) → codex_fallback → END
    """

    graph = StateGraph(ConversationState)

    # === 注册节点 ===
    graph.add_node("query_understanding", query_understanding_node)
    graph.add_node("rag_agent", rag_agent_node)
    graph.add_node("quality_gate", quality_gate_node)
    graph.add_node("generate_answer", response_synthesizer_node)
    graph.add_node("codex_fallback", codex_fallback_node)

    # === 定义边 ===
    graph.add_edge(START, "query_understanding")
    graph.add_edge("query_understanding", "rag_agent")
    graph.add_edge("rag_agent", "quality_gate")

    # 条件路由: 根据质量评估决定走RAG生成还是Codex降级
    graph.add_conditional_edges(
        "quality_gate",
        should_fallback,
        {
            "generate_answer": "generate_answer",
            "codex_fallback": "codex_fallback",
        },
    )

    graph.add_edge("generate_answer", END)
    graph.add_edge("codex_fallback", END)

    return graph


async def compile_graph(
    rag_agent_node: RAGAgentNode,
    response_synthesizer_node: ResponseSynthesizerNode,
    codex_fallback_node: CodexFallbackNode,
    postgres_url: str,
):
    """编译图 (带PostgreSQL持久化检查点)"""

    graph = build_graph(
        rag_agent_node=rag_agent_node,
        response_synthesizer_node=response_synthesizer_node,
        codex_fallback_node=codex_fallback_node,
    )

    # 持久化检查点 (支持可中断/恢复)
    checkpointer = AsyncPostgresSaver.from_conn_string(postgres_url)
    await checkpointer.setup()

    compiled = graph.compile(checkpointer=checkpointer)

    return compiled
```

text



```
Phase 1 图可视化:

    ┌─────────────────┐
    │      START      │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ query_under-    │
    │ standing        │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   rag_agent     │
    │  (Dense检索)    │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  quality_gate   │
    │ (置信度评估)    │
    └───┬─────────┬───┘
        │         │
   ≥0.7 │         │ <0.7
        ▼         ▼
  ┌──────────┐ ┌──────────┐
  │ generate │ │  codex   │
  │ _answer  │ │ fallback │
  │ (RAG)    │ │ (降级)   │
  └────┬─────┘ └────┬─────┘
       │             │
       ▼             ▼
    ┌─────────────────┐
    │       END       │
    └─────────────────┘
```

### 4.4 编排引擎

Python



```
# src/core/orchestrator/engine.py

import time
from dataclasses import dataclass, field
import structlog

from langchain_core.messages import HumanMessage
from llama_index.embeddings.openai import OpenAIEmbedding

from src.core.orchestrator.graph import compile_graph
from src.core.orchestrator.nodes.rag_agent import RAGAgentNode
from src.core.orchestrator.nodes.response_synthesizer import ResponseSynthesizerNode
from src.core.orchestrator.nodes.codex_fallback import CodexFallbackNode
from src.core.rag.retrieval.dense import DenseRetriever
from src.core.rag.retrieval.retriever import RAGRetriever
from src.core.rag.synthesis.synthesizer import AnswerSynthesizer
from src.core.memory.manager import MemoryManager
from src.schemas.chat import CitationItem, ChatMessage, ConversationHistory, SessionInfo
from src.infra.config.settings import Settings

logger = structlog.get_logger()


@dataclass
class OrchestratorResult:
    """编排引擎返回结果"""
    answer: str = ""
    citations: list[CitationItem] = field(default_factory=list)
    confidence: float = 0.0
    model_used: str = ""
    fallback_used: bool = False
    tokens_used: int = 0


class ConversationOrchestrator:
    """
    对话编排器
    
    职责:
    1. 管理LangGraph图的执行
    2. 管理会话记忆
    3. 处理会话持久化
    """

    def __init__(
        self,
        compiled_graph,
        memory_manager: MemoryManager,
        pg_pool,
    ):
        self.graph = compiled_graph
        self.memory = memory_manager
        self.pg_pool = pg_pool

    async def run(
        self,
        session_id: str,
        message: str,
        collection: str = "default",
    ) -> OrchestratorResult:
        """执行一轮对话"""
        start_time = time.perf_counter()

        # 1. 加载对话历史 (构建多轮上下文)
        history = await self.memory.load_context(session_id, max_turns=5)

        # 2. 构建初始状态
        initial_messages = []
        for msg in history:
            if msg["role"] == "user":
                initial_messages.append(HumanMessage(content=msg["content"]))
            else:
                from langchain_core.messages import AIMessage
                initial_messages.append(AIMessage(content=msg["content"]))
        initial_messages.append(HumanMessage(content=message))

        initial_state = {
            "messages": initial_messages,
            "session_id": session_id,
            "collection": collection,
            "original_query": message,
            "rewritten_query": "",
            "retrieved_chunks": [],
            "context_text": "",
            "answer": "",
            "citations": [],
            "confidence": 0.0,
            "model_used": "",
            "tokens_used": 0,
            "fallback_used": False,
            "error": None,
        }

        # 3. 执行图
        thread_config = {
            "configurable": {"thread_id": session_id}
        }

        try:
            result_state = await self.graph.ainvoke(
                initial_state,
                config=thread_config,
            )
        except Exception as e:
            logger.exception("graph_execution_failed", session_id=session_id)
            return OrchestratorResult(
                answer=f"抱歉，处理您的问题时出现了错误。请稍后重试。",
                confidence=0.0,
                model_used="error",
            )

        # 4. 保存对话记忆
        await self.memory.save_turn(
            session_id=session_id,
            user_message=message,
            assistant_message=result_state["answer"],
            metadata={
                "confidence": result_state["confidence"],
                "model_used": result_state["model_used"],
                "fallback_used": result_state["fallback_used"],
            },
        )

        # 5. 保存到PostgreSQL (持久化)
        await self._save_to_db(session_id, message, result_state)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "orchestrator_completed",
            session_id=session_id,
            confidence=result_state["confidence"],
            fallback_used=result_state["fallback_used"],
            latency_ms=round(elapsed_ms, 2),
        )

        # 6. 构建返回结果
        citations = [
            CitationItem(**c) for c in result_state.get("citations", [])
        ]

        return OrchestratorResult(
            answer=result_state["answer"],
            citations=citations,
            confidence=result_state["confidence"],
            model_used=result_state["model_used"],
            fallback_used=result_state["fallback_used"],
            tokens_used=result_state.get("tokens_used", 0),
        )

    async def stream(self, session_id: str, message: str, collection: str = "default"):
        """
        流式执行
        Phase 1: 简化实现 - 先完整执行再逐字返回
        Phase 2: 真正的流式 (astream_events)
        """
        result = await self.run(session_id, message, collection)

        from src.schemas.chat import StreamEvent
        import json

        # 逐字输出 (模拟流式)
        for char in result.answer:
            yield StreamEvent(event="token", data=char)

        # 引用信息
        if result.citations:
            yield StreamEvent(
                event="citation",
                data=json.dumps(
                    [c.model_dump() for c in result.citations],
                    ensure_ascii=False,
                ),
            )

        # 完成
        yield StreamEvent(
            event="done",
            data=json.dumps({
                "session_id": session_id,
                "confidence": result.confidence,
                "model_used": result.model_used,
                "fallback_used": result.fallback_used,
            }),
        )

    async def _save_to_db(self, session_id: str, user_message: str, state: dict):
        """保存对话到PostgreSQL"""
        import json

        # 确保session存在
        existing = await self.pg_pool.fetchval(
            "SELECT id FROM conversation_sessions WHERE id = $1", session_id
        )
        if not existing:
            await self.pg_pool.execute(
                """INSERT INTO conversation_sessions (id, user_id, title, status)
                   VALUES ($1, $2, $3, $4)""",
                session_id,
                "default_user",  # Phase 2: 真实用户
                user_message[:100],  # 用第一条消息做标题
                "active",
            )

        # 保存用户消息
        await self.pg_pool.execute(
            """INSERT INTO conversation_messages 
               (session_id, role, content, metadata)
               VALUES ($1, $2, $3, $4)""",
            session_id, "user", user_message, "{}",
        )

        # 保存助手消息
        await self.pg_pool.execute(
            """INSERT INTO conversation_messages 
               (session_id, role, content, citations, confidence, model_used, tokens_used, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            session_id,
            "assistant",
            state["answer"],
            json.dumps(state.get("citations", []), ensure_ascii=False),
            state.get("confidence", 0.0),
            state.get("model_used", ""),
            state.get("tokens_used", 0),
            json.dumps({"fallback_used": state.get("fallback_used", False)}),
        )

    async def get_history(self, session_id: str, limit: int = 50) -> ConversationHistory:
        """获取对话历史"""
        rows = await self.pg_pool.fetch(
            """SELECT role, content, created_at, metadata 
               FROM conversation_messages 
               WHERE session_id = $1 
               ORDER BY created_at ASC
               LIMIT $2""",
            session_id, limit,
        )

        messages = [
            ChatMessage(
                role=row["role"],
                content=row["content"],
                timestamp=row["created_at"],
            )
            for row in rows
        ]

        return ConversationHistory(
            session_id=session_id,
            messages=messages,
            total_count=len(messages),
        )

    async def list_sessions(self, page: int = 1, page_size: int = 20) -> list[SessionInfo]:
        """获取会话列表"""
        offset = (page - 1) * page_size
        rows = await self.pg_pool.fetch(
            """SELECT s.id, s.title, s.status, s.created_at, s.updated_at,
                      COUNT(m.id) as message_count
               FROM conversation_sessions s
               LEFT JOIN conversation_messages m ON s.id = m.session_id
               GROUP BY s.id
               ORDER BY s.updated_at DESC
               LIMIT $1 OFFSET $2""",
            page_size, offset,
        )

        return [
            SessionInfo(
                session_id=row["id"],
                title=row["title"],
                message_count=row["message_count"],
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    async def delete_session(self, session_id: str):
        """删除会话"""
        await self.pg_pool.execute(
            "DELETE FROM conversation_messages WHERE session_id = $1", session_id
        )
        await self.pg_pool.execute(
            "DELETE FROM conversation_sessions WHERE id = $1", session_id
        )
        await self.memory.clear_session(session_id)


async def init_orchestrator(
    pg_pool,
    redis_client,
    milvus_client,
    settings: Settings,
) -> ConversationOrchestrator:
    """初始化编排引擎 (在应用启动时调用)"""

    # 1. 初始化Embedding模型
    embedding_model = OpenAIEmbedding(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY.get_secret_value(),
        api_base=settings.OPENAI_API_BASE,
        dimensions=settings.EMBEDDING_DIMENSION,
    )

    # 2. 初始化检索器
    dense_retriever = DenseRetriever(
        milvus_client=milvus_client,
        embedding_model=embedding_model,
        settings=settings,
    )
    rag_retriever = RAGRetriever(dense_retriever=dense_retriever)

    # 3. 初始化答案合成器
    synthesizer = AnswerSynthesizer(settings=settings)

    # 4. 创建节点
    rag_agent_node = RAGAgentNode(retriever=rag_retriever)
    response_node = ResponseSynthesizerNode(synthesizer=synthesizer)
    codex_node = CodexFallbackNode(synthesizer=synthesizer)

    # 5. 编译图
    compiled_graph = await compile_graph(
        rag_agent_node=rag_agent_node,
        response_synthesizer_node=response_node,
        codex_fallback_node=codex_node,
        postgres_url=settings.POSTGRES_URL,
    )

    # 6. 初始化记忆管理器
    memory_manager = MemoryManager(redis=redis_client, settings=settings)

    # 7. 创建编排器
    orchestrator = ConversationOrchestrator(
        compiled_graph=compiled_graph,
        memory_manager=memory_manager,
        pg_pool=pg_pool,
    )

    logger.info("orchestrator_initialized")
    return orchestrator
```

------

## 六、Week 5：集成联调 & 异步任务

### 5.1 异步任务队列

Python



```
# src/infra/queue/task_queue.py

from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from src.infra.config.settings import get_settings
import structlog

logger = structlog.get_logger()


async def process_document_job(ctx: dict, doc_id: str, file_path: str, file_type: str, collection: str):
    """异步文档处理任务"""
    from src.core.rag.ingestion.pipeline import IngestionPipeline
    settings = get_settings()
    pipeline = IngestionPipeline(settings)

    logger.info("async_document_processing_start", doc_id=doc_id)

    try:
        chunk_count = await pipeline.process(
            doc_id=doc_id,
            file_path=file_path,
            file_type=file_type,
            collection=collection,
        )

        # 更新数据库状态
        from src.infra.database.postgres import get_postgres_pool
        pool = await get_postgres_pool()
        await pool.execute(
            "UPDATE documents SET status = 'completed', chunk_count = $1, updated_at = NOW() WHERE id = $2",
            chunk_count, doc_id,
        )
        logger.info("async_document_processing_completed", doc_id=doc_id, chunks=chunk_count)

    except Exception as e:
        from src.infra.database.postgres import get_postgres_pool
        pool = await get_postgres_pool()
        await pool.execute(
            "UPDATE documents SET status = 'failed', error_message = $1, updated_at = NOW() WHERE id = $2",
            str(e), doc_id,
        )
        logger.error("async_document_processing_failed", doc_id=doc_id, error=str(e))
        raise


class WorkerSettings:
    """ARQ Worker 配置"""
    functions = [process_document_job]
    redis_settings = RedisSettings(
        host=get_settings().REDIS_HOST,
        port=get_settings().REDIS_PORT,
    )
    max_jobs = 10
    job_timeout = 600  # 10分钟超时
```

### 5.2 完整的 Dockerfile

Dockerfile



```
# docker/Dockerfile.api

FROM python:3.12-slim AS base

# 系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python依赖
COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root

# 复制代码
COPY src/ ./src/
COPY scripts/ ./scripts/

# 创建上传目录
RUN mkdir -p uploads

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--loop", "uvloop"]
```

Dockerfile



```
# docker/Dockerfile.worker

FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root

COPY src/ ./src/
RUN mkdir -p uploads

CMD ["arq", "src.infra.queue.task_queue.WorkerSettings"]
```

------

## 七、Week 6：测试 & 稳定化

### 7.1 测试夹具

Python



```
# tests/conftest.py

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from src.api.main import create_app
from src.infra.config.settings import Settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """测试环境配置"""
    return Settings(
        ENV="test",
        DEBUG=True,
        POSTGRES_DB="qa_assistant_test",
        OPENAI_API_KEY="sk-test-key",  # Mock
    )


@pytest.fixture
async def async_client():
    """异步HTTP测试客户端"""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

### 7.2 单元测试

Python



```
# tests/unit/test_chunker.py

import pytest
from llama_index.core import Document
from src.core.rag.ingestion.chunker import DocumentChunker


class TestDocumentChunker:
    def setup_method(self):
        self.chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)

    def test_basic_chunking(self):
        """测试基础分块"""
        doc = Document(text="这是一段很长的文本。" * 50, metadata={"source": "test.txt"})
        nodes = self.chunker.chunk([doc], doc_id="test_001", collection="default")

        assert len(nodes) > 1
        assert all(n.metadata["doc_id"] == "test_001" for n in nodes)
        assert all(n.metadata["collection"] == "default" for n in nodes)

    def test_empty_document(self):
        """测试空文档"""
        doc = Document(text="", metadata={"source": "empty.txt"})
        nodes = self.chunker.chunk([doc], doc_id="test_002", collection="default")
        assert len(nodes) == 0

    def test_chunk_metadata(self):
        """测试分块元数据"""
        doc = Document(text="Hello world. " * 100, metadata={"source": "test.txt"})
        nodes = self.chunker.chunk([doc], doc_id="test_003", collection="hr")

        for i, node in enumerate(nodes):
            assert node.metadata["chunk_index"] == i
            assert node.metadata["total_chunks"] == len(nodes)
            assert node.id_ == f"test_003_chunk_{i:04d}"


# tests/unit/test_memory.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.memory.short_term import ShortTermMemory
from src.schemas.chat import MessageRole


class TestShortTermMemory:
    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.rpush = AsyncMock()
        redis.expire = AsyncMock()
        redis.llen = AsyncMock(return_value=5)
        redis.lrange = AsyncMock(return_value=[])
        redis.exists = AsyncMock(return_value=1)
        return redis

    @pytest.fixture
    def memory(self, mock_redis):
        return ShortTermMemory(redis=mock_redis, ttl=3600, max_messages=20)

    @pytest.mark.asyncio
    async def test_add_message(self, memory, mock_redis):
        """测试添加消息"""
        await memory.add_message("sess_001", MessageRole.USER, "Hello")

        mock_redis.rpush.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_exists(self, memory, mock_redis):
        """测试会话存在性检查"""
        result = await memory.exists("sess_001")
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_session(self, memory, mock_redis):
        """测试清除会话"""
        mock_redis.delete = AsyncMock()
        await memory.clear("sess_001")
        mock_redis.delete.assert_called_once_with("memory:short:sess_001")
```

### 7.3 集成测试

Python



```
# tests/integration/test_chat_api.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestChatAPI:
    """对话API集成测试 (需要运行中的基础设施)"""

    async def test_health_check(self, async_client: AsyncClient):
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    async def test_create_new_conversation(self, async_client: AsyncClient):
        """测试创建新对话"""
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "message": "你好",
                "collection": "default",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "message" in data
        assert len(data["message"]) > 0

    async def test_multi_turn_conversation(self, async_client: AsyncClient):
        """测试多轮对话"""
        # 第一轮
        resp1 = await async_client.post(
            "/api/v1/chat/completions",
            json={"message": "什么是RAG？"},
        )
        session_id = resp1.json()["session_id"]

        # 第二轮 (使用相同session_id)
        resp2 = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "message": "它有什么优势？",  # 指代"RAG"
                "session_id": session_id,
            },
        )
        assert resp2.status_code == 200
        assert resp2.json()["session_id"] == session_id
```

### 7.4 手动测试脚本

Python



```
# scripts/test_upload.py

"""手动测试文档上传和问答"""

import asyncio
import httpx
import time


BASE_URL = "http://localhost:8000/api/v1"


async def main():
    async with httpx.AsyncClient(timeout=120) as client:
        # 1. 上传文档
        print("=" * 60)
        print("1. 上传文档")
        print("=" * 60)

        # 创建测试文档
        test_content = """
        # 公司年假制度

        ## 一、年假天数
        - 工龄1-5年: 5天年假
        - 工龄5-10年: 10天年假
        - 工龄10年以上: 15天年假

        ## 二、请假流程
        1. 提前3天在OA系统提交申请
        2. 直属上级审批
        3. HR备案

        ## 三、注意事项
        - 年假不可跨年累积
        - 紧急情况可补办手续
        - 年假期间工资照常发放
        """

        with open("/tmp/test_hr_policy.md", "w") as f:
            f.write(test_content)

        with open("/tmp/test_hr_policy.md", "rb") as f:
            response = await client.post(
                f"{BASE_URL}/documents/upload",
                files={"file": ("hr_policy.md", f, "text/markdown")},
                data={"collection": "hr_docs"},
            )

        print(f"Upload response: {response.json()}")
        doc_id = response.json()["doc_id"]

        # 等待处理完成
        print("\n等待文档处理...")
        for _ in range(30):
            status_resp = await client.get(f"{BASE_URL}/documents/{doc_id}")
            status = status_resp.json()["status"]
            print(f"  状态: {status}")
            if status in ("completed", "failed"):
                break
            await asyncio.sleep(2)

        # 2. 问答测试
        print("\n" + "=" * 60)
        print("2. 问答测试")
        print("=" * 60)

        questions = [
            "公司年假制度是什么？",
            "工龄3年有几天年假？",
            "请假需要提前几天？",
            "年假可以跨年吗？",
        ]

        session_id = None
        for q in questions:
            print(f"\n❓ 问: {q}")
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                json={
                    "message": q,
                    "session_id": session_id,
                    "collection": "hr_docs",
                },
            )
            data = resp.json()
            session_id = data["session_id"]

            print(f"💬 答: {data['message']}")
            print(f"   置信度: {data['confidence']:.2f}")
            print(f"   模型: {data['model_used']}")
            print(f"   降级: {data['fallback_used']}")
            print(f"   引用数: {len(data['citations'])}")

        # 3. 多轮对话测试 (指代消解)
        print("\n" + "=" * 60)
        print("3. 多轮对话测试")
        print("=" * 60)

        session_id = None
        multi_turn_qs = [
            "工龄8年有多少天假？",
            "那如果是3年呢？",  # "3年"指代"工龄3年"
            "请假流程是什么？",
            "第二步是什么？",    # "第二步"指代请假流程的步骤
        ]

        for q in multi_turn_qs:
            print(f"\n❓ 问: {q}")
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                json={
                    "message": q,
                    "session_id": session_id,
                    "collection": "hr_docs",
                },
            )
            data = resp.json()
            session_id = data["session_id"]
            print(f"💬 答: {data['message'][:200]}")

        print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
```

------

## 八、Phase 1 验收标准

### 功能验收

| #    | 功能         | 验收标准                            | 状态 |
| ---- | ------------ | ----------------------------------- | ---- |
| 1    | 文档上传     | 支持 PDF/Word/MD/TXT 上传，异步处理 | ⬜    |
| 2    | 文档状态查询 | 可查询处理进度和状态                | ⬜    |
| 3    | 单轮对话     | 基于RAG的单轮问答，返回引用         | ⬜    |
| 4    | 多轮对话     | 保持会话上下文，支持多轮交互        | ⬜    |
| 5    | SSE流式      | 流式返回回答内容                    | ⬜    |
| 6    | Codex降级    | 当RAG置信度低时自动降级             | ⬜    |
| 7    | 会话管理     | 列表/历史/删除                      | ⬜    |
| 8    | 健康检查     | /health 和 /health/detail           | ⬜    |

### 非功能验收

| #    | 指标     | 验收标准                     |
| ---- | -------- | ---------------------------- |
| 1    | 单轮延迟 | P95 < 5s (含LLM调用)         |
| 2    | 并发     | 支持 20 并发请求不报错       |
| 3    | 文档处理 | 10页PDF < 60s                |
| 4    | 日志     | 结构化JSON日志, 含request_id |
| 5    | Docker   | `docker compose up` 一键启动 |
| 6    | 测试覆盖 | 核心模块 > 60%               |

------

## 九、Phase 1 → Phase 2 过渡预留

Phase 1 中已为 Phase 2 预留了以下扩展点：

| 扩展点   | 预留位置                    | Phase 2 计划                      |
| -------- | --------------------------- | --------------------------------- |
| 查询改写 | `query_understanding_node`  | 增加 LLM 改写 + 指代消解          |
| 多路检索 | `RAGRetriever.retrieve()`   | 增加 Sparse(BM25) + RRF融合       |
| Rerank   | `RAGRetriever.retrieve()`   | 增加 Cross-Encoder 重排           |
| 语义缓存 | `infra/cache/` 目录预留     | Redis Stack 向量搜索              |
| 语义分块 | `DocumentChunker`           | 增加 `SemanticSplitterNodeParser` |
| 人工审查 | LangGraph Checkpoint 已启用 | 增加 `interrupt_before`           |
| LLM追踪  | 日志模块                    | 集成 LangFuse                     |
| 长期记忆 | `MemoryManager`             | 增加 PostgreSQL + Milvus 语义搜索 |
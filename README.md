# Enterprise QA Assistant

> 企业级智能问答助手 - 基于 RAG 和 LangGraph 的对话系统

## 项目概述

Enterprise QA Assistant 是一个企业级智能问答助手平台，核心功能包括:

- **RAG (检索增强生成)**: 基于文档检索的智能问答
- **LangGraph 对话编排**: 灵活的多节点对话流程管理
- **异步文档处理**: 支持 PDF/DOCX/MD/TXT 文档的自动摄取
- **优雅降级**: 当 RAG 质量不足时自动降级到轻量模型
- **多轮对话**: 支持会话上下文记忆

## 技术架构

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

## 技术栈

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

## 快速开始

### 前置要求

- Python 3.11+
- Docker 和 Docker Compose
- Poetry (Python 包管理)

### 1. 环境配置

```bash
# 克隆项目
git clone <repository-url>
cd enterprise-qa-assistant

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入必要的配置
# - OPENAI_API_KEY: OpenAI API 密钥
# - 其他配置可根据需要调整
```

### 2. 启动基础设施服务

```bash
# 启动 Docker 服务 (PostgreSQL, Redis, Milvus)
make up

# 查看服务状态
docker compose -f docker/docker-compose.yml ps
```

### 3. 安装依赖

```bash
# 安装项目依赖
make setup

# 或手动安装
poetry install
```

### 4. 启动服务

```bash
# 开发模式启动 (热重载)
make dev

# 后台启动
make up-api
```

### 5. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 详细健康检查
curl http://localhost:8000/health/detail

# 访问 API 文档
open http://localhost:8000/docs
```

## API 使用示例

### 1. 上传文档

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@hr_policy.md" \
  -F "collection=hr_docs"
```

### 2. 问答

```bash
# 同步问答
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "公司的年假制度是什么？",
    "collection": "hr_docs"
  }'

# 流式问答
curl -X POST "http://localhost:8000/api/v1/chat/completions/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "公司的年假制度是什么？",
    "stream": true
  }'
```

### 3. 多轮对话

```bash
# 第一轮
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"message": "什么是RAG？"}')
SESSION_ID=$(echo $RESPONSE | jq -r '.session_id')

# 第二轮 (使用相同 session_id)
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"它有什么优势？\", \"session_id\": \"$SESSION_ID\"}"
```

## 测试

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

## 项目结构

```
enterprise-qa-assistant/
├── src/
│   ├── api/                    # FastAPI 应用层
│   │   ├── main.py            # 应用入口
│   │   ├── dependencies.py    # 依赖注入
│   │   └── routers/           # API 路由
│   ├── core/                   # 核心业务层
│   │   ├── orchestrator/      # 对话编排
│   │   ├── memory/            # 记忆系统
│   │   └── rag/              # RAG 管道
│   ├── infra/                 # 基础设施层
│   │   ├── config/           # 配置管理
│   │   ├── database/         # 数据库客户端
│   │   └── queue/            # 异步任务队列
│   └── schemas/              # 数据模型
├── tests/                    # 测试目录
├── scripts/                  # 工具脚本
├── docker/                   # Docker 配置
└── docs/                     # 文档
```

## 配置说明

主要配置项 (见 `.env.example`):

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | 必填 |
| `PRIMARY_LLM_MODEL` | 主力模型 | `gpt-4o` |
| `FALLBACK_LLM_MODEL` | 降级模型 | `gpt-4o-mini` |
| `RAG_CHUNK_SIZE` | 文档分块大小 | `512` |
| `RAG_TOP_K` | 检索返回数量 | `5` |
| `RAG_MIN_CONFIDENCE` | 最低置信度 | `0.7` |

## 开发指南

### 代码规范

- 使用中文注释
- 所有函数必须有类型注解
- 使用 structlog 进行结构化日志

### Git 提交规范

```
<类型>: <简短描述>

<可选的详细说明>
```

类型: feat, fix, refactor, docs, test, chore

## 文档

- [API 文档](API.md) - 详细的 API 接口文档
- [设计文档](设计文档.md) - 系统设计详细说明
- [Phase 1 任务跟踪](Phase-1-任务进度跟踪.md) - 开发进度跟踪

## License

MIT
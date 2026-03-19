"""测试夹具配置

提供单元测试、集成测试和 E2E 测试共用的测试夹具。
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport
from llama_index.core import Document

from src.api.main import create_app
from src.api.dependencies import get_orchestrator
from src.core.orchestrator.state import OrchestratorResult
from src.infra.config.settings import Settings
from src.schemas.chat import MessageRole


# ============================================================
# Session-scoped Event Loop (用于所有测试)
# ============================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建 session 级别的 event loop

    整个测试会话共享一个 event loop，避免 fixture 嵌套时的兼容性问题。
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================
# 测试配置 Fixture
# ============================================================

@pytest.fixture
def test_settings() -> Settings:
    """测试环境配置

    使用独立的测试数据库，避免污染生产/开发数据。
    """
    return Settings(
        ENV="test",
        DEBUG=True,
        APP_NAME="Enterprise QA Assistant Test",
        APP_VERSION="0.1.0",
        POSTGRES_DB="qa_assistant_test",
        # 使用 DashScope mock API key
        DASHSCOPE_API_KEY="sk-test-mock-key-for-testing-only",
        DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1",
        PRIMARY_LLM_MODEL="qwen3-vl-flash",
        FALLBACK_LLM_MODEL="qwen3-vl-flash",
        EMBEDDING_MODEL="text-embedding-v4",
        EMBEDDING_DIMENSION=1024,
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        REDIS_DB=1,  # 使用独立的 Redis DB
        MILVUS_HOST="localhost",
        MILVUS_PORT=19530,
        MILVUS_COLLECTION_NAME="knowledge_base_test",
    )


@pytest.fixture
def mock_postgres_pool() -> MagicMock:
    """Mock PostgreSQL 连接池

    返回一个 MagicMock 对象，模拟 asyncpg Pool。
    """
    pool = MagicMock()
    pool.fetchval = AsyncMock(return_value=1)
    pool.fetch = AsyncMock(return_value=[])
    pool.fetchrow = AsyncMock(return_value=None)
    pool.execute = AsyncMock(return_value=None)
    pool.acquire = AsyncMock()
    pool.release = AsyncMock()
    return pool


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Mock Redis 客户端

    返回一个 AsyncMock 对象，模拟 redis.asyncio.Redis。
    """
    redis = AsyncMock()
    redis.rpush = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.llen = AsyncMock(return_value=0)
    redis.lrange = AsyncMock(return_value=[])
    redis.exists = AsyncMock(return_value=1)
    redis.delete = AsyncMock(return_value=1)
    redis.ltrim = AsyncMock(return_value=True)
    redis.set = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.close = AsyncMock()
    return redis


@pytest.fixture
def mock_milvus_client() -> MagicMock:
    """Mock Milvus 客户端

    返回一个 MagicMock 对象，模拟 pymilvus.MilvusClient。
    """
    client = MagicMock()
    client.search = MagicMock(return_value=[[]])
    client.insert = MagicMock(return_value={"insert_count": 0})
    client.query = MagicMock(return_value=[])
    client.list_collections = MagicMock(return_value=[])
    client.has_collection = MagicMock(return_value=False)
    client.create_collection = MagicMock()
    client.close = MagicMock()
    return client


# ============================================================
# LangChain/LlamaIndex Mock Fixtures
# ============================================================

@pytest.fixture
def mock_embedding_model() -> MagicMock:
    """Mock OpenAI Embedding 模型

    返回一个 MagicMock 对象，模拟 OpenAIEmbedding。
    """
    model = MagicMock()
    model.aget_text_embedding = AsyncMock(return_value=[0.1] * 3072)
    model.aget_query_embedding = AsyncMock(return_value=[0.1] * 3072)
    return model


@pytest.fixture
def mock_llm_response() -> MagicMock:
    """Mock LLM 响应

    返回一个 MagicMock 对象，模拟 ChatOpenAI 的响应。
    """
    response = MagicMock()
    response.content = "这是一个测试回答。"
    response.usage_metadata = {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50}
    response.additional_kwargs = {}
    return response


# ============================================================
# 测试文档 Fixture
# ============================================================

@pytest.fixture
def sample_documents() -> list[Document]:
    """示例文档列表

    用于测试文档处理和分块功能。
    """
    return [
        Document(
            text="这是一个测试文档。" * 50,
            metadata={"source": "test1.txt", "page": 1}
        ),
        Document(
            text="这是另一个测试文档。" * 50,
            metadata={"source": "test2.txt", "page": 2}
        ),
    ]


@pytest.fixture
def sample_chinese_document() -> Document:
    """中文示例文档

    用于测试中文分块功能。
    """
    content = """
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
    return Document(text=content, metadata={"source": "hr_policy.md"})


# ============================================================
# API 测试客户端 Fixture
# ============================================================

@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """异步 HTTP 测试客户端

    使用 ASGITransport 直接连接到 FastAPI 应用实例，
    避免启动真实的 HTTP 服务器。

    返回的 AsyncClient 有以下属性用于测试:
    - app: FastAPI 应用实例 (用于 dependency_overrides)
    """
    app = create_app()

    # 创建 mock pool - 必须显式设置所有方法，否则 MagicMock 会自动生成新 Mock
    mock_pool = MagicMock()
    mock_pool.fetchval = AsyncMock(return_value=0)
    mock_pool.fetch = AsyncMock(return_value=[])
    mock_pool.fetchrow = AsyncMock(return_value=None)
    mock_pool.execute = AsyncMock(return_value=None)

    # 直接 patch postgres 模块中的全局 _pool 变量
    # 这样 get_postgres_pool() 会直接返回 mock_pool
    import src.infra.database.postgres as pg_module
    original_pool = pg_module._pool
    pg_module._pool = mock_pool

    # Mock orchestrator (ASGITransport 不触发 lifespan，orchestrator 不会初始化)
    mock_orch = MagicMock()
    mock_orch.run = AsyncMock(return_value=OrchestratorResult(
        answer="Mock response",
        citations=[],
        confidence=0.9,
        model_used="mock",
        fallback_used=False,
    ))
    app.dependency_overrides[get_orchestrator] = lambda: mock_orch

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.app = app
        yield client

    # 清理: 恢复原始 pool
    pg_module._pool = original_pool


# ============================================================
# 消息 Fixture
# ============================================================

@pytest.fixture
def sample_user_message() -> dict:
    """示例用户消息"""
    return {
        "role": MessageRole.USER.value,
        "content": "公司的年假制度是什么？",
    }


@pytest.fixture
def sample_assistant_message() -> dict:
    """示例助手消息"""
    return {
        "role": MessageRole.ASSISTANT.value,
        "content": "根据公司制度，年假天数根据工龄不同而不同...",
    }


@pytest.fixture
def sample_conversation_history(
    sample_user_message: dict,
    sample_assistant_message: dict,
) -> list[dict]:
    """示例对话历史"""
    return [sample_user_message, sample_assistant_message]

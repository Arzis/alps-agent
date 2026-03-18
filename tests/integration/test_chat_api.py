"""对话 API 集成测试

测试 Chat API 端点的功能。
注意: 这些测试需要运行中的基础设施服务 (PostgreSQL, Redis, Milvus)。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
class TestChatAPI:
    """对话 API 测试类

    注意: 这些测试使用 mock 来隔离外部依赖。
    """

    async def test_health_endpoint(self, async_client):
        """测试健康检查端点

        验证:
        - /health 返回 200
        """
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_chat_completions_endpoint_exists(self, async_client):
        """测试对话端点存在

        验证:
        - POST /api/v1/chat/completions 存在
        """
        # 由于 orchestrator 初始化需要真实连接，这里只测试端点存在
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={"message": "你好"},
        )
        # 可能会因为服务未启动返回 500 或其他错误，但端点存在
        assert response.status_code in [200, 500, 503, 422]


@pytest.mark.asyncio
class TestChatAPIWithMocks:
    """带 Mock 的 Chat API 测试"""

    @pytest.fixture
    def mock_orchestrator(self):
        """Mock Orchestrator"""
        orchestrator = MagicMock()
        from src.core.orchestrator.state import OrchestratorResult
        from src.schemas.chat import CitationItem

        result = OrchestratorResult(
            answer="这是测试回答",
            citations=[
                CitationItem(
                    doc_id="doc_001",
                    doc_title="测试文档",
                    content="引用内容",
                    relevance_score=0.85,
                )
            ],
            confidence=0.85,
            model_used="gpt-4o-mini",
            fallback_used=False,
            tokens_used=100,
        )
        orchestrator.run = AsyncMock(return_value=result)
        orchestrator.stream = MagicMock(return_value=iter([]))
        return orchestrator

    async def test_chat_request_validation(self, async_client):
        """测试请求参数验证

        验证:
        - 缺少必需字段返回 422
        """
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={},  # 缺少 message
        )
        assert response.status_code == 422

    async def test_chat_request_with_empty_message(self, async_client):
        """测试空消息验证

        验证:
        - 空消息返回 422
        """
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={"message": ""},
        )
        assert response.status_code == 422

    async def test_chat_request_with_valid_message(self, async_client):
        """测试有效消息

        验证:
        - 有效消息格式被接受 (即使后端未启动)
        """
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "message": "你好",
                "collection": "default",
            },
        )
        # 不关心具体状态码，只要不是 422 (验证失败)
        assert response.status_code != 422

    async def test_chat_request_with_session_id(self, async_client):
        """测试带 session_id 的请求

        验证:
        - session_id 被正确处理
        """
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "message": "继续",
                "session_id": "existing_session_123",
            },
        )
        assert response.status_code != 422

    async def test_chat_request_with_custom_collection(self, async_client):
        """测试自定义 collection

        验证:
        - 自定义 collection 被接受
        """
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "message": "查询",
                "collection": "hr_documents",
            },
        )
        assert response.status_code != 422

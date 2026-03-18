"""短期记忆单元测试

测试 ShortTermMemory 类的会话历史管理功能。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.core.memory.short_term import ShortTermMemory
from src.schemas.chat import ChatMessage, MessageRole


class TestShortTermMemory:
    """ShortTermMemory 测试类"""

    @pytest.fixture
    def memory(self, mock_redis: AsyncMock) -> ShortTermMemory:
        """创建 ShortTermMemory 实例"""
        return ShortTermMemory(
            redis=mock_redis,
            ttl=3600,
            max_messages=20,
        )

    def test_key_format(self, memory: ShortTermMemory):
        """测试 Redis Key 格式

        验证:
        - key 格式正确
        """
        key = memory._key("session_123")
        assert key == "memory:short:session_123", "Key 格式应该正确"

    @pytest.mark.asyncio
    async def test_add_message(self, memory: ShortTermMemory, mock_redis: AsyncMock):
        """测试添加单条消息

        验证:
        - 消息被正确添加到 Redis
        - TTL 被设置
        """
        await memory.add_message(
            session_id="sess_001",
            role=MessageRole.USER,
            content="你好",
        )

        mock_redis.rpush.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_message_with_metadata(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试带元数据的消息

        验证:
        - 元数据被正确保存
        """
        metadata = {"source": "test", "confidence": 0.95}
        await memory.add_message(
            session_id="sess_001",
            role=MessageRole.USER,
            content="测试消息",
            metadata=metadata,
        )

        # 验证 rpush 被调用 (消息被添加)
        mock_redis.rpush.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_exchange(self, memory: ShortTermMemory, mock_redis: AsyncMock):
        """测试添加一轮完整对话

        验证:
        - 用户消息和助手回复都被添加
        """
        await memory.add_exchange(
            session_id="sess_001",
            user_message="你好",
            assistant_message="你好！有什么可以帮助你的吗？",
        )

        # 应该调用两次 rpush (用户消息 + 助手回复)
        assert mock_redis.rpush.call_count == 2
        # 应该调用两次 expire
        assert mock_redis.expire.call_count == 2

    @pytest.mark.asyncio
    async def test_get_messages(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试获取消息

        验证:
        - 正确调用 lrange
        - 消息被正确反序列化
        """
        # 模拟 Redis 返回的消息 JSON
        messages_json = [
            ChatMessage(role=MessageRole.USER, content="Hello").model_dump_json(),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi").model_dump_json(),
        ]
        mock_redis.lrange = AsyncMock(return_value=messages_json)

        messages = await memory.get_messages("sess_001")

        mock_redis.lrange.assert_called_once()
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_get_messages_with_last_n(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试获取最近 N 条消息

        验证:
        - last_n 参数被正确传递
        """
        mock_redis.lrange = AsyncMock(return_value=[])

        await memory.get_messages("sess_001", last_n=5)

        # lrange 应该用负索引获取最后 N 条
        mock_redis.lrange.assert_called_with("memory:short:sess_001", -5, -1)

    @pytest.mark.asyncio
    async def test_get_formatted_history(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试获取格式化历史

        验证:
        - 返回正确的格式 (list[dict])
        """
        messages_json = [
            ChatMessage(role=MessageRole.USER, content="Hello").model_dump_json(),
            ChatMessage(role=MessageRole.ASSISTANT, content="Hi").model_dump_json(),
        ]
        mock_redis.lrange = AsyncMock(return_value=messages_json)

        history = await memory.get_formatted_history("sess_001")

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_formatted_history_with_turns(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试获取最近 N 轮对话

        验证:
        - 只返回指定轮数的历史
        """
        # 模拟 6 条消息 (3 轮对话)
        messages_json = [
            ChatMessage(role=MessageRole.USER, content=f"User {i}").model_dump_json()
            for i in range(3)
        ] + [
            ChatMessage(role=MessageRole.ASSISTANT, content=f"Assistant {i}").model_dump_json()
            for i in range(3)
        ]
        mock_redis.lrange = AsyncMock(return_value=messages_json)

        history = await memory.get_formatted_history("sess_001", last_n_turns=1)

        # 应该只获取 2 条消息 (1 轮 = user + assistant)
        assert mock_redis.lrange.call_count == 1

    @pytest.mark.asyncio
    async def test_clear_session(self, memory: ShortTermMemory, mock_redis: AsyncMock):
        """测试清除会话

        验证:
        - delete 被调用
        - 正确的 key 被删除
        """
        await memory.clear("sess_001")

        mock_redis.delete.assert_called_once_with("memory:short:sess_001")

    @pytest.mark.asyncio
    async def test_max_messages_trimming(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试消息数量限制

        验证:
        - 超过 max_messages 时，旧消息被裁剪
        """
        # 模拟超过限制的消息数量
        mock_redis.llen = AsyncMock(return_value=25)  # 超过 20
        mock_redis.ltrim = AsyncMock()

        await memory.add_message(
            session_id="sess_001",
            role=MessageRole.USER,
            content="消息",
        )

        # 应该调用 ltrim 来裁剪
        mock_redis.ltrim.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_exists(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试会话存在性检查

        验证:
        - 正确使用 exists 命令
        """
        mock_redis.exists = AsyncMock(return_value=1)

        exists = await memory.exists("sess_001")

        assert exists is True
        mock_redis.exists.assert_called_once_with("memory:short:sess_001")

    @pytest.mark.asyncio
    async def test_session_not_exists(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试会话不存在

        验证:
        - 返回 False
        """
        mock_redis.exists = AsyncMock(return_value=0)

        exists = await memory.exists("nonexistent")

        assert exists is False


class TestShortTermMemoryEdgeCases:
    """ShortTermMemory 边界情况测试"""

    @pytest.fixture
    def memory(self, mock_redis: AsyncMock) -> ShortTermMemory:
        """创建 ShortTermMemory 实例"""
        return ShortTermMemory(
            redis=mock_redis,
            ttl=3600,
            max_messages=20,
        )

    @pytest.mark.asyncio
    async def test_empty_session_get_messages(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试空会话获取消息

        验证:
        - 返回空列表
        """
        mock_redis.lrange = AsyncMock(return_value=[])

        messages = await memory.get_messages("empty_session")

        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_empty_history_format(self, memory: ShortTermMemory, mock_redis: AsyncMock):
        """测试空历史格式化

        验证:
        - 返回空列表
        """
        mock_redis.lrange = AsyncMock(return_value=[])

        history = await memory.get_formatted_history("empty_session")

        assert history == []

    @pytest.mark.asyncio
    async def test_all_message_roles(
        self, memory: ShortTermMemory, mock_redis: AsyncMock
    ):
        """测试所有消息角色

        验证:
        - USER, ASSISTANT, SYSTEM 角色都能正确保存
        """
        for role in [MessageRole.USER, MessageRole.ASSISTANT, MessageRole.SYSTEM]:
            await memory.add_message(
                session_id="sess_roles",
                role=role,
                content=f"Test {role.value}",
            )

        # 验证 rpush 被调用 3 次
        assert mock_redis.rpush.call_count == 3

    @pytest.mark.asyncio
    async def test_custom_ttl(self, mock_redis: AsyncMock):
        """测试自定义 TTL

        验证:
        - 使用配置的 TTL 值
        """
        custom_ttl = 7200
        memory = ShortTermMemory(
            redis=mock_redis,
            ttl=custom_ttl,
            max_messages=20,
        )

        await memory.add_message(
            session_id="sess_001",
            role=MessageRole.USER,
            content="Hello",
        )

        # 验证 expire 使用自定义 TTL
        call_args = mock_redis.expire.call_args
        assert call_args[0][1] == custom_ttl

"""短期记忆模块 - 基于 Redis 实现会话历史存储"""

import json
from datetime import datetime
from redis.asyncio import Redis
import structlog

from src.schemas.chat import ChatMessage, MessageRole

logger = structlog.get_logger()


class ShortTermMemory:
    """
    短期记忆 - Redis 实现

    存储当前会话的对话历史，支持:
    - 追加消息
    - 获取最近 N 轮消息
    - 自动过期 (TTL)
    - 消息数量限制
    """

    def __init__(self, redis: Redis, ttl: int = 86400, max_messages: int = 20):
        """
        初始化短期记忆

        Args:
            redis: Redis 异步客户端实例
            ttl: 过期时间 (秒)，默认 24 小时
            max_messages: 最大保存消息数，默认 20 条
        """
        self.redis = redis
        self.ttl = ttl
        self.max_messages = max_messages

    def _key(self, session_id: str) -> str:
        """生成 Redis 键名

        Args:
            session_id: 会话 ID

        Returns:
            str: Redis 键名，格式: memory:short:{session_id}
        """
        return f"memory:short:{session_id}"

    async def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        """添加一条消息到会话历史

        Args:
            session_id: 会话 ID
            role: 消息角色 (user/assistant/system)
            content: 消息内容
            metadata: 额外元数据 (可选)
        """
        key = self._key(session_id)
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        # 使用 Redis List 的 rpush 添加到列表末尾
        await self.redis.rpush(key, message.model_dump_json())
        # 设置过期时间
        await self.redis.expire(key, self.ttl)

        # 如果超过最大消息数，裁剪前面的旧消息
        length = await self.redis.llen(key)
        if length > self.max_messages:
            # ltrim 保留最后 max_messages 条
            await self.redis.ltrim(key, length - self.max_messages, -1)

    async def add_exchange(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        metadata: dict | None = None,
    ) -> None:
        """添加一轮完整对话 (用户消息 + 助手回复)

        Args:
            session_id: 会话 ID
            user_message: 用户消息内容
            assistant_message: 助手回复内容
            metadata: 额外元数据 (可选)
        """
        # 先添加用户消息
        await self.add_message(session_id, MessageRole.USER, user_message)
        # 再添加助手回复
        await self.add_message(
            session_id, MessageRole.ASSISTANT, assistant_message, metadata
        )

    async def get_messages(
        self, session_id: str, last_n: int | None = None
    ) -> list[ChatMessage]:
        """获取会话消息

        Args:
            session_id: 会话 ID
            last_n: 只获取最后 N 条消息 (可选，None 表示获取全部)

        Returns:
            list[ChatMessage]: 消息列表
        """
        key = self._key(session_id)

        if last_n:
            # 获取最后 N 条消息 (从末尾往前数)
            raw_messages = await self.redis.lrange(key, -last_n, -1)
        else:
            # 获取全部消息
            raw_messages = await self.redis.lrange(key, 0, -1)

        # 反序列化消息
        return [ChatMessage.model_validate_json(raw) for raw in raw_messages]

    async def get_formatted_history(
        self, session_id: str, last_n_turns: int | None = None
    ) -> list[dict[str, str]]:
        """获取格式化的对话历史 (用于 LLM 上下文)

        Args:
            session_id: 会话 ID
            last_n_turns: 只获取最后 N 轮对话 (每轮 = 用户+助手)

        Returns:
            list[dict]: 格式化的消息列表，格式: [{"role": "user", "content": "..."}]
        """
        # 每轮对话 = 2 条消息 (user + assistant)
        # 如果指定 last_n_turns，则获取 last_n_turns * 2 条消息
        last_n = last_n_turns * 2 if last_n_turns else None
        messages = await self.get_messages(session_id, last_n=last_n)

        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

    async def clear(self, session_id: str) -> None:
        """清除会话的所有记忆

        Args:
            session_id: 会话 ID
        """
        key = self._key(session_id)
        await self.redis.delete(key)
        logger.info("session_memory_cleared", session_id=session_id)

    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在

        Args:
            session_id: 会话 ID

        Returns:
            bool: 会话是否存在（是否有消息）
        """
        key = self._key(session_id)
        result = await self.redis.exists(key)
        return result > 0

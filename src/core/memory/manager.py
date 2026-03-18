"""记忆管理器 - 统一管理多层记忆系统"""

from redis.asyncio import Redis
from src.core.memory.short_term import ShortTermMemory
from src.schemas.chat import ChatMessage, MessageRole
from src.infra.config.settings import Settings


class MemoryManager:
    """
    记忆管理器

    Phase 1: 仅实现短期记忆 (Redis)
    Phase 2+: 会扩展长期记忆和语义记忆

    职责:
    - 提供统一的记忆接口
    - 管理短期记忆 (当前会话)
    - 为编排引擎提供上下文加载/保存功能
    """

    def __init__(self, redis: Redis, settings: Settings):
        """
        初始化记忆管理器

        Args:
            redis: Redis 异步客户端
            settings: 应用配置
        """
        self.short_term = ShortTermMemory(
            redis=redis,                                    # Redis 客户端
            ttl=settings.SESSION_TTL,                        # 会话 TTL (默认24小时)
            max_messages=settings.MAX_CONCURRENT_REQUESTS * 2,  # 最大消息数 (保留一些余量)
        )

    async def load_context(
        self, session_id: str, max_turns: int = 5
    ) -> list[dict[str, str]]:
        """
        加载对话上下文

        Phase 1: 仅从短期记忆加载
        Phase 2+: 融合短期记忆 + 长期记忆 + 语义记忆

        Args:
            session_id: 会话 ID
            max_turns: 最大加载的对话轮数 (每轮=用户+助手)

        Returns:
            list[dict]: 格式化的消息列表，格式: [{"role": "user", "content": "..."}]
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
    ) -> None:
        """
        保存一轮对话

        Args:
            session_id: 会话 ID
            user_message: 用户消息
            assistant_message: 助手回复
            metadata: 额外元数据 (如置信度、使用的模型等)
        """
        await self.short_term.add_exchange(
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            metadata=metadata,
        )

    async def clear_session(self, session_id: str) -> None:
        """
        清除会话记忆

        Args:
            session_id: 会话 ID
        """
        await self.short_term.clear(session_id)

"""对话编排引擎模块

这是 Phase 1 的桩实现。
Week 3 会实现 RAG 管道，Week 4 会实现 LangGraph 编排。
"""

from dataclasses import dataclass, field
from typing import AsyncGenerator

import structlog

from src.schemas.chat import CitationItem, ConversationHistory, SessionInfo
from src.core.memory.manager import MemoryManager
from src.core.rag.ingestion.pipeline import get_ingestion_pipeline

logger = structlog.get_logger()


@dataclass
class OrchestratorResult:
    """编排引擎返回结果

    包含对话回答的所有信息。
    """
    answer: str = ""                                          # 回答内容
    citations: list[CitationItem] = field(default_factory=list)  # RAG 引用
    confidence: float = 0.0                                  # 置信度
    model_used: str = ""                                      # 使用的模型
    fallback_used: bool = False                               # 是否使用了降级模型
    tokens_used: int = 0                                     # 消耗的 token 数


@dataclass
class StreamEvent:
    """流式事件

    用于 SSE 流式响应。
    """
    event: str  # 事件类型
    data: str   # 事件数据


class ConversationOrchestrator:
    """
    对话编排器

    职责:
    1. 管理会话记忆
    2. 处理对话请求 (Phase 1 桩实现)
    3. 管理会话持久化

    Note:
        Week 3 实现 RAG 管道后，这里会调用 LangGraph 编排。
        Week 4 实现 LangGraph 编排后，这里会管理图的执行。
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        pg_pool,
    ):
        """
        初始化编排器

        Args:
            memory_manager: 记忆管理器实例
            pg_pool: PostgreSQL 连接池
        """
        self.memory = memory_manager
        self.pg_pool = pg_pool

    async def run(
        self,
        session_id: str,
        message: str,
        collection: str = "default",
    ) -> OrchestratorResult:
        """
        执行一轮对话 (同步模式)

        Phase 1: 桩实现，直接返回消息
        Week 4: 调用 LangGraph 编排

        Args:
            session_id: 会话 ID
            message: 用户消息
            collection: 知识库集合

        Returns:
            OrchestratorResult: 包含回答结果的 OrchestratorResult
        """
        # 加载对话历史
        history = await self.memory.load_context(session_id, max_turns=5)

        logger.info(
            "orchestrator_run",
            session_id=session_id,
            message_length=len(message),
            history_turns=len(history) // 2,
            collection=collection,
        )

        # ============================================================
        # Phase 1 桩实现 - 后续 Week 3/4 会替换为真正的 RAG + LangGraph
        # ============================================================
        answer = f"[Phase 1 桩实现] 收到消息: {message[:50]}..."

        # 保存对话到记忆
        await self.memory.save_turn(
            session_id=session_id,
            user_message=message,
            assistant_message=answer,
            metadata={"collection": collection},
        )

        return OrchestratorResult(
            answer=answer,
            citations=[],
            confidence=0.0,
            model_used="stub",
            fallback_used=False,
            tokens_used=0,
        )

    async def stream(
        self,
        session_id: str,
        message: str,
        collection: str = "default",
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        执行一轮对话 (流式模式)

        Phase 1: 桩实现

        Args:
            session_id: 会话 ID
            message: 用户消息
            collection: 知识库集合

        Yields:
            StreamEvent: 流式事件
        """
        # 发送处理中状态
        yield StreamEvent(event="status", data='"processing"')

        # 模拟流式输出
        result = await self.run(session_id, message, collection)

        # 发送 token 事件 (模拟)
        for i in range(0, len(result.answer), 10):
            yield StreamEvent(
                event="token",
                data=f'"{result.answer[i:i+10]}"',
            )

        # 发送完成事件
        yield StreamEvent(event="done", data="{}")

    async def get_history(
        self, session_id: str, limit: int = 50
    ) -> ConversationHistory:
        """
        获取对话历史

        Args:
            session_id: 会话 ID
            limit: 最大消息数

        Returns:
            ConversationHistory: 对话历史
        """
        messages = await self.memory.short_term.get_messages(session_id, last_n=limit)

        return ConversationHistory(
            session_id=session_id,
            messages=messages,
            total_count=len(messages),
        )

    async def list_sessions(
        self, page: int = 1, page_size: int = 20
    ) -> list[SessionInfo]:
        """
        获取会话列表

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            list[SessionInfo]: 会话列表
        """
        # Phase 1 桩实现 - 后续从数据库查询
        return []

    async def delete_session(self, session_id: str) -> None:
        """
        删除会话

        Args:
            session_id: 会话 ID
        """
        await self.memory.clear_session(session_id)
        logger.info("session_deleted", session_id=session_id)


async def init_orchestrator(
    pg_pool,
    redis_client,
    milvus_client,
    settings,
) -> ConversationOrchestrator:
    """
    初始化编排引擎

    在应用启动时调用，创建编排引擎实例。

    Args:
        pg_pool: PostgreSQL 连接池
        redis_client: Redis 客户端
        milvus_client: Milvus 客户端
        settings: 应用配置

    Returns:
        ConversationOrchestrator: 编排引擎实例
    """
    # 创建记忆管理器
    memory_manager = MemoryManager(
        redis=redis_client,
        settings=settings,
    )

    # 创建编排引擎
    orchestrator = ConversationOrchestrator(
        memory_manager=memory_manager,
        pg_pool=pg_pool,
    )

    logger.info("orchestrator_initialized")
    return orchestrator

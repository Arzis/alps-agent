"""缓存查询节点模块

在 RAG 检索之前检查语义缓存，提高响应速度。
"""

from langchain_core.messages import AIMessage

import structlog

from src.core.orchestrator.state import ConversationState
from src.infra.cache.cache_manager import CacheManager

logger = structlog.get_logger()


class CacheLookupNode:
    """缓存查询节点 - 在 RAG 之前检查缓存"""

    def __init__(self, cache_manager: CacheManager):
        """初始化缓存查询节点

        Args:
            cache_manager: 缓存管理器实例
        """
        self.cache = cache_manager

    async def execute(self, state: ConversationState) -> ConversationState:
        """检查语义缓存

        Args:
            state: 当前对话状态

        Returns:
            ConversationState: 更新后的状态 (包含 cache_hit, answer, citations 等)
        """
        query = state.rewritten_query or state.user_message
        collection = state.collection

        cache_hit = await self.cache.get(query, collection)

        if cache_hit:
            logger.info(
                "cache_hit_in_graph",
                session_id=state.session_id,
                similarity=round(cache_hit.similarity, 4),
            )
            state.rag_answer = cache_hit.answer
            state.citations = cache_hit.citations
            state.confidence = cache_hit.confidence
            state.model_used = "cache"
            state.fallback_used = False
            state.cache_hit = True
        else:
            state.cache_hit = False
            logger.debug(
                "cache_miss_in_graph",
                session_id=state.session_id,
                query_length=len(query),
            )

        return state


def should_skip_rag(state: ConversationState) -> str:
    """条件路由: 缓存命中则跳过 RAG

    路由逻辑:
    - 缓存命中 → 跳过 RAG, 直接结束
    - 闲聊意图 → Codex (不经过 RAG)
    - 知识问答 → RAG Agent

    Args:
        state: 当前对话状态

    Returns:
        str: 路由目标节点标识
    """
    # 缓存命中 → 跳过 RAG, 直接结束
    if state.get("cache_hit", False):
        return "skip_to_end"

    # 闲聊意图 → Codex (不经过 RAG)
    intent = state.get("intent", "general")
    if intent in ("chitchat", "general"):
        return "codex_fallback"

    # 知识问答 → RAG Agent
    return "rag_agent"

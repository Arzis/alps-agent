"""对话编排引擎模块

基于 LangGraph 的对话编排引擎，管理图的执行和状态流转。
"""

import time
import json
import asyncio
from dataclasses import dataclass, field
from typing import AsyncGenerator, Callable

import structlog

from src.schemas.chat import CitationItem, ConversationHistory, SessionInfo, ChatMessage, MessageRole
from src.core.memory.manager import MemoryManager
from src.core.orchestrator.state import ConversationState, OrchestratorResult
from src.core.orchestrator.graph import create_conversation_graph, compile_graph
from src.core.orchestrator.nodes.query_understanding import QueryUnderstandingNode
from src.core.orchestrator.nodes.cache_lookup import CacheLookupNode
from src.core.orchestrator.nodes.rag_agent import RAGAgentNode
from src.core.orchestrator.nodes.fallback_node import FallbackNode
from src.core.orchestrator.nodes.quality_gate import QualityGateNode
from src.core.orchestrator.nodes.response_synthesizer import ResponseSynthesizerNode
from src.core.rag.retrieval.retriever import RAGRetriever
from src.core.rag.retrieval.dense import DenseRetriever
from src.core.rag.synthesis.synthesizer import AnswerSynthesizer
from src.infra.cache.cache_manager import CacheManager
from src.infra.cache.semantic_cache import SemanticCache
from src.infra.config.settings import Settings
from src.infra.embedding.provider import create_embedding_provider

logger = structlog.get_logger()


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

    基于 LangGraph 的多节点对话编排引擎。

    职责：
    1. 管理会话记忆
    2. 处理对话请求 (调用 LangGraph)
    3. 管理会话持久化

    节点流程 (Phase 2):
    query_understanding → cache_lookup → [条件分支]
                                              ↓
                    ┌─────────────────────────┼─────────────────────────┐
                    ↓                         ↓                         ↓
               skip_to_end               codex_fallback              rag_agent
               (缓存命中)                    (闲聊)                 (知识问答)
                    ↓                         ↓                         ↓
                    END                       END                   quality_gate
                                                                       ↓
                                            ┌─────────────────────────┼─────────────────────────┐
                                            ↓                         ↓                         ↓
                                       direct                      fallback                    reject
                                            ↓                         ↓                         ↓
                                            └─────────────────────────┴─────────────────────────┘
                                                                      ↓
                                                             response_synthesizer
                                                                      ↓
                                                                     END
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        pg_pool,
        compiled_graph: Callable,
        llm_tracer=None,
    ):
        """
        初始化编排器

        Args:
            memory_manager: 记忆管理器实例
            pg_pool: PostgreSQL 连接池
            compiled_graph: 编译后的 LangGraph
            llm_tracer: LLM 追踪器 (可选，用于 LangFuse)
        """
        self.memory = memory_manager
        self.pg_pool = pg_pool
        self.graph = compiled_graph
        self.tracer = llm_tracer

    async def run(
        self,
        session_id: str,
        message: str,
        collection: str = "default",
        user_id: str | None = None,
    ) -> OrchestratorResult:
        """
        执行一轮对话 (同步模式)

        调用 LangGraph 编排执行完整流程。

        Args:
            session_id: 会话 ID
            message: 用户消息
            collection: 知识库集合
            user_id: 用户 ID (用于隔离)

        Returns:
            OrchestratorResult: 包含回答结果的 OrchestratorResult
        """
        start_time = time.time()

        # 创建 LangFuse 追踪 (如果启用)
        trace_ctx = None
        if self.tracer:
            trace_ctx = self.tracer.create_trace(
                session_id=session_id,
                name="chat_completion",
                metadata={"user_id": user_id, "collection": collection, "query": message[:200]},
            )

        try:
            # 加载对话历史
            if trace_ctx:
                history_span = trace_ctx.span(name="load_memory")

            history = await self.memory.load_context(session_id, user_id=user_id, max_turns=5)

            if trace_ctx:
                history_span.end()

            logger.info(
                "orchestrator_run",
                user_id=user_id,
                session_id=session_id,
                message_length=len(message),
                history_turns=len(history) // 2,
                collection=collection,
            )

            # 构建初始状态
            initial_state = ConversationState(
                session_id=session_id,
                user_message=message,
                collection=collection,
                history_turns=history,
            )

            # 获取 LangChain 回调 (自动追踪 LLM 调用)
            langfuse_callback = None
            if trace_ctx and self.tracer:
                langfuse_callback = self.tracer.get_langchain_callback(session_id)

            thread_config = {}
            if langfuse_callback:
                thread_config["callbacks"] = [langfuse_callback]

            # 调用 LangGraph 执行
            final_state = await self.graph.ainvoke(initial_state, config=thread_config)

            # 从最终状态提取结果
            # 注意：最终状态可能是 OrchestratorResult 或 ConversationState
            if isinstance(final_state, OrchestratorResult):
                result = final_state
            else:
                # 如果返回的是 ConversationState，转换为 OrchestratorResult
                result = self._state_to_result(final_state)

            # 记录质量分数到 LangFuse
            if trace_ctx:
                trace_ctx.score(name="confidence", value=result.confidence)
                trace_ctx.score(
                    name="cache_hit",
                    value=1.0 if getattr(final_state, "cache_hit", False) else 0.0,
                )

            # 保存对话到记忆
            await self.memory.save_turn(
                session_id=session_id,
                user_id=user_id,
                user_message=message,
                assistant_message=result.answer,
                metadata={
                    "collection": collection,
                    "confidence": result.confidence,
                    "model_used": result.model_used,
                    "fallback_used": result.fallback_used,
                },
            )

            # 更新会话表
            await self._upsert_session(
                session_id=session_id,
                user_id=user_id,
                title=message[:50] if not None else None,  # 用第一轮用户消息作为标题
            )

            # 计算延迟
            latency_ms = (time.time() - start_time) * 1000

            # 更新 Trace
            if trace_ctx:
                trace_ctx.update(
                    output=result.answer[:500],
                    metadata={
                        "latency_ms": latency_ms,
                        "cache_hit": getattr(final_state, "cache_hit", False),
                        "fallback_used": result.fallback_used,
                    },
                )

            logger.info(
                "orchestrator_completed",
                session_id=session_id,
                latency_ms=latency_ms,
                confidence=result.confidence,
                fallback_used=result.fallback_used,
            )

            return result

        except Exception as e:
            if trace_ctx:
                trace_ctx.score(name="error", value=1.0, comment=str(e))
            logger.error(
                "orchestrator_failed",
                session_id=session_id,
                error=str(e),
            )
            raise
        finally:
            if trace_ctx:
                trace_ctx.flush()

    async def stream(
        self,
        session_id: str,
        message: str,
        collection: str = "default",
        user_id: str | None = None,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        执行一轮对话 (流式模式)

        当前实现：先完整执行，再逐 token 流式返回。
        真正的 LLM 流式输出需要修改 synthesizer 使用 astream。

        Args:
            session_id: 会话 ID
            message: 用户消息
            collection: 知识库集合
            user_id: 用户 ID (用于隔离)

        Yields:
            StreamEvent: 流式事件
        """
        try:
            # 同步执行获取结果
            result = await self.run(session_id, message, collection, user_id)

            # 发送引用事件
            if result.citations:
                citations_data = [
                    {
                        "doc_id": c.doc_id,
                        "doc_title": c.doc_title,
                        "content": c.content,
                        "relevance_score": c.relevance_score,
                    }
                    for c in result.citations
                ]
                yield StreamEvent(
                    event="citation",
                    data=json.dumps(citations_data),
                )

            # 逐 token 流式返回（模拟流式效果）
            for i in range(0, len(result.answer), 10):
                yield StreamEvent(
                    event="token",
                    data=json.dumps(result.answer[i:i+10]),
                )
                # 小延迟，让浏览器有时间渲染
                await asyncio.sleep(0.01)

            # 发送完成事件
            yield StreamEvent(
                event="done",
                data=json.dumps({
                    "confidence": result.confidence,
                    "model_used": result.model_used,
                    "tokens_used": result.tokens_used,
                }),
            )

        except Exception as e:
            logger.error("stream_failed", session_id=session_id, error=str(e))
            yield StreamEvent(
                event="error",
                data=json.dumps({"error": str(e)}),
            )

    async def get_history(
        self, session_id: str, user_id: str | None = None, limit: int = 50
    ) -> ConversationHistory:
        """
        获取对话历史

        Args:
            session_id: 会话 ID
            user_id: 用户 ID (用于隔离)
            limit: 最大消息数

        Returns:
            ConversationHistory: 对话历史
        """
        messages = await self.memory.short_term.get_messages(session_id, user_id=user_id, last_n=limit)

        return ConversationHistory(
            session_id=session_id,
            messages=messages,
            total_count=len(messages),
        )

    async def list_sessions(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> list[SessionInfo]:
        """
        获取会话列表

        Args:
            user_id: 用户 ID (必须，用于隔离)
            page: 页码
            page_size: 每页数量

        Returns:
            list[SessionInfo]: 会话列表 (仅当前用户的会话)
        """
        try:
            pool = self.pg_pool
            offset = (page - 1) * page_size

            rows = await pool.fetch(
                """
                SELECT session_id, user_id, title, message_count, status, created_at, updated_at
                FROM chat_sessions
                WHERE user_id = $1
                ORDER BY updated_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                page_size,
                offset,
            )

            return [
                SessionInfo(
                    session_id=row["session_id"],
                    user_id=row["user_id"],
                    title=row["title"] or "新对话",
                    message_count=row["message_count"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("list_sessions_failed", user_id=user_id, error=str(e))
            return []

    async def delete_session(self, session_id: str, user_id: str) -> None:
        """
        删除会话

        校验 session 是否属于当前用户，防止跨用户删除。

        Args:
            session_id: 会话 ID
            user_id: 用户 ID (用于校验)
        """
        # 校验 session_id 是否属于该用户
        if not session_id.startswith(f"{user_id}_"):
            logger.warning(
                "session_delete_forbidden",
                user_id=user_id,
                session_id=session_id,
            )
            from src.api.middlewares.error_handler import AppError
            raise AppError(
                message="Cannot delete session belonging to another user",
                status_code=403,
                error_code="FORBIDDEN",
            )

        await self.memory.clear_session(session_id, user_id=user_id)

        # 删除 PostgreSQL 中的会话记录
        try:
            await self.pg_pool.execute(
                "DELETE FROM chat_sessions WHERE session_id = $1",
                session_id,
            )
        except Exception as e:
            logger.error("delete_session_from_db_failed", session_id=session_id, error=str(e))

        logger.info("session_deleted", user_id=user_id, session_id=session_id)

    async def _upsert_session(
        self,
        session_id: str,
        user_id: str | None,
        title: str | None = None,
    ) -> None:
        """创建或更新会话记录

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            title: 会话标题
        """
        if not user_id:
            return

        try:
            # 检查会话是否存在
            exists = await self.pg_pool.fetchval(
                "SELECT 1 FROM chat_sessions WHERE session_id = $1",
                session_id,
            )

            if exists:
                # 更新已有会话
                await self.pg_pool.execute(
                    """
                    UPDATE chat_sessions
                    SET message_count = message_count + 2,
                        updated_at = NOW()
                    WHERE session_id = $1
                    """,
                    session_id,
                )
            else:
                # 创建新会话
                await self.pg_pool.execute(
                    """
                    INSERT INTO chat_sessions (session_id, user_id, title, message_count, status)
                    VALUES ($1, $2, $3, 2, 'active')
                    """,
                    session_id,
                    user_id,
                    title or "新对话",
                )
        except Exception as e:
            logger.error("upsert_session_failed", session_id=session_id, error=str(e))

    def _state_to_result(self, state: ConversationState | dict) -> OrchestratorResult:
        """将 ConversationState 转换为 OrchestratorResult

        用于处理图直接返回 ConversationState 的情况（如缓存命中）。

        Args:
            state: 对话状态 (可能是 ConversationState 对象或字典)

        Returns:
            OrchestratorResult: 编排结果
        """
        # 如果是字典，转换为 ConversationState 对象
        if isinstance(state, dict):
            state = ConversationState(**state)

        # 根据路由决策选择回答
        if state.route == "reject":
            answer = "抱歉，我无法找到与您问题相关的信息，建议您查阅相关文档或联系管理员。"
        elif state.rag_answer:
            answer = state.rag_answer
        else:
            answer = "抱歉，我现在无法回答您的问题，请稍后重试。"

        return OrchestratorResult(
            answer=answer,
            citations=state.citations if not state.fallback_used else [],
            confidence=state.confidence,
            model_used=state.model_used,
            fallback_used=state.fallback_used,
            tokens_used=state.tokens_used,
        )


async def init_orchestrator(
    pg_pool,
    redis_client,
    milvus_client,
    settings: Settings,
) -> ConversationOrchestrator:
    """
    初始化编排引擎

    在应用启动时调用，创建编排引擎实例和 LangGraph。

    Args:
        pg_pool: PostgreSQL 连接池
        redis_client: Redis 客户端
        milvus_client: Milvus 客户端
        settings: 应用配置

    Returns:
        ConversationOrchestrator: 编排引擎实例
    """
    logger.info("init_orchestrator_start")

    # 创建记忆管理器
    memory_manager = MemoryManager(
        redis=redis_client,
        settings=settings,
    )

    # 创建 Embedding Provider
    embedding_provider = create_embedding_provider(settings)

    # 创建 Dense 检索器 (使用 provider)
    dense_retriever = DenseRetriever(
        milvus_client=milvus_client,
        embedding_provider=embedding_provider,
        settings=settings,
    )

    # 创建 RAG 检索器
    rag_retriever = RAGRetriever(dense_retriever=dense_retriever)

    # 创建答案合成器
    synthesizer = AnswerSynthesizer(settings=settings)

    # === 创建缓存节点 (Phase 2) ===
    # 创建 Embedding 函数 (使用 provider)
    async def get_embedding(text: str) -> list[float]:
        """获取文本 Embedding 向量"""
        return await embedding_provider.embed_one(text)

    # 创建语义缓存
    semantic_cache = SemanticCache(
        redis=redis_client,
        embedding_fn=get_embedding,
        similarity_threshold=settings.SEMANTIC_CACHE_THRESHOLD,
        ttl=settings.SEMANTIC_CACHE_TTL,
        embedding_dim=embedding_provider.dimension,
    )

    # 创建缓存管理器
    cache_manager = CacheManager(semantic_cache=semantic_cache)

    # 创建缓存查询节点
    cache_lookup_node = CacheLookupNode(cache_manager=cache_manager)

    # === 创建 LangGraph 节点 ===
    query_understanding_node = QueryUnderstandingNode(settings=settings)
    rag_agent_node = RAGAgentNode(
        retriever=rag_retriever,
        synthesizer=synthesizer,
    )
    fallback_node = FallbackNode(settings=settings)
    quality_gate_node = QualityGateNode(settings=settings)
    response_synthesizer_node = ResponseSynthesizerNode()

    # === 创建并编译图 ===
    graph = create_conversation_graph(
        query_understanding_node=query_understanding_node,
        cache_lookup_node=cache_lookup_node,
        rag_agent_node=rag_agent_node,
        fallback_node=fallback_node,
        quality_gate_node=quality_gate_node,
        response_synthesizer_node=response_synthesizer_node,
    )

    compiled_graph = compile_graph(graph)

    # === 初始化 LangFuse 追踪器 (Phase 2) ===
    from src.infra.logging.langfuse_tracer import init_langfuse, LLMTracer

    langfuse = init_langfuse()
    llm_tracer = LLMTracer(langfuse) if langfuse else None

    # 创建编排引擎
    orchestrator = ConversationOrchestrator(
        memory_manager=memory_manager,
        pg_pool=pg_pool,
        compiled_graph=compiled_graph,
        llm_tracer=llm_tracer,
    )

    logger.info("orchestrator_initialized")
    return orchestrator

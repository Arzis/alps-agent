"""对话编排引擎模块

基于 LangGraph 的对话编排引擎，管理图的执行和状态流转。
"""

import time
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
    ):
        """
        初始化编排器

        Args:
            memory_manager: 记忆管理器实例
            pg_pool: PostgreSQL 连接池
            compiled_graph: 编译后的 LangGraph
        """
        self.memory = memory_manager
        self.pg_pool = pg_pool
        self.graph = compiled_graph

    async def run(
        self,
        session_id: str,
        message: str,
        collection: str = "default",
    ) -> OrchestratorResult:
        """
        执行一轮对话 (同步模式)

        调用 LangGraph 编排执行完整流程。

        Args:
            session_id: 会话 ID
            message: 用户消息
            collection: 知识库集合

        Returns:
            OrchestratorResult: 包含回答结果的 OrchestratorResult
        """
        start_time = time.time()

        # 加载对话历史
        history = await self.memory.load_context(session_id, max_turns=5)

        logger.info(
            "orchestrator_run",
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

        # 调用 LangGraph 执行
        try:
            final_state = await self.graph.ainvoke(initial_state)

            # 从最终状态提取结果
            # 注意：最终状态可能是 OrchestratorResult 或 ConversationState
            if isinstance(final_state, OrchestratorResult):
                result = final_state
            else:
                # 如果返回的是 ConversationState，转换为 OrchestratorResult
                result = self._state_to_result(final_state)

            # 保存对话到记忆
            await self.memory.save_turn(
                session_id=session_id,
                user_message=message,
                assistant_message=result.answer,
                metadata={
                    "collection": collection,
                    "confidence": result.confidence,
                    "model_used": result.model_used,
                    "fallback_used": result.fallback_used,
                },
            )

            # 计算延迟
            latency_ms = (time.time() - start_time) * 1000

            logger.info(
                "orchestrator_completed",
                session_id=session_id,
                latency_ms=latency_ms,
                confidence=result.confidence,
                fallback_used=result.fallback_used,
            )

            return result

        except Exception as e:
            logger.error(
                "orchestrator_failed",
                session_id=session_id,
                error=str(e),
            )
            raise

    async def stream(
        self,
        session_id: str,
        message: str,
        collection: str = "default",
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        执行一轮对话 (流式模式)

        注意：当前实现为同步执行后流式返回。
        完整流式支持需要 LangGraph 的流式 API。

        Args:
            session_id: 会话 ID
            message: 用户消息
            collection: 知识库集合

        Yields:
            StreamEvent: 流式事件
        """
        # 发送处理中状态
        yield StreamEvent(event="status", data='"processing"')

        try:
            # 同步执行获取结果
            result = await self.run(session_id, message, collection)

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
                    data=str(citations_data),
                )

            # 发送 token 事件
            for i in range(0, len(result.answer), 10):
                yield StreamEvent(
                    event="token",
                    data=f'"{result.answer[i:i+10]}"',
                )

            # 发送完成事件
            yield StreamEvent(
                event="done",
                data='{"confidence": %f, "model_used": "%s", "tokens_used": %d}' % (
                    result.confidence,
                    result.model_used,
                    result.tokens_used,
                ),
            )

        except Exception as e:
            yield StreamEvent(
                event="error",
                data=f'"{str(e)}"',
            )

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

        Phase 1: 桩实现，返回空列表
        后续从 PostgreSQL 查询

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            list[SessionInfo]: 会话列表
        """
        # TODO: 从 PostgreSQL 查询会话列表
        return []

    async def delete_session(self, session_id: str) -> None:
        """
        删除会话

        Args:
            session_id: 会话 ID
        """
        await self.memory.clear_session(session_id)
        logger.info("session_deleted", session_id=session_id)

    def _state_to_result(self, state: ConversationState) -> OrchestratorResult:
        """将 ConversationState 转换为 OrchestratorResult

        用于处理图直接返回 ConversationState 的情况（如缓存命中）。

        Args:
            state: 对话状态

        Returns:
            OrchestratorResult: 编排结果
        """
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

    # 创建 Dense 检索器 (内部使用 OpenAI 兼容接口)
    dense_retriever = DenseRetriever(
        milvus_client=milvus_client,
        settings=settings,
    )

    # 创建 RAG 检索器
    rag_retriever = RAGRetriever(dense_retriever=dense_retriever)

    # 创建答案合成器
    synthesizer = AnswerSynthesizer(settings=settings)

    # === 创建缓存节点 (Phase 2) ===
    # 创建 Embedding 函数
    async def get_embedding(text: str) -> list[float]:
        """获取文本 Embedding 向量"""
        from langchain_openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
            base_url=settings.DASHSCOPE_BASE_URL,
        )
        return await embeddings.aembed_query(text)

    # 创建语义缓存
    semantic_cache = SemanticCache(
        redis=redis_client,
        embedding_fn=get_embedding,
        similarity_threshold=settings.SEMANTIC_CACHE_THRESHOLD,
        ttl=settings.SEMANTIC_CACHE_TTL,
        embedding_dim=settings.EMBEDDING_DIMENSION,
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

    # 创建编排引擎
    orchestrator = ConversationOrchestrator(
        memory_manager=memory_manager,
        pg_pool=pg_pool,
        compiled_graph=compiled_graph,
    )

    logger.info("orchestrator_initialized")
    return orchestrator

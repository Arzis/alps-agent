"""RAG Agent 节点模块

负责执行 RAG 检索和答案生成。
"""

import structlog

from src.core.orchestrator.state import ConversationState
from src.core.rag.retrieval.retriever import RAGRetriever
from src.core.rag.synthesis.synthesizer import AnswerSynthesizer

logger = structlog.get_logger()


class RAGAgentNode:
    """
    RAG Agent 节点

    职责：
    1. 根据改写后的查询检索相关文档
    2. 基于检索结果生成回答
    3. 提取引用信息
    """

    def __init__(
        self,
        retriever: RAGRetriever,
        synthesizer: AnswerSynthesizer,
    ):
        """初始化 RAG Agent 节点

        Args:
            retriever: RAG 检索器
            synthesizer: 答案合成器
        """
        self.retriever = retriever
        self.synthesizer = synthesizer

    async def execute(self, state: ConversationState) -> ConversationState:
        """执行 RAG 检索和生成

        Args:
            state: 当前对话状态 (包含 rewritten_query)

        Returns:
            ConversationState: 更新后的状态 (包含 rag_answer, citations)
        """
        query = state.rewritten_query or state.user_message
        collection = state.collection
        history = state.history_turns

        logger.info(
            "rag_agent_start",
            session_id=state.session_id,
            query_length=len(query),
            collection=collection,
        )

        try:
            # 1. 检索相关文档
            retrieved_chunks = await self.retriever.retrieve(
                query=query,
                collection=collection,
                top_k=5,
            )

            state.retrieved_chunks = retrieved_chunks

            logger.info(
                "rag_retrieval_completed",
                session_id=state.session_id,
                chunks_retrieved=len(retrieved_chunks),
            )

            # 2. 如果没有检索结果，设置低置信度
            if not retrieved_chunks:
                state.rag_answer = ""
                state.confidence = 0.0
                state.citations = []
                return state

            # 3. 基于检索结果生成答案
            synthesis_result = await self.synthesizer.synthesize(
                query=query,
                retrieved_chunks=retrieved_chunks,
                conversation_history=history,
            )

            state.rag_answer = synthesis_result.answer
            state.citations = synthesis_result.citations
            state.confidence = self._calculate_confidence(retrieved_chunks)
            state.model_used = synthesis_result.model_used
            state.tokens_used = synthesis_result.tokens_used

            logger.info(
                "rag_synthesis_completed",
                session_id=state.session_id,
                answer_length=len(synthesis_result.answer),
                citations_count=len(synthesis_result.citations),
                confidence=state.confidence,
            )

            return state

        except Exception as e:
            logger.error(
                "rag_agent_failed",
                session_id=state.session_id,
                error=str(e),
            )
            state.error = str(e)
            state.rag_answer = ""
            state.confidence = 0.0
            return state

    def _calculate_confidence(self, chunks: list) -> float:
        """计算回答置信度

        基于检索结果的相关度分数计算置信度。

        Args:
            chunks: 检索到的文档块列表

        Returns:
            float: 置信度 (0-1)
        """
        if not chunks:
            return 0.0

        # 使用最高分文档块的分数作为置信度基础
        top_score = max(chunk.score for chunk in chunks)

        # 结合检索结果数量进行调整
        # 有多个结果时更可靠
        count_bonus = min(len(chunks) * 0.05, 0.15)

        confidence = min(top_score + count_bonus, 1.0)

        return round(confidence, 2)

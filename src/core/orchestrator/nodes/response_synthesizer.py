"""响应合成节点模块

将 RAG 回答或降级回答格式化为最终响应。
"""

import structlog

from src.core.orchestrator.state import ConversationState, OrchestratorResult

logger = structlog.get_logger()


class ResponseSynthesizerNode:
    """
    响应合成节点

    职责：
    1. 格式化最终回答
    2. 确保响应结构完整
    3. 处理边缘情况（如空回答）

    设计考虑：
    - 这是最后一个处理节点，只做格式化
    - 不再做复杂的逻辑判断
    """

    # 拒绝回答的默认消息
    REJECT_MESSAGE = "抱歉，我无法找到与您问题相关的信息，建议您查阅相关文档或联系管理员。"
    EMPTY_MESSAGE = "抱歉，我现在无法回答您的问题，请稍后重试。"

    async def execute(self, state: ConversationState) -> OrchestratorResult:
        """执行响应合成

        Args:
            state: 当前对话状态

        Returns:
            OrchestratorResult: 最终响应结果
        """
        logger.info(
            "response_synthesizer_execute",
            session_id=state.session_id,
            route=state.route,
            confidence=state.confidence,
            fallback_used=state.fallback_used,
        )

        # 1. 根据路由决策选择回答
        answer = self._get_answer(state)

        # 2. 构建最终结果
        result = OrchestratorResult(
            answer=answer,
            citations=state.citations if not state.fallback_used else [],
            confidence=state.confidence,
            model_used=state.model_used,
            fallback_used=state.fallback_used,
            tokens_used=state.tokens_used,
        )

        logger.info(
            "response_synthesizer_completed",
            session_id=state.session_id,
            answer_length=len(answer),
            citations_count=len(result.citations),
        )

        return result

    def _get_answer(self, state: ConversationState) -> str:
        """根据路由决策获取最终回答

        Args:
            state: 当前对话状态

        Returns:
            str: 最终回答内容
        """
        # 拒绝回答
        if state.route == "reject":
            logger.info(
                "response_rejected",
                session_id=state.session_id,
                confidence=state.confidence,
            )
            return self.REJECT_MESSAGE

        # RAG 直接通过
        if state.route == "direct":
            if not state.rag_answer:
                return self.EMPTY_MESSAGE
            return state.rag_answer

        # 降级回答
        if state.route == "fallback":
            if not state.rag_answer:
                return self.EMPTY_MESSAGE
            return state.rag_answer

        # 默认情况
        if state.rag_answer:
            return state.rag_answer

        return self.EMPTY_MESSAGE

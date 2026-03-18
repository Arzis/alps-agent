"""质量门禁节点模块

评估 RAG 回答质量，决定是否需要降级或拒绝。
"""

from typing import Literal

import structlog

from src.core.orchestrator.state import ConversationState
from src.infra.config.settings import Settings

logger = structlog.get_logger()


class QualityGateNode:
    """
    质量门禁节点

    职责：
    1. 评估 RAG 回答的置信度
    2. 根据阈值判断路由决策
    3. 决定通过、降级或拒绝

    路由决策：
    - rag: 置信度足够，通过 RAG 回答
    - fallback: 置信度不足，降级使用 LLM 直接回答
    - reject: 置信度过低，拒绝回答
    - direct: 直接返回 RAG 回答（不需要进一步处理）
    """

    # 置信度阈值配置
    CONFIDENCE_PASS_THRESHOLD = 0.5   # 通过阈值
    CONFIDENCE_FALLBACK_THRESHOLD = 0.2  # 降级阈值
    CONFIDENCE_REJECT_THRESHOLD = 0.1  # 拒绝阈值

    def __init__(self, settings: Settings):
        """初始化质量门禁节点

        Args:
            settings: 应用配置
        """
        self.settings = settings

        # 从配置读取阈值（如果配置了的话）
        self.pass_threshold = getattr(
            settings, "RAG_CONFIDENCE_PASS", self.CONFIDENCE_PASS_THRESHOLD
        )
        self.fallback_threshold = getattr(
            settings, "RAG_CONFIDENCE_FALLBACK", self.CONFIDENCE_FALLBACK_THRESHOLD
        )
        self.reject_threshold = getattr(
            settings, "RAG_CONFIDENCE_REJECT", self.CONFIDENCE_REJECT_THRESHOLD
        )

    async def execute(self, state: ConversationState) -> ConversationState:
        """执行质量评估

        Args:
            state: 当前对话状态

        Returns:
            ConversationState: 更新后的状态 (包含 route)
        """
        confidence = state.confidence
        has_retrieved = len(state.retrieved_chunks) > 0
        intent = state.intent

        logger.info(
            "quality_gate_evaluate",
            session_id=state.session_id,
            confidence=confidence,
            has_retrieved=has_retrieved,
            intent=intent,
        )

        # 1. 非知识问答意图，直接通过
        if intent != "knowledge":
            state.route = "direct"
            logger.info(
                "quality_gate_pass_intent",
                session_id=state.session_id,
                intent=intent,
            )
            return state

        # 2. 没有检索结果，路由到降级
        if not has_retrieved:
            state.route = "fallback"
            logger.info(
                "quality_gate_no_results",
                session_id=state.session_id,
            )
            return state

        # 3. 根据置信度判断
        route = self._evaluate_confidence(confidence)
        state.route = route

        logger.info(
            "quality_gate_result",
            session_id=state.session_id,
            confidence=confidence,
            route=route,
        )

        return state

    def _evaluate_confidence(
        self, confidence: float
    ) -> Literal["direct", "fallback", "reject"]:
        """评估置信度并返回路由决策

        Args:
            confidence: 置信度分数

        Returns:
            Literal["direct", "fallback", "reject"]: 路由决策
        """
        if confidence >= self.pass_threshold:
            return "direct"  # 高置信度，直接返回 RAG 回答

        if confidence >= self.fallback_threshold:
            return "fallback"  # 中等置信度，降级使用 LLM

        return "reject"  # 低置信度，拒绝回答

    async def should_reject(self, state: ConversationState) -> bool:
        """判断是否应该拒绝回答

        Args:
            state: 当前对话状态

        Returns:
            bool: 是否应该拒绝
        """
        return state.route == "reject"

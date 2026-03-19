"""质量门禁节点模块

评估 RAG 回答质量，决定是否需要降级或拒绝。
Phase 2: 集成 LLM-based 置信度评估 + 幻觉检测。
"""

import asyncio
from typing import Literal

import structlog

from src.core.orchestrator.state import ConversationState
from src.core.quality.confidence import ConfidenceEvaluator, ConfidenceAssessment
from src.core.quality.hallucination import HallucinationDetector, HallucinationResult
from src.infra.config.settings import Settings

logger = structlog.get_logger()


class QualityGateNode:
    """
    质量门禁节点 - Phase 2 LLM-based

    职责：
    1. 评估 RAG 回答的置信度 (LLM-based)
    2. 幻觉检测
    3. 根据阈值判断路由决策

    评估维度:
    1. 基于检索分数的初步评估
    2. LLM-based 置信度评估 (faithfulness + relevancy + completeness)
    3. 幻觉检测

    决策规则:
    - overall >= 0.7  → 直接通过 (direct)
    - overall >= 0.4  → 降级 Codex (fallback)
    - overall < 0.4   → 拒绝回答 (reject)
    """

    def __init__(
        self,
        settings: Settings,
        confidence_evaluator: ConfidenceEvaluator | None = None,
        hallucination_detector: HallucinationDetector | None = None,
    ):
        """初始化质量门禁节点

        Args:
            settings: 应用配置
            confidence_evaluator: 可选的置信度评估器
            hallucination_detector: 可选的幻觉检测器
        """
        self.settings = settings
        self.confidence_evaluator = confidence_evaluator or ConfidenceEvaluator()
        self.hallucination_detector = hallucination_detector or HallucinationDetector()

        # 从配置读取阈值
        self.pass_threshold = getattr(
            settings, "CONFIDENCE_THRESHOLD_PASS", 0.7
        )
        self.fallback_threshold = getattr(
            settings, "CONFIDENCE_THRESHOLD_FALLBACK", 0.4
        )

    async def execute(self, state: ConversationState) -> ConversationState:
        """执行质量评估

        Args:
            state: 当前对话状态

        Returns:
            ConversationState: 更新后的状态 (包含 route, confidence, quality_metrics)
        """
        answer = state.rag_answer
        chunks = state.retrieved_chunks
        query = state.rewritten_query or state.user_message

        logger.info(
            "quality_gate_evaluate",
            session_id=state.session_id,
            has_answer=bool(answer),
            has_chunks=bool(chunks),
            intent=state.intent,
        )

        # 1. 非知识问答意图，直接通过
        if state.intent != "knowledge":
            state.route = "direct"
            state.confidence = 0.8
            logger.info(
                "quality_gate_pass_intent",
                session_id=state.session_id,
                intent=state.intent,
            )
            return state

        # 2. 如果还没有生成答案 (在 RAG 检索之后，答案生成之前)
        #    则仅基于检索分数做初步评估
        if not answer:
            return self._retrieval_only_assessment(state, chunks)

        # 3. 如果没有检索结果，路由到降级
        if not chunks:
            state.route = "fallback"
            state.confidence = 0.0
            logger.info(
                "quality_gate_no_results",
                session_id=state.session_id,
            )
            return state

        # 4. 并行执行: 置信度评估 + 幻觉检测
        contexts = [c.content for c in chunks]

        confidence_task = self.confidence_evaluator.evaluate(
            question=query,
            answer=answer,
            contexts=contexts,
        )
        hallucination_task = self.hallucination_detector.detect(
            answer=answer,
            contexts=contexts,
        )

        confidence_result, hallucination_result = await asyncio.gather(
            confidence_task, hallucination_task,
            return_exceptions=True,
        )

        # 处理异常
        if isinstance(confidence_result, Exception):
            logger.error("confidence_eval_error", error=str(confidence_result))
            confidence_result = ConfidenceAssessment(
                faithfulness=0.5, relevancy=0.5,
                completeness=0.5, overall=0.5,
            )

        if isinstance(hallucination_result, Exception):
            logger.error("hallucination_detect_error", error=str(hallucination_result))
            hallucination_result = None

        # 综合评分 (考虑幻觉)
        overall = confidence_result.overall
        hallucination_score = 0.0
        if hallucination_result and hallucination_result.has_hallucination:
            # 有幻觉时降低置信度
            hallucination_score = hallucination_result.hallucination_score
            penalty = hallucination_score * 0.3
            overall = max(0.0, overall - penalty)

        # 根据综合评分决定路由
        route = self._evaluate_confidence(overall)

        state.confidence = overall
        state.route = route

        logger.info(
            "quality_gate_evaluated",
            session_id=state.session_id,
            confidence_overall=round(confidence_result.overall, 3),
            faithfulness=round(confidence_result.faithfulness, 3),
            relevancy=round(confidence_result.relevancy, 3),
            completeness=round(confidence_result.completeness, 3),
            hallucination_score=hallucination_score,
            final_confidence=round(overall, 3),
            route=route,
        )

        return state

    def _retrieval_only_assessment(
        self, state: ConversationState, chunks: list
    ) -> ConversationState:
        """仅基于检索结果的初步评估

        Args:
            state: 当前对话状态
            chunks: 检索到的文档块列表

        Returns:
            ConversationState: 更新后的状态
        """
        if not chunks:
            state.confidence = 0.0
            state.route = "fallback"
            state.quality_metrics = {}
            return state

        # 基于检索分数计算初步置信度
        scores = [getattr(c, "score", 0) for c in chunks]
        top_score = max(scores) if scores else 0
        avg_score = sum(scores) / len(scores) if scores else 0
        confidence = 0.6 * top_score + 0.4 * avg_score

        route = self._evaluate_confidence(confidence)

        logger.info(
            "quality_gate_retrieval_only",
            session_id=state.session_id,
            top_score=round(top_score, 3),
            avg_score=round(avg_score, 3),
            confidence=round(confidence, 3),
            route=route,
        )

        state.confidence = confidence
        state.route = route
        state.quality_metrics = {}
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


def should_fallback(state: ConversationState) -> str:
    """条件路由: 根据质量评估决定下一步

    Args:
        state: 当前对话状态

    Returns:
        str: 路由目标节点
    """
    route = state.route if hasattr(state, "route") else "direct"
    return route

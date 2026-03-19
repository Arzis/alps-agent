"""DeepEval 评估器模块

提供 RAG 系统的补充评估能力，基于 DeepEval 框架。
与 RAGAS 互补:
- GEval: 自定义评估标准 (如企业级规范)
- HallucinationMetric: 更细粒度的幻觉检测
- 支持 Conversational 评估 (多轮对话质量)
"""

import structlog

from src.evaluation.ragas_evaluator import TestCase

logger = structlog.get_logger()


class DeepEvalEvaluator:
    """DeepEval 评估器

    与 RAGAS 互补的评估器，提供:
    - GEval: 自定义评估标准
    - HallucinationMetric: 细粒度幻觉检测
    - AnswerRelevancyMetric: 答案相关性
    - ContextualRelevancyMetric: 上下文相关性
    - FaithfulnessMetric: 忠实度
    """

    def __init__(self):
        """初始化 DeepEval 评估器"""
        self.metrics = []
        self._init_metrics()

    def _init_metrics(self):
        """初始化评估指标"""
        try:
            from deepeval.metrics import (
                FaithfulnessMetric,
                ContextualRelevancyMetric,
                HallucinationMetric,
                AnswerRelevancyMetric,
                GEval,
            )
            from deepeval.test_case import LLMTestCase

            self.metrics = [
                FaithfulnessMetric(
                    threshold=0.7,
                    include_reason=True,
                ),
                ContextualRelevancyMetric(
                    threshold=0.7,
                    include_reason=True,
                ),
                HallucinationMetric(
                    threshold=0.5,
                    include_reason=True,
                ),
                AnswerRelevancyMetric(
                    threshold=0.7,
                    include_reason=True,
                ),
                # 自定义企业级评估标准
                GEval(
                    name="企业问答规范",
                    criteria=(
                        "评估答案是否符合企业问答规范: "
                        "1. 语言专业得体 "
                        "2. 不包含不确定/模棱两可的表述(除非确实无法确认) "
                        "3. 提供了可操作的具体信息 "
                        "4. 引用了来源"
                    ),
                    evaluation_params=[
                        LLMTestCase.input,
                        LLMTestCase.actual_output,
                        LLMTestCase.retrieval_context,
                    ],
                    threshold=0.6,
                ),
            ]

        except ImportError as e:
            logger.warning("deepeval_not_available", error=str(e))
            self.metrics = []

    async def evaluate_batch(self, test_cases: list[TestCase]) -> dict:
        """批量评估

        Args:
            test_cases: 测试用例列表

        Returns:
            dict: 评估结果字典
        """
        if not self.metrics:
            logger.warning("deepeval_metrics_not_available")
            return {}

        try:
            from deepeval import evaluate as deepeval_evaluate
            from deepeval.test_case import LLMTestCase

            deepeval_cases = []

            for tc in test_cases:
                deepeval_cases.append(
                    LLMTestCase(
                        input=tc.question,
                        actual_output=tc.generated_answer or "",
                        expected_output=tc.ground_truth,
                        retrieval_context=tc.contexts,
                    )
                )

            results = deepeval_evaluate(
                test_cases=deepeval_cases,
                metrics=self.metrics,
                run_async=True,
                print_results=False,
            )

            # 提取分数
            metric_scores = {}
            for metric in self.metrics:
                scores = []
                for tc in deepeval_cases:
                    for m in tc.metrics:
                        if m.name == metric.name and m.score is not None:
                            scores.append(m.score)
                if scores:
                    metric_scores[metric.name] = {
                        "avg": round(sum(scores) / len(scores), 4),
                        "min": round(min(scores), 4),
                        "max": round(max(scores), 4),
                    }

            logger.info("deepeval_evaluation_completed", metrics=metric_scores)
            return metric_scores

        except ImportError as e:
            logger.warning("deepeval_not_available", error=str(e))
            return {}
        except Exception as e:
            logger.error("deepeval_evaluation_failed", error=str(e))
            return {}

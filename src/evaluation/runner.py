"""评估运行器模块

提供完整的 RAG 系统评估流程:
1. 加载/生成测试集
2. 对每个问题执行 RAG 问答
3. 收集回答和检索上下文
4. 运行 RAGAS + DeepEval 评估
5. 生成报告
"""

import structlog

from src.evaluation.ragas_evaluator import (
    RagasEvaluator,
    TestCase,
    EvaluationReport,
)
from src.evaluation.deepeval_evaluator import DeepEvalEvaluator

logger = structlog.get_logger()


class EvaluationRunner:
    """评估运行器

    完整流程:
    1. 加载/生成测试集
    2. 对每个问题执行 RAG 问答
    3. 收集回答和检索上下文
    4. 运行 RAGAS + DeepEval 评估
    5. 生成报告
    """

    def __init__(
        self,
        orchestrator,
        ragas_evaluator: RagasEvaluator | None = None,
        deepeval_evaluator: DeepEvalEvaluator | None = None,
    ):
        """初始化评估运行器

        Args:
            orchestrator: 对话编排器实例
            ragas_evaluator: RAGAS 评估器 (可选)
            deepeval_evaluator: DeepEval 评估器 (可选)
        """
        self.orchestrator = orchestrator
        self.ragas = ragas_evaluator or RagasEvaluator()
        self.deepeval = deepeval_evaluator

    async def run_evaluation(
        self,
        test_cases: list[TestCase],
        collection: str = "default",
        name: str = "evaluation",
    ) -> EvaluationReport:
        """执行完整评估

        完整流程:
        1. 对每个问题执行 RAG
        2. 收集回答
        3. 运行 RAGAS 评估
        4. 运行 DeepEval 评估 (可选)
        5. 返回报告

        Args:
            test_cases: 测试用例列表
            collection: 知识库集合
            name: 评估名称

        Returns:
            EvaluationReport: 评估报告
        """
        logger.info(
            "evaluation_run_start",
            name=name,
            num_cases=len(test_cases),
            collection=collection,
        )

        # Step 1: 执行 RAG, 收集回答
        enriched_cases = []
        for i, tc in enumerate(test_cases):
            try:
                result = await self.orchestrator.run(
                    session_id=f"eval_{name}_{i}",
                    message=tc.question,
                    collection=collection,
                )

                enriched_cases.append(
                    TestCase(
                        question=tc.question,
                        ground_truth=tc.ground_truth,
                        generated_answer=result.answer,
                        contexts=[c.content for c in result.citations] if result.citations else [],
                    )
                )

                logger.debug(
                    "evaluation_sample_completed",
                    index=i,
                    question=tc.question[:100],
                    confidence=result.confidence,
                )

            except Exception as e:
                logger.error(
                    "evaluation_sample_failed",
                    index=i,
                    error=str(e),
                )
                enriched_cases.append(
                    TestCase(
                        question=tc.question,
                        ground_truth=tc.ground_truth,
                        generated_answer="[ERROR] " + str(e),
                        contexts=[],
                    )
                )

        # Step 2: RAGAS 评估
        report = await self.ragas.evaluate_batch(
            test_cases=enriched_cases,
            name=name,
        )

        # Step 3: DeepEval 评估 (可选)
        if self.deepeval:
            try:
                deepeval_results = await self.deepeval.evaluate_batch(enriched_cases)
                report.config["deepeval_metrics"] = deepeval_results
            except Exception as e:
                logger.error("deepeval_failed", error=str(e))

        logger.info(
            "evaluation_run_completed",
            name=name,
            faithfulness=report.avg_metrics.faithfulness,
            relevancy=report.avg_metrics.answer_relevancy,
            precision=report.avg_metrics.context_precision,
        )

        return report

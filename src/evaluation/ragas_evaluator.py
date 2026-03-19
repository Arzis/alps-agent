"""RAGAS 评估器模块

提供 RAG 系统的标准化评估能力，基于 RAGAS 框架。
评估指标:
- faithfulness: 答案是否基于上下文 (忠实度)
- answer_relevancy: 答案是否切题
- context_precision: 检索的上下文是否精确
- context_recall: 检索是否召回了所有相关信息 (需要 ground_truth)
- answer_correctness: 答案是否正确 (需要 ground_truth)
"""

import json
import uuid
from datetime import datetime
from typing import Literal

import structlog

from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class TestCase:
    """单个测试用例

    Attributes:
        question: 用户问题
        ground_truth: 标准答案 (可选)
        generated_answer: 系统生成的回答 (评估时填充)
        contexts: 检索到的上下文列表 (评估时填充)
    """

    def __init__(
        self,
        question: str,
        ground_truth: str | None = None,
        generated_answer: str | None = None,
        contexts: list[str] | None = None,
    ):
        self.question = question
        self.ground_truth = ground_truth
        self.generated_answer = generated_answer
        self.contexts = contexts or []


class EvaluationMetrics:
    """评估指标

    Attributes:
        faithfulness: 忠实度 (答案基于上下文的程度)
        answer_relevancy: 答案相关性 (答案切题程度)
        context_precision: 上下文精确度 (检索精确度)
        context_recall: 上下文召回率 (需要 ground_truth)
        answer_correctness: 答案正确性 (需要 ground_truth)
    """

    def __init__(
        self,
        faithfulness: float | None = None,
        answer_relevancy: float | None = None,
        context_precision: float | None = None,
        context_recall: float | None = None,
        answer_correctness: float | None = None,
    ):
        self.faithfulness = faithfulness
        self.answer_relevancy = answer_relevancy
        self.context_precision = context_precision
        self.context_recall = context_recall
        self.answer_correctness = answer_correctness


class EvaluationReport:
    """评估报告

    Attributes:
        run_id: 评估运行 ID
        name: 评估名称
        total_samples: 测试样本总数
        avg_metrics: 平均指标
        per_sample_metrics: 每条样本的详细指标
        created_at: 创建时间
        config: 评估配置
    """

    def __init__(
        self,
        run_id: str,
        name: str,
        total_samples: int,
        avg_metrics: EvaluationMetrics | None = None,
        per_sample_metrics: list[dict] | None = None,
        created_at: datetime | None = None,
        config: dict | None = None,
    ):
        self.run_id = run_id
        self.name = name
        self.total_samples = total_samples
        self.avg_metrics = avg_metrics or EvaluationMetrics()
        self.per_sample_metrics = per_sample_metrics or []
        self.created_at = created_at or datetime.utcnow()
        self.config = config or {}


class RagasEvaluator:
    """RAGAS 评估器

    使用 RAGAS 框架对 RAG 系统进行标准化评估。

    评估指标:
    - faithfulness: 答案是否基于上下文
    - answer_relevancy: 答案是否切题
    - context_precision: 检索上下文是否精确
    - context_recall: 检索召回率 (需要 ground_truth)
    - answer_correctness: 答案正确性 (需要 ground_truth)
    """

    def __init__(self):
        """初始化 RAGAS 评估器"""
        settings = get_settings()

        # RAGAS 内部使用的 LLM
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
            base_url=settings.DASHSCOPE_BASE_URL,
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
            base_url=settings.DASHSCOPE_BASE_URL,
        )

    async def evaluate_batch(
        self,
        test_cases: list[TestCase],
        name: str = "evaluation",
        metrics_list: list[str] | None = None,
    ) -> EvaluationReport:
        """批量评估

        Args:
            test_cases: 测试用例列表
            name: 评估任务名称
            metrics_list: 要计算的指标 (默认全部)

        Returns:
            EvaluationReport: 评估报告
        """
        run_id = f"eval_{uuid.uuid4().hex[:12]}"

        logger.info(
            "ragas_evaluation_start",
            run_id=run_id,
            name=name,
            num_samples=len(test_cases),
        )

        # 检查是否有可用的 RAGAS
        try:
            from datasets import Dataset
            from ragas import evaluate
            from ragas.metrics import (
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
                answer_correctness,
            )
        except ImportError as e:
            logger.warning("ragas_not_available", error=str(e))
            # RAGAS 不可用时返回空报告
            return EvaluationReport(
                run_id=run_id,
                name=name,
                total_samples=len(test_cases),
                avg_metrics=EvaluationMetrics(),
                per_sample_metrics=[],
                config={"error": "ragas_not_available"},
            )

        # 构建 HuggingFace Dataset
        data = {
            "question": [],
            "answer": [],
            "contexts": [],
        }

        has_ground_truth = any(tc.ground_truth for tc in test_cases)
        if has_ground_truth:
            data["ground_truth"] = []

        for tc in test_cases:
            data["question"].append(tc.question)
            data["answer"].append(tc.generated_answer or "")
            data["contexts"].append(tc.contexts)
            if has_ground_truth:
                data["ground_truth"].append(tc.ground_truth or "")

        dataset = Dataset.from_dict(data)

        # 选择指标
        selected_metrics = self._select_metrics(metrics_list, has_ground_truth)

        # 执行评估
        try:
            results = evaluate(
                dataset=dataset,
                metrics=selected_metrics,
                llm=self.llm,
                embeddings=self.embeddings,
                raise_exceptions=False,
            )

            # 构建报告
            results_df = results.to_pandas()

            avg_metrics = EvaluationMetrics(
                faithfulness=self._safe_mean(results_df, "faithfulness"),
                answer_relevancy=self._safe_mean(results_df, "answer_relevancy"),
                context_precision=self._safe_mean(results_df, "context_precision"),
                context_recall=self._safe_mean(results_df, "context_recall"),
                answer_correctness=self._safe_mean(results_df, "answer_correctness"),
            )

            per_sample = results_df.to_dict(orient="records")

            report = EvaluationReport(
                run_id=run_id,
                name=name,
                total_samples=len(test_cases),
                avg_metrics=avg_metrics,
                per_sample_metrics=per_sample,
                config={
                    "metrics": [m.name for m in selected_metrics],
                    "llm_model": "gpt-4o-mini",
                },
            )

            # 持久化报告
            await self._save_report(report)

            logger.info(
                "ragas_evaluation_completed",
                run_id=run_id,
                avg_faithfulness=avg_metrics.faithfulness,
                avg_relevancy=avg_metrics.answer_relevancy,
                avg_precision=avg_metrics.context_precision,
            )

            return report

        except Exception as e:
            logger.error("ragas_evaluation_failed", run_id=run_id, error=str(e))
            # 返回错误报告
            return EvaluationReport(
                run_id=run_id,
                name=name,
                total_samples=len(test_cases),
                avg_metrics=EvaluationMetrics(),
                per_sample_metrics=[],
                config={"error": str(e)},
            )

    def _select_metrics(
        self,
        metrics_list: list[str] | None,
        has_ground_truth: bool,
    ) -> list:
        """选择评估指标

        Args:
            metrics_list: 指定指标列表
            has_ground_truth: 是否有标准答案

        Returns:
            list: 选择的指标列表
        """
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_correctness,
        )

        all_metrics = {
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "context_precision": context_precision,
        }

        if has_ground_truth:
            all_metrics.update({
                "context_recall": context_recall,
                "answer_correctness": answer_correctness,
            })

        if metrics_list:
            return [all_metrics[m] for m in metrics_list if m in all_metrics]
        return list(all_metrics.values())

    def _safe_mean(self, df, col: str) -> float | None:
        """安全计算均值

        Args:
            df: pandas DataFrame
            col: 列名

        Returns:
            float | None: 均值，失败返回 None
        """
        if col in df.columns:
            values = df[col].dropna()
            return round(float(values.mean()), 4) if len(values) > 0 else None
        return None

    async def _save_report(self, report: EvaluationReport):
        """保存评估报告到 PostgreSQL

        Args:
            report: 评估报告
        """
        try:
            from src.infra.database.postgres import get_postgres_pool

            pool = await get_postgres_pool()

            # 检查表是否存在
            table_exists = await pool.fetchval(
                """SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'evaluation_runs'
                )"""
            )

            if not table_exists:
                # 创建表
                await pool.execute("""
                    CREATE TABLE evaluation_runs (
                        id VARCHAR(100) PRIMARY KEY,
                        name VARCHAR(500) NOT NULL,
                        dataset_size INTEGER NOT NULL,
                        status VARCHAR(50) NOT NULL,
                        metrics JSONB,
                        config JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        completed_at TIMESTAMP
                    )
                """)
                await pool.execute("""
                    CREATE TABLE evaluation_results (
                        id SERIAL PRIMARY KEY,
                        run_id VARCHAR(100) REFERENCES evaluation_runs(id),
                        question TEXT NOT NULL,
                        ground_truth TEXT,
                        generated_answer TEXT,
                        contexts JSONB,
                        metrics JSONB
                    )
                """)
                await pool.execute("""
                    CREATE INDEX idx_evaluation_results_run_id
                    ON evaluation_results(run_id)
                """)

            # 保存评估运行记录
            await pool.execute(
                """INSERT INTO evaluation_runs
                   (id, name, dataset_size, status, metrics, config, completed_at)
                   VALUES ($1, $2, $3, $4, $5, $6, NOW())""",
                report.run_id,
                report.name,
                report.total_samples,
                "completed",
                json.dumps(self._metrics_to_dict(report.avg_metrics), ensure_ascii=False),
                json.dumps(report.config, ensure_ascii=False),
            )

            # 保存每条结果
            for sample in report.per_sample_metrics:
                await pool.execute(
                    """INSERT INTO evaluation_results
                       (run_id, question, ground_truth, generated_answer, contexts, metrics)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    report.run_id,
                    sample.get("question", ""),
                    sample.get("ground_truth", ""),
                    sample.get("answer", ""),
                    json.dumps(sample.get("contexts", []), ensure_ascii=False),
                    json.dumps(
                        {k: v for k, v in sample.items()
                         if k not in ("question", "answer", "contexts", "ground_truth")},
                        ensure_ascii=False,
                    ),
                )

            logger.info("evaluation_report_saved", run_id=report.run_id)

        except Exception as e:
            logger.error("save_report_failed", run_id=report.run_id, error=str(e))

    def _metrics_to_dict(self, metrics: EvaluationMetrics) -> dict:
        """将评估指标转换为字典

        Args:
            metrics: 评估指标

        Returns:
            dict: 字典格式的指标
        """
        return {
            "faithfulness": metrics.faithfulness,
            "answer_relevancy": metrics.answer_relevancy,
            "context_precision": metrics.context_precision,
            "context_recall": metrics.context_recall,
            "answer_correctness": metrics.answer_correctness,
        }

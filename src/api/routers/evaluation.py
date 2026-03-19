"""评估 API 路由模块

提供评估相关的 API 端点:
- POST /api/v1/evaluation/run - 触发评估任务 (后台异步)
- POST /api/v1/evaluation/generate-testset - 自动生成测试集
- GET /api/v1/evaluation/reports - 获取评估报告列表
- GET /api/v1/evaluation/reports/{run_id} - 获取评估报告详情
"""

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
import structlog

from src.evaluation.ragas_evaluator import TestCase, EvaluationReport
from src.evaluation.runner import EvaluationRunner
from src.evaluation.dataset_generator import TestsetGenerator

logger = structlog.get_logger()

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


class RunEvaluationRequest(BaseModel):
    """运行评估请求"""
    name: str = "manual_evaluation"
    collection: str = "default"
    test_cases: list[TestCase]
    run_deepeval: bool = False


class GenerateTestsetRequest(BaseModel):
    """生成测试集请求"""
    collection: str = "default"
    count_per_doc: int = 5
    max_docs: int = 10


class TestCaseRequest(BaseModel):
    """测试用例请求模型 (用于 API 序列化)"""
    question: str
    ground_truth: str | None = None
    generated_answer: str | None = None
    contexts: list[str] = Field(default_factory=list)


class RunEvaluationResponse(BaseModel):
    """运行评估响应"""
    task_id: str
    status: str
    message: str


class GenerateTestsetResponse(BaseModel):
    """生成测试集响应"""
    total: int
    test_cases: list[dict]


class EvaluationReportSummary(BaseModel):
    """评估报告摘要"""
    run_id: str
    name: str
    dataset_size: int
    status: str
    metrics: dict | None
    created_at: str


class EvaluationReportDetail(BaseModel):
    """评估报告详情"""
    run_id: str
    name: str
    dataset_size: int
    status: str
    avg_metrics: dict
    config: dict
    created_at: str
    samples: list[dict]


@router.post("/run", response_model=RunEvaluationResponse)
async def run_evaluation(
    request: RunEvaluationRequest,
    background_tasks: BackgroundTasks,
) -> RunEvaluationResponse:
    """触发评估任务 (后台异步执行)

    Args:
        request: 评估请求
        background_tasks: FastAPI 后台任务

    Returns:
        RunEvaluationResponse: 任务启动响应
    """
    task_id = f"eval_{uuid.uuid4().hex[:12]}"

    # 异步执行评估
    background_tasks.add_task(
        _run_evaluation_task,
        task_id=task_id,
        name=request.name,
        collection=request.collection,
        test_cases=request.test_cases,
        run_deepeval=request.run_deepeval,
    )

    return RunEvaluationResponse(
        task_id=task_id,
        status="running",
        message=f"评估任务已启动, 共 {len(request.test_cases)} 个样本",
    )


async def _run_evaluation_task(
    task_id: str,
    name: str,
    collection: str,
    test_cases: list[TestCase],
    run_deepeval: bool,
):
    """后台评估任务

    Args:
        task_id: 任务 ID
        name: 评估名称
        collection: 知识库集合
        test_cases: 测试用例列表
        run_deepeval: 是否运行 DeepEval
    """
    from src.evaluation.ragas_evaluator import RagasEvaluator
    from src.evaluation.deepeval_evaluator import DeepEvalEvaluator

    try:
        ragas = RagasEvaluator()
        deepeval = DeepEvalEvaluator() if run_deepeval else None

        # 获取 orchestrator (需要依赖注入改进)
        from src.api.main import app

        orchestrator = getattr(app.state, "orchestrator", None)
        if not orchestrator:
            logger.error("orchestrator_not_available", task_id=task_id)
            return

        runner = EvaluationRunner(
            orchestrator=orchestrator,
            ragas_evaluator=ragas,
            deepeval_evaluator=deepeval,
        )

        report = await runner.run_evaluation(
            test_cases=test_cases,
            collection=collection,
            name=name,
        )

        logger.info("evaluation_task_completed", task_id=task_id)

    except Exception as e:
        logger.error("evaluation_task_failed", task_id=task_id, error=str(e))


@router.post("/generate-testset", response_model=GenerateTestsetResponse)
async def generate_testset(request: GenerateTestsetRequest) -> GenerateTestsetResponse:
    """自动生成评估测试集

    Args:
        request: 生成测试集请求

    Returns:
        GenerateTestsetResponse: 生成的测试集
    """
    from src.infra.database.postgres import get_postgres_pool

    pool = await get_postgres_pool()

    # 从数据库获取文档内容
    rows = await pool.fetch(
        """SELECT id, filename FROM documents
           WHERE collection = $1 AND status = 'completed'
           LIMIT $2""",
        request.collection, request.max_docs,
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No completed documents in collection: {request.collection}",
        )

    # 获取文档的 chunk 内容
    doc_texts = []
    for row in rows:
        try:
            from src.infra.database.milvus_client import get_milvus
            from src.infra.config.settings import get_settings

            milvus = get_milvus()
            settings = get_settings()

            chunks = milvus.query(
                collection_name=settings.MILVUS_COLLECTION_NAME,
                filter=f'doc_id == "{row["id"]}"',
                output_fields=["content"],
                limit=20,
            )

            if chunks:
                doc_text = "\n\n".join([c["content"] for c in chunks])
                doc_texts.append(doc_text)
        except Exception as e:
            logger.warning("failed_to_fetch_chunks", doc_id=row["id"], error=str(e))
            continue

    if not doc_texts:
        raise HTTPException(
            status_code=404,
            detail="No document chunks found for testset generation",
        )

    # 生成测试集
    generator = TestsetGenerator()
    test_cases = await generator.generate_from_documents(
        documents=doc_texts,
        count_per_doc=request.count_per_doc,
    )

    return GenerateTestsetResponse(
        total=len(test_cases),
        test_cases=[tc.model_dump() if hasattr(tc, 'model_dump') else {
            "question": tc.question,
            "ground_truth": tc.ground_truth,
            "generated_answer": tc.generated_answer,
            "contexts": tc.contexts,
        } for tc in test_cases],
    )


@router.get("/reports")
async def list_evaluation_reports(
    page: int = 1,
    page_size: int = 20,
) -> list[EvaluationReportSummary]:
    """获取评估报告列表

    Args:
        page: 页码
        page_size: 每页数量

    Returns:
        list[EvaluationReportSummary]: 报告列表
    """
    from src.infra.database.postgres import get_postgres_pool

    pool = await get_postgres_pool()
    offset = (page - 1) * page_size

    rows = await pool.fetch(
        """SELECT id, name, dataset_size, status, metrics,
                  created_at
           FROM evaluation_runs
           ORDER BY created_at DESC
           LIMIT $1 OFFSET $2""",
        page_size, offset,
    )

    return [
        EvaluationReportSummary(
            run_id=row["id"],
            name=row["name"],
            dataset_size=row["dataset_size"],
            status=row["status"],
            metrics=row["metrics"],
            created_at=row["created_at"].isoformat() if row["created_at"] else "",
        )
        for row in rows
    ]


@router.get("/reports/{run_id}")
async def get_evaluation_report(run_id: str) -> EvaluationReportDetail:
    """获取评估报告详情

    Args:
        run_id: 评估运行 ID

    Returns:
        EvaluationReportDetail: 报告详情
    """
    from src.infra.database.postgres import get_postgres_pool

    pool = await get_postgres_pool()

    run = await pool.fetchrow(
        "SELECT * FROM evaluation_runs WHERE id = $1", run_id
    )
    if not run:
        raise HTTPException(status_code=404, detail="Report not found")

    samples = await pool.fetch(
        """SELECT question, ground_truth, generated_answer, contexts, metrics
           FROM evaluation_results WHERE run_id = $1""",
        run_id,
    )

    return EvaluationReportDetail(
        run_id=run["id"],
        name=run["name"],
        dataset_size=run["dataset_size"],
        status=run["status"],
        avg_metrics=run["metrics"] or {},
        config=run["config"] or {},
        created_at=run["created_at"].isoformat() if run["created_at"] else "",
        samples=[
            {
                "question": s["question"],
                "ground_truth": s["ground_truth"],
                "generated_answer": s["generated_answer"],
                "metrics": s["metrics"],
            }
            for s in samples
        ],
    )

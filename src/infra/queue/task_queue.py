"""ARQ 异步任务队列模块

提供文档处理的异步任务队列功能。
"""

import time
from dataclasses import dataclass
from typing import Any

import structlog
from arq import cron
from arq.connections import RedisSettings
from arq.constants import TimeoutSeconds
from arq.worker import Worker

from src.infra.config.settings import get_settings

logger = structlog.get_logger()

# 在模块加载时评估一次 settings
_settings = get_settings()


@dataclass
class DocumentProcessingResult:
    """文档处理结果"""
    doc_id: str
    file_path: str
    file_type: str
    collection: str
    chunk_count: int
    status: str  # "success" / "failed"
    error: str | None = None
    processing_time_ms: float = 0.0


async def process_document_job(
    ctx: dict[str, Any],
    doc_id: str,
    file_path: str,
    file_type: str,
    collection: str,
) -> DocumentProcessingResult:
    """异步文档处理任务

    执行完整的文档处理流程：解析 → 分块 → Embedding → 存储到 Milvus。

    Args:
        ctx: ARQ 上下文 (包含 redis 连接等)
        doc_id: 文档 ID
        file_path: 文件路径
        file_type: 文件类型 (pdf/docx/md/txt)
        collection: 知识库集合名称

    Returns:
        DocumentProcessingResult: 处理结果
    """
    start_time = time.time()
    settings = get_settings()

    logger.info(
        "document_processing_job_start",
        doc_id=doc_id,
        file_path=file_path,
        file_type=file_type,
        collection=collection,
    )

    try:
        # 动态导入以避免循环依赖
        from src.core.rag.ingestion.pipeline import IngestionPipeline

        # 创建摄取管道
        pipeline = IngestionPipeline(settings=settings)

        # 执行处理
        chunk_count = await pipeline.process(
            doc_id=doc_id,
            file_path=file_path,
            file_type=file_type,
            collection=collection,
        )

        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "document_processing_job_completed",
            doc_id=doc_id,
            chunk_count=chunk_count,
            processing_time_ms=processing_time_ms,
        )

        return DocumentProcessingResult(
            doc_id=doc_id,
            file_path=file_path,
            file_type=file_type,
            collection=collection,
            chunk_count=chunk_count,
            status="success",
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000

        logger.error(
            "document_processing_job_failed",
            doc_id=doc_id,
            error=str(e),
            processing_time_ms=processing_time_ms,
        )

        return DocumentProcessingResult(
            doc_id=doc_id,
            file_path=file_path,
            file_type=file_type,
            collection=collection,
            chunk_count=0,
            status="failed",
            error=str(e),
            processing_time_ms=processing_time_ms,
        )


class WorkerSettings:
    """ARQ Worker 配置

    配置 Redis 连接参数和任务函数。
    """

    # 任务函数列表
    functions = [process_document_job]

    # Redis 连接配置
    redis_settings = RedisSettings(
        host=_settings.REDIS_HOST,
        port=_settings.REDIS_PORT,
        database=_settings.REDIS_DB,
        password=(
            _settings.REDIS_PASSWORD.get_secret_value()
            if _settings.REDIS_PASSWORD
            else None
        ),
    )

    # 工作队列名称
    queue_name = "qa-assistant-queue"

    # 并发配置
    max_jobs = 10  # 最大并发任务数

    # 超时配置
    job_timeout = TimeoutSeconds.default * 3  # 5 分钟超时 (默认 5 * 60 = 300s)

    # 重新排队配置
    keep_result = 3600 * 24  # 保留结果 24 小时

    # 健康检查
    health_check_interval = 30  # 健康检查间隔 (秒)

    # 重试配置
    max_retries = 3  # 最大重试次数
    retry_delay = 60  # 重试延迟 (秒)

    @classmethod
    def get_worker(cls) -> Worker:
        """获取配置好的 Worker 实例

        Returns:
            Worker: ARQ Worker 实例
        """
        return Worker(
            functions=cls.functions,
            redis_settings=cls.redis_settings,
            queue_name=cls.queue_name,
            max_jobs=cls.max_jobs,
            job_timeout=cls.job_timeout,
            keep_result=cls.keep_result,
            health_check_interval=cls.health_check_interval,
            max_retries=cls.max_retries,
            retry_delay=cls.retry_delay,
        )

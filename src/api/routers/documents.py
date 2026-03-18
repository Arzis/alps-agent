"""文档管理路由 - 处理文档上传和查询"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
import structlog

from src.schemas.document import (
    DocumentUploadResponse, DocumentInfo,
    DocumentListResponse, DocumentStatus,
)
from src.infra.config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection: str = Form("default"),
):
    """
    上传文档

    支持格式: PDF, DOCX, MD, TXT
    上传后异步处理: 解析 → 分块 → Embedding → 向量索引

    Args:
        background_tasks: FastAPI 后台任务管理器
        file: 上传的文件
        collection: 知识库集合名称

    Returns:
        DocumentUploadResponse: 上传结果 (包含 doc_id)
    """
    settings = get_settings()

    # ============================================================
    # 校验文件类型
    # ============================================================
    file_ext = f".{file.filename.rsplit('.', 1)[-1].lower()}" if '.' in file.filename else ""
    if file_ext not in settings.UPLOAD_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}. "
                   f"支持: {settings.UPLOAD_ALLOWED_EXTENSIONS}",
        )

    # ============================================================
    # 校验文件大小
    # ============================================================
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # ============================================================
    # 生成文档 ID 并保存文件
    # ============================================================
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    file_path = f"uploads/{collection}/{doc_id}{file_ext}"

    # 确保目录存在 (Phase2 改为 MinIO 存储)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    # ============================================================
    # 写入数据库记录
    # ============================================================
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    await pool.execute(
        """INSERT INTO documents
           (id, collection, filename, file_type, file_size, file_path, status)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        doc_id, collection, file.filename, file_ext,
        len(content), file_path, DocumentStatus.PROCESSING.value,
    )

    logger.info(
        "document_uploaded",
        doc_id=doc_id,
        filename=file.filename,
        file_type=file_ext,
        file_size=len(content),
        collection=collection,
    )

    # ============================================================
    # 添加后台处理任务
    # ============================================================
    background_tasks.add_task(
        process_document_task,
        doc_id=doc_id,
        file_path=file_path,
        file_type=file_ext,
        collection=collection,
    )

    return DocumentUploadResponse(
        doc_id=doc_id,
        filename=file.filename,
        status=DocumentStatus.PROCESSING,
    )


async def process_document_task(
    doc_id: str,
    file_path: str,
    file_type: str,
    collection: str,
) -> None:
    """异步文档处理任务

    在后台执行: 解析 → 分块 → Embedding → 向量索引

    Args:
        doc_id: 文档 ID
        file_path: 文件路径
        file_type: 文件类型
        collection: 知识库集合
    """
    from src.core.rag.ingestion.pipeline import get_ingestion_pipeline
    from src.infra.database.postgres import get_postgres_pool

    pool = await get_postgres_pool()

    try:
        # 获取文档处理管道
        pipeline = get_ingestion_pipeline()
        # 处理文档并获取分块数量
        chunk_count = await pipeline.process(
            doc_id=doc_id,
            file_path=file_path,
            file_type=file_type,
            collection=collection,
        )

        # 更新文档状态为完成
        await pool.execute(
            """UPDATE documents
               SET status = $1, chunk_count = $2, updated_at = NOW()
               WHERE id = $3""",
            DocumentStatus.COMPLETED.value, chunk_count, doc_id,
        )

        logger.info(
            "document_processed",
            doc_id=doc_id,
            chunk_count=chunk_count,
        )

    except Exception as e:
        # 更新文档状态为失败
        await pool.execute(
            """UPDATE documents
               SET status = $1, error_message = $2, updated_at = NOW()
               WHERE id = $3""",
            DocumentStatus.FAILED.value, str(e), doc_id,
        )
        logger.error("document_processing_failed", doc_id=doc_id, error=str(e))


@router.get("/{doc_id}", response_model=DocumentInfo)
async def get_document(doc_id: str):
    """查询文档状态和信息

    Args:
        doc_id: 文档 ID

    Returns:
        DocumentInfo: 文档详细信息

    Raises:
        HTTPException: 文档不存在时返回 404
    """
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    row = await pool.fetchrow(
        "SELECT * FROM documents WHERE id = $1", doc_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentInfo(
        doc_id=row["id"],
        filename=row["filename"],
        file_type=row["file_type"],
        file_size=row["file_size"],
        collection=row["collection"],
        status=DocumentStatus(row["status"]),
        chunk_count=row["chunk_count"] or 0,
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    collection: str = "default",
    page: int = 1,
    page_size: int = 20,
):
    """获取文档列表

    Args:
        collection: 知识库集合名称
        page: 页码 (从 1 开始)
        page_size: 每页数量

    Returns:
        DocumentListResponse: 文档列表响应
    """
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    # 计算分页偏移量
    offset = (page - 1) * page_size

    # 查询文档列表
    rows = await pool.fetch(
        """SELECT * FROM documents
           WHERE collection = $1
           ORDER BY created_at DESC
           LIMIT $2 OFFSET $3""",
        collection, page_size, offset
    )

    # 查询总数
    total = await pool.fetchval(
        "SELECT COUNT(*) FROM documents WHERE collection = $1",
        collection
    )

    documents = [
        DocumentInfo(
            doc_id=row["id"],
            filename=row["filename"],
            file_type=row["file_type"],
            file_size=row["file_size"],
            collection=row["collection"],
            status=DocumentStatus(row["status"]),
            chunk_count=row["chunk_count"] or 0,
            error_message=row["error_message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]

    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size,
    )

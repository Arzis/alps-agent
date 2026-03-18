"""RAG 摄取管道模块

这是 Phase 1 的桩实现。
Week 3 会实现真正的文档解析、分块、Embedding 和向量索引。
"""

from typing import Any

import structlog

logger = structlog.get_logger()


class IngestionPipeline:
    """
    文档摄取管道

    职责:
    1. 解析文档 (PDF, DOCX, MD, TXT)
    2. 分块 (Chunking)
    3. 生成 Embedding
    4. 存储到 Milvus

    Note:
        Week 3 会替换为 LlamaIndex 的 IngestionPipeline 实现。
    """

    def __init__(self):
        """初始化摄取管道"""
        pass

    async def process(
        self,
        doc_id: str,
        file_path: str,
        file_type: str,
        collection: str,
    ) -> int:
        """
        处理文档

        Phase 1: 桩实现，返回模拟的分块数

        Args:
            doc_id: 文档 ID
            file_path: 文件路径
            file_type: 文件类型 (如 .pdf)
            collection: 知识库集合

        Returns:
            int: 分块数量
        """
        logger.info(
            "document_processing_stub",
            doc_id=doc_id,
            file_path=file_path,
            file_type=file_type,
            collection=collection,
        )

        # Phase 1 桩实现 - 后续 Week 3 替换为真正的处理逻辑
        return 1  # 模拟返回 1 个分块


# 单例实例
_pipeline: IngestionPipeline | None = None


def get_ingestion_pipeline() -> IngestionPipeline:
    """获取摄取管道实例 (单例)"""
    global _pipeline
    if _pipeline is None:
        _pipeline = IngestionPipeline()
    return _pipeline

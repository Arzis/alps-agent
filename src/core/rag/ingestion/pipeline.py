"""RAG 摄取管道模块

完整流程: 解析 → 分块 → Embedding → 写入 Milvus
"""

import asyncio
import time
from datetime import datetime

import structlog
from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding

from src.core.rag.ingestion.parser import DocumentParser
from src.core.rag.ingestion.chunker import DocumentChunker
from src.infra.config.settings import Settings, get_settings
from src.infra.database.milvus_client import get_milvus

logger = structlog.get_logger()

# 全局管道实例
_pipeline: "IngestionPipeline | None" = None


class IngestionPipeline:
    """
    文档摄取管道

    完整流程: 解析 → 分块 → Embedding → 写入 Milvus
    """

    def __init__(self, settings: Settings):
        """初始化摄取管道

        Args:
            settings: 应用配置
        """
        self.settings = settings
        self.parser = DocumentParser()
        self.chunker = DocumentChunker(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        )
        # Embedding 模型
        self.embedding_model = OpenAIEmbedding(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            api_base=settings.OPENAI_API_BASE,
            dimensions=settings.EMBEDDING_DIMENSION,
        )
        # 并发控制信号量
        self._embedding_semaphore = asyncio.Semaphore(
            settings.MAX_EMBEDDING_CONCURRENT
        )

    async def process(
        self,
        doc_id: str,
        file_path: str,
        file_type: str,
        collection: str,
    ) -> int:
        """处理文档的完整流程

        Args:
            doc_id: 文档唯一标识
            file_path: 文件路径
            file_type: 文件类型 (如 ".pdf")
            collection: 知识库集合名称

        Returns:
            int: 处理的 chunk 数量
        """
        start_time = time.perf_counter()

        # 1. 解析文档
        logger.info("ingestion_step", step="parsing", doc_id=doc_id)
        documents = await self.parser.parse(file_path, file_type)

        if not documents:
            logger.warning("no_content_parsed", doc_id=doc_id)
            return 0

        # 2. 分块
        logger.info("ingestion_step", step="chunking", doc_id=doc_id)
        nodes = self.chunker.chunk(documents, doc_id, collection)

        if not nodes:
            logger.warning("no_chunks_generated", doc_id=doc_id)
            return 0

        # 3. 批量 Embedding
        logger.info(
            "ingestion_step",
            step="embedding",
            doc_id=doc_id,
            num_chunks=len(nodes),
        )
        embeddings = await self._batch_embed(nodes)

        # 4. 写入 Milvus
        logger.info("ingestion_step", step="indexing", doc_id=doc_id)
        await self._upsert_to_milvus(nodes, embeddings, doc_id, collection)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "ingestion_completed",
            doc_id=doc_id,
            num_chunks=len(nodes),
            latency_ms=round(elapsed_ms, 2),
        )

        return len(nodes)

    async def _batch_embed(
        self, nodes: list[TextNode], batch_size: int = 20
    ) -> list[list[float]]:
        """批量计算 Embedding (带并发控制)

        Args:
            nodes: TextNode 列表
            batch_size: 每批大小，默认 20

        Returns:
            list[list[float]]: Embedding 向量列表
        """
        all_embeddings = []

        for i in range(0, len(nodes), batch_size):
            batch = nodes[i : i + batch_size]
            texts = [node.text for node in batch]

            # 并发控制
            async with self._embedding_semaphore:
                batch_embeddings = await self.embedding_model.aget_text_embedding_batch(
                    texts
                )
                all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def _upsert_to_milvus(
        self,
        nodes: list[TextNode],
        embeddings: list[list[float]],
        doc_id: str,
        collection: str,
    ) -> None:
        """写入 Milvus 向量数据库

        Args:
            nodes: TextNode 列表
            embeddings: Embedding 向量列表
            doc_id: 文档唯一标识
            collection: 知识库集合名称
        """
        milvus = get_milvus()
        collection_name = self.settings.MILVUS_COLLECTION_NAME

        # 准备数据
        data = []
        for node, embedding in zip(nodes, embeddings):
            data.append({
                "id": node.id_,  # 格式: "{doc_id}_chunk_{i:04d}"
                "doc_id": doc_id,
                "chunk_index": node.metadata.get("chunk_index", 0),
                "content": node.text,
                "embedding": embedding,
                "doc_title": node.metadata.get("source", ""),
                "collection": collection,
                "created_at": int(datetime.utcnow().timestamp()),
            })

        # 批量写入 (每批 100 条)
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            milvus.upsert(
                collection_name=collection_name,
                data=batch,
            )

        logger.info(
            "milvus_upserted",
            doc_id=doc_id,
            num_vectors=len(data),
        )


def get_ingestion_pipeline() -> IngestionPipeline:
    """获取摄取管道实例 (单例)

    Returns:
        IngestionPipeline: 摄取管道实例
    """
    global _pipeline
    if _pipeline is None:
        _pipeline = IngestionPipeline(get_settings())
    return _pipeline

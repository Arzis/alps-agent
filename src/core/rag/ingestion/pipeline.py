"""RAG 摄取管道模块 - Phase 2 增强版

完整流程: 解析 → 分块 → 元数据增强 → Embedding → 写入 Milvus (+ ES备选)
"""

import asyncio
import time
from datetime import datetime

import structlog
from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding

from src.core.rag.ingestion.parser import DocumentParser
from src.core.rag.ingestion.chunker import DocumentChunker, ChunkerConfig, ChunkingStrategy
from src.core.rag.ingestion.metadata_extractor import MetadataExtractor
from src.infra.config.settings import Settings, get_settings
from src.infra.database.milvus_client import get_milvus
from src.infra.embedding.provider import BaseEmbeddingProvider, create_embedding_provider

logger = structlog.get_logger()

# 全局管道实例
_pipeline: "IngestionPipeline | None" = None


class IngestionPipeline:
    """
    文档摄取管道 - Phase 2 增强版

    完整流程: 解析 → 分块 → 元数据增强 → Embedding → 写入 Milvus (+ ES备选)

    Phase 2 新增:
    1. 语义分块策略
    2. 元数据增强提取
    3. ES BM25索引写入 (Week 8)
    """

    def __init__(
        self,
        settings: Settings,
        embedding_provider: BaseEmbeddingProvider | None = None,
        chunker: DocumentChunker | None = None,
        enable_metadata_extraction: bool = True,
    ):
        """初始化摄取管道

        Args:
            settings: 应用配置
            embedding_provider: Embedding provider 实例 (默认自动创建)
            chunker: 文档分块器 (默认自动创建)
            enable_metadata_extraction: 是否启用元数据提取
        """
        self.settings = settings
        self.parser = DocumentParser()

        # Embedding Provider
        if embedding_provider is None:
            embedding_provider = create_embedding_provider(settings)
        self._provider = embedding_provider

        # 分块器
        if chunker:
            self.chunker = chunker
        else:
            # 自动创建分块器（带语义分块能力）
            embedding_model = self._create_embedding_model()
            self.chunker = DocumentChunker(
                config=ChunkerConfig(
                    strategy=ChunkingStrategy.AUTO,
                    chunk_size=settings.RAG_CHUNK_SIZE,
                    chunk_overlap=settings.RAG_CHUNK_OVERLAP,
                ),
                embedding_model=embedding_model,
            )

        # 元数据提取器
        self.metadata_extractor = None
        if enable_metadata_extraction:
            self.metadata_extractor = MetadataExtractor()

        # 并发控制信号量
        self._embedding_semaphore = asyncio.Semaphore(
            settings.MAX_EMBEDDING_CONCURRENT
        )

    def _create_embedding_model(self) -> OpenAIEmbedding | None:
        """创建用于语义分块的Embedding模型"""
        try:
            return OpenAIEmbedding(
                model=self._provider.model,
                api_key=self.settings.EMBEDDING_API_KEY,
                api_base=self.settings.EMBEDDING_BASE_URL,
                dimensions=self._provider.dimension,
            )
        except Exception as e:
            logger.warning("embedding_model_creation_failed", error=str(e))
            return None

    async def process(
        self,
        doc_id: str,
        file_path: str,
        file_type: str,
        collection: str,
        chunking_strategy: ChunkingStrategy | None = None,
        enable_metadata_extraction: bool = True,
    ) -> int:
        """处理文档的完整流程 - Phase 2 增强版

        Args:
            doc_id: 文档唯一标识
            file_path: 文件路径
            file_type: 文件类型 (如 ".pdf")
            collection: 知识库集合名称
            chunking_strategy: 分块策略 (None则自动选择)
            enable_metadata_extraction: 是否启用元数据提取 (默认True)

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

        # 2. 分块 (支持语义分块)
        logger.info("ingestion_step", step="chunking", doc_id=doc_id)
        nodes = self.chunker.chunk(
            documents,
            doc_id=doc_id,
            collection=collection,
            strategy=chunking_strategy,
        )

        if not nodes:
            logger.warning("no_chunks_generated", doc_id=doc_id)
            return 0

        # 3. 元数据增强 (可选)
        if enable_metadata_extraction and self.metadata_extractor and len(nodes) <= 100:
            logger.info("ingestion_step", step="metadata_extraction", doc_id=doc_id)
            try:
                nodes = await self.metadata_extractor.extract(nodes)
            except Exception as e:
                logger.warning(
                    "metadata_extraction_failed_continuing",
                    doc_id=doc_id,
                    error=str(e),
                )

        # 4. 批量 Embedding
        logger.info(
            "ingestion_step",
            step="embedding",
            doc_id=doc_id,
            num_chunks=len(nodes),
        )
        embeddings = await self._batch_embed(nodes)

        # 5. 并行写入 Milvus (+ ES备选)
        logger.info("ingestion_step", step="indexing", doc_id=doc_id)
        await asyncio.gather(
            self._upsert_to_milvus(nodes, embeddings, doc_id, collection),
            self._upsert_to_elasticsearch(nodes, doc_id, collection),
        )

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

        使用增强文本(如果有)进行embedding

        Args:
            nodes: TextNode 列表
            batch_size: 每批大小，默认 20

        Returns:
            list[list[float]]: Embedding 向量列表
        """
        all_embeddings = []

        for i in range(0, len(nodes), batch_size):
            # 批量大小不超过 10
            batch = nodes[i : i + min(batch_size, 10)]
            # 使用增强文本(如果有 _enriched_text 的话)
            texts = [
                node.metadata.get("_enriched_text", node.text)
                for node in batch
            ]

            # 并发控制
            async with self._embedding_semaphore:
                batch_embeddings = await self._provider.embed(texts)
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
            record = {
                "id": node.id_,  # 格式: "{doc_id}_chunk_{i:04d}"
                "doc_id": doc_id,
                "chunk_index": node.metadata.get("chunk_index", 0),
                "content": node.text,
                "embedding": embedding,
                "doc_title": node.metadata.get("source", ""),
                "collection": collection,
                "created_at": int(datetime.utcnow().timestamp()),
            }
            # 只添加已定义的字段（Milvus schema 必须匹配）
            # 如果 Milvus collection 开启了 dynamic field，可以添加额外字段
            # 但目前只使用预定义的字段
            data.append(record)

        # 批量写入 (每批 100 条)
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            try:
                milvus.upsert(
                    collection_name=collection_name,
                    data=batch,
                )
            except Exception as e:
                logger.error("milvus_upsert_batch_failed", doc_id=doc_id, batch=i//batch_size, error=str(e), exc_info=True)
                raise

        logger.info(
            "milvus_upserted",
            doc_id=doc_id,
            num_vectors=len(data),
        )

    async def _upsert_to_elasticsearch(
        self,
        nodes: list[TextNode],
        doc_id: str,
        collection: str,
    ) -> None:
        """写入 Elasticsearch (BM25 稀疏检索)

        Note: ES客户端在 Week 8 实现，此处先预留接口

        Args:
            nodes: TextNode 列表
            doc_id: 文档唯一标识
            collection: 知识库集合名称
        """
        try:
            from src.infra.database.elasticsearch import get_elasticsearch
            es = await get_elasticsearch()

            index_name = f"qa_chunks_{collection}"

            # 确保索引存在
            if not await es.indices.exists(index=index_name):
                await es.indices.create(
                    index=index_name,
                    body={
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 0,
                            "analysis": {
                                "analyzer": {
                                    "text_analyzer": {
                                        "type": "standard",
                                    }
                                }
                            }
                        },
                        "mappings": {
                            "properties": {
                                "chunk_id": {"type": "keyword"},
                                "doc_id": {"type": "keyword"},
                                "content": {
                                    "type": "text",
                                    "analyzer": "text_analyzer",
                                },
                                "doc_title": {"type": "text"},
                                "collection": {"type": "keyword"},
                                "chunk_index": {"type": "integer"},
                                "keywords": {"type": "text"},
                                "summary": {"type": "text"},
                                "created_at": {"type": "date", "format": "epoch_second"},
                            }
                        }
                    },
                )

            # 批量写入
            actions = []
            for node in nodes:
                actions.append({"index": {"_index": index_name, "_id": node.id_}})
                actions.append({
                    "chunk_id": node.id_,
                    "doc_id": doc_id,
                    "content": node.text,
                    "doc_title": node.metadata.get("source", ""),
                    "collection": collection,
                    "chunk_index": node.metadata.get("chunk_index", 0),
                    "keywords": node.metadata.get("extracted_keywords", ""),
                    "summary": node.metadata.get("extracted_summary", ""),
                    "created_at": int(datetime.utcnow().timestamp()),
                })

            if actions:
                await es.bulk(body=actions)

            logger.info(
                "elasticsearch_upserted",
                doc_id=doc_id,
                index=index_name,
                num_docs=len(nodes),
            )

        except ImportError:
            # ES客户端尚未实现，跳过
            logger.debug("elasticsearch_not_available_skip_upsert", doc_id=doc_id)
        except Exception as e:
            # ES写入失败不应阻断整个管道
            logger.warning(
                "elasticsearch_upsert_failed",
                doc_id=doc_id,
                error=str(e),
            )


def get_ingestion_pipeline(
    embedding_provider: BaseEmbeddingProvider | None = None,
) -> IngestionPipeline:
    """获取摄取管道实例 (单例)

    Args:
        embedding_provider: Embedding provider 实例 (可选，默认自动创建)

    Returns:
        IngestionPipeline: 摄取管道实例
    """
    global _pipeline
    if _pipeline is None or embedding_provider is not None:
        _pipeline = IngestionPipeline(
            get_settings(),
            embedding_provider=embedding_provider,
        )
    return _pipeline

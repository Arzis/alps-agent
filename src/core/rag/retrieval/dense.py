"""Dense 检索器模块

基于 Milvus 向量数据库的密集检索实现。
"""

import asyncio
from dataclasses import dataclass

import structlog
from openai import AsyncOpenAI
from pymilvus import MilvusClient

from src.infra.config.settings import Settings

logger = structlog.get_logger()


@dataclass
class RetrievedChunk:
    """检索到的文档块"""
    chunk_id: str  # 块 ID
    doc_id: str  # 文档 ID
    content: str  # 文档内容
    score: float  # 相似度分数
    doc_title: str  # 文档标题
    chunk_index: int  # 块索引
    collection: str  # 集合名称


class DenseRetriever:
    """
    稠密检索器 - Milvus 向量相似度检索

    Phase 1: 纯 Dense 检索
    Phase 2: 增加 Sparse 检索 + 混合融合
    """

    def __init__(
        self,
        milvus_client: MilvusClient,
        settings: Settings,
    ):
        """初始化检索器

        Args:
            milvus_client: Milvus 客户端实例
            settings: 应用配置
        """
        self.milvus = milvus_client
        self.settings = settings
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        # OpenAI 兼容客户端 (DashScope)
        self._embedding_client = AsyncOpenAI(
            api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
            base_url=settings.DASHSCOPE_BASE_URL,
        )
        self._embedding_model = settings.EMBEDDING_MODEL
        self._embedding_dim = settings.EMBEDDING_DIMENSION

    async def retrieve(
        self,
        query: str,
        collection: str = "default",
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """检索与 query 最相关的文档块

        Args:
            query: 查询文本
            collection: 知识库集合名称，默认 "default"
            top_k: 返回的最相关结果数量，默认使用配置中的 RAG_TOP_K
            similarity_threshold: 最低相似度阈值，默认使用配置中的 RAG_SIMILARITY_THRESHOLD

        Returns:
            list[RetrievedChunk]: 检索到的文档块列表
        """
        top_k = top_k or self.settings.RAG_TOP_K
        threshold = similarity_threshold or self.settings.RAG_SIMILARITY_THRESHOLD

        # 1. 计算 query 的 embedding (使用 OpenAI 兼容接口)
        response = await self._embedding_client.embeddings.create(
            model=self._embedding_model,
            input=query,
            dimensions=self._embedding_dim,
            encoding_format="float",
        )
        query_embedding = response.data[0].embedding

        # 2. Milvus 向量检索
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.milvus.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                filter=f'collection == "{collection}"',
                limit=top_k,
                output_fields=[
                    "content", "doc_id", "doc_title",
                    "chunk_index", "collection",
                ],
                search_params={
                    "metric_type": "COSINE",  # 余弦相似度
                    "params": {"ef": 128},  # HNSW 搜索参数
                },
            ),
        )

        if not results or not results[0]:
            logger.info("no_results_found", query=query[:100], collection=collection)
            return []

        # 3. 过滤低分结果并构建返回对象
        chunks = []
        for hit in results[0]:
            score = hit["distance"]  # Milvus COSINE 返回的是相似度 (0-1)

            # 过滤低于阈值的结果
            if score < threshold:
                continue

            chunks.append(
                RetrievedChunk(
                    chunk_id=hit["id"],
                    doc_id=hit["entity"]["doc_id"],
                    content=hit["entity"]["content"],
                    score=score,
                    doc_title=hit["entity"]["doc_title"],
                    chunk_index=hit["entity"]["chunk_index"],
                    collection=hit["entity"]["collection"],
                )
            )

        logger.info(
            "retrieval_completed",
            query=query[:100],
            collection=collection,
            total_hits=len(results[0]),
            filtered_hits=len(chunks),
            top_score=chunks[0].score if chunks else 0,
        )

        return chunks

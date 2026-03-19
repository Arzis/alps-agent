"""RAG 检索器统一接口模块

Phase 2: Dense + Sparse (BM25) + RRF + Rerank
"""

import structlog

from src.core.rag.retrieval.dense import DenseRetriever, RetrievedChunk
from src.core.rag.retrieval.sparse import SparseRetriever
from src.core.rag.retrieval.hybrid import HybridRetriever
from src.core.rag.retrieval.reranker import BaseReranker, CrossEncoderReranker

logger = structlog.get_logger()


class RAGRetriever:
    """
    RAG 检索器 - 统一检索接口

    Phase 2:
    - Dense + Sparse 多路召回
    - RRF 融合
    - Cross-Encoder Rerank
    - 支持查询扩展 (Multi-Query)
    """

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever | None = None,
        reranker: BaseReranker | None = None,
    ):
        """初始化检索器

        Args:
            dense_retriever: Dense 检索器 (Milvus)
            sparse_retriever: Sparse 检索器 (ES BM25)，可选
            reranker: 重排器 (Cross-Encoder)，可选
        """
        self.hybrid = HybridRetriever(
            dense_retriever=dense_retriever,
            sparse_retriever=sparse_retriever,
            reranker=reranker,
        )

    async def retrieve(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        expanded_queries: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        """统一检索接口

        Args:
            query: 主查询 (建议使用改写后的查询)
            collection: 知识库集合名
            top_k: 返回结果数
            expanded_queries: 扩展查询列表 (查询理解节点生成)
        """
        return await self.hybrid.retrieve(
            query=query,
            expanded_queries=expanded_queries,
            collection=collection,
            top_k=top_k,
        )

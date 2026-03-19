"""混合检索器模块 - Dense + Sparse + RRF + Rerank

混合检索：并行执行 Dense (Milvus) + Sparse (ES BM25) 检索，
RRF (Reciprocal Rank Fusion) 融合排序，Cross-Encoder Rerank 精排。
"""

import asyncio
from collections import defaultdict
from typing import TYPE_CHECKING

import structlog

from src.core.rag.retrieval.dense import DenseRetriever, RetrievedChunk

if TYPE_CHECKING:
    from src.core.rag.retrieval.sparse import SparseRetriever
    from src.core.rag.retrieval.reranker import BaseReranker

logger = structlog.get_logger()


class HybridRetriever:
    """
    混合检索器

    1. 并行执行 Dense (Milvus) + Sparse (ES BM25) 检索
    2. RRF (Reciprocal Rank Fusion) 融合排序
    3. Cross-Encoder Rerank 精排
    """

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        sparse_retriever: "SparseRetriever | None" = None,
        reranker: "BaseReranker | None" = None,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        rrf_k: int = 60,
    ):
        """初始化混合检索器

        Args:
            dense_retriever: Dense 检索器 (Milvus)
            sparse_retriever: Sparse 检索器 (ES BM25)，可选
            reranker: 重排器 (Cross-Encoder)，可选
            dense_weight: Dense 检索权重
            sparse_weight: Sparse 检索权重
            rrf_k: RRF 融合参数 k
        """
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.reranker = reranker
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.rrf_k = rrf_k

    async def retrieve(
        self,
        query: str,
        expanded_queries: list[str] | None = None,
        collection: str = "default",
        top_k: int = 5,
        retrieval_top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """混合检索 + RRF + Rerank

        Args:
            query: 主查询 (改写后的)
            expanded_queries: 扩展查询列表 (用于多路召回)
            collection: 知识库集合名
            top_k: 最终返回数量
            retrieval_top_k: 初始召回数量 (默认 top_k * 4)
        """
        retrieval_top_k = retrieval_top_k or top_k * 4

        # ============================================================
        # Step 1: 并行多路召回
        # ============================================================
        all_queries = [query]
        if expanded_queries:
            all_queries.extend(expanded_queries[:2])  # 最多用2个扩展查询

        retrieval_tasks = []

        # Dense 检索 (每个查询都检索)
        for q in all_queries:
            retrieval_tasks.append(
                self._safe_retrieve(
                    self.dense.retrieve, q, collection, retrieval_top_k, "dense"
                )
            )

        # Sparse 检索 (只用主查询)
        if self.sparse:
            retrieval_tasks.append(
                self._safe_retrieve(
                    self.sparse.retrieve, query, collection, retrieval_top_k, "sparse"
                )
            )

        results = await asyncio.gather(*retrieval_tasks)

        # 按来源分组
        dense_results = []
        sparse_results = []
        for source, chunks in results:
            if source == "dense":
                dense_results.extend(chunks)
            elif source == "sparse":
                sparse_results.extend(chunks)

        # Dense 结果去重 (多个查询可能返回相同文档)
        dense_results = self._deduplicate(dense_results)

        logger.info(
            "hybrid_retrieval_raw_results",
            dense_count=len(dense_results),
            sparse_count=len(sparse_results),
            query=query[:100],
        )

        # ============================================================
        # Step 2: RRF 融合
        # ============================================================
        if sparse_results:
            fused = self._reciprocal_rank_fusion(
                dense_results=dense_results,
                sparse_results=sparse_results,
            )
        else:
            # 如果没有 Sparse 结果，直接用 Dense
            fused = dense_results

        # 取初步 Top-K
        candidates = fused[:top_k * 3]  # 给 Reranker 多一些候选

        # ============================================================
        # Step 3: Rerank (如果配置了 Reranker)
        # ============================================================
        if self.reranker and candidates:
            try:
                reranked = await self.reranker.rerank(
                    query=query,
                    chunks=candidates,
                    top_n=top_k,
                )
                logger.info(
                    "rerank_completed",
                    input_count=len(candidates),
                    output_count=len(reranked),
                    query=query[:100],
                )
                return reranked
            except Exception as e:
                logger.error("rerank_failed_using_rrf_results", error=str(e))
                return candidates[:top_k]

        return candidates[:top_k]

    def _reciprocal_rank_fusion(
        self,
        dense_results: list[RetrievedChunk],
        sparse_results: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """RRF 融合算法

        score(d) = w_dense / (k + rank_dense(d)) + w_sparse / (k + rank_sparse(d))

        Args:
            dense_results: Dense 检索结果
            sparse_results: Sparse 检索结果

        Returns:
            list[RetrievedChunk]: 融合后的结果
        """
        rrf_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, RetrievedChunk] = {}
        source_map: dict[str, set] = defaultdict(set)

        # Dense 分数
        for rank, chunk in enumerate(dense_results, start=1):
            cid = chunk.chunk_id
            rrf_scores[cid] += self.dense_weight / (self.rrf_k + rank)
            chunk_map[cid] = chunk
            source_map[cid].add("dense")

        # Sparse 分数
        for rank, chunk in enumerate(sparse_results, start=1):
            cid = chunk.chunk_id
            rrf_scores[cid] += self.sparse_weight / (self.rrf_k + rank)
            if cid not in chunk_map:
                chunk_map[cid] = chunk
            source_map[cid].add("sparse")

        # 按 RRF 分数排序
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        fused = []
        for cid in sorted_ids:
            chunk = chunk_map[cid]
            # 用 RRF 分数替换原始分数
            fused.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    content=chunk.content,
                    score=rrf_scores[cid],
                    doc_title=chunk.doc_title,
                    chunk_index=chunk.chunk_index,
                    collection=chunk.collection,
                )
            )

        # 记录融合统计
        both_count = sum(1 for s in source_map.values() if len(s) > 1)
        dense_only = sum(1 for s in source_map.values() if s == {"dense"})
        sparse_only = sum(1 for s in source_map.values() if s == {"sparse"})

        logger.info(
            "rrf_fusion_stats",
            total_unique=len(fused),
            both_sources=both_count,
            dense_only=dense_only,
            sparse_only=sparse_only,
        )

        return fused

    def _deduplicate(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """去重，保留分数最高的

        Args:
            chunks: 待去重的文档块列表

        Returns:
            list[RetrievedChunk]: 去重后的结果
        """
        seen = {}
        for chunk in chunks:
            if chunk.chunk_id not in seen or chunk.score > seen[chunk.chunk_id].score:
                seen[chunk.chunk_id] = chunk
        return list(seen.values())

    async def _safe_retrieve(
        self,
        fn,
        query: str,
        collection: str,
        top_k: int,
        source: str,
    ):
        """安全调用检索，捕获异常

        Args:
            fn: 检索函数
            query: 查询文本
            collection: 集合名称
            top_k: 返回数量
            source: 来源标识 (dense/sparse)

        Returns:
            tuple[str, list[RetrievedChunk]]: (来源, 结果列表)
        """
        try:
            results = await fn(query=query, collection=collection, top_k=top_k)
            return (source, results)
        except Exception as e:
            logger.error(f"{source}_retrieval_failed", error=str(e))
            return (source, [])

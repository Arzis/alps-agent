"""语义缓存模块

基于 Redis Stack 向量搜索的语义缓存，实现对相似问题的快速响应。
"""

import hashlib
import json
from datetime import datetime
from typing import TYPE_CHECKING

import numpy as np
import structlog

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from redis.commands.search.index import FT

from src.schemas.chat import CitationItem

logger = structlog.get_logger()


class CacheHit:
    """缓存命中结果"""

    def __init__(
        self,
        answer: str,
        citations: list[CitationItem],
        confidence: float,
        similarity: float,
        cached_query: str,
    ):
        self.answer = answer
        self.citations = citations
        self.confidence = confidence
        self.similarity = similarity
        self.cached_query = cached_query


class SemanticCache:
    """
    语义缓存 - 基于 Redis Stack 向量搜索

    核心思路:
    - 对用户问题计算 Embedding
    - 在缓存中搜索语义相似的已回答问题
    - 如果相似度超过阈值, 直接返回缓存答案
    - 大幅减少重复 LLM 调用, 降低延迟和成本

    性能预期:
    - 缓存命中: ~50ms (vs 完整 RAG 流程: ~3-5s)
    - 成本节省: 命中时零 LLM 调用费
    """

    INDEX_NAME = "idx:semantic_cache"
    KEY_PREFIX = "cache:semantic:"

    def __init__(
        self,
        redis: "Redis",
        embedding_fn: callable,
        similarity_threshold: float = 0.92,
        ttl: int = 86400,
        embedding_dim: int = 1024,
    ):
        """初始化语义缓存

        Args:
            redis: Redis 异步客户端
            embedding_fn: Embedding 函数，接受字符串返回向量列表
            similarity_threshold: 相似度阈值 (0-1)
            ttl: 缓存过期时间 (秒)
            embedding_dim: Embedding 向量维度
        """
        self.redis = redis
        self.embedding_fn = embedding_fn
        self.threshold = similarity_threshold
        self.ttl = ttl
        self.dim = embedding_dim
        self._initialized = False

    async def initialize(self) -> None:
        """创建 Redis Search 向量索引

        如果索引已存在则跳过创建。
        """
        if self._initialized:
            return

        try:
            # 检查索引是否已存在
            await self.redis.ft(self.INDEX_NAME).info()
            self._initialized = True
            logger.info("semantic_cache_index_exists")
            return
        except Exception:
            pass

        # 创建索引
        from redis.commands.search.field import VectorField, TextField, NumericField
        from redis.commands.search.indexDefinition import IndexDefinition, IndexType

        schema = (
            TextField("$.query", as_name="query"),
            TextField("$.answer", as_name="answer"),
            TextField("$.citations", as_name="citations"),
            TextField("$.collection", as_name="collection"),
            NumericField("$.confidence", as_name="confidence"),
            NumericField("$.timestamp", as_name="timestamp"),
            NumericField("$.hit_count", as_name="hit_count"),
            VectorField(
                "$.embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": self.dim,
                    "DISTANCE_METRIC": "COSINE",
                },
                as_name="embedding",
            ),
        )

        definition = IndexDefinition(
            prefix=[self.KEY_PREFIX],
            index_type=IndexType.JSON,
        )

        await self.redis.ft(self.INDEX_NAME).create_index(
            schema, definition=definition
        )

        self._initialized = True
        logger.info("semantic_cache_index_created", dim=self.dim)

    async def get(
        self, query: str, collection: str = "default"
    ) -> "CacheHit | None":
        """查询语义缓存

        Args:
            query: 用户问题
            collection: 知识库集合名

        Returns:
            CacheHit | None: 缓存命中结果，未命中返回 None
        """
        await self.initialize()

        # 1. 计算 query embedding
        query_embedding = await self.embedding_fn(query)
        if isinstance(query_embedding, list):
            query_embedding = query_embedding[0]
        embedding_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

        # 2. 向量相似度搜索
        from redis.commands.search.query import Query

        search_query = (
            Query(
                f'(@collection:{{{collection}}})=>[KNN 3 @embedding $vec AS distance]'
            )
            .sort_by("distance")
            .return_fields(
                "query", "answer", "citations", "confidence",
                "distance", "collection", "hit_count",
            )
            .dialect(2)
        )

        try:
            results = await self.redis.ft(self.INDEX_NAME).search(
                search_query,
                query_params={"vec": embedding_bytes},
            )
        except Exception as e:
            logger.error("semantic_cache_search_failed", error=str(e))
            return None

        if not results.docs:
            logger.debug("semantic_cache_miss", query=query[:100])
            return None

        # 3. 检查最佳结果是否超过阈值
        best = results.docs[0]
        distance = float(best.distance)
        similarity = 1 - distance  # COSINE distance -> similarity

        if similarity >= self.threshold:
            # 缓存命中！
            cache_key = best.id
            current_count = 0

            # 增加命中计数
            try:
                current_count = int(best.hit_count) if best.hit_count else 0
                await self.redis.json().set(
                    cache_key, "$.hit_count", current_count + 1
                )
                # 刷新 TTL
                await self.redis.expire(cache_key, self.ttl)
            except Exception:
                pass

            citations = json.loads(best.citations) if best.citations else []

            logger.info(
                "semantic_cache_hit",
                query=query[:100],
                cached_query=best.query[:100] if best.query else "",
                similarity=round(similarity, 4),
                hit_count=current_count + 1,
            )

            return CacheHit(
                answer=best.answer,
                citations=[CitationItem(**c) for c in citations],
                confidence=float(best.confidence) if best.confidence else 0.0,
                similarity=similarity,
                cached_query=best.query or "",
            )

        logger.debug(
            "semantic_cache_miss_below_threshold",
            query=query[:100],
            best_similarity=round(similarity, 4),
            threshold=self.threshold,
        )
        return None

    async def set(
        self,
        query: str,
        answer: str,
        collection: str = "default",
        citations: list[CitationItem] | None = None,
        confidence: float = 0.0,
    ) -> None:
        """写入语义缓存

        Args:
            query: 用户问题
            answer: 生成的回答
            collection: 知识库集合名
            citations: 引用列表
            confidence: 置信度
        """
        await self.initialize()

        # 只缓存高质量回答
        if confidence < 0.5:
            logger.debug(
                "semantic_cache_skip_low_confidence",
                confidence=confidence,
            )
            return

        query_embedding = await self.embedding_fn(query)
        if isinstance(query_embedding, list):
            query_embedding = query_embedding[0]

        cache_key = f"{self.KEY_PREFIX}{hashlib.md5(query.encode()).hexdigest()}"

        citations_json = json.dumps(
            [c.model_dump() for c in (citations or [])],
            ensure_ascii=False,
        )

        await self.redis.json().set(
            cache_key,
            "$",
            {
                "query": query,
                "answer": answer,
                "citations": citations_json,
                "collection": collection,
                "confidence": confidence,
                "embedding": query_embedding,
                "timestamp": int(datetime.utcnow().timestamp()),
                "hit_count": 0,
            },
        )

        await self.redis.expire(cache_key, self.ttl)

        logger.info(
            "semantic_cache_set",
            query=query[:100],
            confidence=confidence,
            ttl=self.ttl,
        )

    async def invalidate_collection(self, collection: str) -> None:
        """清除指定集合的所有缓存

        Args:
            collection: 知识库集合名
        """
        from redis.commands.search.query import Query

        search_query = Query(f"@collection:{{{collection}}}").no_content()
        try:
            results = await self.redis.ft(self.INDEX_NAME).search(search_query)
            for doc in results.docs:
                await self.redis.delete(doc.id)
            logger.info(
                "semantic_cache_invalidated",
                collection=collection,
                count=len(results.docs),
            )
        except Exception as e:
            logger.error("semantic_cache_invalidate_failed", error=str(e))

    async def get_stats(self) -> dict:
        """获取缓存统计信息

        Returns:
            dict: 包含 total_entries 和 index_size_mb
        """
        try:
            info = await self.redis.ft(self.INDEX_NAME).info()
            return {
                "total_entries": info.get("num_docs", 0),
                "index_size_mb": round(
                    int(info.get("inverted_sz_mb", 0)) +
                    int(info.get("vector_index_sz_mb", 0)), 2
                ),
            }
        except Exception:
            return {"total_entries": 0, "index_size_mb": 0}

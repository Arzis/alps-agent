"""多级缓存管理器模块

实现 L1 精确匹配 + L2 语义匹配的两级缓存策略。
"""

import hashlib
import json

import structlog

from src.infra.cache.semantic_cache import SemanticCache, CacheHit
from src.schemas.chat import CitationItem

logger = structlog.get_logger()


class CacheManager:
    """
    多级缓存管理器

    Level 1: 精确匹配 (Redis KV) - 最快, ~1ms
        - 使用 query 的 MD5 哈希作为 key
        - 完全相同的问题直接返回

    Level 2: 语义匹配 (Redis Vector Search) - 快, ~50ms
        - 使用问题Embedding 向量搜索
        - 相似问题返回缓存答案
    """

    def __init__(self, semantic_cache: SemanticCache):
        """初始化缓存管理器

        Args:
            semantic_cache: 语义缓存实例
        """
        self.semantic = semantic_cache
        # Redis 客户端从 semantic_cache 获取
        self.redis = semantic_cache.redis

    async def get(
        self, query: str, collection: str = "default"
    ) -> "CacheHit | None":
        """查询缓存 (先精确后语义)

        Args:
            query: 用户问题
            collection: 知识库集合名

        Returns:
            CacheHit | None: 缓存命中结果
        """
        # Level 1: 精确匹配
        exact_key = self._exact_key(query, collection)
        exact_result = await self.redis.get(exact_key)
        if exact_result:
            data = json.loads(exact_result)
            logger.info("cache_hit_exact", query=query[:100])
            return CacheHit(
                answer=data["answer"],
                citations=[CitationItem(**c) for c in data.get("citations", [])],
                confidence=data.get("confidence", 0.0),
                similarity=1.0,
                cached_query=query,
            )

        # Level 2: 语义匹配
        semantic_result = await self.semantic.get(query, collection)
        if semantic_result:
            # 同时写入精确缓存 (下次直接命中 L1)
            await self._set_exact(query, collection, semantic_result)
            return semantic_result

        return None

    async def set(
        self,
        query: str,
        answer: str,
        collection: str = "default",
        citations: list[CitationItem] | None = None,
        confidence: float = 0.0,
    ) -> None:
        """写入缓存 (同时写入 L1 + L2)

        Args:
            query: 用户问题
            answer: 生成的回答
            collection: 知识库集合名
            citations: 引用列表
            confidence: 置信度
        """
        # L1: 精确缓存 (1小时过期)
        exact_key = self._exact_key(query, collection)
        data = {
            "answer": answer,
            "citations": [c.model_dump() for c in (citations or [])],
            "confidence": confidence,
        }
        await self.redis.set(exact_key, json.dumps(data, ensure_ascii=False), ex=3600)

        # L2: 语义缓存
        await self.semantic.set(
            query=query,
            answer=answer,
            collection=collection,
            citations=citations,
            confidence=confidence,
        )

        logger.info(
            "cache_set",
            query=query[:100],
            collection=collection,
            confidence=confidence,
        )

    async def invalidate(self, collection: str) -> None:
        """清除指定集合的缓存

        Args:
            collection: 知识库集合名
        """
        # 清除精确缓存 (使用 pattern 删除)
        pattern = f"cache:exact:{collection}:*"
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

        # 清除语义缓存
        await self.semantic.invalidate_collection(collection)

        logger.info("cache_invalidated", collection=collection)

    async def _set_exact(self, query: str, collection: str, cache_hit: CacheHit) -> None:
        """写入精确缓存

        Args:
            query: 用户问题
            collection: 知识库集合名
            cache_hit: 语义缓存命中结果
        """
        exact_key = self._exact_key(query, collection)
        data = {
            "answer": cache_hit.answer,
            "citations": [c.model_dump() for c in cache_hit.citations],
            "confidence": cache_hit.confidence,
        }
        await self.redis.set(exact_key, json.dumps(data, ensure_ascii=False), ex=3600)

    def _exact_key(self, query: str, collection: str) -> str:
        """生成精确匹配的缓存 key

        Args:
            query: 用户问题
            collection: 知识库集合名

        Returns:
            str: 缓存 key
        """
        query_hash = hashlib.md5(query.strip().lower().encode()).hexdigest()
        return f"cache:exact:{collection}:{query_hash}"

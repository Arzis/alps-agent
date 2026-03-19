"""稀疏检索器模块 - Elasticsearch BM25

基于 Elasticsearch 的稀疏检索实现，使用 BM25 算法进行关键词匹配。
与 Dense 检索互补，融合后效果显著提升。
"""

import structlog

from src.core.rag.retrieval.dense import RetrievedChunk
from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class SparseRetriever:
    """
    稀疏检索器 - Elasticsearch BM25

    优势:
    - 精确关键词匹配 (Dense 检索可能遗漏)
    - 对专有名词、编号等精确匹配效果好
    - 与 Dense 互补，融合后效果显著提升
    """

    def __init__(self, es_client: "AsyncElasticsearch"):
        """初始化稀疏检索器

        Args:
            es_client: Elasticsearch 异步客户端
        """
        self.es = es_client
        self.settings = get_settings()
        self.index_prefix = self.settings.ELASTICSEARCH_INDEX_PREFIX

    async def retrieve(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 20,
    ) -> list[RetrievedChunk]:
        """BM25 检索

        Args:
            query: 查询文本
            collection: 知识库集合名称
            top_k: 返回结果数量

        Returns:
            list[RetrievedChunk]: 检索到的文档块列表
        """
        index_name = f"{self.index_prefix}_{collection}"

        try:
            # 检查索引是否存在
            if not await self.es.indices.exists(index=index_name):
                logger.warning("es_index_not_found", index=index_name)
                return []

            # BM25 搜索
            response = await self.es.search(
                index=index_name,
                body={
                    "query": {
                        "bool": {
                            "should": [
                                # 主内容匹配 (权重最高)
                                {
                                    "match": {
                                        "content": {
                                            "query": query,
                                            "boost": 3.0,
                                        }
                                    }
                                },
                                # 关键词匹配
                                {
                                    "match": {
                                        "keywords": {
                                            "query": query,
                                            "boost": 2.0,
                                        }
                                    }
                                },
                                # 标题匹配
                                {
                                    "match": {
                                        "doc_title": {
                                            "query": query,
                                            "boost": 1.5,
                                        }
                                    }
                                },
                                # 摘要匹配
                                {
                                    "match": {
                                        "summary": {
                                            "query": query,
                                            "boost": 1.0,
                                        }
                                    }
                                },
                            ],
                            "minimum_should_match": 1,
                        }
                    },
                    "size": top_k,
                    "_source": [
                        "chunk_id", "doc_id", "content",
                        "doc_title", "chunk_index", "collection",
                    ],
                },
            )

            hits = response["hits"]["hits"]
            if not hits:
                return []

            # 归一化 BM25 分数到 0-1 范围
            max_score = response["hits"]["max_score"] or 1.0

            chunks = []
            for hit in hits:
                source = hit["_source"]
                normalized_score = hit["_score"] / max_score if max_score > 0 else 0

                chunks.append(
                    RetrievedChunk(
                        chunk_id=source.get("chunk_id", hit["_id"]),
                        doc_id=source["doc_id"],
                        content=source["content"],
                        score=normalized_score,
                        doc_title=source.get("doc_title", ""),
                        chunk_index=source.get("chunk_index", 0),
                        collection=source.get("collection", collection),
                    )
                )

            logger.info(
                "sparse_retrieval_completed",
                query=query[:100],
                collection=collection,
                num_hits=len(chunks),
                max_score=round(max_score, 3),
            )

            return chunks

        except Exception as e:
            logger.error("sparse_retrieval_failed", error=str(e), query=query[:100])
            return []


# 类型注解延迟导入
from elasticsearch import AsyncElasticsearch

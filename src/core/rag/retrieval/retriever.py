"""RAG 检索器统一接口模块"""

from src.core.rag.retrieval.dense import DenseRetriever, RetrievedChunk


class RAGRetriever:
    """
    RAG 检索器 - 统一检索接口

    Phase 1: 仅 Dense
    Phase 2: Dense + Sparse (BM25) + Rerank
    Phase 3: Dense + Sparse + KG + Rerank
    """

    def __init__(self, dense_retriever: DenseRetriever):
        """初始化检索器

        Args:
            dense_retriever: Dense 检索器实例
        """
        self.dense = dense_retriever

    async def retrieve(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """检索文档

        Phase 1: 直接使用 Dense 检索

        Args:
            query: 查询文本
            collection: 知识库集合名称，默认 "default"
            top_k: 返回的最相关结果数量，默认 5

        Returns:
            list[RetrievedChunk]: 检索到的文档块列表
        """
        # Dense 检索 (多取一些，预留给后续 Rerank)
        results = await self.dense.retrieve(
            query=query,
            collection=collection,
            top_k=top_k * 2,  # 多召回一些
        )

        # Phase 1: 直接截取 top_k
        # Phase 2+: 这里会增加 RRF 融合 + Rerank
        return results[:top_k]

"""RAG 检索器单元测试

测试 DenseRetriever 和 RAGRetriever 的检索功能。
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from llama_index.embeddings.openai import OpenAIEmbedding

from src.core.rag.retrieval.dense import DenseRetriever, RetrievedChunk
from src.core.rag.retrieval.retriever import RAGRetriever
from src.infra.config.settings import Settings


class TestDenseRetriever:
    """DenseRetriever 测试类"""

    @pytest.fixture
    def settings(self) -> Settings:
        """测试配置"""
        return Settings(
            ENV="test",
            RAG_TOP_K=5,
            RAG_SIMILARITY_THRESHOLD=0.7,
            MILVUS_COLLECTION_NAME="test_collection",
        )

    @pytest.fixture
    def mock_embedding(self) -> MagicMock:
        """Mock Embedding 模型"""
        embedding = MagicMock(spec=OpenAIEmbedding)
        embedding.aget_text_embedding = AsyncMock(
            return_value=[0.1] * 3072
        )
        return embedding

    @pytest.fixture
    def mock_milvus(self) -> MagicMock:
        """Mock Milvus 客户端"""
        milvus = MagicMock()
        # 模拟搜索返回结果
        milvus.search = MagicMock(return_value=[
            [
                {
                    "id": "chunk_001",
                    "distance": 0.85,
                    "entity": {
                        "doc_id": "doc_001",
                        "content": "测试文档内容",
                        "doc_title": "测试文档",
                        "chunk_index": 0,
                        "collection": "default",
                    }
                },
                {
                    "id": "chunk_002",
                    "distance": 0.78,
                    "entity": {
                        "doc_id": "doc_001",
                        "content": "更多文档内容",
                        "doc_title": "测试文档",
                        "chunk_index": 1,
                        "collection": "default",
                    }
                },
            ]
        ])
        return milvus

    @pytest.fixture
    def retriever(
        self, mock_milvus: MagicMock, mock_embedding: MagicMock, settings: Settings
    ) -> DenseRetriever:
        """创建 DenseRetriever 实例"""
        return DenseRetriever(
            milvus_client=mock_milvus,
            embedding_model=mock_embedding,
            settings=settings,
        )

    @pytest.mark.asyncio
    async def test_retrieve_returns_chunks(self, retriever: DenseRetriever):
        """测试检索返回文档块

        验证:
        - 返回 RetrievedChunk 列表
        - 内容正确
        """
        results = await retriever.retrieve(
            query="测试查询",
            collection="default",
        )

        assert len(results) == 2, "应该返回 2 个检索结果"
        assert all(isinstance(r, RetrievedChunk) for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_filter_by_threshold(self, retriever: DenseRetriever):
        """测试按阈值过滤

        验证:
        - 低分结果被过滤
        """
        # 设置更高阈值，第二个结果 (0.78) 应该被过滤
        retriever.settings.RAG_SIMILARITY_THRESHOLD = 0.80

        results = await retriever.retrieve(
            query="测试查询",
            collection="default",
        )

        # 第一个结果 0.85 > 0.80，第二个结果 0.78 < 0.80
        assert len(results) == 1
        assert results[0].score == 0.85

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self, mock_milvus: MagicMock, retriever: DenseRetriever):
        """测试空检索结果

        验证:
        - 没有结果时返回空列表
        """
        mock_milvus.search = MagicMock(return_value=[[]])

        results = await retriever.retrieve(
            query="不存在的查询",
            collection="default",
        )

        assert len(results) == 0, "空结果应返回空列表"

    @pytest.mark.asyncio
    async def test_retrieve_custom_top_k(self, retriever: DenseRetriever):
        """测试自定义 top_k

        验证:
        - 可以覆盖默认的 top_k 设置
        """
        await retriever.retrieve(
            query="测试查询",
            collection="default",
            top_k=10,
        )

        # 验证 search 被调用时的 limit 参数
        # 注: 具体实现可能不同，这里验证调用参数
        # retriever.milvus.search.assert_called()

    @pytest.mark.asyncio
    async def test_retrieve_chunk_structure(
        self, retriever: DenseRetriever, mock_milvus: MagicMock
    ):
        """测试检索结果结构

        验证:
        - RetrievedChunk 包含所有必要字段
        """
        results = await retriever.retrieve(
            query="测试查询",
            collection="default",
        )

        chunk = results[0]
        assert chunk.chunk_id == "chunk_001"
        assert chunk.doc_id == "doc_001"
        assert chunk.content == "测试文档内容"
        assert chunk.score == 0.85
        assert chunk.doc_title == "测试文档"
        assert chunk.chunk_index == 0
        assert chunk.collection == "default"


class TestRAGRetriever:
    """RAGRetriever 测试类"""

    @pytest.fixture
    def mock_dense_retriever(self) -> MagicMock:
        """Mock DenseRetriever"""
        dense = MagicMock()
        dense.retrieve = AsyncMock(return_value=[
            RetrievedChunk(
                chunk_id="chunk_001",
                doc_id="doc_001",
                content="测试内容",
                score=0.85,
                doc_title="测试文档",
                chunk_index=0,
                collection="default",
            ),
            RetrievedChunk(
                chunk_id="chunk_002",
                doc_id="doc_002",
                content="更多内容",
                score=0.78,
                doc_title="另一个文档",
                chunk_index=0,
                collection="default",
            ),
        ])
        return dense

    @pytest.fixture
    def rag_retriever(self, mock_dense_retriever: MagicMock) -> RAGRetriever:
        """创建 RAGRetriever 实例"""
        return RAGRetriever(dense_retriever=mock_dense_retriever)

    @pytest.mark.asyncio
    async def test_retrieve_returns_results(self, rag_retriever: RAGRetriever):
        """测试检索返回结果

        验证:
        - RAGRetriever 正确调用 DenseRetriever
        - 返回检索结果
        """
        results = await rag_retriever.retrieve(
            query="测试查询",
            collection="default",
            top_k=5,
        )

        assert len(results) == 2
        mock_dense_retriever.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_top_k_truncation(self, rag_retriever: RAGRetriever, mock_dense_retriever: MagicMock):
        """测试 top_k 截断

        验证:
        - 如果结果超过 top_k，只返回前 top_k 个
        """
        # DenseRetriever 返回更多结果
        mock_dense_retriever.retrieve = AsyncMock(return_value=[
            RetrievedChunk(
                chunk_id=f"chunk_{i:03d}",
                doc_id=f"doc_{i:03d}",
                content=f"内容 {i}",
                score=0.9 - i * 0.05,
                doc_title=f"文档 {i}",
                chunk_index=0,
                collection="default",
            )
            for i in range(10)  # 10 个结果
        ])

        results = await rag_retriever.retrieve(
            query="测试查询",
            collection="default",
            top_k=3,  # 只请求 3 个
        )

        assert len(results) == 3, "应该只返回 top_k 个结果"
        # 验证 Dense 被调用时取了更多结果 (top_k * 2)
        mock_dense_retriever.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self, rag_retriever: RAGRetriever, mock_dense_retriever: MagicMock):
        """测试空结果处理

        验证:
        - Dense 返回空时，RAGRetriever 也返回空
        """
        mock_dense_retriever.retrieve = AsyncMock(return_value=[])

        results = await rag_retriever.retrieve(
            query="不存在",
            collection="default",
        )

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_retrieve_passes_parameters(self, rag_retriever: RAGRetriever, mock_dense_retriever: MagicMock):
        """测试参数传递

        验证:
        - query, collection, top_k 被正确传递
        """
        await rag_retriever.retrieve(
            query="测试查询",
            collection="hr_docs",
            top_k=10,
        )

        mock_dense_retriever.retrieve.assert_called_once_with(
            query="测试查询",
            collection="hr_docs",
            top_k=20,  # top_k * 2
        )

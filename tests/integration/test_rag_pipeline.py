"""RAG 管道集成测试

测试文档摄取管道的完整流程。
注意: 这些测试需要运行中的 Milvus 和 PostgreSQL 服务。
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.rag.ingestion.parser import DocumentParser
from src.core.rag.ingestion.chunker import DocumentChunker
from src.core.rag.ingestion.pipeline import IngestionPipeline
from src.infra.config.settings import Settings


class TestDocumentParser:
    """DocumentParser 测试类"""

    @pytest.fixture
    def parser(self) -> DocumentParser:
        """创建解析器实例"""
        return DocumentParser()

    @pytest.fixture
    def temp_markdown_file(self) -> str:
        """创建临时 Markdown 文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("# 测试文档\n\n这是测试内容。")
            temp_path = f.name

        yield temp_path

        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_text_file(self) -> str:
        """创建临时文本文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("这是纯文本内容。\n第二行内容。")
            temp_path = f.name

        yield temp_path

        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_parse_markdown(self, parser: DocumentParser, temp_markdown_file: str):
        """测试解析 Markdown 文件

        验证:
        - Markdown 文件被正确解析
        - 返回 Document 列表
        """
        docs = await parser.parse(temp_markdown_file, ".md")

        assert len(docs) == 1
        assert "测试文档" in docs[0].text
        assert "测试内容" in docs[0].text

    @pytest.mark.asyncio
    async def test_parse_text(self, parser: DocumentParser, temp_text_file: str):
        """测试解析文本文件

        验证:
        - 文本文件被正确解析
        """
        docs = await parser.parse(temp_text_file, ".txt")

        assert len(docs) == 1
        assert "纯文本内容" in docs[0].text

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file(self, parser: DocumentParser):
        """测试解析不存在的文件

        验证:
        - 抛出 FileNotFoundError
        """
        with pytest.raises(FileNotFoundError):
            await parser.parse("/nonexistent/path/file.pdf", ".pdf")

    @pytest.mark.asyncio
    async def test_parse_unsupported_type(self, parser: DocumentParser, temp_text_file: str):
        """测试不支持的文件类型

        验证:
        - 抛出 ValueError
        """
        with pytest.raises(ValueError):
            await parser.parse(temp_text_file, ".xyz")


class TestDocumentChunker:
    """DocumentChunker 集成测试"""

    def test_chunker_with_parser_output(self, sample_documents):
        """测试分块器与解析器输出的配合

        验证:
        - 解析后的文档可以直接用于分块
        """
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        nodes = chunker.chunk(sample_documents, doc_id="test_001", collection="default")

        assert len(nodes) > 0
        assert all(n.metadata["doc_id"] == "test_001" for n in nodes)


class TestIngestionPipeline:
    """IngestionPipeline 测试类

    注意: 这些测试 mock 了外部依赖，仅测试管道逻辑。
    """

    @pytest.fixture
    def settings(self) -> Settings:
        """测试配置"""
        return Settings(
            ENV="test",
            RAG_CHUNK_SIZE=100,
            RAG_CHUNK_OVERLAP=20,
            EMBEDDING_MODEL="text-embedding-v4",
            EMBEDDING_DIMENSION=1024,
            DASHSCOPE_API_KEY="sk-test-key",
            DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1",
            MILVUS_COLLECTION_NAME="test_collection",
            MAX_EMBEDDING_CONCURRENT=5,
        )

    @pytest.fixture
    def temp_markdown_file(self) -> str:
        """创建临时 Markdown 文件"""
        content = """
# 公司年假制度

## 一、年假天数
- 工龄1-5年: 5天年假
- 工龄5-10年: 10天年假
- 工龄10年以上: 15天年假

## 二、请假流程
1. 提前3天在OA系统提交申请
2. 直属上级审批
3. HR备案
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            temp_path = f.name

        yield temp_path

        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, settings: Settings):
        """测试管道初始化

        验证:
        - 管道正确初始化各个组件
        """
        pipeline = IngestionPipeline(settings)

        assert pipeline.parser is not None
        assert pipeline.chunker is not None
        # IngestionPipeline 使用 _embedding_client，不是 embedding_model 属性

    @pytest.mark.asyncio
    async def test_pipeline_process_flow(
        self, settings: Settings, temp_markdown_file: str
    ):
        """测试管道处理流程

        验证:
        - 文档被正确解析
        - 分块正确执行
        - Embedding 被调用
        """
        pipeline = IngestionPipeline(settings)

        # Mock embedding client
        pipeline._embedding_client.embeddings.create = AsyncMock(
            return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 3072)])
        )

        # Mock Milvus
        with patch("src.core.rag.ingestion.pipeline.get_milvus") as mock_get_milvus:
            mock_milvus = MagicMock()
            mock_get_milvus.return_value = mock_milvus

            chunk_count = await pipeline.process(
                doc_id="test_doc_001",
                file_path=temp_markdown_file,
                file_type=".md",
                collection="test_collection",
            )

            assert chunk_count > 0
            # 验证 Milvus upsert 被调用
            if chunk_count > 0:
                mock_milvus.upsert.assert_called()

    @pytest.mark.asyncio
    async def test_pipeline_with_empty_file(self, settings: Settings):
        """测试处理空文件

        验证:
        - 返回 0
        """
        # 创建空文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("")
            temp_path = f.name

        try:
            pipeline = IngestionPipeline(settings)
            # Mock embedding client 返回空结果
            pipeline._embedding_client.embeddings.create = AsyncMock(
                return_value=MagicMock(data=[])
            )

            with patch("src.core.rag.ingestion.pipeline.get_milvus"):
                chunk_count = await pipeline.process(
                    doc_id="empty_doc",
                    file_path=temp_path,
                    file_type=".txt",
                    collection="default",
                )

                assert chunk_count == 0
        finally:
            os.unlink(temp_path)


class TestRetrievalPipeline:
    """检索管道集成测试"""

    @pytest.fixture
    def settings(self) -> Settings:
        """测试配置"""
        return Settings(
            ENV="test",
            RAG_TOP_K=5,
            RAG_SIMILARITY_THRESHOLD=0.7,
            MILVUS_COLLECTION_NAME="test_collection",
            EMBEDDING_MODEL="text-embedding-v4",
            EMBEDDING_DIMENSION=1024,
            DASHSCOPE_API_KEY="sk-test-key",
        )

    @pytest.mark.asyncio
    async def test_retriever_with_mock_results(
        self, settings: Settings, mock_milvus_client: MagicMock
    ):
        """测试检索器与 Mock Milvus 的配合

        验证:
        - 检索器正确处理 Milvus 返回结果
        """
        from src.core.rag.retrieval.dense import DenseRetriever

        retriever = DenseRetriever(
            milvus_client=mock_milvus_client,
            settings=settings,
        )
        # Mock embedding client
        retriever._embedding_client = MagicMock()
        retriever._embedding_client.embeddings.create = AsyncMock(
            return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 3072)])
        )

        results = await retriever.retrieve(
            query="测试查询",
            collection="default",
        )

        assert isinstance(results, list)

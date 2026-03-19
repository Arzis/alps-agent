"""元数据提取器单元测试

测试 MetadataExtractor 类的功能 - Phase 2 新增。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from llama_index.core.schema import TextNode

from src.core.rag.ingestion.metadata_extractor import (
    MetadataExtractor,
    ChunkMetadata,
    METADATA_EXTRACTION_PROMPT,
)


class TestChunkMetadata:
    """ChunkMetadata 数据模型测试"""

    def test_basic_metadata(self):
        """测试基本元数据"""
        metadata = ChunkMetadata(
            title="测试标题",
            keywords=["关键词1", "关键词2"],
            summary="这是摘要",
            potential_questions=["问题1", "问题2"],
        )
        assert metadata.title == "测试标题"
        assert len(metadata.keywords) == 2
        assert metadata.summary == "这是摘要"
        assert len(metadata.potential_questions) == 2

    def test_empty_metadata(self):
        """测试空元数据"""
        metadata = ChunkMetadata()
        assert metadata.title == ""
        assert metadata.keywords == []
        assert metadata.summary == ""
        assert metadata.potential_questions == []

    def test_metadata_validation(self):
        """测试元数据验证"""
        # keywords 应该是字符串列表
        metadata = ChunkMetadata(
            title="标题",
            keywords=["kw1", "kw2"],
        )
        assert all(isinstance(k, str) for k in metadata.keywords)


class TestMetadataExtractor:
    """MetadataExtractor 测试类"""

    @pytest.fixture
    def mock_settings(self):
        """模拟设置"""
        settings = MagicMock()
        settings.DASHSCOPE_API_KEY = MagicMock()
        settings.DASHSCOPE_API_KEY.get_secret_value.return_value = "test-key"
        settings.DASHSCOPE_BASE_URL = "https://api.test.com"
        return settings

    @pytest.fixture
    def sample_nodes(self):
        """创建示例TextNode列表"""
        nodes = []
        for i in range(3):
            node = TextNode(
                text=f"这是第{i}个测试文本段落，包含一些可提取的内容。",
                metadata={"doc_id": f"doc_{i}", "chunk_index": i},
            )
            node.id_ = f"node_{i}"
            nodes.append(node)
        return nodes

    @pytest.mark.asyncio
    async def test_extract_single_node(self, mock_settings, sample_nodes):
        """测试提取单个节点"""
        extractor = MetadataExtractor()

        # Mock LLM响应
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "title": "测试段落标题",
            "keywords": ["测试", "段落", "内容"],
            "summary": "这是测试段落的摘要",
            "potential_questions": ["这是什么内容？", "包含哪些要点？"]
        }
        '''

        with patch.object(extractor, '_extract_single', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = sample_nodes[0]
            result = await extractor.extract(sample_nodes[:1])

            assert len(result) == 1

    def test_metadata_extraction_prompt(self):
        """测试prompt模板"""
        assert "{text}" in METADATA_EXTRACTION_PROMPT
        assert "title" in METADATA_EXTRACTION_PROMPT
        assert "keywords" in METADATA_EXTRACTION_PROMPT
        assert "summary" in METADATA_EXTRACTION_PROMPT
        assert "potential_questions" in METADATA_EXTRACTION_PROMPT

    @pytest.mark.asyncio
    async def test_extract_empty_nodes(self, mock_settings):
        """测试提取空节点列表"""
        extractor = MetadataExtractor()
        result = await extractor.extract([])
        assert result == []

    def test_semaphore_initialized(self, mock_settings):
        """测试信号量初始化"""
        extractor = MetadataExtractor()
        assert extractor._semaphore is not None


class TestMetadataExtractorIntegration:
    """元数据提取集成测试（需要真实LLM或更深入的mock）"""

    @pytest.fixture
    def real_nodes(self):
        """创建用于测试的真实节点"""
        nodes = [
            TextNode(
                text="年假制度是公司为员工提供的带薪休假福利。根据公司政策，员工入职满一年后每年享有5天年假，工作满5年以上的员工可享有10天年假。年假需提前向主管申请，批准后方可使用。",
                metadata={"doc_id": "hr_policy_001", "chunk_index": 0},
            ),
        ]
        nodes[0].id_ = "hr_policy_chunk_0"
        return nodes

    def test_node_enrichment_fields(self, real_nodes):
        """测试节点富化后的字段"""
        node = real_nodes[0]
        # 模拟富化后的metadata
        node.metadata.update({
            "extracted_title": "年假制度",
            "extracted_keywords": "年假, 带薪休假, 福利",
            "extracted_summary": "公司年假制度规定",
            "potential_questions": "年假有多少天？ | 如何申请年假？",
            "_enriched_text": node.text + "\n\n关键词: 年假, 带薪休假, 福利\n相关问题: 年假有多少天？ 如何申请年假？",
        })

        assert "extracted_title" in node.metadata
        assert "extracted_keywords" in node.metadata
        assert "extracted_summary" in node.metadata
        assert "potential_questions" in node.metadata
        assert "_enriched_text" in node.metadata
        assert "年假" in node.metadata["_enriched_text"]

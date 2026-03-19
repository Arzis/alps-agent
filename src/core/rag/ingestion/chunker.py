"""文档分块模块 - Phase 2 增强版

支持:
1. 递归字符分块 (SentenceSplitter) - 通用、快速
2. 语义分块 (SemanticSplitterNodeParser) - 基于Embedding相似度自适应分块
3. 自动策略选择 - 根据文档类型和长度决定
"""

from enum import Enum
from dataclasses import dataclass
import structlog
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
)
from llama_index.core import Document
from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding

from src.infra.config.settings import Settings, get_settings

logger = structlog.get_logger()


class ChunkingStrategy(str, Enum):
    """分块策略枚举"""
    RECURSIVE = "recursive"        # 递归字符分块 (快, 通用)
    SEMANTIC = "semantic"          # 语义分块 (质量高, 较慢)
    AUTO = "auto"                  # 根据文档类型自动选择


@dataclass
class ChunkerConfig:
    """分块配置"""
    strategy: ChunkingStrategy = ChunkingStrategy.AUTO
    chunk_size: int = 512
    chunk_overlap: int = 50
    # 语义分块参数
    semantic_buffer_size: int = 1
    semantic_breakpoint_percentile: int = 95


class DocumentChunker:
    """
    文档分块器 - Phase 2 多策略版

    支持:
    1. 递归字符分块 (SentenceSplitter) - 通用、快速
    2. 语义分块 (SemanticSplitter) - 基于Embedding相似度自适应分块
    3. 自动策略选择 - 根据文档类型和长度决定
    """

    def __init__(
        self,
        config: ChunkerConfig | None = None,
        embedding_model: OpenAIEmbedding | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        """初始化分块器

        Args:
            config: 分块配置 (优先使用)
            embedding_model: Embedding模型 (用于语义分块)
            chunk_size: 每个块的最大字符数 (当config为None时使用)
            chunk_overlap: 块之间的重叠字符数 (当config为None时使用)
        """
        if config:
            self.config = config
        else:
            settings = get_settings()
            self.config = ChunkerConfig(
                chunk_size=chunk_size or settings.RAG_CHUNK_SIZE,
                chunk_overlap=chunk_overlap or settings.RAG_CHUNK_OVERLAP,
            )

        # 递归分块器 (始终初始化, 作为fallback)
        self._recursive_splitter = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            paragraph_separator="\n\n",
            secondary_chunking_regex="[。！？\\.\\!\\?]",
        )

        # 语义分块器 (需要Embedding模型)
        self._semantic_splitter = None
        self._embedding_model = embedding_model
        if embedding_model:
            try:
                self._semantic_splitter = SemanticSplitterNodeParser(
                    buffer_size=self.config.semantic_buffer_size,
                    breakpoint_percentile_threshold=self.config.semantic_breakpoint_percentile,
                    embed_model=embedding_model,
                )
                logger.info("semantic_splitter_initialized")
            except Exception as e:
                logger.warning("semantic_splitter_init_failed", error=str(e))

    def chunk(
        self,
        documents: list[Document],
        doc_id: str,
        collection: str,
        strategy: ChunkingStrategy | None = None,
    ) -> list[TextNode]:
        """将文档分块为TextNode

        Args:
            documents: 解析后的 Document 列表
            doc_id: 文档唯一标识
            collection: 知识库集合名称
            strategy: 分块策略 (None则使用配置中的策略)

        Returns:
            list[TextNode]: 分块后的节点列表
        """
        effective_strategy = strategy or self.config.strategy

        # 自动策略选择
        if effective_strategy == ChunkingStrategy.AUTO:
            effective_strategy = self._auto_select_strategy(documents)

        logger.info(
            "chunking_start",
            doc_id=doc_id,
            strategy=effective_strategy.value,
            num_documents=len(documents),
        )

        # 执行分块
        if effective_strategy == ChunkingStrategy.SEMANTIC and self._semantic_splitter:
            try:
                nodes = self._semantic_chunk(documents)
            except Exception as e:
                logger.warning(
                    "semantic_chunking_failed_fallback_to_recursive",
                    doc_id=doc_id,
                    error=str(e),
                )
                nodes = self._recursive_chunk(documents)
        else:
            nodes = self._recursive_chunk(documents)

        # 注入元数据
        for i, node in enumerate(nodes):
            node.metadata.update({
                "doc_id": doc_id,
                "chunk_index": i,
                "collection": collection,
                "total_chunks": len(nodes),
                "chunking_strategy": effective_strategy.value,
            })
            node.id_ = f"{doc_id}_chunk_{i:04d}"

        # 过滤过短的chunk
        min_length = 20
        nodes = [n for n in nodes if len(n.text.strip()) >= min_length]

        logger.info(
            "chunking_completed",
            doc_id=doc_id,
            strategy=effective_strategy.value,
            num_chunks=len(nodes),
            avg_chunk_length=sum(len(n.text) for n in nodes) // max(len(nodes), 1),
        )

        return nodes

    def _recursive_chunk(self, documents: list[Document]) -> list[TextNode]:
        """递归字符分块"""
        return self._recursive_splitter.get_nodes_from_documents(documents)

    def _semantic_chunk(self, documents: list[Document]) -> list[TextNode]:
        """语义分块"""
        return self._semantic_splitter.get_nodes_from_documents(documents)

    def _auto_select_strategy(self, documents: list[Document]) -> ChunkingStrategy:
        """自动选择分块策略

        规则:
        - 短文档 (<2000字): 递归分块 (不值得用语义分块)
        - 长文档且语义分块器可用: 语义分块
        - 其他: 递归分块
        """
        total_length = sum(len(doc.text) for doc in documents)

        if total_length < 2000:
            return ChunkingStrategy.RECURSIVE

        if self._semantic_splitter is not None:
            return ChunkingStrategy.SEMANTIC

        return ChunkingStrategy.RECURSIVE

    @property
    def supports_semantic(self) -> bool:
        """是否支持语义分块"""
        return self._semantic_splitter is not None

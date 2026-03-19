"""文档分块模块

使用递归字符分块器将文档分割成小块，保持语义完整性。
"""

import structlog
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document
from llama_index.core.schema import TextNode

logger = structlog.get_logger()


class DocumentChunker:
    """
    文档分块器

    Phase 1: 递归字符分块 (SentenceSplitter)
    Phase 2: 语义分块 (SemanticSplitterNodeParser)

    使用 SentenceSplitter 进行递归字符分块，支持中英文句子边界识别。
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """初始化分块器

        Args:
            chunk_size: 每个块的最大字符数，默认 512
            chunk_overlap: 块之间的重叠字符数，默认 50
        """
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,  # 每个块的最大字符数
            chunk_overlap=chunk_overlap,  # 块之间的重叠
            paragraph_separator="\n\n",  # 段落分隔符
            secondary_chunking_regex="[。！？\\.\\!\\?]",  # 中英文句子边界
        )

    def chunk(
        self,
        documents: list[Document],
        doc_id: str,
        collection: str,
    ) -> list[TextNode]:
        """将文档分块为 TextNode

        Args:
            documents: 解析后的 Document 列表
            doc_id: 文档唯一标识
            collection: 知识库集合名称

        Returns:
            list[TextNode]: 分块后的节点列表
        """
        # 使用 SentenceSplitter 进行分块
        nodes = self.splitter.get_nodes_from_documents(documents)

        # 注入元数据
        for i, node in enumerate(nodes):
            node.metadata.update({
                "doc_id": doc_id,  # 文档ID
                "chunk_index": i,  # 块索引
                "collection": collection,  # 集合名称
                "total_chunks": len(nodes),  # 总块数
            })
            # 设置 node ID (用于 Milvus 主键)
            node.id_ = f"{doc_id}_chunk_{i:04d}"

        logger.info(
            "document_chunked",
            doc_id=doc_id,
            num_chunks=len(nodes),
            avg_chunk_size=sum(len(n.text) for n in nodes) // max(len(nodes), 1),
        )

        return nodes

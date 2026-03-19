"""引用溯源提取器模块

从 LLM 回答中识别引用标记 [来源X]，映射到具体的文档和段落。
"""

import re

import structlog

from src.core.rag.retrieval.dense import RetrievedChunk
from src.schemas.chat import CitationItem

logger = structlog.get_logger()


class CitationExtractor:
    """
    引用溯源提取器

    功能:
    1. 从 LLM 输出中识别引用标记 [来源X]
    2. 映射到具体的文档和段落
    3. 生成结构化的引用信息
    """

    def extract_citations(
        self,
        answer: str,
        chunks: list[RetrievedChunk],
    ) -> tuple[str, list[CitationItem]]:
        """从回答中提取引用，并生成引用列表

        Args:
            answer: LLM 生成的回答文本
            chunks: 检索到的文档块列表

        Returns:
            tuple[str, list[CitationItem]]: (处理后的回答, 引用列表)
        """
        citations = []
        used_sources = set()

        # 提取 [来源X] 模式的引用
        pattern = r"\[来源(\d+)\]"
        matches = re.findall(pattern, answer)

        for match in matches:
            source_idx = int(match) - 1  # 转为 0-based
            if 0 <= source_idx < len(chunks) and source_idx not in used_sources:
                chunk = chunks[source_idx]
                citations.append(
                    CitationItem(
                        doc_id=chunk.doc_id,
                        doc_title=chunk.doc_title,
                        chunk_index=chunk.chunk_index,
                        content_preview=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    )
                )
                used_sources.add(source_idx)

        # 按出现顺序排序
        citations.sort(key=lambda x: used_sources.get(list(chunks).index(
            next(c for c in chunks if c.doc_id == x.doc_id and c.chunk_index == x.chunk_index)
        ), 0))

        logger.info(
            "citations_extracted",
            answer_length=len(answer),
            citation_count=len(citations),
        )

        return answer, citations

    def format_citations_for_display(
        self,
        citations: list[CitationItem],
    ) -> str:
        """格式化引用列表用于显示

        Args:
            citations: 引用列表

        Returns:
            str: 格式化后的引用字符串
        """
        if not citations:
            return ""

        lines = ["\n\n--- 引用来源 ---"]
        for i, cite in enumerate(citations, start=1):
            lines.append(f"[{i}] {cite.doc_title}")
            if cite.content_preview:
                lines.append(f"    {cite.content_preview[:100]}...")

        return "\n".join(lines)

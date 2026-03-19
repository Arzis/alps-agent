"""LLM元数据提取模块

为每个chunk提取:
- 主题标题 (extracted_title)
- 关键词 (extracted_keywords)
- 摘要 (extracted_summary)
- 可回答的问题 (potential_questions)
"""

import asyncio
import structlog
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from llama_index.core.schema import TextNode

from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class ChunkMetadata(BaseModel):
    """从文本块中提取的结构化元数据"""
    title: str = Field(default="", description="该段落的主题/标题")
    keywords: list[str] = Field(default_factory=list, description="3-5个关键词")
    summary: str = Field(default="", description="一句话摘要")
    potential_questions: list[str] = Field(
        default_factory=list,
        description="这段文本可以回答的2-3个问题",
    )


METADATA_EXTRACTION_PROMPT = """分析以下文本段落，提取结构化元数据。

文本:
---
{text}
---

请提取:
1. title: 这段文本的主题/标题 (10字以内)
2. keywords: 3-5个关键词
3. summary: 一句话摘要 (30字以内)
4. potential_questions: 这段文本可以回答的2-3个问题

以JSON格式输出。"""


class MetadataExtractor:
    """
    LLM元数据提取器

    为每个chunk提取:
    - 主题标题
    - 关键词
    - 摘要
    - 可回答的问题 (用于HyDE-like增强检索)

    注意: 这是一个可选步骤, 会增加摄取时间和LLM成本
    但显著提升检索质量
    """

    def __init__(self, llm: ChatOpenAI | None = None, batch_size: int = 5):
        """初始化元数据提取器

        Args:
            llm: LLM客户端 (默认使用gpt-4o-mini以控制成本)
            batch_size: 批处理大小 (当前未使用，保留接口)
        """
        settings = get_settings()
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",  # 用轻量模型降低成本
            temperature=0.0,
            api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
            base_url=settings.DASHSCOPE_BASE_URL,
            timeout=30,
        )
        self.batch_size = batch_size
        # 并发控制信号量
        self._semaphore = asyncio.Semaphore(10)

    async def extract(self, nodes: list[TextNode]) -> list[TextNode]:
        """为所有节点提取元数据

        Args:
            nodes: TextNode列表

        Returns:
            list[TextNode]: 增强后的节点列表
        """
        logger.info("metadata_extraction_start", num_nodes=len(nodes))

        if not nodes:
            return nodes

        # 批量并行处理
        tasks = [self._extract_single(node) for node in nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        enriched_nodes = []
        for node, result in zip(nodes, results):
            if isinstance(result, Exception):
                logger.warning(
                    "metadata_extraction_failed",
                    node_id=node.id_,
                    error=str(result),
                )
                enriched_nodes.append(node)  # 使用未增强的原始节点
            else:
                enriched_nodes.append(result)

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(
            "metadata_extraction_completed",
            total=len(nodes),
            success=success_count,
            failed=len(nodes) - success_count,
        )

        return enriched_nodes

    async def _extract_single(self, node: TextNode) -> TextNode:
        """提取单个节点的元数据

        Args:
            node: TextNode

        Returns:
            TextNode: 增强后的节点
        """
        async with self._semaphore:
            text = node.text[:2000]  # 限制长度, 控制token消耗

            try:
                response = await self.llm.ainvoke(
                    [
                        SystemMessage(content="你是一个文本分析专家。请分析文本并提取结构化元数据。"),
                        HumanMessage(content=METADATA_EXTRACTION_PROMPT.format(text=text)),
                    ],
                    response_format={"type": "json_object"},
                )

                metadata = ChunkMetadata.model_validate_json(response.content)

                # 将提取的元数据注入节点
                node.metadata.update({
                    "extracted_title": metadata.title,
                    "extracted_keywords": ", ".join(metadata.keywords),
                    "extracted_summary": metadata.summary,
                    "potential_questions": " | ".join(metadata.potential_questions),
                })

                # 将关键词和问题也追加到文本中, 增强检索效果
                # (这是一种常用的元数据增强trick)
                node.metadata["_enriched_text"] = (
                    f"{node.text}\n\n"
                    f"关键词: {', '.join(metadata.keywords)}\n"
                    f"相关问题: {' '.join(metadata.potential_questions)}"
                )

                logger.debug(
                    "metadata_extracted",
                    node_id=node.id_,
                    title=metadata.title,
                    keywords_count=len(metadata.keywords),
                )

                return node

            except Exception as e:
                logger.error(
                    "metadata_extraction_single_failed",
                    node_id=node.id_,
                    error=str(e),
                )
                raise

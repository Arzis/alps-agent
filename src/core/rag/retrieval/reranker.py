"""重排器模块 - Cross-Encoder & LLM Reranker

使用 Cross-Encoder 或 LLM 对检索结果进行精排，提升相关性排序质量。
"""

import asyncio
from abc import ABC, abstractmethod

import structlog

from src.core.rag.retrieval.dense import RetrievedChunk

logger = structlog.get_logger()


class BaseReranker(ABC):
    """重排器基类"""

    @abstractmethod
    async def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_n: int = 5
    ) -> list[RetrievedChunk]:
        """对检索结果进行重排

        Args:
            query: 查询文本
            chunks: 候选文档块列表
            top_n: 返回的重排结果数量

        Returns:
            list[RetrievedChunk]: 重排后的文档块列表
        """
        ...


class CrossEncoderReranker(BaseReranker):
    """
    Cross-Encoder 重排器

    使用 BAAI/bge-reranker-v2-m3 模型对 query-document 对进行精排。
    比 Bi-Encoder (Dense) 更精确，但速度较慢。
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        """初始化 Cross-Encoder 重排器

        Args:
            model_name: 模型名称，默认使用 BAAI/bge-reranker-v2-m3
        """
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name, max_length=512)
            logger.info("cross_encoder_reranker_loaded", model=model_name)
        except ImportError:
            logger.warning("sentence_transformers_not_installed")
            self.model = None

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_n: int = 5,
    ) -> list[RetrievedChunk]:
        """使用 Cross-Encoder 精排

        Args:
            query: 查询文本
            chunks: 候选文档块列表
            top_n: 返回的重排结果数量

        Returns:
            list[RetrievedChunk]: 重排后的文档块列表
        """
        if not chunks:
            return []

        if self.model is None:
            logger.warning("cross_encoder_model_not_available_returning_original")
            return chunks[:top_n]

        pairs = [(query, chunk.content) for chunk in chunks]

        # Cross-Encoder 推理 (CPU/GPU 密集，放到线程池)
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            lambda: self.model.predict(pairs).tolist(),
        )

        # 用 Rerank 分数替换原始分数，排序
        scored = []
        for chunk, score in zip(chunks, scores):
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    content=chunk.content,
                    score=float(score),
                    doc_title=chunk.doc_title,
                    chunk_index=chunk.chunk_index,
                    collection=chunk.collection,
                )
            )

        scored.sort(key=lambda x: x.score, reverse=True)

        logger.info(
            "cross_encoder_rerank_completed",
            input_count=len(chunks),
            output_count=min(top_n, len(scored)),
            top_score=round(scored[0].score, 4) if scored else 0,
            bottom_score=round(scored[-1].score, 4) if scored else 0,
        )

        return scored[:top_n]


class LLMReranker(BaseReranker):
    """
    LLM Reranker (备选方案)

    使用 LLM 对检索结果打分排序。
    优点: 无需额外模型部署
    缺点: 成本高，延迟高
    """

    def __init__(self, llm=None):
        """初始化 LLM 重排器

        Args:
            llm: LLM 实例，默认使用 FALLBACK_LLM_MODEL
        """
        try:
            from langchain_openai import ChatOpenAI
            from src.infra.config.settings import get_settings

            settings = get_settings()
            self.llm = llm or ChatOpenAI(
                model=settings.FALLBACK_LLM_MODEL,
                temperature=0.0,
                api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
                base_url=settings.DASHSCOPE_BASE_URL,
            )
        except ImportError:
            logger.warning("langchain_openai_not_installed")
            self.llm = None

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_n: int = 5,
    ) -> list[RetrievedChunk]:
        """LLM 打分重排

        Args:
            query: 查询文本
            chunks: 候选文档块列表
            top_n: 返回的重排结果数量

        Returns:
            list[RetrievedChunk]: 重排后的文档块列表
        """
        if not chunks:
            return []

        if self.llm is None:
            logger.warning("llm_not_available_returning_original")
            return chunks[:top_n]

        from langchain_core.messages import HumanMessage

        # 构建文档列表
        doc_list = "\n".join(
            f"[文档{i+1}]: {chunk.content[:300]}"
            for i, chunk in enumerate(chunks)
        )

        prompt = f"""你是一个文档相关性评估专家。给定一个查询和多个候选文档，
请对每个文档与查询的相关性打分(0-10分)。

查询: {query}

候选文档:
{doc_list}

请返回JSON格式: {{"scores": [分数1, 分数2, ...]}}
分数越高表示越相关。"""

        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content=prompt)],
            )

            import json
            result = json.loads(response.content)
            scores = result.get("scores", [0] * len(chunks))

            scored = []
            for chunk, score in zip(chunks, scores):
                scored.append(
                    RetrievedChunk(
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        content=chunk.content,
                        score=float(score) / 10.0,
                        doc_title=chunk.doc_title,
                        chunk_index=chunk.chunk_index,
                        collection=chunk.collection,
                    )
                )

            scored.sort(key=lambda x: x.score, reverse=True)
            return scored[:top_n]

        except Exception as e:
            logger.error("llm_rerank_failed", error=str(e))
            return chunks[:top_n]

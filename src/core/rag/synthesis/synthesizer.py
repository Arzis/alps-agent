"""答案合成模块

基于检索到的上下文，使用 LLM 生成回答。
"""

from dataclasses import dataclass
from typing import Any

import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.core.rag.retrieval.dense import RetrievedChunk
from src.schemas.chat import CitationItem
from src.infra.config.settings import Settings

logger = structlog.get_logger()

# === Prompt 模板 ===

RAG_SYSTEM_PROMPT = """你是一个企业智能问答助手。请根据提供的参考资料回答用户的问题。

规则:
1. 只根据参考资料中的信息回答，不要编造信息
2. 如果参考资料中没有相关信息，请明确说"根据现有资料，我无法找到相关信息"
3. 回答时标注引用来源，使用 [来源X] 的格式
4. 回答要简洁、准确、专业
5. 如果问题不清晰，可以请求用户澄清

参考资料:
{context}
"""

RAG_USER_PROMPT = """用户问题: {question}

请根据参考资料回答上述问题。"""


@dataclass
class SynthesisResult:
    """合成结果"""
    answer: str  # 生成的回答
    citations: list[CitationItem]  # 引用的文档片段
    model_used: str  # 使用的模型
    tokens_used: int  # 消耗的 token 数
    is_fallback: bool = False  # 是否使用了降级模型


class AnswerSynthesizer:
    """答案合成器 - 基于检索到的上下文生成回答"""

    def __init__(self, settings: Settings):
        """初始化答案合成器

        Args:
            settings: 应用配置
        """
        self.settings = settings

        # 主力模型 (用于 RAG 回答)
        self.primary_llm = ChatOpenAI(
            model=settings.PRIMARY_LLM_MODEL,
            temperature=settings.PRIMARY_LLM_TEMPERATURE,
            max_tokens=settings.PRIMARY_LLM_MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
            timeout=settings.LLM_TIMEOUT,
        )

        # 降级模型 (用于 Codex 降级回答)
        self.fallback_llm = ChatOpenAI(
            model=settings.FALLBACK_LLM_MODEL,
            temperature=settings.FALLBACK_LLM_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
            timeout=settings.LLM_TIMEOUT,
        )

    async def synthesize(
        self,
        query: str,
        retrieved_chunks: list[RetrievedChunk],
        conversation_history: list[dict] | None = None,
    ) -> SynthesisResult:
        """基于检索结果合成答案

        Args:
            query: 用户问题
            retrieved_chunks: 检索到的文档块列表
            conversation_history: 对话历史 (可选)

        Returns:
            SynthesisResult: 合成结果
        """
        # 构建上下文
        context = self._build_context(retrieved_chunks)

        # 构建消息
        messages = []

        # System prompt
        messages.append(
            SystemMessage(content=RAG_SYSTEM_PROMPT.format(context=context))
        )

        # 历史对话 (多轮上下文)
        if conversation_history:
            for msg in conversation_history[-6:]:  # 最近 3 轮
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

        # 当前问题
        messages.append(
            HumanMessage(content=RAG_USER_PROMPT.format(question=query))
        )

        # 调用 LLM
        try:
            response = await self.primary_llm.ainvoke(messages)
            model_used = self.settings.PRIMARY_LLM_MODEL
        except Exception as e:
            logger.error("primary_llm_failed", error=str(e))
            raise

        # 提取引用
        citations = self._extract_citations(retrieved_chunks)

        # 估算 token 使用
        tokens_used = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

        return SynthesisResult(
            answer=response.content,
            citations=citations,
            model_used=model_used,
            tokens_used=tokens_used,
        )

    async def synthesize_with_codex(
        self,
        query: str,
        conversation_history: list[dict] | None = None,
    ) -> SynthesisResult:
        """Codex 降级回答 (不使用 RAG 上下文)

        当 RAG 检索结果不好时使用此方法。

        Args:
            query: 用户问题
            conversation_history: 对话历史 (可选)

        Returns:
            SynthesisResult: 合成结果
        """
        messages = [
            SystemMessage(
                content="你是一个企业智能问答助手。请根据你的知识回答用户的问题。"
                        "如果不确定，请明确说明。"
            ),
        ]

        # 历史对话
        if conversation_history:
            for msg in conversation_history[-6:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=query))

        # 调用降级模型
        response = await self.fallback_llm.ainvoke(messages)
        tokens_used = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

        return SynthesisResult(
            answer=response.content,
            citations=[],
            model_used=self.settings.FALLBACK_LLM_MODEL,
            tokens_used=tokens_used,
            is_fallback=True,
        )

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        """构建参考资料文本

        Args:
            chunks: 检索到的文档块列表

        Returns:
            str: 格式化的上下文文本
        """
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[来源{i}] (文档: {chunk.doc_title}, 相关度: {chunk.score:.2f})\n"
                f"{chunk.content}\n"
            )
        return "\n---\n".join(context_parts)

    def _extract_citations(self, chunks: list[RetrievedChunk]) -> list[CitationItem]:
        """提取引用信息

        Args:
            chunks: 检索到的文档块列表

        Returns:
            list[CitationItem]: 引用列表
        """
        return [
            CitationItem(
                doc_id=chunk.doc_id,
                doc_title=chunk.doc_title,
                content=chunk.content[:200],  # 截取前 200 字符
                chunk_index=chunk.chunk_index,
                relevance_score=chunk.score,
            )
            for chunk in chunks
        ]

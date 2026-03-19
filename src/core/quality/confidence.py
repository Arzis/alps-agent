"""置信度评估模块

使用 LLM 评估 RAG 回答的质量，从多个维度打分。
"""

import structlog
from pydantic import BaseModel, Field

from src.infra.config.settings import get_settings

logger = structlog.get_logger()

# === Prompt 模板 ===

CONFIDENCE_PROMPT = """你是一个回答质量评估专家。请评估以下问答对的质量。

## 用户问题
{question}

## 参考上下文 (检索到的文档)
{context}

## 生成的回答
{answer}

## 评估维度

1. **faithfulness** (忠实度, 0-1): 回答的内容是否完全基于参考上下文?
   - 1.0: 完全基于上下文, 没有编造
   - 0.5: 部分基于上下文, 有些推断
   - 0.0: 完全编造, 与上下文无关

2. **relevancy** (相关性, 0-1): 回答是否切题? 是否直接回答了用户问题?
   - 1.0: 完全切题
   - 0.5: 部分相关
   - 0.0: 完全偏题

3. **completeness** (完整性, 0-1): 回答是否覆盖了问题的所有方面?
   - 1.0: 全面完整
   - 0.5: 回答了主要部分
   - 0.0: 严重遗漏

4. **overall** (综合评分, 0-1): 综合考虑以上因素的整体质量分

请以JSON格式输出评估结果。"""


class ConfidenceAssessment(BaseModel):
    """置信度评估结果"""
    faithfulness: float = Field(ge=0, le=1, description="忠实度: 回答是否基于提供的上下文")
    relevancy: float = Field(ge=0, le=1, description="相关性: 回答是否切题")
    completeness: float = Field(ge=0, le=1, description="完整性: 回答是否覆盖问题的各方面")
    overall: float = Field(ge=0, le=1, description="综合置信度评分")
    reasoning: str = Field(default="", description="评估推理过程")


class ConfidenceEvaluator:
    """
    LLM-based 置信度评估器

    使用 LLM 评估 RAG 回答的质量, 从多个维度打分:
    - faithfulness: 忠实度 (是否基于上下文)
    - relevancy: 相关性 (是否切题)
    - completeness: 完整性 (是否全面)

    综合评分用于:
    - 决定是否降级到 Codex
    - 决定是否需要人工审查 (Phase 3)
    - 缓存决策 (只缓存高质量回答)
    """

    def __init__(self, llm=None):
        """初始化置信度评估器

        Args:
            llm: 可选的 LLM 实例，默认使用 gpt-4o-mini
        """
        settings = get_settings()
        if llm is None:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",  # 用轻量模型, 降低成本
                temperature=0.0,
                api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
                base_url=settings.DASHSCOPE_BASE_URL,
                timeout=30,
            )
        else:
            self.llm = llm

    async def evaluate(
        self,
        question: str,
        answer: str,
        contexts: list[str],
    ) -> ConfidenceAssessment:
        """评估回答质量

        Args:
            question: 用户问题
            answer: 生成的回答
            contexts: 参考上下文列表

        Returns:
            ConfidenceAssessment: 置信度评估结果
        """
        context_text = "\n---\n".join(contexts) if contexts else "(无参考上下文)"

        try:
            from langchain_core.messages import SystemMessage, HumanMessage

            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="你是一个严格的回答质量评估专家。"),
                    HumanMessage(
                        content=CONFIDENCE_PROMPT.format(
                            question=question,
                            context=context_text[:3000],  # 限制长度
                            answer=answer[:2000],
                        )
                    ),
                ],
            )

            import json
            result_data = json.loads(response.content)
            assessment = ConfidenceAssessment(**result_data)

            logger.info(
                "confidence_evaluated",
                faithfulness=assessment.faithfulness,
                relevancy=assessment.relevancy,
                completeness=assessment.completeness,
                overall=assessment.overall,
            )

            return assessment

        except Exception as e:
            logger.error("confidence_evaluation_failed", error=str(e))
            # 降级: 基于检索分数的简单评估
            return self._fallback_assessment(contexts)

    def _fallback_assessment(self, contexts: list[str]) -> ConfidenceAssessment:
        """降级评估: 无法调用 LLM 时使用

        Args:
            contexts: 参考上下文列表

        Returns:
            ConfidenceAssessment: 默认评估结果
        """
        if not contexts:
            return ConfidenceAssessment(
                faithfulness=0.0, relevancy=0.0,
                completeness=0.0, overall=0.0,
                reasoning="No context available, fallback assessment",
            )
        return ConfidenceAssessment(
            faithfulness=0.5, relevancy=0.5,
            completeness=0.5, overall=0.5,
            reasoning="LLM evaluation failed, using fallback",
        )

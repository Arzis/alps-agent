"""幻觉检测模块

检测 LLM 回答中是否包含不被参考资料支持的虚假信息。
"""

import structlog
from pydantic import BaseModel, Field

from src.infra.config.settings import get_settings

logger = structlog.get_logger()

# === Prompt 模板 ===

HALLUCINATION_PROMPT = """你是一个幻觉检测专家。请检查以下回答是否包含"幻觉"(即不被参考资料支持的虚假信息)。

## 参考资料
{context}

## 待检查的回答
{answer}

## 任务
1. 将回答拆分为独立的事实声明
2. 逐一检查每个声明是否被参考资料支持
3. 标记不被支持的声明为"幻觉"

输出JSON:
- has_hallucination: 是否存在幻觉
- hallucination_score: 幻觉程度 (0-1, 幻觉声明数/总声明数)
- hallucinated_claims: 被判定为幻觉的声明列表
- reasoning: 检测推理过程"""


class HallucinationResult(BaseModel):
    """幻觉检测结果"""
    has_hallucination: bool = Field(description="是否存在幻觉")
    hallucination_score: float = Field(ge=0, le=1, description="幻觉程度 0=无幻觉, 1=完全幻觉")
    hallucinated_claims: list[str] = Field(
        default_factory=list,
        description="被判定为幻觉的声明列表",
    )
    reasoning: str = ""


class HallucinationDetector:
    """
    幻觉检测器

    检测 LLM 回答中是否包含不被参考资料支持的虚假信息
    """

    def __init__(self, llm=None):
        """初始化幻觉检测器

        Args:
            llm: 可选的 LLM 实例，默认使用 gpt-4o-mini
        """
        settings = get_settings()
        if llm is None:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
                base_url=settings.DASHSCOPE_BASE_URL,
                timeout=30,
            )
        else:
            self.llm = llm

    async def detect(
        self, answer: str, contexts: list[str]
    ) -> HallucinationResult:
        """检测幻觉

        Args:
            answer: 待检查的回答
            contexts: 参考上下文列表

        Returns:
            HallucinationResult: 幻觉检测结果
        """
        if not contexts:
            return HallucinationResult(
                has_hallucination=True,
                hallucination_score=1.0,
                reasoning="No reference context provided",
            )

        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            import json

            context_text = "\n---\n".join(contexts)

            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="你是一个严格的幻觉检测专家。"),
                    HumanMessage(
                        content=HALLUCINATION_PROMPT.format(
                            context=context_text[:3000],
                            answer=answer[:2000],
                        )
                    ),
                ],
            )

            result = HallucinationResult(**json.loads(response.content))

            logger.info(
                "hallucination_detected",
                has_hallucination=result.has_hallucination,
                score=result.hallucination_score,
                num_claims=len(result.hallucinated_claims),
            )

            return result

        except Exception as e:
            logger.error("hallucination_detection_failed", error=str(e))
            return HallucinationResult(
                has_hallucination=False,
                hallucination_score=0.3,
                reasoning=f"Detection failed: {str(e)}",
            )

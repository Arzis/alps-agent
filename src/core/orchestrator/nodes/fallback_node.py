"""降级兜底节点模块

当 RAG 检索结果质量不足时，使用轻量级 LLM 直接回答。
"""

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging
from openai import RateLimitError, APITimeoutError, APIError

import structlog

from src.core.orchestrator.state import ConversationState
from src.infra.config.settings import Settings

logger = structlog.get_logger()

# === Prompt 模板 ===

FALLBACK_SYSTEM_PROMPT = """你是一个企业智能问答助手。请根据你的知识回答用户的问题。

规则：
1. 回答要简洁、准确、专业
2. 如果不确定，请明确说明
3. 可以结合通用知识回答
4. 不要编造具体数据或内部信息"""

FALLBACK_USER_PROMPT = """用户问题: {question}

请回答上述问题。"""


class FallbackNode:
    """
    降级兜底节点

    职责：
    1. 当 RAG 检索结果不足时提供兜底回答
    2. 使用轻量级 LLM 模型直接回答
    3. 不依赖 RAG 检索结果

    设计考虑：
    - 使用 FALLBACK_LLM_MODEL 降级模型降低成本
    - 不返回引用信息，因为没有检索来源
    - 设置较低的置信度，标记为 fallback
    """

    def __init__(self, settings: Settings):
        """初始化降级节点

        Args:
            settings: 应用配置
        """
        self.settings = settings
        self.fallback_llm = ChatOpenAI(
            model=settings.FALLBACK_LLM_MODEL,
            temperature=settings.FALLBACK_LLM_TEMPERATURE,
            api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
            base_url=settings.DASHSCOPE_BASE_URL,
            timeout=settings.LLM_TIMEOUT,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError, OSError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def execute(self, state: ConversationState) -> ConversationState:
        """执行降级回答

        Args:
            state: 当前对话状态

        Returns:
            ConversationState: 更新后的状态
        """
        user_message = state.user_message
        history = state.history_turns

        logger.info(
            "fallback_start",
            session_id=state.session_id,
            message_length=len(user_message),
            reason="rag_no_results" if not state.retrieved_chunks else "low_confidence",
        )

        # 构建消息
        messages = [
            SystemMessage(content=FALLBACK_SYSTEM_PROMPT),
        ]

        # 添加对话历史 (最近 3 轮)
        if history:
            for msg in history[-6:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                else:
                    messages.append(
                        SystemMessage(content=msg["content"])
                    )

        # 添加当前问题
        messages.append(
            HumanMessage(content=FALLBACK_USER_PROMPT.format(question=user_message))
        )

        # 调用降级模型
        response = await self.fallback_llm.ainvoke(messages)

        # 更新状态
        state.rag_answer = response.content
        state.confidence = 0.3  # 降级模式设置较低置信度
        state.model_used = self.settings.FALLBACK_LLM_MODEL
        state.fallback_used = True
        state.citations = []  # 降级回答没有引用
        state.tokens_used = (
            response.usage_metadata.get("total_tokens", 0)
            if response.usage_metadata
            else 0
        )

        logger.info(
            "fallback_completed",
            session_id=state.session_id,
            answer_length=len(response.content),
            tokens_used=state.tokens_used,
        )

        return state

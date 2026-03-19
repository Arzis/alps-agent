"""查询理解节点模块

负责理解用户查询，包括意图识别和查询改写。
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

INTENT_SYSTEM_PROMPT = """你是一个企业智能问答助手的意图识别器。

请分析用户问题，判断其意图类型：

1. knowledge: 用户想要从知识库中查找信息/知识
2. general: 用户进行一般性对话或问候
3. search: 用户想要搜索特定内容

只返回一个词：knowledge、general 或 search。"""


QUERY_REWRITE_SYSTEM_PROMPT = """你是一个企业智能问答助手的查询改写专家。

请将用户的问题改写为更适合检索的查询语句。

规则：
1. 保持原意，去除口语化表达
2. 提取关键概念和实体
3. 可以适当扩展同义词
4. 如果原问题已经清晰，直接返回原问题

只返回改写后的查询语句，不要包含其他内容。"""


class QueryUnderstandingNode:
    """
    查询理解节点

    职责：
    1. 意图识别 - 判断用户是想知识问答还是闲聊
    2. 查询改写 - 将用户问题改写为更适合 RAG 检索的形式
    """

    def __init__(self, settings: Settings):
        """初始化查询理解节点

        Args:
            settings: 应用配置
        """
        self.settings = settings
        self.llm = ChatOpenAI(
            model=settings.PRIMARY_LLM_MODEL,
            temperature=0.0,  # 意图识别不需要创造性
            api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
            base_url=settings.DASHSCOPE_BASE_URL,
            timeout=settings.LLM_TIMEOUT,
        )

    async def execute(self, state: ConversationState) -> ConversationState:
        """执行查询理解

        Args:
            state: 当前对话状态

        Returns:
            ConversationState: 更新后的状态
        """
        user_message = state.user_message

        logger.info(
            "query_understanding_start",
            session_id=state.session_id,
            message_length=len(user_message),
        )

        # 1. 意图识别
        intent = await self._detect_intent(user_message)
        state.intent = intent

        logger.info(
            "intent_detected",
            session_id=state.session_id,
            intent=intent,
        )

        # 2. 查询改写
        rewritten_query = await self._rewrite_query(user_message)
        state.rewritten_query = rewritten_query

        logger.info(
            "query_rewritten",
            session_id=state.session_id,
            original=user_message[:50],
            rewritten=rewritten_query[:50],
        )

        return state

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError, OSError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _detect_intent(self, query: str) -> str:
        """识别用户意图

        Args:
            query: 用户查询

        Returns:
            str: 意图类型 (knowledge/general/search)
        """
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=INTENT_SYSTEM_PROMPT),
                HumanMessage(content=query),
            ])

            intent = response.content.strip().lower()

            # 确保返回有效值
            if intent not in ("knowledge", "general", "search"):
                intent = "knowledge"

            return intent

        except Exception as e:
            logger.error("intent_detection_failed", error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError, OSError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _rewrite_query(self, query: str) -> str:
        """改写用户查询

        Args:
            query: 原始查询

        Returns:
            str: 改写后的查询
        """
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=QUERY_REWRITE_SYSTEM_PROMPT),
                HumanMessage(content=query),
            ])

            rewritten = response.content.strip()

            # 如果改写失败，使用原查询
            if not rewritten:
                return query

            return rewritten

        except Exception as e:
            logger.error("query_rewrite_failed", error=str(e))
            raise

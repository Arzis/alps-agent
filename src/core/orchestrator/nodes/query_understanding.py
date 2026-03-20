"""查询理解节点模块

Phase 2 增强版：
- 多轮指代消解
- 查询改写
- 查询扩展（用于多路召回）
"""

import json
import structlog
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging
from openai import RateLimitError, APITimeoutError, APIError

from src.core.orchestrator.state import ConversationState
from src.infra.config.settings import Settings

logger = structlog.get_logger()

# === 结构化输出模型 ===

class QueryUnderstandingOutput(BaseModel):
    """查询理解结果 - Phase 2 增强版"""
    rewritten_query: str = Field(description="改写后的独立完整查询，消除指代歧义")
    expanded_queries: list[str] = Field(
        default_factory=list,
        description="2-3个扩展查询,从不同角度表述同一问题,用于多路召回",
    )
    intent: str = Field(
        description="意图分类: knowledge_qa / chitchat / unclear",
        default="knowledge_qa",
    )
    reasoning: str = Field(description="查询改写推理过程", default="")


QUERY_UNDERSTANDING_PROMPT = """你是一个企业智能问答助手的查询理解专家。

你的任务是分析用户的当前问题，结合对话历史，生成改写后的查询。

## 任务说明

1. **指代消解**: 如果用户的问题包含代词或省略，需要根据对话历史补全。
   - 例: 历史中提到"年假制度"，用户说"它有什么限制？" → 改写为"年假制度有什么限制？"

2. **查询改写**: 将口语化/模糊的问题改写为清晰、适合检索的查询。
   - 例: "假期咋算的" → "公司员工假期天数如何计算？"

3. **查询扩展**: 生成2-3个语义相同但表述不同的查询，用于多路召回。
   - 例: "年假制度" → ["员工年假政策", "公司带薪休假规定", "年度假期天数标准"]

4. **意图识别**:
   - knowledge_qa: 需要查询知识库的问题
   - chitchat: 闲聊/寒暄，不需要知识检索
   - unclear: 问题不清晰，需要追问

## 对话历史
{conversation_history}

## 当前用户问题
{current_query}

请以JSON格式输出结果。"""


class QueryUnderstandingNode:
    """
    查询理解节点 - Phase 2 增强版

    职责：
    1. 多轮指代消解 - 结合对话历史消除代词/省略的歧义
    2. 查询改写 - 将口语化问题改写为适合检索的形式
    3. 查询扩展 - 生成多个扩展查询用于多路召回
    4. 意图识别 - 判断问题类型
    """

    def __init__(self, settings: Settings):
        """初始化查询理解节点

        Args:
            settings: 应用配置
        """
        self.settings = settings
        self.llm = ChatOpenAI(
            model=settings.FALLBACK_LLM_MODEL,
            temperature=0.0,
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
        original_query = state.user_message
        messages = state.history_turns

        logger.info(
            "query_understanding_start",
            session_id=state.session_id,
            message_length=len(original_query),
            history_turns=len(messages),
        )

        # 如果是第一轮对话且问题足够清晰, 跳过LLM改写
        if len(messages) <= 1 and len(original_query) > 10:
            logger.info(
                "query_understanding_skipped",
                session_id=state.session_id,
                reason="first_turn_clear_query",
            )
            state.rewritten_query = original_query
            state.expanded_queries = [original_query]
            state.intent = "knowledge_qa"
            state.query_reasoning = "直接返回原始查询（首轮且清晰）"
            return state

        # 构建对话历史文本
        history_text = self._format_history(messages)

        # LLM改写
        try:
            result = await self._understand_query(history_text, original_query)

            state.rewritten_query = result.rewritten_query
            state.expanded_queries = result.expanded_queries or [result.rewritten_query]
            state.intent = result.intent
            state.query_reasoning = result.reasoning

            logger.info(
                "query_understanding_completed",
                session_id=state.session_id,
                original=original_query[:50],
                rewritten=result.rewritten_query[:50],
                expanded_count=len(result.expanded_queries),
                intent=result.intent,
            )

        except Exception as e:
            logger.warning(
                "query_understanding_fallback",
                session_id=state.session_id,
                error=str(e),
            )
            # 降级: 直接使用原始查询
            state.rewritten_query = original_query
            state.expanded_queries = [original_query]
            state.intent = "knowledge_qa"
            state.query_reasoning = f"LLM调用失败，使用原始查询: {str(e)}"

        return state

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError, OSError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _understand_query(
        self, conversation_history: str, current_query: str
    ) -> QueryUnderstandingOutput:
        """调用LLM进行查询理解

        Args:
            conversation_history: 格式化后的对话历史
            current_query: 当前用户查询

        Returns:
            QueryUnderstandingOutput: 查询理解结果
        """
        try:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(content=QUERY_UNDERSTANDING_PROMPT.format(
                        conversation_history=conversation_history or "(无历史对话)",
                        current_query=current_query,
                    )),
                ],
                response_format={"type": "json_object"},
            )

            result = QueryUnderstandingOutput.model_validate_json(response.content)

            return result

        except Exception as e:
            logger.error(
                "query_understanding_llm_failed",
                error=str(e),
                query=current_query[:50],
            )
            raise

    def _format_history(self, messages: list, max_turns: int = 5) -> str:
        """格式化对话历史

        Args:
            messages: 对话历史消息列表
            max_turns: 最多保留的轮次

        Returns:
            str: 格式化后的历史文本
        """
        if not messages:
            return ""

        # 取最近的N轮（每轮包含用户+助手两条消息）
        recent = messages[-(max_turns * 2):] if len(messages) > 1 else messages
        if not recent:
            return ""

        lines = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                lines.append(f"用户: {content[:200]}")
            elif role == "assistant":
                lines.append(f"助手: {content[:200]}")

        return "\n".join(lines)

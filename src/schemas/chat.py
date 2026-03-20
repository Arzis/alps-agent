"""对话相关数据模型"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    """消息角色枚举

    - USER: 用户消息
    - ASSISTANT: 助手消息
    - SYSTEM: 系统消息
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """对话消息模型

    表示一条对话消息，包含角色、内容、时间戳和元数据。
    """
    role: MessageRole                                    # 消息角色
    content: str                                         # 消息内容
    timestamp: datetime = Field(default_factory=datetime.utcnow)  # 创建时间
    metadata: dict = Field(default_factory=dict)          # 额外元数据


class CitationItem(BaseModel):
    """引用信息模型

    表示 RAG 检索结果中的引用来源信息。
    """
    doc_id: str                     # 文档 ID
    doc_title: str                   # 文档标题
    content: str = Field(description="引用的原文片段")  # 引用的文本内容
    chunk_index: int | None = None   # 文档块索引
    relevance_score: float           # 相关性得分 (0-1)


class ChatRequest(BaseModel):
    """对话请求模型

    用户发送的对话请求参数。
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="用户消息"
    )                   # 用户消息内容
    session_id: str | None = Field(None, description="会话ID，不传则创建新会话")
    collection: str = Field("default", description="知识库 collection 名称")
    stream: bool = Field(False, description="是否流式返回")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "公司的年假制度是什么？",
                    "session_id": None,
                    "collection": "hr_docs",
                    "stream": False,
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """对话响应模型

    助手返回的对话结果，包含回答、引用、置信度等信息。
    """
    session_id: str                                    # 会话 ID
    message: str = Field(description="助手回复内容")  # 助手回复
    citations: list[CitationItem] = Field(
        default_factory=list,
        description="引用来源列表"
    )                                                  # RAG 引用列表
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="回答置信度"
    )                                                  # 置信度 (0-1)
    model_used: str = Field("", description="使用的模型")  # 实际使用的 LLM 模型
    fallback_used: bool = Field(False, description="是否使用了降级模型")  # 是否启用降级
    latency_ms: float = Field(0.0, description="处理耗时(毫秒)")  # 延迟
    tokens_used: int = Field(0, description="消耗的 token 数")  # Token 消耗


class StreamEvent(BaseModel):
    """SSE 流式事件模型

    用于 SSE (Server-Sent Events) 流式响应中的事件格式。
    """
    event: str  # 事件类型: token / citation / status / done / error
    data: str   # 事件数据 (JSON 字符串)


class SessionInfo(BaseModel):
    """会话信息模型

    表示一个对话会话的基本信息。
    """
    session_id: str                    # 会话 ID
    user_id: str                       # 用户 ID (用于隔离)
    title: str | None = None          # 会话标题
    message_count: int = 0            # 消息数量
    status: str = "active"            # 会话状态: active / completed / archived
    created_at: datetime               # 创建时间
    updated_at: datetime               # 更新时间


class ConversationHistory(BaseModel):
    """对话历史模型

    表示一个会话的完整对话历史。
    """
    session_id: str                    # 会话 ID
    messages: list[ChatMessage]       # 消息列表
    total_count: int                   # 消息总数

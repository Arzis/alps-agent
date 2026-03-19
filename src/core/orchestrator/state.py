"""对话编排状态定义模块

定义 LangGraph 对话编排的状态模式 (State Schema)。
状态在图的节点之间传递，包含对话的所有上下文信息。
"""

from dataclasses import dataclass, field
from typing import Literal

from src.schemas.chat import CitationItem


@dataclass
class ConversationState:
    """
    对话状态 - LangGraph 图中的共享状态

    状态在图的节点之间传递，每个节点可以读取和修改状态。

    Attributes:
        session_id: 会话唯一标识
        user_message: 用户当前消息
        collection: 知识库集合名称
        history_turns: 对话历史 (最近几轮)
        intent: 识别到的用户意图
        rewritten_query: 改写后的查询
        retrieved_chunks: RAG 检索到的文档块
        rag_answer: RAG 生成的回答
        final_answer: 最终回答
        citations: 引用的文档片段
        confidence: 置信度 (0-1)
        model_used: 实际使用的 LLM 模型
        fallback_used: 是否使用了降级模型
        tokens_used: 消耗的 token 数
        route: 当前路由决策
        error: 错误信息 (如有)
    """

    # === 输入字段 (必填) ===
    session_id: str = ""                           # 会话 ID
    user_message: str = ""                         # 用户消息
    collection: str = "default"                   # 知识库集合

    # === 中间状态 (节点间传递) ===
    history_turns: list[dict] = field(default_factory=list)  # 对话历史
    intent: str = "general"                       # 识别的意图 (general/knowledge/search)
    rewritten_query: str = ""                     # 改写后的查询
    expanded_queries: list[str] = field(default_factory=list)  # 扩展查询列表 (多路召回用)
    query_reasoning: str = ""                     # 查询改写推理过程
    retrieved_chunks: list = field(default_factory=list)       # RAG 检索结果
    rag_answer: str = ""                          # RAG 回答
    confidence: float = 0.0                       # 置信度
    model_used: str = ""                          # 使用的模型
    fallback_used: bool = False                    # 是否使用降级
    tokens_used: int = 0                          # token 消耗
    citations: list[CitationItem] = field(default_factory=list)  # 引用列表

    # === 路由字段 ===
    route: Literal["rag", "fallback", "reject", "direct"] = "rag"  # 路由决策
    cache_hit: bool = False  # 是否命中缓存

    # === 错误处理 ===
    error: str = ""                               # 错误信息


@dataclass
class OrchestratorResult:
    """
    编排结果 - 最终返回给调用方

    包含完整对话回答的所有信息。
    """
    answer: str = ""                                           # 回答内容
    citations: list[CitationItem] = field(default_factory=list)  # RAG 引用
    confidence: float = 0.0                                  # 置信度
    model_used: str = ""                                      # 使用的模型
    fallback_used: bool = False                               # 是否使用了降级
    tokens_used: int = 0                                     # 消耗的 token 数

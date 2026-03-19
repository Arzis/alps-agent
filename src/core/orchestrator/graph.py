"""LangGraph 对话编排图定义模块

定义对话编排的状态图结构，包括节点和边的连接。
Phase 2: 新增语义缓存查询节点。
"""

from typing import Callable

from langgraph.graph import StateGraph, END

from src.core.orchestrator.state import ConversationState
from src.core.orchestrator.nodes.query_understanding import QueryUnderstandingNode
from src.core.orchestrator.nodes.cache_lookup import CacheLookupNode, should_skip_rag
from src.core.orchestrator.nodes.rag_agent import RAGAgentNode
from src.core.orchestrator.nodes.fallback_node import FallbackNode
from src.core.orchestrator.nodes.quality_gate import QualityGateNode
from src.core.orchestrator.nodes.response_synthesizer import ResponseSynthesizerNode


def create_conversation_graph(
    query_understanding_node: QueryUnderstandingNode,
    cache_lookup_node: CacheLookupNode,
    rag_agent_node: RAGAgentNode,
    fallback_node: FallbackNode,
    quality_gate_node: QualityGateNode,
    response_synthesizer_node: ResponseSynthesizerNode,
) -> StateGraph:
    """
    创建对话编排图 - Phase 2

    图结构：
    START → query_understanding → cache_lookup
                                           ↓
                    ┌─────────────────────┼─────────────────────┐
                    ↓                     ↓                     ↓
               skip_to_end           codex_fallback          rag_agent
               (缓存命中)                (闲聊)                 (知识问答)
                    ↓                     ↓                     ↓
                    END                   END              quality_gate
                                                                   ↓
                                            ┌─────────────────────┼─────────────────────┐
                                            ↓                     ↓                     ↓
                                       direct                  fallback                reject
                                            ↓                     ↓                     ↓
                                            └─────────────────────┴─────────────────────┘
                                                                      ↓
                                                            response_synthesizer
                                                                      ↓
                                                                     END

    Args:
        query_understanding_node: 查询理解节点
        cache_lookup_node: 缓存查询节点
        rag_agent_node: RAG Agent 节点
        fallback_node: 降级兜底节点
        quality_gate_node: 质量门禁节点
        response_synthesizer_node: 响应合成节点

    Returns:
        StateGraph: 配置好的状态图
    """

    # 创建状态图
    graph = StateGraph(ConversationState)

    # === 注册节点 ===
    # 查询理解
    graph.add_node(
        "query_understanding",
        lambda state: query_understanding_node.execute(state)
    )

    # 缓存查询
    graph.add_node(
        "cache_lookup",
        lambda state: cache_lookup_node.execute(state)
    )

    # RAG Agent
    graph.add_node(
        "rag_agent",
        lambda state: rag_agent_node.execute(state)
    )

    # 降级兜底
    graph.add_node(
        "fallback",
        lambda state: fallback_node.execute(state)
    )

    # 质量门禁
    graph.add_node(
        "quality_gate",
        lambda state: quality_gate_node.execute(state)
    )

    # 响应合成
    graph.add_node(
        "response_synthesizer",
        lambda state: response_synthesizer_node.execute(state)
    )

    # === 定义边 ===

    # START → query_understanding
    graph.set_entry_point("query_understanding")

    # query_understanding → cache_lookup
    graph.add_edge(
        "query_understanding",
        "cache_lookup",
    )

    # cache_lookup → 条件分支
    # - skip_to_end: 缓存命中，直接结束
    # - codex_fallback: 闲聊意图
    # - rag_agent: 知识问答
    graph.add_conditional_edges(
        "cache_lookup",
        should_skip_rag,
        {
            "skip_to_end": END,           # 缓存命中
            "codex_fallback": "fallback",  # 闲聊
            "rag_agent": "rag_agent",      # 知识问答
        },
    )

    # rag_agent → quality_gate
    graph.add_edge(
        "rag_agent",
        "quality_gate",
    )

    # quality_gate → 条件分支
    def quality_gate_router(state: ConversationState) -> str:
        """质量门禁路由决策

        根据质量评估结果决定下一步：
        - direct: 直接返回 RAG 回答
        - fallback: 降级使用 LLM
        - reject: 拒绝回答
        """
        return state.route

    graph.add_conditional_edges(
        "quality_gate",
        quality_gate_router,
        {
            "direct": "response_synthesizer",
            "fallback": "fallback",
            "reject": "response_synthesizer",
        },
    )

    # fallback → response_synthesizer
    graph.add_edge(
        "fallback",
        "response_synthesizer",
    )

    # response_synthesizer → END
    graph.add_edge(
        "response_synthesizer",
        END,
    )

    return graph


def compile_graph(graph: StateGraph) -> Callable:
    """
    编译图为可执行形式

    Args:
        graph: 状态图

    Returns:
        Callable: 编译后的图，可直接调用
    """
    return graph.compile()

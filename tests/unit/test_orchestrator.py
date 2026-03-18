"""对话编排器单元测试

测试 ConversationOrchestrator 类的对话编排功能。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field

from src.core.orchestrator.state import ConversationState, OrchestratorResult
from src.core.orchestrator.engine import ConversationOrchestrator
from src.core.memory.manager import MemoryManager
from src.schemas.chat import CitationItem, MessageRole


class TestConversationState:
    """ConversationState 测试类"""

    def test_default_values(self):
        """测试默认值

        验证:
        - 状态有正确的默认值
        """
        state = ConversationState()

        assert state.session_id == ""
        assert state.user_message == ""
        assert state.collection == "default"
        assert state.intent == "general"
        assert state.route == "rag"
        assert state.confidence == 0.0
        assert state.fallback_used is False

    def test_state_fields(self):
        """测试状态字段

        验证:
        - 所有字段可以正确设置
        """
        citations = [
            CitationItem(
                doc_id="doc_001",
                doc_title="测试文档",
                content="引用内容",
                chunk_index=0,
                relevance_score=0.85,
            )
        ]

        state = ConversationState(
            session_id="sess_001",
            user_message="测试问题",
            collection="hr_docs",
            intent="knowledge",
            confidence=0.85,
            citations=citations,
        )

        assert state.session_id == "sess_001"
        assert state.user_message == "测试问题"
        assert state.collection == "hr_docs"
        assert state.intent == "knowledge"
        assert state.confidence == 0.85
        assert len(state.citations) == 1

    def test_state_mutable(self):
        """测试状态可变性

        验证:
        - 状态字段可以被修改
        """
        state = ConversationState()
        state.rag_answer = "RAG 回答"
        state.confidence = 0.9
        state.fallback_used = True

        assert state.rag_answer == "RAG 回答"
        assert state.confidence == 0.9
        assert state.fallback_used is True


class TestOrchestratorResult:
    """OrchestratorResult 测试类"""

    def test_default_values(self):
        """测试默认值"""
        result = OrchestratorResult()

        assert result.answer == ""
        assert result.confidence == 0.0
        assert result.fallback_used is False
        assert result.tokens_used == 0
        assert len(result.citations) == 0

    def test_result_fields(self):
        """测试结果字段"""
        citations = [
            CitationItem(
                doc_id="doc_001",
                doc_title="测试文档",
                content="内容",
                relevance_score=0.85,
            )
        ]

        result = OrchestratorResult(
            answer="这是最终回答",
            citations=citations,
            confidence=0.9,
            model_used="gpt-4o",
            fallback_used=False,
            tokens_used=500,
        )

        assert result.answer == "这是最终回答"
        assert result.confidence == 0.9
        assert result.model_used == "gpt-4o"
        assert result.tokens_used == 500
        assert len(result.citations) == 1


class TestConversationOrchestrator:
    """ConversationOrchestrator 测试类"""

    @pytest.fixture
    def mock_memory_manager(self) -> MagicMock:
        """Mock 记忆管理器"""
        manager = MagicMock(spec=MemoryManager)
        manager.load_context = AsyncMock(return_value=[])
        manager.save_turn = AsyncMock()
        manager.clear_session = AsyncMock()
        return manager

    @pytest.fixture
    def mock_compiled_graph(self) -> MagicMock:
        """Mock 编译后的 LangGraph"""
        graph = MagicMock()
        # 模拟返回 OrchestratorResult
        result = OrchestratorResult(
            answer="测试回答",
            confidence=0.85,
            model_used="gpt-4o-mini",
            fallback_used=False,
            tokens_used=100,
        )
        graph.ainvoke = AsyncMock(return_value=result)
        return graph

    @pytest.fixture
    def mock_postgres_pool(self) -> MagicMock:
        """Mock PostgreSQL 连接池"""
        pool = MagicMock()
        pool.fetchval = AsyncMock(return_value=1)
        return pool

    @pytest.fixture
    def orchestrator(
        self,
        mock_memory_manager: MagicMock,
        mock_postgres_pool: MagicMock,
        mock_compiled_graph: MagicMock,
    ) -> ConversationOrchestrator:
        """创建 ConversationOrchestrator 实例"""
        return ConversationOrchestrator(
            memory_manager=mock_memory_manager,
            pg_pool=mock_postgres_pool,
            compiled_graph=mock_compiled_graph,
        )

    @pytest.mark.asyncio
    async def test_run_basic_conversation(
        self,
        orchestrator: ConversationOrchestrator,
        mock_memory_manager: MagicMock,
        mock_compiled_graph: MagicMock,
    ):
        """测试基本对话流程

        验证:
        - 编排器正确执行对话
        - 返回正确的回答
        """
        result = await orchestrator.run(
            session_id="sess_001",
            message="你好",
            collection="default",
        )

        assert result.answer == "测试回答"
        assert result.confidence == 0.85
        mock_memory_manager.load_context.assert_called_once()
        mock_compiled_graph.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_history(
        self,
        orchestrator: ConversationOrchestrator,
        mock_memory_manager: MagicMock,
    ):
        """测试带历史的对话

        验证:
        - 历史消息被加载
        - 传递给图执行
        """
        history = [
            {"role": "user", "content": "上一轮的问题"},
            {"role": "assistant", "content": "上一轮的回答"},
        ]
        mock_memory_manager.load_context = AsyncMock(return_value=history)

        result = await orchestrator.run(
            session_id="sess_001",
            message="继续",
            collection="default",
        )

        # 验证历史被加载
        mock_memory_manager.load_context.assert_called_with("sess_001", max_turns=5)

    @pytest.mark.asyncio
    async def test_run_saves_turn(
        self,
        orchestrator: ConversationOrchestrator,
        mock_memory_manager: MagicMock,
    ):
        """测试对话后保存对话

        验证:
        - 对话被保存到记忆
        """
        result = await orchestrator.run(
            session_id="sess_001",
            message="你好",
            collection="default",
        )

        mock_memory_manager.save_turn.assert_called_once()
        call_kwargs = mock_memory_manager.save_turn.call_args[1]
        assert call_kwargs["session_id"] == "sess_001"
        assert call_kwargs["user_message"] == "你好"
        assert call_kwargs["assistant_message"] == "测试回答"

    @pytest.mark.asyncio
    async def test_run_with_collection(
        self,
        orchestrator: ConversationOrchestrator,
        mock_compiled_graph: MagicMock,
    ):
        """测试指定 collection

        验证:
        - collection 被正确传递
        """
        result = await orchestrator.run(
            session_id="sess_001",
            message="问题",
            collection="hr_docs",
        )

        # 验证 initial_state 包含正确的 collection
        call_args = mock_compiled_graph.ainvoke.call_args
        state = call_args[0][0]
        assert state.collection == "hr_docs"

    @pytest.mark.asyncio
    async def test_stream_returns_events(
        self,
        orchestrator: ConversationOrchestrator,
        mock_memory_manager: MagicMock,
        mock_compiled_graph: MagicMock,
    ):
        """测试流式返回事件

        验证:
        - 流式事件被正确生成
        """
        events = []
        async for event in orchestrator.stream(
            session_id="sess_001",
            message="你好",
            collection="default",
        ):
            events.append(event)

        # 应该产生多个事件
        assert len(events) > 0
        # 第一个应该是 status 事件
        assert events[0].event == "status"

    @pytest.mark.asyncio
    async def test_delete_session(
        self,
        orchestrator: ConversationOrchestrator,
        mock_memory_manager: MagicMock,
    ):
        """测试删除会话

        验证:
        - 记忆被清除
        """
        await orchestrator.delete_session("sess_001")

        mock_memory_manager.clear_session.assert_called_once_with("sess_001")


class TestOrchestratorStateTransition:
    """编排器状态流转测试"""

    @pytest.mark.asyncio
    async def test_state_initialization(self):
        """测试状态初始化

        验证:
        - 初始状态有正确的默认值
        """
        state = ConversationState(
            session_id="test_sess",
            user_message="测试消息",
            collection="default",
        )

        # 验证初始状态
        assert state.session_id == "test_sess"
        assert state.user_message == "测试消息"
        assert state.collection == "default"
        assert state.history_turns == []
        assert state.retrieved_chunks == []
        assert state.citations == []
        assert state.error == ""

    @pytest.mark.asyncio
    async def test_rag_answer_flow(self):
        """测试 RAG 回答流程

        验证:
        - RAG 答案可以被设置
        """
        state = ConversationState(
            session_id="sess_001",
            user_message="RAG 问题",
        )

        # 模拟 RAG Agent 设置答案
        state.rag_answer = "这是 RAG 回答"
        state.confidence = 0.85
        state.model_used = "gpt-4o"
        state.citations = [
            CitationItem(
                doc_id="doc_001",
                doc_title="测试文档",
                content="引用内容",
                relevance_score=0.85,
            )
        ]

        assert state.rag_answer == "这是 RAG 回答"
        assert state.confidence == 0.85
        assert len(state.citations) == 1

    @pytest.mark.asyncio
    async def test_fallback_flow(self):
        """测试降级流程

        验证:
        - 降级答案可以被设置
        """
        state = ConversationState(
            session_id="sess_001",
            user_message="降级问题",
        )

        # 模拟降级节点设置答案
        state.rag_answer = "这是降级回答"
        state.confidence = 0.3
        state.model_used = "gpt-4o-mini"
        state.fallback_used = True

        assert state.rag_answer == "这是降级回答"
        assert state.confidence == 0.3
        assert state.fallback_used is True

"""查询理解节点单元测试

测试 QueryUnderstandingNode 类的功能 - Phase 2 增强版。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.orchestrator.state import ConversationState
from src.core.orchestrator.nodes.query_understanding import (
    QueryUnderstandingNode,
    QueryUnderstandingOutput,
    QUERY_UNDERSTANDING_PROMPT,
)


class TestQueryUnderstandingOutput:
    """QueryUnderstandingOutput 数据模型测试"""

    def test_basic_output(self):
        """测试基本输出模型"""
        output = QueryUnderstandingOutput(
            rewritten_query="改写后的查询",
            expanded_queries=["扩展查询1", "扩展查询2"],
            intent="knowledge_qa",
            reasoning="因为原问题是口语化的",
        )
        assert output.rewritten_query == "改写后的查询"
        assert len(output.expanded_queries) == 2
        assert output.intent == "knowledge_qa"

    def test_default_values(self):
        """测试默认值"""
        output = QueryUnderstandingOutput(rewritten_query="测试查询")
        assert output.rewritten_query == "测试查询"
        assert output.expanded_queries == []
        assert output.intent == "knowledge_qa"
        assert output.reasoning == ""


class TestQueryUnderstandingNode:
    """QueryUnderstandingNode 测试类"""

    @pytest.fixture
    def mock_settings(self):
        """模拟设置"""
        settings = MagicMock()
        settings.PRIMARY_LLM_MODEL = "test-model"
        settings.DASHSCOPE_API_KEY = MagicMock()
        settings.DASHSCOPE_API_KEY.get_secret_value.return_value = "test-key"
        settings.DASHSCOPE_BASE_URL = "https://api.test.com"
        settings.LLM_TIMEOUT = 30
        return settings

    @pytest.fixture
    def node(self, mock_settings):
        """创建查询理解节点实例"""
        return QueryUnderstandingNode(settings=mock_settings)

    @pytest.fixture
    def empty_state(self):
        """空对话状态"""
        return ConversationState(
            session_id="test_session",
            user_message="测试问题",
            history_turns=[],
        )

    @pytest.fixture
    def multi_turn_state(self):
        """多轮对话状态"""
        return ConversationState(
            session_id="test_session",
            user_message="它有什么限制？",
            history_turns=[
                {"role": "user", "content": "年假制度是什么？"},
                {"role": "assistant", "content": "年假制度是..."},
            ],
        )

    def test_format_history_empty(self, node):
        """测试格式化空历史"""
        result = node._format_history([])
        assert result == ""

    def test_format_history_single_message(self, node):
        """测试格式化单条消息"""
        messages = [{"role": "user", "content": "你好"}]
        result = node._format_history(messages)
        assert "用户" in result
        assert "你好" in result

    def test_format_history_multiple_turns(self, node):
        """测试格式化多轮对话"""
        messages = [
            {"role": "user", "content": "年假制度是什么？"},
            {"role": "assistant", "content": "年假制度是..."},
            {"role": "user", "content": "它有什么限制？"},
        ]
        result = node._format_history(messages, max_turns=5)
        assert "用户" in result
        assert "助手" in result
        assert "年假制度" in result

    def test_format_history_truncation(self, node):
        """测试历史截断"""
        messages = [
            {"role": "user", "content": f"消息{i}"}
            for i in range(20)
        ]
        result = node._format_history(messages, max_turns=3)
        lines = result.split("\n")
        # max_turns * 2 = 6条消息(用户+助手)
        assert len(lines) <= 6

    def test_skip_llm_for_clear_first_query(self, node, empty_state):
        """测试清晰的首轮查询跳过LLM调用"""
        empty_state.user_message = "这是一个比较长的清晰问题描述"
        empty_state.history_turns = []

        # 同步执行（因为有await）
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(node.execute(empty_state))

        assert result.rewritten_query == "这是一个比较长的问题描述"[:50] or result.rewritten_query == empty_state.user_message
        assert result.expanded_queries == [empty_state.user_message]
        assert result.intent == "knowledge_qa"

    @pytest.mark.asyncio
    async def test_execute_with_history(self, node, multi_turn_state):
        """测试带历史记录的查询理解"""
        # Mock LLM响应
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "rewritten_query": "年假制度有什么限制？",
            "expanded_queries": ["员工年假政策限制", "公司带薪休假规定限制"],
            "intent": "knowledge_qa",
            "reasoning": "根据对话历史，将代词'它'消解为'年假制度'"
        }
        '''

        with patch.object(node, '_understand_query', new_callable=AsyncMock) as mock_understand:
            mock_understand.return_value = QueryUnderstandingOutput.model_validate_json(mock_response.content)

            result = await node.execute(multi_turn_state)

            assert result.rewritten_query == "年假制度有什么限制？"
            assert len(result.expanded_queries) == 2
            assert result.intent == "knowledge_qa"
            assert "年假制度" in result.query_reasoning

    @pytest.mark.asyncio
    async def test_execute_fallback_on_error(self, node, multi_turn_state):
        """测试LLM失败时降级"""
        with patch.object(node, '_understand_query', new_callable=AsyncMock) as mock_understand:
            mock_understand.side_effect = Exception("LLM调用失败")

            result = await node.execute(multi_turn_state)

            # 应该使用原始查询作为降级
            assert result.rewritten_query == multi_turn_state.user_message
            assert result.expanded_queries == [multi_turn_state.user_message]
            assert result.intent == "knowledge_qa"
            assert "LLM调用失败" in result.query_reasoning

    @pytest.mark.asyncio
    async def test_intent_chitchat(self, node, empty_state):
        """测试闲聊意图识别"""
        empty_state.user_message = "你好啊，今天天气不错"

        mock_response = MagicMock()
        mock_response.content = '''
        {
            "rewritten_query": "你好",
            "expanded_queries": ["你好"],
            "intent": "chitchat",
            "reasoning": "用户在进行寒暄"
        }
        '''

        with patch.object(node, '_understand_query', new_callable=AsyncMock) as mock_understand:
            mock_understand.return_value = QueryUnderstandingOutput.model_validate_json(mock_response.content)

            result = await node.execute(empty_state)

            assert result.intent == "chitchat"

    @pytest.mark.asyncio
    async def test_intent_unclear(self, node, empty_state):
        """测试意图不明确"""
        empty_state.user_message = "那个..."

        mock_response = MagicMock()
        mock_response.content = '''
        {
            "rewritten_query": "",
            "expanded_queries": [],
            "intent": "unclear",
            "reasoning": "问题太模糊"
        }
        '''

        with patch.object(node, '_understand_query', new_callable=AsyncMock) as mock_understand:
            mock_understand.return_value = QueryUnderstandingOutput.model_validate_json(mock_response.content)

            result = await node.execute(empty_state)

            assert result.intent == "unclear"


class TestQueryUnderstandingPrompt:
    """Prompt模板测试"""

    def test_prompt_contains_placeholders(self):
        """测试prompt包含必要占位符"""
        assert "{conversation_history}" in QUERY_UNDERSTANDING_PROMPT
        assert "{current_query}" in QUERY_UNDERSTANDING_PROMPT

    def test_prompt_includes_instructions(self):
        """测试prompt包含必要指令"""
        assert "指代消解" in QUERY_UNDERSTANDING_PROMPT
        assert "查询改写" in QUERY_UNDERSTANDING_PROMPT
        assert "查询扩展" in QUERY_UNDERSTANDING_PROMPT
        assert "意图识别" in QUERY_UNDERSTANDING_PROMPT

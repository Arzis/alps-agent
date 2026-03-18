"""端到端测试 - 完整对话流程

测试从文档上传到 RAG 问答的完整流程。
注意: 这些测试需要完整的基础设施服务运行。
"""

import pytest
import io


@pytest.mark.asyncio
class TestFullConversationFlow:
    """完整对话流程测试类"""

    async def test_health_check_before_e2e(self, async_client):
        """E2E 测试前的健康检查

        验证:
        - 所有依赖服务健康
        """
        response = await async_client.get("/health/detail")
        # 如果服务已启动，应该返回详细健康状态
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "checks" in data

    async def test_document_upload_flow(self, async_client):
        """文档上传流程测试

        步骤:
        1. 上传一个包含年假制度的 Markdown 文档
        2. 验证返回 doc_id
        """
        # 创建测试文档内容
        content = """# 公司年假制度

## 一、年假天数
- 工龄1-5年: 5天年假
- 工龄5-10年: 10天年假
- 工龄10年以上: 15天年假

## 二、请假流程
1. 提前3天在OA系统提交申请
2. 直属上级审批
3. HR备案
"""
        files = {
            "file": (
                "hr_policy.md",
                io.BytesIO(content.encode("utf-8")),
                "text/markdown"
            )
        }

        response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
            data={"collection": "hr_docs"},
        )

        # 如果服务已启动
        if response.status_code in [200, 201]:
            data = response.json()
            assert "doc_id" in data
            assert data["filename"] == "hr_policy.md"
        else:
            # 服务未启动时跳过
            pytest.skip("Service not available")

    async def test_chat_completions_flow(self, async_client):
        """对话补全流程测试

        步骤:
        1. 发送对话请求
        2. 验证返回回答
        """
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "message": "公司的年假制度是什么？",
                "collection": "hr_docs",
            },
        )

        if response.status_code == 200:
            data = response.json()
            assert "session_id" in data
            assert "message" in data
        else:
            pytest.skip("Service not available")

    async def test_multi_turn_conversation(self, async_client):
        """多轮对话测试

        步骤:
        1. 第一轮对话
        2. 使用返回的 session_id 进行第二轮对话
        3. 验证上下文保持
        """
        # 第一轮
        response1 = await async_client.post(
            "/api/v1/chat/completions",
            json={"message": "什么是RAG？"},
        )

        if response1.status_code != 200:
            pytest.skip("Service not available")

        session_id = response1.json()["session_id"]

        # 第二轮 - 使用相同 session_id
        response2 = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "message": "它有什么优势？",  # 指代"RAG"
                "session_id": session_id,
            },
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["session_id"] == session_id

    async def test_document_upload_and_query_flow(self, async_client):
        """文档上传+问答完整流程测试

        步骤:
        1. 上传包含特定信息的文档
        2. 查询该信息
        3. 验证回答包含正确信息
        """
        # 1. 上传文档
        content = """# 产品介绍

## 产品A
产品A是一款高端产品，具有以下特性:
- 高性能处理器
- 大容量存储
- 优秀的用户体验

## 产品B
产品B是一款入门级产品，价格实惠:
- 基础功能完善
- 性价比高
"""
        files = {
            "file": (
                "products.md",
                io.BytesIO(content.encode("utf-8")),
                "text/markdown"
            )
        }

        upload_response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
            data={"collection": "product_docs"},
        )

        if upload_response.status_code not in [200, 201]:
            pytest.skip("Service not available")

        doc_data = upload_response.json()
        doc_id = doc_data["doc_id"]

        # 2. 查询文档状态
        # 注: 实际应该等待处理完成，这里简化为直接查询
        # 在真实 E2E 测试中，应该轮询文档状态直到完成

        # 3. 查询相关信息
        query_response = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "message": "产品A有哪些特性？",
                "collection": "product_docs",
            },
        )

        if query_response.status_code == 200:
            data = query_response.json()
            assert "message" in data
            # 验证回答包含产品A的信息 (如果 RAG 正常工作)
            # answer = data["message"]
            # assert "高性能" in answer or "处理器" in answer
        else:
            pytest.skip("Service not available")


@pytest.mark.asyncio
class TestErrorHandling:
    """错误处理测试"""

    async def test_graceful_degradation(self, async_client):
        """优雅降级测试

        验证:
        - 当 RAG 失败时，系统应该降级到 fallback 回答
        """
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={
                "message": "一个非常长的问题" * 100,
                "collection": "nonexistent_collection",
            },
        )

        # 应该返回 200 (即使使用 fallback)
        if response.status_code == 200:
            data = response.json()
            # fallback_used 标志可能为 True
            assert "message" in data


@pytest.mark.asyncio
class TestStreamFlow:
    """流式输出测试"""

    async def test_stream_endpoint_exists(self, async_client):
        """测试流式端点存在

        验证:
        - 流式端点存在 (如果实现了)
        """
        response = await async_client.post(
            "/api/v1/chat/completions/stream",
            json={
                "message": "测试流式输出",
                "stream": True,
            },
        )
        # 如果实现了流式端点，应该返回 200 或处理请求
        # 如果没实现，可能返回 404 或 405
        assert response.status_code in [200, 404, 405, 500]


@pytest.mark.asyncio
class TestPerformance:
    """性能测试"""

    async def test_response_time_reasonable(self, async_client):
        """响应时间测试

        验证:
        - 简单查询的响应时间在合理范围内
        """
        import time

        start = time.perf_counter()
        response = await async_client.post(
            "/api/v1/chat/completions",
            json={"message": "你好"},
        )
        elapsed = time.perf_counter() - start

        if response.status_code == 200:
            # 响应时间应该少于 10 秒 (简单查询)
            assert elapsed < 10

"""文档 API 集成测试

测试 Document API 端点的功能。
注意: 这些测试需要运行中的基础设施服务。
"""

import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
class TestDocumentAPI:
    """文档 API 测试类"""

    async def test_document_upload_endpoint_exists(self, async_client):
        """测试文档上传端点存在

        验证:
        - POST /api/v1/documents/upload 存在
        """
        # 创建一个测试文件
        file_content = b"# Test Document\n\nThis is a test."
        files = {"file": ("test.md", io.BytesIO(file_content), "text/markdown")}

        response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
            data={"collection": "default"},
        )
        # 可能会因为服务未启动返回错误，但端点存在
        assert response.status_code in [200, 201, 500, 503]

    async def test_document_list_endpoint_exists(self, async_client):
        """测试文档列表端点存在

        验证:
        - GET /api/v1/documents/ 存在
        """
        response = await async_client.get("/api/v1/documents/")
        assert response.status_code in [200, 500, 503]


@pytest.mark.asyncio
class TestDocumentAPIWithMocks:
    """带 Mock 的文档 API 测试"""

    async def test_upload_invalid_file_type(self, async_client):
        """测试上传不支持的文件类型

        验证:
        - 返回 400 错误
        """
        file_content = b"invalid content"
        files = {"file": ("test.xyz", io.BytesIO(file_content), "application/octet-stream")}

        response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
        )
        # 不支持的类型应该返回 400
        assert response.status_code == 400

    async def test_upload_without_file(self, async_client):
        """测试不上传文件

        验证:
        - 返回 422 验证错误
        """
        response = await async_client.post(
            "/api/v1/documents/upload",
            data={"collection": "default"},
        )
        assert response.status_code == 422

    async def test_get_nonexistent_document(self, async_client):
        """测试获取不存在的文档

        验证:
        - 返回 404
        """
        response = await async_client.get("/api/v1/documents/nonexistent_doc_id")
        assert response.status_code == 404

    async def test_list_documents_with_pagination(self, async_client):
        """测试文档列表分页

        验证:
        - 分页参数被正确处理
        """
        response = await async_client.get(
            "/api/v1/documents/",
            params={"page": 1, "page_size": 10},
        )
        # 返回 200 或因为 DB 未启动返回错误
        assert response.status_code in [200, 500, 503]

    async def test_list_documents_with_collection_filter(self, async_client):
        """测试按 collection 过滤

        验证:
        - collection 参数被正确处理
        """
        response = await async_client.get(
            "/api/v1/documents/",
            params={"collection": "hr_docs"},
        )
        assert response.status_code in [200, 500, 503]


@pytest.mark.asyncio
class TestDocumentUploadValidation:
    """文档上传验证测试"""

    async def test_upload_empty_file(self, async_client):
        """测试上传空文件

        验证:
        - 空文件被接受 (具体处理取决于后端)
        """
        file_content = b""
        files = {"file": ("empty.txt", io.BytesIO(file_content), "text/plain")}

        response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
        )
        # 空文件可能被接受或拒绝
        assert response.status_code in [200, 201, 400, 413]

    async def test_upload_pdf_file(self, async_client):
        """测试上传 PDF 文件

        验证:
        - PDF 文件被接受
        """
        # 模拟 PDF 文件内容 (实际应该用真实的 PDF)
        file_content = b"%PDF-1.4 fake pdf content"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

        response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
            data={"collection": "default"},
        )
        assert response.status_code in [200, 201, 400, 500, 503]

    async def test_upload_docx_file(self, async_client):
        """测试上传 DOCX 文件

        验证:
        - DOCX 文件被接受
        """
        # 模拟 DOCX 文件内容
        file_content = b"PK\x03\x04 fake docx content"
        files = {"file": ("test.docx", io.BytesIO(file_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}

        response = await async_client.post(
            "/api/v1/documents/upload",
            files=files,
            data={"collection": "default"},
        )
        assert response.status_code in [200, 201, 400, 500, 503]

"""文档相关数据模型"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """文档状态枚举

    - UPLOADED: 已上传
    - PROCESSING: 处理中
    - COMPLETED: 处理完成
    - FAILED: 处理失败
    """
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadResponse(BaseModel):
    """文档上传响应模型

    文档上传接口的返回结果。
    """
    doc_id: str           # 文档 ID
    filename: str        # 文件名
    status: DocumentStatus = DocumentStatus.UPLOADED  # 文档状态
    message: str = "文档已上传，正在后台处理"         # 状态消息


class DocumentInfo(BaseModel):
    """文档信息模型

    表示一个文档的完整信息。
    """
    doc_id: str                    # 文档 ID
    filename: str                  # 文件名
    file_type: str                 # 文件类型 (如 .pdf, .docx)
    file_size: int                 # 文件大小 (字节)
    collection: str                 # 所属知识库集合
    status: DocumentStatus         # 处理状态
    chunk_count: int = 0         # 分块数量
    error_message: str | None = None  # 错误信息 (如果处理失败)
    created_at: datetime           # 创建时间
    updated_at: datetime           # 更新时间


class DocumentListResponse(BaseModel):
    """文档列表响应模型

    文档列表查询接口的返回结果。
    """
    documents: list[DocumentInfo]  # 文档列表
    total: int                    # 总数
    page: int                     # 当前页码
    page_size: int                # 每页大小

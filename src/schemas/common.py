"""通用数据模型 - 基础响应格式"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class BaseResponse(BaseModel):
    """基础响应模型

    所有 API 响应的基类，提供统一的响应格式。
    """
    success: bool = True  # 请求是否成功
    timestamp: datetime = Field(default_factory=datetime.utcnow)  # 响应时间


class ErrorResponse(BaseModel):
    """错误响应模型

    用于返回错误信息给客户端。
    """
    error: dict[str, Any]  # 错误详情字典

"""全局异常处理中间件 - 统一处理应用异常"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import structlog

logger = structlog.get_logger()


class AppError(Exception):
    """应用异常基类

    所有自定义异常的父类。
    提供统一的错误格式: message, status_code, error_code
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR"
    ):
        self.message = message       # 错误消息
        self.status_code = status_code  # HTTP 状态码
        self.error_code = error_code    # 错误代码


class NotFoundError(AppError):
    """资源未找到异常

    HTTP 404 错误。
    """

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class RateLimitError(AppError):
    """请求频率超限异常

    HTTP 429 错误。
    """

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429, error_code="RATE_LIMITED")


class LLMError(AppError):
    """LLM 服务异常

    HTTP 502 错误，表示下游 LLM 服务不可用。
    """

    def __init__(self, message: str = "LLM service error"):
        super().__init__(message, status_code=502, error_code="LLM_ERROR")


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器

    将自定义异常处理器注册到 FastAPI 应用。
    这些处理器会在相应异常抛出时自动调用。

    Args:
        app: FastAPI 应用实例
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        """处理应用自定义异常 (AppError 及其子类)"""
        logger.warning(
            "app_error",
            error_code=exc.error_code,    # 错误代码
            message=exc.message,          # 错误消息
            status_code=exc.status_code,  # HTTP 状态码
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """处理 Pydantic 验证错误 (请求参数校验失败)"""
        logger.warning("validation_error", errors=exc.errors())
        return JSONResponse(
            status_code=422,  # Unprocessable Entity
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),  # 详细的验证错误列表
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        """处理所有未捕获的异常 (最后一道防线)"""
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,  # Internal Server Error
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    # 生产环境不暴露具体错误信息
                    "message": "An unexpected error occurred" if not hasattr(request.app, 'debug') or not request.app.debug else str(exc),
                }
            },
        )

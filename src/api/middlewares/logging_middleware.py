"""请求日志中间件 - 记录每个 HTTP 请求的关键信息"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import structlog

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件

    功能:
    - 为每个请求生成唯一请求 ID
    - 绑定请求上下文到 structlog
    - 记录请求处理时间和状态
    - 添加 X-Request-ID 和 X-Response-Time 响应头
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """处理请求的主方法

        Args:
            request: FastAPI 请求对象
            call_next: 下一个处理器 (路由处理函数)

        Returns:
            Response: 带有额外响应头的响应对象
        """
        # 生成请求 ID (取 UUID 的前 8 位)
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # 绑定到 structlog 上下文
        # 这样所有日志都会带有这些字段
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,                    # 请求唯一标识
            method=request.method,                     # HTTP 方法 (GET/POST 等)
            path=request.url.path,                     # 请求路径
            client_ip=request.client.host if request.client else "unknown",  # 客户端 IP
        )

        start_time = time.perf_counter()  # 记录开始时间

        try:
            # 调用下一个处理器 (实际的处理逻辑)
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start_time) * 1000  # 计算耗时

            # 记录请求完成日志
            logger.info(
                "request_completed",
                status_code=response.status_code,      # HTTP 状态码
                latency_ms=round(elapsed_ms, 2),       # 保留 2 位小数
            )

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"

            return response

        except Exception as e:
            # 请求处理发生异常
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "request_failed",
                error=str(e),                          # 错误信息
                error_type=type(e).__name__,           # 错误类型
                latency_ms=round(elapsed_ms, 2),       # 耗时
            )
            raise  # 重新抛出异常，让 error_handler 中间件处理

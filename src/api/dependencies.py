"""FastAPI 依赖注入模块

提供全局依赖的注入函数，如编排引擎实例、数据库连接池等。
"""

from fastapi import Request
from src.core.orchestrator.engine import ConversationOrchestrator
from src.api.middlewares.error_handler import AppError


async def get_orchestrator(request: Request) -> ConversationOrchestrator:
    """获取编排引擎实例

    从 FastAPI 应用的 app.state 中获取编排引擎实例。

    Args:
        request: FastAPI 请求对象

    Returns:
        ConversationOrchestrator: 编排引擎实例

    Raises:
        AppError: 如果编排引擎未初始化 (503 Service Unavailable)
    """
    orchestrator: ConversationOrchestrator | None = getattr(
        request.app.state, "orchestrator", None
    )
    if orchestrator is None:
        raise AppError(
            message="Orchestrator not initialized - service may be starting up",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
        )
    return orchestrator


async def get_pg_pool(request: Request):
    """获取 PostgreSQL 连接池

    从 FastAPI 应用的 app.state 中获取 PostgreSQL 连接池。

    Args:
        request: FastAPI 请求对象

    Returns:
        asyncpg.Pool: PostgreSQL 连接池
    """
    pg_pool = getattr(request.app.state, "pg_pool", None)
    if pg_pool is None:
        raise AppError(
            message="PostgreSQL pool not initialized",
            status_code=503,
            error_code="DATABASE_UNAVAILABLE",
        )
    return pg_pool

"""FastAPI 依赖注入模块

提供全局依赖的注入函数，如编排引擎实例。
"""

from fastapi import Request
from src.core.orchestrator.engine import ConversationOrchestrator


async def get_orchestrator(request: Request) -> ConversationOrchestrator:
    """获取编排引擎实例

    从 FastAPI 应用的 app.state 中获取编排引擎实例。

    Args:
        request: FastAPI 请求对象

    Returns:
        ConversationOrchestrator: 编排引擎实例

    Raises:
        RuntimeError: 如果编排引擎未初始化
    """
    orchestrator: ConversationOrchestrator | None = getattr(
        request.app.state, "orchestrator", None
    )
    if orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return orchestrator

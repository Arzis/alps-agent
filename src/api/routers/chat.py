"""对话路由 - 处理用户对话请求"""

import time
import uuid
from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
import structlog

from src.schemas.chat import (
    ChatRequest, ChatResponse, ConversationHistory,
    SessionInfo, StreamEvent,
)
from src.schemas.auth import TokenData
from src.api.dependencies import get_orchestrator
from src.api.routers.auth import get_current_user

logger = structlog.get_logger()
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    user: TokenData = Depends(get_current_user),
    orchestrator=Depends(get_orchestrator),
):
    """
    对话接口 - 同步模式

    - 不传 session_id 则创建新会话
    - 传 session_id 则继续已有会话 (多轮对话)
    - 用户只能访问自己的会话

    Args:
        request: 对话请求参数
        user: 当前登录用户 (从 JWT Token 解析)
        orchestrator: 编排引擎实例 (依赖注入)

    Returns:
        ChatResponse: 包含助手回复、引用、置信度等信息的响应
    """
    start_time = time.perf_counter()

    # 如果没有 session_id，创建新会话 (带 user_id 前缀)
    session_id = request.session_id or f"{user.user_id}_sess_{uuid.uuid4().hex[:12]}"

    logger.info(
        "chat_request",
        user_id=user.user_id,
        session_id=session_id,
        message_length=len(request.message),
        collection=request.collection,
    )

    # 调用编排引擎处理对话
    result = await orchestrator.run(
        session_id=session_id,
        message=request.message,
        collection=request.collection,
        user_id=user.user_id,
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "chat_response",
        user_id=user.user_id,
        session_id=session_id,
        confidence=result.confidence,
        fallback_used=result.fallback_used,
        latency_ms=round(elapsed_ms, 2),
    )

    return ChatResponse(
        session_id=session_id,
        message=result.answer,
        citations=result.citations,
        confidence=result.confidence,
        model_used=result.model_used,
        fallback_used=result.fallback_used,
        latency_ms=round(elapsed_ms, 2),
        tokens_used=result.tokens_used,
    )


@router.post("/completions/stream")
async def chat_completion_stream(
    request: ChatRequest,
    user: TokenData = Depends(get_current_user),
    orchestrator=Depends(get_orchestrator),
):
    """
    对话接口 - SSE 流式模式

    使用 Server-Sent Events (SSE) 进行流式响应。
    适用于需要实时显示打字效果的场景。

    事件类型:
    - status: 状态更新 (如 "processing")
    - token: 逐 token 输出
    - citation: 引用信息
    - done: 完成
    - error: 错误
    """
    # 如果没有 session_id，创建新会话 (带 user_id 前缀)
    session_id = request.session_id or f"{user.user_id}_sess_{uuid.uuid4().hex[:12]}"

    async def event_generator():
        try:
            # 发送会话 ID 状态
            yield {
                "event": "status",
                "data": f'{{"session_id": "{session_id}", "status": "processing"}}',
            }

            # 流式处理事件
            async for event in orchestrator.stream(
                session_id=session_id,
                message=request.message,
                collection=request.collection,
                user_id=user.user_id,
            ):
                yield {
                    "event": event.event,
                    "data": event.data,
                }

        except Exception as e:
            logger.exception("stream_error", user_id=user.user_id, session_id=session_id)
            yield {
                "event": "error",
                "data": f'{{"error": "{str(e)}"}}',
            }

    return EventSourceResponse(event_generator())


@router.get("/sessions/{session_id}/history", response_model=ConversationHistory)
async def get_conversation_history(
    session_id: str,
    user: TokenData = Depends(get_current_user),
    limit: int = 50,
    orchestrator=Depends(get_orchestrator),
):
    """获取对话历史

    Args:
        session_id: 会话 ID
        user: 当前登录用户
        limit: 最大返回消息数
        orchestrator: 编排引擎实例

    Returns:
        ConversationHistory: 对话历史
    """
    history = await orchestrator.get_history(session_id, user_id=user.user_id, limit=limit)
    return history


@router.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(
    user: TokenData = Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    orchestrator=Depends(get_orchestrator),
):
    """获取会话列表

    Args:
        user: 当前登录用户
        page: 页码 (从 1 开始)
        page_size: 每页数量
        orchestrator: 编排引擎实例

    Returns:
        list[SessionInfo]: 会话信息列表 (仅返回当前用户的会话)
    """
    sessions = await orchestrator.list_sessions(user_id=user.user_id, page=page, page_size=page_size)
    return sessions


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user: TokenData = Depends(get_current_user),
    orchestrator=Depends(get_orchestrator),
):
    """删除会话

    删除会话及其所有对话历史和记忆。
    用户只能删除自己的会话。

    Args:
        session_id: 会话 ID
        user: 当前登录用户
        orchestrator: 编排引擎实例

    Returns:
        dict: 删除结果
    """
    await orchestrator.delete_session(session_id, user_id=user.user_id)
    return {"message": "Session deleted", "session_id": session_id}

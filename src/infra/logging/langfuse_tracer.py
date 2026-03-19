"""LangFuse 追踪器模块

提供 LLM 调用全链路追踪能力，包括:
1. 追踪每次 LLM 调用 (输入/输出/Token/延迟)
2. 关联到会话 (session_id)
3. 构建调用链路 (Trace -> Span -> Generation)
4. 成本估算
"""

import time
from typing import Any

import structlog

from src.infra.config.settings import get_settings

logger = structlog.get_logger()

_langfuse = None


class LangfuseConfig:
    """LangFuse 配置"""

    LANGFUSE_ENABLED: bool = False
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3000"


def init_langfuse():
    """初始化 LangFuse 客户端

    Returns:
        Langfuse | None: LangFuse 客户端实例，未启用则返回 None
    """
    global _langfuse
    settings = get_settings()

    if not getattr(settings, "LANGFUSE_ENABLED", False):
        logger.info("langfuse_disabled")
        return None

    try:
        from langfuse import Langfuse

        _langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        # 验证连接
        _langfuse.auth_check()
        logger.info("langfuse_connected", host=settings.LANGFUSE_HOST)
        return _langfuse
    except Exception as e:
        logger.warning("langfuse_init_failed", error=str(e))
        return None


def get_langfuse():
    """获取 LangFuse 单例

    Returns:
        Langfuse | None: LangFuse 实例
    """
    return _langfuse


class LLMTracer:
    """LLM 调用追踪器

    功能:
    1. 追踪每次 LLM 调用 (输入/输出/Token/延迟)
    2. 关联到会话 (session_id)
    3. 构建调用链路 (Trace -> Span -> Generation)
    4. 成本估算
    """

    def __init__(self, langfuse=None):
        """初始化追踪器

        Args:
            langfuse: 可选的 LangFuse 实例，默认使用全局单例
        """
        self.langfuse = langfuse or _langfuse

    def create_trace(
        self,
        session_id: str,
        user_id: str = "default",
        name: str = "chat_completion",
        metadata: dict | None = None,
    ) -> "TraceContext":
        """创建一个追踪上下文

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            name: 追踪名称
            metadata: 元数据

        Returns:
            TraceContext: 追踪上下文
        """
        if not self.langfuse:
            return NoOpTraceContext()

        trace = self.langfuse.trace(
            name=name,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )

        return TraceContext(trace=trace, langfuse=self.langfuse)

    def get_langchain_callback(
        self,
        session_id: str,
        user_id: str = "default",
    ):
        """获取 LangChain 回调处理器 (自动追踪 LLM 调用)

        Args:
            session_id: 会话 ID
            user_id: 用户 ID

        Returns:
            LangfuseCallbackHandler | None: LangChain 回调处理器
        """
        if not self.langfuse:
            return None

        try:
            from langfuse.callback import CallbackHandler as LangfuseCallbackHandler

            settings = get_settings()
            return LangfuseCallbackHandler(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
                session_id=session_id,
                user_id=user_id,
            )
        except ImportError:
            logger.warning("langfuse_callback_import_failed")
            return None


class TraceContext:
    """追踪上下文 - 管理 Span 生命周期"""

    def __init__(self, trace, langfuse):
        """初始化追踪上下文

        Args:
            trace: LangFuse Trace 对象
            langfuse: LangFuse 客户端
        """
        self.trace = trace
        self.langfuse = langfuse

    def span(self, name: str, **kwargs) -> "SpanContext":
        """创建子 Span

        Args:
            name: Span 名称
            **kwargs: 其他参数

        Returns:
            SpanContext: Span 上下文
        """
        span = self.trace.span(name=name, **kwargs)
        return SpanContext(span=span)

    def generation(self, name: str, **kwargs) -> "GenerationContext":
        """记录 LLM Generation

        Args:
            name: Generation 名称
            **kwargs: 其他参数

        Returns:
            GenerationContext: Generation 上下文
        """
        generation = self.trace.generation(name=name, **kwargs)
        return GenerationContext(generation=generation)

    def score(self, name: str, value: float, comment: str = ""):
        """记录评分

        Args:
            name: 评分名称
            value: 评分值 (0-1)
            comment: 评分注释
        """
        self.trace.score(name=name, value=value, comment=comment)

    def update(self, **kwargs):
        """更新 Trace 元数据

        Args:
            **kwargs: 要更新的元数据
        """
        self.trace.update(**kwargs)

    def flush(self):
        """刷新到 LangFuse 服务器"""
        self.langfuse.flush()


class SpanContext:
    """Span 上下文"""

    def __init__(self, span):
        self.span = span

    def end(self, **kwargs):
        """结束 Span

        Args:
            **kwargs: 结束时的额外参数
        """
        self.span.end(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.end()


class GenerationContext:
    """Generation 上下文"""

    def __init__(self, generation):
        self.generation = generation

    def end(self, **kwargs):
        """结束 Generation

        Args:
            **kwargs: 结束时的额外参数
        """
        self.generation.end(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.end()


class NoOpTraceContext:
    """空操作追踪上下文 (LangFuse 未启用时使用)"""

    def span(self, *args, **kwargs) -> "NoOpSpanContext":
        return NoOpSpanContext()

    def generation(self, *args, **kwargs) -> "NoOpGenerationContext":
        return NoOpGenerationContext()

    def score(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def flush(self):
        pass


class NoOpSpanContext:
    """空操作 Span 上下文"""

    def end(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class NoOpGenerationContext:
    """空操作 Generation 上下文"""

    def end(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

"""Structlog 日志配置 - 企业 QA 助手"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from src.infra.config.settings import get_settings


def add_app_info(logger: Any, method_name: str, event_dict: dict) -> dict:
    """向日志上下文中添加应用信息"""
    settings = get_settings()
    event_dict["app_name"] = settings.APP_NAME      # 应用名称
    event_dict["app_version"] = settings.APP_VERSION  # 应用版本
    event_dict["env"] = settings.ENV                # 运行环境
    return event_dict


def configure_logging() -> None:
    """配置 structlog - JSON 格式输出 + 请求上下文绑定"""

    settings = get_settings()

    # 根据 LOG_LEVEL 配置确定日志级别 (支持 DEBUG / INFO / WARNING / ERROR)
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # 共享处理器列表 (用于 stdlib 和 structlog)
    shared_processors: list[Processor] = [
        structlog.stdlib.add_log_level,              # 添加日志级别
        structlog.stdlib.add_logger_name,            # 添加日志器名称
        structlog.stdlib.PositionalArgumentsFormatter(),  # 格式化位置参数
        structlog.processors.TimeStamper(fmt="iso"), # 添加 ISO 格式时间戳
        structlog.processors.StackInfoRenderer(),   # 渲染堆栈信息
        structlog.processors.UnicodeDecoder(),       # Unicode 解码
        add_app_info,                                # 添加应用信息
    ]

    # 配置 structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.format_exc_info,    # 格式化异常信息
            # structlog.processors.JSONRenderer(),  # JSON 格式输出
            structlog.dev.ConsoleRenderer(),          # 开发环境易读格式
        ],
        wrapper_class=structlog.stdlib.BoundLogger,  # 包装器类
        context_class=dict,                           # 上下文类
        logger_factory=structlog.stdlib.LoggerFactory(),  # 日志器工厂
        cache_logger_on_first_use=True,               # 首次使用后缓存日志器
    )

    # 配置标准库 logging
    logging.basicConfig(
        format="%(message)s",   # 日志格式
        stream=sys.stdout,      # 输出到标准输出
        level=log_level,        # 日志级别
    )

    # 将第三方库的日志级别设置为 WARNING 以减少噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取配置好的日志器实例

    Args:
        name: 日志器名称，通常使用 __name__

    Returns:
        配置好的 structlog BoundLogger 实例
    """
    return structlog.get_logger(name)

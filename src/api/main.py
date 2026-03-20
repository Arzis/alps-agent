"""FastAPI 应用入口模块

定义 FastAPI 应用实例、生命周期管理和中间件配置。
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infra.config.settings import get_settings
from src.infra.database.postgres import init_postgres_pool, close_postgres_pool
from src.infra.database.redis_client import init_redis, close_redis
from src.infra.database.milvus_client import init_milvus
from src.infra.logging.logger import configure_logging
from src.api.middlewares.error_handler import register_exception_handlers
from src.api.middlewares.logging_middleware import RequestLoggingMiddleware
from src.api.routers import auth, chat, documents, health, evaluation

import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    在应用启动时初始化所有依赖:
    - 日志配置
    - 数据库连接池
    - Redis 客户端
    - Milvus 客户端
    - 编排引擎

    在应用关闭时清理资源。
    """
    settings = get_settings()

    # ============================================================
    # 启动阶段
    # ============================================================
    # 配置日志
    configure_logging()
    logger.info("application_starting", env=settings.ENV)

    # 初始化 PostgreSQL 连接池
    pg_pool = await init_postgres_pool()
    app.state.pg_pool = pg_pool  # 存储到 app.state 供依赖使用
    logger.info("postgres_connected", pool_size=settings.POSTGRES_POOL_MAX)

    # 初始化 Redis 客户端
    redis_client = await init_redis()
    logger.info("redis_connected")

    # 初始化 Milvus 客户端
    milvus_client = init_milvus()
    logger.info("milvus_connected")

    # 初始化编排引擎
    from src.core.orchestrator.engine import init_orchestrator
    orchestrator = await init_orchestrator(
        pg_pool=pg_pool,
        redis_client=redis_client,
        milvus_client=milvus_client,
        settings=settings,
    )
    app.state.orchestrator = orchestrator
    logger.info("orchestrator_initialized")

    logger.info("application_started", version=settings.APP_VERSION)

    # ============================================================
    # 应用运行中 (yield 后的代码在关闭时执行)
    # ============================================================
    yield

    # ============================================================
    # 关闭阶段
    # ============================================================
    logger.info("application_shutting_down")

    # 关闭数据库连接
    await close_postgres_pool()
    await close_redis()

    logger.info("application_stopped")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例

    配置:
    - 生命周期管理器
    - CORS 中间件
    - 请求日志中间件
    - 异常处理器
    - 路由注册

    Returns:
        FastAPI: 配置好的 FastAPI 应用实例
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,                    # 应用标题
        version=settings.APP_VERSION,               # 应用版本
        lifespan=lifespan,                        # 生命周期管理
        docs_url="/docs" if settings.DEBUG else None,   # Swagger UI (仅开发环境)
        redoc_url="/redoc" if settings.DEBUG else None,  # ReDoc (仅开发环境)
    )

    # ============================================================
    # 中间件配置
    # ============================================================
    # CORS 中间件 - 允许跨域请求
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else ["https://your-domain.com"],
        allow_credentials=True,                   # 允许携带凭证
        allow_methods=["*"],                      # 允许所有 HTTP 方法
        allow_headers=["*"],                      # 允许所有请求头
    )

    # 请求日志中间件
    app.add_middleware(RequestLoggingMiddleware)

    # ============================================================
    # 异常处理器注册
    # ============================================================
    register_exception_handlers(app)

    # ============================================================
    # 路由注册
    # ============================================================
    # 健康检查路由 (无前缀)
    app.include_router(health.router)
    # Auth 路由 (带 /api/v1 前缀)
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    # Chat 路由 (带 /api/v1 前缀)
    app.include_router(chat.router, prefix=settings.API_PREFIX)
    # Documents 路由 (带 /api/v1 前缀)
    app.include_router(documents.router, prefix=settings.API_PREFIX)
    # Evaluation 路由 (带 /api/v1 前缀)
    app.include_router(evaluation.router, prefix=settings.API_PREFIX)

    return app


# 创建应用实例
app = create_app()

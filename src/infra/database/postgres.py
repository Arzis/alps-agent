"""PostgreSQL 数据库连接池管理模块"""

import asyncpg
from src.infra.config.settings import get_settings

# 全局连接池变量
_pool: asyncpg.Pool | None = None


async def init_postgres_pool() -> asyncpg.Pool:
    """初始化 PostgreSQL 连接池

    创建异步连接池，用于管理数据库连接。
    连接池可以减少频繁创建/销毁连接的开销。

    Returns:
        asyncpg.Pool: PostgreSQL 连接池实例
    """
    global _pool
    settings = get_settings()
    _pool = await asyncpg.create_pool(
        dsn=settings.POSTGRES_URL,        # 数据库连接字符串
        min_size=settings.POSTGRES_POOL_MIN,  # 最小连接数
        max_size=settings.POSTGRES_POOL_MAX,  # 最大连接数
        command_timeout=60,                  # 命令超时时间(秒)
    )
    return _pool


async def get_postgres_pool() -> asyncpg.Pool:
    """获取 PostgreSQL 连接池

    Returns:
        asyncpg.Pool: PostgreSQL 连接池实例

    Raises:
        RuntimeError: 如果连接池未初始化
    """
    if _pool is None:
        raise RuntimeError("PostgreSQL pool not initialized. Call init_postgres_pool() first.")
    return _pool


async def close_postgres_pool() -> None:
    """关闭 PostgreSQL 连接池

    在应用关闭时调用，释放所有连接资源。
    """
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

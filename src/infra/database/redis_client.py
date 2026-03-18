"""Redis 客户端连接管理模块"""

import redis.asyncio as aioredis
from src.infra.config.settings import get_settings

# 全局 Redis 客户端变量
_redis: aioredis.Redis | None = None


async def init_redis() -> aioredis.Redis:
    """初始化 Redis 客户端连接

    创建 Redis 异步客户端，用于缓存和会话管理。

    Returns:
        aioredis.Redis: Redis 异步客户端实例
    """
    global _redis
    settings = get_settings()
    _redis = aioredis.from_url(
        settings.REDIS_URL,                    # Redis 连接 URL
        encoding="utf-8",                       # 响应编码
        decode_responses=True,                  # 自动解码响应为字符串
        max_connections=settings.REDIS_POOL_MAX,  # 最大连接数
    )
    # 验证连接
    await _redis.ping()
    return _redis


async def get_redis() -> aioredis.Redis:
    """获取 Redis 客户端实例

    Returns:
        aioredis.Redis: Redis 异步客户端实例

    Raises:
        RuntimeError: 如果 Redis 客户端未初始化
    """
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis


async def close_redis() -> None:
    """关闭 Redis 连接

    在应用关闭时调用，释放连接资源。
    """
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None

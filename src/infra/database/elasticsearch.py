"""Elasticsearch 异步客户端模块

提供 Elasticsearch 异步连接管理，支持 BM25 稀疏检索。
"""

import structlog

from src.infra.config.settings import get_settings

logger = structlog.get_logger()

_es_client = None


async def init_elasticsearch() -> "AsyncElasticsearch":
    """初始化 Elasticsearch 异步客户端

    Returns:
        AsyncElasticsearch: ES 异步客户端实例
    """
    global _es_client

    try:
        from elasticsearch import AsyncElasticsearch

        settings = get_settings()
        _es_client = AsyncElasticsearch(
            hosts=[settings.ELASTICSEARCH_URL],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )
        # 验证连接
        info = await _es_client.info()
        logger.info("elasticsearch_connected", version=info["version"]["number"])
        return _es_client
    except ImportError:
        logger.warning("elasticsearch_package_not_installed")
        raise
    except Exception as e:
        logger.error("elasticsearch_connection_failed", error=str(e))
        raise


async def get_elasticsearch() -> "AsyncElasticsearch":
    """获取 Elasticsearch 客户端单例

    Returns:
        AsyncElasticsearch: ES 异步客户端实例
    """
    global _es_client
    if _es_client is None:
        _es_client = await init_elasticsearch()
    return _es_client


async def close_elasticsearch() -> None:
    """关闭 Elasticsearch 连接"""
    global _es_client
    if _es_client:
        await _es_client.close()
        _es_client = None
        logger.info("elasticsearch_closed")


# 类型注解延迟导入，避免循环依赖
from elasticsearch import AsyncElasticsearch

__all__ = [
    "init_elasticsearch",
    "get_elasticsearch",
    "close_elasticsearch",
]

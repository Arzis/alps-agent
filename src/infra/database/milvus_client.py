"""Milvus 向量数据库客户端管理模块"""

from pymilvus import MilvusClient as _MilvusClient
from src.infra.config.settings import get_settings

# 全局 Milvus 客户端变量
_client: _MilvusClient | None = None


def init_milvus() -> _MilvusClient:
    """初始化 Milvus 客户端

    Milvus 是一个向量数据库，用于存储和检索文档嵌入向量。

    Returns:
        _MilvusClient: Milvus 客户端实例
    """
    global _client
    settings = get_settings()
    _client = _MilvusClient(
        uri=settings.MILVUS_URI,              # Milvus 服务器 URI
        token=settings.MILVUS_TOKEN or None,  # 认证令牌 (可选)
        db_name=settings.MILVUS_DB_NAME,      # 数据库名称
    )
    return _client


def get_milvus() -> _MilvusClient:
    """获取 Milvus 客户端实例

    Returns:
        _MilvusClient: Milvus 客户端实例

    Raises:
        RuntimeError: 如果 Milvus 客户端未初始化
    """
    if _client is None:
        raise RuntimeError("Milvus client not initialized. Call init_milvus() first.")
    return _client

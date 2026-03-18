"""Milvus 向量数据库客户端管理模块"""

from pymilvus import MilvusClient as _MilvusClient, CollectionSchema, FieldSchema, DataType
from src.infra.config.settings import get_settings

# 全局 Milvus 客户端变量
_client: _MilvusClient | None = None


def init_milvus() -> _MilvusClient:
    """初始化 Milvus 客户端

    Milvus 是一个向量数据库，用于存储和检索文档嵌入向量。
    初始化时会确保知识库 Collection 存在，如不存在则创建。

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

    # 确保 Collection 存在
    _ensure_collection(_client, settings)

    return _client


def _ensure_collection(client: _MilvusClient, settings) -> None:
    """确保 Milvus Collection 存在，如不存在则创建

    Args:
        client: Milvus 客户端实例
        settings: 应用配置
    """
    collection_name = settings.MILVUS_COLLECTION_NAME

    # 如果 Collection 已存在，直接返回
    if client.has_collection(collection_name):
        return

    # 定义 Collection Schema
    schema = CollectionSchema(
        fields=[
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),  # 主键 (chunk ID)
            FieldSchema("doc_id", DataType.VARCHAR, max_length=64),  # 文档 ID
            FieldSchema("chunk_index", DataType.INT64),  # 块索引
            FieldSchema("content", DataType.VARCHAR, max_length=65535),  # 文档内容
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),  # 向量
            FieldSchema("doc_title", DataType.VARCHAR, max_length=512),  # 文档标题
            FieldSchema("collection", DataType.VARCHAR, max_length=128),  # 集合名称
            FieldSchema("created_at", DataType.INT64),  # 创建时间戳
        ],
        description="Knowledge base document chunks",  # 知识库文档块
    )

    # 创建 Collection
    client.create_collection(
        collection_name=collection_name,
        schema=schema,
    )

    # 配置向量索引 (HNSW)
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",  # 向量字段
        index_type="HNSW",  # HNSW 索引
        metric_type="COSINE",  # 余弦相似度
        params={"M": 16, "efConstruction": 256},  # HNSW 参数
    )
    index_params.add_index(
        field_name="doc_id",  # 文档 ID 字段
        index_type="Trie",  # Trie 索引用于快速过滤
    )

    # 创建索引
    client.create_index(
        collection_name=collection_name,
        index_params=index_params,
    )


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

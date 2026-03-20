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

    Note:
        当检测到向量维度与现有 collection 不匹配时：
        - 如果是新部署，可以删除旧 collection 重建
        - 如果有重要数据，应该先导出再切换配置
        当前策略：直接重建（可能丢失数据），后续可扩展为迁移逻辑
    """
    collection_name = settings.MILVUS_COLLECTION_NAME

    # 如果 Collection 存在，检查维度是否匹配，不匹配则删除重建
    if client.has_collection(collection_name):
        coll_info = client.describe_collection(collection_name=collection_name)
        fields = {f["name"]: f for f in coll_info.get("fields", [])}
        emb_field = fields.get("embedding", {})
        # Milvus 返回的维度在 params.dim 里，不是顶层 dimension 字段
        existing_dim = emb_field.get("params", {}).get("dim", 0)
        expected_dim = settings.ACTIVE_EMBEDDING_DIMENSION

        if existing_dim != expected_dim:
            # 维度不匹配：删除旧 collection
            # 注意：这会丢失所有已导入的向量数据！
            # 切换 embedding provider 时必须重新导入文档
            client.drop_collection(collection_name=collection_name)
        else:
            return  # 维度匹配，保留现有 collection

    # 定义 Collection Schema
    schema = CollectionSchema(
        fields=[
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),  # 主键 (chunk ID)
            FieldSchema("doc_id", DataType.VARCHAR, max_length=64),  # 文档 ID
            FieldSchema("chunk_index", DataType.INT64),  # 块索引
            FieldSchema("content", DataType.VARCHAR, max_length=65535),  # 文档内容
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.ACTIVE_EMBEDDING_DIMENSION),  # 向量
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

    # 加载 Collection 到内存 (必须在 create_index 之后)
    client.load_collection(collection_name=collection_name)


def get_milvus() -> _MilvusClient:
    """获取 Milvus 客户端实例

    如果客户端未初始化，则重新初始化（支持懒加载）。

    Returns:
        _MilvusClient: Milvus 客户端实例
    """
    global _client
    if _client is None:
        # 懒加载初始化
        return init_milvus()
    return _client

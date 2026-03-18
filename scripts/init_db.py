"""数据库初始化脚本 - 创建 Milvus Collection + 验证数据库连接"""

import asyncio
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncpg                           # PostgreSQL 异步驱动
import redis.asyncio as redis             # Redis 异步客户端
from pymilvus import CollectionSchema, FieldSchema, DataType  # Milvus schema 定义

from src.infra.config.settings import get_settings
from src.infra.logging.logger import configure_logging, get_logger


# 初始化日志配置
configure_logging()
logger = get_logger(__name__)


async def init_milvus() -> None:
    """初始化 Milvus Collection - 创建知识库向量索引"""
    settings = get_settings()

    from pymilvus import MilvusClient

    # 创建 Milvus 客户端
    client = MilvusClient(uri=settings.MILVUS_URI)
    collection_name = settings.MILVUS_COLLECTION_NAME

    # 检查 Collection 是否已存在
    if client.has_collection(collection_name):
        logger.info("collection_already_exists", collection=collection_name)
        return

    # ============================================================
    # 创建 Collection Schema (定义字段结构)
    # ============================================================
    schema = CollectionSchema(
        fields=[
            # 主键 ID
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
            # 文档 ID (用于关联原始文档)
            FieldSchema("doc_id", DataType.VARCHAR, max_length=64),
            # 文档块索引 (一个文档被分割成多个块)
            FieldSchema("chunk_index", DataType.INT64),
            # 文档块内容 (文本内容)
            FieldSchema("content", DataType.VARCHAR, max_length=65535),
            # 向量嵌入 (用于相似度搜索)
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),
            # 文档标题
            FieldSchema("doc_title", DataType.VARCHAR, max_length=512),
            # 所属知识库集合
            FieldSchema("collection", DataType.VARCHAR, max_length=128),
            # 创建时间戳
            FieldSchema("created_at", DataType.INT64),
        ],
        description="Knowledge base document chunks",  # 知识库文档块
    )

    # 创建 Collection
    client.create_collection(
        collection_name=collection_name,
        schema=schema,
    )

    # ============================================================
    # 创建向量索引 (HNSW 算法)
    # HNSW = Hierarchical Navigable Small World
    # 优点: 高召回率、查询速度快
    # ============================================================
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",           # 索引字段: 向量嵌入
        index_type="HNSW",                 # 索引类型: HNSW
        metric_type="COSINE",              # 距离度量: 余弦相似度
        params={"M": 16, "efConstruction": 256},  # HNSW 参数
    )
    # 为 doc_id 和 collection 字段创建 Trie 索引 (用于精确匹配)
    index_params.add_index(field_name="doc_id", index_type="Trie")
    index_params.add_index(field_name="collection", index_type="Trie")

    # 执行索引创建
    client.create_index(
        collection_name=collection_name,
        index_params=index_params,
    )

    # 将 Collection 加载到内存 (Milvus 必须先加载才能查询)
    client.load_collection(collection_name)

    logger.info("collection_created_successfully", collection=collection_name)


async def verify_postgres() -> bool:
    """验证 PostgreSQL 数据库连接"""
    settings = get_settings()
    try:
        # 建立异步连接
        conn = await asyncpg.connect(settings.POSTGRES_URL)
        # 执行版本查询
        version = await conn.fetchval("SELECT version()")
        # 关闭连接
        await conn.close()
        logger.info("postgres_connected", version=version[:80])
        return True
    except Exception as e:
        logger.error("postgres_connection_failed", error=str(e))
        return False


async def verify_redis() -> bool:
    """验证 Redis 连接"""
    settings = get_settings()
    try:
        # 创建 Redis 异步客户端
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD.get_secret_value() if settings.REDIS_PASSWORD else None,
        )
        # Ping 测试连接
        await r.ping()
        # 关闭连接
        await r.aclose()
        logger.info("redis_connected")
        return True
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        return False


async def verify_milvus() -> bool:
    """验证 Milvus 向量数据库连接"""
    settings = get_settings()
    try:
        from pymilvus import MilvusClient

        client = MilvusClient(uri=settings.MILVUS_URI)
        # 检查连接状态
        client.check_connectivity()
        logger.info("milvus_connected", uri=settings.MILVUS_URI)
        return True
    except Exception as e:
        logger.error("milvus_connection_failed", error=str(e))
        return False


async def main() -> None:
    """主初始化函数 - 初始化 Milvus 并验证所有数据库连接"""
    logger.info("starting_database_initialization")

    # 初始化 Milvus Collection
    await init_milvus()

    # 并行验证所有数据库连接
    results = await asyncio.gather(
        verify_postgres(),  # PostgreSQL
        verify_redis(),     # Redis
        verify_milvus(),    # Milvus
    )

    # 检查所有连接是否成功
    if all(results):
        logger.info("all_database_connections_verified")
    else:
        logger.warning("some_database_connections_failed")
        sys.exit(1)  # 退出码 1 表示初始化失败


if __name__ == "__main__":
    asyncio.run(main())

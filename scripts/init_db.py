"""Database initialization script - Create Milvus Collection + Verify Connections."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncpg
import redis.asyncio as redis
from pymilvus import CollectionSchema, FieldSchema, DataType

from src.infra.config.settings import get_settings
from src.infra.logging.logger import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


async def init_milvus() -> None:
    """Initialize Milvus Collection with HNSW index."""
    settings = get_settings()

    from pymilvus import MilvusClient

    client = MilvusClient(uri=settings.MILVUS_URI)
    collection_name = settings.MILVUS_COLLECTION_NAME

    # Check if collection already exists
    if client.has_collection(collection_name):
        logger.info("collection_already_exists", collection=collection_name)
        return

    # Create Collection Schema
    schema = CollectionSchema(
        fields=[
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema("doc_id", DataType.VARCHAR, max_length=64),
            FieldSchema("chunk_index", DataType.INT64),
            FieldSchema("content", DataType.VARCHAR, max_length=65535),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),
            FieldSchema("doc_title", DataType.VARCHAR, max_length=512),
            FieldSchema("collection", DataType.VARCHAR, max_length=128),
            FieldSchema("created_at", DataType.INT64),
        ],
        description="Knowledge base document chunks",
    )

    client.create_collection(
        collection_name=collection_name,
        schema=schema,
    )

    # Create vector index (HNSW)
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="HNSW",
        metric_type="COSINE",
        params={"M": 16, "efConstruction": 256},
    )
    index_params.add_index(field_name="doc_id", index_type="Trie")
    index_params.add_index(field_name="collection", index_type="Trie")

    client.create_index(
        collection_name=collection_name,
        index_params=index_params,
    )

    # Load collection into memory
    client.load_collection(collection_name)

    logger.info("collection_created_successfully", collection=collection_name)


async def verify_postgres() -> bool:
    """Verify PostgreSQL connection."""
    settings = get_settings()
    try:
        conn = await asyncpg.connect(settings.POSTGRES_URL)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        logger.info("postgres_connected", version=version[:80])
        return True
    except Exception as e:
        logger.error("postgres_connection_failed", error=str(e))
        return False


async def verify_redis() -> bool:
    """Verify Redis connection."""
    settings = get_settings()
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD.get_secret_value() if settings.REDIS_PASSWORD else None,
        )
        await r.ping()
        await r.aclose()
        logger.info("redis_connected")
        return True
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        return False


async def verify_milvus() -> bool:
    """Verify Milvus connection."""
    settings = get_settings()
    try:
        from pymilvus import MilvusClient

        client = MilvusClient(uri=settings.MILVUS_URI)
        client.check_connectivity()
        logger.info("milvus_connected", uri=settings.MILVUS_URI)
        return True
    except Exception as e:
        logger.error("milvus_connection_failed", error=str(e))
        return False


async def main() -> None:
    """Main initialization function."""
    logger.info("starting_database_initialization")

    # Initialize Milvus collection
    await init_milvus()

    # Verify all connections
    results = await asyncio.gather(
        verify_postgres(),
        verify_redis(),
        verify_milvus(),
    )

    if all(results):
        logger.info("all_database_connections_verified")
    else:
        logger.warning("some_database_connections_failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

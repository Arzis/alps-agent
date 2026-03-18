"""健康检查路由 - 检查服务依赖的健康状态"""

from fastapi import APIRouter
from src.infra.config.settings import get_settings
from src.infra.database.postgres import get_postgres_pool
from src.infra.database.redis_client import get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """基础健康检查

    返回服务的基本状态，用于负载均衡器和健康探测。
    """
    return {
        "status": "ok",
        "version": get_settings().APP_VERSION
    }


@router.get("/health/detail")
async def detailed_health_check():
    """详细健康检查

    检查所有依赖服务 (PostgreSQL, Redis, Milvus) 的连接状态。
    用于 Kubernetes liveness/readiness probes 和运维监控。
    """
    checks = {}

    # ============================================================
    # PostgreSQL 健康检查
    # ============================================================
    try:
        pool = await get_postgres_pool()
        # 执行简单查询验证连接
        await pool.fetchval("SELECT 1")
        checks["postgres"] = {"status": "healthy"}
    except Exception as e:
        checks["postgres"] = {"status": "unhealthy", "error": str(e)}

    # ============================================================
    # Redis 健康检查
    # ============================================================
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # ============================================================
    # Milvus 健康检查
    # ============================================================
    try:
        from src.infra.database.milvus_client import get_milvus
        client = get_milvus()
        client.list_collections()
        checks["milvus"] = {"status": "healthy"}
    except Exception as e:
        checks["milvus"] = {"status": "unhealthy", "error": str(e)}

    # 判断总体状态
    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    return {
        "status": "healthy" if all_healthy else "degraded",  # degraded = 部分依赖不健康
        "checks": checks,
    }

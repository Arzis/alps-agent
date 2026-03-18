"""健康检查路由 - 检查服务依赖的健康状态"""

import time
from dataclasses import dataclass

from fastapi import APIRouter
from src.infra.config.settings import get_settings
from src.infra.database.postgres import get_postgres_pool
from src.infra.database.redis_client import get_redis

router = APIRouter(tags=["Health"])


@dataclass
class DependencyCheck:
    """依赖检查结果"""
    status: str
    latency_ms: float | None = None
    error: str | None = None


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

    检查所有依赖服务 (PostgreSQL, Redis, Milvus) 的连接状态和响应时间。
    用于 Kubernetes liveness/readiness probes 和运维监控。
    """
    checks: dict[str, DependencyCheck] = {}

    # ============================================================
    # PostgreSQL 健康检查
    # ============================================================
    try:
        start = time.perf_counter()
        pool = await get_postgres_pool()
        await pool.fetchval("SELECT 1")
        latency_ms = (time.perf_counter() - start) * 1000
        checks["postgres"] = DependencyCheck(status="healthy", latency_ms=latency_ms)
    except Exception as e:
        checks["postgres"] = DependencyCheck(
            status="unhealthy",
            error=str(e),
        )

    # ============================================================
    # Redis 健康检查
    # ============================================================
    try:
        start = time.perf_counter()
        redis_client = await get_redis()
        await redis_client.ping()
        latency_ms = (time.perf_counter() - start) * 1000
        checks["redis"] = DependencyCheck(status="healthy", latency_ms=latency_ms)
    except Exception as e:
        checks["redis"] = DependencyCheck(status="unhealthy", error=str(e))

    # ============================================================
    # Milvus 健康检查
    # ============================================================
    try:
        start = time.perf_counter()
        from src.infra.database.milvus_client import get_milvus
        client = get_milvus()
        client.list_collections()
        latency_ms = (time.perf_counter() - start) * 1000
        checks["milvus"] = DependencyCheck(status="healthy", latency_ms=latency_ms)
    except Exception as e:
        checks["milvus"] = DependencyCheck(status="unhealthy", error=str(e))

    # 判断总体状态
    all_healthy = all(c.status == "healthy" for c in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": get_settings().APP_VERSION,
        "checks": {
            name: {
                "status": check.status,
                "latency_ms": check.latency_ms,
                "error": check.error,
            }
            for name, check in checks.items()
        },
    }

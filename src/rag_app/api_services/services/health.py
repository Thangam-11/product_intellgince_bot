from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.rag_app.core_app.retrieval import get_retriever
from src.rag_app.configure.config_settings import get_settings
from src.rag_app.utils.logger import get_logger
import time

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)

# Track app start time for uptime metric
_start_time = time.time()

# Simple in-memory counters (use Redis/CloudWatch in production)
_counters = {"requests": 0, "errors": 0, "cache_hits": 0}


def increment(counter: str):
    _counters[counter] = _counters.get(counter, 0) + 1


@router.get("/health")
async def health():
    """
    Liveness probe — 'Is the process alive?'
    Called by ECS every 30 seconds.
    If this returns non-200, ECS kills and restarts the container.
    Rules:
      - Must be FAST (< 100ms)
      - Must NOT call external services (AstraDB, OpenAI)
      - Must NOT require authentication
    """
    return JSONResponse({
        "status": "ok",
        "environment": get_settings().environment,
        "uptime_seconds": round(time.time() - _start_time, 1),
    })


@router.get("/ready")
async def ready():
    """
    Readiness probe — 'Is the app ready to receive traffic?'
    Called by the load balancer before routing requests here.
    Unlike /health, this DOES check external dependencies.
    """
    db_ok = get_retriever().check_connection()
    if not db_ok:
        logger.warning("Readiness check failed — AstraDB unreachable")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "reason": "AstraDB connection failed",
            },
        )
    return JSONResponse({
        "status": "ready",
        "db": "connected",
    })


@router.get("/metrics")
async def metrics():
    """
    Basic application metrics.
    In production, replace with Prometheus metrics or ship to CloudWatch.
    """
    return JSONResponse({
        "uptime_seconds": round(time.time() - _start_time, 1),
        "requests_total": _counters["requests"],
        "errors_total": _counters["errors"],
        "cache_hits_total": _counters["cache_hits"],
        "error_rate": (
            _counters["errors"] / max(_counters["requests"], 1)
        ),
    })
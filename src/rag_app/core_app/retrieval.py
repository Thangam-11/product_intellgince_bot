from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.core.retrieval import get_retriever          # ✅ singleton
from app.api_services.schemas.chat import HealthResponse, ReadyResponse  # ✅ typed responses
from app.config.settings import get_settings
from app.utils.logger import get_logger
import time

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)

_start_time = time.time()

# Simple in-memory counters (use Redis/CloudWatch in production)
_counters = {"requests": 0, "errors": 0, "cache_hits": 0}


def increment(counter: str):
    _counters[counter] = _counters.get(counter, 0) + 1


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Liveness probe — 'Is the process alive?'
    Called by ECS every 30 seconds.
    Rules:
      - Must be FAST (< 100ms)
      - Must NOT call external services (AstraDB, Redis)
      - Must NOT require authentication
    """
    return HealthResponse(
        status="ok",
        environment=get_settings().environment,
    )


@router.get("/ready", response_model=ReadyResponse)
async def ready():
    """
    Readiness probe — 'Is the app ready to receive traffic?'
    Called by load balancer before routing requests here.
    If non-200, load balancer stops sending traffic to this instance.
    Unlike /health, this DOES check external dependencies.
    """
    db_ok = get_retriever().check_connection()   # ✅ singleton

    if not db_ok:
        logger.warning("Readiness check failed — AstraDB unreachable")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "db": "unavailable",
            },
        )

    return ReadyResponse(
        status="ready",
        db="connected",
    )


@router.get("/metrics")
async def metrics():
    """
    Basic application metrics.
    In production, replace with Prometheus or ship to CloudWatch.
    """
    return JSONResponse({
        "uptime_seconds": round(time.time() - _start_time, 1),
        "requests_total": _counters["requests"],
        "errors_total": _counters["errors"],
        "cache_hits_total": _counters["cache_hits"],
        "error_rate": round(
            _counters["errors"] / max(_counters["requests"], 1), 4
        ),
    })
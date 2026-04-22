from fastapi import Security, HTTPException, Request
from fastapi.security import APIKeyHeader
from rag_app.configure.config_settings import get_settings
from rag_app.utils.logger import get_logger

logger = get_logger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    request: Request,
    api_key: str = Security(API_KEY_HEADER),
):
    settings = get_settings()

    # ✅ Skip auth in development + testing
    if settings.environment in ["development", "testing"]:
        return

    if not api_key:
        logger.warning(
            "Missing API key",
            extra={"request_id": getattr(request.state, "request_id", "unknown")},
        )
        raise HTTPException(status_code=403, detail="Missing API key")

    if api_key != settings.api_key:
        logger.warning(
            "Invalid API key attempt",
            extra={"request_id": getattr(request.state, "request_id", "unknown")},
        )
        raise HTTPException(status_code=403, detail="Invalid API key")
from fastapi import Security, HTTPException, Request
from fastapi.security import APIKeyHeader
from src.rag_app.configure.config_settings import get_settings
from src.rag_app.utils.logger import get_logger

logger = get_logger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    request: Request,
    api_key: str = Security(API_KEY_HEADER),
):
    """
    FastAPI dependency for API key authentication.

    Usage in routes:
        @router.post("/get", dependencies=[Depends(verify_api_key)])

    Behavior:
      - In development mode: auth is SKIPPED (easy local dev)
      - In staging/production: X-API-Key header is required and validated
      - Wrong/missing key → 403 Forbidden with clear message

    Why skip in development?
      - Local dev should be friction-free
      - You don't want to manage API keys in .env just to test locally
      - The environment variable ENVIRONMENT=development enables this bypass
    """
    settings = get_settings()

    # Skip auth in local development
    if settings.environment == "development":
        return

    if not api_key:
        logger.warning(
            "Missing API key",
            extra={"request_id": getattr(request.state, "request_id", "unknown")},
        )
        raise HTTPException(
            status_code=403,
            detail="Missing X-API-Key header. "
                   "Include your API key in the request header.",
        )

    if api_key != settings.api_key:
        logger.warning(
            "Invalid API key attempt",
            extra={"request_id": getattr(request.state, "request_id", "unknown")},
        )
        raise HTTPException(
            status_code=403,
            detail="Invalid API key.",
        )

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from src.rag_app.logger_exceptions.exception import CustomerproductinteglligenceException
from src.rag_app.utils.logger import get_logger 

logger = get_logger(__name__)


def register_exception_handlers(app):
    """
    Register all global exception handlers with the FastAPI app.
    Call this once in main.py during app setup.

    Without these handlers:
      - CustomerproductinteglligenceException → FastAPI returns ugly 500 with full traceback exposed
      - RateLimitExceeded → Returns 429 but with no structured JSON body
      - Unhandled exceptions → No request_id in response, impossible to trace in logs
    """

    @app.exception_handler(CustomerproductinteglligenceException)
    async def bot_exception_handler(
        request: Request, exc: CustomerproductinteglligenceException
    ):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            "CustomerproductinteglligenceException",
            extra={
                "request_id": request_id,
                "error": str(exc),
                "trace": exc.full_trace(),
            },
        )
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service temporarily unavailable. Please try again.",
                "request_id": request_id,
            },
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too many requests. Please wait before sending another message.",
                "retry_after": "60 seconds",
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            "Unhandled exception",
            extra={"request_id": request_id, "error": str(exc)},
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "An unexpected error occurred.",
                "request_id": request_id,
            },
        )

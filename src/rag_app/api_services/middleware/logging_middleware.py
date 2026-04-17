import uuid
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from rag_app.utils.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Runs on EVERY incoming request before route handlers.

    What it does:
      1. Generates a unique UUID for the request
      2. Attaches it to request.state.request_id
      3. Logs request start with method, path, client IP
      4. Logs request end with status code and duration
      5. Adds X-Request-ID header to every response

    Why request_id matters:
      - A single user action triggers many log lines
        (middleware → auth → chain → retriever → LLM → response)
      - Without request_id, you cannot connect these lines in CloudWatch
      - With request_id, one CloudWatch Insights query shows the full trace:
        filter request_id = "abc-123"
    """

    async def dispatch(self, request: Request, call_next):
        # Generate unique ID for this request
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Attach request_id to response header so clients can use it
        # for support tickets: "My request ID was abc-123, please check logs"
        response.headers["X-Request-ID"] = request_id
        return response

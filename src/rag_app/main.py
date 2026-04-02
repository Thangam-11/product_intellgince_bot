import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from src.rag_app.configure.config_settings import get_settings
from src.rag_app.api_services.services.router import router
from src.rag_app.api_services.middleware.logging_middleware import RequestLoggingMiddleware
from src.rag_app.api_services.middleware.rate_limit import get_limiter
from src.rag_app.logger_exceptions.handlers import register_exception_handlers
from src.rag_app.cache_layer.redis_cache import setup_cache
from src.rag_app.core_app.model_loader import get_model_loader
from src.rag_app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Customer Product Intelligence Bot",
        description="AI-powered e-commerce product intelligence using RAG",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
    )

    # ── Middleware ──
    app.add_middleware(RequestLoggingMiddleware)

    allowed_origins = (
        ["*"] if settings.environment == "development"
        else ["https://yourdomain.com"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # ── Rate limiter ──
    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Exception handlers ──
    register_exception_handlers(app)

    # ── API Routes ──
    app.include_router(router)

    # ── Serve frontend ──
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse("static/index.html")

    # ── Startup ──
    @app.on_event("startup")
    async def startup():
        logger.info("Starting up", extra={"environment": settings.environment})
        embeddings = get_model_loader().load_embeddings()
        cache_ok = setup_cache(embeddings)
        logger.info("Cache setup", extra={"cache_enabled": cache_ok})

    # ── Shutdown ──
    @app.on_event("shutdown")
    async def shutdown():
        logger.info("Shutting down gracefully")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "src.rag_app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        workers=1 if settings.environment == "development" else 4,
    )
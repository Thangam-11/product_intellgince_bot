import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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

BASE_DIR = Path(__file__).resolve().parent       # → src/rag_app/
ROOT_DIR = BASE_DIR.parent.parent                # → customer_product_intelligence-bot/

templates = Jinja2Templates(directory=ROOT_DIR / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    logger.info(
        "Starting up",
        extra={
            "environment": settings.environment,
            "host": "0.0.0.0",
            "port": settings.port,
        },
    )
    try:
        embeddings = get_model_loader().load_embeddings()
    except Exception as e:
        logger.critical("Failed to load embeddings — aborting startup", exc_info=e)
        raise

    cache_ok = setup_cache(embeddings)
    logger.info("Cache setup", extra={"cache_enabled": cache_ok})

    yield

    logger.info("Shutting down gracefully")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Customer Product Intelligence Bot",
        description="AI-powered e-commerce product intelligence using RAG",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # Store settings on app state so lifespan and routes can access them
    app.state.settings = settings

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=(
            ["*"] if settings.environment == "development"
            else ["https://yourdomain.com"]
        ),
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    register_exception_handlers(app)
    app.include_router(router)

    app.mount(
        "/static",
        StaticFiles(directory=ROOT_DIR / "static"),
        name="static",
    )

    return app


app = create_app()


@app.get("/", include_in_schema=False)
async def serve_frontend(request: Request):
    return templates.TemplateResponse(request=request, name="chat.html")


if __name__ == "__main__":
    _settings = get_settings()
    uvicorn.run(
        "src.rag_app.main:app",
        host="0.0.0.0",
        port=_settings.port,
        reload=_settings.environment == "development",
        
        workers=1 if _settings.environment == "development" else 4,
    )
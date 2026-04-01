import redis
import langchain
from langchain_community.cache import RedisSemanticCache
from src.rag_app.configure.config_settings import get_settings
from src.rag_app.utils.logger import get_logger

logger = get_logger(__name__)


def setup_cache(embeddings) -> bool:
    """
    Configures LangChain's global semantic cache backed by Redis.

    How semantic cache works:
      - Normal cache: "best headphones" ≠ "top headphones" → cache MISS
      - Semantic cache: "best headphones" ≈ "top headphones" → cache HIT
      - Uses embedding similarity (score_threshold=0.2) to match queries
      - Expected cost reduction: 40-60% on LLM API spend

    Why Redis (not in-memory)?
      - In-memory cache is per-container — useless with multiple ECS instances
      - Redis is shared across all containers
      - Redis persists across container restarts

    Returns:
        True if cache setup succeeded, False if Redis is unavailable.
        App continues working without cache — just slower and more expensive.
    """
    settings = get_settings()

    try:
        # Test Redis connectivity before setting up cache
        client = redis.from_url(
            settings.redis_url,         # ✅ from settings, not hardcoded
            socket_connect_timeout=2,
        )
        client.ping()

        redis_cache = RedisSemanticCache(
            redis_url=settings.redis_url,           # ✅ from settings, not hardcoded
            embedding=embeddings,                   # ✅ pass full embeddings object, not .embed_query
            score_threshold=0.2,
        )

        langchain.llm_cache = redis_cache           # ✅ actually apply cache to LangChain globally
                                                    # without this line the cache is built but never used

        logger.info(
            "Redis semantic cache enabled",
            extra={"redis_url": settings.redis_url},
        )
        return True

    except Exception as e:
        # Redis being down should NOT crash the app
        # Every request goes to the LLM directly — more expensive but functional
        logger.warning(
            "Redis unavailable — running without semantic cache",
            extra={"error": str(e)},
        )
        return False


def clear_cache() -> int:
    """
    Clears all cached LLM responses.
    Useful after updating product data or prompt templates.

    Returns: number of keys deleted
    """
    settings = get_settings()
    try:
        client = redis.from_url(settings.redis_url)
        keys = client.keys("langchain:*")
        if keys:
            client.delete(*keys)
        logger.info("Cache cleared", extra={"keys_deleted": len(keys)})
        return len(keys)
    except Exception as e:
        logger.error("Failed to clear cache", extra={"error": str(e)})
        return 0


if __name__ == "__main__":
    from app.core.model_loader import get_model_loader

    embeddings = get_model_loader().load_embeddings()

    print("Testing Redis cache setup...")
    ok = setup_cache(embeddings)
    print(f"✅ Cache enabled: {ok}")

    if ok:
        print("\nTesting cache clear...")
        deleted = clear_cache()
        print(f"✅ Keys deleted: {deleted}")
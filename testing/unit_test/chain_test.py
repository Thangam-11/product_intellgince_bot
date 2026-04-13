import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# ── test invoke_chain cache HIT ───────────────────────
@pytest.mark.asyncio
async def test_invoke_chain_returns_cached_response():
    """Cache HIT must return cached value without calling LLM."""
    cached_response = b"cached answer about headphones"

    with patch("src.rag_app.core_app.chain._get_redis") as mock_redis:
        mock_redis.return_value.get.return_value = cached_response
        from src.rag_app.core_app.chain import invoke_chain
        result = await invoke_chain("Are boAt headphones good?")
        assert result == "cached answer about headphones"
        mock_redis.return_value.get.assert_called_once()


# ── test invoke_chain cache MISS ──────────────────────
@pytest.mark.asyncio
async def test_invoke_chain_calls_llm_on_cache_miss():
    """Cache MISS must call LLM and store result in cache."""
    with patch("src.rag_app.core_app.chain._get_redis") as mock_redis, \
         patch("src.rag_app.core_app.chain.get_chain") as mock_get_chain:

        mock_redis.return_value.get.return_value = None  # cache miss
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value="LLM response about headphones")
        mock_get_chain.return_value = mock_chain

        from src.rag_app.core_app.chain import invoke_chain
        result = await invoke_chain("Are boAt headphones good?")

        assert result == "LLM response about headphones"
        mock_chain.ainvoke.assert_called_once()
        mock_redis.return_value.setex.assert_called_once()  # stored in cache


# ── test invoke_chain empty query ─────────────────────
@pytest.mark.asyncio
async def test_invoke_chain_rejects_empty_query():
    """Empty query must raise exception."""
    from src.rag_app.core_app.chain import invoke_chain
    from src.rag_app.logger_exceptions.exception import CustomerProductIntelligenceException

    with pytest.raises(CustomerProductIntelligenceException):
        await invoke_chain("")


@pytest.mark.asyncio
async def test_invoke_chain_rejects_blank_query():
    """Blank whitespace query must raise exception."""
    from src.rag_app.core_app.chain import invoke_chain
    from src.rag_app.logger_exceptions.exception import CustomerProductIntelligenceException

    with pytest.raises(CustomerProductIntelligenceException):
        await invoke_chain("   ")


# ── test cache key ────────────────────────────────────
def test_cache_key_is_deterministic():
    """Same query must always produce same cache key."""
    from src.rag_app.core_app.chain import _cache_key
    key1 = _cache_key("Are boAt headphones good?")
    key2 = _cache_key("Are boAt headphones good?")
    assert key1 == key2


def test_cache_key_is_case_insensitive():
    """Cache key must be same regardless of case."""
    from src.rag_app.core_app.chain import _cache_key
    key1 = _cache_key("Are boAt headphones good?")
    key2 = _cache_key("are boat headphones good?")
    assert key1 == key2


def test_cache_key_strips_whitespace():
    """Cache key must strip leading/trailing whitespace."""
    from src.rag_app.core_app.chain import _cache_key
    key1 = _cache_key("Are boAt headphones good?")
    key2 = _cache_key("  Are boAt headphones good?  ")
    assert key1 == key2


def test_cache_key_has_prefix():
    """Cache key must start with rag:response: prefix."""
    from src.rag_app.core_app.chain import _cache_key
    key = _cache_key("test query")
    assert key.startswith("rag:response:")


# ── test get_chain singleton ──────────────────────────
def test_get_chain_returns_same_instance():
    """get_chain must return the same cached instance."""
    with patch("src.rag_app.core_app.chain._build_chain") as mock_build:
        mock_build.return_value = MagicMock()
        from src.rag_app.core_app.chain import get_chain
        import src.rag_app.core_app.chain as chain_module
        chain_module._chain = None  # reset

        chain1 = get_chain()
        chain2 = get_chain()
        assert chain1 is chain2
        mock_build.assert_called_once()  # built only once
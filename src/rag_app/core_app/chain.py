import hashlib
import redis as redis_client
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential
from rag_app.core_app.retrieval import get_retriever
from rag_app.core_app.model_loader import get_model_loader
from rag_app.prompts_lib.prompt import PROMPT_TEMPLATES
from rag_app.logger_exceptions.exception import CustomerProductIntelligenceException
from rag_app.configure.config_settings import get_settings
from rag_app.utils.logger import get_logger
from typing import AsyncIterator

logger = get_logger(__name__)

_chain = None
CACHE_TTL = 3600  # 1 hour


def _get_redis():
    """Returns Redis client."""
    return redis_client.from_url(
        get_settings().redis_url,
        socket_connect_timeout=2,
    )


def _cache_key(query: str) -> str:
    """Deterministic cache key from query."""
    return f"rag:response:{hashlib.md5(query.strip().lower().encode()).hexdigest()}"


def _build_chain():
    """
    Builds the LangChain RAG chain.
    Chain flow:
      user query
        → retriever fetches top-k relevant docs from AstraDB
        → docs + query injected into prompt template
        → LLM generates answer grounded in retrieved docs
        → StrOutputParser extracts plain string from LLM response
    """
    retriever = get_retriever().load_retriever()
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATES["product_bot"])
    llm = get_model_loader().load_llm()
    return (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )


def get_chain():
    """Returns cached RAG chain — built once, reused for every request."""
    global _chain
    if _chain is None:
        _chain = _build_chain()
        logger.info("RAG chain built and cached")
    return _chain


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def invoke_chain(query: str) -> str:
    """
    Invokes the RAG chain with direct Redis caching.
      1. Check Redis — return instantly if cached
      2. Cache MISS — call LLM, store result in Redis
      3. TTL: 1 hour — cache auto-expires
    """
    if not query or not query.strip():
        raise CustomerProductIntelligenceException("Query cannot be empty")

    # ✅ Step 1 — check cache
    try:
        r = _get_redis()
        cached = r.get(_cache_key(query))
        if cached:
            logger.info("Cache HIT", extra={"query_length": len(query)})
            return cached.decode("utf-8")
    except Exception as e:
        logger.warning("Redis unavailable for read", extra={"error": str(e)})

    # ✅ Step 2 — cache miss, call LLM
    try:
        logger.info("Cache MISS — invoking chain", extra={"query_length": len(query)})
        chain = get_chain()
        result = await chain.ainvoke(query)
        logger.info("Chain completed", extra={"response_length": len(result)})
    except CustomerProductIntelligenceException:
        raise
    except Exception as e:
        raise CustomerProductIntelligenceException("Chain invocation failed", e)

    # ✅ Step 3 — store in cache
    try:
        r = _get_redis()
        r.setex(_cache_key(query), CACHE_TTL, result)
        logger.info("Response cached", extra={"ttl": CACHE_TTL})
    except Exception as e:
        logger.warning("Redis unavailable for write", extra={"error": str(e)})

    return result


async def invoke_chain(query: str) -> str:
    if not query or not query.strip():
        raise CustomerProductIntelligenceException("Query cannot be empty")

    return await _invoke_chain_internal(query)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _invoke_chain_internal(query: str) -> str:
    chain = get_chain()
    return await chain.ainvoke(query)

if __name__ == "__main__":
    import asyncio

    async def test():
        print("Testing RAG chain...")
        result = await invoke_chain("Are boAt headphones good for bass?")
        print(f"\n✅ First request (cache MISS):\n{result}")

        print("\nTesting cache hit...")
        result2 = await invoke_chain("Are boAt headphones good for bass?")
        print(f"✅ Second request (cache HIT):\n{result2}")

    asyncio.run(test())

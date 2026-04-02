from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential
from src.rag_app.core_app.retrieval import get_retriever
from src.rag_app.core_app.model_loader import get_model_loader
from src.rag_app.prompts_lib.prompt import PROMPT_TEMPLATES
from src.rag_app.logger_exceptions.exception import CustomerProductIntelligenceException
from src.rag_app.utils.logger import get_logger
from typing import AsyncIterator

logger = get_logger(__name__)

_chain = None


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
    Invokes the RAG chain asynchronously.
      - ainvoke() never blocks the FastAPI event loop
      - tenacity retries up to 3x with exponential backoff
        on transient errors (network timeouts, rate limits)
      - Wraps errors in CustomerProductIntelligenceException
    """
    if not query or not query.strip():
        raise CustomerProductIntelligenceException("Query cannot be empty")
    try:
        logger.info("Invoking chain", extra={"query_length": len(query)})
        chain = get_chain()
        result = await chain.ainvoke(query)
        logger.info("Chain completed", extra={"response_length": len(result)})
        return result
    except CustomerProductIntelligenceException:
        raise
    except Exception as e:
        raise CustomerProductIntelligenceException("Chain invocation failed", e)


async def invoke_chain_stream(query: str) -> AsyncIterator[str]:
    """
    Streams the LLM response token by token.
    Without: user waits 10s staring at blank screen, then sees full answer.
    With:    user sees text appearing word by word after ~0.5s (like ChatGPT).
    """
    if not query or not query.strip():
        raise CustomerProductIntelligenceException("Query cannot be empty")
    try:
        chain = get_chain()
        async for chunk in chain.astream(query):
            yield chunk
    except CustomerProductIntelligenceException:
        raise
    except Exception as e:
        raise CustomerProductIntelligenceException("Chain streaming failed", e)


if __name__ == "__main__":
    import asyncio

    async def test():
        print("Testing RAG chain...")
        result = await invoke_chain("Are boAt headphones good for bass?")
        print(f"\n✅ Response:\n{result}")

    asyncio.run(test())
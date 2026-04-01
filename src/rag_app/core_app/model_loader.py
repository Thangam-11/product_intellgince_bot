from typing import List
from functools import lru_cache
from langchain_astradb import AstraDBVectorStore
from langchain_core.documents import Document
from src.rag_app.configure.config_settings import get_settings  # ✅ fixed import path
from src.rag_app.core_app.model_loader import get_model_loader  # ✅ singleton
from src.rag_app.logger_exceptions.exception import CustomerProductIntelligenceException
from src.rag_app.utils.logger import get_logger

logger = get_logger(__name__)


class Retriever:
    """
    Manages AstraDB vector store connection and similarity search.
      - Uses get_model_loader() singleton (no duplicate model loads)
      - Lazy-loads vstore on first use (fast container startup)
      - Caches vstore + retriever (no reconnect per request)
      - Structured logging instead of print()
      - Wraps all errors in CustomerSupportBotException 
    """

    def __init__(self):
        self.settings = get_settings()
        self.model_loader = get_model_loader()  # ✅ singleton
        self._vstore: AstraDBVectorStore | None = None
        self._retriever = None

    def _get_vstore(self) -> AstraDBVectorStore:
        """Lazy-initializes AstraDB connection."""
        if self._vstore is None:
            try:
                self._vstore = AstraDBVectorStore(
                    embedding=self.model_loader.load_embeddings(),
                    collection_name=self.settings.astra_db_collection,
                    api_endpoint=self.settings.astra_db_api_endpoint,
                    token=self.settings.astra_db_application_token,
                    namespace=self.settings.astra_db_keyspace,
                )
                logger.info(
                    "AstraDB connected",
                    extra={"collection": self.settings.astra_db_collection},
                )
            except Exception as e:
                raise CustomerProductIntelligenceException("Failed to connect to AstraDB", e)
        return self._vstore

    def load_retriever(self):
        """Returns cached LangChain retriever."""
        if self._retriever is None:
            vstore = self._get_vstore()
            self._retriever = vstore.as_retriever(
                search_kwargs={"k": self.settings.retriever_top_k}
            )
            logger.info(
                "Retriever ready",
                extra={"top_k": self.settings.retriever_top_k},
            )
        return self._retriever

    async def similarity_search(self, query: str) -> List[Document]:
        """
        Direct similarity search — bypasses LangChain retriever.
        Useful for evaluation and debugging retrieval quality.
        """
        try:
            vstore = self._get_vstore()
            return await vstore.asimilarity_search(
                query, k=self.settings.retriever_top_k
            )
        except Exception as e:
            raise CustomerProductIntelligenceException(
                f"Similarity search failed for query: '{query}'", e
            )

    def check_connection(self) -> bool:
        """
        Health check — verifies AstraDB is reachable.
        Called by /ready endpoint.
        """
        try:
            self._get_vstore()
            return True
        except Exception:
            return False


@lru_cache()
def get_retriever() -> Retriever:
    """Process-level singleton — mirrors get_model_loader() pattern."""
    return Retriever()


if __name__ == "__main__":
    retriever = get_retriever()

    print("Testing connection...")
    ok = retriever.check_connection()
    print(f"✅ AstraDB connected: {ok}")

    print("\nTesting retriever...")
    lc_retriever = retriever.load_retriever()
    results = lc_retriever.invoke("What is your return policy?")
    print(f"✅ Retrieved {len(results)} documents")
    for doc in results:
        print(f"  - {doc.page_content[:80]}...")
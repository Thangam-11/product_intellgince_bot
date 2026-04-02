from functools import lru_cache
from langchain_openai import ChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.rag_app.configure.config_settings import get_settings, Settings
from src.rag_app.utils.logger import get_logger

logger = get_logger(__name__)


class ModelLoader:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._embeddings = None
        self._llm = None

    def load_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        if not self._embeddings:
            logger.info(
                "Loading embedding model",
                extra={"model": self.settings.embedding_model},
            )
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=self.settings.embedding_model,
                google_api_key=self.settings.gemini_api_key,
            )
        return self._embeddings

    def load_llm(self) -> ChatOpenAI:
        if not self._llm:
            if not self.settings.open_router_api_key:
                raise ValueError("Missing OpenRouter API key")
            logger.info(
                "Loading LLM via OpenRouter",
                extra={"model": self.settings.llm_model},
            )
            self._llm = ChatOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.settings.open_router_api_key,
                model=self.settings.llm_model,
                temperature=0.7,
                request_timeout=30,
                max_retries=2,
            )
        return self._llm


@lru_cache()
def get_model_loader() -> ModelLoader:
    return ModelLoader(settings=get_settings())


if __name__ == "__main__":
    loader = get_model_loader()

    print("Testing embeddings...")
    embeddings = loader.load_embeddings()
    print(f"✅ Embeddings loaded: {type(embeddings).__name__}")

    print("Testing LLM...")
    llm = loader.load_llm()
    print(f"✅ LLM loaded: {type(llm).__name__}")
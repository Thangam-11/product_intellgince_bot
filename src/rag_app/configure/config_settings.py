from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Required secrets ──
    gemini_api_key: str
    open_router_api_key: str
    astra_db_api_endpoint: str
    astra_db_application_token: str
    astra_db_keyspace: str
    port: int = 8000

    # ── Optional secrets ──
    openai_api_key: str = ""
    groq_api_key: str = ""

    # ── App config ──
    astra_db_collection: str = "ecommercedatanew"
    embedding_model: str = "models/gemini-embedding-001"
    llm_model: str = "meta-llama/llama-3-8b-instruct"
    retriever_top_k: int = 10
    redis_url: str = "redis://localhost:6379"
    api_key: str = "changeme-in-production"
    environment: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # ✅ ADD THIS BLOCK (VERY IMPORTANT)
    def model_post_init(self, __context):
        self.astra_db_application_token = self.astra_db_application_token.strip()
        self.gemini_api_key = self.gemini_api_key.strip()
        self.open_router_api_key = self.open_router_api_key.strip()


@lru_cache()
def get_settings() -> Settings:
    return Settings()
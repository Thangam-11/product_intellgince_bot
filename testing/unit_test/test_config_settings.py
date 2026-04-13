import pytest
import os
from unittest.mock import patch
from src.rag_app.configure.config_settings import get_settings

REQUIRED_ENV = {
    "GEMINI_API_KEY":              "gemini-test-key",
    "OPEN_ROUTER_API_KEY":         "sk-router-test",
    "ASTRA_DB_API_ENDPOINT":       "https://test.astra.endpoint",
    "ASTRA_DB_APPLICATION_TOKEN":  "AstraCS:test-token",
    "ASTRA_DB_KEYSPACE":           "test_keyspace",
}


def make_settings(**overrides):
    from src.rag_app.configure.config_settings import Settings
    env = {**REQUIRED_ENV, **overrides}
    with patch.dict(os.environ, env, clear=True):
        return Settings()


def test_settings_loads_required_fields():
    settings = make_settings()
    assert settings.open_router_api_key == "sk-router-test"
    assert settings.astra_db_api_endpoint == "https://test.astra.endpoint"
    assert settings.astra_db_application_token == "AstraCS:test-token"
    assert settings.astra_db_keyspace == "test_keyspace"
    assert settings.gemini_api_key == "gemini-test-key"


def test_settings_defaults_are_applied():
    settings = make_settings()
    assert settings.llm_model == "meta-llama/llama-3-8b-instruct"
    assert settings.retriever_top_k == 10
    assert settings.environment == "development"
    assert settings.astra_db_collection == "ecommercedatanew"
    assert settings.redis_url == "redis://localhost:6379"
    assert settings.log_level == "INFO"


def test_settings_overrides_defaults():
    settings = make_settings(
        RETRIEVER_TOP_K="5",
        ENVIRONMENT="production",
        LOG_LEVEL="DEBUG",
    )
    assert settings.retriever_top_k == 5
    assert settings.environment == "production"
    assert settings.log_level == "DEBUG"


def test_settings_missing_required_field_raises():
    """Missing required field must raise ValidationError."""
    from pydantic import ValidationError
    incomplete = {k: v for k, v in REQUIRED_ENV.items() if k != "GEMINI_API_KEY"}
    with patch.dict(os.environ, incomplete, clear=True):
        with pytest.raises(ValidationError):
            from src.rag_app.configure.config_settings import Settings
            Settings(_env_file=None)  # ✅ skip .env file

def test_settings_lru_cache_returns_same_instance():
    from src.rag_app.configure.config_settings import get_settings
    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
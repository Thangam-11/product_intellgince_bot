"""
Integration tests for the chat API endpoints.
Uses FastAPI TestClient with all external services mocked.
"""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.fixture
def mock_chain_response():
    return "boAt headphones are great for bass with powerful drivers."


@pytest.fixture
def test_client():
    """FastAPI TestClient with all external services mocked."""
    with patch("src.rag_app.core_app.retrieval.AstraDBVectorStore"), \
         patch("src.rag_app.core_app.model_loader.GoogleGenerativeAIEmbeddings"), \
         patch("src.rag_app.core_app.model_loader.ChatOpenAI"), \
         patch("src.rag_app.cache_layer.redis_cache.setup_cache", return_value=True), \
         patch("redis.from_url"):
        from fastapi.testclient import TestClient
        from src.rag_app.main import app
        with TestClient(app) as client:
            yield client


@pytest.fixture
def client_with_mock_chain(test_client, mock_chain_response):
    """TestClient with chain mocked to return fake response."""
    with patch(
        "src.rag_app.api_services.services.chatbot.invoke_chain",
        new=AsyncMock(return_value=mock_chain_response),
    ):
        yield test_client


def test_chat_returns_200_with_valid_message(client_with_mock_chain):
    """Valid message must return 200."""
    response = client_with_mock_chain.post(
        "/chat",
        json={"msg": "Are boAt headphones good for bass?"},
    )
    assert response.status_code == 200


def test_chat_response_contains_response_key(client_with_mock_chain):
    """Response must be JSON with response key."""
    response = client_with_mock_chain.post(
        "/chat",
        json={"msg": "recommend headphones"},
    )
    body = response.json()
    assert "response" in body
    assert isinstance(body["response"], str)
    assert len(body["response"]) > 0


def test_chat_response_contains_request_id(client_with_mock_chain):
    """Every response must include request_id for tracing."""
    response = client_with_mock_chain.post(
        "/chat",
        json={"msg": "test query"},
    )
    body = response.json()
    assert "request_id" in body
    assert isinstance(body["request_id"], str)



def test_chat_returns_422_for_empty_message(client_with_mock_chain):
    """Whitespace-only messages must be rejected by validation."""
    response = client_with_mock_chain.post(
        "/chat",
        json={"msg": "   "},
    )
    assert response.status_code == 422


def test_chat_returns_422_for_too_long_message(client_with_mock_chain):
    """Messages over 1000 chars must be rejected."""
    response = client_with_mock_chain.post(
        "/chat",
        json={"msg": "a" * 1001},
    )
    assert response.status_code == 422


def test_chat_response_matches_mock(client_with_mock_chain, mock_chain_response):
    """Response content must match mocked chain output."""
    response = client_with_mock_chain.post(
        "/chat",
        json={"msg": "Are boAt headphones good?"},
    )
    body = response.json()
    assert body["response"] == mock_chain_response
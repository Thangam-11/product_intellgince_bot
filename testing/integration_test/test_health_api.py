"""
Integration tests for health and readiness endpoints.
These are called by AWS ECS to check if the app is alive.
"""
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def test_client():
    with patch("rag_app.core_app.retrieval.AstraDBVectorStore"), \
         patch("rag_app.core_app.model_loader.GoogleGenerativeAIEmbeddings"), \
         patch("rag_app.core_app.model_loader.ChatOpenAI"), \
         patch("rag_app.cache_layer.redis_cache.setup_cache", return_value=True), \
         patch("redis.from_url"):
        from fastapi.testclient import TestClient
        from rag_app.main import app  # ← FIXED
        with TestClient(app) as client:
            yield client

def test_health_returns_200(test_client):
    """Health endpoint must return 200."""
    response = test_client.get("/health")
    assert response.status_code == 200

def test_health_returns_correct_status(test_client):
    """Health response must contain status ok."""
    response = test_client.get("/health")
    body = response.json()
    assert body["status"] == "ok"

def test_health_returns_environment(test_client):
    """Health response must contain environment field."""
    response = test_client.get("/health")
    body = response.json()
    assert "environment" in body
    assert body["environment"] in ["development", "testing"]  # ← FIXED

def test_health_returns_uptime(test_client):
    """Health response must contain uptime_seconds."""
    response = test_client.get("/health")
    body = response.json()
    assert "uptime_seconds" in body
    assert body["uptime_seconds"] >= 0

def test_health_does_not_require_auth(test_client):
    """Health endpoint must work without API key."""
    response = test_client.get("/health")
    assert response.status_code == 200

def test_ready_returns_200_when_db_connected(test_client):
    with patch("rag_app.api_services.services.health.get_retriever") as mock:
        mock_retriever = MagicMock()
        mock_retriever.check_connection.return_value = True
        mock.return_value = mock_retriever
        response = test_client.get("/ready")
        assert response.status_code == 200

def test_ready_returns_correct_fields_when_connected(test_client):
    """Ready response must contain status and db fields."""
    with patch("rag_app.api_services.services.health.get_retriever") as mock:
        mock.return_value.check_connection.return_value = True
        response = test_client.get("/ready")
        body = response.json()
        assert body["status"] == "ready"
        assert body["db"] == "connected"

def test_ready_returns_503_when_db_down(test_client):
    """Ready endpoint must return 503 when AstraDB is unreachable."""
    with patch("rag_app.api_services.services.health.get_retriever") as mock:
        mock.return_value.check_connection.return_value = False
        response = test_client.get("/ready")
        assert response.status_code == 503

def test_metrics_returns_200(test_client):
    """Metrics endpoint must return 200."""
    response = test_client.get("/metrics")
    assert response.status_code == 200

def test_metrics_returns_correct_fields(test_client):
    """Metrics response must contain expected fields."""
    response = test_client.get("/metrics")
    body = response.json()
    assert "uptime_seconds" in body
    assert "requests_total" in body
    assert "errors_total" in body
    assert "cache_hits_total" in body
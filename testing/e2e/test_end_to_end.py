import pytest
import httpx
import os

pytestmark = pytest.mark.e2e

STAGING_URL = os.getenv("STAGING_URL", "http://localhost:8000")
STAGING_API_KEY = os.getenv("STAGING_API_KEY", "changeme-in-production")

@pytest.fixture
def staging_client():
    return httpx.Client(
        base_url=STAGING_URL,
        headers={"X-API-Key": STAGING_API_KEY},
        timeout=30.0,
    )

def test_health_endpoint_on_staging(staging_client):
    response = staging_client.get("/health")
    assert response.status_code == 200

def test_ready_endpoint_on_staging(staging_client):
    response = staging_client.get("/ready")
    assert response.status_code == 200

def test_chat_returns_relevant_response(staging_client):
    response = staging_client.post("/get", data={"msg": "recommend budget headphones"})
    assert response.status_code == 200
    body = response.json()
    assert "response" in body

def test_rate_limit_is_enforced(staging_client):
    responses = [
        staging_client.post("/get", data={"msg": f"query {i}"})
        for i in range(12)
    ]
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from rag_app.main import create_app


@pytest.fixture
def mock_chain_response():
    return "boAt headphones are great for bass with powerful drivers."


@pytest.fixture
def client_with_mock_chain(mock_chain_response):
    app = create_app()

    with patch(
        "rag_app.core_app.chain.invoke_chain",
        new=AsyncMock(return_value=mock_chain_response),
    ):
        with TestClient(
            app,
            headers={"X-API-Key": "test-api-key"}  # ← fixes 403 error
        ) as client:
            yield client
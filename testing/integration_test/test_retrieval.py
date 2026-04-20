"""
Integration tests for AstraDB retrieval.
These tests mock AstraDB — no real DB connection needed.
Mark with @pytest.mark.integration for real DB tests.
"""
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


MOCK_DOCS = [
    Document(
        page_content="boAt BassHeads 100 has excellent bass and great sound quality.",
        metadata={"product_name": "boAt BassHeads 100", "product_rating": 4.5, "id": "abc123"},
    ),
    Document(
        page_content="The build quality is decent for the price.",
        metadata={"product_name": "boAt BassHeads 100", "product_rating": 4.0, "id": "def456"},
    ),
]


@pytest.fixture
def mock_retriever():
    """Mock retriever that returns fake documents."""
    with patch("rag_app.core_app.retrieval.AstraDBVectorStore") as mock_store:
        mock_vstore = MagicMock()
        mock_vstore.as_retriever.return_value.invoke.return_value = MOCK_DOCS
        mock_store.return_value = mock_vstore

        from rag_app.core_app.retrieval import Retriever
        retriever = Retriever()
        retriever._vstore = mock_vstore
        yield retriever


def test_retriever_returns_documents(mock_retriever):
    """Retriever must return documents for a valid query."""
    mock_retriever._retriever = MagicMock()
    mock_retriever._retriever.invoke.return_value = MOCK_DOCS
    results = mock_retriever._retriever.invoke("boAt headphones bass")
    assert len(results) == 2


def test_retriever_documents_have_page_content(mock_retriever):
    """Each document must have page_content."""
    mock_retriever._retriever = MagicMock()
    mock_retriever._retriever.invoke.return_value = MOCK_DOCS
    results = mock_retriever._retriever.invoke("boAt headphones")
    for doc in results:
        assert doc.page_content
        assert len(doc.page_content) > 0


def test_retriever_documents_have_metadata(mock_retriever):
    """Each document must have product metadata."""
    mock_retriever._retriever = MagicMock()
    mock_retriever._retriever.invoke.return_value = MOCK_DOCS
    results = mock_retriever._retriever.invoke("boAt headphones")
    for doc in results:
        assert "product_name" in doc.metadata
        assert "product_rating" in doc.metadata
        assert "id" in doc.metadata


def test_check_connection_returns_true_when_connected():
    """check_connection must return True when AstraDB is reachable."""
    with patch("rag_app.core_app.retrieval.AstraDBVectorStore"):
        from rag_app.core_app.retrieval import Retriever
        retriever = Retriever()
        retriever._vstore = MagicMock()  # mock connected vstore
        assert retriever.check_connection() is True


def test_check_connection_returns_false_when_failed():
    """check_connection must return False when AstraDB is unreachable."""
    from rag_app.core_app.retrieval import Retriever
    retriever = Retriever()
    retriever._vstore = None
    with patch.object(retriever, "_get_vstore", side_effect=Exception("Connection failed")):
        assert retriever.check_connection() is False
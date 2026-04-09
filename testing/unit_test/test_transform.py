import pytest
import pandas as pd
from src.data_ingestion.data_transform import make_doc_id, is_valid_row, transform  # ✅ fixed import path


def test_make_doc_id_is_deterministic():
    """Same content must always produce the same ID."""
    id1 = make_doc_id("Sony Headphones", "Great sound quality")
    id2 = make_doc_id("Sony Headphones", "Great sound quality")
    assert id1 == id2


def test_make_doc_id_is_unique_for_different_content():
    """Different content must produce different IDs."""
    id1 = make_doc_id("Sony Headphones", "Great sound quality")
    id2 = make_doc_id("boAt Headphones", "Decent quality")
    assert id1 != id2


def test_make_doc_id_length():
    """ID must be 32 characters (first 32 of SHA256 hex)."""
    doc_id = make_doc_id("Product", "Review text here")
    assert len(doc_id) == 32

    
def test_make_doc_id_strips_whitespace():
    """Leading/trailing whitespace must not affect the ID."""
    id1 = make_doc_id("Sony", "Great sound")
    id2 = make_doc_id("  Sony  ", "  Great sound  ")
    assert id1 == id2                              # ✅ new test


def test_is_valid_row_passes_good_data():
    row = pd.Series({
        "product_title": "Sony Headphones",
        "rating": 4.5,
        "summary": "Great product",
        "review": "This is a detailed review with enough content",
    })
    assert is_valid_row(row) is True


def test_is_valid_row_rejects_null_title():
    row = pd.Series({
        "product_title": None,
        "rating": 4.5,
        "summary": "Great",
        "review": "Good product review here",
    })
    assert is_valid_row(row) is False


def test_is_valid_row_rejects_empty_title():
    """Empty string title must be rejected."""
    row = pd.Series({
        "product_title": "   ",                    # ✅ new test
        "rating": 4.5,
        "summary": "Great",
        "review": "Good product review here",
    })
    assert is_valid_row(row) is False


def test_is_valid_row_rejects_short_review():
    """Review must be at least 10 characters after stripping."""
    row = pd.Series({
        "product_title": "Sony",
        "rating": 4.5,
        "summary": "Good",
        "review": "OK",
    })
    assert is_valid_row(row) is False


def test_is_valid_row_rejects_null_rating():
    """Null rating must be rejected."""
    row = pd.Series({                              # ✅ new test
        "product_title": "Sony",
        "rating": None,
        "summary": "Good",
        "review": "Good product review here",
    })
    assert is_valid_row(row) is False


def test_transform_creates_correct_document_count():
    df = pd.DataFrame([
        {"product_title": "Sony", "rating": 4.5, "summary": "Good", "review": "Excellent product with great sound"},
        {"product_title": "boAt", "rating": 3.8, "summary": "Ok",   "review": "Decent budget friendly headphones"},
        {"product_title": None,   "rating": 4.0, "summary": "N/A",  "review": "Should be skipped"},
    ])
    documents, skipped = transform(df)
    assert len(documents) == 2
    assert skipped == 1


def test_transform_document_has_correct_metadata():
    df = pd.DataFrame([{
        "product_title": "Sony WH-1000XM4",
        "rating": 4.5,
        "summary": "Best noise cancelling",
        "review": "Incredible noise cancellation and sound quality",
    }])
    documents, _ = transform(df)
    doc = documents[0]
    assert doc.metadata["product_name"] == "Sony WH-1000XM4"
    assert doc.metadata["product_rating"] == 4.5
    assert doc.metadata["product_summary"] == "Best noise cancelling"
    assert "id" in doc.metadata
    assert len(doc.metadata["id"]) == 32


def test_transform_page_content_is_review():
    """page_content must be the review text."""
    df = pd.DataFrame([{               # ✅ new test
        "product_title": "Sony",
        "rating": 4.5,
        "summary": "Good",
        "review": "Incredible noise cancellation and sound quality",
    }])
    documents, _ = transform(df)
    assert documents[0].page_content == "Incredible noise cancellation and sound quality"


def test_transform_skips_all_invalid_rows():
    df = pd.DataFrame([
        {"product_title": None, "rating": None, "summary": None, "review": "x"},
        {"product_title": "",   "rating": 4.0,  "summary": "Ok", "review": "short"},
    ])
    documents, skipped = transform(df)
    assert len(documents) == 0
    assert skipped == 2


def test_transform_empty_dataframe():
    """Empty DataFrame must return empty list with zero skipped."""
    documents, skipped = transform(pd.DataFrame())  # ✅ new test
    assert documents == []
    assert skipped == 0
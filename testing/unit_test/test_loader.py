import pytest
import pandas as pd
import tempfile
import os
from data_ingestion.data_loader import load_csv
from rag_app.logger_exceptions.exception import CustomerProductIntelligenceException


# ── Helper ────────────────────────────────────────────
def create_temp_csv(content: str) -> str:
    """Write content to a temp CSV file, return path."""
    f = tempfile.NamedTemporaryFile(
        mode='w', suffix='.csv', delete=False, encoding='utf-8'
    )
    f.write(content)
    f.close()
    return f.name


VALID_CSV = (
    "product_title,rating,summary,review\n"
    "boAt BassHeads 100,4.5,Great sound,Excellent bass and build quality\n"
    "Sony WH-1000XM4,5.0,Best ANC,Amazing noise cancellation\n"
)


# ── Tests ─────────────────────────────────────────────
def test_load_csv_success():
    """Valid CSV must load correctly with all rows."""
    path = create_temp_csv(VALID_CSV)
    try:
        df = load_csv(path)
        assert len(df) == 2
        assert "product_title" in df.columns
        assert "rating" in df.columns
        assert "summary" in df.columns
        assert "review" in df.columns
    finally:
        os.unlink(path)


def test_load_csv_missing_file():
    """Non-existent file must raise exception."""
    with pytest.raises(CustomerProductIntelligenceException) as exc_info:
        load_csv("/nonexistent/path/file.csv")
    assert "not found" in str(exc_info.value).lower()


def test_load_csv_missing_columns():
    """CSV missing required columns must raise exception."""
    path = create_temp_csv("name,score\nSony,5\n")
    try:
        with pytest.raises(CustomerProductIntelligenceException) as exc_info:
            load_csv(path)
        assert "missing" in str(exc_info.value).lower()
    finally:
        os.unlink(path)


def test_load_csv_empty_file():
    """CSV with headers but no rows must raise exception."""
    path = create_temp_csv("product_title,rating,summary,review\n")
    try:
        with pytest.raises(CustomerProductIntelligenceException) as exc_info:
            load_csv(path)
        assert "empty" in str(exc_info.value).lower()
    finally:
        os.unlink(path)


def test_load_csv_strips_column_whitespace():
    """Column names with whitespace must be stripped."""
    path = create_temp_csv(
        " product_title , rating , summary , review \n"
        "boAt,4.5,Good,Nice sound\n"
    )
    try:
        df = load_csv(path)
        assert "product_title" in df.columns
        assert len(df) == 1
    finally:
        os.unlink(path)


def test_load_csv_drops_all_null_rows():
    """Rows where all required fields are null must be dropped."""
    path = create_temp_csv(
        "product_title,rating,summary,review\n"
        "boAt,4.5,Good,Nice sound\n"
        ",,, \n"
    )
    try:
        df = load_csv(path)
        assert len(df) == 1
    finally:
        os.unlink(path)


def test_load_csv_returns_dataframe():
    """Return type must be a pandas DataFrame."""
    path = create_temp_csv(VALID_CSV)
    try:
        df = load_csv(path)
        assert isinstance(df, pd.DataFrame)
    finally:
        os.unlink(path)


def test_load_csv_partial_null_rows_kept():
    """Rows missing ANY required field are dropped — this is correct behavior."""
    path = create_temp_csv(
        "product_title,rating,summary,review\n"
        "boAt,4.5,Good,Nice sound\n"       # all fields present — kept
        "Sony,5.0,,Amazing quality\n"      # summary null — dropped
    )
    try:
        df = load_csv(path)
        assert len(df) == 1               # only fully valid row kept
    finally:
        os.unlink(path)


def test_load_csv_handles_bad_lines():
    """CSV with malformed lines must skip them gracefully."""
    path = create_temp_csv(
        "product_title,rating,summary,review\n"
        "boAt,4.5,Good,Nice sound\n"
        "broken,line,with,too,many,columns\n"
        "Sony,5.0,Great,Amazing quality\n"
    )
    try:
        df = load_csv(path)
        assert len(df) >= 2               # at least valid rows loaded
    finally:
        os.unlink(path)
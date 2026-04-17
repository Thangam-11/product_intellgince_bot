import pandas as pd
from rag_app.utils.logger import get_logger
from rag_app.logger_exceptions.exception import CustomerProductIntelligenceException

logger = get_logger(__name__)

REQUIRED_COLUMNS = {"product_title", "rating", "summary", "review"}


def load_csv(csv_path: str) -> pd.DataFrame:
    """
    Loads and validates the product review CSV.

    Separated from transformer so each step can be
    unit tested independently:
      - test_loader.py: tests validation logic with fake DataFrames
      - test_transformer.py: tests transformation with pre-validated data

    Validation checks:
      1. File exists and is readable
      2. Required columns are present
      3. File is not empty after loading
      4. Rows missing ANY required field are dropped

    Returns: clean DataFrame ready for tran sformation
    Raises: CustomerProductIntelligenceException if any check fails
    """
    try:
        logger.info("Loading CSV", extra={"path": csv_path})
        df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")
    except FileNotFoundError:
        raise CustomerProductIntelligenceException(
            f"CSV file not found: {csv_path}. "
            "Place your data at data/flipkart_product_review.csv"
        )
    except Exception as e:
        raise CustomerProductIntelligenceException(f"Failed to read CSV: {csv_path}", e)

    # Strip column name whitespace — common CSV export issue
    df.columns = df.columns.str.strip()

    # Check required columns
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise CustomerProductIntelligenceException(
            f"CSV missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    if df.empty:
        raise CustomerProductIntelligenceException("CSV file is empty — nothing to ingest.")

    # Normalize required columns: strip whitespace, convert blanks to NA
    for col in REQUIRED_COLUMNS:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": pd.NA, "": pd.NA})

    # Drop rows missing ANY required column (not just all-null rows)
    # A row without a review text or product title is not usable for RAG
    before = len(df)
    df = df.dropna(subset=list(REQUIRED_COLUMNS), how="any")
    dropped = before - len(df)

    if dropped:
        logger.warning(
            "Dropped rows with missing required fields",
            extra={"dropped": dropped, "remaining": len(df)},
        )
    else:
        logger.info("No rows dropped — all required fields present")

    if df.empty:
        raise CustomerProductIntelligenceException(
            "No valid rows remaining after cleaning. "
            "Check that required columns contain data."
        )

    logger.info(
        "CSV loaded successfully",
        extra={"rows": len(df), "columns": list(df.columns)},
    )

    return df


if __name__ == "__main__":
    df = load_csv("data/flipkart_product_review.csv")
    print(f"✅ Loaded {len(df)} rows")
    print(df.head(2))

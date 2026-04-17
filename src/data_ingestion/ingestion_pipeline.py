"""
Ingestion pipeline entry point.
Run directly:  python -m src.data_ingestion.ingestion_pipeline
Run via CI:    Triggered by .github/workflows/ingestion.yml on schedule

This file just orchestrates loader → transformer → vector_store.
Each step is in its own module for independent testing.
"""
import os
from rag_app.utils.logger import get_logger
from rag_app.logger_exceptions.exception import CustomerProductIntelligenceException
from data_ingestion.data_loader import load_csv
from data_ingestion.data_transform import transform
from data_ingestion.vector_store import store_documents

logger = get_logger(__name__)

DEFAULT_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "flipkart_product_review.csv"
)

def run_pipeline(csv_path: str = DEFAULT_CSV) -> dict:
    """
    Runs the full data ingestion pipeline.

    Steps:
      1. load_csv()        — read + validate CSV
      2. transform()       — rows → LangChain Documents with hash IDs
      3. store_documents() — batch upsert into AstraDB

    Returns summary dict with counts for logging/monitoring.
    """
    logger.info("Pipeline started", extra={"csv_path": csv_path})

    try:
        # Step 1: Load
        df = load_csv(csv_path)

        # Step 2: Transform
        documents, skipped = transform(df)

        if not documents:
            logger.warning("No valid documents to store — pipeline complete with 0 inserts")
            return {"csv_rows": 0, "documents_created": 0, "skipped": skipped, "stored": 0}

        # Step 3: Store
        stored = store_documents(documents)

        summary = {
            "csv_rows": len(df),
            "documents_created": len(documents),
            "skipped": skipped,
            "stored": stored,
        }
        logger.info("Pipeline complete", extra=summary)
        return summary

    except CustomerProductIntelligenceException as e:
        logger.error("Pipeline failed", extra={"error": str(e)})
        raise


if __name__ == "__main__":
    run_pipeline()

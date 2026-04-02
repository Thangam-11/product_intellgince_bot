import hashlib
import pandas as pd
from typing import List, Tuple
from langchain_core.documents import Document
from src.rag_app.utils.logger import get_logger
from src.rag_app.logger_exceptions.exception import CustomerProductIntelligenceException

logger = get_logger(__name__)


def make_doc_id(product_title: str, review: str) -> str:
    """
    Creates a deterministic SHA-256 hash ID from content.

    Why content-based IDs?
      Without IDs: every pipeline run adds duplicate documents to AstraDB
      With hash IDs: AstraDB upserts — re-running is completely safe

    The hash is based on product_title + review text.
    Same content = same ID = upsert (no duplicate).
    Different content = different ID = new document.
    """
    content = f"{product_title.strip()}{review.strip()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:32]


def is_valid_row(row: pd.Series) -> bool:
    """
    Validates a single CSV row before creating a Document.

    Skips rows where:
      - product_title is null/empty
      - review is null/empty or too short to be useful (< 10 chars)
      - rating is null (needed for metadata)
    """
    return (
        pd.notna(row.get("product_title"))
        and str(row.get("product_title", "")).strip() != ""
        and pd.notna(row.get("review"))
        and len(str(row.get("review", ""))) >= 10
        and pd.notna(row.get("rating"))
    )


def transform(df: pd.DataFrame) -> Tuple[List[Document], int]:
    """
    Converts DataFrame rows into LangChain Documents.

    Returns:
        documents: List of valid Document objects ready for AstraDB
        skipped: Count of rows that failed validation

    Document structure:
        page_content = review text (this gets embedded and searched)
        metadata = product_name, rating, summary, id
                   (returned alongside search results for context)
    """
    documents = []
    skipped = 0

    for _, row in df.iterrows():
        if not is_valid_row(row):
            skipped += 1
            continue

        product_title = str(row["product_title"]).strip()
        review = str(row["review"]).strip()
        doc_id = make_doc_id(product_title, review)

        doc = Document(
            page_content=review,
            metadata={
                "id": doc_id,
                "product_name": product_title,
                "product_rating": float(row["rating"]),
                "product_summary": str(row.get("summary", "")).strip(),
            },
        )
        documents.append(doc)

    logger.info(
        "Transformation complete",
        extra={
            "total_rows": len(df),
            "documents_created": len(documents),
            "skipped": skipped,
            "skip_rate_pct": round(skipped / max(len(df), 1) * 100, 1),
        },
    )

    return documents, skipped

import time
from typing import List
from langchain_core.documents import Document
from langchain_astradb import AstraDBVectorStore
from tqdm import tqdm
from src.rag_app.configure.config_settings import get_settings
from src.rag_app.core_app.model_loader import get_model_loader
from src.rag_app.utils.logger import get_logger
from src.rag_app.logger_exceptions.exception import CustomerProductIntelligenceException

logger = get_logger(__name__)
    
BATCH_SIZE = 20       # ✅ reduced from 100 — stay under free tier limit
BATCH_DELAY = 15      # ✅ 15s between batches — 20 docs/batch = safe under 100 req/min
RATE_LIMIT_WAIT = 60  # ✅ if 429 hit anyway, wait 60s before moving to next batch


def get_vector_store() -> AstraDBVectorStore:
    """
    Separated into its own function so it can be reused
    by both ingestion and retrieval without duplication.
    """
    settings = get_settings()
    model_loader = get_model_loader()
    try:
        vstore = AstraDBVectorStore(
            embedding=model_loader.load_embeddings(),
            collection_name=settings.astra_db_collection,
            api_endpoint=settings.astra_db_api_endpoint,
            token=settings.astra_db_application_token,
            namespace=settings.astra_db_keyspace,
        )
        logger.info("AstraDB connection established")
        return vstore
    except Exception as e:
        raise CustomerProductIntelligenceException("Failed to connect to AstraDB", e)


def store_documents(documents: List[Document]) -> int:
    """
    Stores documents in AstraDB with idempotency via content-hash IDs.
    Includes rate limiting for Gemini free tier (100 req/min).
    """
    if not documents:
        logger.warning("store_documents called with empty list, skipping")
        return 0

    vstore = get_vector_store()

    # Validate all docs have an ID before starting — fail fast
    missing_ids = [i for i, doc in enumerate(documents) if "id" not in doc.metadata]
    if missing_ids:
        raise CustomerProductIntelligenceException(
            f"Documents at indices {missing_ids} are missing metadata['id']. "
            "All documents must have a content-hash ID for idempotent upserts."
        )

    total_stored = 0
    failed_batches = 0
    batches = [
        documents[i : i + BATCH_SIZE]
        for i in range(0, len(documents), BATCH_SIZE)
    ]

    logger.info(
        "Starting upload",
        extra={
            "total_documents": len(documents),
            "total_batches": len(batches),
            "batch_size": BATCH_SIZE,
            "estimated_minutes": round(len(batches) * BATCH_DELAY / 60, 1),
        },
    )

    for i, batch in enumerate(tqdm(batches, desc="Uploading to AstraDB")):
        try:
            ids = [doc.metadata["id"] for doc in batch]
            vstore.add_documents(batch, ids=ids)
            total_stored += len(batch)
            logger.info(
                "Batch uploaded",
                extra={"batch": f"{i+1}/{len(batches)}", "stored": total_stored},
            )
            # ✅ Wait between batches to stay under free tier rate limit
            if i < len(batches) - 1:  # no need to wait after last batch
                time.sleep(BATCH_DELAY)

        except Exception as e:
            failed_batches += 1
            logger.error(
                "Batch upload failed",
                extra={"batch_size": len(batch), "error": str(e)},
            )
            # ✅ If rate limited, wait longer before next batch
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning(
                    f"Rate limited — waiting {RATE_LIMIT_WAIT}s",
                    extra={"batch": f"{i+1}/{len(batches)}"},
                )
                time.sleep(RATE_LIMIT_WAIT)
            continue

    logger.info(
        "Ingestion complete",
        extra={
            "total_stored": total_stored,
            "failed_batches": failed_batches,
            "total_batches": len(batches),
        },
    )
    return total_stored
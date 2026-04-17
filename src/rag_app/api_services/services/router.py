from fastapi import APIRouter
from rag_app.api_services.services import chatbot, health

router = APIRouter()
router.include_router(health.router)
router.include_router(chatbot.router)

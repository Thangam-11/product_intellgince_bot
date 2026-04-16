from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from src.rag_app.core_app.chain import invoke_chain, invoke_chain_stream
from src.rag_app.api_services.middleware.auth import verify_api_key
from src.rag_app.api_services.middleware.rate_limit import get_limiter
from src.rag_app.api_services.schmeas.chat import ChatRequest, ChatResponse
from src.rag_app.utils.logger import get_logger

router = APIRouter(tags=["Chat"])
logger = get_logger(__name__)
limiter = get_limiter()


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatRequest,
):
    # ✅ strip and reject blank — schema validator handles this
    # but double-check here for safety
    msg = body.msg.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        "Chat request",
        extra={"request_id": request_id, "query_length": len(msg)},
    )

    result = await invoke_chain(msg)

    return ChatResponse(                           # ✅ typed response
        response=result,
        request_id=request_id,
        cached=False,
    )


@router.post("/stream", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def stream_chat(
    request: Request,
    body: ChatRequest,
):
    msg = body.msg.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    async def generate():
        try:
            async for chunk in invoke_chain_stream(msg):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "X-Request-ID": getattr(request.state, "request_id", "unknown"),
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
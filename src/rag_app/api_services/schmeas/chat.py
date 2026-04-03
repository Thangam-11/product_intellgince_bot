from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ChatRequest(BaseModel):
    """
    Request body for POST /chat endpoint.
    Why Pydantic schemas?
      - Auto-validates input before it reaches your route handler
      - Auto-generates OpenAPI docs at /docs
      - Type-safe — no manual parsing or casting needed
    """
    msg: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User message / query",
        examples=["Are boAt headphones good for bass?"],
    )

    @field_validator("msg")
    @classmethod
    def strip_and_reject_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be blank or whitespace only.")
        return stripped


class ChatResponse(BaseModel):
    """Response body for POST /chat endpoint."""
    response: str = Field(
        ...,
        description="LLM answer grounded in retrieved product reviews",
    )
    request_id: str = Field(
        ...,
        description="Unique request ID for log tracing",
    )
    cached: bool = Field(
        default=False,
        description="True if response was served from Redis semantic cache",
    )


class HealthResponse(BaseModel):
    """Response body for GET /health endpoint."""
    status: str = Field(..., examples=["ok"])
    environment: str = Field(..., examples=["production"])
    uptime_seconds: float = Field(..., description="Seconds since app started")  # ← added


class ReadyResponse(BaseModel):
    """Response body for GET /ready endpoint."""
    status: str = Field(..., examples=["ready"])
    db: str = Field(..., examples=["connected"])


class ErrorResponse(BaseModel):
    """Standard error response shape for all endpoints."""
    detail: str = Field(..., description="Human readable error message")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")
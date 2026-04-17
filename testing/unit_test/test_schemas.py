import pytest
from pydantic import ValidationError
from rag_app.api_services.schmeas.chat import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ReadyResponse,
    ErrorResponse,
)


# ── ChatRequest ───────────────────────────────────────
def test_chat_request_valid():
    """Valid message must be accepted."""
    req = ChatRequest(msg="Are boAt headphones good for bass?")
    assert req.msg == "Are boAt headphones good for bass?"


def test_chat_request_strips_whitespace():
    """Whitespace must be stripped from message."""
    req = ChatRequest(msg="  best headphones?  ")
    assert req.msg == "best headphones?"


def test_chat_request_rejects_blank():
    """Blank message must raise ValidationError."""
    with pytest.raises(ValidationError):
        ChatRequest(msg="   ")


def test_chat_request_rejects_empty():
    """Empty string must raise ValidationError."""
    with pytest.raises(ValidationError):
        ChatRequest(msg="")


def test_chat_request_rejects_too_long():
    """Message over 1000 chars must raise ValidationError."""
    with pytest.raises(ValidationError):
        ChatRequest(msg="a" * 1001)


def test_chat_request_accepts_max_length():
    """Message of exactly 1000 chars must be accepted."""
    req = ChatRequest(msg="a" * 1000)
    assert len(req.msg) == 1000


# ── ChatResponse ──────────────────────────────────────
def test_chat_response_valid():
    """Valid response must be created correctly."""
    res = ChatResponse(
        response="boAt headphones are great for bass.",
        request_id="abc-123",
        cached=False,
    )
    assert res.response == "boAt headphones are great for bass."
    assert res.request_id == "abc-123"
    assert res.cached is False


def test_chat_response_cached_defaults_false():
    """cached must default to False."""
    res = ChatResponse(
        response="some answer",
        request_id="req-456",
    )
    assert res.cached is False


def test_chat_response_cached_can_be_true():
    """cached must accept True."""
    res = ChatResponse(
        response="cached answer",
        request_id="req-789",
        cached=True,
    )
    assert res.cached is True


# ── HealthResponse ────────────────────────────────────
def test_health_response_valid():
    """Valid health response must be created correctly."""
    res = HealthResponse(
        status="ok",
        environment="development",
        uptime_seconds=123.5,
    )
    assert res.status == "ok"
    assert res.environment == "development"


# ── ReadyResponse ─────────────────────────────────────
def test_ready_response_valid():
    """Valid ready response must be created correctly."""
    res = ReadyResponse(status="ready", db="connected")
    assert res.status == "ready"
    assert res.db == "connected"


# ── ErrorResponse ─────────────────────────────────────
def test_error_response_valid():
    """Valid error response must be created correctly."""
    res = ErrorResponse(detail="Something went wrong", request_id="req-123")
    assert res.detail == "Something went wrong"
    assert res.request_id == "req-123"


def test_error_response_request_id_optional():
    """request_id must default to None."""
    res = ErrorResponse(detail="Something went wrong")
    assert res.request_id is None
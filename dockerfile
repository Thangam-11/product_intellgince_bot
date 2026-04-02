# Stage 1: Install dependencies in a build container
FROM python:3.10-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target=/build/packages

# Stage 2: Lean production image
FROM python:3.10-slim AS production
WORKDIR /app

# Security: run as non-root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# Copy installed packages from builder
COPY --from=builder /build/packages /app/packages

# Copy application code (owned by appuser)
COPY --chown=appuser:appgroup . .

USER appuser
ENV PYTHONPATH=/app/packages:/app
ENV PATH=/app/packages/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.rag_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
# Stage 1: Install dependencies in a build container
FROM python:3.10-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Lean production image
FROM python:3.10-slim AS production
WORKDIR /app

# Security: run as non-root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy application code
COPY --chown=appuser:appgroup . .

USER appuser

ENV PYTHONPATH=/app/src

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "rag_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
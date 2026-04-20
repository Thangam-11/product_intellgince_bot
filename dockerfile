FROM python:3.10-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim AS production
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY --chown=appuser:appgroup . .

USER appuser

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "rag_app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]


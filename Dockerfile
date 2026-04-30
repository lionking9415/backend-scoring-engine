# Backend Dockerfile for Google Cloud Run
FROM python:3.12-slim

WORKDIR /app

# System deps (gcc needed by some Python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer-cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scoring_engine/ ./scoring_engine/
COPY run_server.py .

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run injects $PORT at runtime (usually 8080).
# run_server.py reads $PORT automatically; this ENV is just the documented default.
ENV PORT=8080
EXPOSE 8080

# Health check (Cloud Run also does its own HTTP health probes)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/v1/health', timeout=4)"

# Shell form so $PORT is expanded from the environment
CMD python run_server.py --host 0.0.0.0 --port ${PORT}

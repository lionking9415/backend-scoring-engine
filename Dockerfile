# Backend Dockerfile for Google Cloud Run
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY scoring_engine/ ./scoring_engine/
COPY run_server.py .

# Expose port (Cloud Run will set PORT env var)
ENV PORT=8080

# Run the application
CMD exec uvicorn scoring_engine.api:app --host 0.0.0.0 --port ${PORT}

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv (locked versions)
RUN uv sync --locked --no-dev

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config.py ./

# Create necessary directories
RUN mkdir -p data/raw data/processed data/neo4j_backups outputs models

# Environment variables (override via docker-compose or runtime)
ENV NEO4J_URI=bolt://neo4j:7687
ENV NEO4J_USER=neo4j
ENV NEO4J_PASSWORD=fraud_detection_2024
ENV MLFLOW_TRACKING_URI=http://mlflow:5000
ENV PYTHONUNBUFFERED=1

# Default command (batch scoring)
CMD ["uv", "run", "python", "scripts/batch_scoring.py"]

# Graph-Based Fraud Detection - Production MLOps Pipeline

[![CI Pipeline](https://github.com/Diplomado-UDD/graph-fraud/actions/workflows/ci.yml/badge.svg)](https://github.com/Diplomado-UDD/graph-fraud/actions/workflows/ci.yml)
[![Deploy Pipeline](https://github.com/Diplomado-UDD/graph-fraud/actions/workflows/deploy.yml/badge.svg)](https://github.com/Diplomado-UDD/graph-fraud/actions/workflows/deploy.yml)

Educational fraud detection system demonstrating production-grade MLOps practices with graph-based machine learning and Graph RAG.

**Test Coverage**: 44/44 tests passing (100%) | **Model Performance**: 88.2% precision, 100% recall, F1-score 0.938

## Overview

This project showcases a **complete end-to-end MLOps pipeline** for fraud detection in P2P payment networks, featuring:

### Core ML Capabilities
- **Synthetic dataset generation** with realistic fraud patterns (fraud rings, money mules)
- **Graph construction** using **NetworkX** (in-memory) or **Neo4j** (production database)
- **Fraud detection algorithms** (Louvain community detection, centrality analysis, shared resource detection)
- **Graph RAG** - natural language query interface for fraud investigation
- **Optimized performance** - 88.2% precision, 100% recall, F1-score 0.938

### MLOps Infrastructure
- **Data versioning** with DVC for reproducible datasets
- **Experiment tracking** with MLflow for model lineage
- **Containerization** with Docker and Docker Compose
- **Container registry** with GitHub Container Registry (ghcr.io)
- **Monitoring** with Prometheus and Grafana
- **CI/CD** with GitHub Actions (automated testing, building, deployment)
- **API serving** with FastAPI for Graph RAG queries
- **Neo4j graph database** for production graph storage and queries

## Installation

### Prerequisites
- Python 3.12+
- Docker and Docker Compose
- Git
- `uv` package manager (used for dependency management and running project commands)

### Quick Start

```bash
# Clone repository
git clone <your-repo-url>
cd graph-fraud

# Install dependencies with locked versions
uv sync --locked

# Copy environment template
cp .env.example .env
```

See `MLOPS_SETUP.md` for complete setup instructions.

## Quick Start Workflows

### 1. Exploratory Data Analysis (Mandatory)

```bash
# Interactive EDA with marimo (optional)
uv run marimo edit notebooks/eda/01_dataset_exploration.py
uv run marimo edit notebooks/eda/02_graph_analysis.py

# Export to HTML reports
uv run marimo export html notebooks/eda/*.py
```

### 2. Train Fraud Detection Model

```bash
# Run training pipeline with MLflow tracking
uv run python scripts/train_fraud_detector.py

# View experiments in MLflow UI (MLflow server bound to host port 5001)
open http://localhost:5001
```

### 3. Batch Score Users

```bash
uv run python scripts/batch_scoring.py

# Check outputs
ls outputs/
```

### 4. Query Graph RAG API

```bash
# Health check
curl http://localhost:8000/health

# Query user fraud risk
curl -X POST http://localhost:8000/query/fraud_risk \
  -H "Content-Type: application/json" \
  -d '{"user_id": "U0001"}'

# Interactive API documentation
open http://localhost:8000/docs
```

### 5. Monitor System (Prometheus + Grafana)

```bash
# Access monitoring dashboards
open http://localhost:3000  # Grafana (admin/admin)
open http://localhost:9090  # Prometheus
```

### 6. Original Demos (Still Available)

```bash
# NetworkX in-memory demo
uv run python main.py

# Neo4j database demo
uv run python test_neo4j.py
```

## Features

(Shortened for brevity — full details in repository files and docs.)

## Project Structure

```
graph-fraud/
  src/
    data/
      generate_dataset.py    # Synthetic data generation
    models/
      graph_builder.py       # Graph construction
      fraud_detector.py      # Detection algorithms
    features/
      graph_rag.py           # Query interface
  notebooks/
    fraud_detection_demo.ipynb # Interactive demo
  data/
    raw/                        # Raw dataset storage
    processed/                  # Processed data
  main.py                         # CLI demo
  pyproject.toml                  # Dependencies
```

## Full run instructions (recommended)

This section contains step-by-step, cross-platform instructions to run the entire solution on any machine using Docker and the `uv` package manager. The repository is designed to be run without installing dependencies via `pip` on the host; use `uv` for Python dependency management and Docker / Docker Compose for services.

**Execution Context Note**: 
- **Host commands** (e.g., `uv run ...`): For local development, data generation, and accessing service UIs
- **Container commands** (e.g., `docker compose exec graph-rag-api uv run ...`): For scripts that interact with Docker services (MLflow, Neo4j). These must run inside the API container for proper networking.

Prerequisites
- Git
- Docker Engine (Docker Desktop on macOS / Windows) with Docker Compose support
- A POSIX shell (instructions use zsh / bash)
- `uv` package manager (used to manage the project virtual environment and run commands)

Notes for Apple Silicon (M1/M2/M3): the Docker images included are multi-arch where possible. If you encounter image architecture errors, try rebuilding with platform emulation:

```bash
# (optional) use platform forcing if there are compatibility issues
docker compose build --no-cache --progress=plain --platform linux/amd64
docker compose up -d --build
```

1) Clone and prepare the repository

```bash
git clone <your-repo-url>
cd graph-fraud

# Install Python dependencies into the uv-managed environment (locked versions)
uv sync --locked

# Copy the environment file and edit credentials (Neo4j, MLflow paths) if needed
cp .env.example .env
# Edit .env with an editor to set NEO4J_PASSWORD, MLFLOW_ARTIFACT_ROOT, etc.
```

2) Start the infra stack (Neo4j, MLflow, API, Prometheus, Grafana)

```bash
# Start services; -d will run in background
docker compose up -d --build

# Wait a few moments and check service status
docker compose ps
```

3) Verify services are reachable

| Service | URL | Credentials |
|---------|-----|-------------|
| **Graph RAG API** | http://localhost:8000/docs | - |
| **MLflow UI** | http://localhost:5001 | - |
| **Neo4j Browser** | http://localhost:7474 | neo4j / fraud_detection_2024 |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / admin |

You can run the included health check which verifies HTTP endpoints and performs a bolt-level Neo4j check inside the API container:

```bash
uv run python scripts/check_system_health.py
```

4) Generate or prepare the dataset

```bash
# Generate synthetic dataset (writes into data/raw/)
uv run python scripts/generate_data.py

# Or use DVC to pull versioned datasets if configured
dvc pull
```

5) Train the fraud detection model (with MLflow tracking)

**Note**: Scripts that interact with Docker services (MLflow, Neo4j) must run inside the API container.

```bash
# Run training inside the container (recommended)
docker compose exec graph-rag-api uv run python scripts/train_fraud_detector.py

# After training is finished, view experiments in MLflow UI
open http://localhost:5001
```

**Alternative**: For development/testing on host (limited functionality):
```bash
uv run python scripts/train_fraud_detector.py  # May fail due to service connectivity
```

Notes:
- MLflow artifacts and sqlite database are stored under `./mlflow/` by default. Ensure the host `./mlflow` directory is writable by Docker if you run training in containers.

6) Run batch scoring

**Note**: Scripts that interact with Docker services (MLflow, Neo4j) must run inside the API container.

```bash
# Run batch scoring inside the container (recommended)
docker compose exec graph-rag-api uv run python scripts/batch_scoring.py

# Outputs are written to ./outputs/
ls -la outputs
```

**Alternative**: For development/testing on host (limited functionality):
```bash
uv run python scripts/batch_scoring.py  # May fail due to service connectivity
```

7) Generate presentation plots and graph images (used in `docs/`)

```bash
uv run python scripts/generate_presentation_plots.py
uv run python scripts/generate_graph_images.py

# The scripts write into docs/images/ and docs/
```

8) Export MLflow runs to JSON

```bash
uv run python scripts/export_mlflow_runs.py

# Output: outputs/mlflow_runs.json
```

9) Run tests and produce coverage report

The project includes **44 comprehensive unit tests** covering all major components:

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| Data Generation | 11 | Schema validation, fraud rate, referential integrity |
| Graph Builder | 11 | NetworkX graph construction, node/edge attributes |
| Fraud Detector | 11 | Risk scoring, community detection, performance metrics |
| Graph RAG | 11 | All 7 query types, error handling, risk classification |

```bash
# Run all tests with coverage (writes html to htmlcov/)
uv run pytest --maxfail=1 -q --cov=src --cov-report=html:htmlcov

# Run specific test suite
uv run pytest tests/test_fraud_detector.py -v

# Optional: copy coverage into docs/ for a static site
cp -R htmlcov docs/coverage
```

**Test Results**: All 44 tests pass (100% success rate) in ~2 seconds

10) Troubleshooting & common issues

- If a service appears "unhealthy" in Docker, inspect logs:

```bash
docker compose logs service-name --tail=200
# Example
docker compose logs fraud-mlflow --tail=200
```

- If MLflow UI is empty after training, confirm the tracking URI and that the sqlite file exists at `./mlflow/mlflow.db` and is writeable.
- Neo4j bolt connection issues: ensure `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` values in `.env` are correct and that the bolt port (7687) is not blocked.
- If you see missing Python modules on the host, prefer running scripts via `uv run ...` which uses the locked environment, or run them inside the API container with:

```bash
docker compose exec graph-rag-api uv run python scripts/train_fraud_detector.py
```

11) CI/CD and Container Registry

The project uses **GitHub Actions** for CI/CD with three workflows:

- **CI Pipeline** (`.github/workflows/ci.yml`): Runs on every push/PR
  - Lints code and runs 44 unit tests
  - Validates marimo notebooks syntax
  - Builds Docker images
  - Validates docker-compose and Prometheus configs

- **Deploy Pipeline** (`.github/workflows/deploy.yml`): Builds and publishes container images
  - Builds batch scoring and API images
  - Pushes to GitHub Container Registry (ghcr.io)
  - Images available at: `ghcr.io/diplomado-udd/graph-fraud:main`

- **Health Check** (`.github/workflows/health-check.yml`): Full integration test
  - Starts complete MLOps stack
  - Runs training and scoring pipelines
  - Generates coverage reports
  - Collects Docker diagnostics on failure

**Pulling Published Images:**
```bash
docker pull ghcr.io/diplomado-udd/graph-fraud:main
docker pull ghcr.io/diplomado-udd/graph-fraud-api:main
```

For reproducibility, use the `uv.lock` file and provided Docker Compose files.

12) Optional: Keep the repository small

- The HTML coverage report is committed to `docs/coverage/` for convenience. If you prefer to keep the repo lean, remove it and rely on CI artifacts instead:

```bash
git rm -r docs/coverage
echo "docs/coverage/" >> .gitignore
git add .gitignore && git commit -m "ci: store coverage only in CI artifacts"
```

## License

Educational use only.

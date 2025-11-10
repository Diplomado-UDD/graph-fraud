Reproducing key workflows
==========================

This short guide explains how to start the local stack, run training, batch scoring, run Graph RAG queries and validate system health.

Prerequisites
-------------
- Docker & Docker Compose
- `uv` (project package manager) — see https://astral.sh/uv

Start the full stack
--------------------
1. Bring up the services with Docker Compose

```bash
docker compose up -d
```

2. Verify services are reachable

```bash
# MLflow UI
open http://localhost:5001
# Neo4j browser
open http://localhost:7474
# Prometheus
open http://localhost:9090
# Grafana
open http://localhost:3000
```

Run training (inside container or locally via uv)
-----------------------------------------------
Preferred: use the API container so dependencies are isolated.

```bash
docker compose run --rm -e MLFLOW_TRACKING_URI=http://fraud-mlflow:5000 graph-rag-api uv run python scripts/train_fraud_detector.py
```

Batch scoring
-------------

```bash
docker compose run --rm -e MLFLOW_TRACKING_URI=http://fraud-mlflow:5000 graph-rag-api uv run python scripts/batch_scoring.py
```

Run Graph RAG queries
---------------------

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/query/fraud_risk -H 'Content-Type: application/json' -d '{"user_id":"U0014"}'
```

Export MLflow runs to JSON
--------------------------

```bash
uv run python scripts/export_mlflow_runs.py
# Output: outputs/mlflow_runs.json
```

Run the health-check script
---------------------------

```bash
uv run python scripts/check_system_health.py
```

Notes
-----
- Always use `uv` when running Python-related tasks locally in this repo to ensure locked dependencies.
- Use Docker Compose to run the full integration stack to avoid local dependency issues.

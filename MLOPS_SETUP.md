# MLOps Pipeline Setup Guide

Complete guide for setting up and running the fraud detection MLOps pipeline.

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git
- uv package manager
- Neo4j database (installed via Homebrew or Docker)

## Quick Start

### 1. Clone and Setup Environment

```bash
git clone <your-repo-url>
cd graph-fraud

# Install dependencies
uv sync --locked

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Generate Initial Dataset

```bash
# Generate synthetic fraud dataset
uv run python scripts/generate_data.py

# Track with DVC
dvc add data/raw/
git add data/raw.dvc data/.gitignore
git commit -m "data: initial dataset v1.0"
```

### 3. Run EDA Notebooks (Mandatory)

```bash
# Start marimo server
uv run marimo edit notebooks/eda/01_dataset_exploration.py

# Or export to HTML
uv run marimo export html notebooks/eda/01_dataset_exploration.py > eda_report1.html
uv run marimo export html notebooks/eda/02_graph_analysis.py > eda_report2.html
```

### 4. Start Infrastructure with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

Services will be available at:
- **Neo4j Browser**: http://localhost:7474 (neo4j/fraud_detection_2024)
- **MLflow UI**: http://localhost:5000
- **Graph RAG API**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### 5. Train Initial Model

```bash
# Run training pipeline
uv run python scripts/train_fraud_detector.py

# Check MLflow for results
open http://localhost:5000
```

### 6. Run Batch Scoring

```bash
# Score all users
uv run python scripts/batch_scoring.py

# Check outputs
ls outputs/
```

### 7. Query Graph RAG API

```bash
# Health check
curl http://localhost:8000/health

# Query user fraud risk
curl -X POST http://localhost:8000/query/fraud_risk \
  -H "Content-Type: application/json" \
  -d '{"user_id": "U0001"}'

# Find shared devices
curl http://localhost:8000/query/shared_devices

# Access interactive docs
open http://localhost:8000/docs
```

## Airflow Setup (Optional)

If using Apache Airflow for orchestration:

```bash
# Initialize Airflow database
uv run airflow db init

# Create admin user
uv run airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com

# Start Airflow webserver
uv run airflow webserver --port 8080

# In another terminal, start scheduler
uv run airflow scheduler

# Access UI
open http://localhost:8080
```

DAGs available:
- `fraud_detection_training`: Weekly model retraining
- `batch_scoring_daily`: Daily user scoring

## DVC Remote Storage (Optional)

Configure S3 or compatible storage for DVC:

```bash
# Configure S3 remote
dvc remote add -d storage s3://fraud-detection-datasets

# Set AWS credentials
dvc remote modify storage access_key_id YOUR_ACCESS_KEY
dvc remote modify storage secret_access_key YOUR_SECRET_KEY

# Push data
dvc push

# On another machine, pull data
dvc pull
```

## Monitoring Setup

### Prometheus

Prometheus is configured to scrape metrics from all services. Access at http://localhost:9090.

### Grafana

1. Access http://localhost:3000 (admin/admin)
2. Add Prometheus datasource: http://prometheus:9090
3. Import dashboards from `monitoring/grafana/dashboards/`

### Alerts

Alert rules are defined in `monitoring/prometheus/alert_rules.yml`. Configure alertmanager for notifications (Slack, email, PagerDuty).

## CI/CD Pipeline

GitHub Actions workflows are configured in `.github/workflows/`:

### CI Pipeline (`ci.yml`)

Runs on every push/PR:
- Lint and format checks
- Unit tests
- Docker image builds
- Configuration validation
- Marimo notebook validation

### Deploy Pipeline (`deploy.yml`)

Runs on main branch and version tags:
- Build and push Docker images to registry
- Deploy to staging environment
- Deploy to production (on version tags)

**Required secrets:**
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

## Project Structure

```
graph-fraud/
├── .dvc/                  # DVC configuration
├── .github/workflows/     # CI/CD pipelines
├── config.py              # Central configuration
├── dags/                  # Airflow DAGs
├── data/
│   ├── raw/              # DVC-tracked datasets
│   ├── processed/        # Feature-engineered data
│   └── neo4j_backups/    # Graph snapshots
├── docker/               # Dockerfiles
├── docker-compose.yml    # Full stack definition
├── monitoring/
│   ├── prometheus/       # Metrics and alerts
│   └── grafana/          # Dashboards
├── notebooks/eda/        # Marimo EDA notebooks (mandatory)
├── outputs/              # Batch scoring results
├── models/               # Trained model artifacts
├── scripts/              # Training and scoring pipelines
└── src/
    ├── api/              # Graph RAG API
    ├── data/             # Dataset generation
    ├── features/         # Graph RAG implementation
    └── models/           # Fraud detection models
```

## Configuration

All configuration is centralized in `config.py` and can be overridden via environment variables:

```bash
# Dataset parameters
export N_USERS=500
export N_TRANSACTIONS=5000
export SEED=123

# Model parameters
export RISK_THRESHOLD=0.15
export TARGET_PRECISION_MIN=0.8
export TARGET_PRECISION_MAX=0.9

# Neo4j connection
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password

# MLflow tracking
export MLFLOW_TRACKING_URI=http://localhost:5000
```

## Troubleshooting

### Neo4j Connection Issues

```bash
# Check Neo4j status
brew services info neo4j

# Restart Neo4j
brew services restart neo4j

# View logs
tail -f /opt/homebrew/var/log/neo4j.log
```

### Docker Services Not Starting

```bash
# Check logs
docker-compose logs neo4j
docker-compose logs mlflow

# Restart specific service
docker-compose restart neo4j

# Rebuild images
docker-compose build --no-cache
```

### DVC Push/Pull Errors

```bash
# Verify remote configuration
dvc remote list

# Check credentials
dvc remote modify storage --local access_key_id YOUR_KEY

# Test connection
dvc pull --remote storage
```

## Best Practices

1. **Always run EDA notebooks** before model development
2. **Version all datasets** with DVC before training
3. **Tag model versions** in git: `git tag v1.0.0`
4. **Monitor precision/recall** via Grafana dashboards
5. **Review MLflow experiments** before deploying models
6. **Test API endpoints** after deployment
7. **Set up alerts** for model performance degradation

## Next Steps

1. Configure DVC remote storage for team collaboration
2. Set up GitHub secrets for CI/CD
3. Customize Grafana dashboards for your metrics
4. Configure alertmanager for notifications
5. Deploy to production infrastructure (AWS EC2/ECS)
6. Set up automated retraining schedule
7. Implement A/B testing for model updates

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Review MLflow experiments: http://localhost:5000
- Query API docs: http://localhost:8000/docs
- Monitor metrics: http://localhost:9090

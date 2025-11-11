"""
Central configuration for fraud detection MLOps pipeline
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
NEO4J_BACKUP_DIR = DATA_DIR / "neo4j_backups"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODELS_DIR = PROJECT_ROOT / "models"

# Ensure directories exist
for directory in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    NEO4J_BACKUP_DIR,
    OUTPUTS_DIR,
    MODELS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# Dataset generation parameters
SEED = int(os.getenv("SEED", "42"))
N_USERS = int(os.getenv("N_USERS", "200"))
N_TRANSACTIONS = int(os.getenv("N_TRANSACTIONS", "1000"))
FRAUD_RATE = float(os.getenv("FRAUD_RATE", "0.15"))

# Data versioning
DATA_VERSION = os.getenv("DATA_VERSION", "v1.0")

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "fraud_detection_2024")

# MLflow configuration
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "fraud-detection")
MLFLOW_ARTIFACT_ROOT = os.getenv("MLFLOW_ARTIFACT_ROOT", str(MODELS_DIR))

# Model parameters
RISK_THRESHOLD = float(os.getenv("RISK_THRESHOLD", "0.15"))

# Risk score weights
DEVICE_RISK_WEIGHT = float(os.getenv("DEVICE_RISK_WEIGHT", "0.35"))
AGE_RISK_WEIGHT = float(os.getenv("AGE_RISK_WEIGHT", "0.25"))
AMOUNT_RISK_WEIGHT = float(os.getenv("AMOUNT_RISK_WEIGHT", "0.20"))
VOLUME_RISK_WEIGHT = float(os.getenv("VOLUME_RISK_WEIGHT", "0.10"))
CENTRALITY_RISK_WEIGHT = float(os.getenv("CENTRALITY_RISK_WEIGHT", "0.10"))

# Target metrics
TARGET_PRECISION_MIN = float(os.getenv("TARGET_PRECISION_MIN", "0.8"))
TARGET_PRECISION_MAX = float(os.getenv("TARGET_PRECISION_MAX", "0.9"))
TARGET_RECALL_MIN = float(os.getenv("TARGET_RECALL_MIN", "0.95"))  # Maximize recall

# Monitoring configuration
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8001"))
METRICS_UPDATE_INTERVAL = int(os.getenv("METRICS_UPDATE_INTERVAL", "60"))  # seconds

# API configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# AWS/S3 configuration (optional)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "fraud-detection-datasets")

"""
Training pipeline for fraud detection model with MLflow tracking
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import mlflow
import mlflow.pyfunc
import pandas as pd
import json
from datetime import datetime
import config
from src.models.neo4j_graph_builder import Neo4jFraudGraph
from src.models.graph_builder import FraudGraph
from src.models.fraud_detector import FraudDetector


def load_dataset():
    """Load dataset from DVC-tracked files"""
    print("Loading dataset from DVC...")
    dataset = {}
    for name in ["users", "devices", "user_devices", "transactions", "fraud_rings"]:
        file_path = config.RAW_DATA_DIR / f"{name}.csv"
        if file_path.exists():
            dataset[name] = pd.read_csv(file_path)
        else:
            raise FileNotFoundError(f"Dataset file not found: {file_path}")

    print(
        f"  Loaded {len(dataset['users'])} users, {len(dataset['transactions'])} transactions"
    )
    return dataset


def build_neo4j_graph(dataset):
    """Build Neo4j graph from dataset"""
    print("\nBuilding Neo4j graph...")
    neo4j_graph = Neo4jFraudGraph(
        uri=config.NEO4J_URI, user=config.NEO4J_USER, password=config.NEO4J_PASSWORD
    )

    # Clear existing data
    neo4j_graph.clear_database()

    # Build graph
    neo4j_graph.build_from_dataset(dataset)

    # Verify
    stats = neo4j_graph.get_statistics()
    print(f"  Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")

    return neo4j_graph


def train_and_evaluate(neo4j_graph, dataset, risk_threshold=None):
    """Train fraud detector and evaluate performance"""
    if risk_threshold is None:
        risk_threshold = config.RISK_THRESHOLD

    print(f"\nTraining fraud detector (threshold={risk_threshold})...")

    # Build NetworkX graph for fraud detection algorithms
    nx_graph = FraudGraph()
    nx_graph.build_from_dataset(dataset)

    detector = FraudDetector(nx_graph)
    report = detector.generate_fraud_report(
        dataset["transactions"], risk_threshold=risk_threshold
    )

    # Calculate metrics
    risk_df = report["risk_scores"]
    high_risk = risk_df[risk_df["risk_score"] > risk_threshold]

    true_positives = len(high_risk[high_risk["is_fraudster"]])
    false_positives = len(high_risk[~high_risk["is_fraudster"]])
    total_fraudsters = len(risk_df[risk_df["is_fraudster"]])

    precision = true_positives / len(high_risk) if len(high_risk) > 0 else 0
    recall = true_positives / total_fraudsters if total_fraudsters > 0 else 0
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    # Detection breakdown
    ring_members = sum(
        1
        for uid in report["high_risk_users"]
        if risk_df[risk_df["user_id"] == uid]["device_risk"].values[0] > 0.5
    )
    solo_fraudsters = len(report["high_risk_users"]) - ring_members

    metrics = {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "total_fraudsters": total_fraudsters,
        "high_risk_users": len(report["high_risk_users"]),
        "ring_members_detected": ring_members,
        "solo_fraudsters_detected": solo_fraudsters,
    }

    print(f"  Precision: {precision:.3f}")
    print(f"  Recall: {recall:.3f}")
    print(f"  F1-Score: {f1_score:.3f}")
    print(f"  High-risk users: {len(report['high_risk_users'])}/{len(risk_df)}")

    return detector, report, metrics


def save_model_artifacts(report, metrics, dataset_version):
    """Save model artifacts"""
    print("\nSaving model artifacts...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_dir = config.MODELS_DIR / f"fraud_detector_{timestamp}"
    model_dir.mkdir(parents=True, exist_ok=True)

    # Save risk scores
    risk_scores_path = model_dir / "risk_scores.parquet"
    report["risk_scores"].to_parquet(risk_scores_path)

    # Save model metadata
    metadata = {
        "version": timestamp,
        "data_version": dataset_version,
        "risk_threshold": config.RISK_THRESHOLD,
        "weights": {
            "device_risk": config.DEVICE_RISK_WEIGHT,
            "age_risk": config.AGE_RISK_WEIGHT,
            "amount_risk": config.AMOUNT_RISK_WEIGHT,
            "volume_risk": config.VOLUME_RISK_WEIGHT,
            "centrality_risk": config.CENTRALITY_RISK_WEIGHT,
        },
        "metrics": metrics,
        "trained_at": datetime.now().isoformat(),
    }

    metadata_path = model_dir / "model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  Saved to {model_dir}")
    return model_dir


def main():
    print("=== Fraud Detection Training Pipeline ===\n")

    # Set up MLflow
    mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(config.MLFLOW_EXPERIMENT_NAME)

    # Load dataset
    dataset = load_dataset()

    # Load metadata
    metadata_path = config.RAW_DATA_DIR / "dataset_metadata.json"
    with open(metadata_path, "r") as f:
        dataset_metadata = json.load(f)

    # Build graph
    neo4j_graph = build_neo4j_graph(dataset)

    # Start MLflow run
    with mlflow.start_run(
        run_name=f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ):
        # Log parameters
        mlflow.log_params(
            {
                "data_version": dataset_metadata["version"],
                "seed": config.SEED,
                "n_users": config.N_USERS,
                "n_transactions": config.N_TRANSACTIONS,
                "risk_threshold": config.RISK_THRESHOLD,
                "device_risk_weight": config.DEVICE_RISK_WEIGHT,
                "age_risk_weight": config.AGE_RISK_WEIGHT,
                "amount_risk_weight": config.AMOUNT_RISK_WEIGHT,
                "volume_risk_weight": config.VOLUME_RISK_WEIGHT,
                "centrality_risk_weight": config.CENTRALITY_RISK_WEIGHT,
            }
        )

        # Train and evaluate
        detector, report, metrics = train_and_evaluate(neo4j_graph, dataset)

        # Log metrics
        mlflow.log_metrics(metrics)

        # Check if model meets criteria
        meets_criteria = (
            metrics["precision"] >= config.TARGET_PRECISION_MIN
            and metrics["precision"] <= config.TARGET_PRECISION_MAX
            and metrics["recall"] >= config.TARGET_RECALL_MIN
        )

        mlflow.log_param("meets_criteria", meets_criteria)

        if meets_criteria:
            print("\n Model meets criteria!")
            print(
                f"  Precision: {metrics['precision']:.3f} (target: {config.TARGET_PRECISION_MIN}-{config.TARGET_PRECISION_MAX})"
            )
            print(
                f"  Recall: {metrics['recall']:.3f} (target: >{config.TARGET_RECALL_MIN})"
            )

            # Save artifacts
            model_dir = save_model_artifacts(
                report, metrics, dataset_metadata["version"]
            )

            # Log artifacts to MLflow
            mlflow.log_artifacts(str(model_dir))

            # Register model
            print("\n Model registered in MLflow")
        else:
            print("\n Model does NOT meet criteria")
            print(
                f"  Precision: {metrics['precision']:.3f} (target: {config.TARGET_PRECISION_MIN}-{config.TARGET_PRECISION_MAX})"
            )
            print(
                f"  Recall: {metrics['recall']:.3f} (target: >{config.TARGET_RECALL_MIN})"
            )

    # Close Neo4j connection
    neo4j_graph.close()

    print("\n=== Training pipeline complete ===")


if __name__ == "__main__":
    main()

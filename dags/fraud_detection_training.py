"""
Airflow DAG for fraud detection training pipeline
Runs weekly or on-demand to retrain model with new data
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

default_args = {
    "owner": "mlops",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "fraud_detection_training",
    default_args=default_args,
    description="Train fraud detection model with new data",
    schedule_interval="@weekly",  # Every Sunday at midnight
    catchup=False,
    tags=["fraud-detection", "training", "ml"],
)


def generate_dataset(**context):
    """Generate new synthetic dataset"""
    import config
    from src.data.generate_dataset import FraudDatasetGenerator
    import json
    from datetime import datetime

    print("Generating new dataset...")
    generator = FraudDatasetGenerator(seed=config.SEED)
    dataset = generator.generate_dataset(
        n_users=config.N_USERS, n_transactions=config.N_TRANSACTIONS
    )

    # Save dataset
    for name, df in dataset.items():
        output_path = config.RAW_DATA_DIR / f"{name}.csv"
        df.to_csv(output_path, index=False)

    # Save metadata
    metadata = {
        "version": config.DATA_VERSION,
        "generated_at": datetime.now().isoformat(),
        "parameters": {
            "seed": config.SEED,
            "n_users": config.N_USERS,
            "n_transactions": config.N_TRANSACTIONS,
        },
    }

    metadata_path = config.RAW_DATA_DIR / "dataset_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(
        f"Dataset generated: {len(dataset['users'])} users, {len(dataset['transactions'])} transactions"
    )
    return str(metadata_path)


def validate_data_quality(**context):
    """Run data quality checks"""
    import config
    import pandas as pd

    print("Validating data quality...")

    # Load dataset
    users = pd.read_csv(config.RAW_DATA_DIR / "users.csv")
    transactions = pd.read_csv(config.RAW_DATA_DIR / "transactions.csv")

    # Quality checks
    checks_passed = True

    # Check 1: No missing values
    if users.isnull().sum().sum() > 0 or transactions.isnull().sum().sum() > 0:
        print("FAIL: Missing values detected")
        checks_passed = False

    # Check 2: Positive amounts
    if (transactions["amount"] <= 0).any():
        print("FAIL: Non-positive transaction amounts found")
        checks_passed = False

    # Check 3: Fraud rate in acceptable range
    fraud_rate = users["is_fraudster"].mean()
    if fraud_rate < 0.1 or fraud_rate > 0.25:
        print(f"WARNING: Fraud rate {fraud_rate:.1%} outside expected range (10-25%)")

    # Check 4: Referential integrity
    all_user_ids = set(users["user_id"])
    if not set(transactions["sender_id"]).issubset(all_user_ids):
        print("FAIL: Invalid sender_ids in transactions")
        checks_passed = False

    if checks_passed:
        print("All data quality checks passed")
    else:
        raise ValueError("Data quality validation failed")

    return checks_passed


def build_neo4j_graph(**context):
    """Build Neo4j graph from dataset"""
    import config
    import pandas as pd
    from src.models.neo4j_graph_builder import Neo4jFraudGraph

    print("Building Neo4j graph...")

    # Load dataset
    dataset = {}
    for name in ["users", "devices", "user_devices", "transactions", "fraud_rings"]:
        dataset[name] = pd.read_csv(config.RAW_DATA_DIR / f"{name}.csv")

    # Connect and build
    neo4j_graph = Neo4jFraudGraph(
        uri=config.NEO4J_URI, user=config.NEO4J_USER, password=config.NEO4J_PASSWORD
    )

    neo4j_graph.clear_database()
    neo4j_graph.build_from_dataset(dataset)

    stats = neo4j_graph.get_statistics()
    neo4j_graph.close()

    print(f"Graph built: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
    return stats


def train_model(**context):
    """Train fraud detection model"""
    import config
    import pandas as pd
    import mlflow
    from datetime import datetime
    from src.models.neo4j_graph_builder import Neo4jFraudGraph
    from src.models.fraud_detector import FraudDetector

    print("Training fraud detection model...")

    # Set up MLflow
    mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(config.MLFLOW_EXPERIMENT_NAME)

    # Load dataset
    dataset = {}
    for name in ["users", "devices", "user_devices", "transactions"]:
        dataset[name] = pd.read_csv(config.RAW_DATA_DIR / f"{name}.csv")

    # Connect to Neo4j
    neo4j_graph = Neo4jFraudGraph(
        uri=config.NEO4J_URI, user=config.NEO4J_USER, password=config.NEO4J_PASSWORD
    )

    with mlflow.start_run(
        run_name=f"airflow_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ):
        # Log parameters
        mlflow.log_params(
            {
                "data_version": config.DATA_VERSION,
                "risk_threshold": config.RISK_THRESHOLD,
                "n_users": len(dataset["users"]),
                "n_transactions": len(dataset["transactions"]),
            }
        )

        # Train
        detector = FraudDetector(neo4j_graph)
        report = detector.generate_fraud_report(
            dataset["transactions"], risk_threshold=config.RISK_THRESHOLD
        )

        # Calculate metrics
        risk_df = report["risk_scores"]
        high_risk = risk_df[risk_df["risk_score"] > config.RISK_THRESHOLD]

        true_positives = len(high_risk[high_risk["is_fraudster"]])
        total_fraudsters = len(risk_df[risk_df["is_fraudster"]])

        precision = true_positives / len(high_risk) if len(high_risk) > 0 else 0
        recall = true_positives / total_fraudsters if total_fraudsters > 0 else 0
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        metrics = {"precision": precision, "recall": recall, "f1_score": f1_score}

        # Log metrics
        mlflow.log_metrics(metrics)

        # Check criteria
        meets_criteria = (
            precision >= config.TARGET_PRECISION_MIN
            and precision <= config.TARGET_PRECISION_MAX
            and recall >= config.TARGET_RECALL_MIN
        )

        mlflow.log_param("meets_criteria", meets_criteria)

        print(
            f"Model trained - Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1_score:.3f}"
        )
        print(f"Meets criteria: {meets_criteria}")

        context["ti"].xcom_push(key="meets_criteria", value=meets_criteria)
        context["ti"].xcom_push(key="metrics", value=metrics)

    neo4j_graph.close()
    return metrics


# Define tasks
generate_data_task = PythonOperator(
    task_id="generate_synthetic_data",
    python_callable=generate_dataset,
    dag=dag,
)

validate_data_task = PythonOperator(
    task_id="validate_data_quality",
    python_callable=validate_data_quality,
    dag=dag,
)

track_with_dvc_task = BashOperator(
    task_id="track_data_with_dvc",
    bash_command='cd /app && dvc add data/raw/ && dvc push || echo "DVC remote not configured"',
    dag=dag,
)

build_graph_task = PythonOperator(
    task_id="build_neo4j_graph",
    python_callable=build_neo4j_graph,
    dag=dag,
)

train_model_task = PythonOperator(
    task_id="train_fraud_detector",
    python_callable=train_model,
    dag=dag,
)

# Set dependencies
(
    generate_data_task
    >> validate_data_task
    >> track_with_dvc_task
    >> build_graph_task
    >> train_model_task
)

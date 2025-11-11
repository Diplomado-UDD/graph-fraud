"""
Airflow DAG for daily batch scoring pipeline
Scores all users and generates risk reports
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

default_args = {
    "owner": "mlops",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

dag = DAG(
    "batch_scoring_daily",
    default_args=default_args,
    description="Daily batch scoring of all users",
    schedule_interval="@daily",  # Every day at midnight
    catchup=False,
    tags=["fraud-detection", "scoring", "batch"],
)


def run_batch_scoring(**context):
    """Execute batch scoring pipeline"""
    import config
    import pandas as pd
    import json
    from datetime import datetime
    from src.models.neo4j_graph_builder import Neo4jFraudGraph
    from src.models.fraud_detector import FraudDetector

    print("Running batch scoring...")

    # Connect to Neo4j
    neo4j_graph = Neo4jFraudGraph(
        uri=config.NEO4J_URI, user=config.NEO4J_USER, password=config.NEO4J_PASSWORD
    )

    # Load dataset
    dataset = {}
    for name in ["users", "devices", "user_devices", "transactions"]:
        dataset[name] = pd.read_csv(config.RAW_DATA_DIR / f"{name}.csv")

    # Run detection
    detector = FraudDetector(neo4j_graph)
    report = detector.generate_fraud_report(
        dataset["transactions"], risk_threshold=config.RISK_THRESHOLD
    )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    risk_scores_path = config.OUTPUTS_DIR / f"risk_scores_{timestamp}.csv"
    report["risk_scores"].to_csv(risk_scores_path, index=False)

    high_risk_output = config.OUTPUTS_DIR / f"high_risk_users_{timestamp}.json"
    with open(high_risk_output, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "risk_threshold": config.RISK_THRESHOLD,
                "high_risk_users": report["high_risk_users"],
                "count": len(report["high_risk_users"]),
            },
            f,
            indent=2,
        )

    print(f"Scored {len(report['risk_scores'])} users")
    print(f"High-risk users: {len(report['high_risk_users'])}")

    neo4j_graph.close()

    return {
        "total_users": len(report["risk_scores"]),
        "high_risk_users": len(report["high_risk_users"]),
        "output_file": str(risk_scores_path),
    }


# Define task
scoring_task = PythonOperator(
    task_id="run_batch_scoring",
    python_callable=run_batch_scoring,
    dag=dag,
)

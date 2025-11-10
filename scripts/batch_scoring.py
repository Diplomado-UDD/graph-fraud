"""
Batch scoring pipeline for fraud detection
Scores all users and generates risk reports
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import json
from datetime import datetime
import config
from src.models.neo4j_graph_builder import Neo4jFraudGraph
from src.models.fraud_detector import FraudDetector


def load_latest_dataset():
    """Load latest dataset from DVC"""
    print("Loading dataset...")
    dataset = {}
    for name in ["users", "devices", "user_devices", "transactions"]:
        file_path = config.RAW_DATA_DIR / f"{name}.csv"
        dataset[name] = pd.read_csv(file_path)
    return dataset


def batch_score_users():
    """Score all users and generate reports"""
    print("=== Batch Scoring Pipeline ===\n")

    # Connect to Neo4j
    print("Connecting to Neo4j...")
    neo4j_graph = Neo4jFraudGraph(
        uri=config.NEO4J_URI,
        user=config.NEO4J_USER,
        password=config.NEO4J_PASSWORD
    )

    # Load dataset
    dataset = load_latest_dataset()

    # Initialize detector
    print("Running fraud detection...")
    detector = FraudDetector(neo4j_graph)
    report = detector.generate_fraud_report(
        dataset["transactions"],
        risk_threshold=config.RISK_THRESHOLD
    )

    # Generate outputs
    risk_scores = report["risk_scores"]
    high_risk_users = report["high_risk_users"]

    print(f"  Total users scored: {len(risk_scores)}")
    print(f"  High-risk users: {len(high_risk_users)}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save risk scores
    output_path = config.OUTPUTS_DIR / f"risk_scores_{timestamp}.csv"
    risk_scores.to_csv(output_path, index=False)
    print(f"\n  Saved risk scores: {output_path}")

    # Save high-risk users list
    high_risk_output = config.OUTPUTS_DIR / f"high_risk_users_{timestamp}.json"
    with open(high_risk_output, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "risk_threshold": config.RISK_THRESHOLD,
            "high_risk_users": high_risk_users,
            "count": len(high_risk_users)
        }, f, indent=2)
    print(f"  Saved high-risk list: {high_risk_output}")

    # Close connection
    neo4j_graph.close()

    print("\n=== Batch scoring complete ===")


if __name__ == "__main__":
    batch_score_users()

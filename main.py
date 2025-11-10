"""Main entry point for fraud detection demo."""

from src.data.generate_dataset import FraudDatasetGenerator
from src.models.graph_builder import FraudGraph
from src.models.fraud_detector import FraudDetector
from src.features.graph_rag import GraphRAG


def main():
    """Run fraud detection pipeline."""
    print("=== Graph-Based Fraud Detection Demo ===\n")

    # Generate dataset
    print("1. Generating synthetic dataset...")
    generator = FraudDatasetGenerator(seed=42)
    dataset = generator.generate_dataset(n_users=200, n_transactions=1000)

    for name, df in dataset.items():
        print(f"   {name}: {len(df)} records")

    # Build graph
    print("\n2. Building fraud graph...")
    fraud_graph = FraudGraph()
    fraud_graph.build_from_dataset(dataset)

    stats = fraud_graph.get_statistics()
    print(f"   Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")

    # Detect fraud
    print("\n3. Running fraud detection algorithms...")
    detector = FraudDetector(fraud_graph)
    report = detector.generate_fraud_report(dataset["transactions"])

    print(f"   Communities detected: {len(set(report['communities'].values()))}")
    print(f"   High-risk users: {len(report['high_risk_users'])}")
    print(f"   Shared devices: {len(report['shared_resources'])}")

    # Graph RAG queries
    print("\n4. Graph RAG Analysis...")
    graph_rag = GraphRAG(fraud_graph, detector, dataset)

    if report["high_risk_users"]:
        user_id = report["high_risk_users"][0]
        risk_info = graph_rag.query("fraud_risk", user_id=user_id)

        print(f"\n   High-Risk User: {user_id}")
        print(f"   Risk Score: {risk_info['risk_score']:.3f}")
        print(f"   Risk Level: {risk_info['risk_level']}")
        print(f"   Actual Fraudster: {risk_info['is_actual_fraudster']}")

    # Detection performance
    patterns = graph_rag.query("suspicious_patterns", top_n=10)
    print("\n5. Detection Performance:")
    for metric, value in patterns["detection_accuracy"].items():
        print(f"   {metric}: {value}")

    print("\n=== Done! Run notebooks/fraud_detection_demo.ipynb for detailed analysis ===")


if __name__ == "__main__":
    main()

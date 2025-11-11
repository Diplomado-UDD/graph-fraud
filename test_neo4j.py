"""Test Neo4j integration with fraud detection."""

from src.data.generate_dataset import FraudDatasetGenerator
from src.models.neo4j_graph_builder import Neo4jFraudGraph


def main():
    """Test Neo4j graph builder."""
    print("=== Neo4j Fraud Detection Test ===\n")

    # Initialize Neo4j connection
    print("1. Connecting to Neo4j...")
    neo4j_graph = Neo4jFraudGraph(
        uri="bolt://localhost:7687", user="neo4j", password="fraud_detection_2024"
    )
    print("   ✓ Connected successfully\n")

    # Clear existing data
    print("2. Clearing existing data...")
    neo4j_graph.clear_database()
    print("   ✓ Database cleared\n")

    # Generate dataset
    print("3. Generating synthetic dataset...")
    generator = FraudDatasetGenerator(seed=42)
    dataset = generator.generate_dataset(n_users=50, n_transactions=200)
    print(
        f"   Users: {len(dataset['users'])} ({dataset['users']['is_fraudster'].sum()} fraudsters)"
    )
    print(f"   Transactions: {len(dataset['transactions'])}\n")

    # Build graph in Neo4j
    print("4. Building graph in Neo4j...")
    neo4j_graph.build_from_dataset(dataset)
    print("   ✓ Graph built successfully\n")

    # Get statistics
    print("5. Graph statistics:")
    stats = neo4j_graph.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()

    # Find shared devices
    print("6. Detecting shared devices...")
    shared = neo4j_graph.get_shared_devices()
    print(f"   Shared devices found: {len(shared)}")
    for device_id, users in list(shared.items())[:3]:
        print(f"   - {device_id}: {len(users)} users")
    print()

    # Test transaction paths
    print("7. Testing transaction path queries...")
    users = dataset["users"]["user_id"].head(5).tolist()
    if len(users) >= 2:
        paths = neo4j_graph.get_transaction_paths(users[0], users[1])
        print(f"   Paths from {users[0]} to {users[1]}: {len(paths)}")
    print()

    print("✓ Neo4j integration test complete!")
    print("\n=== Access Neo4j Browser ===")
    print("URL: http://localhost:7474")
    print("Username: neo4j")
    print("Password: fraud_detection_2024")
    print("\nTry these queries in the browser:")
    print("1. View all users: MATCH (u:User) RETURN u LIMIT 25")
    print(
        "2. View fraud network: MATCH (u:User {is_fraudster: true})-[r]->(n) RETURN u, r, n"
    )
    print(
        "3. Find shared devices: MATCH (u:User)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(u2:User) RETURN u, d, u2"
    )

    # Close connection
    neo4j_graph.close()


if __name__ == "__main__":
    main()

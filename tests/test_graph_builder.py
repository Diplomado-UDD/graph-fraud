"""Unit tests for graph construction."""

import pytest
from src.data.generate_dataset import FraudDatasetGenerator
from src.models.graph_builder import FraudGraph


class TestFraudGraph:
    """Test NetworkX graph builder."""

    @pytest.fixture
    def dataset(self):
        """Generate small test dataset."""
        generator = FraudDatasetGenerator(seed=42)
        return generator.generate_dataset(n_users=30, n_transactions=50)

    @pytest.fixture
    def graph(self, dataset):
        """Build graph from test dataset."""
        fraud_graph = FraudGraph()
        fraud_graph.build_from_dataset(dataset)
        return fraud_graph

    def test_graph_initialization(self):
        """Test graph initializes empty."""
        graph = FraudGraph()
        assert graph.G is not None
        assert len(graph.G.nodes) == 0
        assert len(graph.G.edges) == 0

    def test_graph_build(self, graph):
        """Test graph builds successfully."""
        stats = graph.get_statistics()

        assert stats["total_nodes"] > 0
        assert stats["total_edges"] > 0
        assert stats["user_nodes"] > 0
        assert stats["device_nodes"] > 0

    def test_user_nodes_created(self, graph, dataset):
        """Test all users become nodes."""
        stats = graph.get_statistics()
        n_users = len(dataset["users"])

        assert stats["user_nodes"] == n_users

    def test_device_nodes_created(self, graph, dataset):
        """Test devices become nodes."""
        stats = graph.get_statistics()
        n_devices = len(dataset["devices"])

        assert stats["device_nodes"] == n_devices

    def test_transaction_edges_created(self, graph, dataset):
        """Test transactions create edges."""
        completed_transactions = len(
            dataset["transactions"][dataset["transactions"]["status"] == "completed"]
        )

        # Count transaction edges
        transaction_edges = [
            e
            for e in graph.G.edges(data=True)
            if e[2].get("edge_type") == "transaction"
        ]

        # Should have transaction edges (at least some)
        assert len(transaction_edges) > 0
        # Should not exceed total completed transactions
        assert len(transaction_edges) <= completed_transactions

    def test_node_attributes(self, graph, dataset):
        """Test nodes have correct attributes."""
        # Check a user node
        user_id = dataset["users"]["user_id"].iloc[0]
        user_node = graph.G.nodes[user_id]

        assert "node_type" in user_node
        assert user_node["node_type"] == "user"
        assert "is_fraudster" in user_node
        assert "account_age_days" in user_node

    def test_edge_attributes(self, graph, dataset):
        """Test edges have correct attributes."""
        # Find a completed transaction edge
        completed = dataset["transactions"][
            dataset["transactions"]["status"] == "completed"
        ]
        if len(completed) > 0:
            sender = completed["sender_id"].iloc[0]
            receiver = completed["receiver_id"].iloc[0]

            if graph.G.has_edge(sender, receiver):
                edge_data = graph.G.get_edge_data(sender, receiver)
                assert "edge_type" in edge_data
                assert "amount" in edge_data

    def test_get_user_neighbors(self, graph, dataset):
        """Test getting user neighbors."""
        user_id = dataset["users"]["user_id"].iloc[0]
        neighbors = list(graph.G.neighbors(user_id))

        # Should be a list (may be empty)
        assert isinstance(neighbors, list)

    def test_get_shared_devices(self, graph):
        """Test shared device detection."""
        shared = graph.get_shared_devices()

        # Should be a dict
        assert isinstance(shared, dict)

    def test_get_transaction_paths(self, graph, dataset):
        """Test finding paths between users."""
        users = dataset["users"]["user_id"].head(2).tolist()

        if len(users) >= 2:
            paths = graph.get_transaction_paths(users[0], users[1], max_depth=3)
            assert isinstance(paths, list)

    def test_statistics_keys(self, graph):
        """Test statistics contain expected keys."""
        stats = graph.get_statistics()

        required_keys = ["total_nodes", "total_edges", "user_nodes", "device_nodes"]
        for key in required_keys:
            assert key in stats

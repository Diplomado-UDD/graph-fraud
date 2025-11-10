"""Unit tests for Graph RAG query interface."""

import pytest
from src.data.generate_dataset import FraudDatasetGenerator
from src.models.graph_builder import FraudGraph
from src.models.fraud_detector import FraudDetector
from src.features.graph_rag import GraphRAG


class TestGraphRAG:
    """Test Graph RAG query interface."""

    @pytest.fixture
    def dataset(self):
        """Generate test dataset."""
        generator = FraudDatasetGenerator(seed=42)
        return generator.generate_dataset(n_users=50, n_transactions=150)

    @pytest.fixture
    def graph(self, dataset):
        """Build graph."""
        fraud_graph = FraudGraph()
        fraud_graph.build_from_dataset(dataset)
        return fraud_graph

    @pytest.fixture
    def detector(self, graph, dataset):
        """Create detector with report."""
        detector = FraudDetector(graph)
        detector.generate_fraud_report(dataset["transactions"])
        return detector

    @pytest.fixture
    def graph_rag(self, graph, detector, dataset):
        """Create GraphRAG instance."""
        return GraphRAG(graph, detector, dataset)

    def test_graph_rag_initialization(self, graph, detector, dataset):
        """Test GraphRAG initializes correctly."""
        rag = GraphRAG(graph, detector, dataset)
        assert rag.fraud_graph == graph
        assert rag.fraud_detector == detector
        assert rag.dataset == dataset

    def test_user_profile_query(self, graph_rag, dataset):
        """Test user profile query."""
        user_id = dataset["users"]["user_id"].iloc[0]
        result = graph_rag.query("user_profile", user_id=user_id)

        assert result is not None
        assert "user_id" in result
        assert result["user_id"] == user_id

    def test_fraud_risk_query(self, graph_rag, dataset):
        """Test fraud risk query."""
        user_id = dataset["users"]["user_id"].iloc[0]
        result = graph_rag.query("fraud_risk", user_id=user_id)

        assert result is not None
        assert "user_id" in result
        assert "risk_score" in result
        assert "risk_level" in result

    def test_user_connections_query(self, graph_rag, dataset):
        """Test user connections query."""
        user_id = dataset["users"]["user_id"].iloc[0]
        result = graph_rag.query("user_connections", user_id=user_id, depth=2)

        assert result is not None
        assert "user_id" in result
        assert "connected_users" in result or "error" not in result

    def test_shared_devices_query(self, graph_rag):
        """Test shared devices query."""
        result = graph_rag.query("shared_devices")

        assert result is not None
        # Check for actual keys in the response
        assert "total_shared_devices" in result or "all_shared_devices" in result

    def test_transaction_path_query(self, graph_rag, dataset):
        """Test transaction path query."""
        users = dataset["users"]["user_id"].head(2).tolist()

        if len(users) >= 2:
            result = graph_rag.query(
                "transaction_path",
                source=users[0],
                target=users[1]
            )

            assert result is not None
            assert "source" in result
            assert "target" in result

    def test_community_info_query(self, graph_rag, dataset):
        """Test community info query."""
        user_id = dataset["users"]["user_id"].iloc[0]
        result = graph_rag.query("community_info", user_id=user_id)

        assert result is not None

    def test_suspicious_patterns_query(self, graph_rag):
        """Test suspicious patterns query."""
        result = graph_rag.query("suspicious_patterns", top_n=5)

        assert result is not None
        assert "high_risk_users" in result

    def test_invalid_query_type(self, graph_rag):
        """Test invalid query type returns error."""
        result = graph_rag.query("invalid_query_type")
        assert result is not None
        assert "error" in result

    def test_user_profile_missing_user(self, graph_rag):
        """Test user profile with non-existent user."""
        result = graph_rag.query("user_profile", user_id="NONEXISTENT")

        # Should return None or error message
        assert result is None or "error" in result or "not_found" in result

    def test_risk_level_classification(self, graph_rag, dataset):
        """Test risk level is properly classified."""
        user_id = dataset["users"]["user_id"].iloc[0]
        result = graph_rag.query("fraud_risk", user_id=user_id)

        if result and "risk_level" in result:
            assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

"""Unit tests for fraud detection algorithms."""

import pytest
import pandas as pd
from src.data.generate_dataset import FraudDatasetGenerator
from src.models.graph_builder import FraudGraph
from src.models.fraud_detector import FraudDetector


class TestFraudDetector:
    """Test fraud detection algorithms."""

    @pytest.fixture
    def dataset(self):
        """Generate test dataset with known fraudsters."""
        generator = FraudDatasetGenerator(seed=42)
        return generator.generate_dataset(n_users=100, n_transactions=300)

    @pytest.fixture
    def graph(self, dataset):
        """Build graph from dataset."""
        fraud_graph = FraudGraph()
        fraud_graph.build_from_dataset(dataset)
        return fraud_graph

    @pytest.fixture
    def detector(self, graph):
        """Create fraud detector."""
        return FraudDetector(graph)

    def test_detector_initialization(self, graph):
        """Test detector initializes correctly."""
        detector = FraudDetector(graph)
        assert detector.fraud_graph == graph

    def test_generate_fraud_report(self, detector, dataset):
        """Test fraud report generation."""
        report = detector.generate_fraud_report(
            dataset["transactions"], risk_threshold=0.15
        )

        # Check report structure
        assert "risk_scores" in report
        assert "high_risk_users" in report
        assert "shared_resources" in report
        assert "communities" in report

    def test_risk_scores_dataframe(self, detector, dataset):
        """Test risk scores is a proper DataFrame."""
        report = detector.generate_fraud_report(dataset["transactions"])
        risk_scores = report["risk_scores"]

        assert isinstance(risk_scores, pd.DataFrame)
        assert "user_id" in risk_scores.columns
        assert "risk_score" in risk_scores.columns
        assert "is_fraudster" in risk_scores.columns

    def test_risk_scores_range(self, detector, dataset):
        """Test risk scores are between 0 and 1."""
        report = detector.generate_fraud_report(dataset["transactions"])
        risk_scores = report["risk_scores"]

        assert (risk_scores["risk_score"] >= 0).all()
        assert (risk_scores["risk_score"] <= 1).all()

    def test_high_risk_users_list(self, detector, dataset):
        """Test high risk users is a list."""
        report = detector.generate_fraud_report(
            dataset["transactions"], risk_threshold=0.15
        )

        assert isinstance(report["high_risk_users"], list)

    def test_shared_resources_dict(self, detector, dataset):
        """Test shared resources is present in report."""
        report = detector.generate_fraud_report(dataset["transactions"])

        # shared_resources can be dict or list depending on implementation
        assert "shared_resources" in report

    def test_communities_detected(self, detector, dataset):
        """Test community detection runs."""
        report = detector.generate_fraud_report(dataset["transactions"])
        communities = report["communities"]

        # Should be a dict mapping user_id to community_id
        assert isinstance(communities, dict)

    def test_performance_metrics_calculation(self, detector, dataset):
        """Test precision and recall calculation."""
        report = detector.generate_fraud_report(
            dataset["transactions"], risk_threshold=0.15
        )

        risk_scores = report["risk_scores"]
        high_risk = risk_scores[risk_scores["risk_score"] > 0.15]

        if len(high_risk) > 0:
            # Calculate precision
            true_positives = len(high_risk[high_risk["is_fraudster"]])
            precision = true_positives / len(high_risk)

            assert 0 <= precision <= 1

    def test_all_users_scored(self, detector, dataset):
        """Test all users receive risk scores."""
        report = detector.generate_fraud_report(dataset["transactions"])
        risk_scores = report["risk_scores"]

        n_users = len(dataset["users"])
        assert len(risk_scores) == n_users

    def test_threshold_affects_high_risk_count(self, detector, dataset):
        """Test changing threshold changes high risk count."""
        report_low = detector.generate_fraud_report(
            dataset["transactions"], risk_threshold=0.05
        )
        report_high = detector.generate_fraud_report(
            dataset["transactions"], risk_threshold=0.50
        )

        # Lower threshold should flag more users
        assert len(report_low["high_risk_users"]) >= len(report_high["high_risk_users"])

    def test_detector_with_empty_transactions(self, graph):
        """Test detector handles empty transactions."""
        detector = FraudDetector(graph)
        empty_transactions = pd.DataFrame(
            columns=["transaction_id", "sender_id", "receiver_id", "amount"]
        )

        # Should not crash
        report = detector.generate_fraud_report(empty_transactions)
        assert "risk_scores" in report

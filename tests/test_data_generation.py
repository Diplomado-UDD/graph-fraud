"""Unit tests for synthetic data generation."""

import pytest
from src.data.generate_dataset import FraudDatasetGenerator


class TestFraudDatasetGenerator:
    """Test synthetic fraud dataset generation."""

    @pytest.fixture
    def generator(self):
        """Create generator with fixed seed."""
        return FraudDatasetGenerator(seed=42)

    def test_generator_initialization(self, generator):
        """Test generator initializes with fraud rings list."""
        assert generator.fraud_rings is not None
        assert isinstance(generator.fraud_rings, list)

    def test_generate_dataset_structure(self, generator):
        """Test dataset has correct structure."""
        dataset = generator.generate_dataset(n_users=50, n_transactions=100)

        # Check all required tables exist
        assert "users" in dataset
        assert "devices" in dataset
        assert "user_devices" in dataset
        assert "transactions" in dataset
        assert "fraud_rings" in dataset

    def test_users_table_schema(self, generator):
        """Test users table has correct schema."""
        dataset = generator.generate_dataset(n_users=50, n_transactions=100)
        users = dataset["users"]

        # Check columns
        required_columns = ["user_id", "account_age_days", "is_fraudster"]
        for col in required_columns:
            assert col in users.columns

        # Check data types
        assert users["user_id"].dtype == object
        assert users["account_age_days"].dtype in [int, "int64"]
        assert users["is_fraudster"].dtype == bool

    def test_transactions_table_schema(self, generator):
        """Test transactions table has correct schema."""
        dataset = generator.generate_dataset(n_users=50, n_transactions=100)
        transactions = dataset["transactions"]

        # Check columns
        required_columns = [
            "transaction_id",
            "sender_id",
            "receiver_id",
            "amount",
            "timestamp",
        ]
        for col in required_columns:
            assert col in transactions.columns

        # Check positive amounts
        assert (transactions["amount"] > 0).all()

    def test_fraud_rate(self, generator):
        """Test fraud rate is within expected range."""
        dataset = generator.generate_dataset(n_users=200, n_transactions=1000)
        users = dataset["users"]

        fraud_rate = users["is_fraudster"].mean()
        assert (
            0.1 <= fraud_rate <= 0.25
        ), f"Fraud rate {fraud_rate:.2%} outside expected range"

    def test_referential_integrity(self, generator):
        """Test referential integrity between tables."""
        dataset = generator.generate_dataset(n_users=50, n_transactions=100)

        users = dataset["users"]
        transactions = dataset["transactions"]
        devices = dataset["devices"]
        user_devices = dataset["user_devices"]

        # All user IDs
        all_user_ids = set(users["user_id"])

        # Transaction senders/receivers must be valid users
        assert set(transactions["sender_id"]).issubset(all_user_ids)
        assert set(transactions["receiver_id"]).issubset(all_user_ids)

        # User devices must reference valid users
        assert set(user_devices["user_id"]).issubset(all_user_ids)

        # User devices must reference valid devices
        all_device_ids = set(devices["device_id"])
        assert set(user_devices["device_id"]).issubset(all_device_ids)

    def test_fraud_rings_exist(self, generator):
        """Test fraud rings are created."""
        dataset = generator.generate_dataset(n_users=200, n_transactions=1000)
        fraud_rings = dataset["fraud_rings"]

        # Should have fraud rings
        assert len(fraud_rings) > 0

        # Rings should have ring_id and members columns
        assert "ring_id" in fraud_rings.columns
        assert "members" in fraud_rings.columns

    def test_reproducibility(self):
        """Test same seed produces consistent structure."""
        gen1 = FraudDatasetGenerator(seed=123)
        gen2 = FraudDatasetGenerator(seed=123)

        dataset1 = gen1.generate_dataset(n_users=50, n_transactions=100)
        dataset2 = gen2.generate_dataset(n_users=50, n_transactions=100)

        # Check structure is identical
        assert len(dataset1["users"]) == len(dataset2["users"])
        assert len(dataset1["transactions"]) == len(dataset2["transactions"])
        # Check fraud flags are identical
        assert (
            dataset1["users"]["is_fraudster"] == dataset2["users"]["is_fraudster"]
        ).all()

    def test_no_missing_values(self, generator):
        """Test dataset has no missing values."""
        dataset = generator.generate_dataset(n_users=50, n_transactions=100)

        for name, df in dataset.items():
            assert df.isnull().sum().sum() == 0, f"Missing values found in {name}"

    def test_user_count(self, generator):
        """Test correct number of users generated."""
        n_users = 100
        dataset = generator.generate_dataset(n_users=n_users, n_transactions=500)

        assert len(dataset["users"]) == n_users

    def test_transaction_count(self, generator):
        """Test correct number of transactions generated."""
        n_transactions = 500
        dataset = generator.generate_dataset(n_users=100, n_transactions=n_transactions)

        assert len(dataset["transactions"]) == n_transactions

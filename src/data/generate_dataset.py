"""Generate synthetic fraud detection dataset."""

import random
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd


class FraudDatasetGenerator:
    """Generate synthetic P2P payment data with fraud patterns."""

    def __init__(self, seed: int = 42):
        """Initialize generator with random seed."""
        random.seed(seed)
        np.random.seed(seed)
        self.fraud_rings: List[List[int]] = []

    def generate_users(
        self, n_users: int = 200, fraud_rate: float = 0.02
    ) -> pd.DataFrame:
        """Generate user entities."""
        n_fraudsters = int(n_users * fraud_rate)

        users = []
        for i in range(n_users):
            users.append(
                {
                    "user_id": f"U{i:04d}",
                    "is_fraudster": i < n_fraudsters,
                    "account_age_days": (
                        random.randint(1, 1000)
                        if i >= n_fraudsters
                        else random.randint(1, 90)
                    ),
                    "verification_level": (
                        random.choice(["basic", "verified", "premium"])
                        if i >= n_fraudsters
                        else "basic"
                    ),
                }
            )

        return pd.DataFrame(users)

    def generate_fraud_rings(
        self, users_df: pd.DataFrame, n_rings: int = 3
    ) -> List[List[str]]:
        """Create fraud rings - groups of fraudsters sharing resources."""
        fraudsters = users_df[users_df["is_fraudster"]]["user_id"].tolist()

        rings = []
        fraudsters_copy = fraudsters.copy()
        random.shuffle(fraudsters_copy)

        for i in range(n_rings):
            ring_size = random.randint(3, 7)
            if len(fraudsters_copy) >= ring_size:
                ring = fraudsters_copy[:ring_size]
                fraudsters_copy = fraudsters_copy[ring_size:]
                rings.append(ring)

        self.fraud_rings = rings
        return rings

    def generate_devices(self, users_df: pd.DataFrame) -> pd.DataFrame:
        """Generate device entities and user-device relationships."""
        devices = []
        user_devices = []

        device_id = 0

        # Normal users: 1-2 devices each
        normal_users = users_df[~users_df["is_fraudster"]]["user_id"].tolist()
        for user_id in normal_users:
            n_devices = random.randint(1, 2)
            for _ in range(n_devices):
                device_name = f"D{device_id:04d}"
                devices.append(
                    {
                        "device_id": device_name,
                        "device_type": random.choice(["mobile", "desktop", "tablet"]),
                    }
                )
                user_devices.append({"user_id": user_id, "device_id": device_name})
                device_id += 1

        # Fraud rings: share devices
        for ring in self.fraud_rings:
            shared_devices = []
            n_shared = random.randint(1, 3)
            for _ in range(n_shared):
                device_name = f"D{device_id:04d}"
                devices.append(
                    {
                        "device_id": device_name,
                        "device_type": "mobile",
                    }
                )
                shared_devices.append(device_name)
                device_id += 1

            for user_id in ring:
                for device_name in shared_devices:
                    user_devices.append({"user_id": user_id, "device_id": device_name})

        # Other fraudsters: individual devices
        other_fraudsters = [
            uid
            for uid in users_df[users_df["is_fraudster"]]["user_id"].tolist()
            if not any(uid in ring for ring in self.fraud_rings)
        ]
        for user_id in other_fraudsters:
            device_name = f"D{device_id:04d}"
            devices.append(
                {
                    "device_id": device_name,
                    "device_type": "mobile",
                }
            )
            user_devices.append({"user_id": user_id, "device_id": device_name})
            device_id += 1

        return pd.DataFrame(devices), pd.DataFrame(user_devices)

    def generate_transactions(
        self,
        users_df: pd.DataFrame,
        n_transactions: int = 1000,
        start_date: datetime = None,
    ) -> pd.DataFrame:
        """Generate transaction data with fraud patterns."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=180)

        transactions = []
        fraudsters = set(users_df[users_df["is_fraudster"]]["user_id"].tolist())
        normal_users = users_df[~users_df["is_fraudster"]]["user_id"].tolist()

        for i in range(n_transactions):
            # Determine if transaction involves fraud
            if random.random() < 0.3 and fraudsters:  # 30% fraud transactions
                # Fraudster transactions
                sender = random.choice(list(fraudsters))

                # Fraud patterns
                if random.random() < 0.6:  # Money mule pattern
                    receiver = random.choice(normal_users)
                else:  # Fraud ring internal
                    same_ring = [ring for ring in self.fraud_rings if sender in ring]
                    if same_ring:
                        receiver = random.choice(same_ring[0])
                    else:
                        receiver = random.choice(list(fraudsters))

                amount = random.uniform(100, 5000)  # Higher amounts
                is_fraudulent = True
            else:
                # Normal transactions
                sender = random.choice(normal_users)
                receiver = random.choice(normal_users)
                while receiver == sender:
                    receiver = random.choice(normal_users)

                amount = random.uniform(5, 500)  # Lower amounts
                is_fraudulent = False

            timestamp = start_date + timedelta(minutes=random.randint(0, 180 * 24 * 60))

            transactions.append(
                {
                    "transaction_id": f"T{i:05d}",
                    "sender_id": sender,
                    "receiver_id": receiver,
                    "amount": round(amount, 2),
                    "timestamp": timestamp,
                    "is_fraudulent": is_fraudulent,
                    "status": random.choice(
                        ["completed", "completed", "completed", "pending"]
                    ),
                }
            )

        return (
            pd.DataFrame(transactions).sort_values("timestamp").reset_index(drop=True)
        )

    def generate_dataset(
        self, n_users: int = 200, n_transactions: int = 1000
    ) -> Dict[str, pd.DataFrame]:
        """Generate complete fraud detection dataset."""
        users_df = self.generate_users(n_users)
        self.generate_fraud_rings(users_df)
        devices_df, user_devices_df = self.generate_devices(users_df)
        transactions_df = self.generate_transactions(users_df, n_transactions)

        return {
            "users": users_df,
            "devices": devices_df,
            "user_devices": user_devices_df,
            "transactions": transactions_df,
            "fraud_rings": pd.DataFrame(
                {
                    "ring_id": [f"R{i}" for i in range(len(self.fraud_rings))],
                    "members": [",".join(ring) for ring in self.fraud_rings],
                }
            ),
        }

    def save_dataset(
        self, dataset: Dict[str, pd.DataFrame], output_dir: str = "data/raw"
    ):
        """Save dataset to CSV files."""
        import os

        os.makedirs(output_dir, exist_ok=True)

        for name, df in dataset.items():
            df.to_csv(f"{output_dir}/{name}.csv", index=False)
            print(f"Saved {name}.csv: {len(df)} records")

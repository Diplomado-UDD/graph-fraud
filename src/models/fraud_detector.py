"""Fraud detection algorithms using graph analysis."""

from typing import Dict, List, Tuple

import community as community_louvain
import networkx as nx
import pandas as pd


class FraudDetector:
    """Apply graph-based fraud detection algorithms."""

    def __init__(self, fraud_graph):
        """Initialize detector with fraud graph."""
        self.fraud_graph = fraud_graph
        self.G = fraud_graph.G
        self.transaction_network = fraud_graph.transaction_network

    def detect_communities(self) -> Dict[str, int]:
        """Detect communities using Louvain method."""
        # Only consider user-to-user connections for communities
        user_subgraph = self.G.subgraph([
            n for n in self.G.nodes()
            if self.G.nodes[n].get("node_type") == "user"
        ])

        if len(user_subgraph.nodes()) == 0:
            return {}

        # Convert to undirected if needed
        if isinstance(user_subgraph, nx.DiGraph):
            user_subgraph = user_subgraph.to_undirected()

        communities = community_louvain.best_partition(user_subgraph)
        return communities

    def calculate_centrality_scores(self) -> pd.DataFrame:
        """Calculate various centrality metrics for users."""
        user_nodes = [
            n for n in self.transaction_network.nodes()
            if self.transaction_network.nodes[n].get("is_fraudster") is not None
        ]

        if not user_nodes:
            return pd.DataFrame()

        # PageRank - identifies influential nodes
        pagerank = nx.pagerank(self.transaction_network)

        # In/Out degree centrality
        in_degree = dict(self.transaction_network.in_degree())
        out_degree = dict(self.transaction_network.out_degree())

        # Betweenness centrality - identifies nodes in key paths
        betweenness = nx.betweenness_centrality(self.transaction_network)

        scores = []
        for node in user_nodes:
            scores.append({
                "user_id": node,
                "pagerank": pagerank.get(node, 0),
                "in_degree": in_degree.get(node, 0),
                "out_degree": out_degree.get(node, 0),
                "betweenness": betweenness.get(node, 0),
                "is_fraudster": self.transaction_network.nodes[node]["is_fraudster"],
            })

        return pd.DataFrame(scores)

    def detect_shared_resources(self) -> List[Dict]:
        """Detect users sharing devices (fraud ring indicator)."""
        shared_devices = self.fraud_graph.get_shared_devices()

        results = []
        for device_id, user_list in shared_devices.items():
            fraud_count = sum(
                1 for u in user_list
                if self.G.nodes[u].get("is_fraudster", False)
            )

            results.append({
                "device_id": device_id,
                "shared_by_count": len(user_list),
                "shared_by": user_list,
                "fraudster_count": fraud_count,
                "risk_score": fraud_count / len(user_list) if user_list else 0,
            })

        return sorted(results, key=lambda x: x["risk_score"], reverse=True)

    def calculate_transaction_velocity(self, transactions_df: pd.DataFrame, window_hours: int = 24) -> pd.DataFrame:
        """Calculate transaction velocity (fraud indicator)."""
        from datetime import timedelta

        transactions_df = transactions_df.sort_values("timestamp")

        velocity_data = []
        for user_id in transactions_df["sender_id"].unique():
            user_txns = transactions_df[transactions_df["sender_id"] == user_id].sort_values("timestamp")

            if len(user_txns) < 2:
                continue

            for i, row in user_txns.iterrows():
                window_start = row["timestamp"] - timedelta(hours=window_hours)
                recent_txns = user_txns[
                    (user_txns["timestamp"] >= window_start) &
                    (user_txns["timestamp"] <= row["timestamp"])
                ]

                velocity_data.append({
                    "user_id": user_id,
                    "transaction_id": row["transaction_id"],
                    "timestamp": row["timestamp"],
                    "txn_count_24h": len(recent_txns),
                    "txn_amount_24h": recent_txns["amount"].sum(),
                })

        return pd.DataFrame(velocity_data)

    def compute_risk_scores(self, centrality_df: pd.DataFrame, shared_resources: List[Dict], transactions_df: pd.DataFrame = None) -> pd.DataFrame:
        """Combine signals into risk scores."""
        # Normalize centrality scores
        risk_df = centrality_df.copy()

        for col in ["pagerank", "betweenness"]:
            if col in risk_df.columns and risk_df[col].max() > 0:
                risk_df[f"{col}_norm"] = risk_df[col] / risk_df[col].max()
            else:
                risk_df[f"{col}_norm"] = 0

        # Add shared device risk
        device_risk = {}
        for resource in shared_resources:
            for user_id in resource["shared_by"]:
                device_risk[user_id] = max(device_risk.get(user_id, 0), resource["risk_score"])

        risk_df["device_risk"] = risk_df["user_id"].map(device_risk).fillna(0)

        # Add account age risk (younger accounts = higher risk)
        risk_df["account_age_days"] = risk_df["user_id"].map(
            lambda uid: self.G.nodes[uid].get("account_age_days", 365)
        )
        # Normalize: accounts < 90 days are suspicious (fraud avg ~44, normal avg ~467)
        risk_df["age_risk"] = (90 - risk_df["account_age_days"].clip(upper=90)) / 90

        # Add transaction-based risks
        if transactions_df is not None:
            # Transaction amount risk
            user_avg_amounts = transactions_df.groupby("sender_id")["amount"].mean()
            risk_df["avg_txn_amount"] = risk_df["user_id"].map(user_avg_amounts).fillna(0)
            # Normalize: amounts > $500 are suspicious (fraud avg ~$2493, normal avg ~$247)
            risk_df["amount_risk"] = (risk_df["avg_txn_amount"] - 500).clip(lower=0) / 2500

            # Transaction volume risk
            user_txn_counts = transactions_df[transactions_df["sender_id"].isin(risk_df["user_id"])].groupby("sender_id").size()
            risk_df["txn_count"] = risk_df["user_id"].map(user_txn_counts).fillna(0)
            # Normalize: > 7 transactions is suspicious (fraud avg ~10.5, normal avg ~4)
            risk_df["volume_risk"] = (risk_df["txn_count"] - 7).clip(lower=0) / 15
        else:
            risk_df["age_risk"] = 0
            risk_df["amount_risk"] = 0
            risk_df["volume_risk"] = 0

        # Composite risk score - multiple signals
        risk_df["risk_score"] = (
            0.05 * risk_df["pagerank_norm"] +
            0.05 * risk_df["betweenness_norm"] +
            0.35 * risk_df["device_risk"] +
            0.25 * risk_df["age_risk"] +
            0.20 * risk_df["amount_risk"] +
            0.10 * risk_df["volume_risk"]
        )

        return risk_df.sort_values("risk_score", ascending=False)

    def generate_fraud_report(self, transactions_df: pd.DataFrame, risk_threshold: float = 0.15) -> Dict:
        """Generate comprehensive fraud detection report."""
        communities = self.detect_communities()
        centrality_df = self.calculate_centrality_scores()
        shared_resources = self.detect_shared_resources()
        risk_df = self.compute_risk_scores(centrality_df, shared_resources, transactions_df)

        # Community analysis
        community_df = pd.DataFrame([
            {"user_id": k, "community": v} for k, v in communities.items()
        ])

        if not community_df.empty:
            community_df = community_df.merge(
                risk_df[["user_id", "is_fraudster"]],
                on="user_id",
                how="left"
            )

            community_stats = community_df.groupby("community").agg({
                "user_id": "count",
                "is_fraudster": "sum",
            }).rename(columns={"user_id": "size", "is_fraudster": "fraudster_count"})
            community_stats["fraud_rate"] = community_stats["fraudster_count"] / community_stats["size"]
        else:
            community_stats = pd.DataFrame()

        return {
            "communities": communities,
            "community_stats": community_stats,
            "centrality_scores": centrality_df,
            "shared_resources": shared_resources,
            "risk_scores": risk_df,
            "high_risk_users": risk_df[risk_df["risk_score"] > risk_threshold]["user_id"].tolist(),
            "risk_threshold": risk_threshold,
        }

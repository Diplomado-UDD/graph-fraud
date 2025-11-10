"""Graph RAG - Query interface for fraud detection graph."""

from typing import Dict, List, Any

import pandas as pd


class GraphRAG:
    """Retrieval-Augmented interface for querying fraud graph."""

    def __init__(self, fraud_graph, fraud_detector, dataset: Dict[str, pd.DataFrame]):
        """Initialize RAG with graph and detector."""
        self.fraud_graph = fraud_graph
        self.fraud_detector = fraud_detector
        self.dataset = dataset
        self.G = fraud_graph.G
        self.transaction_network = fraud_graph.transaction_network

    def query(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """Execute structured query on graph."""
        query_handlers = {
            "user_profile": self._query_user_profile,
            "user_connections": self._query_user_connections,
            "fraud_risk": self._query_fraud_risk,
            "shared_devices": self._query_shared_devices,
            "transaction_path": self._query_transaction_path,
            "community_info": self._query_community_info,
            "suspicious_patterns": self._query_suspicious_patterns,
        }

        handler = query_handlers.get(query_type)
        if not handler:
            return {"error": f"Unknown query type: {query_type}"}

        return handler(**kwargs)

    def _query_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user profile."""
        if user_id not in self.G:
            return {"error": f"User {user_id} not found"}

        user_attrs = self.G.nodes[user_id]
        neighbors = list(self.G.neighbors(user_id))

        # Get devices
        devices = [n for n in neighbors if self.G.nodes[n].get("node_type") == "device"]

        # Get transaction stats
        user_txns = self.dataset["transactions"][
            (self.dataset["transactions"]["sender_id"] == user_id) |
            (self.dataset["transactions"]["receiver_id"] == user_id)
        ]

        return {
            "user_id": user_id,
            "is_fraudster": user_attrs.get("is_fraudster"),
            "account_age_days": user_attrs.get("account_age_days"),
            "verification_level": user_attrs.get("verification_level"),
            "connected_users": len([n for n in neighbors if self.G.nodes[n].get("node_type") == "user"]),
            "devices": devices,
            "total_transactions": len(user_txns),
            "sent_transactions": len(user_txns[user_txns["sender_id"] == user_id]),
            "received_transactions": len(user_txns[user_txns["receiver_id"] == user_id]),
        }

    def _query_user_connections(self, user_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get user's network connections."""
        if user_id not in self.G:
            return {"error": f"User {user_id} not found"}

        subgraph = self.fraud_graph.get_user_subgraph(user_id, depth)

        users = [n for n in subgraph.nodes() if subgraph.nodes[n].get("node_type") == "user"]
        devices = [n for n in subgraph.nodes() if subgraph.nodes[n].get("node_type") == "device"]

        fraudsters = [n for n in users if subgraph.nodes[n].get("is_fraudster")]

        return {
            "user_id": user_id,
            "depth": depth,
            "connected_users": len(users) - 1,  # Exclude self
            "shared_devices": len(devices),
            "fraudsters_in_network": len([u for u in fraudsters if u != user_id]),
            "fraud_exposure_rate": len([u for u in fraudsters if u != user_id]) / max(len(users) - 1, 1),
            "subgraph_nodes": list(subgraph.nodes()),
        }

    def _query_fraud_risk(self, user_id: str) -> Dict[str, Any]:
        """Calculate fraud risk for user."""
        centrality_df = self.fraud_detector.calculate_centrality_scores()
        shared_resources = self.fraud_detector.detect_shared_resources()
        risk_df = self.fraud_detector.compute_risk_scores(centrality_df, shared_resources, self.dataset["transactions"])

        user_risk = risk_df[risk_df["user_id"] == user_id]

        if user_risk.empty:
            return {"error": f"No risk data for user {user_id}"}

        user_risk_row = user_risk.iloc[0]

        # Find if user shares devices
        shared_device_info = [
            r for r in shared_resources
            if user_id in r["shared_by"]
        ]

        risk_factors = []
        if user_risk_row["pagerank_norm"] > 0.5:
            risk_factors.append("High PageRank - central in transaction network")
        if user_risk_row["betweenness_norm"] > 0.5:
            risk_factors.append("High betweenness - key intermediary in transactions")
        if user_risk_row["device_risk"] > 0.5:
            risk_factors.append("Shares devices with known fraudsters")

        return {
            "user_id": user_id,
            "risk_score": float(user_risk_row["risk_score"]),
            "risk_level": "HIGH" if user_risk_row["risk_score"] > 0.5 else "MEDIUM" if user_risk_row["risk_score"] > 0.3 else "LOW",
            "pagerank": float(user_risk_row["pagerank"]),
            "betweenness": float(user_risk_row["betweenness"]),
            "device_risk": float(user_risk_row["device_risk"]),
            "shared_devices_count": len(shared_device_info),
            "risk_factors": risk_factors,
            "is_actual_fraudster": bool(user_risk_row["is_fraudster"]),
        }

    def _query_shared_devices(self) -> Dict[str, Any]:
        """Get all shared device information."""
        shared_resources = self.fraud_detector.detect_shared_resources()

        return {
            "total_shared_devices": len(shared_resources),
            "high_risk_devices": [r for r in shared_resources if r["risk_score"] > 0.5],
            "all_shared_devices": shared_resources[:10],  # Top 10
        }

    def _query_transaction_path(self, source: str, target: str, max_depth: int = 3) -> Dict[str, Any]:
        """Find transaction paths between users."""
        paths = self.fraud_graph.get_transaction_paths(source, target, max_depth)

        return {
            "source": source,
            "target": target,
            "paths_found": len(paths),
            "paths": paths[:5],  # Top 5 paths
            "shortest_path_length": len(paths[0]) - 1 if paths else None,
        }

    def _query_community_info(self, user_id: str = None) -> Dict[str, Any]:
        """Get community detection information."""
        communities = self.fraud_detector.detect_communities()

        if not communities:
            return {"error": "No communities detected"}

        if user_id:
            if user_id not in communities:
                return {"error": f"User {user_id} not in any community"}

            community_id = communities[user_id]
            community_members = [u for u, c in communities.items() if c == community_id]

            fraudsters = [
                u for u in community_members
                if self.G.nodes[u].get("is_fraudster")
            ]

            return {
                "user_id": user_id,
                "community_id": community_id,
                "community_size": len(community_members),
                "community_members": community_members,
                "fraudsters_in_community": len(fraudsters),
                "fraud_rate": len(fraudsters) / len(community_members),
            }
        else:
            # Overall community stats
            community_sizes = {}
            for user, comm in communities.items():
                community_sizes[comm] = community_sizes.get(comm, 0) + 1

            return {
                "total_communities": len(set(communities.values())),
                "avg_community_size": sum(community_sizes.values()) / len(community_sizes),
                "largest_community_size": max(community_sizes.values()),
                "community_distribution": dict(sorted(community_sizes.items(), key=lambda x: x[1], reverse=True)[:5]),
            }

    def _query_suspicious_patterns(self, top_n: int = 10, risk_threshold: float = 0.15) -> Dict[str, Any]:
        """Identify suspicious patterns in the graph."""
        centrality_df = self.fraud_detector.calculate_centrality_scores()
        shared_resources = self.fraud_detector.detect_shared_resources()
        risk_df = self.fraud_detector.compute_risk_scores(centrality_df, shared_resources, self.dataset["transactions"])

        high_risk = risk_df[risk_df["risk_score"] > risk_threshold].head(top_n)

        patterns = {
            "high_risk_users": high_risk[["user_id", "risk_score", "is_fraudster"]].to_dict("records"),
            "shared_device_clusters": [r for r in shared_resources if r["shared_by_count"] > 2][:5],
            "detection_accuracy": self._calculate_detection_accuracy(risk_df, risk_threshold),
        }

        return patterns

    def _calculate_detection_accuracy(self, risk_df: pd.DataFrame, risk_threshold: float = 0.15) -> Dict[str, float]:
        """Calculate how well risk scores identify actual fraudsters."""
        if risk_df.empty:
            return {}

        # High risk threshold
        high_risk_users = risk_df[risk_df["risk_score"] > risk_threshold]

        if len(high_risk_users) == 0:
            return {"precision": 0.0, "recall": 0.0}

        true_positives = len(high_risk_users[high_risk_users["is_fraudster"] == True])
        false_positives = len(high_risk_users[high_risk_users["is_fraudster"] == False])

        total_fraudsters = len(risk_df[risk_df["is_fraudster"] == True])

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / total_fraudsters if total_fraudsters > 0 else 0

        return {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(2 * (precision * recall) / (precision + recall), 3) if (precision + recall) > 0 else 0,
        }

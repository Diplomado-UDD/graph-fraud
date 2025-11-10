"""Build graph structures from fraud detection data."""

from typing import Dict

import networkx as nx
import pandas as pd


class FraudGraph:
    """Build and manage fraud detection graph."""

    def __init__(self):
        """Initialize empty graph."""
        self.G = nx.Graph()
        self.transaction_network = nx.DiGraph()

    def build_from_dataset(self, dataset: Dict[str, pd.DataFrame]) -> None:
        """Construct graph from dataset components."""
        users_df = dataset["users"]
        devices_df = dataset["devices"]
        user_devices_df = dataset["user_devices"]
        transactions_df = dataset["transactions"]

        # Add user nodes
        for _, user in users_df.iterrows():
            self.G.add_node(
                user["user_id"],
                node_type="user",
                is_fraudster=user["is_fraudster"],
                account_age_days=user["account_age_days"],
                verification_level=user["verification_level"],
            )

        # Add device nodes
        for _, device in devices_df.iterrows():
            self.G.add_node(
                device["device_id"],
                node_type="device",
                device_type=device["device_type"],
            )

        # Add user-device edges
        for _, rel in user_devices_df.iterrows():
            self.G.add_edge(
                rel["user_id"],
                rel["device_id"],
                edge_type="uses_device",
            )

        # Build transaction network (directed)
        for _, user in users_df.iterrows():
            self.transaction_network.add_node(
                user["user_id"],
                is_fraudster=user["is_fraudster"],
                account_age_days=user["account_age_days"],
            )

        # Add transaction edges
        for _, txn in transactions_df.iterrows():
            if txn["status"] == "completed":
                # Add to main graph
                self.G.add_edge(
                    txn["sender_id"],
                    txn["receiver_id"],
                    edge_type="transaction",
                    amount=txn["amount"],
                    timestamp=txn["timestamp"],
                    is_fraudulent=txn["is_fraudulent"],
                )

                # Add to transaction network (accumulate amounts)
                if self.transaction_network.has_edge(txn["sender_id"], txn["receiver_id"]):
                    self.transaction_network[txn["sender_id"]][txn["receiver_id"]]["total_amount"] += txn["amount"]
                    self.transaction_network[txn["sender_id"]][txn["receiver_id"]]["transaction_count"] += 1
                else:
                    self.transaction_network.add_edge(
                        txn["sender_id"],
                        txn["receiver_id"],
                        total_amount=txn["amount"],
                        transaction_count=1,
                    )

    def get_user_subgraph(self, user_id: str, depth: int = 1) -> nx.Graph:
        """Extract subgraph around a specific user."""
        if user_id not in self.G:
            return nx.Graph()

        nodes = {user_id}
        for _ in range(depth):
            neighbors = set()
            for node in nodes:
                neighbors.update(self.G.neighbors(node))
            nodes.update(neighbors)

        return self.G.subgraph(nodes).copy()

    def get_shared_devices(self) -> Dict[str, list]:
        """Find devices shared by multiple users."""
        shared = {}
        for node in self.G.nodes():
            if self.G.nodes[node].get("node_type") == "device":
                users = [n for n in self.G.neighbors(node) if self.G.nodes[n].get("node_type") == "user"]
                if len(users) > 1:
                    shared[node] = users
        return shared

    def get_transaction_paths(self, source: str, target: str, max_depth: int = 3) -> list:
        """Find transaction paths between two users."""
        try:
            paths = nx.all_simple_paths(
                self.transaction_network,
                source=source,
                target=target,
                cutoff=max_depth,
            )
            return list(paths)
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            return []

    def get_statistics(self) -> Dict:
        """Compute basic graph statistics."""
        user_nodes = [n for n in self.G.nodes() if self.G.nodes[n].get("node_type") == "user"]
        device_nodes = [n for n in self.G.nodes() if self.G.nodes[n].get("node_type") == "device"]

        return {
            "total_nodes": self.G.number_of_nodes(),
            "total_edges": self.G.number_of_edges(),
            "user_nodes": len(user_nodes),
            "device_nodes": len(device_nodes),
            "avg_degree": sum(dict(self.G.degree()).values()) / self.G.number_of_nodes() if self.G.number_of_nodes() > 0 else 0,
            "connected_components": nx.number_connected_components(self.G),
            "transaction_edges": self.transaction_network.number_of_edges(),
        }

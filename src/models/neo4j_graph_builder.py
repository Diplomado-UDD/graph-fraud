"""Build graph structures in Neo4j from fraud detection data."""

from typing import Dict
import pandas as pd
from neo4j import GraphDatabase
import networkx as nx


class Neo4jFraudGraph:
    """Build and manage fraud detection graph in Neo4j."""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "neo4j",
    ):
        """Initialize Neo4j connection."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connection()
        # Keep an in-memory NetworkX representation so other components (FraudDetector)
        # can operate on a NetworkX graph even when the canonical store is Neo4j.
        self.G = nx.MultiDiGraph()
        self.transaction_network = nx.DiGraph()

    def _verify_connection(self):
        """Verify Neo4j connection is working."""
        with self.driver.session() as session:
            result = session.run("RETURN 1 AS test")
            result.single()

    def close(self):
        """Close Neo4j driver connection."""
        self.driver.close()

    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def build_from_dataset(self, dataset: Dict[str, pd.DataFrame]) -> None:
        """Construct graph from dataset components."""
        users_df = dataset["users"]
        devices_df = dataset["devices"]
        user_devices_df = dataset["user_devices"]
        transactions_df = dataset["transactions"]

        with self.driver.session() as session:
            # Create constraints and indexes
            session.run(
                "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT device_id IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE"
            )
            session.run(
                "CREATE INDEX user_fraudster IF NOT EXISTS FOR (u:User) ON (u.is_fraudster)"
            )

            # Create user nodes
            for _, user in users_df.iterrows():
                session.run(
                    """
                    CREATE (u:User {
                        user_id: $user_id,
                        is_fraudster: $is_fraudster,
                        account_age_days: $account_age_days,
                        verification_level: $verification_level
                    })
                    """,
                    user_id=user["user_id"],
                    is_fraudster=bool(user["is_fraudster"]),
                    account_age_days=int(user["account_age_days"]),
                    verification_level=user["verification_level"],
                )

            # Create device nodes
            for _, device in devices_df.iterrows():
                session.run(
                    """
                    CREATE (d:Device {
                        device_id: $device_id,
                        device_type: $device_type
                    })
                    """,
                    device_id=device["device_id"],
                    device_type=device["device_type"],
                )

            # Create user-device relationships
            for _, rel in user_devices_df.iterrows():
                session.run(
                    """
                    MATCH (u:User {user_id: $user_id})
                    MATCH (d:Device {device_id: $device_id})
                    CREATE (u)-[:USES_DEVICE]->(d)
                    """,
                    user_id=rel["user_id"],
                    device_id=rel["device_id"],
                )

            # Create transaction relationships
            for _, txn in transactions_df.iterrows():
                if txn["status"] == "completed":
                    session.run(
                        """
                        MATCH (sender:User {user_id: $sender_id})
                        MATCH (receiver:User {user_id: $receiver_id})
                        MERGE (sender)-[t:TRANSACTED {transaction_id: $transaction_id}]->(receiver)
                        ON CREATE SET
                            t.amount = $amount,
                            t.timestamp = datetime($timestamp),
                            t.is_fraudulent = $is_fraudulent
                        """,
                        sender_id=txn["sender_id"],
                        receiver_id=txn["receiver_id"],
                        transaction_id=txn["transaction_id"],
                        amount=float(txn["amount"]),
                        timestamp=str(txn["timestamp"]).replace(" ", "T"),
                        is_fraudulent=bool(txn["is_fraudulent"]),
                    )

        # Also build an in-memory NetworkX graph mirror for algorithms that expect NetworkX
        # User nodes
        for _, user in users_df.iterrows():
            uid = user["user_id"]
            self.G.add_node(
                uid,
                node_type="user",
                is_fraudster=bool(user["is_fraudster"]),
                account_age_days=int(user["account_age_days"]),
            )
            # transaction network uses users only
            self.transaction_network.add_node(
                uid, is_fraudster=bool(user["is_fraudster"])
            )

        # Device nodes
        for _, device in devices_df.iterrows():
            did = device["device_id"]
            self.G.add_node(
                did, node_type="device", device_type=device.get("device_type")
            )

        # User-device edges
        for _, rel in user_devices_df.iterrows():
            uid = rel["user_id"]
            did = rel["device_id"]
            # Add in Neo4j we already created; mirror in NetworkX
            if uid not in self.G:
                self.G.add_node(uid, node_type="user")
            if did not in self.G:
                self.G.add_node(did, node_type="device")
            self.G.add_edge(uid, did, relation="USES_DEVICE")

        # Transactions -> transaction_network (directed)
        for _, txn in transactions_df.iterrows():
            if txn["status"] == "completed":
                s = txn["sender_id"]
                r = txn["receiver_id"]
                tid = txn["transaction_id"]
                amt = float(txn["amount"])
                is_fraud = bool(txn["is_fraudulent"])
                # ensure nodes
                if s not in self.transaction_network:
                    self.transaction_network.add_node(s, is_fraudster=False)
                if r not in self.transaction_network:
                    self.transaction_network.add_node(r, is_fraudster=False)
                self.transaction_network.add_edge(
                    s, r, transaction_id=tid, amount=amt, is_fraudulent=is_fraud
                )

    def get_shared_devices(self) -> Dict[str, list]:
        """Find devices shared by multiple users."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User)-[:USES_DEVICE]->(d:Device)
                WITH d, collect(u.user_id) AS users
                WHERE size(users) > 1
                RETURN d.device_id AS device_id, users
                """
            )
            return {record["device_id"]: record["users"] for record in result}

    def get_user_subgraph(self, user_id: str, depth: int = 1) -> Dict:
        """Extract subgraph around a specific user."""
        with self.driver.session() as session:
            # Build query with literal depth value
            query = f"""
                MATCH path = (u:User {{user_id: $user_id}})-[*1..{depth}]-(connected)
                RETURN path
            """
            result = session.run(query, user_id=user_id)
            paths = list(result)
            return {"paths": paths, "user_id": user_id}

    def get_transaction_paths(
        self, source: str, target: str, max_depth: int = 3
    ) -> list:
        """Find transaction paths between two users."""
        with self.driver.session() as session:
            # Build query with literal max_depth value (Cypher doesn't support parameterized path lengths)
            query = f"""
                MATCH path = (source:User {{user_id: $source}})-[:TRANSACTED*1..{max_depth}]->(target:User {{user_id: $target}})
                RETURN [node in nodes(path) | node.user_id] AS path
                LIMIT 10
            """
            result = session.run(query, source=source, target=target)
            return [record["path"] for record in result]

    def get_statistics(self) -> Dict:
        """Compute basic graph statistics."""
        with self.driver.session() as session:
            # Count nodes by type
            users_count = session.run(
                "MATCH (u:User) RETURN count(u) AS count"
            ).single()["count"]
            devices_count = session.run(
                "MATCH (d:Device) RETURN count(d) AS count"
            ).single()["count"]

            # Count relationships
            uses_device_count = session.run(
                "MATCH ()-[r:USES_DEVICE]->() RETURN count(r) AS count"
            ).single()["count"]
            transaction_count = session.run(
                "MATCH ()-[r:TRANSACTED]->() RETURN count(r) AS count"
            ).single()["count"]

            return {
                "total_nodes": users_count + devices_count,
                "user_nodes": users_count,
                "device_nodes": devices_count,
                "total_edges": uses_device_count + transaction_count,
                "uses_device_edges": uses_device_count,
                "transaction_edges": transaction_count,
            }

    def run_community_detection(self) -> Dict[str, int]:
        """Run Louvain community detection using Graph Data Science library."""
        with self.driver.session() as session:
            # Create in-memory projection
            session.run(
                """
                CALL gds.graph.project(
                    'fraudGraph',
                    'User',
                    {
                        TRANSACTED: {orientation: 'UNDIRECTED'}
                    }
                )
                """
            )

            # Run Louvain
            result = session.run(
                """
                CALL gds.louvain.stream('fraudGraph')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).user_id AS user_id, communityId
                """
            )

            communities = {
                record["user_id"]: record["communityId"] for record in result
            }

            # Drop projection
            session.run("CALL gds.graph.drop('fraudGraph')")

            return communities

    def calculate_pagerank(self) -> pd.DataFrame:
        """Calculate PageRank using Graph Data Science library."""
        with self.driver.session() as session:
            # Create projection
            session.run(
                """
                CALL gds.graph.project(
                    'transactionGraph',
                    'User',
                    'TRANSACTED'
                )
                """
            )

            # Run PageRank
            result = session.run(
                """
                CALL gds.pageRank.stream('transactionGraph')
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).user_id AS user_id,
                       gds.util.asNode(nodeId).is_fraudster AS is_fraudster,
                       score
                ORDER BY score DESC
                """
            )

            data = [
                {
                    "user_id": r["user_id"],
                    "pagerank": r["score"],
                    "is_fraudster": r["is_fraudster"],
                }
                for r in result
            ]

            # Drop projection
            session.run("CALL gds.graph.drop('transactionGraph')")

            return pd.DataFrame(data)

    def load_networkx_from_neo4j(self) -> None:
        """Populate the in-memory NetworkX graphs from the current Neo4j database state."""
        # Clear existing in-memory graphs
        self.G = nx.MultiDiGraph()
        self.transaction_network = nx.DiGraph()

        with self.driver.session() as session:
            # Load users
            users = session.run(
                "MATCH (u:User) RETURN u.user_id AS user_id, u.is_fraudster AS is_fraudster, u.account_age_days AS account_age_days"
            )
            for rec in users:
                uid = rec["user_id"]
                self.G.add_node(
                    uid,
                    node_type="user",
                    is_fraudster=bool(rec.get("is_fraudster", False)),
                    account_age_days=int(rec.get("account_age_days") or 0),
                )
                self.transaction_network.add_node(
                    uid, is_fraudster=bool(rec.get("is_fraudster", False))
                )

            # Load devices
            devices = session.run(
                "MATCH (d:Device) RETURN d.device_id AS device_id, d.device_type AS device_type"
            )
            for rec in devices:
                did = rec["device_id"]
                self.G.add_node(
                    did, node_type="device", device_type=rec.get("device_type")
                )

            # Load user-device relationships
            uds = session.run(
                "MATCH (u:User)-[:USES_DEVICE]->(d:Device) RETURN u.user_id AS user_id, d.device_id AS device_id"
            )
            for rec in uds:
                uid = rec["user_id"]
                did = rec["device_id"]
                if uid not in self.G:
                    self.G.add_node(uid, node_type="user")
                if did not in self.G:
                    self.G.add_node(did, node_type="device")
                self.G.add_edge(uid, did, relation="USES_DEVICE")

            # Load transactions
            txns = session.run(
                "MATCH (s:User)-[t:TRANSACTED]->(r:User) RETURN s.user_id AS sender, r.user_id AS receiver, t.transaction_id AS transaction_id, t.amount AS amount, t.is_fraudulent AS is_fraudulent"
            )
            for rec in txns:
                s = rec["sender"]
                r = rec["receiver"]
                tid = rec.get("transaction_id")
                amt = float(rec.get("amount") or 0)
                is_fraud = bool(rec.get("is_fraudulent", False))
                if s not in self.transaction_network:
                    self.transaction_network.add_node(s, is_fraudster=False)
                if r not in self.transaction_network:
                    self.transaction_network.add_node(r, is_fraudster=False)
                self.transaction_network.add_edge(
                    s, r, transaction_id=tid, amount=amt, is_fraudulent=is_fraud
                )

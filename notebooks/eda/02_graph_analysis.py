"""
EDA Notebook 2: Graph Analysis
Network structure analysis and community detection using Neo4j
"""

import marimo

__generated_with = "0.17.7"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import networkx as nx
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path.cwd().parent.parent))

    from src.data.generate_dataset import FraudDatasetGenerator
    from src.models.graph_builder import FraudGraph
    from src.models.fraud_detector import FraudDetector

    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = (12, 6)

    mo.md("# Graph Structure Analysis")
    return (
        FraudDatasetGenerator,
        FraudDetector,
        FraudGraph,
        Path,
        mo,
        np,
        nx,
        pd,
        plt,
        sns,
        sys,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## 1. Build Graph from Dataset

    Construct NetworkX graph representation of fraud detection data.
    """
    )
    return


@app.cell
def __(FraudDatasetGenerator, FraudGraph):
    # Generate dataset
    SEED = 42
    generator = FraudDatasetGenerator(seed=SEED)
    dataset = generator.generate_dataset(n_users=200, n_transactions=1000)

    # Build graph
    fraud_graph = FraudGraph()
    fraud_graph.build_from_dataset(dataset)

    G = fraud_graph.G
    transaction_network = fraud_graph.transaction_network
    return (
        G,
        SEED,
        dataset,
        fraud_graph,
        generator,
        transaction_network,
    )


@app.cell
def __(fraud_graph, mo, pd):
    stats = fraud_graph.get_statistics()
    stats_df = pd.DataFrame([stats]).T
    stats_df.columns = ["Value"]

    mo.md(
        f"""
    ## 2. Graph Statistics

    {mo.as_html(stats_df)}

    **Interpretation:**
    - Multi-type graph with Users and Devices as nodes
    - Edges represent device usage and transactions
    - Connected components indicate network structure
    """
    )
    return stats, stats_df


@app.cell
def __(mo):
    mo.md(
        """
    ## 3. Degree Distribution Analysis
    """
    )
    return


@app.cell
def __(G, mo, np, plt):
    # Calculate degree distribution
    degrees = [G.degree(n) for n in G.nodes()]

    # Separate by node type
    user_degrees = [
        G.degree(n) for n in G.nodes() if G.nodes[n].get("node_type") == "user"
    ]
    device_degrees = [
        G.degree(n) for n in G.nodes() if G.nodes[n].get("node_type") == "device"
    ]

    fig_degree, axes_deg = plt.subplots(1, 3, figsize=(16, 5))

    # Overall degree distribution
    axes_deg[0].hist(degrees, bins=30, edgecolor="black", alpha=0.7)
    axes_deg[0].set_title("Overall Degree Distribution")
    axes_deg[0].set_xlabel("Degree")
    axes_deg[0].set_ylabel("Count")
    axes_deg[0].axvline(
        np.mean(degrees),
        color="red",
        linestyle="--",
        label=f"Mean: {np.mean(degrees):.2f}",
    )
    axes_deg[0].legend()

    # User degree distribution
    axes_deg[1].hist(
        user_degrees, bins=20, edgecolor="black", alpha=0.7, color="skyblue"
    )
    axes_deg[1].set_title("User Node Degree Distribution")
    axes_deg[1].set_xlabel("Degree")
    axes_deg[1].set_ylabel("Count")
    axes_deg[1].axvline(
        np.mean(user_degrees),
        color="red",
        linestyle="--",
        label=f"Mean: {np.mean(user_degrees):.2f}",
    )
    axes_deg[1].legend()

    # Device degree distribution
    axes_deg[2].hist(
        device_degrees, bins=15, edgecolor="black", alpha=0.7, color="lightcoral"
    )
    axes_deg[2].set_title("Device Node Degree Distribution")
    axes_deg[2].set_xlabel("Degree")
    axes_deg[2].set_ylabel("Count")
    axes_deg[2].axvline(
        np.mean(device_degrees),
        color="red",
        linestyle="--",
        label=f"Mean: {np.mean(device_degrees):.2f}",
    )
    axes_deg[2].legend()

    plt.tight_layout()
    fig_degree_final = plt.gcf()
    plt.close()

    mo.md(
        f"""
    {mo.as_html(fig_degree_final)}

    **Key Observations:**
    - Most nodes have low degree (few connections)
    - Some high-degree hubs (shared devices or active users)
    - Average user degree: {np.mean(user_degrees):.2f}
    - Average device degree: {np.mean(device_degrees):.2f}
    """
    )
    return (
        axes_deg,
        degrees,
        device_degrees,
        fig_degree,
        fig_degree_final,
        user_degrees,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## 4. Community Detection (Louvain Algorithm)
    """
    )
    return


@app.cell
def __(FraudDetector, fraud_graph, mo, pd):
    detector = FraudDetector(fraud_graph)
    communities = detector.detect_communities()

    # Community size distribution
    community_sizes = pd.Series(communities.values()).value_counts().sort_index()

    mo.md(
        f"""
    ### Community Structure

    - **Total communities detected**: {len(community_sizes)}
    - **Largest community size**: {community_sizes.max()}
    - **Smallest community size**: {community_sizes.min()}
    - **Average community size**: {community_sizes.mean():.1f}

    Communities represent groups of users with dense transaction connections.
    Fraud rings often form distinct communities.
    """
    )
    return communities, community_sizes, detector


@app.cell
def __(communities, dataset, mo, pd, plt):
    # Analyze fraud concentration in communities
    community_fraud_analysis = []
    users_df_comm = dataset["users"]

    for comm_id in set(communities.values()):
        comm_members = [u for u, c in communities.items() if c == comm_id]
        fraud_count = sum(
            1
            for uid in comm_members
            if users_df_comm[users_df_comm["user_id"] == uid]["is_fraudster"].any()
        )
        community_fraud_analysis.append(
            {
                "Community ID": comm_id,
                "Size": len(comm_members),
                "Fraudsters": fraud_count,
                "Fraud Rate": (
                    fraud_count / len(comm_members) if len(comm_members) > 0 else 0
                ),
            }
        )

    comm_fraud_df = pd.DataFrame(community_fraud_analysis).sort_values(
        "Fraud Rate", ascending=False
    )

    # Plot fraud rate by community
    fig_comm, ax_comm = plt.subplots(figsize=(12, 6))
    ax_comm.bar(
        comm_fraud_df["Community ID"], comm_fraud_df["Fraud Rate"], color="coral"
    )
    ax_comm.set_xlabel("Community ID")
    ax_comm.set_ylabel("Fraud Rate")
    ax_comm.set_title("Fraud Rate by Community")
    ax_comm.axhline(
        y=0.15, color="red", linestyle="--", label="Overall Fraud Rate (15%)"
    )
    ax_comm.legend()
    plt.tight_layout()
    fig_comm_final = plt.gcf()
    plt.close()

    mo.md(
        f"""
    ### Fraud Concentration by Community

    {mo.as_html(comm_fraud_df.head(10))}

    {mo.as_html(fig_comm_final)}

    **High-risk communities** (fraud rate > 50%) should be investigated for fraud rings.
    """
    )
    return (
        ax_comm,
        comm_fraud_df,
        comm_id,
        comm_members,
        community_fraud_analysis,
        fig_comm,
        fig_comm_final,
        fraud_count,
        uid,
        users_df_comm,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## 5. Centrality Analysis
    """
    )
    return


@app.cell
def __(detector, mo, pd):
    # Calculate centrality scores
    centrality_df = detector.calculate_centrality_scores()

    # Top users by centrality
    top_pagerank = centrality_df.nlargest(10, "pagerank")[
        ["user_id", "pagerank", "is_fraudster"]
    ]
    top_betweenness = centrality_df.nlargest(10, "betweenness")[
        ["user_id", "betweenness", "is_fraudster"]
    ]

    mo.md(
        f"""
    ### Centrality Metrics

    Centrality measures identify influential nodes in the transaction network.

    #### Top 10 Users by PageRank
    {mo.as_html(top_pagerank)}

    #### Top 10 Users by Betweenness Centrality
    {mo.as_html(top_betweenness)}

    **Interpretation:**
    - High PageRank: Influential users receiving many transactions
    - High betweenness: Bridge users connecting different parts of network
    - Many high-centrality users are fraudsters (money mules, hub operators)
    """
    )
    return betweenness, centrality_df, pagerank, top_betweenness, top_pagerank


@app.cell
def __(mo):
    mo.md(
        """
    ## 6. Shared Device Analysis
    """
    )
    return


@app.cell
def __(fraud_graph, mo, pd):
    shared_devices = fraud_graph.get_shared_devices()

    shared_analysis = []
    for device_id, user_list in shared_devices.items():
        users_df_shared = dataset["users"]
        fraud_count_shared = sum(
            1
            for u in user_list
            if users_df_shared[users_df_shared["user_id"] == u]["is_fraudster"].any()
        )
        shared_analysis.append(
            {
                "Device ID": device_id,
                "User Count": len(user_list),
                "Fraudsters": fraud_count_shared,
                "Fraud Rate": fraud_count_shared / len(user_list) if user_list else 0,
                "Users": ", ".join(user_list[:3])
                + ("..." if len(user_list) > 3 else ""),
            }
        )

    shared_df = pd.DataFrame(shared_analysis).sort_values("Fraud Rate", ascending=False)

    mo.md(
        f"""
    ### Shared Device Detection

    **Total shared devices**: {len(shared_devices)}

    {mo.as_html(shared_df)}

    **Key Insight:** Shared devices with 100% fraud rate indicate fraud rings.
    These devices should be flagged for investigation.
    """
    )
    return (
        device_id,
        fraud_count_shared,
        shared_analysis,
        shared_devices,
        shared_df,
        u,
        user_list,
        users_df_shared,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## 7. Transaction Network Properties
    """
    )
    return


@app.cell
def __(mo, nx, plt, transaction_network):
    # Analyze transaction network
    in_degrees = dict(transaction_network.in_degree())
    out_degrees = dict(transaction_network.out_degree())

    # Calculate network density
    network_density = nx.density(transaction_network)

    # Try to calculate clustering (may fail for directed graph)
    try:
        avg_clustering = nx.average_clustering(transaction_network.to_undirected())
    except:
        avg_clustering = None

    fig_txn_net, axes_txn_net = plt.subplots(1, 2, figsize=(14, 5))

    # In-degree distribution
    axes_txn_net[0].hist(
        list(in_degrees.values()),
        bins=20,
        edgecolor="black",
        alpha=0.7,
        color="lightblue",
    )
    axes_txn_net[0].set_title("In-Degree Distribution (Receivers)")
    axes_txn_net[0].set_xlabel("In-Degree")
    axes_txn_net[0].set_ylabel("Count")

    # Out-degree distribution
    axes_txn_net[1].hist(
        list(out_degrees.values()),
        bins=20,
        edgecolor="black",
        alpha=0.7,
        color="lightgreen",
    )
    axes_txn_net[1].set_title("Out-Degree Distribution (Senders)")
    axes_txn_net[1].set_xlabel("Out-Degree")
    axes_txn_net[1].set_ylabel("Count")

    plt.tight_layout()
    fig_txn_net_final = plt.gcf()
    plt.close()

    mo.md(
        f"""
    ### Transaction Network Properties

    - **Network density**: {network_density:.4f}
    - **Average clustering coefficient**: {avg_clustering:.4f if avg_clustering else 'N/A'}
    - **Number of nodes**: {transaction_network.number_of_nodes()}
    - **Number of edges**: {transaction_network.number_of_edges()}

    {mo.as_html(fig_txn_net_final)}

    **Interpretation:**
    - Low density indicates sparse network (not everyone transacts with everyone)
    - In/out-degree asymmetry shows some users are primarily senders or receivers
    - High out-degree users may be fraudsters distributing funds
    """
    )
    return (
        avg_clustering,
        axes_txn_net,
        fig_txn_net,
        fig_txn_net_final,
        in_degrees,
        network_density,
        out_degrees,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## 8. Fraud Ring Network Visualization
    """
    )
    return


@app.cell
def __(G, dataset, mo, nx, plt):
    # Extract fraud ring subgraph
    fraudsters = dataset["users"][dataset["users"]["is_fraudster"]]["user_id"].tolist()

    # Get subgraph of fraudsters and their connections
    fraud_nodes = [
        n
        for n in G.nodes()
        if n in fraudsters
        or (
            G.nodes[n].get("node_type") == "device"
            and any(neighbor in fraudsters for neighbor in G.neighbors(n))
        )
    ]
    fraud_subgraph = G.subgraph(fraud_nodes)

    # Create visualization
    fig_fraud_net, ax_fraud_net = plt.subplots(figsize=(14, 10))

    # Layout
    pos = nx.spring_layout(fraud_subgraph, k=2, iterations=50, seed=42)

    # Node colors
    node_colors = []
    for node in fraud_subgraph.nodes():
        if fraud_subgraph.nodes[node].get("node_type") == "user":
            node_colors.append("red")
        else:
            node_colors.append("lightblue")

    # Draw network
    nx.draw_networkx_nodes(
        fraud_subgraph,
        pos,
        node_color=node_colors,
        node_size=300,
        alpha=0.8,
        ax=ax_fraud_net,
    )
    nx.draw_networkx_edges(fraud_subgraph, pos, alpha=0.3, ax=ax_fraud_net)
    nx.draw_networkx_labels(fraud_subgraph, pos, font_size=6, ax=ax_fraud_net)

    ax_fraud_net.set_title(
        "Fraud Ring Network (Red = Fraudsters, Blue = Shared Devices)", fontsize=14
    )
    ax_fraud_net.axis("off")

    plt.tight_layout()
    fig_fraud_net_final = plt.gcf()
    plt.close()

    mo.md(
        f"""
    {mo.as_html(fig_fraud_net_final)}

    **Network Structure:**
    - Red nodes = Fraudsters
    - Blue nodes = Shared devices
    - Clusters indicate fraud rings sharing resources
    - Dense connections within clusters, sparse between clusters
    """
    )
    return (
        ax_fraud_net,
        fig_fraud_net,
        fig_fraud_net_final,
        fraud_nodes,
        fraud_subgraph,
        fraudsters,
        neighbor,
        node,
        node_colors,
        pos,
    )


@app.cell
def __(mo):
    mo.md(
        """
    ## Summary and Insights

    ### Graph Structure Findings:

    1. **Network is sparse** with clear community structure
    2. **Fraud rings form distinct communities** with high internal fraud rates
    3. **Shared devices are strong indicators** of fraud rings (100% fraud rate for some devices)
    4. **Centrality metrics identify key fraudsters** acting as hubs or bridges
    5. **Transaction network** shows asymmetric patterns between normal users and fraudsters

    ### Implications for Fraud Detection:

    1. **Community detection** can isolate fraud rings
    2. **Device sharing patterns** are the strongest topological signal
    3. **Centrality scores** identify influential fraudsters (money mules, coordinators)
    4. **Graph-based features** complement transaction-based features

    ### Next Steps:
    - **03_fraud_patterns.py**: Deep dive into fraud ring behaviors
    - **04_feature_engineering.py**: Create composite risk scores
    """
    )
    return


if __name__ == "__main__":
    app.run()

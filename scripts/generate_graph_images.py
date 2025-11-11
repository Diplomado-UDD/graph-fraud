#!/usr/bin/env python3
"""Generate graph visualizations for the MARP presentation.

Produces images in docs/images/:
 - graph_overview.png         (small subgraph overview)
 - graph_communities.png      (nodes colored by detected community)
 - transaction_path.png       (path-of-transactions subgraph for a high-risk user)

The script builds a NetworkX graph from `data/raw/users.csv`, `data/raw/devices.csv`,
`data/raw/user_devices.csv`, and `data/raw/transactions.csv` and uses the latest
risk_scores CSV to highlight high-risk users.
"""
from pathlib import Path
import glob
import sys
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def latest_risk_file():
    files = sorted(glob.glob(str(ROOT / "outputs" / "risk_scores_*.csv")))
    if not files:
        raise FileNotFoundError("No risk_scores CSV found in outputs/")
    return files[-1]


def build_graph():
    users = pd.read_csv(ROOT / "data" / "raw" / "users.csv")
    devices = pd.read_csv(ROOT / "data" / "raw" / "devices.csv")
    user_devices = pd.read_csv(ROOT / "data" / "raw" / "user_devices.csv")
    tx = pd.read_csv(ROOT / "data" / "raw" / "transactions.csv")

    G = nx.Graph()

    # Add user and device nodes with type attribute
    for _, r in users.iterrows():
        G.add_node(f"u_{r['user_id']}", label=str(r["user_id"]), type="user")
    for _, r in devices.iterrows():
        G.add_node(f"d_{r['device_id']}", label=str(r["device_id"]), type="device")

    # User-device edges
    for _, r in user_devices.iterrows():
        u = f"u_{r['user_id']}"
        d = f"d_{r['device_id']}"
        if G.has_node(u) and G.has_node(d):
            G.add_edge(u, d, type="uses")

    # Transaction edges between users (undirected for visualization)
    for _, r in tx.iterrows():
        u1 = f"u_{r['sender_id']}" if "sender_id" in r else f"u_{r['user_id_from']}"
        u2 = f"u_{r['receiver_id']}" if "receiver_id" in r else f"u_{r['user_id_to']}"
        if G.has_node(u1) and G.has_node(u2):
            G.add_edge(u1, u2, type="transaction")

    return G


def draw_overview(G, path=None):
    plt.figure(figsize=(8, 6))
    # take a subgraph: largest connected component's top 200 nodes for clarity
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    nodes = list(comps[0])[:200] if comps else list(G.nodes())[:200]
    sub = G.subgraph(nodes)

    pos = nx.spring_layout(sub, seed=42)
    user_nodes = [n for n, d in sub.nodes(data=True) if d.get("type") == "user"]
    device_nodes = [n for n, d in sub.nodes(data=True) if d.get("type") == "device"]

    nx.draw_networkx_nodes(
        sub, pos, nodelist=user_nodes, node_color="#2b8cbe", node_size=80, label="users"
    )
    nx.draw_networkx_nodes(
        sub,
        pos,
        nodelist=device_nodes,
        node_color="#7fc97f",
        node_size=60,
        label="devices",
    )
    # draw edges lightly
    nx.draw_networkx_edges(sub, pos, alpha=0.4, width=0.7)
    plt.axis("off")
    plt.title("Graph overview (users + devices + transactions)")
    p = OUT_DIR / "graph_overview.png"
    plt.tight_layout()
    plt.savefig(p, dpi=150)
    plt.close()
    print("Wrote", p)


def draw_communities(G):
    # run a simple community detection on the user-only projection
    users = [n for n, d in G.nodes(data=True) if d.get("type") == "user"]
    U = G.subgraph(users)
    # if fewer nodes, fall back
    if U.number_of_nodes() == 0:
        print("No user nodes for communities")
        return

    try:
        from networkx.algorithms.community import greedy_modularity_communities

        comms = list(greedy_modularity_communities(U))
    except Exception:
        comms = []

    # assign community id per user
    com_map = {}
    for i, c in enumerate(comms):
        for n in c:
            com_map[n] = i

    # prepare colors
    import matplotlib.cm as cm

    cmap = cm.get_cmap("tab20")

    # pick a subgraph for drawing
    nodes = users[:200]
    sub = G.subgraph(nodes)
    pos = nx.spring_layout(sub, seed=24)
    colors = []
    for n in sub.nodes():
        if sub.nodes[n].get("type") == "device":
            colors.append("#cccccc")
        else:
            cid = com_map.get(n, -1)
            colors.append(cmap((cid % 20) / 20) if cid >= 0 else "#999999")

    plt.figure(figsize=(8, 6))
    nx.draw_networkx_nodes(sub, pos, node_color=colors, node_size=80)
    nx.draw_networkx_edges(sub, pos, alpha=0.4)
    plt.axis("off")
    plt.title("User communities (detected via greedy modularity)")
    p = OUT_DIR / "graph_communities.png"
    plt.tight_layout()
    plt.savefig(p, dpi=150)
    plt.close()
    print("Wrote", p)


def draw_transaction_path(G, risk_df):
    # pick highest-risk user id
    hr = risk_df.sort_values("risk_score", ascending=False).head(1)
    if hr.empty:
        print("No high-risk users found")
        return
    uid = str(hr.iloc[0]["user_id"])
    node = f"u_{uid}"
    if not G.has_node(node):
        print("High-risk user node not found in graph:", node)
        return

    # get neighborhood up to 3 hops
    nodes = nx.single_source_shortest_path_length(G, node, cutoff=3).keys()
    sub = G.subgraph(nodes)
    pos = nx.spring_layout(sub, seed=7)

    plt.figure(figsize=(8, 6))
    # highlight the path center
    node_colors = []
    for n in sub.nodes():
        if n == node:
            node_colors.append("#d73027")
        elif sub.nodes[n].get("type") == "device":
            node_colors.append("#fdae61")
        else:
            node_colors.append("#4575b4")

    nx.draw_networkx_nodes(sub, pos, node_color=node_colors, node_size=120)
    nx.draw_networkx_edges(sub, pos, width=1.0, alpha=0.6)
    nx.draw_networkx_labels(
        sub, pos, {n: sub.nodes[n].get("label", "") for n in sub.nodes()}, font_size=8
    )
    plt.axis("off")
    plt.title(f"Transaction neighborhood for high-risk user {uid}")
    p = OUT_DIR / "transaction_path.png"
    plt.tight_layout()
    plt.savefig(p, dpi=150)
    plt.close()
    print("Wrote", p)


def main():
    try:
        rf = latest_risk_file()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    risk_df = pd.read_csv(rf)
    G = build_graph()
    draw_overview(G)
    draw_communities(G)
    draw_transaction_path(G, risk_df)


if __name__ == "__main__":
    main()

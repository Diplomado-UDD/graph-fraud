#!/usr/bin/env python3
"""Generate an interactive HTML network using pyvis for the MARP presentation.

Produces: docs/graph_interactive.html

Note: pyvis may not be installed in the environment. Install with `uv sync` or
add to the project venv if you want to render interactively.
"""
from pathlib import Path
import glob
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs' / 'graph_interactive.html'

def latest_risk_file():
    files = sorted(glob.glob(str(ROOT / 'outputs' / 'risk_scores_*.csv')))
    if not files:
        raise FileNotFoundError('No risk_scores CSV found in outputs/')
    return files[-1]


def build_network():
    import networkx as nx
    users = pd.read_csv(ROOT / 'data' / 'raw' / 'users.csv')
    devices = pd.read_csv(ROOT / 'data' / 'raw' / 'devices.csv')
    user_devices = pd.read_csv(ROOT / 'data' / 'raw' / 'user_devices.csv')
    tx = pd.read_csv(ROOT / 'data' / 'raw' / 'transactions.csv')

    G = nx.Graph()
    for _, r in users.iterrows():
        G.add_node(f"u_{r['user_id']}", label=str(r['user_id']), group='user')
    for _, r in devices.iterrows():
        G.add_node(f"d_{r['device_id']}", label=str(r['device_id']), group='device')
    for _, r in user_devices.iterrows():
        G.add_edge(f"u_{r['user_id']}", f"d_{r['device_id']}")
    for _, r in tx.iterrows():
        # assume sender_id / receiver_id
        if 'sender_id' in r and 'receiver_id' in r:
            G.add_edge(f"u_{r['sender_id']}", f"u_{r['receiver_id']}")
    return G


def main():
    try:
        rf = latest_risk_file()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    try:
        from pyvis.network import Network
    except Exception as e:
        print('pyvis not installed; to create an interactive HTML please install pyvis in the venv')
        print('Error:', e)
        sys.exit(1)

    G = build_network()
    net = Network(height='800px', width='100%', notebook=False)
    net.from_nx(G)
    net.show(str(OUT))
    print('Wrote', OUT)


if __name__ == '__main__':
    main()

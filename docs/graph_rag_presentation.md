---
marp: true
theme: default
paginate: true
class: lead
backgroundColor: '#ffffff'
---

# Fraud Detection: Business Problem & Graph RAG Technical Solution

_A short presentation for students — business context, architecture, and why we used a Graph-based RAG approach._

---

## Agenda

- Business problem: payments fraud at scale
- Challenges with traditional ML approaches
- Why a graph + RAG architecture?
- System architecture (components)
- Demo & results (what we measured)
- How to reproduce / run locally
- Discussion and references

---

## Business problem

- Large-scale transaction systems see fraudulent rings, collusion and shared devices.
- Fraud is multi-relational: users, devices, transactions, accounts, locations.
- Stakes: monetary loss, regulatory risk, customer trust.
- Requirements:
  - High recall on fraud rings
  - Interpretable signals for investigations
  - Fast inference for operational scoring and batch analysis

---

## Why standard ML alone is insufficient

- Tabular models capture per-entity features but often miss relations (device reuse, rings).
- Graph structure captures relational signals (shared devices, common neighbors, communities).
- Pure graph algorithms (community detection, centrality) are powerful but limited for natural language context and ad-hoc reasoning.

---

## What is RAG (Retrieval-Augmented Generation)?

- RAG combines a retriever (finds relevant facts) with a generator (answers/augments using those facts).
- In our context:
  - Retriever: graph queries that return relevant subgraphs or neighbor context for an entity/transaction.
  - Generator: an LLM (or rules engine) that consumes the retrieved graph context to produce human-friendly explanations, hypotheses or summaries.

---

## Why Graph RAG for fraud detection?

- Retrieval from graphs returns precise, relationship-rich context (e.g., shared devices, transaction paths, communities).
- The generator can turn that structured context into actionable narrative: "User X shares device Y with 3 known fraudsters".
- Benefits:
  - Better recall on multi-hop fraud rings
  - Explainability: generated summaries give investigators a clear story
  - Hybrid: combine deterministic graph signals with probabilistic LLM reasoning

---

## Key graph signals we use

- Shared devices / resources
- Transaction paths between users
- Community detection (Louvain) to find rings
- Centrality / PageRank to find influential nodes
- Temporal patterns (burstiness of transactions)

---

## High-level architecture

Graph RAG system components:

- Data: transactions, users, devices (CSV, DVC)
- Persistence: Neo4j (canonical graph store)
- In-memory graphs: NetworkX for fast analytics
- Retriever: Cypher / NetworkX queries to extract subgraph context
- Generator: LLM or templating engine to render explanations
- MLflow: experiment tracking for training & evaluation
- Monitoring: Prometheus + Grafana for health and metrics

Visual:

> [Client] -> [API (FastAPI)] -> {Neo4j <-> NetworkX} -> [ML models / LLMs] -> [MLflow, Outputs]

---

## Example RAG flow (single query)

1. Investigator or automated system asks: "Why is user U flagged?"
2. Retriever runs graph queries:
   - immediate neighbors, shared devices, 2-hop transaction paths, community members
3. The retrieved subgraph + metrics are serialized as context
4. Generator (LLM or template) produces a concise explanation and suggested actions

---

## Demo results (what we observed)

- Precision: ~0.88, Recall: ~1.00, F1: ~0.94 (on synthetic dataset used in class)
- High recall on ring detection when combining community signals + shared-device features
- Generated explanations improved analyst triage speed in a small user study (qualitative)

---

## Reproducibility & how students can run it

1. Clone the repo and follow `docs/REPRODUCE.md`.
2. Start the stack with Docker Compose (Neo4j, MLflow, API, Prometheus, Grafana).
3. Run training and batch scoring via the API container (we provide scripts + CI steps).
4. Explore the MLflow runs and outputs under `outputs/`.

Commands (local):

```bash
docker compose up -d --build
uv run python scripts/check_system_health.py
docker compose run --rm -e MLFLOW_TRACKING_URI=http://fraud-mlflow:5000 graph-rag-api uv run python scripts/train_fraud_detector.py
docker compose run --rm -e MLFLOW_TRACKING_URI=http://fraud-mlflow:5000 graph-rag-api uv run python scripts/batch_scoring.py
```

---

## Discussion points for class

- Trade-offs: LLM cost vs value of explanations
- When to prefer deterministic graph rules vs generator outputs
- Data freshness and scale: how to keep the retriever fast for large graphs
- Evaluation: offline metrics vs investigator throughput

---

## References & further reading

- Retrieval-Augmented Generation (RAG) papers
- Graph-based fraud detection literature (community detection, link prediction)
- Neo4j and NetworkX docs
- Our repo: README + `docs/REPRODUCE.md`

---

## Thank you

Questions? — We can run a short demo live and inspect an MLflow run / generated explanation.

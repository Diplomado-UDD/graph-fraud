# Project Summary

## Graph-Based Fraud Detection System

Educational fraud detection implementation with **NetworkX** and **Neo4j** support.

---

## System Architecture

### Data Pipeline
```
Synthetic Dataset → Graph Construction → Fraud Detection → Graph RAG Queries
```

### Supported Backends
1. **NetworkX** - In-memory graph processing (default)
2. **Neo4j** - Persistent graph database (optional)

---

## Performance Metrics

### Optimized Detection (as of 2025-11-10)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Precision** | 88.2% | 0.5-0.9 | ✓ Met |
| **Recall** | 100% | Maximized | ✓ Optimal |
| **F1-Score** | 0.938 | - | ✓ Excellent |

### Detection Breakdown
- **Fraud ring members**: 14/14 detected (100%)
- **Solo fraudsters**: 16/16 detected (100%)
- **False positives**: 4/170 normal users (2.4%)
- **Total coverage**: 30/30 fraudsters identified

---

## Key Features Implemented

### 1. Multi-Signal Risk Scoring
Composite risk calculation using:
- **Device sharing** (35%) - Fraud ring detection
- **Account age** (25%) - New account fraud
- **Transaction amount** (20%) - High-value fraud
- **Transaction volume** (10%) - Velocity patterns
- **Network centrality** (10%) - PageRank + Betweenness

### 2. Fraud Pattern Detection
- Community detection (Louvain algorithm)
- Shared resource analysis (device fingerprinting)
- Transaction network analysis
- Centrality-based ranking

### 3. Graph RAG Query Interface
Interactive fraud investigation with queries:
- User profile analysis
- Network connections (multi-hop)
- Fraud risk assessment
- Shared device identification
- Transaction path discovery
- Community membership
- Suspicious pattern detection

---

## Technology Stack

### Core Libraries
- **Python 3.12** - Language
- **uv** - Package management
- **NetworkX 3.5** - Graph algorithms
- **pandas 2.3** - Data processing
- **scikit-learn 1.7** - ML utilities
- **python-louvain 0.16** - Community detection

### Database (Optional)
- **Neo4j 2025.10.1** - Graph database
- **neo4j-driver 6.0.3** - Python connector

---

## Project Structure

```
graph-fraud/
├── src/
│   ├── data/
│   │   └── generate_dataset.py       # Synthetic data generation
│   ├── models/
│   │   ├── graph_builder.py          # NetworkX implementation
│   │   ├── neo4j_graph_builder.py    # Neo4j implementation
│   │   └── fraud_detector.py         # Detection algorithms
│   └── features/
│       └── graph_rag.py               # Query interface
├── main.py                            # NetworkX demo
├── test_neo4j.py                      # Neo4j demo
├── README.md                          # Main documentation
├── NEO4J_SETUP.md                     # Neo4j guide
├── .env.example                       # Config template
└── pyproject.toml                     # Dependencies
```

---

## Installation & Usage

### Quick Start (NetworkX)
```bash
uv sync
uv run python main.py
```

### With Neo4j
```bash
brew install neo4j
brew services start neo4j
uv run python test_neo4j.py
```

---

## Detection Algorithm Evolution

### Version 1 (Initial)
- **Precision**: 100%
- **Recall**: 46.7%
- **Approach**: Device sharing only
- **Issue**: Missed solo fraudsters

### Version 2 (Optimized - Current)
- **Precision**: 88.2%
- **Recall**: 100%
- **Approach**: Multi-signal composite scoring
- **Improvement**: +53.3% recall, detects all fraud types

### Key Optimization
- Added account age, transaction amount, and volume signals
- Adjusted risk score weights to balance precision/recall
- Lowered detection threshold from 0.5 to 0.15
- Captures both organized rings and solo operators

---

## Use Cases

### Educational
- Learn graph-based fraud detection
- Understand community detection algorithms
- Explore Graph RAG concepts
- Compare NetworkX vs Neo4j

### Proof of Concept
- Demonstrate fraud pattern detection
- Validate graph approach effectiveness
- Benchmark detection algorithms
- Prototype investigation workflows

---

## Neo4j Integration Highlights

### Advantages
- **Persistence** - Data survives restarts
- **Cypher queries** - Declarative graph queries
- **Browser UI** - Visual graph exploration
- **Scalability** - Production-ready database
- **GDS library** - Advanced graph algorithms

### Example Queries
```cypher
// Find fraud rings
MATCH (u1:User {is_fraudster: true})-[:USES_DEVICE]->(d:Device)
      <-[:USES_DEVICE]-(u2:User {is_fraudster: true})
RETURN u1, d, u2

// High-risk transaction paths
MATCH path = (sender:User)-[:TRANSACTED*1..3]->(receiver:User)
WHERE sender.is_fraudster = true
RETURN path
```

---

## Future Enhancements

### Potential Additions
- [ ] Graph Neural Networks (GNN) for classification
- [ ] Temporal pattern analysis (time-series fraud)
- [ ] Feature engineering automation
- [ ] Real-time streaming detection
- [ ] Explainable AI (XAI) for risk scores
- [ ] Integration with external fraud databases

### Database Extensions
- [ ] Neo4j Graph Data Science (GDS) algorithms
- [ ] Multi-database support (ArangoDB, TigerGraph)
- [ ] Distributed graph processing (GraphX, Pregel)

---

## Performance Considerations

### NetworkX
- **Best for**: < 10K nodes, development, prototyping
- **Memory**: Entire graph in RAM
- **Speed**: Fast for small graphs

### Neo4j
- **Best for**: > 10K nodes, production, persistence
- **Memory**: Efficient disk-based storage
- **Speed**: Optimized for large graphs with indexes

---

## References

- [Neo4j Fraud Detection Guide](https://neo4j.com/use-cases/fraud-detection/)
- [NetworkX Documentation](https://networkx.org/documentation/stable/)
- [Louvain Community Detection](https://en.wikipedia.org/wiki/Louvain_method)
- [Graph RAG Overview](https://arxiv.org/abs/2404.16130)

---

## License

Educational use only.

## Contact

For questions or contributions, see project repository.

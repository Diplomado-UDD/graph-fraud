# Neo4j Setup Guide

This project now supports both **NetworkX** (in-memory) and **Neo4j** (database) for graph operations.

## Installation

### 1. Install Neo4j Database

```bash
# macOS
brew install neo4j

# Start Neo4j service
brew services start neo4j

# Check status
brew services info neo4j
```

### 2. Install Python Driver

Already included in project dependencies:

```bash
uv sync
```

### 3. Configure Credentials

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your Neo4j credentials:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

**Note**: Default password is `neo4j` but must be changed on first use.

## Quick Test

Run the test script to verify installation:

```bash
uv run python test_neo4j.py
```

This will:
- Connect to Neo4j
- Clear existing data
- Generate synthetic fraud dataset
- Build graph in Neo4j
- Run queries to test functionality

## Neo4j Browser

Access the Neo4j Browser interface at:
- **URL**: http://localhost:7474
- **Username**: neo4j
- **Password**: (your configured password)

### Useful Cypher Queries

**View all users:**
```cypher
MATCH (u:User)
RETURN u
LIMIT 25
```

**View fraud network:**
```cypher
MATCH (u:User {is_fraudster: true})-[r]->(n)
RETURN u, r, n
```

**Find shared devices (fraud rings):**
```cypher
MATCH (u:User)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(u2:User)
WHERE u.user_id < u2.user_id
RETURN u, d, u2
```

**Find fraudsters sharing devices:**
```cypher
MATCH (u1:User {is_fraudster: true})-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(u2:User {is_fraudster: true})
WHERE u1.user_id < u2.user_id
RETURN u1, d, u2
```

**Transaction patterns:**
```cypher
MATCH (sender:User)-[t:TRANSACTED]->(receiver:User)
WHERE t.is_fraudulent = true
RETURN sender, t, receiver
LIMIT 50
```

**User transaction volume:**
```cypher
MATCH (u:User)-[t:TRANSACTED]->()
RETURN u.user_id, u.is_fraudster, count(t) as tx_count, sum(t.amount) as total_amount
ORDER BY tx_count DESC
LIMIT 20
```

## Using Neo4j in Code

### Basic Usage

```python
from src.models.neo4j_graph_builder import Neo4jFraudGraph
from src.data.generate_dataset import FraudDatasetGenerator

# Connect to Neo4j
neo4j_graph = Neo4jFraudGraph(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="your_password"
)

# Generate dataset
generator = FraudDatasetGenerator(seed=42)
dataset = generator.generate_dataset(n_users=200, n_transactions=1000)

# Build graph
neo4j_graph.build_from_dataset(dataset)

# Query graph
stats = neo4j_graph.get_statistics()
shared_devices = neo4j_graph.get_shared_devices()

# Close connection
neo4j_graph.close()
```

### Available Methods

- `build_from_dataset(dataset)` - Load data into Neo4j
- `get_statistics()` - Get node/edge counts
- `get_shared_devices()` - Find devices used by multiple users
- `get_user_subgraph(user_id, depth)` - Get user neighborhood
- `get_transaction_paths(source, target, max_depth)` - Find paths between users
- `clear_database()` - Delete all data (use with caution!)

## Neo4j vs NetworkX

| Feature | NetworkX | Neo4j |
|---------|----------|-------|
| **Storage** | In-memory | Persistent database |
| **Scale** | Small-medium datasets | Large-scale graphs |
| **Performance** | Fast for small graphs | Optimized for large graphs |
| **Queries** | Python API | Cypher query language |
| **Setup** | None required | Database installation |
| **Visualization** | Matplotlib | Built-in browser |
| **Use case** | Development, testing | Production, analysis |

## Troubleshooting

### Service not starting

```bash
# Check logs
tail -f /opt/homebrew/var/log/neo4j.log

# Restart service
brew services restart neo4j
```

### Connection refused

1. Verify Neo4j is running: `brew services info neo4j`
2. Check port 7687 is not in use: `lsof -i :7687`
3. Try connecting via browser: http://localhost:7474

### Password issues

If you forgot your password, stop Neo4j and reset:

```bash
brew services stop neo4j
neo4j-admin dbms set-initial-password your_new_password
brew services start neo4j
```

## Advanced: Graph Data Science

Neo4j offers a Graph Data Science (GDS) library for advanced algorithms. To use it:

1. Install GDS plugin (separate download)
2. Use methods like `run_community_detection()` and `calculate_pagerank()` in the code

**Note**: The current implementation includes GDS examples but requires the GDS plugin to be installed separately.

## Stopping Neo4j

When you're done:

```bash
# Stop the service
brew services stop neo4j

# Or completely remove
brew uninstall neo4j
```

## Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Graph Data Science](https://neo4j.com/docs/graph-data-science/current/)

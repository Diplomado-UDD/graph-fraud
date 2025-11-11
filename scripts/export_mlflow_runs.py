#!/usr/bin/env python3
"""Export MLflow experiments and runs to JSON by reading the local mlflow sqlite DB.

This script expects the MLflow server to be using a local sqlite DB at ./mlflow/mlflow.db
(the default in the project's docker-compose). It reads experiments, runs, params and metrics
and writes outputs/mlflow_runs.json.

Uses only the Python stdlib so it can be run with `uv run python` without extra deps.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("mlflow/mlflow.db")
OUT_PATH = Path("outputs/mlflow_runs.json")


def export_db(db_path: Path):
    if not db_path.exists():
        raise FileNotFoundError(f"MLflow DB not found at {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    experiments = []
    for exp in cur.execute("SELECT experiment_id, name FROM experiments").fetchall():
        exp_id = exp["experiment_id"]
        name = exp["name"]
        runs = []
        for run in cur.execute(
            "SELECT run_uuid, artifact_uri, status, start_time FROM runs WHERE experiment_id=? ORDER BY start_time DESC",
            (exp_id,),
        ).fetchall():
            run_id = run["run_uuid"]
            # params
            params = {
                r["key"]: r["value"]
                for r in cur.execute(
                    "SELECT key, value FROM params WHERE run_uuid=?", (run_id,)
                ).fetchall()
            }
            # metrics (latest value per key)
            metrics_rows = cur.execute(
                "SELECT key, value, timestamp FROM metrics WHERE run_uuid=? ORDER BY timestamp DESC",
                (run_id,),
            ).fetchall()
            metrics = {}
            for r in metrics_rows:
                k = r["key"]
                if k not in metrics:
                    metrics[k] = r["value"]

            runs.append(
                {
                    "run_uuid": run_id,
                    "artifact_uri": run["artifact_uri"],
                    "status": run["status"],
                    "start_time": run["start_time"],
                    "params": params,
                    "metrics": metrics,
                }
            )

        experiments.append({"experiment_id": exp_id, "name": name, "runs": runs})

    conn.close()
    return experiments


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = export_db(DB_PATH)
    with OUT_PATH.open("w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()

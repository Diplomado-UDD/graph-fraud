#!/usr/bin/env python3
"""Simple CI-like health check script for the graph-fraud stack.

Checks:
 - Graph RAG API health (/health)
 - MLflow UI root
 - Prometheus readiness
 - Grafana API health
 - Neo4j browser root
 - Docker container status for key services

This script uses only the Python standard library to avoid extra dependencies.
"""
import json
import subprocess
import urllib.request
import urllib.error
from urllib.parse import urljoin
import os
import sys

try:
    import config
except Exception:
    config = None

try:
    from neo4j import GraphDatabase
except Exception:
    GraphDatabase = None

SERVICES = {
    "api": "http://localhost:8000/health",
    "mlflow": "http://localhost:5001/",
    "prometheus": "http://localhost:9090/-/ready",
    "grafana": "http://localhost:3000/api/health",
    "neo4j": "http://localhost:7474/",
}


def check_http(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return True, r.read(1024).decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, str(e)


def docker_ps(names):
    out = {}
    for name in names:
        try:
            cmd = ["docker", "ps", "--filter", f"name={name}", "--format", '{{.Names}} {{.Status}}']
            p = subprocess.run(cmd, capture_output=True, text=True, check=False)
            out[name] = p.stdout.strip() or "not running"
        except Exception as e:
            out[name] = f"error: {e}"
    return out


def main():
    results = {}
    print("Checking HTTP services:")
    any_fail = False
    for k, url in SERVICES.items():
        ok, info = check_http(url)
        results[k] = {"ok": ok, "info": info}
        status = "OK" if ok else "FAIL"
        print(f" - {k}: {status}")

    # Try a bolt-level Neo4j connectivity check (preferred) when neo4j driver is available
    neo4j_bolt_ok = False
    neo4j_bolt_info = None
    if GraphDatabase and config is not None:
        try:
            uri = config.NEO4J_URI
            user = config.NEO4J_USER
            pwd = config.NEO4J_PASSWORD
            drv = GraphDatabase.driver(uri, auth=(user, pwd))
            with drv.session() as sess:
                r = sess.run("RETURN 1 AS ok")
                _ = r.single()
            neo4j_bolt_ok = True
            neo4j_bolt_info = f"Bolt OK ({uri})"
        except Exception as e:
            neo4j_bolt_ok = False
            neo4j_bolt_info = str(e)
    else:
        # If the neo4j driver is not available in this environment, try running
        # a bolt connectivity check inside the API container which has the
        # project's virtualenv and the driver installed. This avoids host vs
        # container mismatch when this script runs on the host.
        neo4j_bolt_info = "neo4j driver not available or config not found"
        try:
            cmd = [
                "docker",
                "exec",
                "fraud-graph-rag-api",
                "uv",
                "run",
                "python",
                "-c",
                ("import config; from neo4j import GraphDatabase; "
                 "drv=GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)); "
                 "s=drv.session(); r=s.run('RETURN 1 AS ok').single(); s.close(); drv.close(); print('BOLT_OK')")
            ]
            p = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=10)
            out = (p.stdout or "") + (p.stderr or "")
            if "BOLT_OK" in out or "QUERY_OK" in out:
                neo4j_bolt_ok = True
                neo4j_bolt_info = f"Bolt OK (checked inside container): {out.strip()}"
            else:
                neo4j_bolt_ok = False
                neo4j_bolt_info = f"Fallback container check failed: {out.strip()}"
        except Exception as e:
            neo4j_bolt_ok = False
            neo4j_bolt_info = f"fallback check error: {e}"

    results['neo4j_bolt'] = {"ok": neo4j_bolt_ok, "info": neo4j_bolt_info}
    print(f" - neo4j_bolt: {'OK' if neo4j_bolt_ok else 'FAIL'}")

    print("\nChecking Docker containers:")
    names = ["fraud-neo4j", "fraud-mlflow", "fraud-prometheus", "fraud-grafana", "fraud-graph-rag-api"]
    ps = docker_ps(names)
    for n, s in ps.items():
        print(f" - {n}: {s}")

    print("\nSummary JSON:")
    summary = {"http": results, "docker": ps}
    print(json.dumps(summary, indent=2))

    # Exit non-zero if any check failed so CI can fail fast
    any_fail = False
    for k, v in results.items():
        if not v.get("ok", False):
            any_fail = True
            break

    if any_fail:
        print("One or more health checks failed; exiting with status 2")
        sys.exit(2)


if __name__ == '__main__':
    main()

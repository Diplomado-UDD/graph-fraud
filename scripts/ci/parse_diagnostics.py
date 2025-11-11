#!/usr/bin/env python3
"""Parse docker-compose diagnostics and health report to produce a short human-readable summary.

Writes diagnostics_summary.txt in the current working directory.
"""
import json
import re
from pathlib import Path


def read_file(path: Path):
    try:
        return path.read_text(errors="replace")
    except Exception:
        return ""


def find_matches(text: str, patterns):
    matches = []
    for i, line in enumerate(text.splitlines()):
        for p in patterns:
            if re.search(p, line, flags=re.IGNORECASE):
                matches.append((i + 1, line.strip()))
                break
    return matches


def summarize_matches(name: str, matches, limit=20):
    if not matches:
        return f"--- {name}: no notable matches found\n"
    out = [f"--- {name}: {len(matches)} notable lines (showing up to {limit})\n"]
    for ln, line in matches[:limit]:
        out.append(f"{ln}: {line}\n")
    out.append("\n")
    return "".join(out)


def suggest_from_text(text: str):
    suggestions = []
    if re.search(
        r"address already in use|bind: address already in use|port.*in use",
        text,
        re.IGNORECASE,
    ):
        suggestions.append(
            "Port conflict detected. Verify host ports in docker-compose and that no other service is using them."
        )
    if re.search(
        r"permission denied|write permission|permissionerror", text, re.IGNORECASE
    ):
        suggestions.append(
            "Permission issues detected. Ensure container volumes map to writable host directories (e.g., ./mlflow) and correct filesystem permissions."
        )
    if re.search(
        r"authentication|unauthorized|invalid credentials|neo4j.*authentication",
        text,
        re.IGNORECASE,
    ):
        suggestions.append(
            "Authentication failures detected. Check NEO4J_USERNAME/NEO4J_PASSWORD and MLflow tracking URI credentials."
        )
    if re.search(r"traceback|exception", text, re.IGNORECASE):
        suggestions.append(
            "Python exceptions found. Inspect traceback snippets above to identify failing module or missing dependency."
        )
    if re.search(r"out of memory|oom|killed", text, re.IGNORECASE):
        suggestions.append(
            "Containers may be OOM killed. Consider increasing runner memory or optimizing services."
        )
    return suggestions


def try_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def main():
    cwd = Path.cwd()
    files = {
        "health_report": cwd / "health-report.txt",
        "compose_ps": cwd / "docker-compose-ps.txt",
        "compose_logs": cwd / "docker-compose-logs.txt",
    }
    # include any per-service logs present
    for p in cwd.glob("logs_*.txt"):
        files[p.stem] = p

    summary_lines = []

    # Read health report and try to parse JSON
    hr_text = (
        read_file(files["health_report"]) if files["health_report"].exists() else ""
    )
    if hr_text:
        parsed = try_parse_json(hr_text)
        if parsed:
            summary_lines.append("Health report: parsed JSON\n")
            # look for top-level http/docker sections
            if isinstance(parsed, dict):
                # summarize http subkeys
                http = (
                    parsed.get("http") or parsed.get("services") or parsed.get("status")
                )
                if isinstance(http, dict):
                    for k, v in http.items():
                        summary_lines.append(
                            f" - {k}: {('OK' if (isinstance(v, dict) and v.get('ok')) else str(v))}\n"
                        )
        else:
            summary_lines.append(
                "Health report: not JSON, captured raw text in diagnostics.\n"
            )

    patterns = [r"error", r"exception", r"traceback", r"warn", r"failed", r"unhealthy"]

    # Scan compose logs
    compose_text = (
        read_file(files["compose_logs"]) if files["compose_logs"].exists() else ""
    )
    matches = find_matches(compose_text, patterns)
    summary_lines.append(summarize_matches("docker-compose logs", matches))

    # Scan per-service logs
    for name, path in list(files.items()):
        if name.startswith("logs_"):
            text = read_file(path)
            m = find_matches(text, patterns)
            summary_lines.append(summarize_matches(path.name, m))

    # Add top suggestions
    suggestions = suggest_from_text(compose_text + "\n" + hr_text)
    if suggestions:
        summary_lines.append("Suggested fixes:\n")
        for s in suggestions:
            summary_lines.append(f" - {s}\n")
    else:
        summary_lines.append("No automatic suggestions could be inferred.\n")

    out_path = cwd / "diagnostics_summary.txt"
    out_path.write_text("".join(summary_lines))
    print(f"Wrote summary to {out_path}")


if __name__ == "__main__":
    main()

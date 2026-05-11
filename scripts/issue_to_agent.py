#!/usr/bin/env -S uv run python
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Spawn the orchestrator on a feature/bug description.

Usage:
    issue_to_agent.py --title "..." --body "..."
    echo "..." | issue_to_agent.py --title "..."

Invokes `claude -p /orchestrate "<description>"` in the repo root.
Used by:
- GitHub Actions workflow (.github/workflows/agent-trigger.yml)
- Cron trigger (scripts/cron_trigger.py)
- Direct CLI invocation by the operator
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Spawn /orchestrate on an issue.")
    parser.add_argument("--title", required=True, help="Issue or task title.")
    parser.add_argument(
        "--body",
        default=None,
        help="Issue body. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--repo",
        default=str(Path(__file__).resolve().parent.parent),
        help="Repo root (default: parent of this script).",
    )
    args = parser.parse_args()

    body = args.body if args.body is not None else sys.stdin.read().strip()
    description = f"{args.title}\n\n{body}".strip()

    cmd = ["claude", "-p", f"/orchestrate {description}"]
    print(f"[issue_to_agent] dispatching: {args.title}", file=sys.stderr)
    result = subprocess.run(cmd, cwd=args.repo, check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

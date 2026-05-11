#!/usr/bin/env -S uv run python
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Cron / launchd trigger — pick up the next queued spec and run /orchestrate.

Watches `specs/` for files. On each run, picks the oldest spec by mtime,
hands it to the orchestrator, and moves it to `specs/done/` on success.

Schedule example (cron, every 15 minutes):
    */15 * * * * cd /path/to/mobius-conf-demo && uv run scripts/cron_trigger.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    specs_dir = repo / "specs"
    done_dir = specs_dir / "done"
    done_dir.mkdir(parents=True, exist_ok=True)

    pending = sorted(
        (p for p in specs_dir.iterdir() if p.is_file() and p.suffix == ".md"),
        key=lambda p: p.stat().st_mtime,
    )
    if not pending:
        print("[cron_trigger] no specs queued", file=sys.stderr)
        return 0

    next_spec = pending[0]
    print(f"[cron_trigger] dispatching: {next_spec.name}", file=sys.stderr)

    cmd = ["claude", "-p", f"/orchestrate {next_spec.read_text()}"]
    result = subprocess.run(cmd, cwd=repo, check=False)

    if result.returncode == 0:
        shutil.move(str(next_spec), str(done_dir / next_spec.name))
        print(f"[cron_trigger] archived: {next_spec.name}", file=sys.stderr)
    else:
        print(f"[cron_trigger] failed, leaving in queue: {next_spec.name}", file=sys.stderr)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

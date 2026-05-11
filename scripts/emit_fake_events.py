# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx>=0.27",
# ]
# ///
"""posts a stream of fake claude-code lifecycle events at the local backend"""
import os
import random
import time
import uuid
from datetime import datetime, timezone

import httpx

BASE = os.environ.get("MOBIUS_URL", "http://localhost:8000")
TOKEN = os.environ.get("MOBIUS_TOKEN", "dev-secret-token")
MACHINES = ["laptop-q", "rig-01", "ci-runner"]
TOOLS = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]


def post(evt):
    try:
        r = httpx.post(
            f"{BASE}/events",
            json=evt,
            headers={"Authorization": TOKEN},
            timeout=5.0,
        )
        return r.status_code
    except Exception as e:
        print("post failed:", e)
        return None


def now():
    return datetime.now(timezone.utc).isoformat()


def fake_session():
    sid = str(uuid.uuid4())
    machine = random.choice(MACHINES)

    print(f"session {sid[:8]} on {machine}")
    code = post({
        "event_type": "SessionStart",
        "session_id": sid,
        "machine_id": machine,
        "timestamp": now(),
    })
    print("  SessionStart:", code)
    time.sleep(0.5)

    for _ in range(random.randint(3, 8)):
        tool = random.choice(TOOLS)
        post({
            "event_type": "PreToolUse",
            "session_id": sid,
            "machine_id": machine,
            "tool_name": tool,
            "tool_input": {"path": "/tmp/fake"},
            "timestamp": now(),
        })
        time.sleep(0.2)
        post({
            "event_type": "PostToolUse",
            "session_id": sid,
            "machine_id": machine,
            "tool_name": tool,
            "tool_output": {"ok": True, "bytes": random.randint(10, 5000)},
            "timestamp": now(),
        })
        print(f"  tool: {tool}")
        time.sleep(0.3)

    code = post({
        "event_type": "SessionEnd",
        "session_id": sid,
        "machine_id": machine,
        "timestamp": now(),
    })
    print("  SessionEnd:", code)


def main():
    n = int(os.environ.get("N_SESSIONS", "3"))
    for _ in range(n):
        fake_session()
        time.sleep(0.5)


if __name__ == "__main__":
    main()

"""Read-API filter coverage for `GET /events`."""
from __future__ import annotations

from fastapi.testclient import TestClient


def _post(
    client: TestClient,
    auth_header: dict[str, str],
    *,
    event_type: str,
    session_id: str,
    machine_id: str,
    tool_name: str | None = None,
) -> None:
    payload: dict[str, object] = {
        "event_type": event_type,
        "session_id": session_id,
        "machine_id": machine_id,
    }
    if tool_name is not None:
        payload["tool_name"] = tool_name
    resp = client.post("/events", json=payload, headers=auth_header)
    assert resp.status_code == 200, resp.text


def test_filter_by_machine_id(client: TestClient, auth_header: dict[str, str]) -> None:
    _post(client, auth_header, event_type="PreToolUse", session_id="s-a", machine_id="laptop-q", tool_name="Read")
    _post(client, auth_header, event_type="PreToolUse", session_id="s-b", machine_id="rig-01", tool_name="Bash")
    _post(client, auth_header, event_type="PreToolUse", session_id="s-c", machine_id="rig-01", tool_name="Edit")

    resp = client.get("/events", params={"machine_id": "rig-01"})
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    assert {r["machine_id"] for r in rows} == {"rig-01"}


def test_filter_by_session_id(client: TestClient, auth_header: dict[str, str]) -> None:
    _post(client, auth_header, event_type="SessionStart", session_id="s-only", machine_id="laptop-q")
    _post(client, auth_header, event_type="PreToolUse", session_id="s-only", machine_id="laptop-q", tool_name="Read")
    _post(client, auth_header, event_type="PreToolUse", session_id="s-other", machine_id="laptop-q", tool_name="Write")

    resp = client.get("/events", params={"session_id": "s-only"})
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    assert {r["session_id"] for r in rows} == {"s-only"}

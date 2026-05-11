"""Event ingestion + retrieval roundtrips.

The session-event roundtrip indirectly exercises `broadcast_to_websocket`,
which historically raised `AttributeError` on `tool_name=None`. The listener
swallows the exception, so the roundtrip itself doesn't fail — see
`test_broadcast_bug.py` for the direct demonstration of the bug fix.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_tool_event_roundtrip(client: TestClient, auth_header: dict[str, str]) -> None:
    payload = {
        "event_type": "PreToolUse",
        "session_id": "s-1",
        "machine_id": "laptop-q",
        "tool_name": "Read",
        "tool_input": {"path": "/tmp/x"},
    }
    post_resp = client.post("/events", json=payload, headers=auth_header)
    assert post_resp.status_code == 200, post_resp.text
    body = post_resp.json()
    assert body["ok"] is True
    assert isinstance(body["id"], int)

    get_resp = client.get("/events", params={"session_id": "s-1"})
    assert get_resp.status_code == 200
    rows = get_resp.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["event_type"] == "PreToolUse"
    assert row["session_id"] == "s-1"
    assert row["machine_id"] == "laptop-q"
    assert row["tool_name"] == "Read"


def test_session_event_roundtrip(client: TestClient, auth_header: dict[str, str]) -> None:
    """SessionStart has no tool_name; must still store and retrieve cleanly."""
    payload = {
        "event_type": "SessionStart",
        "session_id": "s-2",
        "machine_id": "rig-01",
    }
    post_resp = client.post("/events", json=payload, headers=auth_header)
    assert post_resp.status_code == 200, post_resp.text

    get_resp = client.get("/events", params={"session_id": "s-2"})
    assert get_resp.status_code == 200
    rows = get_resp.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["event_type"] == "SessionStart"
    assert row["tool_name"] is None


def test_response_carries_request_id(client: TestClient, auth_header: dict[str, str]) -> None:
    """RequestIdMiddleware should echo a request_id back."""
    resp = client.get("/events")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    assert len(resp.headers["x-request-id"]) > 0


def test_ingest_requires_auth(client: TestClient) -> None:
    resp = client.post(
        "/events",
        json={"event_type": "PreToolUse", "session_id": "s-x", "machine_id": "m-x"},
    )
    assert resp.status_code == 401

"""Direct demonstration of the broadcast bug fix.

Historically, `_build_payload` called `evt.tool_name.lower()`, which raised
`AttributeError` on `SessionStart` / `SessionEnd` events where `tool_name is
None`. The listener swallowed the error silently, so the API stayed green
while the WebSocket broadcast never fired.

This test exercises `_build_payload` directly on a session-boundary event and
asserts it returns a payload with `tool=None` instead of raising.
"""
from __future__ import annotations

from datetime import datetime

from models import Event
from utils.notifications import _build_payload


def test_build_payload_on_session_event_returns_none_tool() -> None:
    event = Event(
        id=1,
        session_id="s-1",
        machine_id="laptop-q",
        event_type="SessionStart",
        tool_name=None,
        payload="{}",
        created_at=datetime(2026, 5, 12, 0, 0, 0),
    )
    payload = _build_payload(event)
    assert payload["event_type"] == "SessionStart"
    assert payload["tool"] is None
    assert payload["session_id"] == "s-1"


def test_build_payload_on_tool_event_lowercases_tool() -> None:
    event = Event(
        id=2,
        session_id="s-1",
        machine_id="laptop-q",
        event_type="PreToolUse",
        tool_name="Read",
        payload="{}",
        created_at=datetime(2026, 5, 12, 0, 0, 0),
    )
    payload = _build_payload(event)
    assert payload["tool"] == "read"

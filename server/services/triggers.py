"""External-trigger dispatch.

A trigger arrives (webhook from GitHub/Forgejo, cron firing, custom POST),
the operator wants the agent to handle it without manual involvement.
This service receives the trigger payload and dispatches to the orchestrator.

Dispatch itself is stubbed for tag-9 — the trigger surface and audit trail
ship as the demonstrable artifact. Wiring to a live `claude -p` invocation
is left as a one-line follow-up.
"""

from __future__ import annotations

from dataclasses import dataclass

from logging_config import get_logger

log = get_logger("services.triggers")


@dataclass
class TriggerRequest:
    source: str  # "github_issue", "forgejo_issue", "cron", "custom"
    title: str
    body: str
    external_id: str | None = None  # issue number, cron id, etc.


def dispatch(trigger: TriggerRequest) -> dict[str, object]:
    """Receive a trigger, log it, hand off to the orchestrator.

    Returns a record describing what was dispatched. The actual
    `claude -p /orchestrate ...` invocation is intentionally a stub here —
    wire via `scripts/issue_to_agent.py` when going live.
    """
    log.info(
        "trigger.received",
        source=trigger.source,
        external_id=trigger.external_id,
        title=trigger.title,
    )
    # NOTE: real dispatch lives in scripts/issue_to_agent.py for now.
    # Inline `claude -p` invocation belongs in a separate runner so the
    # web request can return immediately without blocking on the agent.
    return {
        "dispatched": True,
        "source": trigger.source,
        "external_id": trigger.external_id,
        "runner": "scripts/issue_to_agent.py",
    }

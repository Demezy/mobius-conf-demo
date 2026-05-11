import json
from datetime import datetime

from sqlalchemy.orm import Session

from logging_config import get_logger
from models import Event

log = get_logger("utils.parse")


def parse_event(raw) -> Event:
    """Normalize a raw payload (dict / json string) into an unsaved Event row."""
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("parse.invalid_json", raw_len=len(raw))
            data = {}
    elif isinstance(raw, dict):
        data = raw
    else:
        data = {}

    # figure out the type
    evt = data.get("event_type") or data.get("type") or data.get("hook_event_name")
    if evt is None:
        e = "Unknown"
    else:
        e = str(evt)

    # session_id: try a couple of places
    sid = data.get("session_id")
    if sid is None:
        sid = data.get("sessionId")
    if sid is None:
        # sometimes the agent sends "session" wrapper
        sess = data.get("session")
        if isinstance(sess, dict):
            sid = sess.get("id")
    if not sid:
        sid = "unknown-session"

    mid = data.get("machine_id") or data.get("machine") or data.get("host")
    if not mid:
        mid = "unknown-machine"

    # tool name extraction
    tn = None
    if e == "PreToolUse" or e == "PostToolUse":
        tn = data.get("tool_name")
        if tn is None:
            ti = data.get("tool_input")
            if isinstance(ti, dict):
                tn = ti.get("name")
        if tn is None:
            tn = data.get("tool")
    elif e == "SessionStart" or e == "SessionEnd":
        # session boundary events have no tool
        tn = None
    else:
        # fallback: try the field anyway, sometimes it's set
        tn = data.get("tool_name")

    # normalize timestamp
    ts = data.get("timestamp") or data.get("ts") or data.get("created_at")
    if ts:
        try:
            if isinstance(ts, (int, float)):
                created = datetime.utcfromtimestamp(ts)
            else:
                created = datetime.fromisoformat(str(ts).replace("Z", ""))
        except (ValueError, TypeError):
            log.warning("parse.bad_timestamp", ts=str(ts))
            created = datetime.utcnow()
    else:
        created = datetime.utcnow()

    # build payload blob, drop a few oversized things if present
    blob = dict(data)
    for k in ("file_contents", "diff", "stdout"):
        if k in blob and isinstance(blob[k], str) and len(blob[k]) > 4000:
            blob[k] = blob[k][:4000] + "...[truncated]"

    return Event(
        session_id=sid,
        machine_id=mid,
        event_type=e,
        tool_name=tn,
        payload=json.dumps(blob),
        created_at=created,
    )


def store_event(event: Event, db: Session) -> Event:
    """Persist a parsed event row. Commits and refreshes so callers see the id."""
    try:
        db.add(event)
        db.commit()
        db.refresh(event)
        log.info(
            "event.stored",
            event_id=event.id,
            event_type=event.event_type,
            session_id=event.session_id,
            machine_id=event.machine_id,
            tool_name=event.tool_name,
        )
        return event
    except Exception:
        db.rollback()
        log.exception(
            "event.store_failed",
            event_type=event.event_type,
            session_id=event.session_id,
            machine_id=event.machine_id,
        )
        raise

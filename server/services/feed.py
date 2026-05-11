"""feed service layer — used by some routes, others bypass it"""
import json

from sqlalchemy import desc

from logging_config import get_logger
from models import Event

log = get_logger("services.feed")


def list_events(db, session_id=None, machine_id=None, limit=200):
    q = db.query(Event)
    if session_id:
        q = q.filter(Event.session_id == session_id)
    if machine_id:
        q = q.filter(Event.machine_id == machine_id)
    q = q.order_by(desc(Event.created_at)).limit(limit)
    rows = q.all()
    out = []
    for r in rows:
        try:
            blob = json.loads(r.payload) if r.payload else {}
        except json.JSONDecodeError:
            log.warning("feed.bad_payload_json", event_id=r.id)
            blob = {}
        out.append({
            "id": r.id,
            "session_id": r.session_id,
            "machine_id": r.machine_id,
            "event_type": r.event_type,
            "tool_name": r.tool_name,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "payload": blob,
        })
    return out

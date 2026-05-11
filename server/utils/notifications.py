"""misc notification helpers.

Legacy: SQLAlchemy event listeners drive websocket broadcast and the session
summary update. Violates CLAUDE.md "side effects explicit"; slated for refactor
in tag-8. tag-3 only adds logging at the swallowed exception paths and guards
the `None` tool_name on session-boundary events.
"""
import asyncio
import json
from datetime import datetime

from sqlalchemy import event as sa_event

from logging_config import get_logger
from models import Event, SessionSummary

log = get_logger("utils.notifications")

# in-memory connected websockets
_clients = set()

# bookkeeping counter, not exposed anywhere yet
_metric_counter = {"events_total": 0}


def register_client(ws):
    _clients.add(ws)


def unregister_client(ws):
    try:
        _clients.remove(ws)
    except KeyError:
        pass


async def _send_to_all(msg: str):
    dead = []
    for c in list(_clients):
        try:
            await c.send_text(msg)
        except Exception:
            log.exception("ws.broadcast_failed")
            dead.append(c)
    for d in dead:
        unregister_client(d)


def _build_payload(evt):
    # session-boundary events (SessionStart/SessionEnd) have no tool_name.
    tool = evt.tool_name.lower() if evt.tool_name else None
    return {
        "id": evt.id,
        "session_id": evt.session_id,
        "machine_id": evt.machine_id,
        "event_type": evt.event_type,
        "tool": tool,
        "created_at": evt.created_at.isoformat() if evt.created_at else None,
    }


@sa_event.listens_for(Event, "after_insert")
def broadcast_to_websocket(mapper, connection, target):
    try:
        payload = _build_payload(target)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_send_to_all(json.dumps(payload)))
            log.info(
                "broadcast.scheduled",
                event_id=target.id,
                event_type=target.event_type,
                session_id=target.session_id,
                machine_id=target.machine_id,
                tool_name=target.tool_name,
            )
        except RuntimeError:
            # no running loop in this thread (e.g. sync tests) — drop.
            log.debug(
                "broadcast.no_loop",
                event_id=target.id,
                event_type=target.event_type,
            )
    except Exception:
        log.exception(
            "broadcast.failed",
            event_id=getattr(target, "id", None),
            event_type=getattr(target, "event_type", None),
        )


@sa_event.listens_for(Event, "after_insert")
def update_session_summary(mapper, connection, target):
    # uses the same connection as the inserting transaction
    try:
        tbl = SessionSummary.__table__
        existing = connection.execute(
            tbl.select().where(tbl.c.session_id == target.session_id)
        ).first()
        if existing is None:
            connection.execute(
                tbl.insert().values(
                    session_id=target.session_id,
                    machine_id=target.machine_id,
                    event_count=1,
                    last_seen=datetime.utcnow(),
                )
            )
        else:
            connection.execute(
                tbl.update()
                .where(tbl.c.session_id == target.session_id)
                .values(
                    event_count=(existing.event_count or 0) + 1,
                    last_seen=datetime.utcnow(),
                )
            )
        log.info(
            "summary.updated",
            session_id=target.session_id,
            machine_id=target.machine_id,
        )
    except Exception:
        log.exception(
            "summary.failed",
            session_id=getattr(target, "session_id", None),
        )


@sa_event.listens_for(Event, "after_insert")
def record_metric(mapper, connection, target):
    _metric_counter["events_total"] += 1

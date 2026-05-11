"""Side-effect helpers called explicitly from the route handler.

Post tag-8: these are bare functions, not SQLAlchemy event listeners. They run
in linear order from the ingestion route after the event row has been
committed, so `target.id` and `target.created_at` are populated.
"""
import asyncio
import json
from datetime import datetime

from sqlalchemy.orm import Session

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


def _build_payload(evt: Event) -> dict[str, object]:
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


def broadcast_event(event: Event) -> None:
    try:
        payload = _build_payload(event)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_send_to_all(json.dumps(payload)))
            log.info(
                "broadcast.scheduled",
                event_id=event.id,
                event_type=event.event_type,
                session_id=event.session_id,
                machine_id=event.machine_id,
                tool_name=event.tool_name,
            )
        except RuntimeError:
            # no running loop in this thread (e.g. sync tests) — drop.
            log.debug(
                "broadcast.no_loop",
                event_id=event.id,
                event_type=event.event_type,
            )
    except Exception:
        log.exception(
            "broadcast.failed",
            event_id=getattr(event, "id", None),
            event_type=getattr(event, "event_type", None),
        )


def update_session_summary(event: Event, db: Session) -> None:
    try:
        tbl = SessionSummary.__table__
        existing = db.execute(
            tbl.select().where(tbl.c.session_id == event.session_id)
        ).first()
        if existing is None:
            db.execute(
                tbl.insert().values(
                    session_id=event.session_id,
                    machine_id=event.machine_id,
                    event_count=1,
                    last_seen=datetime.utcnow(),
                )
            )
        else:
            db.execute(
                tbl.update()
                .where(tbl.c.session_id == event.session_id)
                .values(
                    event_count=(existing.event_count or 0) + 1,
                    last_seen=datetime.utcnow(),
                )
            )
        db.commit()
        log.info(
            "summary.updated",
            session_id=event.session_id,
            machine_id=event.machine_id,
        )
    except Exception:
        db.rollback()
        log.exception(
            "summary.failed",
            session_id=getattr(event, "session_id", None),
        )


def record_metric(event: Event) -> None:
    _metric_counter["events_total"] += 1

"""misc notification helpers"""
import asyncio
import json
from datetime import datetime

from sqlalchemy import event as sa_event

from models import Event, SessionSummary


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
            dead.append(c)
    for d in dead:
        unregister_client(d)


def _build_payload(evt):
    # NOTE: tool_name is None on SessionStart/SessionEnd
    return {
        "id": evt.id,
        "session_id": evt.session_id,
        "machine_id": evt.machine_id,
        "event_type": evt.event_type,
        "tool": evt.tool_name.lower(),
        "created_at": evt.created_at.isoformat() if evt.created_at else None,
    }


@sa_event.listens_for(Event, "after_insert")
def broadcast_to_websocket(mapper, connection, target):
    try:
        payload = _build_payload(target)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_send_to_all(json.dumps(payload)))
        except RuntimeError:
            # no running loop in this thread, drop
            pass
    except:
        pass


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
    except:
        pass


@sa_event.listens_for(Event, "after_insert")
def record_metric(mapper, connection, target):
    _metric_counter["events_total"] += 1

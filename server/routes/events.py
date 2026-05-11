from fastapi import APIRouter, Header, HTTPException, Query
from fastapi import Depends
from sqlalchemy.orm import Session

from db import get_db
from logging_config import bind_request_context, get_logger
from services.feed import list_events
from utils.helpers import verify_token_value
from utils.notifications import broadcast_event, update_session_summary
from utils.parse import parse_event, store_event

router = APIRouter()
log = get_logger("routes.events")


def _check_auth(authorization: str | None) -> None:
    if not verify_token_value(authorization):
        log.warning("auth.rejected")
        raise HTTPException(status_code=401, detail="bad token")


@router.post("/events")
async def ingest(
    payload: dict,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _check_auth(authorization)
    event_type = payload.get("event_type") or payload.get("type") or payload.get("hook_event_name")
    session_id = payload.get("session_id")
    machine_id = payload.get("machine_id") or payload.get("machine") or payload.get("host")
    bind_request_context(
        event_type=event_type,
        session_id=session_id,
        machine_id=machine_id,
    )
    log.info(
        "event.received",
        event_type=event_type,
        session_id=session_id,
        machine_id=machine_id,
    )
    log.debug("event.payload", payload=payload)

    # linear pipeline — every side effect named and visible at the call site.
    event = parse_event(payload)
    store_event(event, db)
    broadcast_event(event)
    update_session_summary(event, db)

    return {"ok": True, "id": event.id}


@router.get("/events")
def get_events(
    session_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    limit: int = Query(default=200),
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    # no auth on read for the operator's own dashboard
    log.info(
        "events.list",
        session_id=session_id,
        machine_id=machine_id,
        limit=limit,
    )
    return list_events(db, session_id=session_id, machine_id=machine_id, limit=limit)

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from db import get_db
from models import Event
from utils.helpers import verify_token_value
from utils.parse import process_incoming_event
from services.feed import list_events

router = APIRouter()


def _check_auth(authorization: str | None):
    if not verify_token_value(authorization):
        raise HTTPException(status_code=401, detail="bad token")


@router.post("/events")
async def ingest(payload: dict, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    _check_auth(authorization)
    # use the parse helper to normalize+persist
    event = process_incoming_event(payload, db=db)
    return {"ok": True, "id": event.id}


@router.get("/events")
def get_events(
    session_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    limit: int = Query(default=200),
    db: Session = Depends(get_db),
):
    # no auth on read for the operator's own dashboard
    return list_events(db, session_id=session_id, machine_id=machine_id, limit=limit)

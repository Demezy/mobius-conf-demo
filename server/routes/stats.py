from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from models import Event, SessionSummary

router = APIRouter()


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    # inline logic — no service layer, unlike events.py
    total = db.query(Event).count()
    sessions = db.query(SessionSummary).all()
    return {
        "total_events": total,
        "sessions": [
            {
                "session_id": s.session_id,
                "machine_id": s.machine_id,
                "event_count": s.event_count,
                "last_seen": s.last_seen.isoformat() if s.last_seen else None,
            }
            for s in sessions
        ],
    }

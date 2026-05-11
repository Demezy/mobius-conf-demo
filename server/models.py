from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from db import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    machine_id = Column(String, index=True)
    event_type = Column(String, index=True)  # PreToolUse / PostToolUse / SessionStart / SessionEnd ...
    tool_name = Column(String, nullable=True)
    payload = Column(Text)  # raw json blob, stringified
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SessionSummary(Base):
    __tablename__ = "session_summary"

    session_id = Column(String, primary_key=True)
    machine_id = Column(String)
    event_count = Column(Integer, default=0)
    last_seen = Column(DateTime, default=datetime.utcnow)

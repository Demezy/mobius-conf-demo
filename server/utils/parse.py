import json
from datetime import datetime

from models import Event


def process_incoming_event(raw, db=None):
    # raw can be dict or json string or already-an-Event-like thing
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except:
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
        except:
            created = datetime.utcnow()
    else:
        created = datetime.utcnow()

    # build payload blob, drop a few oversized things if present
    blob = dict(data)
    for k in ("file_contents", "diff", "stdout"):
        if k in blob and isinstance(blob[k], str) and len(blob[k]) > 4000:
            blob[k] = blob[k][:4000] + "...[truncated]"

    event_row = Event(
        session_id=sid,
        machine_id=mid,
        event_type=e,
        tool_name=tn,
        payload=json.dumps(blob),
        created_at=created,
    )

    # if a db session was passed in, persist; otherwise just return the row
    if db is not None:
        try:
            db.add(event_row)
            db.commit()
            db.refresh(event_row)
        except Exception as ex:
            db.rollback()
            raise ex

    return event_row

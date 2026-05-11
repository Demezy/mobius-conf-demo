from fastapi import APIRouter, Header, HTTPException

from logging_config import bind_request_context, get_logger
from services.triggers import TriggerRequest, dispatch
from utils.helpers import verify_token_value

router = APIRouter()
log = get_logger("routes.triggers")


def _check_auth(authorization: str | None) -> None:
    if not verify_token_value(authorization):
        log.warning("auth.rejected")
        raise HTTPException(status_code=401, detail="bad token")


@router.post("/triggers")
async def receive_trigger(
    payload: dict,
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    """Accept a trigger from an external system (Forgejo, custom webhook, cron).

    Shape:
        {"source": "...", "title": "...", "body": "...", "external_id": "..."}
    """
    _check_auth(authorization)

    source = payload.get("source") or "custom"
    title = payload.get("title") or ""
    body = payload.get("body") or ""
    external_id = payload.get("external_id")

    bind_request_context(trigger_source=source, external_id=external_id)
    log.info("trigger.in", source=source, external_id=external_id, title=title)

    trigger = TriggerRequest(
        source=source,
        title=title,
        body=body,
        external_id=external_id,
    )
    return dispatch(trigger)

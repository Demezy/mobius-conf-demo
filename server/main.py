from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from logging_config import configure_logging, get_logger
from middleware import RequestIdMiddleware
from routes.events import router as events_router
from routes.stats import router as stats_router
# importing utils.notifications wires up the @event.listens_for handlers.
# legacy debt: side effects belong at the call site — slated for tag-8.
from utils import notifications

configure_logging()
log = get_logger("main")

app = FastAPI(title="mobius")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIdMiddleware)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    log.info("app.startup", service="mobius")


app.include_router(events_router)
app.include_router(stats_router)


@app.get("/")
def root() -> dict[str, object]:
    return {"service": "mobius", "ok": True}


# random helper sitting inline, used nowhere yet
def _ping() -> str:
    return "pong"


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    notifications.register_client(websocket)
    log.info("ws.connect", client=str(websocket.client))
    try:
        while True:
            # keep-alive: just drain anything client sends, ignore content
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                log.info("ws.disconnect", client=str(websocket.client))
                break
            except Exception:
                log.exception("ws.receive_error", client=str(websocket.client))
    finally:
        notifications.unregister_client(websocket)

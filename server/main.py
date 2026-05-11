from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routes.events import router as events_router
from routes.stats import router as stats_router
# importing utils.notifications wires up the @event.listens_for handlers
from utils import notifications

app = FastAPI(title="mobius")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


app.include_router(events_router)
app.include_router(stats_router)


@app.get("/")
def root():
    return {"service": "mobius", "ok": True}


# random helper sitting inline, used nowhere yet
def _ping():
    return "pong"


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    notifications.register_client(websocket)
    try:
        while True:
            # keep-alive: just drain anything client sends, ignore content
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except:
                pass
    finally:
        notifications.unregister_client(websocket)

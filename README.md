# mobius-conf-demo

## Stack

- Backend: FastAPI + SQLAlchemy + SQLite (Python 3.12+)
- Frontend: Vue 3 + TypeScript + Vite
- WebSocket for real-time event push

## Run

Backend:

```
cd server
uv sync
uv run uvicorn main:app --reload
```

Frontend:

```
cd client
bun install
bun run dev
```

Emit fake events:

```
uv run scripts/emit_fake_events.py
```

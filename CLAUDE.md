# mobius-conf-demo

Multi-machine observability dashboard for Claude Code sessions. Single operator (the user); multiple machines POST lifecycle events to a central FastAPI backend; Vue+TS frontend shows them live via WebSocket.

## Stack

- Backend: FastAPI + SQLAlchemy + SQLite, Python 3.12+
- Frontend: Vue 3 + TypeScript + Vite
- Realtime: WebSocket from server to connected frontend clients
- Tooling: `uv` for Python, `bun` for Node — do not use pip/npm/yarn

## Run

```bash
# backend (port 8000)
cd server && uv sync && uv run uvicorn main:app --reload

# frontend (port 5173)
cd client && bun install && bun run dev

# generate fake events for verification (from repo root)
uv run scripts/emit_fake_events.py
```

## Where things live

Strict layering. New code goes to one of:

- `server/routes/` — HTTP endpoints. Thin. Parse request, call services, return response. No business logic.
- `server/services/` — business logic. All of it. Functions take typed inputs, return typed outputs. Side effects happen here, explicitly, in linear sequence.
- `server/utils/` — pure helpers. No I/O, no DB, no side effects. (Existing `utils/notifications.py` violates this — see legacy debt.)
- `server/models.py` — SQLAlchemy models only.
- `client/src/views/` — page-level Vue components.
- `client/src/components/` — reusable Vue components.
- `client/src/api.ts` — all backend calls. No fetch elsewhere.
- `scripts/` — operator utilities (event emitter, db reset, etc.).

If you can't place new code into one of these, the rule needs a new line — flag it, don't improvise a new folder.

## Style rules

- **Side effects are explicit.** Functional core, imperative shell. Handler functions in `routes/` are the imperative shell — they call services in a visible, linear sequence. Services are pure where possible; when not pure, the impurity is in the function's name (`store_event`, `broadcast_event`).
- **No SQLAlchemy event listeners.** Do not use `@event.listens_for`. Side effects belong at the call site, not in invisible registrations. (The existing listeners in `utils/notifications.py` are legacy debt slated for removal.)
- **Type hints on every function.** No `Any` unless you can justify it in one sentence. Use `Event`, `Session`, etc. — not `dict`.
- **Naming**: `event` for an event row everywhere (never `evt`, `e`, `raw`, `data`, `tn`). `session_id`, `machine_id`, `tool_name` for those fields. Match domain terms exactly.
- **No bare `except:`.** Catch the specific exception. Log it (when logging exists). Never `except: pass`.
- **Python**: snake_case for functions/variables, PascalCase for classes.
- **TypeScript**: camelCase for functions/variables, PascalCase for components/types.

## How to add a feature

1. Identify the rule sheet entry it belongs to (route / service / utility / view / component).
2. Define the types first — input and output of each new function.
3. Wire the route → service → utility chain explicitly. If the feature involves a side effect (DB write, WebSocket push, external call), make it a named function called from the handler. Do not hide it behind a listener or signal.
4. Verify with the fake event emitter if it touches the event flow.

## What this project is NOT

- Not a multi-user SaaS. Single operator. No user registration or login flow.
- Not generic observability. Specifically targets Claude Code event payloads.
- Not optimized for scale. SQLite is fine for the operator's machines.

## Known legacy debt

The baseline tag (`tag-0-baseline`) has known violations of the rules above:

- **`utils/notifications.py`** uses SQLAlchemy event listeners for WebSocket broadcast and session-summary updates. This violates "side effects explicit". Slated for refactor: move side effects into the route handler call site. The cascading-listener pattern is also the source of a silent `AttributeError` on session-boundary events.
- **`utils/parse.py`** contains `process_incoming_event` — an ~80-line function mixing parse + normalize + persist + side-effects, no types, inconsistent naming (`raw` / `data` / `e` / `evt` for the same shape). Needs decomposition + type hints.
- **`helpers/timefmt.py`** lives outside `utils/` for no reason. New helpers go to `utils/`; merge `helpers/` into `utils/` when convenient.
- **`routes/stats.py`** puts query logic inline instead of going through `services/`. Move on next touch.
- **Bare `except: pass`** blocks exist in `utils/parse.py`, `utils/notifications.py`, and `main.py` websocket loop. Replace with specific-exception + log when logging lands.
- **No tests, no structured logging.** Both arrive in subsequent tags.

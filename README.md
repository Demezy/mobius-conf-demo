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

## Triggers

External events can wake the agent without operator action.

**GitHub Actions** — `.github/workflows/agent-trigger.yml` fires when an issue gets the `agent-go` label. The workflow checks out the repo, hands the issue to `scripts/issue_to_agent.py`, and opens a PR with the agent's output.

**Cron / launchd** — `scripts/cron_trigger.py` picks the oldest queued spec from `specs/`, runs `/orchestrate`, archives the spec on success. Schedule with cron or launchd.

**Custom webhook** — `POST /triggers` on the backend accepts a signed payload (`{source, title, body, external_id}`) and dispatches to the orchestrator. Same shared-secret token as `/events`.

All three paths terminate at the same orchestrator (`.claude/commands/orchestrate.md`), which spawns plan → implement → verify in sequence.

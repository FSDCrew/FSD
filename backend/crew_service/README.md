# Crew Service

A FastAPI + CrewAI service that turns crew definitions from the CRUD Service into executable multi-agent flows. It exposes APIs for kicking off crew runs, validates user inputs against the YAML-defined flow state, and ships with an async worker that polls the CRUD queue to execute jobs with LLM-powered agents and browser automation tools.

## Features

- **Crew orchestration API** – Small surface area (`/crew`, `/tasks`, `/status`) that lets the UI validate inputs, kick off runs, and inspect static task metadata.
- **Dynamic flow builder** – Converts `tasks.yaml` + `agents.yaml` into typed Flow state models, generates sequential CrewAI steps, and enforces data dependencies before execution.
- **Queue-backed worker** – `app/services/worker.py` continuously polls the CRUD job queue, executes runs concurrently, streams heartbeats, and persists outputs back to CRUD.
- **Tooling layer** – Built-in Bright Data search, Playwright scraping utilities, Markdown→Word / HTML→Excel converters, and helper scripts for regenerating the CRUD API client.
- **Strict config validation** – Pydantic + custom validators catch missing fields, unknown agents, or incorrect YAML before a flow reaches production.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `app/__init__.py` | FastAPI app factory that wires routers and CORS. |
| `app/api/` | REST endpoints (`crew_endpoints.py`, `tasks_endpoints.py`, `status_endpoints.py`) and the generated CRUD client. |
| `app/services/` | Business logic: `crew_service.py`, `flow/`, `job_executor.py`, and the async `worker.py`. |
| `app/config/agents.yaml` & `tasks.yaml` | Declarative definition of agents, tools, task IO, and flow state schema. |
| `app/lib/tools/` | Playwright/Bright Data powered CrewAI tools invoked by agents. |
| `scripts/` | Helper scripts for running the API, worker, and regenerating the CRUD client. |

## Tech Stack

- **FastAPI** with Uvicorn reloader for the REST surface.
- **CrewAI** (`crewai`, `crewai.flow`) for agent orchestration and guardrailed task execution.
- **OpenAI** models (see `app/services/flow/flow_builder.py`) for both task agents and validation judges.
- **Bright Data + Playwright** tools for research-heavy tasks that require SERP queries and DOM scraping.
- **uv** for dependency management (`pyproject.toml` + `uv.lock`).

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) installed globally
- Access to a running CRUD Service instance (used for crew metadata, queueing, and storage)

## Configuration

Create `backend/crew_service/.env` with the following variables (see `config.py`):

| Variable | Description |
| --- | --- |
| `INTERNAL_CREW_API_KEY` | Shared secret used when this service calls CRUD internal endpoints. |
| `CRUD_SERVICE_URL` | Base URL of the CRUD Service (e.g. `http://localhost:8000`). |
| `QUEUE_POLL_INTERVAL_SECONDS` | Sleep interval between worker poll cycles. |
| `JOB_VISIBILITY_TIMEOUT_SECONDS` | Lease duration handed out by the CRUD queue. |
| `HEARTBEAT_INTERVAL_SECONDS` | Interval for extending the lease while a job is running. |
| `OPENAI_API_KEY` | Used by CrewAI agents + judge LLMs. |
| `HEADLESS` | `true/false` toggle for Playwright launches. |
| `BRIGHT_DATA_API_KEY` / `BRIGHT_DATA_ZONE` | Required by the Bright Data SERP tool wrappers. |

## Setup

1. **Create a virtual environment**
   ```bash
   cd backend/crew_service
   uv venv
   ```
2. **Activate the venv**
   ```bash
   source .venv/bin/activate          # macOS/Linux
   .venv\Scripts\activate             # Windows PowerShell
   ```
3. **Install dependencies**
   ```bash
   uv sync
   ```
4. **Install Playwright browsers (first run only)**
   ```bash
   uv run playwright install chromium
   ```
5. **Verify CRUD Service reachability**
   Ensure `CRUD_SERVICE_URL` is reachable and its OpenAPI schema is available (needed for client regeneration).

## Running the API Locally

```bash
./scripts/local_run_dev.sh
```
- Runs `uvicorn app:app --reload` on `http://localhost:8001`.
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`can 

## Queue Worker

The worker consumes queued jobs from CRUD and runs the dynamic flows.

```bash
./scripts/run_worker.sh
```

What it does:
1. Polls `/internal/queue/claim` until a job is available (up to 3 concurrent jobs).
2. Fetches the crew and crew run metadata, then builds a Flow via `FlowService`.
3. Launches CrewAI tasks; each task can call tools defined in `app/lib/tools`.
4. Streams heartbeats back to CRUD to retain the lease.
5. Serializes flow results + state and updates the crew run output.
6. Cleans up gracefully on SIGINT/SIGTERM by cancelling tasks and marking unfinished jobs as failed.

Run the worker alongside the API when developing locally so you can kick off runs via the HTTP endpoints and see them progress.

## Flow Configuration

- **Agents** live in `app/config/agents.yaml`. Each entry defines the agent's role, goal, backstory, and optional tool list.
- **Tasks and state schema** live in `app/config/tasks.yaml`. Each task declares the context/data fields it reads or writes, the agent key, and prompt templates.
- **Validation**: before committing YAML changes run:
  ```bash
  uv run python app/config/validate_tasks_yaml.py app/config/tasks.yaml
  ```
  This catches duplicate keys, missing fields, invalid cardinalities, and agent mismatches early.
- **Required inputs**: the API derives mandatory user inputs by building a `FlowDependencyGraph` from the YAML—no hardcoding needed.

## CRUD Client Regeneration

Whenever the CRUD Service's OpenAPI schema changes, regenerate the async client used by `CrewService` and the worker:

```bash
./scripts/generate_crud_client.sh
```

The script installs `openapi-python-client==2.11.0` if missing, then writes the client into `app/api/crud_client/`.

## Troubleshooting

- **Playwright errors** – Ensure `HEADLESS` matches your environment (set `HEADLESS=false` when debugging). Run `uv run playwright install chromium` if you see "browser not found" logs.
- **Bright Data failures** – Double-check `BRIGHT_DATA_API_KEY`/`BRIGHT_DATA_ZONE` and confirm the zone allows SERP scraping.
- **Client desync** – If CRUD schemas change, re-run `scripts/generate_crud_client.sh` to avoid `UnexpectedStatus` errors due to outdated models.

# CRUD Service

FastAPI backend that persists crew definitions, tasks, and run history, exposes authenticated APIs for the UI, and provides an internal queue-backed contract that the Crew Service/worker uses to execute automations. It also stores artifacts in S3 and handles IAM-authenticated user access via Cognito.

## Features

- **Crew + task management** – CRUD APIs for crews, nested tasks, required inputs, and ownership rules enforced via Cognito JWTs.
- **Run queue + metadata** – Persists crew run inputs/outputs, tracks queue leases, and exposes internal endpoints for the worker (claim, heartbeat, mark complete/fail).
- **Artifact storage** – Base64 upload + presigned URL retrieval backed by S3 for large file outputs.
- **Internal API surface** – Locked-down routes (X-Internal-Api-Key/Bearer) that power the Crew Service without exposing sensitive operations to end users.
- **Database migrations** – Alembic-managed Postgres schema with helper scripts for generating and applying revisions per environment.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `app/__init__.py` | FastAPI factory, router registration, S3 client bootstrap, DB health check. |
| `app/api/` | Route handlers for crews, users, tasks, artifacts, crew runs, internal queue, and status endpoints. |
| `app/services/` | Business logic for CRUD, queue, artifact/S3 operations, Cognito auth, etc. |
| `app/db/` | SQLAlchemy async engine/session helpers. |
| `app/models` & `schemas` | Pydantic models shared across routes and services. |
| `alembic/` | Migration environment + generated revisions. |
| `scripts/` | Local DB bootstrap, alembic helpers, uvicorn launcher, and crew client generator. |
| `tests/` | Pytest suite (currently artifact endpoint coverage). |

## Tech Stack

- **FastAPI + Uvicorn** serving async REST APIs
- **SQLAlchemy (async)** ORM/data access, **Alembic** migrations, **PostgreSQL** storage
- **AWS S3 (boto3)** for artifact persistence
- **Cognito / JWKS** validation for user auth
- **uv** for dependency and virtualenv management

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) installed globally
- Docker (for `scripts/start_local_db.sh` convenience script)
- Access to AWS credentials/S3 bucket + Cognito user pool configured for your app
- Crew Service running (internal client + downstream orchestrator)

## Configuration

Create `backend/crud_service/.env` and populate the following (see `config.py`):

| Variable | Description |
| --- | --- |
| `INTERNAL_CREW_API_KEY` | Shared secret that the Crew Service/worker passes via `Authorization` or `X-Internal-Api-Key`. |
| `CREW_SERVICE_URL` | Used by `scripts/generate_crew_client.sh` (default `http://localhost:8001`). |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Postgres connection pieces. `CRUD_DATABASE_URL` is derived automatically. |
| `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_APP_CLIENT_ID` | Used to build the JWKS URL for verifying JWTs. |
| `S3_BUCKET_NAME`, `S3_REGION` | Artifact storage target. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Optional – set if you are not using an IAM role. (Legacy code also looks for `S3_ACCESS_KEY`/`S3_SECRET_KEY`; define both sets if needed.) |

> **Tip:** Keep a `.env.example` in sync with the values above so onboarding remains painless.

## Setup

1. **Create a venv & install deps**
   ```bash
   cd backend/crud_service
   uv venv
   source .venv/bin/activate          # macOS/Linux
   # .venv\Scripts\activate          # Windows
   uv sync
   ```
2. **Start Postgres (Docker)**
   ```bash
   ./scripts/start_local_db.sh
   ```
   Creates a `postgres-crew-crud` container with database `crud`, user `crew`, password `postgres`, data persisted under `.data/postgresql/crud`.
3. **Apply migrations**
   ```bash
   ./scripts/db_migrate_apply.sh local
   ```

## Running the API Locally

```bash
./scripts/local_run_dev.sh
```
- Serves FastAPI at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `GET /status/health`

### Key API Groups

- `/crew` – CRUD endpoints scoped to the authenticated user.
- `/task` – Manage tasks nested under crews.
- `/crew-run` – Fetch historic runs + outputs.
- `/artifact` – Upload artifacts via Base64 payload and retrieve presigned URLs.
- `/internal/*` – Crew Service integrations (create runs, claim queue jobs, update status, heartbeat, fetch crew metadata). These require `INTERNAL_CREW_API_KEY`.

## Database Migrations

- **Create a migration**
  ```bash
  ./scripts/db_migrate.sh "add_queue_index"
  ```
- **Apply migrations**
  ```bash
  ./scripts/db_migrate_apply.sh local      # or develop|staging|production
  ```
- **Downgrade manually**
  ```bash
  alembic downgrade -1
  ```

Alembic respects the `ENVIRONMENT` variable exported inside the helper scripts.

## Generating the Crew Client

The CRUD service depends on a generated client for calling the Crew Service (e.g., internal automation). Regenerate it after the Crew Service OpenAPI changes:

```bash
./scripts/generate_crew_client.sh
```

Outputs to `app/api/crew_client/` using `openapi-python-client==2.11.0`.

## Authentication Flow

- End-user requests must carry `Authorization: Bearer <JWT>` from Cognito or a compatible `*.idToken` cookie. `app.dependencies.get_token_from_request` checks both.
- Internal automation (Crew Service worker) authenticates via `X-Internal-Api-Key` or Bearer token matching `INTERNAL_CREW_API_KEY`.
- On startup the app performs a DB connectivity check and instantiates an S3 client using the configured region/credentials.

## Worker Handshake

External workers interact solely with `/internal`:

1. `POST /internal/crew-run/create` – Validate the end-user token and enqueue metadata.
2. `POST /internal/queue/claim` – Atomically claim the next job; returns queue + crew run IDs and lease token.
3. `POST /internal/queue/{id}/heartbeat` – Extend lease while a flow runs.
4. `PUT /internal/queue/{id}/status` – Mark `COMPLETED` or `FAILED` when done.
5. `PUT /internal/crew-run/{crew_run_id}/output` – Persist final outputs plus artifact keys.

These endpoints all require the shared internal API key.

## Testing

```bash
uv run pytest
```
The existing suite mocks authentication/S3 interactions for artifact endpoints. Follow that pattern when adding coverage for other routers/services.

## Troubleshooting

- **Database connection failed** – ensure `.env` values match the running Postgres container and rerun `./scripts/start_local_db.sh` to recreate it.
- **401s on public routes** – verify the Cognito token audience matches `COGNITO_APP_CLIENT_ID` and that your request includes either the header or `*.idToken` cookie.
- **S3 upload errors** – confirm AWS credentials/role allow `PutObject`/`GetObject` on `S3_BUCKET_NAME`. For local testing, consider using [LocalStack](https://www.localstack.cloud/).
- **Alembic revision conflicts** – check `alembic/versions` for duplicate revision IDs, then regenerate after rebasing.
- **Client drift** – if you see `UnexpectedStatus` when this service calls Crew Service, regenerate the client using the script above to sync models.
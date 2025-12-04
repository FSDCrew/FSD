# FSD - Full Stack Development Project

A full-stack application for managing and executing multi-agent AI crew workflows. The system consists of a Next.js frontend, a CRUD service for data persistence and queue management, and a Crew service that orchestrates AI agents using CrewAI.

## Architecture

The project is composed of three main services:

- **Frontend** (`frontend/`) - Next.js application providing the user interface for managing crews, tasks, and viewing run history
- **CRUD Service** (`backend/crud_service/`) - FastAPI backend that persists crew definitions, tasks, run history, and manages an internal job queue
- **Crew Service** (`backend/crew_service/`) - FastAPI + CrewAI service that executes crew runs using multi-agent workflows with LLM-powered agents and browser automation tools

The services communicate as follows:
- Frontend → CRUD Service (user-facing APIs)
- Frontend → Crew Service (crew orchestration APIs)
- Crew Service → CRUD Service (internal queue APIs)
- Crew Worker → CRUD Service (queue polling and job execution)

## Prerequisites

Before starting local development, ensure you have the following installed:

- **Docker** - Required for running the local PostgreSQL database
- **Python 3.11+** - Required for backend services
- **[uv](https://github.com/astral-sh/uv)** - Python package manager (install globally)
- **Node.js** - Required for frontend (check `frontend/package.json` for version requirements)
- **AWS Credentials** - Access to S3 bucket and Cognito user pool configured for your app
- **OpenAI API Key** - Required for CrewAI agents and LLM operations
- **Bright Data API Key** (optional) - Required for SERP search functionality in crew tools

## Local Development Setup

This guide covers local development setup. Each service runs independently and requires its own configuration.

### 1. Database Setup

The CRUD service requires a PostgreSQL database. You can use Docker to run a local instance:

```bash
cd backend/crud_service
./scripts/start_local_db.sh
```

This creates a PostgreSQL container with:
- Database: `crud`
- User: `crew`
- Password: `postgres`
- Port: `5432`

Alternatively, you can use an existing PostgreSQL instance by configuring the connection in `backend/crud_service/.env`.

### 2. CRUD Service Setup

1. **Navigate to the CRUD service directory:**
   ```bash
   cd backend/crud_service
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   uv sync
   ```

3. **Create `.env` file** (see `backend/crud_service/README.md` for all required variables):
   ```bash
   # Required variables:
   INTERNAL_CREW_API_KEY=<shared-secret>
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=crud
   DB_USER=crew
   DB_PASSWORD=postgres
   COGNITO_REGION=<your-region>
   COGNITO_USER_POOL_ID=<your-pool-id>
   COGNITO_APP_CLIENT_ID=<your-client-id>
   S3_BUCKET_NAME=<your-bucket>
   S3_REGION=<your-region>
   AWS_ACCESS_KEY_ID=<your-key>
   AWS_SECRET_ACCESS_KEY=<your-secret>
   ```

4. **Apply database migrations:**
   ```bash
   ./scripts/db_migrate_apply.sh local
   ```

5. **Start the CRUD service:**
   ```bash
   ./scripts/local_run_dev.sh
   ```

The service will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/status/health`

### 3. Crew Service Setup

1. **Navigate to the Crew service directory:**
   ```bash
   cd backend/crew_service
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   uv venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   uv sync
   ```

3. **Install Playwright browsers (first run only):**
   ```bash
   uv run playwright install chromium
   ```

4. **Create `.env` file** (see `backend/crew_service/README.md` for all required variables):
   ```bash
   # Required variables:
   INTERNAL_CREW_API_KEY=<same-secret-as-crud-service>
   CRUD_SERVICE_URL=http://localhost:8000
   OPENAI_API_KEY=<your-openai-key>
   HEADLESS=true
   QUEUE_POLL_INTERVAL_SECONDS=5
   JOB_VISIBILITY_TIMEOUT_SECONDS=300
   HEARTBEAT_INTERVAL_SECONDS=60
   # Optional:
   BRIGHT_DATA_API_KEY=<your-key>
   BRIGHT_DATA_ZONE=<your-zone>
   ```

5. **Start the Crew service API:**
   ```bash
   ./scripts/local_run_dev.sh
   ```

The service will be available at `http://localhost:8001`
- Swagger UI: `http://localhost:8001/docs`

### 4. Crew Service Worker Setup

The worker is a separate process that polls the CRUD queue and executes crew runs. It should be run alongside the Crew service API.

1. **In a separate terminal, navigate to the Crew service directory:**
   ```bash
   cd backend/crew_service
   source .venv/bin/activate  # Ensure venv is activated
   ```

2. **Start the worker:**
   ```bash
   ./scripts/run_worker.sh
   ```

The worker will:
- Poll `/internal/queue/claim` for available jobs
- Execute crew runs using CrewAI agents
- Stream heartbeats to maintain lease
- Persist results back to CRUD service

**Note:** The worker is required for executing crew runs. Without it, jobs will be queued but not processed.

### 5. Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Create `.env.local` file** (if needed for local configuration):
   ```bash
   # Add any frontend-specific environment variables here
   # See frontend/README.md for details
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

The frontend will be available at `http://localhost:3000`

## Service URLs

When running services locally, they are available at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| CRUD Service | http://localhost:8000 | FastAPI backend, Swagger at `/docs` |
| Crew Service | http://localhost:8001 | Crew orchestration API, Swagger at `/docs` |

## Deployment

The deployed application is available at:

**www.campaign.ongspace.com**

## Documentation

### Service-Specific Documentation

Each service has its own detailed README:

- **[CRUD Service README](backend/crud_service/README.md)** - Database setup, migrations, API endpoints, authentication
- **[Crew Service README](backend/crew_service/README.md)** - Flow configuration, worker setup, tooling layer

### Additional Documentation

Comprehensive documentation is available in:

- **[Backend Documentation](backend/crew_service/docs/)** - Detailed guides covering:
  - [Dynamic Flow](backend/crew_service/docs/dynamic_flow.md) - How flows are built from tasks
  - [Worker](backend/crew_service/docs/worker.md) - Worker implementation details
  - [Required Inputs](backend/crew_service/docs/required_inputs.md) - Backend and frontend integration guides
  - [Configuration](backend/crew_service/docs/configuration.md) - YAML configuration structure
  - [Custom Types](backend/crew_service/docs/custom_types.md) - Type system documentation
  - [CrewRun Cancellation](backend/crew_service/docs/crewrun_cancellation.md) - Logic for Crew Run Cancellation
  - [CrewRun Retry](backend/crew_service/docs/crewrun_cancellation.md) - Logic for Retrying a Crew from Any Completed Task

- **[Notion Documentation](https://www.notion.so/Share-With-Prof-2be3bdec703d80d68f7ffe5698c75b0d)** - Project documentation and shared resources

## Troubleshooting

### Common Issues

**Database connection failed**
- Ensure PostgreSQL is running and accessible
- Verify `.env` variables match your database configuration
- Check that migrations have been applied: `./scripts/db_migrate_apply.sh local`

**401 Unauthorized errors**
- Verify Cognito configuration in `backend/crud_service/.env`
- Ensure JWT tokens include the correct audience (`COGNITO_APP_CLIENT_ID`)
- Check that requests include `Authorization: Bearer <token>` header

**Crew runs not executing**
- Ensure the Crew Service worker is running (`./scripts/run_worker.sh`)
- Verify `CRUD_SERVICE_URL` in Crew Service `.env` points to the correct CRUD service
- Check that `INTERNAL_CREW_API_KEY` matches between CRUD and Crew services

**S3 upload errors**
- Confirm AWS credentials are configured correctly
- Verify S3 bucket permissions allow `PutObject` and `GetObject`
- For local testing, consider using [LocalStack](https://www.localstack.cloud/)

**Playwright errors**
- Run `uv run playwright install chromium` in the Crew service directory
- Set `HEADLESS=false` in `.env` for debugging browser issues

**Client desync errors**
- If CRUD or Crew service schemas change, regenerate clients:
  - CRUD → Crew: `cd backend/crew_service && ./scripts/generate_crud_client.sh`
  - Crew → CRUD: `cd backend/crud_service && ./scripts/generate_crew_client.sh`

### Getting Help

For service-specific issues, refer to:
- [CRUD Service README](backend/crud_service/README.md) - Troubleshooting section
- [Crew Service README](backend/crew_service/README.md) - Troubleshooting section
- [Backend Documentation](backend/crew_service/docs/) - Detailed technical documentation

## Project Structure

```
FSD/
├── backend/
│   ├── crud_service/     # FastAPI CRUD service
│   └── crew_service/     # FastAPI + CrewAI service
│       └── docs/         # Additional documentation
├── frontend/             # Next.js frontend
├── terraform/            # Infrastructure as code
```

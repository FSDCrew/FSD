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

- **Docker and Docker Compose** - Required for Docker Compose setup (recommended). Docker Compose handles all services automatically including PostgreSQL, backend services, frontend, and worker.
- **Python 3.11+** - Required for manual setup of backend services (optional if using Docker Compose)
- **[uv](https://github.com/astral-sh/uv)** - Python package manager (required for manual setup, install globally)
- **Node.js** - Required for manual frontend setup (check `frontend/package.json` for version requirements)
- **AWS Credentials** - Access to S3 bucket and Cognito user pool configured for your app
- **OpenAI API Key** - Required for CrewAI agents and LLM operations
- **Bright Data API Key** (optional) - Required for SERP search functionality in crew tools

**Note:** Docker Compose is the recommended approach for local development as it automatically manages all services, dependencies, and networking. Manual setup is available for developers who prefer to run services individually.

## Docker Compose Setup (Recommended)

Docker Compose provides the easiest way to run the entire application stack locally. It automatically handles service dependencies, networking, database persistence, and includes health checks to ensure services start in the correct order.

### Prerequisites

- **Docker** (version 20.10+) and **Docker Compose** (version 2.0+)
- All environment variables configured in a root `.env` file (see below)

### Quick Start

1. **Create a `.env` file in the project root** with all required environment variables:

```bash
# Shared secret between services
INTERNAL_CREW_API_KEY=<your-shared-secret>

# Database configuration (optional - defaults provided)
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=crud_db
POSTGRES_PORT=5433

# CRUD Service configuration
DB_HOST=crud_db  # Use Docker service name for internal communication
DB_PORT=5432     # Internal port (not host port)
DB_NAME=crud_db
DB_USER=user
DB_PASSWORD=pass

# AWS/Cognito configuration
COGNITO_REGION=<your-region>
COGNITO_USER_POOL_ID=<your-pool-id>
COGNITO_APP_CLIENT_ID=<your-client-id>
S3_BUCKET_NAME=<your-bucket>
S3_REGION=<your-region>
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
S3_ACCESS_KEY=<your-key>  # Legacy support
S3_SECRET_KEY=<your-secret>  # Legacy support

# Crew Service configuration
CRUD_SERVICE_URL=http://crud_service:6010  # Use Docker service name
OPENAI_API_KEY=<your-openai-key>
HEADLESS=true
QUEUE_POLL_INTERVAL_SECONDS=5
JOB_VISIBILITY_TIMEOUT_SECONDS=300
HEARTBEAT_INTERVAL_SECONDS=60

# Optional: Bright Data
BRIGHT_DATA_API_KEY=<your-key>
BRIGHT_DATA_ZONE=<your-zone>

# Optional: Orshot
ORSHOT_API_KEY=<your-key>
ORSHOT_MOCK_MODE=false

# Optional: Gemini
GEMINI_API_KEY=<your-key>

# Frontend configuration
FRONTEND_ORIGIN=http://localhost:3000
```

**Note:** Database credentials have defaults (`user`, `pass`, `crud_db`) but can be overridden via environment variables. For internal service communication, use Docker service names (`crud_db`, `crud_service`, `crew_service`) instead of `localhost`.

2. **Build and start all services:**

```bash
docker-compose up --build
```

This will:
- Build all service images
- Start PostgreSQL database with persistent storage
- Start CRUD service (waits for database to be healthy)
- Start Crew service API (waits for CRUD service to be healthy)
- Start Crew worker (waits for CRUD service to be healthy)
- Start Frontend (waits for backend services)
- Start pgAdmin (database management UI)

3. **Apply database migrations:**

In a separate terminal, run migrations inside the CRUD service container:

```bash
docker-compose exec crud_service alembic upgrade head
```

Or if you have a local migration script:

```bash
docker-compose exec crud_service bash -c "cd /app && alembic upgrade head"
```

### Service Management

**Start services:**
```bash
docker-compose up
```

**Start services in detached mode (background):**
```bash
docker-compose up -d
```

**Stop services:**
```bash
docker-compose down
```

**Stop services and remove volumes (⚠️ deletes database data):**
```bash
docker-compose down -v
```

**Restart a specific service:**
```bash
docker-compose restart crud_service
```

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f crud_service
docker-compose logs -f crew_service
docker-compose logs -f crew_worker
```

**Rebuild services after code changes:**
```bash
docker-compose up --build
```

### Service URLs (Docker Compose)

When running with Docker Compose, services are available at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| CRUD Service | http://localhost:6010 | FastAPI backend, Swagger at `/docs` |
| Crew Service | http://localhost:6011 | Crew orchestration API, Swagger at `/docs` |
| pgAdmin | http://localhost:5434 | Database management UI (admin@admin.com / admin) |
| PostgreSQL | localhost:5433 | Direct database connection (if needed) |

**Internal Service Communication:** Services communicate using Docker service names:
- `crud_db` - PostgreSQL database
- `crud_service:6010` - CRUD service API
- `crew_service:6011` - Crew service API

### Database Persistence

PostgreSQL data is persisted in a Docker volume (`postgres_data`). This means:
- Database data survives container restarts
- Data persists even after `docker-compose down` (unless you use `-v` flag)
- To reset the database, use `docker-compose down -v` and restart

### Health Checks

All services include health checks that ensure proper startup order:
- `crud_db` - Checks PostgreSQL readiness
- `crud_service` - Checks API health endpoint
- `crew_service` - Checks API health endpoint
- `pgadmin` - Checks web interface availability

Services wait for their dependencies to be healthy before starting.

### Troubleshooting Docker Compose

**Services won't start:**
- Check logs: `docker-compose logs <service-name>`
- Verify `.env` file exists and has all required variables
- Ensure ports aren't already in use (3000, 6010, 6011, 5433, 5434)

**Database connection errors:**
- Ensure `DB_HOST=crud_db` (Docker service name, not localhost)
- Verify database is healthy: `docker-compose ps`
- Check database logs: `docker-compose logs crud_db`

**Crew runs not executing:**
- Verify `crew_worker` container is running: `docker-compose ps`
- Check worker logs: `docker-compose logs crew_worker`
- Ensure `CRUD_SERVICE_URL=http://crud_service:6010` uses Docker service name

**Rebuild after dependency changes:**
```bash
docker-compose build --no-cache <service-name>
docker-compose up
```

## Local Development Setup

> **Note:** If you prefer a simpler setup, consider using [Docker Compose](#docker-compose-setup-recommended) which handles all services automatically. This section covers manual setup for developers who want to run services individually.

This guide covers manual setup for local development. Each service runs independently and requires its own configuration.

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
- Port: `5432` (mapped to host port `5433` in docker-compose)

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
   DB_PORT=5433  # or 5432 if using local Postgres
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

### Manual Setup (Local Development)

When running services manually (see [Local Development Setup](#local-development-setup)), services are available at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| CRUD Service | http://localhost:8000 | FastAPI backend, Swagger at `/docs` |
| Crew Service | http://localhost:8001 | Crew orchestration API, Swagger at `/docs` |

### Docker Compose Setup

When using Docker Compose (see [Docker Compose Setup](#docker-compose-setup-recommended)), services are available at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| CRUD Service | http://localhost:6010 | FastAPI backend, Swagger at `/docs` |
| Crew Service | http://localhost:6011 | Crew orchestration API, Swagger at `/docs` |
| pgAdmin | http://localhost:5434 | Database management UI (admin@admin.com / admin) |
| PostgreSQL | localhost:5433 | Direct database connection (if needed) |

**Important:** When using Docker Compose, services communicate internally using Docker service names (`crud_db`, `crud_service`, `crew_service`) rather than `localhost`. This is automatically configured in the docker-compose.yml file.

## Deployment

The deployed application is available at:

**https://campaign.ongspace.com**

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

**Docker Compose issues**
- Services won't start: Check logs with `docker-compose logs <service-name>` and verify `.env` file has all required variables
- Port conflicts: Ensure ports 3000, 6010, 6011, 5433, 5434 are not in use
- Database connection errors: Verify `DB_HOST=crud_db` (Docker service name) in `.env`, not `localhost`
- Worker not processing jobs: Check `docker-compose ps` to ensure `crew_worker` container is running, view logs with `docker-compose logs crew_worker`
- Need to rebuild after code changes: Use `docker-compose up --build` or rebuild specific service: `docker-compose build --no-cache <service-name>`

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
└── docker-compose.yml    # Docker Compose configuration
```

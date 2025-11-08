# CRUD Service

A FastAPI-based CRUD service for managing crews, tasks, and related entities. This service provides RESTful APIs for creating, reading, updating, and managing crew configurations and their associated tasks.

## Features

- **Crew Management**: Create, read, and update crew configurations
- **Task Management**: Create, update, and manage tasks associated with crews
- **Database Migrations**: Alembic-based database schema management
- **CORS Support**: Configured for cross-origin requests

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **PostgreSQL**: Database
- **Pydantic**: Data validation using Python type annotations
- **uv**: Fast Python package installer and resolver

## Setup

### 1. Environment Setup
Create a virtual environment
```
uv venv
```
Activate virtual environment
```
source .venv/bin/activate  # macos
.venv\Scripts\activate uv sync # windows
```
Install Dependencies
```
uv sync
```

### 2. Database Initialization

#### Start Local Database

Start a local PostgreSQL database using Docker by using `./scripts/start_local_db.sh`

This script will:
- Start a PostgreSQL container named `postgres-crew-crud`
- Create a database named `crud`
- Set up user `crew` with password `postgres`
- Expose the database on port `5432`

#### Apply Database Migrations

Apply all existing migrations to initialize the database schema:

```
./scripts/db_migrate_apply.sh local
```

### 3. Configuration

### Development Mode

Run `./scripts/local_run_dev.sh`
## API Documentation

Once the service is running, interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database Migrations

### Creating a New Migration

Generate a new migration file:

`./scripts/db_migrate.sh <migration_name>` will create a new migration file in `alembic/versions/` that you can edit before applying.

### Applying Migrations

Apply all pending migrations:

`./scripts/db_migrate_apply.sh local` to apply migrations in `/alembic/versions` to your db

### Downgrading Migrations

To downgrade by one migration:

```
alembic downgrade -1
```

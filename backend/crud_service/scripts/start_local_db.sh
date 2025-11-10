#!/usr/bin/env bash
set -euo pipefail

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="crud"
DB_USER="crew"
DB_PASSWORD="postgres"

DB_DOCKER_NAME="postgres-crew-crud"
PG_IMAGE="postgres:15.1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/.data/postgresql/crud"

mkdir -p "${DATA_DIR}"

echo "Starting PostgreSQL container '${DB_DOCKER_NAME}'..."
echo "Data dir: ${DATA_DIR}"

docker rm -f "${DB_DOCKER_NAME}" >/dev/null 2>&1 || true

docker run --name "${DB_DOCKER_NAME}" \
  -e POSTGRES_USER="${DB_USER}" \
  -e POSTGRES_PASSWORD="${DB_PASSWORD}" \
  -e POSTGRES_DB="${DB_NAME}" \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -p "${DB_PORT}:5432" \
  -v "${DATA_DIR}:/var/lib/postgresql/data" \
  -d "${PG_IMAGE}"

echo
echo "Container started. Checking logs (first few lines):"
docker logs --tail 20 "${DB_DOCKER_NAME}" || true

echo
echo "Postgres should be available at:"
echo "  host=${DB_HOST}  port=${DB_PORT}  db=${DB_NAME}  user=${DB_USER}"
echo
echo "psql connection:"
echo "  PGPASSWORD='${DB_PASSWORD}' psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME}"
echo
echo "SQLAlchemy URL (sync):"
echo "  postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo
echo "SQLAlchemy URL (async):"
echo "  postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo
echo "Tip: if connection fails immediately, give Postgres a few seconds to finish init, or run:"
echo "  docker logs -f ${DB_DOCKER_NAME}"

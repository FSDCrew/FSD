#!/bin/bash

BASEDIR=$(dirname "$0")
MIGRATION_NAME=$1

export ENVIRONMENT=local
cd "${BASEDIR}"/.. && alembic revision --autogenerate -m "${MIGRATION_NAME}"

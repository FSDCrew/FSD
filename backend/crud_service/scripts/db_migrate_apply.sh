#!/bin/bash

BASEDIR=$(dirname "$0")
ENVIRONMENT=$1

case "$ENVIRONMENT" in
    local|develop|staging|production)
        export ENVIRONMENT=${ENVIRONMENT}
        cd "${BASEDIR}"/.. && alembic upgrade head
        if [[ $? != 0 ]]; then
            exit 1
        fi
        ;;
    *)
        echo input env: ${ENVIRONMENT} is not supported!
        exit 1
        ;;
esac

#!/bin/bash

# Script to generate CRUD service API client from OpenAPI specification

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

OPENAPI_URL="${CREW_SERVICE_URL:-http://localhost:8001/openapi.json}"

OUTPUT_DIR="$PROJECT_ROOT/app/api"
CLIENT_DIR="$OUTPUT_DIR/crew_client"

echo "Generating Crew service API client..."
echo "OpenAPI URL:      $OPENAPI_URL"
echo "Output directory: $CLIENT_DIR"

if ! command -v openapi-python-client >/dev/null 2>&1; then
    echo "openapi-python-client not found. Installing (pinned to 2.11.0)..."
    python -m pip install "openapi-python-client==2.11.0"
fi

mkdir -p "$OUTPUT_DIR"

openapi-python-client generate \
    --url "$OPENAPI_URL" \
    --output-path "$CLIENT_DIR" \
    --meta none \
    --overwrite

echo "Client generated successfully at $CLIENT_DIR"

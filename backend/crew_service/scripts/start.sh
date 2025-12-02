#!/bin/bash

echo "Starting Worker..."
python -m app.run_worker &

echo "Starting Uvicorn..."
exec uvicorn app:app --host 0.0.0.0 --port 6011
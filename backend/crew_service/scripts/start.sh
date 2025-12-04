#!/bin/bash

echo "Starting Uvicorn..."
exec uvicorn app:app --host 0.0.0.0 --port 6011
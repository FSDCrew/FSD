@echo off
echo Starting Uvicorn with uv...

uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000


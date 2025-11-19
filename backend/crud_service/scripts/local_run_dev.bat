@echo off
echo Starting Uvicorn with uv...

uv run uvicorn app:app --reload --host 127.0.0.1 --port 8000


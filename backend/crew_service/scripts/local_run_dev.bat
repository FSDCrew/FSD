@echo off
echo Starting Uvicorn development server...

uv run uvicorn app:app ^
    --reload ^
    --reload-dir . ^
    --host 0.0.0.0 ^
    --port 8001

pause
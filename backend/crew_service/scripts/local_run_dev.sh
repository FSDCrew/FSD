#!/bin/bash

uv run uvicorn app:app --reload --reload-dir . --reload-exclude ".venv" --host 0.0.0.0 --port 8001
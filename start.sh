#!/bin/bash
set -e

# Railway и другие платформы задают PORT; локально по умолчанию 8000.
PORT="${PORT:-8000}"

cd /app/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" &

cd /app/bot
exec python main.py

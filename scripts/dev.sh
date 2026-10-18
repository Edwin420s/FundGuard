#!/usr/bin/env bash
set -euo pipefail
echo "Run backend and frontend in separate terminals:"
echo "  cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload"
echo "  cd frontend && npm install && npm run dev"

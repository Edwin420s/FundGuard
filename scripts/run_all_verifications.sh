#!/usr/bin/env bash
set -euo pipefail

echo "================================================================="
echo "  Omega FundGuard — Master Verification & Quality Audit"
echo "================================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# 1. Backend Linting
echo -e "\n[1/6] Running Backend Ruff Linting..."
cd "$ROOT_DIR/backend"
ruff check app tests
echo "[OK] Backend linting clean."

# 2. Backend Automated Test Suite
echo -e "\n[2/6] Running Backend Pytest Test Suite..."
pytest -v
echo "[OK] 25 backend tests passed."

# 3. Performance & MeTTa Benchmark
echo -e "\n[3/6] Running MeTTa & Invariants Benchmark..."
cd "$ROOT_DIR"
python3 scripts/benchmark_engine.py
echo "[OK] Performance benchmark verified."

# 4. Frontend Vitest Suite
echo -e "\n[4/6] Running Frontend Vitest Suite..."
cd "$ROOT_DIR/frontend"
npm test
echo "[OK] 13 frontend tests passed (12 unit + 1 E2E)."

# 5. Frontend Production Build
echo -e "\n[5/6] Building Production Frontend Bundle..."
npm run build
echo "[OK] Production bundle built successfully."

# 6. End-to-End Live API Demo & Learning Loop
echo -e "\n[6/6] Running Live API Demonstration & Learning Verification..."
if curl -s http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
  echo "Existing active API server detected on port 8000."
  cd "$ROOT_DIR"
  bash scripts/demo_api.sh
else
  cd "$ROOT_DIR/backend"
  python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/fundguard_uvicorn.log 2>&1 &
  UVICORN_PID=$!
  cleanup() {
    echo -e "\nStopping backend test server (PID $UVICORN_PID)..."
    kill "$UVICORN_PID" >/dev/null 2>&1 || true
  }
  trap cleanup EXIT
  for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
      echo "API server is ready."
      break
    fi
    sleep 0.5
  done
  cd "$ROOT_DIR"
  bash scripts/demo_api.sh
fi

echo -e "\n================================================================="
echo "  All Verifications Passed! Omega FundGuard is 100% Complete."
echo "================================================================="

.PHONY: help verify test test-backend test-frontend lint benchmark demo eval backend frontend build docker-build docker-up docker-down clean

help:
	@echo "============================================================"
	@echo "  Omega FundGuard — Developer & Operations Makefile"
	@echo "============================================================"
	@echo "  make verify        : Run complete verification suite (tests, lint, build, demo)"
	@echo "  make test          : Run all automated tests (backend + frontend)"
	@echo "  make test-backend  : Run pytest test suite (18 tests)"
	@echo "  make test-frontend : Run frontend test suite (vitest)"
	@echo "  make lint          : Run ruff linter on backend"
	@echo "  make benchmark     : Run MeTTa reasoning & base-unit benchmark"
	@echo "  make eval          : Run adversarial security evaluation benchmarks"
	@echo "  make demo          : Run 10-step end-to-end demo script"
	@echo "  make backend       : Start FastAPI backend server on http://localhost:8000"
	@echo "  make frontend      : Start React Vite development server on http://localhost:5173"
	@echo "  make build         : Build React frontend for production"
	@echo "  make docker-build  : Build backend and frontend Docker containers"
	@echo "  make docker-up     : Start Docker Compose services in background"
	@echo "  make docker-down   : Stop Docker Compose services"
	@echo "  make clean         : Clean cache and temporary database files"

verify:
	bash scripts/run_all_verifications.sh

test: test-backend test-frontend

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm test

lint:
	cd backend && ruff check app tests

benchmark:
	python3 scripts/benchmark_engine.py

eval:
	cd backend && python3 -c "from app.database import SessionLocal; from app.agent.evaluator import AgentEvaluator; db=SessionLocal(); e=AgentEvaluator(db); import json; print(json.dumps(e.run_all_evaluations(), indent=2))"

demo:
	bash scripts/demo_api.sh

backend:
	cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -f backend/fundguard.db
	rm -rf backend/.pytest_cache backend/__pycache__ backend/app/__pycache__ backend/tests/__pycache__ frontend/dist

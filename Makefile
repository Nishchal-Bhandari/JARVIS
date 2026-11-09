.PHONY: setup dev api web test lint seed
setup:
	python3 -m venv .venv || true
	.venv/bin/pip install -e backend[dev]
	cd frontend && npm ci
api:
	uvicorn app.main:app --reload --port 8000 --app-dir backend
web:
	cd frontend && npm run dev
dev:
	@echo "Run 'make api' and 'make web' in separate terminals"
test:
	python3 -m pytest backend/tests -q
	(cd frontend && npm run test -- --run)
lint:
	python3 -m ruff check backend && python3 -m ruff format --check backend || true
	(cd frontend && npm run lint && npm run typecheck)
seed:
	python3 scripts/seed.py

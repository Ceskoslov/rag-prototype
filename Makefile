.PHONY: up down build test seed evaluate logs clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

test:
	cd apps/backend && uv run pytest tests/ -v
	cd apps/frontend && npm test

seed:
	docker compose exec api python scripts/ingest.py --all --data-dir /data

evaluate:
	curl -X POST http://localhost:8000/api/v1/evaluation/trigger \
		-H "Content-Type: application/json" \
		-H "X-API-Key: your-secret-api-key-change-in-production" \
		-d '{"session_id": "demo-001"}'

logs:
	docker compose logs -f

clean:
	docker compose down -v
	rm -rf apps/backend/.pytest_cache apps/frontend/node_modules

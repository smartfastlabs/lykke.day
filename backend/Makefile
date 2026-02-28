.PHONY: serve serve-prod serve-http test typecheck check test-target docker-up docker-down docker-restart migrate-dev migrate-test migrate-prod migrate-create init-db migrate-data-to-prod docker-build export-openapi generate-types worker scheduler check-mappers fix worker-prod

COMPOSE_FILE := ../docker-compose.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)
API_SERVICE := api
DOCKER_RUN_API := $(COMPOSE) run --rm --no-deps $(API_SERVICE)
TEST_DATABASE_URL := postgresql+psycopg://lykke_test:password@postgres:5432/lykke_test
RESOLVE_PRODUCTION_DB_URL = if [ -n "$$PRODUCTION_MIGRATION_DB_URL" ]; then DATABASE_URL="$$PRODUCTION_MIGRATION_DB_URL"; elif [ -f .env.prod ] && grep -q '^PRODUCTION_MIGRATION_DB_URL=' .env.prod; then DATABASE_URL=$$(grep '^PRODUCTION_MIGRATION_DB_URL=' .env.prod | cut -d'=' -f2-); else echo "Error: PRODUCTION_MIGRATION_DB_URL not set and not found in .env.prod"; exit 1; fi;

# Docker management
docker-up:
	@$(COMPOSE) up -d postgres redis

docker-down:
	@$(COMPOSE) down

docker-restart: docker-down docker-up

docker-build:
	@$(COMPOSE) build api worker scheduler

init-db: docker-up
	@echo "Postgres initialization runs from backend/docker/init-db.sh on first startup."
	@echo "If the postgres volume already exists, recreate it to rerun init scripts."

# Application targets (Docker-first local development)
serve:
	@$(COMPOSE) up --build api worker scheduler

serve-http:
	@$(COMPOSE) up --build api

worker:
	@$(COMPOSE) up --build worker

scheduler:
	@$(COMPOSE) up --build scheduler

# Database migrations
migrate-dev: docker-up
	@$(DOCKER_RUN_API) poetry run alembic upgrade head

migrate-test: docker-up
	@$(COMPOSE) run --rm --no-deps -e DATABASE_URL=$(TEST_DATABASE_URL) $(API_SERVICE) poetry run alembic upgrade head

migrate-create: docker-up
	@if [ -z "$(MSG)" ]; then \
		echo "Usage: make migrate-create MSG='your migration message'"; \
		exit 1; \
	fi
	@$(DOCKER_RUN_API) poetry run alembic revision --autogenerate -m "$(MSG)"

migrate-prod: docker-build
	@bash -c '$(RESOLVE_PRODUCTION_DB_URL) $(COMPOSE) run --rm --no-deps -e DATABASE_URL=$$DATABASE_URL $(API_SERVICE) poetry run alembic upgrade head'

serve-prod: docker-up
	@echo "Starting FastAPI server against production DB..."
	@bash -c ' \
		$(RESOLVE_PRODUCTION_DB_URL) \
		$(COMPOSE) run --rm --service-ports --no-deps -e DATABASE_URL=$$DATABASE_URL -e REDIS_URL=redis://redis:6379 $(API_SERVICE) poetry run uvicorn lykke.app:app --host 0.0.0.0 --port 8080 --reload'

worker-prod: docker-up
	@echo "Starting Taskiq worker (and scheduler) against production DB..."
	@bash -c ' \
		$(RESOLVE_PRODUCTION_DB_URL) \
		$(COMPOSE) run --rm --no-deps -e DATABASE_URL=$$DATABASE_URL -e REDIS_URL=redis://redis:6379 $(API_SERVICE) bash -c "poetry run taskiq scheduler lykke.presentation.workers.tasks:scheduler & SCHEDULER_PID=\$$!; trap \"kill \$$SCHEDULER_PID 2>/dev/null; exit\" EXIT INT TERM; poetry run taskiq worker lykke.infrastructure.workers.config:broker"'

# Quality and tests
test: docker-up
	@$(COMPOSE) run --rm --no-deps -e DATABASE_URL=$(TEST_DATABASE_URL) -e ENV_FILE=.env.test $(API_SERVICE) poetry run pytest tests --vcr-record=once

test-target: docker-up
	@$(COMPOSE) run --rm --no-deps -e DATABASE_URL=$(TEST_DATABASE_URL) -e ENV_FILE=.env.test $(API_SERVICE) poetry run pytest $(if $(findstring /,$(TARGET)),$(TARGET),tests -k '$(TARGET)') --vcr-record=once -vv -s

typecheck:
	@$(DOCKER_RUN_API) poetry run mypy lykke

check-mappers:
	@$(DOCKER_RUN_API) poetry run python scripts/check_mappers.py

fix:
	@$(DOCKER_RUN_API) poetry run ruff check --fix lykke
	@$(DOCKER_RUN_API) poetry run black lykke

check:
	@$(MAKE) typecheck
	@$(MAKE) test

# Type generation
export-openapi:
	@$(DOCKER_RUN_API) poetry run python scripts/export_openapi_schema.py

generate-types: export-openapi
	@$(DOCKER_RUN_API) poetry run python scripts/generate_ts_types.py

# Data migration
migrate-data-to-prod: docker-build
	@if [ -z "$$DEST_DATABASE_URL" ]; then \
		$(RESOLVE_PRODUCTION_DB_URL) \
		$(COMPOSE) run --rm --no-deps -e DEST_DATABASE_URL=$$DATABASE_URL $(API_SERVICE) poetry run python scripts/migrate_data_to_production.py $(ARGS); \
	else \
		$(COMPOSE) run --rm --no-deps -e DEST_DATABASE_URL=$$DEST_DATABASE_URL $(API_SERVICE) poetry run python scripts/migrate_data_to_production.py $(ARGS); \
	fi
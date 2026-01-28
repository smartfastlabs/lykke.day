.PHONY: serve serve-prod serve-http test typecheck check test-target docker-up docker-down docker-restart migrate-dev migrate-test migrate-prod migrate-create init-db migrate-data-to-prod docker-build export-openapi generate-types migrate-data-to-prod worker scheduler check-mappers fix

# Docker management
docker-up:
	@cd .. && docker-compose up -d
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 2
	@cd .. && docker-compose exec -T postgres pg_isready -U lykke || (echo "Waiting a bit more..." && sleep 3)
	@echo "PostgreSQL is ready!"

# Initialize databases and users (idempotent)
init-db:
	@echo "Ensuring databases and users exist..."
	@cd .. && docker-compose exec -T postgres psql -U lykke -d lykke_dev -c "CREATE USER lykke_test WITH PASSWORD 'password';" 2>&1 | grep -v "already exists" || true
	@cd .. && docker-compose exec -T postgres psql -U lykke -d lykke_dev -c "CREATE DATABASE lykke_test OWNER lykke_test;" 2>&1 | grep -v "already exists" || true
	@cd .. && docker-compose exec -T postgres psql -U lykke -d lykke_dev -c "GRANT ALL PRIVILEGES ON DATABASE lykke_test TO lykke_test;" 2>&1 | grep -v -E "(ERROR|already granted)" || true
	@cd .. && docker-compose exec -T postgres psql -U lykke -d lykke_test -c "GRANT ALL ON SCHEMA public TO lykke_test;" 2>&1 | grep -v -E "(ERROR|already granted)" || true
	@cd .. && docker-compose exec -T postgres psql -U lykke -d lykke_dev -c "GRANT ALL ON SCHEMA public TO lykke;" 2>&1 | grep -v -E "(ERROR|already granted)" || true
	@echo "Databases and users initialized!"


docker-down:
	@cd .. && docker-compose down

docker-restart: docker-down docker-up

# Build Docker image
docker-build:
	docker build -t lykke .

# Database migrations
migrate-dev: docker-up
	DATABASE_URL=postgresql+psycopg://lykke:password@localhost:5432/lykke_dev poetry run alembic upgrade head

migrate-test: docker-up
	DATABASE_URL=postgresql+psycopg://lykke_test:password@localhost:5432/lykke_test poetry run alembic upgrade head

migrate-prod: docker-build
	@if [ -z "$$PRODUCTION_MIGRATION_DB_URL" ]; then \
		if [ -f .env.prod ] && grep -q '^PRODUCTION_MIGRATION_DB_URL=' .env.prod; then \
			DB_URL=$$(grep '^PRODUCTION_MIGRATION_DB_URL=' .env.prod | cut -d'=' -f2-); \
			docker run --rm -it \
				-v $(CURDIR):/app \
				-w /app \
				-e DATABASE_URL=$$DB_URL \
				lykke \
				poetry run alembic upgrade head; \
		else \
			echo "Error: PRODUCTION_MIGRATION_DB_URL not set and not found in .env.prod"; \
			exit 1; \
		fi \
	else \
		docker run --rm -it \
			-v $(CURDIR):/app \
			-w /app \
			-e DATABASE_URL=$$PRODUCTION_MIGRATION_DB_URL \
			lykke \
			poetry run alembic upgrade head; \
	fi

migrate-create: docker-up
	@if [ -z "$(MSG)" ]; then \
		echo "Usage: make migrate-create MSG='your migration message'"; \
		exit 1; \
	fi
	DATABASE_URL=postgresql+psycopg://lykke:password@localhost:5432/lykke_dev poetry run alembic revision --autogenerate -m "$(MSG)"

# Application targets
serve: docker-up
	@echo "Starting FastAPI server, scheduler, and worker..."
	@bash -c ' \
		export REDIS_URL=redis://localhost:6379; \
		export DATABASE_URL=postgresql+psycopg://lykke:password@localhost:5432/lykke_dev; \
		poetry run taskiq scheduler lykke.presentation.workers.tasks:scheduler & \
		SCHEDULER_PID=$$!; \
		poetry run taskiq worker lykke.infrastructure.workers.config:broker & \
		WORKER_PID=$$!; \
		trap "kill $$SCHEDULER_PID $$WORKER_PID 2>/dev/null; exit" EXIT INT TERM; \
		poetry run uvicorn lykke.app:app --host 0.0.0.0 --port 8080 --reload; \
		kill $$SCHEDULER_PID $$WORKER_PID 2>/dev/null || true'

serve-prod: docker-up
	@echo "Starting FastAPI server, scheduler, and worker against production DB..."
	@bash -c ' \
		if [ -z "$$PRODUCTION_MIGRATION_DB_URL" ]; then \
			if [ -f .env.prod ] && grep -q "^PRODUCTION_MIGRATION_DB_URL=" .env.prod; then \
				DATABASE_URL=$$(grep "^PRODUCTION_MIGRATION_DB_URL=" .env.prod | cut -d"=" -f2-); \
			else \
				echo "Error: PRODUCTION_MIGRATION_DB_URL not set and .env.prod missing"; \
				exit 1; \
			fi; \
		else \
			DATABASE_URL=$$PRODUCTION_MIGRATION_DB_URL; \
		fi; \
		export REDIS_URL=redis://localhost:6379; \
		export DATABASE_URL=$$DATABASE_URL; \
		poetry run taskiq scheduler lykke.presentation.workers.tasks:scheduler & \
		SCHEDULER_PID=$$!; \
		poetry run taskiq worker lykke.infrastructure.workers.config:broker & \
		WORKER_PID=$$!; \
		trap "kill $$SCHEDULER_PID $$WORKER_PID 2>/dev/null; exit" EXIT INT TERM; \
		poetry run uvicorn lykke.app:app --host 0.0.0.0 --port 8080 --reload; \
		kill $$SCHEDULER_PID $$WORKER_PID 2>/dev/null || true'

serve-http: docker-up
	DATABASE_URL=postgresql+psycopg://lykke:password@localhost:5432/lykke_dev poetry run uvicorn lykke.app:app --host 0.0.0.0 --port 8080 --reload

worker: docker-up
	REDIS_URL=redis://localhost:6379 DATABASE_URL=postgresql+psycopg://lykke:password@localhost:5432/lykke_dev poetry run taskiq worker lykke.infrastructure.workers.config:broker

scheduler: docker-up
	REDIS_URL=redis://localhost:6379 DATABASE_URL=postgresql+psycopg://lykke:password@localhost:5432/lykke_dev poetry run taskiq scheduler lykke.presentation.workers.tasks:scheduler

test: 
	DATABASE_URL=postgresql+psycopg://lykke_test:password@localhost:5432/lykke_test ENV_FILE=.env.test poetry run pytest tests --vcr-record=once

typecheck:
	poetry run mypy lykke

check-mappers:
	poetry run python scripts/check_mappers.py

fix:
	poetry run ruff check --fix lykke
	poetry run black lykke

check:
	make typecheck
	make test

test-target: docker-up
	DATABASE_URL=postgresql+psycopg://lykke_test:password@localhost:5432/lykke_test ENV_FILE=.env.test poetry run pytest $(if $(findstring /,$(TARGET)),$(TARGET),tests -k '$(TARGET)') --vcr-record=once -vv -s

# Type generation
export-openapi:
	poetry run python scripts/export_openapi_schema.py

generate-types: export-openapi
	poetry run python scripts/generate_ts_types.py

# Data migration
migrate-data-to-prod: docker-build
	@if [ -z "$$DEST_DATABASE_URL" ]; then \
		if [ -f .env.prod ] && grep -q '^PRODUCTION_MIGRATION_DB_URL=' .env.prod; then \
			DEST_DATABASE_URL=$$(grep '^PRODUCTION_MIGRATION_DB_URL=' .env.prod | cut -d'=' -f2-); \
			docker run --rm -it \
				-v $(CURDIR):/app \
				-w /app \
				-e DEST_DATABASE_URL=$$DEST_DATABASE_URL \
				lykke \
				poetry run python scripts/migrate_data_to_production.py $(ARGS); \
		else \
			echo "Error: DEST_DATABASE_URL not set and PRODUCTION_MIGRATION_DB_URL not found in .env.prod"; \
			exit 1; \
		fi \
	else \
		docker run --rm -it \
			-v $(CURDIR):/app \
			-w /app \
			-e DEST_DATABASE_URL=$$DEST_DATABASE_URL \
			lykke \
			poetry run python scripts/migrate_data_to_production.py $(ARGS); \
	fi
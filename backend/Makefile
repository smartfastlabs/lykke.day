.PHONY: serve test typecheck check test-target docker-up docker-down docker-restart migrate-dev migrate-test migrate-prod migrate-create init-db migrate-data-to-prod docker-build export-openapi generate-types migrate-data-to-prod

# Docker management
docker-up:
	@cd .. && docker-compose up -d
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 2
	@cd .. && docker-compose exec -T postgres pg_isready -U planned || (echo "Waiting a bit more..." && sleep 3)
	@echo "PostgreSQL is ready!"

# Initialize databases and users (idempotent)
init-db:
	@echo "Ensuring databases and users exist..."
	@cd .. && docker-compose exec -T postgres psql -U planned -d planned_dev -c "CREATE USER planned_test WITH PASSWORD 'password';" 2>&1 | grep -v "already exists" || true
	@cd .. && docker-compose exec -T postgres psql -U planned -d planned_dev -c "CREATE DATABASE planned_test OWNER planned_test;" 2>&1 | grep -v "already exists" || true
	@cd .. && docker-compose exec -T postgres psql -U planned -d planned_dev -c "GRANT ALL PRIVILEGES ON DATABASE planned_test TO planned_test;" 2>&1 | grep -v -E "(ERROR|already granted)" || true
	@cd .. && docker-compose exec -T postgres psql -U planned -d planned_test -c "GRANT ALL ON SCHEMA public TO planned_test;" 2>&1 | grep -v -E "(ERROR|already granted)" || true
	@cd .. && docker-compose exec -T postgres psql -U planned -d planned_dev -c "GRANT ALL ON SCHEMA public TO planned;" 2>&1 | grep -v -E "(ERROR|already granted)" || true
	@echo "Databases and users initialized!"

docker-down:
	@cd .. && docker-compose down

docker-restart: docker-down docker-up

# Build Docker image
docker-build:
	docker build -t planned .

# Database migrations
migrate-dev: docker-up docker-build
	docker run --rm -it \
		--network plannedday_default \
		-v $(CURDIR):/app \
		-w /app \
		-e DATABASE_URL=postgresql+psycopg://planned:password@postgres:5432/planned_dev \
		planned \
		poetry run alembic upgrade head

migrate-test: docker-up docker-build
	docker run --rm -it \
		--network plannedday_default \
		-v $(CURDIR):/app \
		-w /app \
		-e DATABASE_URL=postgresql+psycopg://planned_test:password@postgres:5432/planned_test \
		planned \
		poetry run alembic upgrade head

migrate-prod: docker-build
	@if [ -z "$$PRODUCTION_MIGRATION_DB_URL" ]; then \
		if [ -f .env.prod ] && grep -q '^PRODUCTION_MIGRATION_DB_URL=' .env.prod; then \
			DB_URL=$$(grep '^PRODUCTION_MIGRATION_DB_URL=' .env.prod | cut -d'=' -f2-); \
			docker run --rm -it \
				-v $(CURDIR):/app \
				-w /app \
				-e DATABASE_URL=$$DB_URL \
				planned \
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
			planned \
			poetry run alembic upgrade head; \
	fi

migrate-create: docker-up docker-build
	@if [ -z "$(MSG)" ]; then \
		echo "Usage: make migrate-create MSG='your migration message'"; \
		exit 1; \
	fi
	docker run --rm -it \
		--network plannedday_default \
		-v $(CURDIR):/app \
		-w /app \
		-e DATABASE_URL=postgresql+psycopg://planned:password@postgres:5432/planned_dev \
		planned \
		poetry run alembic revision --autogenerate -m "$(MSG)"

# Application targets
serve: docker-up
	DATABASE_URL=postgresql+psycopg://planned:password@localhost:5432/planned_dev poetry run uvicorn planned.app:app --host 0.0.0.0 --port 8080 --reload

worker: docker-up
	REDIS_URL=redis://localhost:6379 DATABASE_URL=postgresql+psycopg://planned:password@localhost:5432/planned_dev poetry run taskiq worker planned.infrastructure.workers.config.broker

test: docker-up docker-build
	docker run --rm -it \
		--network plannedday_default \
		-v $(CURDIR):/app \
		-w /app \
		-e DATABASE_URL=postgresql+psycopg://planned_test:password@postgres:5432/planned_test \
		-e ENV_FILE=.env.test \
		planned \
		poetry run pytest tests --vcr-record=once

typecheck: docker-build
	docker run --rm -it \
		-v $(CURDIR):/app \
		-w /app \
		planned \
		poetry run mypy planned

check:
	make typecheck
	make test

test-target: docker-up docker-build
	docker run --rm -it \
		--network plannedday_default \
		-v $(CURDIR):/app \
		-w /app \
		-e DATABASE_URL=postgresql+psycopg://planned_test:password@postgres:5432/planned_test \
		-e ENV_FILE=.env.test \
		planned \
		poetry run pytest $(if $(findstring /,$(TARGET)),$(TARGET),tests -k '$(TARGET)') --vcr-record=once -vv -s

# Type generation
export-openapi: docker-build
	docker run --rm -it \
		-v $(CURDIR):/app \
		-w /app \
		planned \
		poetry run python scripts/export_openapi_schema.py

generate-types: export-openapi docker-build
	docker run --rm -it \
		-v $(CURDIR):/app \
		-w /app \
		planned \
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
				planned \
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
			planned \
			poetry run python scripts/migrate_data_to_production.py $(ARGS); \
	fi
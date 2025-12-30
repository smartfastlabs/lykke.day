.PHONY: serve test typecheck check test-target docker-up docker-down docker-restart migrate-dev migrate-test migrate-create init-db

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

# Database migrations
migrate-dev:
	DATABASE_URL=postgresql+psycopg://planned:password@localhost:5432/planned_dev poetry run alembic upgrade head

migrate-test:
	DATABASE_URL=postgresql+psycopg://planned_test:password@localhost:5432/planned_test poetry run alembic upgrade head

migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Usage: make migrate-create MSG='your migration message'"; \
		exit 1; \
	fi
	DATABASE_URL=postgresql+psycopg://planned:password@localhost:5432/planned_dev poetry run alembic revision --autogenerate -m "$(MSG)"

# Application targets
serve: docker-up
	DATABASE_URL=postgresql+psycopg://planned:password@localhost:5432/planned_dev poetry run uvicorn planned.app:app --host 0.0.0.0 --port 8080 --reload

test: docker-up
	DATABASE_URL=postgresql+psycopg://planned_test:password@localhost:5432/planned_test ENV_FILE=.env.test poetry run pytest tests --vcr-record=once

typecheck:
	poetry run mypy planned

check:
	make typecheck
	make test

test-target: docker-up
	DATABASE_URL=postgresql+psycopg://planned_test:password@localhost:5432/planned_test \
	ENV_FILE=.env.test \
	poetry run pytest $(if $(findstring /,$(TARGET)),$(TARGET),tests -k '$(TARGET)') --vcr-record=once -vv -s
# ============================================
# Base stage - shared dependencies
# ============================================
FROM python:3.13-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-root

# Copy application code
COPY . .

# Install the application
RUN poetry install --no-interaction

# No CMD specified - command must be provided when running the container
# Example commands:
#   API:       poetry run uvicorn planned.app:app --host 0.0.0.0 --port 8080
#   Worker:    poetry run taskiq worker planned.infrastructure.workers.config:broker
#   Scheduler: poetry run taskiq scheduler planned.presentation.workers.tasks:scheduler

EXPOSE 8080

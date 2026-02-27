# lykke.day

![Tests](https://github.com/smartfastlabs/lykke.day/actions/workflows/ci.yml/badge.svg?branch=main)
[![codecov](https://codecov.io/github/smartfastlabs/lykke.day/graph/badge.svg?token=LKE5MI43G4)](https://codecov.io/github/smartfastlabs/lykke.day)

> **Work in progress / experiment**  
> This repository is actively changing and may break at any time.

## What Lykke Is About

Lykke is about intentional daily living: planning your day around what matters, following through with consistency, and reflecting without turning life into hustle metrics.

The project exists to support wellbeing-first productivity. The core idea is simple: a day should feel purposeful and sustainable, not overloaded.

## Architecture Overview

The backend follows Clean Architecture with CQRS. The codebase is organized into five layers with strict dependency flow:

- `core` - shared primitives, constants, config, and cross-cutting utilities
- `domain` - entities, value objects, domain services, and domain events
- `application` - commands, queries, protocols, and use-case orchestration
- `infrastructure` - database/repository/gateway implementations and workers
- `presentation` - FastAPI routes, request/response schemas, and API wiring

Dependency direction is inward: outer layers depend on inner layers, never the reverse.

## Experiment Focus

This repository is also intentionally centered on process:

- LLMs write essentially all production code in this repo.
- Humans set direction, constraints, and review.
- The goal is to learn what workflows, architecture, and guardrails make this approach reliable.

This means commits may be frequent, structure may shift, and rough edges are expected.

## Current Status

- Not stable
- Not production-ready
- No compatibility guarantees between commits

If you are reading this, treat the project as a live lab notebook rather than a finished product.

## Cursor Quick Links

### Important Commands

- [Add Feature](.cursor/commands/add-feature.md)
- [Run Tests](.cursor/commands/run-tests.md)
- [Run Typecheck](.cursor/commands/run-typecheck.md)
- [Commit Message](.cursor/commands/commit-message.md)

### Important Rules

- [Backend Architecture](.cursor/rules/backend-architecture.mdc)
- [Python Help](.cursor/rules/python-help.mdc)
- [Events and Audit Logs](.cursor/rules/events-and-audit-logs.mdc)
- [Domain](.cursor/rules/domain.mdc)
- [Application](.cursor/rules/application.mdc)
- [Infrastructure](.cursor/rules/infrastructure.mdc)
- [Presentation](.cursor/rules/presentation.mdc)
- [Core](.cursor/rules/core.mdc)

## Local Development

### Prerequisites

- Docker
- Python 3.12+ with Poetry
- Node.js 18+ with npm

### Setup

```bash
git clone https://github.com/smartfastlabs/lykke.day.git
cd lykke.day

# Backend
cd backend
poetry install
make docker-up
make init-db
make migrate-dev
make serve

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Common Commands

```bash
# backend/
make test
make typecheck
make check

# frontend/
npm run test
npm run type-check
npm run lint
```

## Contributing

Contributions are welcome, especially if you are interested in AI-assisted development practices.

Before opening a PR:

1. Run checks (`make check` in `backend/`, tests/lint in `frontend/`)
2. Keep changes small and explicit
3. Add or update tests when behavior changes
4. Document any prompt, workflow, or guardrail improvements

## License

GNU Affero General Public License v3.0 (AGPLv3) - see `LICENSE`.

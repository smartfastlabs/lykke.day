# lykke.day

![Tests](https://github.com/smartfastlabs/lykke.day/actions/workflows/ci.yml/badge.svg?branch=main)
[![codecov](https://codecov.io/github/smartfastlabs/lykke.day/graph/badge.svg?token=LKE5MI43G4)](https://codecov.io/github/smartfastlabs/lykke.day)

> **Pre-alpha software** — Expect breaking changes and incomplete features.

A daily we application built with Clean Architecture and Domain-Driven Design. Try it at [lykke.day](https://lykke.day).

## Architecture

The backend follows a strict **Clean Architecture** with **CQRS**; the codebase is organized into five layers with explicit dependency rules:

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│  FastAPI routers, API schemas, request/response handling        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  Commands, Queries, Repository & Gateway protocols              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                               │
│  Entities, Value Objects, Domain Events, Domain Services        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                          │
│  Repository implementations, Gateway implementations, Database  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       CORE LAYER                                │
│  Configuration, constants, exceptions, shared utilities         │
└─────────────────────────────────────────────────────────────────┘
```

**Layer dependency rules:**

| Layer          | Can Import From                           |
|----------------|-------------------------------------------|
| Domain         | Core only                                 |
| Application    | Domain, Core                              |
| Infrastructure | Application, Domain, Core                 |
| Presentation   | Application, Domain, Infrastructure, Core |
| Core           | Nothing                                   |

## Business Domains

### Day (Aggregate Root)

The central domain entity. A `Day` represents a single day's schedule for a user with:
- **Status lifecycle**: `UNSCHEDULED` → `SCHEDULED` → `COMPLETE`
- **Time blocks**: Scheduled periods derived from templates
- **Goals**: Up to 3 active goals per day
- **Tasks**: Scheduled via routines or ad-hoc

### Routine

Reusable task collections with scheduling rules:
- **Category**: Wellness, work, personal, etc.
- **Schedule**: Days of week, frequency patterns
- **Tasks**: Attached `RoutineTask` items with individual schedules

### Task

Individual work items with:
- **Status**: `PENDING` → `READY` → `COMPLETE` | `PUNT`
- **Actions**: Immutable action log (complete, punt, notify)
- **Scheduling**: Time-based or triggered by routine

### Calendar

External calendar integration:
- **Subscriptions**: Google Calendar sync
- **Entry Series**: Recurring event patterns
- **Entries**: Individual calendar events

### Day Template

Predefined day structures:
- **Time blocks**: Named periods (Morning Routine, Focus Time, etc.)
- **Routines**: Associated routine assignments
- **Reusable**: Applied when scheduling days

## Project Structure

```
lykke.day/
├── backend/
│   ├── lykke/
│   │   ├── domain/           # Business logic
│   │   │   ├── entities/     # Aggregate roots & entities
│   │   │   ├── value_objects/# Immutable value types
│   │   │   └── events/       # Domain events
│   │   ├── application/      # Use cases
│   │   │   ├── commands/     # Write operations (CQRS)
│   │   │   ├── queries/      # Read operations (CQRS)
│   │   │   ├── repositories/ # Repository protocols
│   │   │   └── gateways/     # External service protocols
│   │   ├── infrastructure/   # Implementations
│   │   │   ├── repositories/ # SQLAlchemy implementations
│   │   │   ├── gateways/     # External API clients
│   │   │   └── database/     # Table definitions
│   │   ├── presentation/     # HTTP API
│   │   │   └── api/
│   │   │       ├── routers/  # FastAPI routes
│   │   │       └── schemas/  # Request/response models
│   │   └── core/             # Shared utilities
│   ├── alembic/              # Database migrations
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
│
├── frontend/                 # SolidJS web application
│   └── src/
│       ├── pages/
│       └── components/
│
└── docker-compose.yml
```

## Tech Stack

**Backend:**
- Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL, Redis
- Poetry for dependency management
- Strict mypy type checking

**Frontend:**
- SolidJS, TypeScript, Vite, TailwindCSS

## Getting Started

### Prerequisites

- Docker (PostgreSQL, Redis)
- Python 3.12+ with Poetry
- Node.js 18+ with npm

### Setup

```bash
git clone https://github.com/smartfastlabs/lykke.day.git
cd lykke.day

# Backend
cd backend
poetry install
make docker-up      # Start PostgreSQL and Redis
make init-db        # Initialize databases
make migrate-dev    # Run migrations
make serve          # Start API server

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

API: `http://localhost:8080` | Frontend: `http://localhost:5173`

### Configuration

Create `backend/.env`:

```bash
DATABASE_URL=postgresql+psycopg://lykke:password@localhost:5432/lykke_dev
REDIS_URL=redis://localhost:6379
SECRET=your-secret-key-here
```

## Development

```bash
# Backend (from backend/)
make test                           # Run all tests
make test-target TARGET=test_name   # Run specific test
make typecheck                      # mypy type checking
make check-mappers                  # Verify mapper completeness
make check                          # typecheck + tests

# Frontend (from frontend/)
npm run test
npm run type-check
npm run lint
```

## AI-Assisted Development

This project uses LLMs for ~90% of implementation. The DDD architecture was chosen specifically to work well with AI assistance:
- Clear layer boundaries reduce context needed
- Explicit protocols make contracts unambiguous
- Event-driven patterns enable isolated changes

## Contributing

Contributions welcome. Before submitting:

1. Run `make check` (typecheck + tests)
2. Respect layer boundaries
3. Add tests for new functionality
4. Use domain events for side effects

## License

GNU Affero General Public License v3.0 (AGPLv3) — See [LICENSE](LICENSE).
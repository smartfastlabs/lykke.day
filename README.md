# lykke.day

![Tests](https://github.com/smartfastlabs/lykke.day/actions/workflows/ci.yml/badge.svg?branch=main)
[![codecov](https://codecov.io/github/smartfastlabs/lykke.day/graph/badge.svg?token=LKE5MI43G4)](https://codecov.io/github/smartfastlabs/lykke.day)

> **Pre-alpha software** — Expect breaking changes and incomplete features.

A daily wellness companion built with Clean Architecture and Domain-Driven Design. Try it at [lykke.day](https://lykke.day).

_Lykke_ (Danish for "happiness") reflects our belief that sustainable productivity emerges from intentional living, not hustle culture. This is open-source software you can trust with your most personal data—your daily habits, thoughts, and goals.

## Why Lykke?

Modern productivity tools often optimize for output at the expense of wellbeing. Lykke takes a different approach:

- **Your data, your control** — Self-hostable, open source, no vendor lock-in
- **Privacy by design** — No analytics, no tracking, no data harvesting
- **Sustainable habits** — Focus on consistency and wellbeing over raw productivity
- **Community-driven** — Built in the open, shaped by user needs

## Overview

Lykke helps users build consistent daily habits through structured routines and mindful task management. The core workflow:

1. **Define routines** — Create reusable collections of tasks (morning routine, exercise, work blocks)
2. **Schedule your day** — Apply a template to generate today's tasks
3. **Track progress** — Complete or punt tasks throughout the day
4. **Set daily reminders** — Focus on up to 3 meaningful objectives per day
5. **Receive smart notifications** — AI-assisted nudges via push notifications or SMS

The application syncs with Google Calendar to show external commitments alongside scheduled tasks, giving users a unified view of their day.

## Features

### Progressive Web App (PWA)

Lykke is delivered as a PWA, providing a native app experience without app store dependencies:

- **Installable** — Add to home screen on any device
- **Offline-capable** — Core functionality works without network [TODO :)]
- **Push notifications** — Real-time reminders and updates
- **Fast** — Service worker caching for instant loads

### Multi-Channel Communications

Stay connected to your day through your preferred channel:

- **Push notifications** — Browser and mobile push via Web Push API
- **SMS messaging** — Text-based interactions via Twilio integration
- **Real-time updates** — WebSocket-powered live sync across devices

### Brain Dump

Capture thoughts the moment they arise without breaking your flow. Brain Dump is a frictionless inbox for ideas, reminders, and mental clutter:

- **Quick capture** — Instantly jot down thoughts tied to today's context
- **Voice dictation** — Speak your thoughts using the browser's Web Speech API
- **Status tracking** — Mark items complete or punt them forward
- **LLM context** — Brain dump items inform smart notifications, so the AI understands what's on your mind

Brain Dump reduces cognitive load by giving fleeting thoughts a place to live. Review them during planning, convert important ones to tasks, or simply let them go.

### LLM Integration (Early Stage)

Lykke is beginning to integrate large language models to provide intelligent assistance. This is foundational work—expect the capabilities to grow significantly.

**Current capabilities:**

- **Smart notifications** — LLM-powered contextual nudges that understand your day's progress, upcoming tasks, and reminders to send timely, relevant push notifications
- **Pluggable providers** — Support for OpenAI and Anthropic APIs (bring your own key)

**Architecture:**

- **UseCases** — Modular LLM use cases in `application/llm_usecases/` define specific AI-assisted behaviors
- **Jinja2 templates** — Prompts are templated for consistency and customization
- **Context injection** — Day state, tasks, reminders, and calendar events provide grounded context

This is just the beginning. Future directions may include conversational interactions, intelligent scheduling suggestions, and reflection prompts—always with user agency and privacy at the center.

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
| -------------- | ----------------------------------------- |
| Domain         | Core only                                 |
| Application    | Domain, Core                              |
| Infrastructure | Application, Domain, Core                 |
| Presentation   | Application, Domain, Infrastructure, Core |
| Core           | Nothing                                   |

### Event System

Lykke uses a three-tier event architecture for decoupled, observable state changes:

**1. Domain Events** — In-memory events emitted by domain entities during business operations. Handlers run within the transaction boundary, enabling atomic cross-aggregate coordination.

```python
@dataclass(frozen=True, kw_only=True)
class TaskCompletedEvent(DomainEvent, AuditableDomainEvent):
    task_id: UUID
    completed_at: datetime
```

**2. Audit Logs** — Persistent records of user-visible activities. Events marked with `AuditableDomainEvent` automatically generate audit log entries stored in PostgreSQL and broadcast to connected clients.

**3. Real-time Notifications** — Domain events are published to Redis after commit, then forwarded to WebSocket clients for instant UI updates.

This architecture ensures:

- **Transactional consistency** — Handlers run before commit, failures rollback
- **Observable state** — All significant changes are tracked
- **Real-time sync** — Clients stay in sync without polling
- **Audit trail** — User activity history for transparency

### Background Jobs with Taskiq

Lykke uses [Taskiq](https://taskiq-python.github.io/) for distributed background processing:

**Why Taskiq:**

- Native async/await support
- Redis-backed queue for reliability
- Cron-like scheduling via labels
- Dependency injection for clean handler composition

```python
@broker.task(schedule=[{"cron": "0 3 * * *"}])
async def schedule_all_users_day_task():
    """Generate today's schedule for all users."""
    ...
```

## Business Domains

### Day (Aggregate Root)

The central domain entity. A `Day` represents a single day's schedule for a user with:

- **Status lifecycle**: `UNSCHEDULED` → `SCHEDULED` → `COMPLETE`
- **Time blocks**: Scheduled periods derived from templates
- **Reminders**: No active reminder limit per day
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

- **Subscriptions**: Google Calendar sync via webhooks
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
│   │   │   ├── gateways/     # External service protocols
│   │   │   ├── events/       # Domain event handlers
│   │   │   └── llm_usecases/ # LLM-powered use cases
│   │   ├── infrastructure/   # Implementations
│   │   │   ├── repositories/ # SQLAlchemy implementations
│   │   │   ├── gateways/     # External API clients (Twilio, LLM providers)
│   │   │   ├── database/     # Table definitions
│   │   │   └── workers/      # Taskiq configuration
│   │   ├── presentation/     # HTTP API
│   │   │   ├── api/
│   │   │   │   ├── routers/  # FastAPI routes
│   │   │   │   └── schemas/  # Request/response models
│   │   │   └── workers/      # Background task definitions
│   │   └── core/             # Shared utilities
│   ├── templates/            # Jinja2 templates for LLM prompts
│   ├── alembic/              # Database migrations
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
│
├── frontend/                 # SolidJS PWA
│   └── src/
│       ├── pages/
│       ├── components/
│       └── sw.ts             # Service worker
│
└── docker-compose.yml
```

## Tech Stack

**Backend:**

- Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL, Redis
- Taskiq for background job processing
- Poetry for dependency management
- Strict mypy type checking

**Frontend:**

- SolidJS, TypeScript, Vite, TailwindCSS
- Workbox for PWA/service worker
- Web Push API for notifications

**Integrations:**

- Google Calendar API
- Twilio (SMS)
- OpenAI / Anthropic (LLM)

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

### Running Background Workers

```bash
cd backend
poetry run taskiq worker lykke.infrastructure.workers.config:broker
```

For scheduled tasks (cron-like):

```bash
poetry run taskiq scheduler lykke.infrastructure.workers.config:scheduler
```

### Configuration

Create `backend/.env`:

```bash
DATABASE_URL=postgresql+psycopg://lykke:password@localhost:5432/lykke_dev
REDIS_URL=redis://localhost:6379
SECRET=your-secret-key-here

# Optional: LLM integration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: SMS notifications
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
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

## Philosophy

Lykke is built on principles that prioritize human flourishing:

**Trust through transparency** — Every line of code is open. No dark patterns, no hidden data collection, no algorithmic manipulation.

**Wellbeing over engagement** — We measure success by whether users feel better about their days, not by time-on-app metrics.

**Sustainable by design** — The AGPLv3 license ensures improvements benefit the community. Self-hosting keeps you in control.

**Community first** — Built for the people who use it, shaped by their needs, accountable to their values.

## Contributing

Contributions welcome. Before submitting:

1. Run `make check` (typecheck + tests)
2. Respect layer boundaries
3. Add tests for new functionality
4. Use domain events for side effects

See the architecture rules in `.cursor/rules/` for detailed guidance on each layer.

## Community

- [GitHub Issues](https://github.com/smartfastlabs/lykke.day/issues) — Bug reports and feature requests
- [Discussions](https://github.com/smartfastlabs/lykke.day/discussions) — Questions and ideas

## License

GNU Affero General Public License v3.0 (AGPLv3) — See [LICENSE](LICENSE).

This license ensures that if you run a modified version of Lykke as a network service, you must make your source code available to users. This keeps the community's improvements accessible to everyone.

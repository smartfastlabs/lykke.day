# Add Feature Workflow (Current Backend Architecture)

Use this command when adding or changing backend functionality in this repo.
This project uses Clean Architecture + CQRS:
- Commands handle writes (`lykke/application/commands/`)
- Queries handle reads (`lykke/application/queries/`)
- Routers stay thin (`lykke/presentation/api/routers/`)
- Persistence and external I/O live in infrastructure (`lykke/infrastructure/`)

## Operating Rules

1. Diagnose requirements and likely root cause first; do not jump to symptom-level patches.
2. If the change is large or cross-cutting, propose the plan and impact first, then wait for approval before broad edits.
3. Keep strict layer boundaries (domain/application do not depend on presentation).
4. Use async end-to-end for I/O paths (routers, handlers, repositories, gateways, unit of work).

---

## Phase 1: Clarify Scope and Risk

Before coding, confirm:
- Problem statement and user-visible behavior
- Read path(s) and write path(s) affected
- Whether this is a small local change or a multi-layer refactor

If large refactor or many files/layers are needed:
- Provide a concise plan (files, sequence, risks, test strategy)
- 🛑 **CHECKPOINT: Wait for approval before broad implementation**

---

## Phase 2: Domain and Application Design

### Domain (`lykke/domain/`)
- Add/update entities in `entities/` if business state/rules change
- Add/update value objects in `value_objects/` for typed inputs/filters
- Add domain events in `events/` for meaningful business occurrences

### Application (`lykke/application/`)
- Add a **command** handler for writes
- Add a **query** handler for reads
- Add repository/gateway protocols only when needed

Command/query patterns:
- Base classes: `application/commands/base.py`, `application/queries/base.py`
- Handler construction and DI: `presentation/handler_factory.py`
- Unit of work/repo protocols: `application/unit_of_work.py`

Do not create generic service-layer methods as the primary orchestration pattern; prefer command/query handlers.

---

## Phase 3: Infrastructure Wiring

For persistence or external integrations:
- Implement repository protocol(s) in `lykke/infrastructure/repositories/`
- Add/adjust SQLAlchemy tables in `lykke/infrastructure/database/tables/` if schema changes
- Create Alembic migration in `backend/alembic/versions/` for DB changes
- Implement gateway protocols in `lykke/infrastructure/gateways/` when needed

Repository mapping requirements:
- Keep `entity_to_row()` and `row_to_entity()` mappings correct
- Run mapper validation checks (see verification phase)

If adding a new repository to read-only repos:
- Update `ReadOnlyRepositories` in `application/unit_of_work.py`
- Update `UnitOfWorkProtocol` if command/UoW access is needed
- Update infrastructure UoW/repository factories
- Update protocol doubles in `tests/support/dobles.py`

---

## Phase 4: API Endpoints and Schemas

For HTTP/WebSocket API changes:
- Add/update route in `lykke/presentation/api/routers/`
- Add/update request/response schema in `lykke/presentation/api/schemas/`
- Map entities to response schemas via `presentation/api/schemas/mappers.py`
- Use DI factories from `presentation/api/routers/dependencies/factories.py`

Endpoint pattern:
- Inject `CommandHandlerFactory` / `QueryHandlerFactory` via `Depends(...)`
- `factory.create(YourHandler)` per request
- Convert schema payloads into domain value objects/command inputs
- Return mapped schema objects (never raw entities)

Auth/user context:
- HTTP uses `get_current_user`
- WebSocket uses `get_current_user_from_token`

---

## Phase 5: Async, Events, and Side Effects

### Async Requirements
- Route handlers are `async def`
- Command/query handlers are `async def handle(...)`
- Repository and gateway I/O is async
- Use async context managers for UoW paths

### Event Flow Requirements
- Domain events are dispatched before commit in UoW flow
- After successful commit, events/changes are broadcast to Redis streams/channels
- Use event and entity-change stream model for sync behavior

Do not reintroduce removed audit-log architecture primitives (`AuditLogEntity`, `audit_logs`, `AuditLogRepository*`, `AuditableDomainEvent`, audit-log queries).

---

## Phase 6: Verification and Tests

Add/adjust tests at the correct level:
- Unit tests: `backend/tests/unit/`
- Integration tests: `backend/tests/integration/`
- E2E/router tests: `backend/tests/e2e/routers/`

Testing conventions:
- Mark async tests with `@pytest.mark.asyncio`
- Use `dobles` for protocol doubles

Run checks from `backend/`:
- `make test`
- `make typecheck`
- `make check-mappers`
- `make check` when finishing broader changes

If failures appear, identify and fix root causes (not superficial patches).

---

## Implementation Checklist

- [ ] Scope confirmed; root cause understood
- [ ] Plan approved first if change is large
- [ ] Domain entities/value objects/events updated as needed
- [ ] Command handler(s) for writes added/updated
- [ ] Query handler(s) for reads added/updated
- [ ] Repositories/gateways and infrastructure wiring updated
- [ ] Endpoints + schemas + mapper functions updated
- [ ] Async flow preserved across all I/O boundaries
- [ ] Event flow remains compatible with current Redis-based model
- [ ] Tests added/updated and all checks pass

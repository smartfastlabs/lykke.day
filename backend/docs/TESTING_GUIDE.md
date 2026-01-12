# Testing Guide for Lykke Backend

This guide explains how to write tests for the Lykke backend codebase, which uses Clean Architecture with CQRS (Command Query Responsibility Segregation).

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Types](#test-types)
3. [Testing Command Handlers](#testing-command-handlers)
4. [Testing Query Handlers](#testing-query-handlers)
5. [Testing Domain Entities](#testing-domain-entities)
6. [Testing Repositories](#testing-repositories)
7. [Test Fixtures and Helpers](#test-fixtures-and-helpers)
8. [Running Tests](#running-tests)
9. [Best Practices](#best-practices)

---

## Testing Philosophy

Our testing strategy follows the **Testing Pyramid**:

```
        ╱ ╲
       ╱ E2E╲         - Test full API flows
      ╱──────╲        - Use real HTTP requests
     ╱  Integ╲        - Test with real database
    ╱─────────╲       - Verify data persistence
   ╱    Unit   ╲      - Test business logic in isolation
  ╱_____________╲     - Mock all dependencies
```

**Key Principles:**

1. **Write tests BEFORE production code** (TDD when possible)
2. **Unit tests are REQUIRED for all command handlers** (this is where bugs hide!)
3. **Test behavior, not implementation details**
4. **Each test should test ONE thing**
5. **Tests should be independent** (no shared state)

---

## Test Types

### Unit Tests (`tests/unit/`)

**Purpose:** Test business logic in isolation

**Characteristics:**
- Mock ALL dependencies using fake classes
- Fast execution (no I/O)
- Test domain logic and orchestration

**When to use:**
- Command handlers ✅ **CRITICAL**
- Query handlers ✅ **CRITICAL**
- Domain entities (business rules)
- Domain services
- Value objects

**Example:**
```python
# tests/unit/application/commands/test_my_command.py
@pytest.mark.asyncio
async def test_my_command_adds_entity_to_uow():
    # Arrange: Create fakes
    # Act: Execute command
    # Assert: Verify UoW received entity
```

### Integration Tests (`tests/integration/`)

**Purpose:** Test with real infrastructure (database, external APIs)

**Characteristics:**
- Real database connection
- Test repository implementations
- Verify data persistence
- Test transactions and rollbacks

**When to use:**
- Repository implementations
- Database queries
- Transaction handling
- External gateway integrations

**Example:**
```python
# tests/integration/repositories/test_task_repository.py
@pytest.mark.asyncio
async def test_task_repository_persists_data(test_database):
    # Uses real PostgreSQL database
```

### E2E Tests (`tests/e2e/`)

**Purpose:** Test full application flows via HTTP API

**Characteristics:**
- Real HTTP requests to FastAPI
- Test authentication/authorization
- Verify API contracts
- Test error responses

**When to use:**
- API endpoint validation
- Multi-step workflows
- Authorization checks
- Response format validation

**Example:**
```python
# tests/e2e/routers/test_tasks.py
async def test_complete_task_endpoint(authenticated_client):
    response = await authenticated_client.post(f"/tasks/{task_id}/complete")
    assert response.status_code == 200
```

---

## Testing Command Handlers

**⚠️ CRITICAL:** Commands handle ALL data mutations. Untested commands = production bugs.

### What to Test

For EVERY command handler, test:

1. ✅ Entity is added to UoW (via `uow.add()` or `uow.create()`)
2. ✅ Domain events are raised
3. ✅ Business rules are enforced
4. ✅ Error cases are handled
5. ✅ Side effects occur correctly

### Example: Testing RecordTaskActionHandler

```python
"""Unit tests for RecordTaskActionHandler."""

from uuid import uuid4
from datetime import UTC, date as dt_date, datetime

import pytest

from lykke.application.commands.task import RecordTaskActionHandler
from lykke.domain import value_objects
from lykke.domain.entities import DayEntity, TaskEntity, DayTemplateEntity
from lykke.domain.events.task_events import TaskStateUpdatedEvent


# Fake implementations (lightweight mocks)
class _FakeTaskReadOnlyRepo:
    """Fake task repository for testing."""
    
    def __init__(self, task: TaskEntity) -> None:
        self._task = task
    
    async def get(self, task_id):
        if task_id == self._task.id:
            return self._task
        raise NotFoundError(f"Task {task_id} not found")


class _FakeDayReadOnlyRepo:
    """Fake day repository for testing."""
    
    def __init__(self, day: DayEntity) -> None:
        self._day = day
    
    async def get(self, day_id):
        if day_id == self._day.id:
            return self._day
        raise NotFoundError(f"Day {day_id} not found")


class _FakeReadOnlyRepos:
    """Container matching ReadOnlyRepositories protocol."""
    
    def __init__(self, task_repo, day_repo, day_template_repo, user_repo):
        # Assign real repos
        self.task_ro_repo = task_repo
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = day_template_repo
        self.user_ro_repo = user_repo
        
        # Stub out unused repos
        fake = object()
        self.auth_token_ro_repo = fake
        self.calendar_entry_ro_repo = fake
        # ... etc for all repos


class _FakeUoW:
    """Minimal UnitOfWork that collects added entities."""
    
    def __init__(self, task_repo, day_repo, day_template_repo, user_repo):
        self.added = []
        self.created = []
        # Provide repos for command to use
        self.task_ro_repo = task_repo
        self.day_ro_repo = day_repo
        self.day_template_ro_repo = day_template_repo
        self.user_ro_repo = user_repo
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        return None
    
    def add(self, entity):
        """Track entities added to UoW."""
        self.added.append(entity)
    
    async def create(self, entity):
        """Track entities created in UoW."""
        self.created.append(entity)
        entity.create()


class _FakeUoWFactory:
    def __init__(self, task_repo, day_repo, day_template_repo, user_repo):
        self.uow = _FakeUoW(task_repo, day_repo, day_template_repo, user_repo)
    
    def create(self, _user_id):
        return self.uow


@pytest.mark.asyncio
async def test_record_task_action_adds_task_and_day_to_uow():
    """Verify task and day are added to UoW after recording action."""
    # Arrange: Create test data
    user_id = uuid4()
    task_date = dt_date(2025, 11, 27)
    
    template = DayTemplateEntity(
        user_id=user_id,
        name="Default",
        slug="default",
        routines=[],
        time_blocks=[],
    )
    
    day = DayEntity.create_for_date(task_date, user_id, template)
    
    task = TaskEntity(
        id=uuid4(),
        user_id=user_id,
        scheduled_date=task_date,
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.TODO,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    
    # Setup fakes
    task_repo = _FakeTaskReadOnlyRepo(task)
    day_repo = _FakeDayReadOnlyRepo(day)
    day_template_repo = _FakeDayTemplateReadOnlyRepo(template)
    user_repo = _FakeUserReadOnlyRepo(create_test_user(user_id))
    
    ro_repos = _FakeReadOnlyRepos(task_repo, day_repo, day_template_repo, user_repo)
    uow_factory = _FakeUoWFactory(task_repo, day_repo, day_template_repo, user_repo)
    handler = RecordTaskActionHandler(ro_repos, uow_factory, user_id)
    
    # Create action
    action = value_objects.Action(
        type=value_objects.ActionType.COMPLETE,
        timestamp=datetime.now(UTC),
    )
    
    # Act: Execute command
    result = await handler.record_task_action(task.id, action)
    
    # Assert: Verify behavior
    assert result.status == value_objects.TaskStatus.COMPLETE
    assert len(result.actions) == 1
    
    # CRITICAL: Verify entities were added to UoW
    assert len(uow_factory.uow.added) == 2
    added_entities = uow_factory.uow.added
    assert any(isinstance(e, DayEntity) for e in added_entities)
    assert any(isinstance(e, TaskEntity) for e in added_entities)


@pytest.mark.asyncio
async def test_record_task_action_raises_domain_events():
    """Verify domain events are raised when recording action."""
    # ... setup ...
    
    # Act
    result = await handler.record_task_action(task.id, action)
    
    # Assert: Check domain events
    task_events = [e for e in result._domain_events 
                   if isinstance(e, TaskStateUpdatedEvent)]
    assert len(task_events) > 0


@pytest.mark.asyncio
async def test_record_task_action_creates_day_if_not_exists():
    """Verify day is created if it doesn't exist."""
    # ... setup with day_repo returning None ...
    
    # Act
    result = await handler.record_task_action(task.id, action)
    
    # Assert: Verify day was created
    assert len(uow_factory.uow.created) == 1
    created_day = uow_factory.uow.created[0]
    assert isinstance(created_day, DayEntity)
```

### Key Patterns

1. **Use Fake Classes, Not Mocks**
   - Lightweight, predictable
   - Easy to understand
   - No mock library magic

2. **Verify UoW Receives Entities**
   ```python
   assert len(uow_factory.uow.added) == 1
   assert uow_factory.uow.added[0] == expected_entity
   ```

3. **Test Error Cases**
   ```python
   with pytest.raises(DomainError, match="Task already complete"):
       await handler.complete_task(completed_task.id)
   ```

---

## Testing Query Handlers

Query handlers are simpler than commands - they just read data.

### What to Test

1. ✅ Correct repository method is called
2. ✅ Query parameters are passed correctly
3. ✅ Results are returned unchanged
4. ✅ NotFoundError is raised when appropriate

### Example: Testing GetRoutineHandler

```python
"""Unit tests for GetRoutineHandler."""

from uuid import uuid4
import pytest

from lykke.application.queries.routine import GetRoutineHandler
from lykke.core.exceptions import NotFoundError
from lykke.domain.entities import RoutineEntity


class _FakeRoutineReadOnlyRepo:
    def __init__(self, routine: RoutineEntity | None = None):
        self._routine = routine
    
    async def get(self, routine_id):
        if self._routine and routine_id == self._routine.id:
            return self._routine
        raise NotFoundError(f"Routine {routine_id} not found")


class _FakeReadOnlyRepos:
    def __init__(self, routine_repo):
        self.routine_ro_repo = routine_repo
        # ... stub out other repos ...


@pytest.mark.asyncio
async def test_get_routine_returns_routine_by_id():
    """Verify get_routine returns the correct routine."""
    user_id = uuid4()
    routine_id = uuid4()
    
    routine = RoutineEntity(
        id=routine_id,
        user_id=user_id,
        name="Morning Routine",
        task_definitions=[],
    )
    
    routine_repo = _FakeRoutineReadOnlyRepo(routine)
    ro_repos = _FakeReadOnlyRepos(routine_repo)
    handler = GetRoutineHandler(ro_repos, user_id)
    
    # Act
    result = await handler.run(routine_id)
    
    # Assert
    assert result == routine
    assert result.id == routine_id


@pytest.mark.asyncio
async def test_get_routine_raises_not_found_for_invalid_id():
    """Verify get_routine raises NotFoundError for invalid ID."""
    # ... setup ...
    
    with pytest.raises(NotFoundError):
        await handler.run(invalid_id)
```

---

## Testing Domain Entities

Domain entities contain business rules. Test them thoroughly!

### What to Test

1. ✅ Business rules are enforced
2. ✅ State transitions are correct
3. ✅ Domain events are raised
4. ✅ Invalid operations raise DomainError

### Example: Testing TaskEntity

```python
"""Unit tests for TaskEntity business logic."""

import pytest
from datetime import UTC, date as dt_date, datetime

from lykke.domain.entities import TaskEntity
from lykke.domain import value_objects
from lykke.core.exceptions import DomainError


def test_task_record_action_updates_status():
    """Verify recording COMPLETE action updates status."""
    task = TaskEntity(
        id=uuid4(),
        user_id=uuid4(),
        scheduled_date=dt_date.today(),
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.TODO,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    
    action = value_objects.Action(
        type=value_objects.ActionType.COMPLETE,
        timestamp=datetime.now(UTC),
    )
    
    # Act
    old_status = task.record_action(action)
    
    # Assert
    assert old_status == value_objects.TaskStatus.READY
    assert task.status == value_objects.TaskStatus.COMPLETE
    assert task.completed_at is not None
    assert len(task.actions) == 1


def test_task_cannot_complete_already_completed_task():
    """Verify completing an already completed task raises error."""
    task = TaskEntity(
        # ... setup ...
        status=value_objects.TaskStatus.COMPLETE,
    )
    
    action = value_objects.Action(
        type=value_objects.ActionType.COMPLETE,
        timestamp=datetime.now(UTC),
    )
    
    # Act & Assert
    with pytest.raises(DomainError, match="Task is already complete"):
        task.record_action(action)
```

---

## Testing Repositories

**Integration tests required!** Repositories interact with the database.

### Example: Testing TaskRepository

```python
"""Integration tests for TaskRepository."""

import pytest
from datetime import date as dt_date

from lykke.infrastructure.repositories import TaskRepository
from lykke.domain.entities import TaskEntity
from lykke.domain import value_objects


@pytest.mark.asyncio
async def test_task_repository_persists_and_retrieves_task(
    test_database, test_user_id
):
    """Verify repository can persist and retrieve a task."""
    repo = TaskRepository(user_id=test_user_id)
    
    task = TaskEntity(
        id=uuid4(),
        user_id=test_user_id,
        scheduled_date=dt_date.today(),
        name="Test Task",
        status=value_objects.TaskStatus.READY,
        type=value_objects.TaskType.WORK,
        category=value_objects.TaskCategory.TODO,
        frequency=value_objects.TaskFrequency.ONCE,
    )
    
    # Act: Persist
    await repo.put(task)
    
    # Assert: Retrieve
    retrieved = await repo.get(task.id)
    assert retrieved.name == "Test Task"
    assert retrieved.status == value_objects.TaskStatus.READY
```

---

## Test Fixtures and Helpers

### Global Fixtures (`tests/conftest.py`)

```python
@pytest.fixture
def test_date():
    """Fixed test date for consistent testing."""
    with freeze_time("2025-11-27 00:00:00-6:00", real_asyncio=True):
        yield datetime.date(2025, 11, 27)

@pytest.fixture
def test_user_id():
    """Test user UUID."""
    return uuid4()
```

### Layer-Specific Fixtures

Create fixtures in layer-specific `conftest.py` files:
- `tests/unit/conftest.py` - Fake repositories
- `tests/integration/conftest.py` - Database setup
- `tests/e2e/conftest.py` - Authenticated clients

---

## Running Tests

### Run All Tests

```bash
make test
```

### Run Specific Test File

```bash
make test-target TARGET=tests/unit/application/commands/test_record_task_action.py
```

### Run Tests by Name

```bash
make test-target TARGET=test_record_task_action
```

### Run with Coverage

```bash
poetry run pytest tests --cov=lykke --cov-report=html
open htmlcov/index.html
```

---

## Best Practices

### DO ✅

1. **Write tests for ALL command handlers**
   - This is where production bugs hide
   - Verify `uow.add()` or `uow.create()` is called
   - Check domain events are raised

2. **Use descriptive test names**
   ```python
   # Good
   def test_complete_task_updates_status_and_sets_completed_at():
   
   # Bad
   def test_task_1():
   ```

3. **Follow AAA pattern**
   ```python
   # Arrange: Setup test data
   task = create_test_task()
   
   # Act: Execute the operation
   result = await handler.complete_task(task.id)
   
   # Assert: Verify expectations
   assert result.status == TaskStatus.COMPLETE
   ```

4. **Test one thing per test**
   - Each test should have a single assertion focus
   - Makes failures easier to debug

5. **Use fake classes instead of mock libraries**
   - Simpler and more maintainable
   - No "magic" mock behavior

### DON'T ❌

1. **Don't skip command tests** 
   - "I'll add tests later" = production bugs

2. **Don't test implementation details**
   ```python
   # Bad: Testing implementation
   assert handler._internal_method_was_called
   
   # Good: Testing behavior
   assert result.status == expected_status
   ```

3. **Don't use shared mutable state**
   ```python
   # Bad: Global state
   SHARED_DATA = []
   
   # Good: Fresh data per test
   @pytest.fixture
   def test_data():
       return []
   ```

4. **Don't make tests depend on each other**
   - Each test should be independent
   - Tests should pass in any order

5. **Don't mock domain entities**
   - They're POJOs, just create real ones
   - Only mock repositories and gateways

---

## Troubleshooting

### Test Fails with "RuntimeError: Task attached to a different loop"

**Solution:** Use `real_asyncio=True` with freezegun:
```python
with freeze_time("2025-11-27", real_asyncio=True):
    yield datetime.date(2025, 11, 27)
```

### Test Can't Find Module

**Solution:** Check `PYTHONPATH` or use absolute imports:
```bash
DATABASE_URL=... poetry run pytest tests/unit
```

### Integration Test Hangs

**Solution:** Check database connection:
```bash
make docker-up
make migrate-test
```

---

## Summary

**Testing Priority:**

1. **P0 - CRITICAL:** Command handlers (all must have tests)
2. **P1 - HIGH:** Query handlers, Domain entities
3. **P2 - MEDIUM:** Integration tests for repositories
4. **P3 - LOW:** E2E tests for critical flows

**Remember:** The command layer is the most critical to test. Bugs in commands = data not saved = unhappy users. Test every command handler thoroughly!

**Questions?** See examples in:
- `tests/unit/application/commands/`
- `tests/unit/application/queries/`
- `tests/integration/repositories/`

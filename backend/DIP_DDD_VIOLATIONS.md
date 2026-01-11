# DIP and DDD Violations Report

This document outlines Dependency Inversion Principle (DIP) and Domain-Driven Design (DDD) violations found in the backend codebase.

## Summary

The codebase generally follows good architectural principles:
- ✅ Domain layer is pure (no infrastructure dependencies)
- ✅ Application layer uses protocols for dependencies
- ✅ Repository protocols are properly defined
- ⚠️ **Presentation layer has several DIP violations** by directly depending on infrastructure

## DIP Violations

The Dependency Inversion Principle states that:
1. High-level modules should not depend on low-level modules; both should depend on abstractions
2. Abstractions should not depend on details; details should depend on abstractions

### Critical Violations

#### 1. `push_subscriptions.py` - Direct Infrastructure Gateway Usage

**File:** `backend/lykke/presentation/api/routers/push_subscriptions.py`

**Issue:** The router directly imports and uses the infrastructure gateway module instead of using dependency injection with a protocol.

```17:17:backend/lykke/presentation/api/routers/push_subscriptions.py
from lykke.infrastructure.gateways import web_push
```

```107:114:backend/lykke/presentation/api/routers/push_subscriptions.py
    background_tasks.add_task(
        web_push.send_notification,
        subscription=result,
        content={
            "title": "Notifications Enabled!",
            "body": "Look at that a notification ;)",
        },
    )
```

**Fix:** Use `WebPushGatewayProtocol` via dependency injection instead of directly calling `web_push.send_notification`.

**Note:** There's already a `WebPushGatewayProtocol` in `backend/lykke/application/gateways/web_push_protocol.py` that should be used.

---

#### 2. `google.py` - Direct Static Method Calls on Infrastructure Class

**File:** `backend/lykke/presentation/api/routers/google.py`

**Issue:** The router directly calls static methods on the concrete `GoogleCalendarGateway` class instead of using dependency injection.

```42:49:backend/lykke/presentation/api/routers/google.py
    authorization_url, state = GoogleCalendarGateway.get_flow(
        "login"
    ).authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
        prompt="consent",
    )
```

```109:109:backend/lykke/presentation/api/routers/google.py
    flow = GoogleCalendarGateway.get_flow("login")
```

**Fix:** Move OAuth flow handling to a command handler or service, and inject `GoogleCalendarGatewayProtocol` via dependency injection. The OAuth flow logic should not be in the router.

**Note:** There's a TODO comment on line 12 acknowledging this needs refactoring:
```12:14:backend/lykke/presentation/api/routers/google.py
# TODO: Refactor OAuth flow to use commands/queries instead of direct repository access
# This is a complex OAuth callback flow that creates multiple entities in a single transaction.
# Consider creating a dedicated OAuthCallbackCommand to handle this flow properly.
```

---

#### 3. `dependencies/commands/calendar.py` - Direct Instantiation in Dependency Function

**File:** `backend/lykke/presentation/api/routers/dependencies/commands/calendar.py`

**Issue:** While this is in a dependency injection function (which is better than in the router), it directly instantiates the concrete implementation.

```24:26:backend/lykke/presentation/api/routers/dependencies/commands/calendar.py
def get_google_calendar_gateway() -> GoogleCalendarGatewayProtocol:
    """Get an instance of GoogleCalendarGateway."""
    return GoogleCalendarGateway()
```

**Assessment:** This is a **minor violation**. The function returns a protocol type, which is good, but the instantiation should ideally come from a factory or container. However, this is acceptable for dependency injection in FastAPI, as long as the concrete class implements the protocol (which it does).

**Fix (optional improvement):** Consider using a dependency injection container, but this is not critical since it's already properly abstracted via the protocol return type.

---

#### 4. `workers/tasks.py` - Direct Instantiation in Background Workers

**File:** `backend/lykke/presentation/workers/tasks.py`

**Issue:** Background workers directly instantiate infrastructure classes.

```32:34:backend/lykke/presentation/workers/tasks.py
def get_google_gateway() -> GoogleCalendarGatewayProtocol:
    """Get a GoogleCalendarGateway instance."""
    return GoogleCalendarGateway()
```

**Assessment:** Similar to #3, this is acceptable for background workers, but could be improved with a factory pattern.

---

## DDD Violations

### Domain Layer Purity ✅

The domain layer is properly isolated:
- ✅ No imports from `lykke.infrastructure`
- ✅ No imports from `lykke.application` (except value objects used in entities)
- ✅ Domain entities use standard library and domain types only
- ✅ Domain events are defined in the domain layer
- ✅ Repository protocols are in the application layer (correct placement)

### Minor Observations

#### Value Objects Using Pydantic

**Files:** `backend/lykke/domain/value_objects/*.py`

**Observation:** Some value objects use Pydantic's `BaseModel`:

- `time_block.py`
- `task.py`
- `sync.py`
- `day.py`
- `routine.py`

**Assessment:** This is **acceptable**. Pydantic is a data validation/serialization library, not infrastructure. It doesn't violate DDD principles as it's used for data modeling, not infrastructure concerns.

---

## Recommendations

### High Priority

1. **Refactor `push_subscriptions.py` router:**
   - Inject `WebPushGatewayProtocol` via dependency injection
   - Create a dependency function similar to `get_google_calendar_gateway()`
   - Use the protocol instead of direct `web_push.send_notification` call

2. **Refactor `google.py` OAuth flow:**
   - Create an `OAuthCallbackCommand` handler as suggested in the TODO
   - Move OAuth flow logic out of the router
   - Use dependency injection for `GoogleCalendarGatewayProtocol`

### Medium Priority

3. **Consider dependency injection container:**
   - While current DI approach works, a container (like `dependency-injector`) could centralize infrastructure instantiation
   - This would make the dependency functions even cleaner

### Low Priority

4. **Worker dependency management:**
   - Background workers currently instantiate dependencies directly
   - Consider a shared factory pattern for consistency

---

## Architecture Assessment

### What's Working Well ✅

1. **Clean Domain Layer:** Domain entities, value objects, and events are properly isolated
2. **Protocol-Based Design:** Application layer correctly uses protocols for repositories and gateways
3. **Proper Layer Separation:** Infrastructure correctly depends on domain and application layers
4. **Repository Pattern:** Repository protocols are properly defined and implemented

### What Needs Improvement ⚠️

1. **Presentation Layer Dependencies:** Routers should depend on protocols, not concrete infrastructure
2. **OAuth Flow:** Should be handled by command handlers, not directly in routers
3. **Background Tasks:** Some direct infrastructure usage in workers

---

## Conclusion

The codebase demonstrates a solid understanding of DDD and DIP principles overall. The main violations are in the presentation layer where routers directly depend on infrastructure implementations instead of abstractions. These are fixable and don't indicate fundamental architectural issues.

The violations are concentrated in:
- 1 critical violation: `push_subscriptions.py` router
- 1 critical violation: `google.py` OAuth flow (with existing TODO)
- 2 minor violations: Direct instantiation in dependency functions (acceptable but could be improved)

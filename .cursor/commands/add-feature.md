# Add Feature Workflow

## How This Works

This is an INTERACTIVE workflow. You MUST stop at each checkpoint and wait for explicit approval before proceeding. Do NOT continue to the next phase until the user says "approved", "looks good", "continue", or similar.

## Phase 1: Feature Understanding

Ask clarifying questions about:

- What problem does this solve?
- Who uses it?
- What's the happy path?
- What are edge cases?

Output a brief feature summary for confirmation.

🛑 **CHECKPOINT: Wait for user to confirm understanding is correct.**

## Phase 2: Data Model Design

Propose:

- New/modified entities (with fields and types)
- New/modified value objects
- Database schema changes (if any)
- Relationships between entities

Format as a simple diagram or structured list. Do NOT write any code yet.

🛑 **CHECKPOINT: Wait for user approval of data model.**

## Phase 3: Service Layer Design

Propose:

- Service methods needed (name, inputs, outputs)
- Business logic summary for each
- Error cases to handle

Format as method signatures with docstrings. Do NOT implement yet.

🛑 **CHECKPOINT: Wait for user approval of service design.**

## Phase 4: Repository Layer Design

Propose:

- Repository methods needed
- Query patterns
- Any new database operations

🛑 **CHECKPOINT: Wait for user approval.**

## Phase 5: API Design (if applicable)

Propose:

- Endpoints (method, path, request/response shapes)
- Authentication requirements

🛑 **CHECKPOINT: Wait for user approval.**

## Phase 6: Frontend Design (if applicable)

Propose:

- Components needed (new or modified)
- State management approach
- UI flow

🛑 **CHECKPOINT: Wait for user approval.**

## Phase 7: Implementation

Only NOW write the actual code, following the approved designs.
Implement in order:

1. Domain entities/value objects
2. Repository interfaces
3. Repository implementations
4. Services
5. API routes
6. Frontend types (run generate_ts_types.py)
7. Frontend components

## Phase 8: Testing

Add tests for all new functionality.

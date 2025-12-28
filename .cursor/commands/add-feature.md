# Add Feature Workflow

## Pre-Implementation Checklist

- [ ] Understand the feature requirements
- [ ] Check existing similar features for patterns
- [ ] Identify affected components (backend/frontend/both)
- [ ] Check for existing tests to understand testing patterns

## Implementation Steps

### Backend (if applicable)

1. **Domain Layer**

   - Create/update domain entities in `planned/domain/entities/`
   - Create/update value objects in `planned/domain/value_objects/`
   - Follow existing naming conventions

2. **Application Layer**

   - Create/update repositories in `planned/application/repositories/`
   - Create/update services in `planned/application/services/`
   - Create/update gateways if external integrations needed

3. **Infrastructure Layer**

   - Implement repository implementations in `planned/infrastructure/repositories/`
   - Add database migrations if schema changes needed

4. **Presentation Layer**

   - Add API routes in `planned/presentation/api/routers/`
   - Follow existing router patterns
   - Add proper authentication/authorization

5. **Testing**
   - Add tests in `tests/` mirroring the structure
   - Ensure coverage matches project standards
   - Test both success and error cases

### Frontend (if applicable)

1. **Types**

   - Update TypeScript types in `frontend/src/types/`
   - Run `generate_ts_types.py` if backend types changed

2. **Components**

   - Create/update components in `frontend/src/components/`
   - Follow existing component patterns
   - Ensure responsive design

3. **Pages/Routes**
   - Add pages in `frontend/src/pages/` if new routes needed
   - Update navigation if needed

## Post-Implementation Checklist

- [ ] All tests pass (`make test` or `poetry run pytest`)
- [ ] Type checking passes (`poetry run mypy planned`)
- [ ] Code follows existing patterns and conventions
- [ ] No linter errors
- [ ] Documentation updated if needed

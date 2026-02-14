# Make TypeCheck Command

Run the command `make typecheck` in the terminal.

If any errors occur, do **not** apply superficial "type-only" patches. Diagnose and explain the underlying root cause first, then implement a fix that resolves that cause.

If the root-cause fix would require a large or wide-reaching change, explain the proposed plan and impact first, and wait for confirmation before proceeding.

When fixing typecheck issues, prefer proper module structure and import hygiene:
- Keep imports at the top of the file.
- Circular imports are not allowed and should be resolved by refactoring module boundaries/dependencies.
- Using `if TYPE_CHECKING` is a last resort, not a default pattern.

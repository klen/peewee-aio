# AGENTS Guide for peewee-aio

This file is for coding agents working in this repository.
Follow it as the default operating guide.

## Project Snapshot

- Project: `peewee-aio`
- Purpose: async support layer for Peewee ORM
- Language: Python (`>=3.10,<4`)
- Package manager + runner: `uv`
- Core package: `peewee_aio/`
- Tests: `tests/` (pytest, async backends)

## Repository Layout

- `peewee_aio/manager.py`: async manager, query execution wrappers, table lifecycle
- `peewee_aio/model.py`: async model/query classes and overrides
- `peewee_aio/fields.py`: typed field shims and async foreign key accessors
- `peewee_aio/databases.py`: sync-guarded Peewee DB wrappers
- `peewee_aio/utils.py`: small query helper utilities
- `tests/`: integration-heavy pytest suite across sqlite/mysql/postgres + asyncio/trio
- `pyproject.toml`: tool config (pytest, ruff, pyrefly, build backend)
- `Makefile`: common dev commands and release helpers
- `.pre-commit-config.yaml`: commit, lint, format, typing, and pre-push test hooks

## Environment Setup

1. Install dependencies:
   - `uv sync --locked --all-extras --dev`
2. Install git hooks:
   - `uv run pre-commit install`
3. Optional (matches `make test` behavior): start local databases:
   - `docker start postgres mysql`

If `--locked` fails after dependency edits, run:
- `uv lock`

## Build, Lint, Typecheck, Test

Primary commands (prefer these):

- Full test suite:
  - `uv run pytest tests`
  - or `make test`
- Single test file:
  - `uv run pytest tests/test_base.py`
- Single test function (important):
  - `uv run pytest tests/test_base.py::test_databases`
- Filter by test name expression:
  - `uv run pytest tests -k databas`
- Type checking:
  - `uv run pyrefly check`
  - or `make types`
- Lint:
  - `uv run ruff check`
- Format:
  - `uv run ruff format`
- Verify lockfile metadata:
  - `uv run uv check`

Notes:

- `pytest` default options come from `pyproject.toml` (`-xsv`, `log_cli=true`).
- Some tests require running MySQL/PostgreSQL services.
- Pre-push hook runs `uv run pytest tests`.

## CI Expectations

GitHub Actions (`.github/workflows/tests.yml`) runs:

1. `uv sync --locked --all-extras --dev`
2. `uv run ruff check`
3. `uv run pyrefly check`
4. `uv run pytest tests`

It tests Python 3.10-3.14 and starts MySQL/Postgres services.

## Code Style and Conventions

### Imports

- Keep `from __future__ import annotations` at the top of Python modules.
- Group imports in order:
  1) stdlib
  2) third-party
  3) local package imports
- Use explicit imports; avoid wildcard imports.
- Prefer module aliases only when conventional (`import peewee as pw`).

### Formatting

- Use `ruff format` output as source of truth.
- Max line length: 100 (configured in Ruff).
- Keep code compact; add vertical spacing for logical blocks.
- Avoid adding comments unless the logic is non-obvious.

### Typing

- This is a typed codebase; preserve and improve typing when editing.
- Use built-in generics (`list[T]`, `dict[K, V]`, `type[T]`) on Python 3.10+.
- Prefer precise return types over `Any`; use `Any` only for dynamic boundaries.
- Use overloads where API surface is polymorphic.
- Keep `TYPE_CHECKING` imports and typing-only helpers behind guards.
- When interacting with Peewee internals, targeted `# type: ignore[...]` is accepted.

### Naming

- Modules/functions/variables: `snake_case`.
- Classes/types: `PascalCase`.
- Type variables follow existing pattern (`TV`, `TVModel`, `TVAIOModel`).
- Test files: `test_*.py`; test functions: `test_*`.

### Async and Query Patterns

- Favor async APIs exposed by `Manager` and `AIOModel`.
- Do not introduce sync Peewee operations unless wrapped in `manager.allow_sync()`.
- For selects, prefer existing await/iteration patterns used by `AIOModelSelect`.
- Keep query/result conversion behavior consistent with `manager.process()` and `Constructor`.

### Error Handling

- Use guard clauses and early returns to reduce nesting.
- Raise specific exceptions already used by project APIs (`DoesNotExist`, `RuntimeError`, `ValueError`).
- Preserve Peewee exception wrapping behavior (`__exception_wrapper__`).
- Avoid broad `except Exception`; catch expected concrete exceptions.

### Testing Conventions

- Reuse fixtures from `tests/conftest.py` (`manager`, `transaction`, `schema`).
- Keep tests backend-aware; avoid hardcoding assumptions for a single driver.
- For async tests, follow existing pytest-aio style (async test functions directly).
- Prefer assertions on behavior and returned model objects over implementation details.

## Lint Rules Snapshot

- Ruff lint uses `select = ["ALL"]` with a curated ignore list in `pyproject.toml`.
- Do not assume strict docstring/type-annotation enforcement for every symbol.
- Keep new code compliant with active rules; run `ruff check` locally.

## Commit and Hook Conventions

- Conventional commits are enforced via pre-commit commit-msg hook.
- Allowed commit types include:
  - `feat`, `fix`, `perf`, `refactor`, `style`, `test`, `build`, `ops`, `docs`, `merge`
- Before finishing substantial changes, run:
  1) `uv run ruff check`
  2) `uv run pyrefly check`
  3) `uv run pytest tests` (or targeted subset while iterating)

## Cursor/Copilot Rules

No repository-specific Cursor or Copilot instruction files were found:

- `.cursorrules`: not present
- `.cursor/rules/`: not present
- `.github/copilot-instructions.md`: not present

If these files are added later, update this guide and follow them as highest-priority repo rules.

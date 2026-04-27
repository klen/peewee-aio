# AGENTS Guide for peewee-aio

- **Project:** `peewee-aio` — async support layer for Peewee ORM
- **Language:** Python (`>=3.10,<4`), package manager `uv`
- **Core:** `peewee_aio/` — `manager.py`, `model.py`, `fields.py`, `databases.py`, `utils.py`,
  `types.py`
- **Tests:** `tests/` — pytest with asyncio/trio backends; shared fixtures in `tests/conftest.py`
- **Config:** `pyproject.toml` (pytest, ruff, pyrefly); `Makefile`
  (dev + release targets); `.pre-commit-config.yaml`

## Safe Validation Commands

- `uv run ruff check` / `uv run ruff format`
- `uv run pyrefly check`
- `uv run pytest tests/test_base.py` — single file
- `uv run pytest tests/test_base.py::test_databases` — single function
- `uv run pytest tests -k <pattern>` — filter by expression
- `uv run pytest tests` — full suite (needs `docker start postgres mysql`)

## High-Risk Commands — Avoid Unless Instructed

- `make release` / `patch` / `minor` / `major` — version bump, tag, merge, push (maintainer-only)
- `git push`, `git tag`, `git merge main` — get explicit user approval first
- `docker stop postgres mysql`, `rm -rf .venv` — destructive; prefer `uv sync`

## Files and Directories to Avoid

- `uv.lock` — auto-generated; update via `uv lock`
- `CHANGELOG.md` — maintained by release process
- `.git-commits.yaml` — commit convention whitelist
- `.github/workflows/tests.yml` — CI definition

## Editing Guidelines

- `from __future__ import annotations` at the top of every module
- Import order: stdlib → third-party → local; explicit only; `import peewee as pw`
- `ruff format` is source of truth; max line length 100
- Typed codebase: built-in generics (`list[T]`), precise types over `Any`, `TYPE_CHECKING` guards,
  `# type: ignore[...]` OK for Peewee internals
- Naming: `snake_case` modules/functions/variables, `PascalCase` classes,
  type vars `TV`/`TVModel`/`TVAIOModel`, tests `test_*.py`/`test_*`
- Favor async APIs (`Manager`, `AIOModel`); no sync Peewee outside `manager.allow_sync()`
  preserve `__exception_wrapper__`; avoid broad `except Exception`
- Reuse `tests/conftest.py` fixtures
  (`manager`, `transaction`, `schema`); backend-aware tests; async test functions directly

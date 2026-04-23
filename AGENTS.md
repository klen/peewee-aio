# AGENTS Guide for peewee-aio

Default operating guide for coding agents in this repository.

## Repository Overview

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
- `uv run uv check` — verify lockfile metadata

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
- Guard clauses and early returns; specific exceptions
  (`DoesNotExist`, `RuntimeError`, `ValueError`);
  preserve `__exception_wrapper__`; avoid broad `except Exception`
- Reuse `tests/conftest.py` fixtures
  (`manager`, `transaction`, `schema`); backend-aware tests; async test functions directly

## Repo-Specific Notes

- Ruff lint: `select = ["ALL"]` with curated ignores in `pyproject.toml`
- Conventional commits enforced: `feat`, `fix`, `perf`, `refactor`, `style`, `test`, `build`, `ops`,
  `docs`, `merge`
- Pre-push hook runs `uv run pytest tests`;
  CI runs across Python 3.10–3.14 with MySQL and Postgres services
- If `uv sync --locked` fails after dependency edits, run `uv lock`

## Good Defaults for Agents

- Read relevant source and tests before editing
- After changes: `uv run ruff check`, `uv run pyrefly check`, targeted `uv run pytest`
- Do not commit or push unless explicitly instructed
- Keep changes focused; avoid unrelated refactors

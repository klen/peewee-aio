VIRTUAL_ENV ?= env

$(VIRTUAL_ENV): uv.lock pyproject.toml
	@uv sync
	@uv run pre-commit install
	@touch $(VIRTUAL_ENV)

.PHONY: test
test t: $(VIRTUAL_ENV)
	docker start postgres mysql
	@uv run pytest tests

.PHONY: types
types: $(VIRTUAL_ENV)
	@uv run pyrefly check

.PHONY: example
example: $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/pip install uvicorn asgi-tools
	@$(VIRTUAL_ENV)/bin/uvicorn --port 5000 example:app

.PHONY: release
VPART?=minor
# target: release - Bump version
release:
	@git checkout develop
	@git pull
	@git merge master
	@uvx bump-my-version bump $(VPART)
	@uv lock
	@{ \
	  printf 'build(release): %s\n\n' "$$(uv version --short)"; \
	  printf 'Changes:\n\n'; \
	  git log --oneline --pretty=format:'%s [%an]' master..develop | grep -Evi 'github|^Merge' || true; \
	} | git commit -a -F -
	@git tag `uv version --short`
	@git checkout master
	@git pull
	@git merge develop
	@git checkout develop
	@git push origin develop master
	@git push origin --tags
	@echo "Release process complete for `uv version --short`."

.PHONY: minor
minor: release

.PHONY: patch
patch:
	make release VPART=patch

.PHONY: major
major:
	make release VPART=major

version v:
	uv version --short

.PHONY: setup-postgres
setup-postgres:
	docker exec -i postgres psql -U postgres < tests/assets/init-postgres.sql

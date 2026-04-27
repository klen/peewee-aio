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

.PHONY: lint
lint: $(VIRTUAL_ENV) types
	@uv run ruff check

outdated:
	@echo "Checking for outdated dependencies..."
	@uv tree --depth 1 --outdated | grep 'latest' || echo "All dependencies are up to date."

.PHONY: example
example: $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/pip install uvicorn asgi-tools
	@$(VIRTUAL_ENV)/bin/uvicorn --port 5000 example:app

# ==============
#  Bump version
# ==============

VPART	?= minor
MAIN_BRANCH = main
DEV_BRANCH = develop

.PHONY: release
# target: release - Bump version
release:
	git checkout $(MAIN_BRANCH)
	git pull
	git checkout $(DEV_BRANCH)
	git pull
	uvx bump-my-version bump $(VPART)
	uv lock
	@VERSION="$$(uv version --short)"; \
		{ \
			printf 'build(release): %s\n\n' "$$VERSION"; \
			printf 'Changes:\n\n'; \
			git log --oneline --pretty=format:'%s [%an]' $(MAIN_BRANCH)..$(DEV_BRANCH) | grep -Evi 'github|^Merge' || true; \
		} | git commit -a -F -
	git checkout $(MAIN_BRANCH)
	git merge $(DEV_BRANCH)
	@VERSION="$$(uv version --short)"; \
		git push origin $(MAIN_BRANCH); \
		git tag -a "$$VERSION" -m "$$VERSION"; \
		git push origin "$$VERSION"
	git checkout $(DEV_BRANCH)
	git merge $(MAIN_BRANCH)
	git push origin $(DEV_BRANCH)
	@echo "Release process complete for `uv version --short`"

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

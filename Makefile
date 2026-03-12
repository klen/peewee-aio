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

VERSION	?= minor
MAIN_BRANCH = main
STAGE_BRANCH = develop

.PHONY: release
VPART?=minor
# target: release - Bump version
release:
	git checkout $(MAIN_BRANCH)
	git pull
	git checkout $(STAGE_BRANCH)
	git pull
	uvx bump-my-version bump $(VPART)
	uv lock
	@VERSION="$$(uv version --short)"; \
		{ \
			printf 'build(release): %s\n\n' "$$VERSION"; \
			printf 'Changes:\n\n'; \
			git log --oneline --pretty=format:'%s [%an]' $(MAIN_BRANCH)..$(STAGE_BRANCH) | grep -Evi 'github|^Merge' || true; \
		} | git commit -a -F -; \
		git tag -a "$$VERSION" -m "$$VERSION";
	git checkout $(MAIN_BRANCH)
	git merge $(STAGE_BRANCH)
	git checkout $(STAGE_BRANCH)
	git merge $(MAIN_BRANCH)
	@git -c push.followTags=false push origin $(STAGE_BRANCH) $(MAIN_BRANCH)
	@git push --tags origin
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

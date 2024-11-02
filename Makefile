VIRTUAL_ENV ?= env

$(VIRTUAL_ENV): pyproject.toml
	@poetry install --with dev
	@GIT_CONFIG=/dev/null || @poetry run pre-commit install
	@touch $(VIRTUAL_ENV)

.PHONY: test
test t: $(VIRTUAL_ENV)
	docker start postgres mysql
	@poetry run pytest tests

.PHONY: mypy
mypy: $(VIRTUAL_ENV)
	@poetry run mypy

.PHONY: example
example: $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/pip install uvicorn asgi-tools
	@$(VIRTUAL_ENV)/bin/uvicorn --port 5000 example:app


VERSION	?= minor

.PHONY: version
version:
	@$(eval VFROM := $(shell poetry version -s))
	@poetry version $(VERSION)
	@git commit -am "build: bump version $(VFROM) → `poetry version -s`"
	@git tag `poetry version -s`
	@git checkout master
	@git merge develop
	@git checkout develop
	@git push origin develop master
	@git push --tags

.PHONY: minor
minor:
	make version VERSION=minor

.PHONY: patch
patch:
	make version VERSION=patch

.PHONY: major
major:
	make version VERSION=major

.PHONY: clean
# target: clean - Display callable targets
clean:
	rm -rf build/ dist/ docs/_build *.egg-info
	find $(CURDIR) -name "*.py[co]" -delete
	find $(CURDIR) -name "*.orig" -delete
	find $(CURDIR)/$(MODULE) -name "__pycache__" | xargs rm -rf

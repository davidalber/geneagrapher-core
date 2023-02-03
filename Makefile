.PHONY: format flake8 mypy test

check: format-check flake8 mypy test

# Code formatting
format:
	poetry run black geneagrapher_core tests
fmt: format
black: format

format-check:
	poetry run black --check geneagrapher_core tests

# Linting
flake8:
	poetry run flake8
flake: flake8
lint: flake8

# Type enforcement
mypy:
	poetry run mypy geneagrapher_core tests
types: mypy

# Tests
test:
	poetry run pytest -m "not live" tests

all:

.PHONY: format flake8 mypy test

check: format-check flake8 mypy test

# Code formatting
format_targets := geneagrapher_core examples tests

format:
	poetry run black $(format_targets)
fmt: format
black: format

format-check:
	poetry run black --check $(format_targets)

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

clean:
	rm -rf dist

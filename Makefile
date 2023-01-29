# Code formatting
format:
	poetry run black geneagrapher_core tests
fmt: format

# Linting
flake8:
	poetry run flake8
flake: flake8
lint: flake8

# Type enforcement
mypy:
	poetry run mypy geneagrapher_core/record.py tests/test_record.py
types: mypy

# Tests
test:
	poetry run pytest tests

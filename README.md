# Development
Several development commands are runnable with `make`:
- `make fmt` (also `make format`) formats code using black
- `make format-check` runs black and reports if the code passes
  formatting checks
- `make lint` (also `make flake8` and `make flake`) does linting
- `make mypy` (also `make types`) checks the code for typing violations
- `make test` runs automated tests
- `make check` does code formatting (checking, not modifying),
  linting, type checking, and testing in one command; if this command
  does not pass, CI will not pass

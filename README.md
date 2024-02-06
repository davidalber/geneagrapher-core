# geneagrapher-core [![Continuous Integration Status](https://github.com/davidalber/geneagrapher-core/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/davidalber/geneagrapher-core/actions/workflows/ci.yaml/badge.svg?branch=main) [![Live Tests Status](https://github.com/davidalber/geneagrapher-core/actions/workflows/live-tests.yaml/badge.svg?branch=main)](https://github.com/davidalber/geneagrapher-core/actions/workflows/live-tests.yaml/badge.svg?branch=main) [![Documentation Status](https://readthedocs.org/projects/geneagrapher-core/badge/?version=latest)](https://geneagrapher-core.readthedocs.io/en/latest/?badge=latest)

## Overview
Geneagrapher is a tool for extracting information from the
[Mathematics Genealogy Project](https://www.mathgenealogy.org/) to
form a math family tree, where connections are between advisors and
their students.

This package contains the core data-grabbing and manipulation
functions needed to build a math family tree. The functionality here
is low level and intended to support the development of other
tools. If you just want to build a geneagraph, take a look at
[Geneagrapher](https://github.com/davidalber/geneagrapher). If you
want to get mathematician records and use them in code, then this
project may be useful to you.

## Documentation
Documentation about how to call into this package's functions can be
found at http://geneagrapher-core.readthedocs.io/.

## Development
Dependencies in this package are managed by
[Poetry](https://python-poetry.org/). Thus, your Python environment
will need Poetry installed. Install all dependencies with:

```sh
$ poetry install
```

Several development commands are runnable with `make`:
- `make fmt` (also `make black` and `make format`) formats code using
  black
- `make format-check` runs black and reports if the code passes
  formatting checks without making changes
- `make lint` (also `make flake8` and `make flake`) does linting
- `make mypy` (also `make types`) checks the code for typing violations
- `make test` runs automated tests
- `make check` does code formatting (checking, not modifying),
  linting, type checking, and testing in one command; if this command
  does not pass, CI will not pass

## Releasing New Versions

1. Increase the version in pyproject.toml (e.g., [ed80c2c](https://github.com/davidalber/geneagrapher-core/commit/ed80c2c568605f0eab3c3b8a9bf9d7d14aaf1495)).
1. Add an entry for the new version in CHANGELOG.md (e.g., [bf2931a](https://github.com/davidalber/geneagrapher-core/commit/bf2931a2b602c692cf690dd55b0809489c457e7c)).
1. Push changes.
1. Tag the new version with message "Release VERSION".
   ```bash
   $ git tag -s vVERSION COMMIT_SHA
   ```
1. Push the tag.
   ```bash
   $ git push origin vVERSION
   ```
1. Build the distribution.
   ```bash
   $ poetry build
   ```
1. Publish release to Test PyPI (this assumes that Poetry has been
   configured with the Test PyPI URL).
   ```bash
   $ poetry publish -r testpypi
   ```
1. Publish release to PyPI.
   ```bash
   $ poetry publish
   ```
1. Create [new
   release](https://github.com/davidalber/geneagrapher-core/releases/new).

# 0.1.2
Release 26-Jan-2024

- Updated dependency versions to resolve Dependabot alerts.
- Updated GitHub Actions workflow dependencies to use Node 20.

# 0.1.1
Released 22-May-2023

- Extract promotors and co-promotors as advisors (#2).

# 0.1.0
Released 07-Apr-2023

This is the first release of geneagrapher-core. Much of the
functionality of this package comes from
[Geneagrapher](https://github.com/davidalber/geneagrapher), which
until now was responsible for retrieving mathematician records
directly from the Math Genealogy Project. This package now owns that
responsibility. The main features of this release are:

- Functions to support the retrieval of single records or to build
  entire graphs.
- Arguments to provide callback functions that will receive
  information during a graph-building process.
- Online documentation to make it easier for others to use this
  package for retrieving records or building graphs.
- Support for general caching schemes.

Additionally, this release modernizes the coding standards and tools
used. Much of the Geneagrapher code this replaces was written
in 2008. More recent updates were made in 2011 and 2018, but much has
changed with Python and development tools during that time. This
release adds type hints, updated and more modern testing, linting, and
a continuous integration process. Of course, this release also targets
Python 3, instead of Python 2.

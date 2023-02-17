#################
geneagrapher-core
#################

.. toctree::
   :maxdepth: 2
   :hidden:

   get-one-record
   build-graph

Description
===========

Geneagrapher is a tool for extracting information from the
`Mathematics Genealogy Project <https://www.mathgenealogy.org/>`_ to
form a math family tree, where connections are between advisors and
their students.

This package contains the core data-grabbing and manipulation
functions needed to build a math family tree. The functionality here
is low level and intended to support the development of other
tools. If you just want to build a geneagraph, take a look at
`Geneagrapher <https://github.com/davidalber/geneagrapher>`_. If you
want to get mathematician records and use them in code, then this
project may be useful to you.

Overview
========

This package uses :mod:`asyncio` to concurrently retrieve records. In
order to use the package, your code will need to call it from within
an event loop.

The package provides two main features:

- Functions to get single records. These functions are described in
  :doc:`get-one-record`.
- A function that will return all data for a tree that begins with
  specified records. This function is described in :doc:`build-graph`.

Questions and Issues
====================

If the documentation is unclear, please reach out with
questions. Likewise, if you encounter issues with the package, please
report them. In both cases, the best way to do this is to file an
issue `here
<https://github.com/davidalber/geneagrapher-core/issues>`_.

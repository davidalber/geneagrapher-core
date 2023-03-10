##############################
Getting All Records in a Graph
##############################
.. currentmodule:: geneagrapher_core.traverse

Get all records in a graph using the :func:`build_graph <build_graph>`
function.

.. autofunction:: build_graph

Related types
=============
.. autoclass:: TraverseItem
   :members:
   :undoc-members:
   :member-order: bysource

.. autoclass:: TraverseDirection()
   :members:
   :undoc-members:
   :member-order: bysource

.. autoclass:: Geneagraph
   :members:
   :undoc-members:
   :member-order: bysource

Callbacks
=========

Report callback
---------------

The :func:`build_graph <build_graph>` function optionally takes a
reporting callback function. If provided, this function will be called
when new records are added to the traversal plan or when records have
been retrieved.

The ``report_callback`` function is called with:

- An :class:`asyncio.TaskGroup`, which is useful if you want to do
  something expensive in the reporting callback and do not want to
  block the graph-building path.
- Three integers that report:

  1. The number of known records yet to be retrieved.
  2. The number of records in the process of being retrieved.
  3. The number of records that have been retrieved.

Examples
^^^^^^^^
Here's an example of a simple, blocking callback::

    async def show_progress(
        tg: asyncio.TaskGroup, to_fetch: int, fetching: int, fetched: int
    ) -> None:
        print(f"Todo: {to_fetch}    Doing: {fetching}    Done: {fetched}")

Here's a more complicated example where you might want to create a new
task to complete the reporting. Doing so keeps the reporting callback
from blocking progress on data retrieval.

.. code-block::

    async def do_expensive_network_request(
        to_fetch: int, fetching: int, fetched: int
    ) -> None:
        # Do something that takes a long time.

    async def show_progress(
        tg: asyncio.TaskGroup, to_fetch: int, fetching: int, fetched: int
    ) -> None:
        tg.create_task(do_expensive_network_request(to_fetch, fetching, fetched))

Record callback
---------------

The :func:`build_graph <build_graph>` function optionally takes a
record callback function. If provided, this function will be called
when a record has been retrieved. The callback function receives the
record data as an argument.

The ``record_callback`` function is called with:

- An :class:`asyncio.TaskGroup`, which is useful if you want to do
  something expensive in the reporting callback and do not want to
  block the graph-building path.
- A :class:`Record <geneagrapher_core.record.Record>` object
  containing the record data.

Examples
^^^^^^^^
Here's an example of a simple, blocking callback::

    async def got_record(tg: asyncio.TaskGroup, record: Record) -> None:
        print(record)

Here's a more complicated example where you might want to create a new
task. Doing so keeps the record callback from blocking progress on
data retrieval.

.. code-block::

    async def do_expensive_network_request(record: Record) -> None:
        # Do something that takes a long time.

    async def got_record(tg: asyncio.TaskGroup, record: Record) -> None:
        tg.create_task(do_expensive_network_request(record))

Example Code
============
An example of how to use the ``cache`` and ``report_callback``
arguments to :func:`build_graph
<geneagrapher_core.traverse.build_graph>` is in the repository's
`examples directory
<https://github.com/davidalber/geneagrapher-core/tree/main/examples>`_.

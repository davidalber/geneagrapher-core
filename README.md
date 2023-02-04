# Overview
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

# Documentation
## Functions
The geneagrapher-core package uses
[asyncio](https://docs.python.org/3/library/asyncio.html) to
concurrently retrieve records. In order to use it, your code will need
to call it from within an event loop.

This package has two entry-point functions used to get mathematician
records: `get_record` and `build_graph`.

### `get_record`
This function is in record.py and is used to get a single
mathematician record. The function takes the ID of the record to
retrieve and, optionally, a `Cache` object.

```python
async def get_record(
    record_id: RecordId, cache: Optional[Cache] = None
) -> Optional[Record]
```

The `RecordId` type is a typing `NewType` that aliases integer. The ID
is the Math Genealogy Project ID. For instance, 18231 is [Carl
Friedrich Gauß](https://www.mathgenealogy.org/id.php?id=18231).

If an object is passed as the `cache` argument, it needs to implement
the `Cache` protocol defined in record.py.

#### Examples
To get the record for Carl Friedrich Gauß without using a cache:

```python
record = await get_record(RecordId(18231))
```

To get the record for Carl Friedrich Gauß with a cache (assuming
`cache` implements the `Cache` protocol):

```python
record = await get_record(RecordId(18231), cache)
```

### `build_graph`
This function is in traverse.py and is used to build a geneagraph
(from descendants to advisors). The function takes a list of record
IDs that are the leaves of the graph to build, an optional `Cache`
object, and an optional callback function that will be sent status on
the building process. The function returns a dict that conforms to the
`Geneagraph` definition in traverse.py.

```python
async def build_graph(
    start_nodes: List[RecordId],
    cache: Optional[Cache] = None,
    report_progress: Optional[
        Callable[[asyncio.TaskGroup, int, int, int], Awaitable[None]]
    ] = None,
) -> Geneagraph
```

The `RecordId` and `Cache` types were described in the `get_record`
documentation. The `report_progress` callback function is called with:

- An asyncio
  [TaskGroup](https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup),
  which is useful if you want to do something expensive in the
  reporting callback and do not want to block the graph-building path.
- Three integers that report:
  1. The number of known records yet to be retrieved.
  1. The number of records in the process of being retrieved.
  1. The number of records that have been retrieved.

#### Examples
Here's an example of a simple, blocking callback:

```python
async def show_progress(
    tg: asyncio.TaskGroup, to_fetch: int, fetching: int, fetched: int
) -> None:
    print(f"Todo: {to_fetch}    Doing: {fetching}    Done: {fetched}")
```

Here's a more complicated example where you might want to create a new
task to complete the reporting. Doing so keeps the reporting process
from blocking progress on data retrieval.

```python
async def do_expensive_network_request(
    to_fetch: int, fetching: int, fetched: int
) -> None:
    # Do something that takes a long time.

async def show_progress(
    tg: asyncio.TaskGroup, to_fetch: int, fetching: int, fetched: int
) -> None:
    tg.create_task(do_expensive_network_request(to_fetch, fetching, fetched))
```

## Argument Types
More details on custom types can be found in the following locations:
- `Cache`: record.py
- `Geneagraph`: traverse.py
- `Record`: record.py
- `RecordId`: record.py

## Example Drivers
The examples directory contains simple drivers that use this package.

# Development
This section describes what is needed to do development on the code in
this package.

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

from geneagrapher_core.record import (
    Cache,
    Record,
    RecordId,
    get_record_inner,
)

from aiohttp import ClientSession
import asyncio
from enum import Flag, auto
import functools
from typing import Awaitable, Callable, List, Literal, NamedTuple, Optional, TypedDict


class Geneagraph(TypedDict):
    start_nodes: List[RecordId]
    nodes: dict[RecordId, Record]
    status: Literal["complete", "truncated"]


class TraverseDirection(Flag):
    """A flag that specifies the traversal direction for a node. This
    is a :class:`enum.Flag`, so attributes can be combined (e.g.,
    ``ADVISORS | DESCENDANTS``).
    """

    ADVISORS = auto()
    DESCENDANTS = auto()


class TraverseItem(NamedTuple):
    id: RecordId
    traverse_direction: TraverseDirection


class MaxRecordsException(Exception):
    pass


class LifecycleTracking:
    """This class is used to track the state of records during the
    graph-building process.
    """

    PROCESSING_OVERAGE_BUFFER = 10

    def __init__(
        self,
        start_items: List[TraverseItem],
        max_records: Optional[int],
        report_callback: Optional[Callable[[int, int, int], Awaitable[None]]] = None,
    ):
        self.todo: dict[RecordId, TraverseItem] = {ti.id: ti for ti in start_items}
        self.doing: dict[RecordId, TraverseItem] = {}
        self.done: set[RecordId] = set()
        self.max_records = max_records
        self._report_callback = report_callback
        self.num_records_received = 0
        self.finished_record_event = asyncio.Event()

    @property
    def all_done(self) -> bool:
        return bool(self.num_todo == len(self.doing) == 0)

    @property
    def num_todo(self) -> int:
        return len(self.todo)

    @property
    def num_doing(self) -> int:
        return len(self.doing)

    @property
    def potential_fetched_records(self) -> int:
        return self.num_doing + self.num_records_received

    async def purge_todo(self) -> None:
        self.todo.clear()
        await self.report_back()

    async def create(self, id: RecordId, direction: TraverseDirection) -> None:
        """Add the node to the `todo` set if it is not in todo, doing,
        or done already.
        """
        if not (id in self.todo or id in self.doing or id in self.done):
            self.todo[id] = TraverseItem(id, direction)
            await self.report_back()

    async def start_next(self) -> TraverseItem:
        """Get a record ID from the `todo` set, add it to the `doing`
        set, and call the `report_back` callback function.
        """
        (id, item) = self.todo.popitem()
        self.doing[id] = item
        await self.report_back()
        return item

    async def finish(self, id: RecordId, got_record: bool) -> None:
        """Move a record ID from the `doing` set to the `done` set and
        call the `report_back` callback function. Record if a record
        was received.
        """
        self.doing.pop(id)
        self.done.add(id)

        if got_record:
            self.num_records_received += 1

        self.finished_record_event.set()

        await self.report_back()

    async def process_another(self) -> None:
        """Limit the number of records being requested to an amount
        slightly more than the maximum number of records. This avoids
        situations where hundreds or thousands of additional records
        are being processed when the maximum number of records has
        been reached.
        """
        if self.max_records is not None:
            while (
                self.potential_fetched_records
                >= self.max_records + LifecycleTracking.PROCESSING_OVERAGE_BUFFER
            ):
                # If max_records has been reached, raise an exception.
                if self.num_records_received >= self.max_records:
                    raise MaxRecordsException()

                # Wait until another fetch operation has finished.
                self.finished_record_event.clear()
                await self.finished_record_event.wait()

    async def report_back(self) -> None:
        """Call the reporting callback function that was optionally
        provided during initialization.
        """
        if self._report_callback is not None:
            await self._report_callback(self.num_todo, len(self.doing), len(self.done))


async def build_graph(
    start_items: List[TraverseItem],
    *,
    http_semaphore: Optional[asyncio.Semaphore] = None,
    max_records: Optional[int] = None,
    user_agent: Optional[str] = None,
    cache: Optional[Cache] = None,
    record_callback: Optional[
        Callable[[asyncio.TaskGroup, Record], Awaitable[None]]
    ] = None,
    report_callback: Optional[
        Callable[[asyncio.TaskGroup, int, int, int], Awaitable[None]]
    ] = None,
) -> Geneagraph:
    """Build a complete geneagraph using the ``start_nodes`` as the
    graph's leaf nodes.

    :param start_items: a list of nodes and direction from which to traverse from them
    :param http_semaphore: a semaphore to limit HTTP request concurrency
    :param max_records: the maximum number of records to include in the built graph
    :param user_agent: a custom user agent string to use in HTTP requests
    :param cache: a cache object for getting and storing results
    :param record_callback: callback function called with record data as it is retrieved
    :param report_callback: callback function called to report graph-building progress

    **Example**::

        # Build a graph that contains Carl Friedrich Gauß (18231), his advisor tree,
        # Johann Friedrich Pfaff (18230), his advisor tree, and his descendant tree.
        start_items = [
            TraverseItem(RecordId(18231), TraverseDirection.ADVISORS),
            TraverseItem(
                RecordId(18230),
                TraverseDirection.ADVISORS | TraverseDirection.DESCENDANTS
            ),
        ]
        graph = await build_graph(start_items)

    """
    ggraph: Geneagraph = {
        "start_nodes": [n.id for n in start_items],
        "nodes": {},
        "status": "complete",
    }

    continue_event = asyncio.Event()

    def below_max_records() -> bool:
        return max_records is None or len(ggraph["nodes"]) < max_records

    async def add_neighbor_work(
        record: Record, traverse_direction: TraverseDirection
    ) -> None:
        key: Literal["advisors", "descendants"] = (
            "advisors"
            if traverse_direction is TraverseDirection.ADVISORS
            else "descendants"
        )
        for id in record[key]:
            await tracking.create(RecordId(id), traverse_direction)
            if tracking.num_todo > 0:
                # New work was added to the todo queue. Signal the
                # loop below.
                continue_event.set()

    async def fetch_and_process(
        item: TraverseItem, client: ClientSession, cache: Optional[Cache]
    ) -> None:
        record = await get_record_inner(item.id, client, http_semaphore, cache)

        await tracking.finish(item.id, record is not None)
        if record is not None:
            if below_max_records():
                ggraph["nodes"][item.id] = record

                if record_callback is not None:
                    await record_callback(tg, record)

                for td in (TraverseDirection.ADVISORS, TraverseDirection.DESCENDANTS):
                    if td in item.traverse_direction:
                        await add_neighbor_work(record, td)
            else:
                # The graph is now as large as it is allowed to be.
                ggraph["status"] = "truncated"

        if tracking.all_done:
            # There's no more work to do. Signal the loop below.
            continue_event.set()

    headers = None if user_agent is None else {"User-Agent": user_agent}
    async with ClientSession(
        "https://www.mathgenealogy.org", headers=headers
    ) as client:

        async with asyncio.TaskGroup() as tg:
            tracking = LifecycleTracking(
                start_items,
                max_records,
                None
                if report_callback is None
                else functools.partial(report_callback, tg),
            )
            while tracking.num_todo > 0:
                try:
                    await tracking.process_another()
                except MaxRecordsException:
                    # We're done.
                    await tracking.purge_todo()
                    break

                item = await tracking.start_next()

                # Create a task to fetch and process the record.
                tg.create_task(fetch_and_process(item, client, cache))

                if tracking.num_todo == 0:
                    # There's nothing left to do for now. Wait for
                    # something to happen.
                    continue_event.clear()
                    await continue_event.wait()

    return ggraph

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


class LifecycleTracking:
    """This class is used to track the state of records during the
    graph-building process.
    """

    def __init__(
        self,
        start_items: List[TraverseItem],
        report_callback: Optional[Callable[[int, int, int], Awaitable[None]]] = None,
    ):
        self.todo: dict[RecordId, TraverseItem] = {ti.id: ti for ti in start_items}
        self.doing: dict[RecordId, TraverseItem] = {}
        self.done: set[RecordId] = set()
        self._report_callback = report_callback

    @property
    def all_done(self) -> bool:
        return bool(self.num_todo == len(self.doing) == 0)

    @property
    def num_todo(self) -> int:
        return len(self.todo)

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

    async def finish(self, id: RecordId) -> None:
        """Move a record ID from the `doing` set to the `done` set and
        call the `report_back` callback function.
        """
        self.doing.pop(id)
        self.done.add(id)
        await self.report_back()

    async def report_back(self) -> None:
        """Call the reporting callback function that was optionally
        provided during initialization.
        """
        if self._report_callback is not None:
            await self._report_callback(self.num_todo, len(self.doing), len(self.done))


async def build_graph(
    start_nodes: List[TraverseItem],
    *,
    max_concurrency: int = 4,
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

    :param start_nodes: a list of nodes and direction from which to traverse from them
    :param max_concurrency: the maximum number of concurrent HTTP requests allowed
    :param cache: a cache object for getting and storing results
    :param record_callback: callback function called with record data as it is retrieved
    :param report_callback: callback function called to report graph-building progress

    **Example**::

        # Build a graph that contains Carl Friedrich Gauß (18231), his advisor tree,
        # Johann Friedrich Pfaff (18230), his advisor tree, and his descendant tree.
        start_nodes = [
            TraverseItem(RecordId(18231), TraverseDirection.ADVISORS),
            TraverseItem(
                RecordId(18230),
                TraverseDirection.ADVISORS | TraverseDirection.DESCENDANTS
            ),
        ]
        graph = await build_graph(start_nodes)

    """
    semaphore = asyncio.Semaphore(max_concurrency)
    ggraph: Geneagraph = {
        "start_nodes": [n.id for n in start_nodes],
        "nodes": {},
    }

    continue_event = asyncio.Event()

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
        record = await get_record_inner(item.id, client, semaphore, cache)

        await tracking.finish(item.id)
        if record is not None:
            ggraph["nodes"][item.id] = record
            if record_callback is not None:
                await record_callback(tg, record)

            for td in (TraverseDirection.ADVISORS, TraverseDirection.DESCENDANTS):
                if td in item.traverse_direction:
                    await add_neighbor_work(record, td)

        if tracking.all_done:
            # There's no more work to do. Signal the loop below.
            continue_event.set()

    async with asyncio.TaskGroup() as tg:
        tracking = LifecycleTracking(
            start_nodes,
            None if report_callback is None else functools.partial(report_callback, tg),
        )
        async with ClientSession("https://www.mathgenealogy.org") as client:
            while tracking.num_todo > 0:
                item = await tracking.start_next()

                # Create a task to fetch and process the record.
                tg.create_task(fetch_and_process(item, client, cache))

                if tracking.num_todo == 0:
                    # There's nothing left to do for now. Wait for
                    # something to happen.
                    continue_event.clear()
                    await continue_event.wait()

    return ggraph

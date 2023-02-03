from geneagrapher_core.record import (
    Cache,
    Record,
    RecordId,
    TypedDict,
    get_record_inner,
)

from aiohttp import ClientSession
import asyncio
import functools
from typing import Awaitable, Callable, List, Optional


class Geneagraph(TypedDict):
    start_nodes: List[RecordId]
    nodes: dict[RecordId, Record]


class LifecycleTracking:
    """This class is used to track the state of records during the
    graph-building process.
    """

    def __init__(
        self,
        start_nodes: List[RecordId],
        report_back: Optional[
            Callable[[asyncio.TaskGroup, int, int, int], Awaitable[None]]
        ] = None,
    ):
        self.todo: set[RecordId] = set(start_nodes)
        self._doing: set[RecordId] = set()
        self._done: set[RecordId] = set()
        self._report_back = report_back

    @property
    def all_done(self):
        return len(self.todo) == len(self._doing) == 0

    @property
    def num_todo(self):
        return len(self.todo)

    async def create(self, id: RecordId):
        """Add the id to the `todo` set if it is not in todo, doing,
        or done already.
        """
        if not (id in self.todo or id in self._doing or id in self._done):
            self.todo.add(id)
            await self.report_back()

    async def start_next(self) -> RecordId:
        """Get a record ID from the `todo` set, add it to the `_doing`
        set, and call the `report_back` callback function.
        """
        record_id = self.todo.pop()
        self._doing.add(record_id)
        await self.report_back()
        return record_id

    async def done(self, id: RecordId):
        """Move a record ID from the `_doing` set to the `_done` set
        and call the `report_back` callback function.
        """
        self._doing.remove(id)
        self._done.add(id)
        await self.report_back()

    async def report_back(self):
        """Call the reporting callback function that was optionally
        provided during initialization.
        """
        self._report_back and await self._report_back(
            len(self.todo), len(self._doing), len(self._done)
        )


async def build_graph(
    start_nodes: List[RecordId],
    cache: Optional[Cache] = None,
    report_progress: Optional[
        Callable[[asyncio.TaskGroup, int, int, int], Awaitable[None]]
    ] = None,
) -> Geneagraph:
    """Build a complete geneagraph using the `start_nodes` as the
    graph's leaf nodes. This function traverses in the direction of
    ancestors.
    """
    ggraph: Geneagraph = {
        "start_nodes": start_nodes,
        "nodes": {},
    }

    continue_event = asyncio.Event()

    async def fetch_and_process(record_id, client, cache):
        record = await get_record_inner(record_id, client, cache)

        await tracking.done(record_id)
        if record is not None:
            ggraph["nodes"][record_id] = record
            for id in record["advisors"]:
                await tracking.create(RecordId(id))
                if tracking.num_todo > 0:
                    # New work was added to the todo queue. Signal the
                    # loop below.
                    continue_event.set()

        if tracking.all_done:
            # There's no more work to do. Signal the loop below.
            continue_event.set()

    async with asyncio.TaskGroup() as tg:
        tracking = LifecycleTracking(
            start_nodes,
            None if report_progress is None else functools.partial(report_progress, tg),
        )
        async with ClientSession("https://www.mathgenealogy.org") as client:
            while tracking.num_todo > 0:
                record_id = await tracking.start_next()

                # Create a task to fetch and process the `record_id`
                # record.
                tg.create_task(fetch_and_process(record_id, client, cache))

                if tracking.num_todo == 0:
                    # There's nothing left to do for now. Wait for
                    # something to happen.
                    continue_event.clear()
                    await continue_event.wait()

    return ggraph

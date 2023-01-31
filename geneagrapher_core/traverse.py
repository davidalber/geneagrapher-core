from geneagrapher_core.record import Cache, Record, RecordId, TypedDict, get_record

from typing import Callable, List, Optional


class Geneagraph(TypedDict):
    start_nodes: List[RecordId]
    nodes: dict[RecordId, Record]


class LifecycleTracking:
    def __init__(
        self,
        start_nodes: List[RecordId],
        report_back: Optional[Callable[[int, int, int], None]] = None,
    ):
        self.todo: set[RecordId] = set(start_nodes)
        self._doing: set[RecordId] = set()
        self._done: set[RecordId] = set()
        self._report_back = report_back

    def create(self, id: RecordId):
        """Add the id to the todo set if it is not in todo, doing, or
        done already.
        """
        if not (id in self.todo or id in self._doing or id in self._done):
            self.todo.add(id)
            self.report_back()

    def start_next(self) -> RecordId:
        record_id = self.todo.pop()
        self.doing(record_id)
        return record_id

    def doing(self, id: RecordId):
        self._doing.add(id)
        self.report_back()

    def done(self, id: RecordId):
        self._doing.remove(id)
        self._done.add(id)
        self.report_back()

    def report_back(self):
        self._report_back and self._report_back(
            len(self.todo), len(self._doing), len(self._done)
        )


def build_graph(
    start_nodes: List[RecordId],
    cache: Optional[Cache] = None,
    report_progress: Optional[Callable[[int, int, int], None]] = None,
) -> Geneagraph:
    tracking = LifecycleTracking(start_nodes, report_progress)

    ggraph: Geneagraph = {
        "start_nodes": start_nodes,
        "nodes": {},
    }

    while len(tracking.todo) > 0:
        record_id = tracking.start_next()
        record = get_record(record_id, cache)
        tracking.done(record_id)

        if record is not None:
            ggraph["nodes"][record_id] = record
            for id in record["advisors"]:
                tracking.create(RecordId(id))

    return ggraph

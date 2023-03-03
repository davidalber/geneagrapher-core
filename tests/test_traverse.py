from geneagrapher_core.traverse import (
    LifecycleTracking,
    MaxRecordsException,
    TraverseDirection,
    TraverseItem,
    build_graph,
)
from geneagrapher_core.record import RecordId

import pytest
from typing import List, Literal, Optional
from unittest.mock import (
    ANY,
    AsyncMock,
    MagicMock,
    PropertyMock,
    call,
    patch,
    sentinel as s,
)


class TestLifecycleTracking:
    def test_init(self) -> None:
        start_nodes = [TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)]
        t = LifecycleTracking(start_nodes, s.max_records, s.report_back)
        assert t.todo == {ti.id: ti for ti in start_nodes}
        assert t.doing == {}
        assert t.done == set()
        assert t.max_records == s.max_records
        assert t._report_callback == s.report_back

    @pytest.mark.parametrize(
        "todo,doing,expected",
        [
            ([], {}, True),
            ([TraverseItem(s.rid1, s.tda)], {}, False),
            ([], {s.rid1: TraverseItem(s.rid1, s.tda)}, False),
            (
                [TraverseItem(s.rid1, s.tda)],
                {s.rid2: TraverseItem(s.rid2, s.tda)},
                False,
            ),
        ],
    )
    def test_all_done(
        self,
        todo: List[TraverseItem],
        doing: dict[RecordId, TraverseItem],
        expected: bool,
    ) -> None:
        t = LifecycleTracking(todo, s.max_records)
        t.doing = doing
        assert t.all_done is expected

    @pytest.mark.parametrize(
        "todo,expected",
        [
            ([], 0),
            ([TraverseItem(s.rid1, s.tda)], 1),
            ([TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)], 2),
        ],
    )
    def test_num_todo(self, todo: List[TraverseItem], expected: int) -> None:
        t = LifecycleTracking(todo, s.max_records)
        assert t.num_todo == expected

    @pytest.mark.parametrize(
        "doing,expected",
        [
            ({}, 0),
            ({s.rid1: TraverseItem(s.rid1, s.tda)}, 1),
            (
                {
                    s.rid1: TraverseItem(s.rid1, s.tda),
                    s.rid2: TraverseItem(s.rid2, s.tda),
                },
                2,
            ),
        ],
    )
    def test_num_doing(
        self,
        doing: dict[RecordId, TraverseItem],
        expected: int,
    ) -> None:
        t = LifecycleTracking([], s.max_records)
        t.doing = doing
        assert t.num_doing == expected

    @pytest.mark.parametrize(
        "doing,num_records_received,expected",
        [
            ({}, 0, 0),
            ({}, 14, 14),
            ({s.rid1: TraverseItem(s.rid1, s.tda)}, 0, 1),
            ({s.rid1: TraverseItem(s.rid1, s.tda)}, 13, 14),
            (
                {
                    s.rid1: TraverseItem(s.rid1, s.tda),
                    s.rid2: TraverseItem(s.rid2, s.tda),
                },
                0,
                2,
            ),
            (
                {
                    s.rid1: TraverseItem(s.rid1, s.tda),
                    s.rid2: TraverseItem(s.rid2, s.tda),
                },
                12,
                14,
            ),
        ],
    )
    def test_potential_fetched_records(
        self,
        doing: dict[RecordId, TraverseItem],
        num_records_received: int,
        expected: int,
    ) -> None:
        t = LifecycleTracking([], s.max_records)
        t.doing = doing
        t.num_records_received = num_records_received
        assert t.potential_fetched_records == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "start_nodes,new_node,new_direction,final_todo",
        [
            (
                [TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)],
                s.rid1,
                s.tda,
                {
                    s.rid1: TraverseItem(s.rid1, s.tda),
                    s.rid2: TraverseItem(s.rid2, s.tda),
                },
            ),
            (
                [TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)],
                s.rid3,
                s.tda,
                {
                    s.rid1: TraverseItem(s.rid1, s.tda),
                    s.rid2: TraverseItem(s.rid2, s.tda),
                    s.rid3: TraverseItem(s.rid3, s.tda),
                },
            ),
            (
                [TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)],
                s.rid1,
                s.tdd,
                {
                    s.rid1: TraverseItem(s.rid1, s.tda),
                    s.rid2: TraverseItem(s.rid2, s.tda),
                },
            ),
            (
                [TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)],
                s.rid3,
                s.tdd,
                {
                    s.rid1: TraverseItem(s.rid1, s.tda),
                    s.rid2: TraverseItem(s.rid2, s.tda),
                    s.rid3: TraverseItem(s.rid3, s.tdd),
                },
            ),
        ],
    )
    @patch("geneagrapher_core.traverse.LifecycleTracking.report_back")
    async def test_create(
        self,
        m_report_back: MagicMock,
        start_nodes: List[TraverseItem],
        new_node: RecordId,
        new_direction: TraverseDirection,
        final_todo: dict[RecordId, TraverseItem],
    ) -> None:
        t = LifecycleTracking(start_nodes, s.max_records)
        await t.create(new_node, new_direction)
        assert t.todo == final_todo

    @pytest.mark.asyncio
    async def test_start_next(self) -> None:
        start_nodes = [TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)]
        t = LifecycleTracking(start_nodes, s.max_records)

        next_rec = await t.start_next()
        assert next_rec in start_nodes
        assert t.todo == {sn.id: sn for sn in start_nodes if sn.id != next_rec.id}
        assert t.doing == {sn.id: sn for sn in start_nodes if sn.id == next_rec.id}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "got_record,expected_num_records_received",
        ([False, 0], [True, 1]),
    )
    @patch("geneagrapher_core.traverse.LifecycleTracking.report_back")
    async def test_finish(
        self,
        m_report_back: MagicMock,
        got_record: bool,
        expected_num_records_received: int,
    ) -> None:
        t = LifecycleTracking([TraverseItem(s.rid1, s.tda)], s.max_records)
        t.doing[s.rid2] = TraverseItem(s.rid2, s.tda)

        await t.finish(s.rid2, got_record)
        assert t.doing == {}
        assert t.done == {s.rid2}
        assert t.num_records_received == expected_num_records_received
        m_report_back.assert_called_once_with()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "max_records,num_records_received,num_potential_fetched_records,expected_num_fre_clear_calls,\
expected_num_fre_wait_calls,expect_exception",
        (
            [None, 0, (1000, 2000), 0, 0, False],
            [10, 0, (19,), 0, 0, False],
            [10, 0, (20, 19), 1, 1, False],
            [10, 10, (20, 19), 0, 0, True],
            [10, 0, (20, 21, 19), 2, 2, False],
        ),
    )
    @patch.object(
        LifecycleTracking, "potential_fetched_records", new_callable=PropertyMock
    )
    async def test_process_another(
        self,
        m_potential_fetched_records: MagicMock,
        max_records: int,
        num_records_received: int,
        num_potential_fetched_records: List[int],
        expected_num_fre_clear_calls: int,
        expected_num_fre_wait_calls: int,
        expect_exception: bool,
    ) -> None:
        m_potential_fetched_records.side_effect = num_potential_fetched_records

        t = LifecycleTracking([], max_records)
        t.num_records_received = num_records_received
        t.finished_record_event = MagicMock()
        t.finished_record_event.wait = AsyncMock()
        if expect_exception:
            with pytest.raises(MaxRecordsException):
                await t.process_another()
        else:
            await t.process_another()
        assert (
            len(t.finished_record_event.clear.call_args_list)
            == expected_num_fre_clear_calls
        )
        assert (
            len(t.finished_record_event.wait.call_args_list)
            == expected_num_fre_wait_calls
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("report_callback", [None, AsyncMock()])
    async def test_report_back(self, report_callback: Optional[AsyncMock]) -> None:
        t = LifecycleTracking(
            [TraverseItem(s.rid1, s.tda)], s.max_records, report_callback
        )

        await t.report_back()
        if report_callback is not None:
            report_callback.assert_called_once_with(1, 0, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "start_nodes,max_records,user_agent,expected_graph_records,expected_call_ids,\
expected_num_report_callbacks,expected_status",
    [
        (
            [
                TraverseItem(RecordId(1), TraverseDirection.ADVISORS),
                TraverseItem(RecordId(2), TraverseDirection.ADVISORS),
            ],
            None,
            None,
            [1, 2, 3, 4],
            [1, 2, 3, 4, 5],
            13,
            "complete",
        ),
        (
            [
                TraverseItem(RecordId(1), TraverseDirection.ADVISORS),
                TraverseItem(RecordId(2), TraverseDirection.ADVISORS),
            ],
            None,
            "test user agent",
            [1, 2, 3, 4],
            [1, 2, 3, 4, 5],
            13,
            "complete",
        ),
        (
            [
                TraverseItem(RecordId(1), TraverseDirection.DESCENDANTS),
                TraverseItem(RecordId(2), TraverseDirection.ADVISORS),
            ],
            None,
            None,
            [1, 2, 3, 6, 7, 8],
            [1, 2, 3, 5, 6, 7, 8, 9],
            22,
            "complete",
        ),
        (
            [
                TraverseItem(
                    RecordId(1),
                    TraverseDirection.ADVISORS | TraverseDirection.DESCENDANTS,
                ),
                TraverseItem(RecordId(2), TraverseDirection.ADVISORS),
            ],
            None,
            None,
            [1, 2, 3, 4, 6, 7, 8],
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            25,
            "complete",
        ),
        (
            [
                TraverseItem(
                    RecordId(1),
                    TraverseDirection.ADVISORS | TraverseDirection.DESCENDANTS,
                ),
                TraverseItem(RecordId(2), TraverseDirection.ADVISORS),
            ],
            7,
            None,
            [1, 2, 3, 4, 6, 7, 8],
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            25,
            "complete",
        ),
        (
            [
                TraverseItem(
                    RecordId(1),
                    TraverseDirection.ADVISORS | TraverseDirection.DESCENDANTS,
                ),
                TraverseItem(RecordId(2), TraverseDirection.ADVISORS),
            ],
            4,
            None,
            [1, 2, 6, 7],
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            25,
            "truncated",
        ),
    ],
)
@patch("geneagrapher_core.traverse.get_record_inner")
@patch("geneagrapher_core.traverse.ClientSession")
async def test_build_graph(
    m_client_session: MagicMock,
    m_get_record_inner: MagicMock,
    start_nodes: List[TraverseItem],
    max_records: Optional[int],
    user_agent: Optional[str],
    expected_graph_records: List[int],
    expected_call_ids: List[int],
    expected_num_report_callbacks: int,
    expected_status: Literal["complete", "truncated"],
) -> None:
    m_session = AsyncMock()
    m_client_session.return_value.__aenter__.return_value = m_session

    m_http_semaphore = AsyncMock()
    m_report_callback = AsyncMock()
    m_record_callback = AsyncMock()

    testdata = {
        1: {
            "id": 1,
            "advisors": [3, 4],
            "descendants": [6, 7],
        },
        2: {
            "id": 2,
            "advisors": [3, 5],
            "descendants": [6, 8],
        },
        3: {
            "id": 3,
            "advisors": [],
            "descendants": [1, 2],
        },
        4: {
            "id": 4,
            "advisors": [],
            "descendants": [1],
        },
        5: None,
        6: {
            "id": 6,
            "advisors": [1, 2],
            "descendants": [8],
        },
        7: {
            "id": 7,
            "advisors": [1],
            "descendants": [9],
        },
        8: {
            "id": 8,
            "advisors": [2],
            "descendants": [9],
        },
        9: None,
    }
    m_get_record_inner.side_effect = (
        lambda record_id, client, semaphore, cache: testdata[record_id]
    )

    expected = {
        "start_nodes": [r.id for r in start_nodes],
        "nodes": {rid: testdata[rid] for rid in expected_graph_records},
        "status": expected_status,
    }

    assert (
        await build_graph(
            start_nodes,
            http_semaphore=m_http_semaphore,
            max_records=max_records,
            user_agent=user_agent,
            cache=s.cache,
            record_callback=m_record_callback,
            report_callback=m_report_callback,
        )
        == expected
    )
    expected_headers = None if user_agent is None else {"User-Agent": user_agent}
    m_client_session.assert_called_once_with(
        "https://www.mathgenealogy.org", headers=expected_headers
    )

    assert len(m_get_record_inner.call_args_list) == len(expected_call_ids)
    for c in [
        call(rid, m_session, m_http_semaphore, s.cache) for rid in expected_call_ids
    ]:
        assert c in m_get_record_inner.call_args_list

    # Check the reporting callback calls.
    assert len(m_report_callback.mock_calls) == expected_num_report_callbacks
    assert m_report_callback.call_args == call(
        ANY, 0, 0, len(expected_call_ids)
    )  # ANY is a placeholder for the TaskGroup object passed to the callback function

    # Check the record callback calls.
    assert len(m_record_callback.mock_calls) == len(expected_graph_records)
    for record_id in expected_graph_records:
        assert (
            call(ANY, testdata[record_id]) in m_record_callback.mock_calls
        )  # ANY is a placeholder for the TaskGroup object passed to the callback
        # function

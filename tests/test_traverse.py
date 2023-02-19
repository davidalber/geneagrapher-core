from geneagrapher_core.traverse import (
    LifecycleTracking,
    TraverseDirection,
    TraverseItem,
    build_graph,
)
from geneagrapher_core.record import RecordId

import pytest
from unittest.mock import AsyncMock, call, patch, sentinel as s


class TestLifecycleTracking:
    def test_init(self) -> None:
        start_nodes = [TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)]
        t = LifecycleTracking(start_nodes, s.report_back)
        assert t.todo == {ti.id: ti for ti in start_nodes}
        assert t._doing == {}
        assert t._done == set()
        assert t._report_callback == s.report_back

    @pytest.mark.parametrize(
        "todo,doing,expected",
        [
            ([], [], True),
            ([TraverseItem(s.rid1, s.tda)], [], False),
            ([], [TraverseItem(s.rid1, s.tda)], False),
            ([TraverseItem(s.rid1, s.tda)], [TraverseItem(s.rid2, s.tda)], False),
        ],
    )
    def test_all_done(self, todo, doing, expected) -> None:
        t = LifecycleTracking(todo)
        t._doing = doing
        assert t.all_done is expected

    @pytest.mark.parametrize(
        "todo,expected",
        [
            ([], 0),
            ([TraverseItem(s.rid1, s.tda)], 1),
            ([TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)], 2),
        ],
    )
    def test_num_todo(self, todo, expected):
        t = LifecycleTracking(todo)
        assert t.num_todo == expected

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
        self, m_report_back, start_nodes, new_node, new_direction, final_todo
    ) -> None:
        t = LifecycleTracking(start_nodes)
        await t.create(new_node, new_direction)
        assert t.todo == final_todo

    @pytest.mark.asyncio
    async def test_start_next(self) -> None:
        start_nodes = [TraverseItem(s.rid1, s.tda), TraverseItem(s.rid2, s.tda)]
        t = LifecycleTracking(start_nodes)

        next_rec = await t.start_next()
        assert next_rec in start_nodes
        assert t.todo == {sn.id: sn for sn in start_nodes if sn.id != next_rec.id}
        assert t._doing == {sn.id: sn for sn in start_nodes if sn.id == next_rec.id}

    @pytest.mark.asyncio
    @patch("geneagrapher_core.traverse.LifecycleTracking.report_back")
    async def test_done(self, m_report_back) -> None:
        t = LifecycleTracking([TraverseItem(s.rid1, s.tda)])
        t._doing[s.rid2] = TraverseItem(s.rid2, s.tda)

        await t.done(s.rid2)
        assert t._doing == {}
        assert t._done == {s.rid2}
        m_report_back.assert_called_once_with()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("report_back", [None, AsyncMock()])
    async def test_report_back(self, report_back) -> None:
        t = LifecycleTracking([TraverseItem(s.rid1, s.tda)], report_back)

        assert await t.report_back() is None
        if report_back is not None:
            report_back.assert_called_once_with(1, 0, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "start_nodes,expected_info,expected_call_ids,expected_num_report_callbacks",
    [
        (
            [
                TraverseItem(RecordId(1), TraverseDirection.ADVISORS),
                TraverseItem(RecordId(2), TraverseDirection.ADVISORS),
            ],
            {
                "node_list": [1, 2, 3, 4],
            },
            [1, 2, 3, 4, 5],
            13,
        ),
        (
            [
                TraverseItem(RecordId(1), TraverseDirection.DESCENDANTS),
                TraverseItem(RecordId(2), TraverseDirection.ADVISORS),
            ],
            {
                "node_list": [1, 2, 3, 6, 7, 8],
            },
            [1, 2, 3, 5, 6, 7, 8, 9],
            22,
        ),
        (
            [
                TraverseItem(
                    RecordId(1),
                    TraverseDirection.ADVISORS | TraverseDirection.DESCENDANTS,
                ),
                TraverseItem(RecordId(2), TraverseDirection.ADVISORS),
            ],
            {
                "node_list": [1, 2, 3, 4, 6, 7, 8],
            },
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            25,
        ),
    ],
)
@patch("geneagrapher_core.traverse.asyncio.Semaphore")
@patch("geneagrapher_core.traverse.get_record_inner")
@patch("geneagrapher_core.traverse.ClientSession")
async def test_build_graph(
    m_client_session,
    m_get_record_inner,
    m_semaphore,
    start_nodes,
    expected_info,
    expected_call_ids,
    expected_num_report_callbacks,
) -> None:
    m_session = AsyncMock()
    m_client_session.return_value.__aenter__.return_value = m_session

    m_report_progress = AsyncMock()

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
        "nodes": {rid: testdata[rid] for rid in expected_info["node_list"]},
    }

    assert (
        await build_graph(
            start_nodes,
            max_concurrency=s.concurrency,
            cache=s.cache,
            report_progress=m_report_progress,
        )
        == expected
    )
    m_client_session.assert_called_once_with("https://www.mathgenealogy.org")
    m_semaphore.assert_called_once_with(s.concurrency)

    assert len(m_get_record_inner.call_args_list) == len(expected_call_ids)
    for c in [
        call(rid, m_session, m_semaphore.return_value, s.cache)
        for rid in expected_call_ids
    ]:
        assert c in m_get_record_inner.call_args_list

    # Check the reporting callback calls.
    assert len(m_report_progress.mock_calls) == expected_num_report_callbacks
    assert m_report_progress.call_args.args[1] == 0
    assert m_report_progress.call_args.args[2] == 0
    assert m_report_progress.call_args.args[3] == len(expected_call_ids)

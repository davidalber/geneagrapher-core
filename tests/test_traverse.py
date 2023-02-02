from geneagrapher_core.traverse import LifecycleTracking, build_graph
from geneagrapher_core.record import RecordId

import pytest
from unittest.mock import AsyncMock, call, patch, sentinel as s


class TestLifecycleTracking:
    def test_init(self) -> None:
        t = LifecycleTracking([s.i1, s.i2], s.report_back)
        assert t.todo == {s.i1, s.i2}
        assert t._doing == set()
        assert t._done == set()
        assert t._report_back == s.report_back

    @pytest.mark.parametrize(
        "todo,doing,expected",
        [
            ([], [], True),
            ([s.rid1], [], False),
            ([], [s.rid1], False),
            ([s.rid1], [s.rid2], False),
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
            ([s.rid1], 1),
            ([s.rid1, s.rid2], 2),
        ],
    )
    def test_num_todo(self, todo, expected):
        t = LifecycleTracking(todo)
        assert t.num_todo == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "start_nodes,new_node,final_todo",
        [
            ([1, 2], 1, {1, 2}),
            ([1, 2], 3, {1, 2, 3}),
        ],
    )
    @patch("geneagrapher_core.traverse.LifecycleTracking.report_back")
    async def test_create(
        self, m_report_back, start_nodes, new_node, final_todo
    ) -> None:
        t = LifecycleTracking(start_nodes)
        await t.create(new_node)
        assert t.todo == final_todo

    @pytest.mark.asyncio
    async def test_start_next(self) -> None:
        start_nodes = [RecordId(1), RecordId(2)]
        t = LifecycleTracking(start_nodes)

        next_rid = await t.start_next()
        assert next_rid in start_nodes
        assert t.todo == set(start_nodes) - set([next_rid])
        assert t._doing == set([next_rid])

    @pytest.mark.asyncio
    @patch("geneagrapher_core.traverse.LifecycleTracking.report_back")
    async def test_done(self, m_report_back) -> None:
        t = LifecycleTracking([s.sn1])
        t._doing.add(s.sn2)

        await t.done(s.sn2)
        assert t._doing == set()
        assert t._done == {s.sn2}
        m_report_back.assert_called_once_with()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("report_back", [None, AsyncMock()])
    async def test_report_back(self, report_back) -> None:
        t = LifecycleTracking([s.sn1], report_back)

        assert await t.report_back() is None
        if report_back is not None:
            report_back.assert_called_once_with(1, 0, 0)


@pytest.mark.asyncio
@patch("geneagrapher_core.traverse.get_record_inner")
@patch("geneagrapher_core.traverse.ClientSession")
async def test_build_graph(m_client_session, m_get_record_inner) -> None:
    m_session = AsyncMock()
    m_client_session.return_value.__aenter__.return_value = m_session

    m_report_progress = AsyncMock()
    start_nodes = [RecordId(1), RecordId(2)]

    testdata = {
        1: {
            "id": s.rec1,
            "advisors": [3, 4],
        },
        2: {
            "id": s.rec2,
            "advisors": [3, 5],
        },
        3: {
            "id": s.rec3,
            "advisors": [4],
        },
        4: {
            "id": s.rec4,
            "advisors": [],
        },
        5: None,
    }
    m_get_record_inner.side_effect = lambda record_id, client, cache: testdata[
        record_id
    ]

    expected = {
        "start_nodes": start_nodes,
        "nodes": {
            1: testdata[1],
            2: testdata[2],
            3: testdata[3],
            4: testdata[4],
        },
    }

    assert await build_graph(start_nodes, s.cache, m_report_progress) == expected
    m_client_session.assert_called_once_with("https://www.mathgenealogy.org")
    assert m_get_record_inner.call_args_list == [
        call(1, m_session, s.cache),
        call(2, m_session, s.cache),
        call(3, m_session, s.cache),
        call(4, m_session, s.cache),
        call(5, m_session, s.cache),
    ]

from geneagrapher_core.traverse import LifecycleTracking, build_graph
from geneagrapher_core.record import RecordId

import pytest
from unittest.mock import MagicMock, call, patch, sentinel as s


class TestLifecycleTracking:
    def test_init(self) -> None:
        t = LifecycleTracking([s.i1, s.i2], s.report_back)
        assert t.todo == {s.i1, s.i2}
        assert t._doing == set()
        assert t._done == set()
        assert t._report_back == s.report_back

    @pytest.mark.parametrize(
        "start_nodes,new_node,final_todo",
        [
            ([1, 2], 1, {1, 2}),
            ([1, 2], 3, {1, 2, 3}),
        ],
    )
    @patch("geneagrapher_core.traverse.LifecycleTracking.report_back")
    def test_create(self, m_report_back, start_nodes, new_node, final_todo) -> None:
        t = LifecycleTracking(start_nodes)
        t.create(new_node)
        assert t.todo == final_todo

    @patch("geneagrapher_core.traverse.LifecycleTracking.doing")
    def test_start_next(self, m_doing) -> None:
        start_nodes = [RecordId(1), RecordId(2)]
        t = LifecycleTracking(start_nodes)

        next_rid = t.start_next()
        assert next_rid in start_nodes
        assert t.todo == set(start_nodes) - set([next_rid])
        m_doing.assert_called_once_with(next_rid)

    @patch("geneagrapher_core.traverse.LifecycleTracking.report_back")
    def test_doing(self, m_report_back) -> None:
        t = LifecycleTracking([s.sn1])
        t.doing(s.sn2)
        assert t._doing == {s.sn2}
        m_report_back.assert_called_once_with()

    @patch("geneagrapher_core.traverse.LifecycleTracking.report_back")
    def test_done(self, m_report_back) -> None:
        t = LifecycleTracking([s.sn1])
        t._doing.add(s.sn2)

        t.done(s.sn2)
        assert t._doing == set()
        assert t._done == {s.sn2}
        m_report_back.assert_called_once_with()

    @pytest.mark.parametrize("report_back", [None, MagicMock()])
    def test_report_back(self, report_back) -> None:
        t = LifecycleTracking([s.sn1], report_back)

        assert t.report_back() is None
        if report_back is not None:
            report_back.assert_called_once_with(1, 0, 0)


@patch("geneagrapher_core.traverse.get_record")
def test_build_graph(m_get_record) -> None:
    m_report_progress = MagicMock()
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
    m_get_record.side_effect = lambda record_id, cache: testdata[record_id]

    expected = {
        "start_nodes": start_nodes,
        "nodes": {
            1: testdata[1],
            2: testdata[2],
            3: testdata[3],
            4: testdata[4],
        },
    }

    assert build_graph(start_nodes, s.cache, m_report_progress) == expected
    assert m_get_record.call_args_list == [
        call(1, s.cache),
        call(2, s.cache),
        call(3, s.cache),
        call(4, s.cache),
        call(5, s.cache),
    ]

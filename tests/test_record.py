from geneagrapher_core.record import (
    CacheResult,
    fetch_document,
    get_advisors,
    get_descendants,
    get_institution,
    get_name,
    get_record_inner,
    get_year,
    has_record,
)

from bs4 import BeautifulSoup
from glob import glob
import os
import pytest

try:
    import tomllib
except ModuleNotFoundError:
    # tomllib is only in Python >= 3.11
    # fall back to tomli
    import tomli as tomllib  # type: ignore
from unittest.mock import AsyncMock, patch, sentinel as s


CURR_DIR = os.path.dirname(os.path.abspath(__file__))
SEARCH_DIR = os.path.join(CURR_DIR, "testdata_records")


def load_toml(filename):
    with open(filename, "rb") as f:
        return tomllib.load(f)


def load_soup(filename):
    with open(filename, "r") as f:
        return BeautifulSoup(f, "html.parser")


def load_record_test(record_id):
    path_stub = os.path.join(SEARCH_DIR, record_id)
    return load_soup(f"{path_stub}.html"), load_toml(f"{path_stub}.toml")


def pytest_generate_tests(metafunc):
    if "test_record_ids" in metafunc.fixturenames:
        # Generate a list of the IDs of test records in the test data
        # directory.
        files = glob(os.path.join(SEARCH_DIR, "*.toml"))
        metafunc.parametrize(
            "test_record_ids", [f.removesuffix(".toml") for f in files]
        )


def test_has_record(test_record_ids) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert has_record(soup) is expected["is_valid"]


@pytest.mark.asyncio
@pytest.mark.parametrize("has_record", [False, True])
@pytest.mark.parametrize("cache_hit", [False, True])
@patch("geneagrapher_core.record.get_advisors")
@patch("geneagrapher_core.record.get_descendants")
@patch("geneagrapher_core.record.get_year")
@patch("geneagrapher_core.record.get_institution")
@patch("geneagrapher_core.record.get_name")
@patch("geneagrapher_core.record.has_record")
@patch("geneagrapher_core.record.fetch_document")
async def test_get_record_inner(
    m_fetch_document,
    m_has_record,
    m_get_name,
    m_get_institution,
    m_get_year,
    m_get_descendants,
    m_get_advisors,
    has_record,
    cache_hit,
) -> None:
    m_has_record.return_value = has_record
    m_soup = m_fetch_document.return_value

    m_cache = AsyncMock()
    m_cache.get.return_value = (
        (CacheResult.HIT, s.cache_record) if cache_hit else (CacheResult.MISS, None)
    )

    record = await get_record_inner(s.rid, s.client_session, m_cache)

    if cache_hit:
        assert record is s.cache_record
        m_fetch_document.assert_not_called()
        m_has_record.assert_not_called()
        m_get_name.assert_not_called()
        m_get_institution.assert_not_called()
        m_get_year.assert_not_called()
        m_get_descendants.assert_not_called()
        m_get_advisors.assert_not_called()
        m_cache.set.assert_not_called()

    else:
        m_fetch_document.assert_called_once_with(s.rid, s.client_session)
        m_has_record.assert_called_once_with(m_soup)

        if has_record:
            assert record == {
                "id": s.rid,
                "name": m_get_name.return_value,
                "institution": m_get_institution.return_value,
                "year": m_get_year.return_value,
                "descendants": m_get_descendants.return_value,
                "advisors": m_get_advisors.return_value,
            }

            m_get_name.assert_called_once_with(m_soup)
            m_get_institution.assert_called_once_with(m_soup)
            m_get_year.assert_called_once_with(m_soup)
            m_get_descendants.assert_called_once_with(m_soup)
            m_get_advisors.assert_called_once_with(m_soup)
        else:
            assert record is None

            m_get_name.assert_not_called()
            m_get_institution.assert_not_called()
            m_get_year.assert_not_called()
            m_get_descendants.assert_not_called()
            m_get_advisors.assert_not_called()

        m_cache.set.assert_called_once_with(s.rid, record)


@pytest.mark.asyncio
@patch("geneagrapher_core.record.BeautifulSoup")
@patch("geneagrapher_core.record.ClientSession")
async def test_fetch_document(m_client_session, m_bs) -> None:
    m_page = AsyncMock()
    m_client_session.get.return_value.__aenter__.return_value = m_page

    assert await fetch_document(s.rid, m_client_session) == m_bs.return_value
    m_client_session.get.assert_called_once_with("/id.php?id=sentinel.rid")
    m_bs.assert_called_once_with(m_page.text.return_value, "html.parser")


def test_get_name(test_record_ids) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_name(soup) == expected["name"]


def test_get_institution(test_record_ids) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_institution(soup) == expected.get("institution")


def test_get_year(test_record_ids) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_year(soup) == expected.get("year")


def test_get_descendants(test_record_ids) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_descendants(soup) == expected["descendants"]


def test_get_advisors(test_record_ids) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_advisors(soup) == expected["advisors"]

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

from .conftest import RECORD_TESTDATA_DIR, load_record_test

from glob import glob
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, sentinel as s


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "test_record_ids" in metafunc.fixturenames:
        # Generate a list of the IDs of test records in the test data
        # directory.
        files = glob(os.path.join(RECORD_TESTDATA_DIR, "*.toml"))
        metafunc.parametrize(
            "test_record_ids", [f.removesuffix(".toml") for f in files]
        )


def test_has_record(test_record_ids: str) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert has_record(soup) is expected["is_valid"]


@pytest.mark.asyncio
@pytest.mark.parametrize("has_record", [False, True])
@pytest.mark.parametrize("cache_hit", [False, True])
@pytest.mark.parametrize("semaphore_is_none", [False, True])
@patch("geneagrapher_core.record.get_advisors")
@patch("geneagrapher_core.record.get_descendants")
@patch("geneagrapher_core.record.get_year")
@patch("geneagrapher_core.record.get_institution")
@patch("geneagrapher_core.record.get_name")
@patch("geneagrapher_core.record.has_record")
@patch("geneagrapher_core.record.fetch_document")
@patch("geneagrapher_core.record.fake_semaphore")
async def test_get_record_inner(
    m_fake_semaphore: AsyncMock,
    m_fetch_document: AsyncMock,
    m_has_record: MagicMock,
    m_get_name: MagicMock,
    m_get_institution: MagicMock,
    m_get_year: MagicMock,
    m_get_descendants: MagicMock,
    m_get_advisors: MagicMock,
    semaphore_is_none: bool,
    has_record: bool,
    cache_hit: bool,
) -> None:
    m_has_record.return_value = has_record
    m_soup = m_fetch_document.return_value

    m_cache = AsyncMock()
    m_cache.get.return_value = (
        (CacheResult.HIT, s.cache_record) if cache_hit else (CacheResult.MISS, None)
    )

    m_http_semaphore = None if semaphore_is_none else AsyncMock()

    record = await get_record_inner(s.rid, s.client_session, m_http_semaphore, m_cache)

    if cache_hit:
        assert record is s.cache_record
        m_fake_semaphore.return_value.__aenter__.assert_not_called()
        if m_http_semaphore is not None:
            m_http_semaphore.__aenter__.assert_not_called()

        m_fetch_document.assert_not_called()
        m_has_record.assert_not_called()
        m_get_name.assert_not_called()
        m_get_institution.assert_not_called()
        m_get_year.assert_not_called()
        m_get_descendants.assert_not_called()
        m_get_advisors.assert_not_called()
        m_cache.set.assert_not_called()

    else:
        if m_http_semaphore is None:
            m_fake_semaphore.return_value.__aenter__.assert_called_once_with()
        else:
            m_http_semaphore.__aenter__.assert_called_once_with()
            m_fake_semaphore.return_value.__aenter__.assert_not_called()

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
async def test_fetch_document(m_client_session: MagicMock, m_bs: MagicMock) -> None:
    m_page = AsyncMock()
    m_client_session.get.return_value.__aenter__.return_value = m_page

    assert await fetch_document(s.rid, m_client_session) == m_bs.return_value
    m_client_session.get.assert_called_once_with("/id.php?id=sentinel.rid")
    m_bs.assert_called_once_with(m_page.text.return_value, "html.parser")


def test_get_name(test_record_ids: str) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_name(soup) == expected["name"]


def test_get_institution(test_record_ids: str) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_institution(soup) == expected.get("institution")


def test_get_year(test_record_ids: str) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_year(soup) == expected.get("year")


def test_get_descendants(test_record_ids: str) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_descendants(soup) == expected["descendants"]


def test_get_advisors(test_record_ids: str) -> None:
    soup, expected = load_record_test(test_record_ids)
    assert get_advisors(soup) == expected["advisors"]

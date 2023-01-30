from geneagrapher_core.record import fetch_document, get_record
from unittest.mock import MagicMock, patch, sentinel as s


@patch("geneagrapher_core.record.get_ancestors")
@patch("geneagrapher_core.record.get_descendants")
@patch("geneagrapher_core.record.get_year")
@patch("geneagrapher_core.record.get_institution")
@patch("geneagrapher_core.record.get_name")
@patch("geneagrapher_core.record.fetch_document")
def test_get_record(
    m_fetch_document,
    m_get_name,
    m_get_institution,
    m_get_year,
    m_get_descendants,
    m_get_ancestors,
) -> None:
    m_soup = m_fetch_document.return_value

    assert get_record(s.rid) == {
        "id": s.rid,
        "name": m_get_name.return_value,
        "institution": m_get_institution.return_value,
        "year": m_get_year.return_value,
        "descendants": m_get_descendants.return_value,
        "ancestors": m_get_ancestors.return_value,
    }

    m_fetch_document.assert_called_once_with(s.rid)
    m_get_name.assert_called_once_with(m_soup)
    m_get_institution.assert_called_once_with(m_soup)
    m_get_year.assert_called_once_with(m_soup)
    m_get_descendants.assert_called_once_with(m_soup)
    m_get_ancestors.assert_called_once_with(m_soup)


@patch("geneagrapher_core.record.BeautifulSoup")
@patch("geneagrapher_core.record.urllib")
def test_fetch_document(m_urllib, m_bs) -> None:
    m_page = MagicMock()
    m_urllib.request.urlopen.return_value.__enter__.return_value = m_page

    assert fetch_document(s.rid) == m_bs.return_value
    m_urllib.request.urlopen.assert_called_once_with(
        "https://www.mathgenealogy.org/id.php?id=sentinel.rid"
    )
    m_bs.assert_called_once_with(m_page, "html.parser")

from geneagrapher_core.record import fetch_document
from unittest.mock import MagicMock, patch, sentinel as s


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

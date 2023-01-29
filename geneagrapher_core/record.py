from bs4 import BeautifulSoup
from typing import NewType
import urllib.request

RecordId = NewType("RecordId", int)


def fetch_document(rid: RecordId) -> BeautifulSoup:
    with urllib.request.urlopen(
        f"https://www.mathgenealogy.org/id.php?id={rid}"
    ) as page:
        return BeautifulSoup(page, "html.parser")

from bs4 import BeautifulSoup
from typing import List, NewType, Optional, TypedDict
import urllib.request

RecordId = NewType("RecordId", int)


class Record(TypedDict):
    id: RecordId
    name: str
    institution: Optional[str]
    year: Optional[int]
    descendants: List[int]
    ancestors: List[int]


def get_record(record_id: RecordId) -> Record:
    soup: BeautifulSoup = fetch_document(record_id)

    result: Record = {
        "id": record_id,
        "name": get_name(soup),
        "institution": get_institution(soup),
        "year": get_year(soup),
        "descendants": get_descendants(soup),
        "ancestors": get_ancestors(soup),
    }

    return result


def fetch_document(rid: RecordId) -> BeautifulSoup:
    with urllib.request.urlopen(
        f"https://www.mathgenealogy.org/id.php?id={rid}"
    ) as page:
        return BeautifulSoup(page, "html.parser")


def get_name(soup: BeautifulSoup) -> str:
    return ""


def get_institution(soup: BeautifulSoup) -> Optional[str]:
    ...


def get_year(soup: BeautifulSoup) -> Optional[int]:
    ...


def get_descendants(soup: BeautifulSoup) -> List[int]:
    return []


def get_ancestors(soup: BeautifulSoup) -> List[int]:
    return []

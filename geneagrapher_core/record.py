from bs4 import BeautifulSoup, Tag
import re
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
    """Extract the mathematician name."""
    el = soup.find("h2")
    name = el.getText(strip=True) if el is not None else ""
    return re.sub(" {2,}", " ", name)  # remove redundant whitespace


def get_institution(soup: BeautifulSoup) -> Optional[str]:
    """Return institution name (or None, if there is no institution name)."""
    for inst in soup.findAll(
        "div", style="line-height: 30px; text-align: center; margin-bottom: 1ex"
    ):
        try:
            institution = inst.find("span").find("span").text
            if institution != "":
                return institution
        except AttributeError:
            pass
    return None


def get_year(soup: BeautifulSoup) -> Optional[int]:
    """Return graduation year (or None, if there is no graduation year).

    Rarely, a record has multiple years listed (e.g.,
    https://www.genealogy.math.ndsu.nodak.edu/id.php?id=131575). In
    this case, return the first year in the record.
    """
    for inst_year in soup.findAll(
        "div", style="line-height: 30px; text-align: center; margin-bottom: 1ex"
    ):
        try:
            year = inst_year.find("span").contents[-1].strip()
            if year != "":
                year = year.split(",")[  # this addresses records with multiple years
                    0
                ].strip()
                if year.isdigit():
                    return int(year)
        except AttributeError:
            pass

    return None


def extract_id(tag: Tag) -> int:
    """Extract the ID from a tag with form <a href="id.php?id=7401">."""
    return int(tag.attrs["href"].split("=")[-1])


def get_descendants(soup: BeautifulSoup) -> List[int]:
    """Return the list of descendants."""
    table = soup.find("table")
    if isinstance(table, Tag):
        return [extract_id(info) for info in table.findAll("a")]
    else:
        return []


def get_ancestors(soup: BeautifulSoup) -> List[int]:
    """Return the set of advisors.

    Rarely, a record has multiple groups of advisors (e.g.,
    https://www.mathgenealogy.org/id.php?id=17864). In this case,
    capture all of the advisors from all groups..
    """
    return [
        extract_id(info.findNext())
        for info in soup.findAll(string=re.compile("Advisor"))
        if "Advisor: Unknown" not in info
    ]

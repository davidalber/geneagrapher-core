from aiohttp import ClientSession
import asyncio
from bs4 import BeautifulSoup, Tag
from contextlib import asynccontextmanager
from enum import Enum, auto
import re
from typing import AsyncIterator, List, NewType, Optional, Protocol, Tuple, TypedDict

RecordId = NewType("RecordId", int)


class Record(TypedDict):
    id: RecordId
    name: str
    institution: Optional[str]
    year: Optional[int]
    descendants: List[int]
    advisors: List[int]


class CacheResult(Enum):
    HIT = auto()
    MISS = auto()


class Cache(Protocol):
    """This defines an interface that passed-in cache objects must implement."""

    async def get(self, id: RecordId) -> Tuple[CacheResult, Optional[Record]]:
        """Get a record from the cache.

        :param id: Math Genealogy Project ID of the record to retrieve
        """
        ...

    async def set(self, id: RecordId, value: Optional[Record]) -> None:
        """Store a record in the cache.

        :param id: Math Genealogy Project ID of the record to store
        :param value: the value to store
        """
        ...


@asynccontextmanager
async def fake_semaphore() -> AsyncIterator[None]:
    """If the caller to the `get_record*` functions below does not
    pass a semaphore, this async context manager, which does nothing,
    is used instead.
    """
    yield None


def has_record(soup: BeautifulSoup) -> bool:
    """Return True if the input tree contains a mathematician record
    and False otherwise.
    """
    if soup.string == "Non-numeric id supplied. Aborting.":
        # This is received, for instance, by going to
        # https://www.mathgenealogy.org/id.php?id=9999999999999999999999999.
        return False

    return (
        soup.p is not None
        and soup.p.string
        != "You have specified an ID that does not exist in the database. Please back \
up and try again."
    )


async def get_record(
    record_id: RecordId,
    cache: Optional[Cache] = None,
) -> Optional[Record]:
    """Get a single record. This is meant to be called for one-off
    requests. If the calling code is planning to get several records
    during its lifetime, it should instantiate a
    :class:`aiohttp.ClientSession` object as
    ``ClientSession("https://www.mathgenealogy.org")`` and call
    :func:`get_record_inner <get_record_inner>` instead.

    :param record_id: Math Genealogy Project ID of the record to retrieve
    :param cache: a cache object for getting and storing results

    **Example**::

        record = await get_record(RecordId(18231))

    """
    async with ClientSession("https://www.mathgenealogy.org") as client:
        return await get_record_inner(record_id, client, cache=cache)


async def get_record_inner(
    record_id: RecordId,
    client: ClientSession,
    http_semaphore: Optional[asyncio.Semaphore] = None,
    cache: Optional[Cache] = None,
) -> Optional[Record]:
    """Get a single record using the provided
    :class:`aiohttp.ClientSession` and :class:`asyncio.Semaphore`
    objects. This is useful when making several record requests.

    :param record_id: Math Genealogy Project ID of the record to retrieve
    :param client: a client session object with which to make HTTP requests
    :param http_semaphore: a semaphore to limit HTTP request concurrency
    :param cache: a cache object for getting and storing results

    """
    if cache:
        (status, record) = await cache.get(record_id)
        if status is CacheResult.HIT:
            return record

    async with http_semaphore or fake_semaphore():
        soup: BeautifulSoup = await fetch_document(record_id, client)

    if not has_record(soup):
        record = None
    else:
        record = {
            "id": record_id,
            "name": get_name(soup),
            "institution": get_institution(soup),
            "year": get_year(soup),
            "descendants": get_descendants(soup),
            "advisors": get_advisors(soup),
        }

    if cache:
        await cache.set(record_id, record)

    return record


async def fetch_document(rid: RecordId, client: ClientSession) -> BeautifulSoup:
    async with client.get(f"/id.php?id={rid}") as resp:
        return BeautifulSoup(await resp.text(), "html.parser")


def get_name(soup: BeautifulSoup) -> str:
    """Extract the mathematician name."""
    el = soup.find("h2")
    name = el.get_text(strip=True) if el is not None else ""
    return re.sub(" {2,}", " ", name)  # remove redundant whitespace


def get_institution(soup: BeautifulSoup) -> Optional[str]:
    """Return institution name (or None, if there is no institution name)."""
    for inst in soup.find_all(
        "div", style="line-height: 30px; text-align: center; margin-bottom: 1ex"
    ):
        try:
            institution: str = inst.find("span").find("span").text
            if institution != "":
                return institution
        except AttributeError:
            pass
    return None


def get_year(soup: BeautifulSoup) -> Optional[int]:
    """Return graduation year (or None, if there is no graduation year).

    Rarely, a record has multiple years listed (e.g.,
    https://www.mathgenealogy.org/id.php?id=131575). In this case,
    return the first year in the record.
    """
    for inst_year in soup.find_all(
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
        return [extract_id(info) for info in table.find_all("a")]
    else:
        return []


def get_advisors(soup: BeautifulSoup) -> List[int]:
    """Return the set of advisors.

    Rarely:
      - A record has multiple groups of advisors (e.g.,
        https://www.mathgenealogy.org/id.php?id=17864). In this case,
        capture all of the advisors from all groups.
      - A record has promotors and co-promotors (e.g.,
        https://www.mathgenealogy.org/id.php?id=51506). Capture
        promotors and co-promotors as advisors.
    """
    return [
        extract_id(info.find_next())
        for info in soup.find_all(string=re.compile("(Advisor|Promotor)"))
        if "Advisor: Unknown" not in info
    ]

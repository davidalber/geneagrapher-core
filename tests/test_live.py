"""This file contains tests that request pages from the Math Genealogy
Project (as opposed to only using stored test data).
"""
from geneagrapher_core.record import RecordId, get_record

from .conftest import load_record_test

import pytest


@pytest.mark.asyncio
@pytest.mark.live
@pytest.mark.parametrize("record_id", (18231,))
async def test_still_works(record_id: int) -> None:
    """Compare the computed record for a given `record_id` to stored data."""
    _, expected = load_record_test(str(record_id))

    # Clean the test data up a bit to make it look like a record.
    del expected["is_valid"]
    expected["id"] = record_id

    assert await get_record(RecordId(record_id)) == expected

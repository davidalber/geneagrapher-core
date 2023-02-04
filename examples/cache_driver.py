"""This example demonstrates a simple cache using Redis.

In order to run this, you will need to install the redis package into
your Python environment and run a Redis instance on your development
machine. You can accomplish this by doing
`poetry install --with examples`.

A couple notes:

1. This example does not specify any TTLs for data that is cached. A
   more complete implementation probably should do that.
2. This example does not take any command-line arguments to control
   the graph that is being built. It simply hardcodes a starting
   record ID. A general driver would want to accept the starting
   record IDs as input.

Running:
```
$ poetry run python cache_driver.py

# If you want to see nicer output and have jq installed.
$ poetry run python cache_driver.py | jq

# If you want to see the progress bar either redirect output to a file
# or /dev/null.
$ poetry run python cache_driver.py > /dev/null
```

"""

from geneagrapher_core.record import CacheResult, Record, RecordId
from geneagrapher_core.traverse import build_graph

import asyncio
import json
import redis.asyncio as redis
import sys
from typing import Optional, Tuple


class RedisCache:
    def __init__(self):
        self.r = redis.Redis(host="localhost", port=6379, db=0)

    def key(self, id: RecordId):
        return f"ggrapher::{id}"

    async def get(self, id: RecordId) -> Tuple[CacheResult, Optional[Record]]:
        val = await self.r.get(self.key(id))

        if val is None:
            # Miss
            return (CacheResult.MISS, None)
        elif val == {}:
            # A null-value hit
            return (CacheResult.HIT, None)
        else:
            # General hit
            return (CacheResult.HIT, json.loads(val))

    async def set(self, id: RecordId, value: Optional[Record]) -> None:
        val = {} if value is None else value
        await self.r.set(self.key(id), json.dumps(val))


def display_progress(queued, doing, done):
    prefix = "Progress: "
    size = 60
    count = queued + doing + done

    x = int(size * done / count)
    y = int(size * doing / count)

    print(
        f"{prefix}[{u'█'*x}{u':'*y}{('.'*(size - x - y))}] {done}/{count}",
        end="\r",
        file=sys.stderr,
        flush=True,
    )


async def get_progress(
    tg: asyncio.TaskGroup, to_fetch: int, fetching: int, fetched: int
) -> None:
    display_progress(to_fetch, fetching, fetched)


if __name__ == "__main__":
    cache = RedisCache()
    ggraph = asyncio.run(
        build_graph([RecordId(18231)], cache=cache, report_progress=get_progress)
    )

    print(file=sys.stderr)  # this adds a newline to the progress bar
    print(json.dumps(ggraph))

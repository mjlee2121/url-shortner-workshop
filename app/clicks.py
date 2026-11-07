"""Milestone 5: move buffered click counts from Redis into Postgres in batches.

Why buffer at all? Think about what `UPDATE ... clicks = clicks + 1` on EVERY redirect
would do to the hottest, read-mostly path in the service.
"""

from __future__ import annotations

import asyncio
import logging

import asyncpg

from . import repository  # noqa: F401
from .cache import Cache

log = logging.getLogger(__name__)


async def flush_clicks(pool: asyncpg.Pool, cache: Cache) -> int:
    """Write buffered counts to Postgres. Return how many links were updated.

    TODO(M5):
      counts = await cache.take_pending_clicks(); return 0 if empty
      try: write them with repository.add_clicks_batch(conn, counts)
      except: put them back with cache.restore_pending_clicks(counts), then re-raise
      return len(counts)
    """
    raise NotImplementedError("TODO(M5): flush_clicks")


async def run_flusher(pool: asyncpg.Pool, cache: Cache, interval_seconds: float) -> None:
    """Flush forever until cancelled at shutdown. (Given: nothing to do here.)"""
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            flushed = await flush_clicks(pool, cache)
            if flushed:
                log.info("flushed clicks for %d links", flushed)
        except Exception:
            log.exception("click flush failed; will retry next interval")

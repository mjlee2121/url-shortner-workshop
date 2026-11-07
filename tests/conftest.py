"""Shared test setup for every milestone.

Milestones 1-2 run fully in memory. From Milestone 3 on, the tests need
PostgreSQL and Redis:  docker compose up -d db redis
"""

from __future__ import annotations

import os

import pytest

# Point the app at TEST resources before it is imported:
# a separate database and Redis database 15, so tests never touch dev data.
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/urldb_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("CLICK_FLUSH_INTERVAL_SECONDS", "3600")  # tests flush clicks explicitly
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "1000")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

URL = "https://example.com/some/very/long/path?with=query"


async def _reset(app) -> None:
    """Start every test from empty storage."""
    if hasattr(app.state, "pool"):
        async with app.state.pool.acquire() as conn:
            await conn.execute("TRUNCATE urls RESTART IDENTITY")
    if hasattr(app.state, "cache"):
        await app.state.cache.client.flushdb()


@pytest.fixture
def client():
    # Entering the TestClient runs the app's lifespan (startup), and leaving it runs shutdown.
    with TestClient(app, follow_redirects=False) as c:
        c.portal.call(_reset, app)
        yield c


@pytest.fixture
def pg_client(client):
    if not hasattr(client.app.state, "pool"):
        pytest.skip("Milestone 3 not done yet: the app has no app.state.pool")
    return client


@pytest.fixture
def cache_client(pg_client):
    if not hasattr(pg_client.app.state, "cache"):
        pytest.skip("Milestone 4 not done yet: the app has no app.state.cache")
    return pg_client


def run(client: TestClient, fn, *args):
    """Run an async function on the app's event loop (where the pool and Redis client live)."""
    return client.portal.call(fn, *args)


def shorten(client: TestClient, **body):
    return client.post("/shorten", json={"url": URL, **body})

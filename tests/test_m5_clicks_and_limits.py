"""Milestone 5: buffered clicks, rate limiting, graceful degradation. Needs: docker compose up -d db redis"""

from dataclasses import replace

from redis.asyncio import Redis

from app import clicks
from app.cache import Cache
from tests.conftest import run, shorten


def _db_clicks(client, code):
    async def q():
        async with client.app.state.pool.acquire() as conn:
            return await conn.fetchval("SELECT clicks FROM urls WHERE code = $1", code)

    return run(client, q)


def test_clicks_are_buffered_then_flushed_without_double_counting(cache_client):
    code = shorten(cache_client).json()["code"]
    for _ in range(3):
        cache_client.get(f"/{code}")

    assert _db_clicks(cache_client, code) == 0                       # nothing written yet
    assert cache_client.get(f"/stats/{code}").json()["clicks"] == 3  # but /stats adds the buffer

    run(cache_client, clicks.flush_clicks, cache_client.app.state.pool, cache_client.app.state.cache)

    assert _db_clicks(cache_client, code) == 3
    assert cache_client.get(f"/stats/{code}").json()["clicks"] == 3


def test_stats_for_unknown_code_is_404(cache_client):
    assert cache_client.get("/stats/missing").status_code == 404


def test_redirects_keep_working_when_redis_is_down(cache_client):
    code = shorten(cache_client).json()["code"]
    real = cache_client.app.state.cache
    dead = Redis.from_url("redis://localhost:6390/0", socket_connect_timeout=0.2,
                          socket_timeout=0.2, decode_responses=True)
    cache_client.app.state.cache = Cache(dead, 3600, 60)
    try:
        assert cache_client.get(f"/{code}").status_code == 302
        h = cache_client.get("/health").json()
        assert h["redis"] == "disconnected" and h["database"] == "connected"
    finally:
        cache_client.app.state.cache = real
        run(cache_client, dead.aclose)
    assert _db_clicks(cache_client, code) == 1  # the click went straight to Postgres


def test_rate_limit_on_shorten(cache_client):
    original = cache_client.app.state.settings
    cache_client.app.state.settings = replace(original, rate_limit_per_minute=2)
    try:
        assert shorten(cache_client).status_code == 201
        assert shorten(cache_client).status_code == 201
        assert shorten(cache_client).status_code == 429
    finally:
        cache_client.app.state.settings = original

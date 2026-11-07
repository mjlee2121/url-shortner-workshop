"""Milestone 4: Redis cache-aside. Needs: docker compose up -d db redis"""

from app.cache import GONE, NOT_FOUND
from tests.conftest import URL, run, shorten


def test_second_redirect_is_served_from_redis(cache_client):
    code = shorten(cache_client).json()["code"]
    cache_client.get(f"/{code}")  # miss: Postgres, then cached

    async def delete_row_behind_the_cache():
        async with cache_client.app.state.pool.acquire() as conn:
            await conn.execute("DELETE FROM urls WHERE code = $1", code)

    run(cache_client, delete_row_behind_the_cache)
    # Postgres no longer has the row, so a 302 proves Redis answered
    assert cache_client.get(f"/{code}").status_code == 302


def test_not_found_is_negatively_cached(cache_client):
    assert cache_client.get("/nope123").status_code == 404
    assert run(cache_client, cache_client.app.state.cache.client.get, "url:nope123") == NOT_FOUND


def test_creating_a_link_clears_a_cached_404(cache_client):
    assert cache_client.get("/mylink").status_code == 404
    assert shorten(cache_client, custom_code="mylink").status_code == 201
    assert cache_client.get("/mylink").status_code == 302


def test_cache_ttl_never_outlives_the_link(cache_client):
    code = shorten(cache_client, expires_in_days=1).json()["code"]
    cache_client.get(f"/{code}")
    ttl = run(cache_client, cache_client.app.state.cache.client.ttl, f"url:{code}")
    assert 0 < ttl <= 86_400


def test_expired_answer_is_cached(cache_client):
    async def insert_expired():
        async with cache_client.app.state.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO urls (code, original_url, expires_at) VALUES ('old2', $1, now() - interval '1 hour')",
                URL,
            )

    run(cache_client, insert_expired)
    assert cache_client.get("/old2").status_code == 410
    assert run(cache_client, cache_client.app.state.cache.client.get, "url:old2") == GONE


def test_delete_invalidates_the_cache(cache_client):
    code = shorten(cache_client).json()["code"]
    cache_client.get(f"/{code}")
    assert cache_client.delete(f"/{code}").status_code == 204
    assert cache_client.get(f"/{code}").status_code == 404

"""Milestone 3: PostgreSQL is the source of truth. Needs: docker compose up -d db redis"""

from fastapi.testclient import TestClient

from app.codes import code_for_id
from app.main import app
from tests.conftest import URL, run, shorten


def test_links_survive_a_restart(pg_client):
    code = shorten(pg_client).json()["code"]
    # leaving a TestClient shuts the app down; a new one starts it again
    with TestClient(app, follow_redirects=False) as restarted:
        assert restarted.get(f"/{code}").status_code == 302


def test_migration_is_recorded_once(pg_client):
    async def versions():
        async with pg_client.app.state.pool.acquire() as conn:
            return [r["version"] for r in await conn.fetch("SELECT version FROM schema_migrations")]

    assert run(pg_client, versions).count("001_create_urls") == 1


def test_uniqueness_is_enforced_by_the_database(pg_client):
    async def insert_behind_the_api():
        async with pg_client.app.state.pool.acquire() as conn:
            await conn.execute("INSERT INTO urls (code, original_url) VALUES ('taken1', $1)", URL)

    run(pg_client, insert_behind_the_api)
    assert shorten(pg_client, custom_code="taken1").status_code == 409


def test_generated_code_skips_a_colliding_custom_code(pg_client):
    async def plant_collision():
        async with pg_client.app.state.pool.acquire() as conn:
            # a custom link that happens to equal the code id 1 would get
            await conn.execute(
                "INSERT INTO urls (id, code, original_url) VALUES (999999, $1, $2)", code_for_id(1), URL
            )

    run(pg_client, plant_collision)
    r = shorten(pg_client)
    assert r.status_code == 201
    assert r.json()["code"] != code_for_id(1)


def test_expired_link_returns_410(pg_client):
    async def insert_expired():
        async with pg_client.app.state.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO urls (code, original_url, expires_at) VALUES ('old1', $1, now() - interval '1 day')",
                URL,
            )

    run(pg_client, insert_expired)
    assert pg_client.get("/old1").status_code == 410


def test_expiry_is_returned_and_validated(pg_client):
    r = shorten(pg_client, expires_in_days=7)
    assert r.status_code == 201 and r.json()["expires_at"] is not None
    assert shorten(pg_client, expires_in_days=0).status_code == 422
    assert shorten(pg_client, expires_in_days=366).status_code == 422


def test_health_reports_the_database(pg_client):
    assert pg_client.get("/health").json()["database"] == "connected"

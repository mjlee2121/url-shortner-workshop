"""Milestone 1: FastAPI basics. Works with in-memory storage (and keeps working later)."""

from tests.conftest import URL, shorten


def test_health_is_not_shadowed_by_the_code_route(client):
    r = client.get("/health")
    assert r.status_code == 200, "Is GET /health declared BEFORE GET /{code}?"
    assert r.json()["status"] == "ok"


def test_shorten_returns_201_with_a_code(client):
    r = shorten(client)
    assert r.status_code == 201
    body = r.json()
    assert body["code"]
    assert body["short_url"].endswith("/" + body["code"])
    assert body["original_url"] == URL


def test_redirect_is_a_302_to_the_original_url(client):
    code = shorten(client).json()["code"]
    r = client.get(f"/{code}")
    assert r.status_code == 302, "Use 302, not 301 (why? see Milestone 1)"
    assert r.headers["location"] == URL


def test_unknown_code_is_404(client):
    assert client.get("/doesnotexist").status_code == 404


def test_invalid_urls_are_rejected_with_422(client):
    assert client.post("/shorten", json={"url": "not a url"}).status_code == 422
    assert client.post("/shorten", json={"url": "javascript:alert(1)"}).status_code == 422


def test_custom_code_works_and_duplicates_get_409(client):
    r = shorten(client, custom_code="my-link")
    assert r.status_code == 201 and r.json()["code"] == "my-link"
    assert client.get("/my-link").headers["location"] == URL
    assert shorten(client, custom_code="my-link").status_code == 409


def test_bad_or_reserved_custom_codes_get_422(client):
    assert shorten(client, custom_code="ab").status_code == 422          # too short
    assert shorten(client, custom_code="has space").status_code == 422   # bad characters
    assert shorten(client, custom_code="health").status_code == 422      # would shadow a route
    assert shorten(client, custom_code="Stats").status_code == 422       # reserved, any case


def test_delete_then_404(client):
    code = shorten(client).json()["code"]
    assert client.delete(f"/{code}").status_code == 204
    assert client.get(f"/{code}").status_code == 404
    assert client.delete(f"/{code}").status_code == 404

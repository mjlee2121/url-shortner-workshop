"""URL Shortener API: the file you grow, milestone by milestone.

M1  in-memory storage (a dict on app.state), the endpoints, status codes
M2  generated codes come from codes.code_for_id()
M3  replace the dict with PostgreSQL (db.py, repository.py, migrations/)
M4  put Redis in front of the redirect (cache.py): cache-aside
M5  buffered clicks (clicks.py), GET /stats/{code}, rate limiting, graceful degradation

Search for "TODO(M1)", "TODO(M2)", ... to find your work for each milestone.
Each TODO says WHAT to build; the study guide explains WHY.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone  # noqa: F401  (you'll need these from M3)

from fastapi import FastAPI, HTTPException, Request, Response, status  # noqa: F401
from fastapi.responses import JSONResponse, RedirectResponse  # noqa: F401

from .config import Settings
from .schemas import ShortenRequest, ShortenResponse, StatsResponse

# Imports you'll add later:
#   M2: from .codes import code_for_id
#   M3: import asyncpg; from . import db, repository
#   M4: from redis.asyncio import Redis; from .cache import GONE, NOT_FOUND, Cache
#   M5: import asyncio; from contextlib import suppress; from . import clicks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once at startup (everything before `yield`) and once at shutdown (after it)."""
    app.state.settings = Settings.from_env()

    # Milestone 1 storage: code -> {"original_url": str, "expires_at": datetime | None}
    app.state.urls = {}
    app.state.next_id = 1

    # TODO(M3): replace the two lines above with a PostgreSQL connection pool:
    #     app.state.pool = await db.create_pool(settings.database_url)
    #     await db.run_migrations(app.state.pool)
    #   and close the pool after `yield`. (The tests detect M3 by app.state.pool existing.)
    # TODO(M4): create a Redis client with SHORT timeouts (0.5 s) and set app.state.cache = Cache(...).
    #   Why short timeouts? What would a 30-second Redis timeout do to every redirect?
    # TODO(M5): start clicks.run_flusher(...) with asyncio.create_task; at shutdown cancel it
    #   and flush one last time so the last few seconds of clicks aren't lost.
    yield


app = FastAPI(title="URL Shortener API", lifespan=lifespan)


# ROUTE ORDER MATTERS. FastAPI tries routes in the order they are declared,
# so the fixed paths (/health, /stats/..., /shorten) stay ABOVE the catch-all /{code}.
# Exercise: once M1 passes, move /health below /{code}, run the tests, and explain what broke.


@app.get("/health")
async def health(request: Request):
    # TODO(M1): return {"status": "ok"}
    # TODO(M3): also run `SELECT 1` and report "database": "connected" / "disconnected".
    #   Database down -> return JSONResponse(..., status_code=503).
    # TODO(M4): also report "redis": "connected" / "disconnected" using cache.ping().
    #   Redis down is NOT a 503. Why not?
    raise NotImplementedError("TODO(M1): GET /health")


@app.post("/shorten", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED)
async def shorten(req: ShortenRequest, request: Request):
    # TODO(M1):
    #   1. original = str(req.url)
    #   2. If req.custom_code is set, that's the code; if it's already in app.state.urls -> HTTPException(409).
    #      Otherwise code = str(app.state.next_id), then add 1 to next_id.
    #   3. Save {"original_url": original, "expires_at": None} under the code.
    #   4. Return ShortenResponse(code=..., short_url=f"{base_url}/{code}", original_url=original),
    #      where base_url = request.app.state.settings.base_url
    # TODO(M2): generated codes become code_for_id(next_id).
    #   If a custom code already equals that value, take the next id. Why can that happen at all?
    # TODO(M3): expires_at = now(UTC) + timedelta(days=req.expires_in_days) when it's set.
    #   Custom code: repository.insert(...) returning None means "taken" -> 409.
    #   Generated code: loop up to 5 times: id = repository.next_id(conn), insert with code_for_id(id).
    # TODO(M4): after a successful insert, cache.invalidate(code). Why? (Hint: negative caching.)
    # TODO(M5): FIRST, rate-limit by client IP: cache.allow(f"shorten:{ip}", limit) is False -> 429.
    raise NotImplementedError("TODO(M1): POST /shorten")


@app.get("/stats/{code}", response_model=StatsResponse)
async def stats(code: str, request: Request):
    # TODO(M5): 404 if the code is unknown.
    #   clicks = clicks already in Postgres + clicks still buffered in Redis (cache.pending_clicks).
    raise NotImplementedError("TODO(M5): GET /stats/{code}")


@app.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(code: str, request: Request):
    # TODO(M1): 404 if unknown; otherwise remove it and return Response(status_code=204).
    # TODO(M3): repository.delete_by_code(...) returning False -> 404.
    # TODO(M4): delete from Postgres FIRST, then cache.invalidate(code). Why that order and not the reverse?
    # TODO(M5): also cache.drop_pending_clicks(code).
    raise NotImplementedError("TODO(M1): DELETE /{code}")


@app.get("/{code}")
async def redirect(code: str, request: Request):
    # TODO(M1): 404 if unknown; else RedirectResponse(original_url, status_code=302).
    #   Why 302 and not 301? (You'll need the answer for M5.)
    # TODO(M3): read the row with repository.get_by_code; expires_at <= now(UTC) -> 410 Gone.
    # TODO(M4): cache-aside.
    #   cached = await cache.get_url(code)
    #     NOT_FOUND -> 404, GONE -> 410, a URL -> redirect (no database query!)
    #   On a miss: Postgres. Not found -> cache.set_negative(code, NOT_FOUND) -> 404.
    #   Expired -> cache.set_negative(code, GONE) -> 410.
    #   Found -> cache.set_url(code, url, expires_at), then redirect.
    # TODO(M5): count the click: cache.record_click(code); if that returns False (Redis down),
    #   write it straight to Postgres with repository.increment_clicks. Never fail a redirect over a counter.
    raise NotImplementedError("TODO(M1): GET /{code}")

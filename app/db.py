"""Milestone 3: PostgreSQL connection pool and migration runner.

Why a pool: opening a Postgres connection costs a network round trip plus
authentication. A pool keeps a few connections open and lends one to each request.
"""

from __future__ import annotations

from pathlib import Path

import asyncpg

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
MIGRATION_LOCK_ID = 7_243_001  # any constant; every copy of the app must use the same one


async def create_pool(dsn: str) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn, min_size=1, max_size=10, command_timeout=5)


async def run_migrations(pool: asyncpg.Pool) -> list[str]:
    """Apply every migrations/*.sql file that hasn't run yet, in name order. Return the ones applied.

    TODO(M3): inside `async with pool.acquire() as conn:`
      1. Take a Postgres advisory lock: await conn.execute("SELECT pg_advisory_lock($1)", MIGRATION_LOCK_ID)
         (Why? Picture two copies of the app starting at the same second.)
      2. In try/finally (always unlock with pg_advisory_unlock in `finally`):
         a. CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY,
                                                          applied_at TIMESTAMPTZ NOT NULL DEFAULT now())
         b. Read the versions already applied.
         c. For each path in sorted(MIGRATIONS_DIR.glob("*.sql")) not yet applied (version = path.stem):
              async with conn.transaction():       # why one transaction per file?
                  run path.read_text(), then INSERT its version into schema_migrations
    Running this twice must change nothing the second time (the M3 tests restart the app).
    """
    raise NotImplementedError("TODO(M3): run_migrations")

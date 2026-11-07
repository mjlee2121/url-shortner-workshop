"""Milestone 3 (and one function in M5): every SQL query the service runs, in one place.

Rule: always pass values as $1, $2 parameters, never with f-strings. Why?
(Try to explain what an f-string would let `custom_code = "x'; DROP TABLE urls; --"` do.)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import asyncpg

COLUMNS = "id, code, original_url, is_custom, clicks, created_at, expires_at"


@dataclass(frozen=True)
class UrlRecord:
    id: int
    code: str
    original_url: str
    is_custom: bool
    clicks: int
    created_at: datetime
    expires_at: datetime | None

    @classmethod
    def from_row(cls, row: asyncpg.Record) -> "UrlRecord":
        return cls(**dict(row))


async def next_id(conn: asyncpg.Connection) -> int:
    """Reserve the next id from the table's sequence.

    TODO(M3): SELECT nextval(pg_get_serial_sequence('urls', 'id'))  (use conn.fetchval)
    Why is a sequence safe even with many app copies running at once?
    """
    raise NotImplementedError("TODO(M3): next_id")


async def insert(
    conn: asyncpg.Connection,
    *,
    code: str,
    original_url: str,
    expires_at: datetime | None,
    is_custom: bool,
    id: int | None = None,
) -> UrlRecord | None:
    """Insert a link. Return the new UrlRecord, or None if the code is already taken.

    TODO(M3): ONE statement:
        INSERT INTO urls (id, code, original_url, expires_at, is_custom)
        VALUES (COALESCE($1, nextval(pg_get_serial_sequence('urls', 'id'))), $2, $3, $4, $5)
        ON CONFLICT (code) DO NOTHING
        RETURNING <COLUMNS>
    No row back = conflict. Why is this better than "SELECT to check, then INSERT"?
    """
    raise NotImplementedError("TODO(M3): insert")


async def get_by_code(conn: asyncpg.Connection, code: str) -> UrlRecord | None:
    """TODO(M3): SELECT the row by code; None if there is none."""
    raise NotImplementedError("TODO(M3): get_by_code")


async def delete_by_code(conn: asyncpg.Connection, code: str) -> bool:
    """TODO(M3): DELETE ... RETURNING id; True if a row was deleted."""
    raise NotImplementedError("TODO(M3): delete_by_code")


async def increment_clicks(conn: asyncpg.Connection, code: str, by: int = 1) -> None:
    """TODO(M5): UPDATE urls SET clicks = clicks + $2 WHERE code = $1  (the fallback when Redis is down)"""
    raise NotImplementedError("TODO(M5): increment_clicks")


async def add_clicks_batch(conn: asyncpg.Connection, counts: dict[str, int]) -> None:
    """Apply many click counts in ONE statement.

    TODO(M5): do nothing if counts is empty; otherwise
        UPDATE urls SET clicks = urls.clicks + batch.n
        FROM unnest($1::text[], $2::bigint[]) AS batch(code, n)
        WHERE urls.code = batch.code
    with list(counts.keys()) and list(counts.values()).
    Why one statement instead of a loop of UPDATEs?
    """
    raise NotImplementedError("TODO(M5): add_clicks_batch")

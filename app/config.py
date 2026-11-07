"""Settings read from environment variables (12-factor config).

The same Docker image runs locally, in CI and in production; only the
environment changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    base_url: str
    cache_ttl_seconds: int          # how long a hot link stays in Redis
    negative_cache_ttl_seconds: int # how long "not found" / "expired" answers are cached
    rate_limit_per_minute: int      # max POST /shorten requests per client IP per minute
    click_flush_interval_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/urldb"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            base_url=os.getenv("BASE_URL", "http://localhost:8000").rstrip("/"),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "3600")),
            negative_cache_ttl_seconds=int(os.getenv("NEGATIVE_CACHE_TTL_SECONDS", "60")),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "30")),
            click_flush_interval_seconds=float(os.getenv("CLICK_FLUSH_INTERVAL_SECONDS", "10")),
        )

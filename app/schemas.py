"""Request and response models. Pydantic validates input BEFORE your endpoint code runs.

Milestone 1: fill in the two validators.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

# Paths the API itself uses. Why must a custom code never equal one of these?
RESERVED_CODES = {"shorten", "stats", "health", "docs", "redoc", "openapi"}
CUSTOM_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,30}$")
MAX_URL_LENGTH = 2048


class ShortenRequest(BaseModel):
    # HttpUrl only accepts http:// and https:// URLs.
    # Question: what would go wrong if we accepted "javascript:alert(1)" and redirected to it?
    url: HttpUrl
    custom_code: str | None = Field(default=None, description="3-30 letters, digits, '-' or '_'")
    expires_in_days: int | None = Field(default=None, ge=1, le=365)

    @field_validator("url")
    @classmethod
    def url_not_too_long(cls, v: HttpUrl) -> HttpUrl:
        # TODO(M1): raise ValueError if str(v) is longer than MAX_URL_LENGTH.
        #   (Raising ValueError inside a validator makes FastAPI answer 422 for you.)
        return v

    @field_validator("custom_code")
    @classmethod
    def valid_custom_code(cls, v: str | None) -> str | None:
        # TODO(M1):
        #   - None is allowed (no custom code requested)
        #   - must fully match CUSTOM_CODE_PATTERN, else ValueError
        #   - v.lower() must not be in RESERVED_CODES, else ValueError ("Stats" is reserved too)
        return v


class ShortenResponse(BaseModel):
    code: str
    short_url: str
    original_url: str
    expires_at: datetime | None = None


class StatsResponse(BaseModel):
    code: str
    short_url: str
    original_url: str
    clicks: int
    created_at: datetime
    expires_at: datetime | None = None

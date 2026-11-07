# URL Shortener Workshop

Rebuild a production-style URL shortener (FastAPI, PostgreSQL, Redis, Docker, CI) milestone by milestone.
The study guide ("URL Shortener: Build It Yourself") explains each milestone and why it's built that way.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest                         # all red/skipped at the start: that's expected
```

From Milestone 3 on, start the databases first: `docker compose up -d db redis`
(run `docker compose down -v` once beforehand if you used this folder with Docker before).

## Milestones

| # | What you build | Where the TODOs are | Done when |
|---|----------------|---------------------|-----------|
| 0 | Requirements and estimates | the section below | written |
| 1 | FastAPI basics, in memory | `app/main.py`, `app/schemas.py` | `pytest tests/test_m1_api.py` passes |
| 2 | Short codes (base62 + scramble) | `app/codes.py`, `app/main.py` | `pytest tests/test_m2_codes.py` passes |
| 3 | PostgreSQL | `app/db.py`, `app/migrations/`, `app/repository.py`, `app/main.py` | `pytest tests/test_m3_postgres.py` passes |
| 4 | Redis cache-aside | `app/cache.py`, `app/main.py` | `pytest tests/test_m4_cache.py` passes |
| 5 | Clicks, rate limits, degradation | `app/cache.py`, `app/clicks.py`, `app/repository.py`, `app/main.py` | `pytest tests/test_m5_clicks_and_limits.py` passes |
| 6 | Docker and CI | `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` | `docker compose up --build` works; CI is green |
| 7 | Interview drill | `ANSWERS.md`, your own notes | you can explain every decision out loud |

Tests for milestones you haven't reached are **skipped**, not failed. After each milestone, run the whole suite:
earlier milestones must keep passing.

Find your work with: `grep -rn "TODO(M3)" app/`

## Milestone 0: Requirements (fill this in before writing code)

**Functional requirements**

Read should be very fast compared to Write. Read happens 10 times more than write, so the redirect is what needs to be optimized. The link should be 
- 

**Non-functional requirements**

Must have: No duplicated links. Correctedness. When the link is expired, it should be removed or stop working.
Nice to have: click statistics and be delayed 1-2 seconds. The custom code that a user wants is just a nice-to-have
- 

**Back-of-envelope:** 

if 1 million links are created per month and each is clicked 100 times on average,
how many redirects per second is that on average? What does that ratio tell you about where to optimize?
that's 1mil * 100 = 100 mil clicks per month. 1 months has 2,600,000 seconds. So 100 mil / 2,600,000 = 40 click/sec. Whereas creating a link happens 4 times / sec. Write should be buffered and read should be cached.
- 

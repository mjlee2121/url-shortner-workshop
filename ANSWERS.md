# Model answers to the "Explain it" questions

Write your own answer first, out loud or on paper, then compare. These are model answers, not the only correct ones; an interviewer cares that your reasoning holds up, not that your wording matches.

---

## Milestone 0: Requirements

**1. What's the read/write ratio, and how does it shape the design?**
A link is created once and clicked many times, often around 100 reads per write. So the redirect (`GET /{code}`) is the path to optimize: it should usually avoid the database (cache), never wait on a write (buffered clicks), and stay fast even when parts fail. Creating links can be slower and stricter.

**2. Which requirements are about correctness, and which are nice to have?**
Correctness: two links must never share a code, a link must redirect to exactly the URL it was created with, and an expired or deleted link must stop working. Nice to have: exact real-time click counts (a few seconds of delay is acceptable), custom codes, analytics.

**3. The back-of-envelope:** 1M links/month × 100 clicks = 100M redirects/month, about 100,000,000 / 2.6M seconds ≈ 40 redirects per second on average, with peaks several times higher. Writes are about 0.4 per second. That gap is the whole argument for caching reads and buffering click writes.

---

## Milestone 1: FastAPI basics

**1. Why 302 and not 301?**
Browsers cache a 301 ("moved permanently") and stop asking the server, so later clicks never reach you. You'd lose click counts, and you could never expire, change or delete the link. A 302 sends every click through the service.

**2. Why must `/health` be declared before `/{code}`?**
FastAPI matches routes in declaration order. `/{code}` matches any single path segment, including "health", so if it came first, `GET /health` would be treated as a short code and return 404. Reserving names like `health` for custom codes prevents the same clash from the data side.

**3. What does Pydantic do before your function runs, and why reject `javascript:` URLs?**
It parses the JSON body, checks types and rules (`HttpUrl`, `ge`/`le`, your validators), and answers 422 with a precise error if anything fails, so your code only ever sees valid data. `javascript:` URLs would turn your short link into a way to run script in the victim's browser; allowing only `http`/`https` closes that hole.

**4. Why 409 for a taken custom code but 422 for an invalid one?**
422 means the request itself is malformed (it can never succeed as written). 409 means the request is valid but conflicts with the current state: the same request would succeed if that code were free.

---

## Milestone 2: Short codes

**1. Compare hashing, random strings and id → base62.**

| Approach | Upside | Downside |
|---|---|---|
| Hash the URL, truncate | Same URL gives the same code | Collisions possible, so check and retry |
| Random string | Unpredictable | Collisions grow as the table fills; check and retry |
| Unique id → base62 | Collision-free by construction, no retries | Sequential unless scrambled |

**2. Why base62, not base64?**
Base64 includes `+` and `/` (and `=` padding), which have special meaning in URLs and need escaping. Base62 is letters and digits only, so codes are safe in any URL and easy to read aloud.

**3. Why scramble the id, and why doesn't scrambling break uniqueness?**
Unscrambled, consecutive ids give consecutive codes, so anyone can enumerate every link. `(id × M + OFFSET) mod 62⁷` is a bijection when M shares no factor with 62⁷: it rearranges the numbers 0…62⁷−1 without ever sending two to the same place. Unique ids in, unique codes out. It's obfuscation, not security; it stops casual enumeration, not a determined attacker.

**4. How many codes do 7 characters give?**
62⁷ ≈ 3.5 trillion. At 1 million new links per day, that lasts about 9,600 years.

---

## Milestone 3: PostgreSQL

**1. Why Postgres as the source of truth?**
It's durable, so data survives restarts. It's shared, so every copy of the app sees the same data. It has transactions and a UNIQUE constraint that guarantees no two links share a code even if your Python has a bug. Redis only holds copies, so losing Redis loses nothing.

**2. Why `INSERT ... ON CONFLICT DO NOTHING` instead of check-then-insert?**
Check-then-insert is two steps. Two requests for the same custom code can both run the check, both see "free", and both insert. `ON CONFLICT` lets the UNIQUE index decide in one atomic statement: exactly one wins, and the other gets no row back, which becomes a 409.

**3. Why a connection pool?**
Opening a connection costs a network round trip, authentication and process setup on the database side. A pool keeps a few connections open and lends them out, which is faster and also caps how many connections your app can open, protecting the database's connection limit.

**4. Why versioned migrations and an advisory lock?**
Migrations make every schema change a numbered, reviewed, version-controlled file, applied exactly once and in order on every environment. The `schema_migrations` table remembers what ran, so startup is idempotent. The advisory lock stops two app instances that start simultaneously from both running the same migration.

**5. Why `$1` parameters instead of f-strings?**
Parameters are sent to the database separately from the SQL text, so user input is always treated as data and can never change the query: no SQL injection. They also let Postgres reuse query plans.

---

## Milestone 4: Redis cache-aside

**1. Explain cache-aside and why it fits a read-heavy system.**
On a read, check the cache; on a miss, read the database and store the result in the cache with a TTL. Only links people actually click occupy memory, and most clicks hit a small set of popular links, so a small cache absorbs most traffic. The database stays the single source of truth.

**2. Why must the cache TTL never outlive the link?**
A cache hit skips the database, so it never sees `expires_at`. If a link expiring in 10 minutes were cached for an hour, it would keep redirecting for 50 minutes after it expired. Capping the TTL at the link's remaining lifetime makes a hit always correct, with no expiry check on the hot path.

**3. What's negative caching, and what does it blunt?**
Remembering "this code doesn't exist" (or "has expired") for a short time. Without it, a bot requesting random codes turns every request into a database query, an easy way to overload the database. The TTL is short so a newly created link isn't blocked for long, and creating a link explicitly clears its cached 404.

**4. On delete, why Postgres first, then Redis?**
If you cleared Redis first, a redirect arriving in between would miss the cache, read the still-present row from Postgres, and put it back in the cache, and the deleted link would keep working until the TTL ran out. Deleting the source of truth first, then the copy, closes that window.

---

## Milestone 5: Clicks, rate limiting, degradation

**1. Why buffer clicks instead of an UPDATE per redirect? What's the trade-off?**
An UPDATE per click adds a database write and round trip to the hottest path and turns a read-heavy workload into a write-heavy one, with row-lock contention on popular links. A Redis `HINCRBY` is microseconds, and one batched UPDATE every few seconds replaces thousands of individual ones. Trade-offs: `/stats` can lag a few seconds (we add the buffer to hide that), and if Redis loses data before a flush, a few seconds of clicks are lost. That's fine for analytics, not for billing.

**2. Why RENAME the buffer before flushing?**
`HGETALL` then `DEL` are two commands, so a click arriving between them would be deleted without ever being counted. `RENAME` is atomic: new clicks land in a fresh `clicks:pending`, and the renamed snapshot can be read and deleted safely. Two app instances flushing at once can never take the same counts.

**3. What happens when Redis is down, for each feature?**
Cache read: treated as a miss, served from Postgres. Cache write: skipped. Click: written straight to Postgres. Rate limiter: allows the request. `/health` reports Redis disconnected but still returns 200. The service gets slower but stays correct and available.

**4. Why does the rate limiter fail open?**
The limiter protects against abuse; it isn't needed for correctness. Failing closed would turn a Redis outage into a total outage for link creation. For a security-critical limiter, such as login attempts, you might choose to fail closed instead; it's a deliberate trade-off.

**5. Why `volatile-lru` and not `allkeys-lru`?**
`volatile-lru` evicts only keys that have a TTL: cached URLs and rate-limit counters, which can always be rebuilt. The click buffer has no TTL, so it's never evicted before being flushed. `allkeys-lru` could silently throw away uncounted clicks.

---

## Milestone 6: Docker and CI

**1. Image vs container?**
An image is the packaged, read-only template: OS layer, Python, dependencies, your code. A container is a running instance of an image. One image can run as many containers.

**2. Why healthchecks and `depends_on: condition: service_healthy`?**
Plain `depends_on` only waits for the database container to start, not for Postgres to accept connections, so the API can crash on startup. The healthcheck defines "ready", and the condition waits for it.

**3. Why run as a non-root user and drop `--reload`?**
Non-root limits the damage if the app is ever compromised. `--reload` watches files for changes: useful in development, wasted work and a needless risk in production.

**4. What does CI prove that your laptop can't?**
That the project builds and passes its tests from a clean checkout, on a fresh machine, with real Postgres and Redis. That means no "works on my machine": no forgotten dependency, no leftover local state. And it runs on every change, so regressions are caught before merging.

---

## Milestone 7: Scaling and reflection

**1. 100× the redirects?**
The app is stateless, so run more instances behind a load balancer. Add a Redis cluster for cache capacity, Postgres read replicas for cache misses, and possibly a CDN or edge cache for the very hottest links. Measure p95/p99 latency before and after each change.

**2. Ids across many servers?**
One sequence handles thousands of creates per second, but at larger scale it becomes a bottleneck. Hand out ranges of ids to each instance (one database call reserves 1,000 ids), or use Snowflake-style ids that combine a timestamp, a machine id and a counter, generated locally without coordination.

**3. Analytics at scale?**
Publish each click as an event to a log like Kafka and aggregate it downstream (counts per link per hour, referrers, countries) instead of counting in Redis. That decouples the redirect path from analytics completely.

**4. What would you do differently?**
Examples: a sliding-window or token-bucket rate limiter keyed by API key, not just IP; a cleanup job for expired links using the partial index; authentication so users can manage their own links; and load tests with published numbers.

**5. Walk me through what happens when someone clicks a short link.**
The browser sends `GET /abc1234`. FastAPI checks Redis for `url:abc1234`. On a hit it counts the click with one `HINCRBY` and returns a 302 with no database query. On a miss it reads Postgres: not found → caches "not found" briefly, 404; expired → caches "gone", 410; found → caches the URL with a TTL capped at the link's expiry, counts the click, 302. Every 10 seconds a background task moves the buffered counts into Postgres in one UPDATE.

**6. What if Postgres goes down?**
Cached redirects keep working from Redis for as long as their TTL lasts. Creating, deleting, stats and cache misses fail, and `/health` returns 503 so a load balancer can react. Buffered clicks stay in Redis and are flushed when Postgres comes back (and are put back in Redis if a flush fails). Postgres is the source of truth, so correctness never depends on Redis, but availability for writes does depend on Postgres.

**7. What would you change if this held payment data instead of click counts?**
No buffering in a store that can lose data: every write goes to the database in a transaction before the request succeeds. Idempotency keys so a retried request can't charge twice. Stricter consistency (no serving from a possibly stale cache for balances). Audit logs, encryption, and a rate limiter that fails closed.

**8. The hardest bug**
Use a real one from your own build. Good candidates from this project: the route-order bug (`/health` swallowed by `/{code}`); an expired link still redirecting from the cache before the TTL was capped; or a click lost between `HGETALL` and `DEL` before switching to `RENAME`. Describe the symptom, how you found it (which test), and the fix.

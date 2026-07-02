# Module 10 — Performance Engineering

Performance questions in interviews come in two forms: "your system is slow —
debug it" (a war-story test) and "how do you keep this design fast at scale"
(a prevention test). This module arms you for both.

---

## 10.1 Bottleneck Analysis & Profiling

### Why Interviewers Ask This

"Users report the app is slow" is a favorite senior scenario. They grade your
*method*: do you measure before changing anything, and do you know the usual
suspects in order of likelihood?

### Core Concept — the method

1. **Define "slow" numerically**: which endpoint, which percentile, since when, for whom (all users? one region? one tenant?). A p99 regression with flat p50 points at tail causes (GC, lock contention, one bad shard); a uniform shift points at a code/deploy/dependency change.
2. **Follow the request path with data**: client → CDN → LB → service → dependencies. Distributed tracing (Module 12) shows which hop grew; without it, compare latency dashboards layer by layer.
3. **Utilization–Saturation–Errors (USE)** on the suspect host: CPU, memory, disk I/O, network — is a resource saturated (run queue, iowait, swap)? Queueing theory: latency explodes as any resource approaches 100%.
4. **Profile before optimizing**: CPU flame graphs (perf, async-profiler, pprof) show where time is actually spent — it is almost never where intuition says. Continuous profilers (Parca, Pyroscope, Datadog) let you diff "yesterday vs today". For latency (not CPU) problems, use wall-clock/off-CPU profiling — a thread waiting on a lock or socket is invisible to CPU profiles.
5. **The base-rate list** (most production slowness, in rough order): a slow **database query** (new unindexed access pattern, plan flip, table growth) → **N+1 patterns** → **connection/thread pool exhaustion** → cache hit-ratio drop → GC pauses → a slow downstream API → resource saturation from a noisy neighbor or organic growth.

Amdahl again: optimize the biggest span in the trace, not the most interesting one.

### Interview Questions

1. p99 doubled at 9am; p50 flat; no deploys. Your first five actions?
2. Why can CPU profiles mislead for latency problems? (off-CPU time invisible)
3. What's the USE method?

---

## 10.2 Slow Queries

### Core Concept & Playbook

The single most common production performance incident. The loop:

- **Find them**: `pg_stat_statements` / slow query log (log everything > 100 ms), APM traces, `EXPLAIN ANALYZE` the top offenders.
- **Read the plan**: seq scan under a selective WHERE = missing index; wrong composite order (Module 4.4); huge `Rows Removed by Filter`; sort/hash spilling to disk (`work_mem`); nested-loop joins on unindexed FKs; plan flips after data growth or stale statistics (`ANALYZE`).
- **Fix ladder**: add/repair the index → rewrite the query (avoid functions on indexed columns, `SELECT` only needed columns, EXISTS over IN for big sets, keyset pagination instead of OFFSET) → denormalize/precompute (materialized views, counter columns) → cache the result → move the workload (replica for analytics, columnar warehouse for aggregations — OLAP queries do not belong on the OLTP primary).
- **Contain them**: `statement_timeout` per role/endpoint so one runaway query can't hold locks and drain the pool; separate replica/warehouse for ad-hoc internal queries (a data analyst's cross join should never be able to take down checkout).
- Watch **lock waits** disguised as slow queries (`pg_locks`, blocked-by chains): a long transaction holding a row lock makes everything behind it "slow".

### Interview Questions

1. A query got 100× slower overnight with no code change — hypotheses? (growth crossed a plan threshold, stats stale → plan flip, index bloat, lock contention, autovacuum behind)
2. Why is OFFSET 500000 pagination slow and what replaces it? (scans and discards; keyset/seek: `WHERE id < last_seen ORDER BY id LIMIT 20`)

---

## 10.3 Connection Pool Exhaustion

(Deep treatment in Module 4.6 — here, the incident pattern interviewers ask about.)

```
 trigger: one slow query/dependency (2 s instead of 5 ms)
 → connections held 400× longer → pool (20) fully busy at 10 QPS instead of 4000
 → new requests queue at acquire → app threads block → upstream times out
 → RETRIES arrive (more load) → total stall. DB often looks IDLE (it's waiting, not working).
```

Diagnosis signature: latency spike + pool "active = max" + DB CPU *low* + acquire
timeouts in logs. Fixes in order: kill/timeout the slow query (statement_timeout),
fail fast at acquire (small timeout), bulkhead pools per workload, circuit-break
the offending dependency, then restore. Prevention: Little's-Law sizing, per-
endpoint timeouts shorter than the client's, PgBouncer at fleet scale, and
load tests that include the slow-dependency scenario.

### Interview Question

"The DB looks healthy but the app is down and every thread is 'waiting for
connection'." — narrate the cascade above and the runbook.

---

## 10.4 N+1 Queries

### Core Concept

The ORM classic: fetch N parents, then lazily query children once per parent —
1 + N round trips (100 posts = 101 queries; at 1 ms each that's the whole latency
budget). Each query is fast; the *count* kills you — which is why it hides from
slow-query logs and only shows in traces (a comb of tiny identical spans) or query
counters per request.

Fixes:

- **Batch**: `WHERE post_id IN (...)` / ORM eager loading (`includes`, `select_related`/`prefetch_related`, JPA fetch joins).
- **JOIN** parent+child in one query where shapes allow.
- **Application-level batching — DataLoader pattern** (essential vocabulary for GraphQL designs): collect all child-IDs requested in one tick, issue one batched query, distribute results. GraphQL's resolver-per-field model makes N+1 the *default* failure mode; DataLoader is the standard answer.
- The same disease exists across services: a for-loop of RPC calls = distributed N+1 → batch APIs (`GET /users?ids=...`) — every internal API should expose batch endpoints.

Guardrails: per-request query counters in dev/CI (fail tests on query-count
regressions), ORM lazy-loading warnings in staging.

### Interview Questions

1. Feed page makes 400 queries — find it, fix it, prevent regression.
2. Why is GraphQL especially N+1-prone and what's the standard fix?

---

## 10.5 Compression

### Core Concept

Trade CPU for bytes — almost always a win over WAN/mobile, often a wash on LAN.

- **HTTP responses**: gzip (universal) vs **Brotli** (~15–20% smaller for text, slower to compress — use high-level Brotli for *static* assets precompressed at build time, fast levels or gzip/dynamic for API JSON) vs **zstd** (best speed/ratio family, growing support). Compress text (HTML/JSON/JS); never recompress JPEG/MP4 (already compressed — wasted CPU).
- **Internal**: gRPC/protobuf is a form of schema compression (binary vs JSON ≈ 3–10× smaller); Kafka producer compression (lz4/zstd per batch) is standard and multiplies effective broker throughput; column stores (Parquet) get 10×+ from columnar encodings (RLE, dictionary, delta).
- **Trade-offs to name**: CPU cost at high QPS (measure — compression can become *the* CPU consumer at an edge tier), latency of buffering to compress, and small responses (< ~1 KB) not worth headers/CPU. BREACH/CRIME caveat: compressing secrets alongside attacker-controlled input in TLS responses leaks data — don't compress pages mixing both.
- Media is its own pipeline: images → WebP/AVIF renditions, video → H.264/265/AV1 adaptive bitrate ladders (Module 13 YouTube/Netflix) — "compression" there is transcoding, done once offline, not per request.

### Interview Question

"Mobile users on slow networks: what do you compress, where, and what do you skip?"

---

## 10.6 Pagination

### Core Concept

Never return unbounded lists — pagination is memory protection, latency
protection, and DB protection at once.

- **Offset/limit** (`LIMIT 20 OFFSET 10000`): simple, jumpable to page N, but the DB *scans and discards* offset rows (page 500 costs 500× page 1) and pages **drift** when rows are inserted/deleted between requests (skipped/duplicated items).
- **Cursor/keyset (seek)**: `WHERE (created_at, id) < (:last_created, :last_id) ORDER BY created_at DESC, id DESC LIMIT 20` — constant cost per page (pure index seek), stable under inserts; the cursor is an opaque token encoding the last-seen sort key. Cost: no "jump to page 37", requires a unique, indexed, stable sort key (tie-break with id).
- **Rules**: infinite scroll/feeds/APIs → cursor (Slack, Stripe, Twitter, GitHub APIs all use cursors); small admin tables where humans want page numbers → offset is fine; always enforce a **max page size**; return `next_cursor` + `has_more`; make cursors opaque (base64 the key material) so clients can't fabricate them.
- Deep-pagination at scale (page 10,000 of search results): nobody legitimate does it — cap it (Google stops at ~page 40; Elasticsearch caps `from+size` at 10k and offers `search_after` for the rest).

### Interview Question

"Design pagination for a feed with new items arriving constantly — why does OFFSET
break, exactly?"

---

## 10.7 Batch Processing & Streaming

### Core Concept

Two execution models for work that isn't request/response:

- **Batch**: bounded dataset, scheduled, high throughput, latency = schedule + runtime (minutes–hours). MapReduce lineage → Spark. Right for: billing runs, ML training, backfills, reports, dedup/reconciliation. Design points: **idempotent + re-runnable** jobs (reruns after failure must be safe — write to a staging location and atomically swap), checkpointing for long jobs, and isolation from OLTP (run against replicas/warehouse/lake).
- **Streaming**: unbounded events processed continuously, latency in seconds. Flink / Kafka Streams / Spark Structured Streaming. Right for: fraud scoring, live dashboards/metrics, feed fan-out, CDC pipelines, sessionization. Design vocabulary interviewers probe: **event time vs processing time**, **windows** (tumbling/sliding/session), **watermarks** (how long to wait for late events), **stateful operators** with checkpointed state (RocksDB + changelogs — this is what makes exactly-once processing possible inside the pipeline).
- **The batching principle inside services** (micro-batching): amortize per-operation overhead everywhere — batched DB inserts (1000-row multi-insert ≈ 50× faster than 1000 singles), batched Kafka produces, batched cache MGETs, coalesced writes for hot counters. Throughput up, small latency cost (Module 1.1).
- **Lambda vs Kappa architecture** (one-liner): lambda = batch + speed layers reconciled (two codebases — operational pain); kappa = streaming-only with replayable log as source of truth (rebuild by replaying Kafka). Modern default leans kappa + occasional backfills.

```
 events ─► Kafka ─┬─► Flink (windows, state, watermarks) ─► serving store (live)
                  └─► object storage (raw) ─► Spark batch (backfill/repair/training)
```

### Interview Questions

1. Fraud detection needs a decision in < 2 s — batch or streaming, and what state does the pipeline keep? (streaming; per-card/session aggregates in checkpointed state)
2. Your nightly batch failed at 80% — what design choices make the rerun safe?
3. Event time vs processing time — why does the difference matter for "orders per minute" dashboards?

---

## Module 10 Cheat Sheet

```
METHOD       Quantify (endpoint, percentile, cohort) → trace the path → USE per
             host → profile (flame graphs; off-CPU for latency) → fix biggest span.
             Base rates: slow query > N+1 > pool exhaustion > cache drop > GC > dep.
SLOW QUERY   pg_stat_statements → EXPLAIN ANALYZE → index/rewrite/precompute/cache/
             relocate. statement_timeout. OLAP off the OLTP box. Lock waits lie.
POOLS        slow dependency ⇒ held connections ⇒ acquire queue ⇒ stall while DB
             idles. Fail-fast acquire, statement timeouts, bulkheads, breakers.
N+1          1+N round trips; invisible in slow logs, visible in traces. Eager
             load / IN-batch / JOIN / DataLoader (GraphQL). Batch RPC endpoints.
             Query-count guardrails in CI.
COMPRESSION  Brotli static (precompressed), gzip/zstd dynamic, never re-compress
             media. gRPC/protobuf, Kafka lz4/zstd, Parquet columnar. CPU vs bytes;
             skip < 1 KB.
PAGINATION   OFFSET scans+drifts; keyset/cursor = constant cost, stable, no jumps.
             Opaque cursors, max page size, cap deep pages (search_after).
BATCH        bounded, scheduled, idempotent + re-runnable, staging+atomic swap,
             off the OLTP path.
STREAMING    unbounded, seconds latency; event-time windows + watermarks +
             checkpointed state (Flink/Kafka Streams). Kappa: replay the log.
MICRO-BATCH  amortize everything: multi-row inserts, MGET, producer batches.
```

## Top Interview Questions (Module 10)

1. "App is slow" — full triage method. 2. Query 100× slower overnight. 3. Pool-
exhaustion cascade with an idle DB. 4. N+1 in GraphQL + DataLoader. 5. OFFSET vs
keyset internals. 6. What to compress for mobile. 7. Batch vs streaming for fraud/
billing/dashboards. 8. Idempotent rerunnable batch design. 9. Watermarks and late
events. 10. Where batching adds latency and why it's usually worth it.

## Common Mistakes Recap

Optimizing without profiling • average-latency thinking • OLAP on the OLTP primary
• no statement timeouts • ORMs lazy-loading in loops • unbounded list endpoints •
OFFSET on infinite scroll • compressing JPEGs, skipping JSON • non-idempotent batch
jobs • ignoring event-time vs processing-time skew.

## Mock Interview Exercise

*"An e-commerce 'order history' page p99 went from 300 ms to 4 s over two months.
Traffic doubled; the table grew 5×; there were many small deploys."* Walk the
triage: trace shows DB span dominant → EXPLAIN reveals OFFSET pagination + a plan
flip on the grown table + an N+1 for item thumbnails. Fix: keyset pagination,
composite index `(user_id, created_at DESC)`, batched thumbnail fetch, statement
timeout, and a CI query-count guard. Then state prevention: pagination standards,
index review in migrations, continuous profiling.

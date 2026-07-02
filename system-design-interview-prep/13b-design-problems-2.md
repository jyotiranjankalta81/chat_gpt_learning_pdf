# Module 13 — Classic System Design Problems (Part 2)

*(Chat Application: fully covered in 13.3 (WhatsApp) — a generic chat app is the
same design minus E2E encryption, plus permanent history + search (Slack model):
keep messages forever in the conv-partitioned store, add an ES index fed by CDC,
and per-channel pull for large channels.)*

---

## 13.10 Notification Service

**Functional:** one API for all channels (push APNs/FCM, email, SMS, in-app);
templates + localization; user preferences & opt-outs; scheduling; batching/digests;
delivery tracking. **Non-functional:** OTPs in seconds (high priority lane);
marketing can lag minutes; **at-least-once with dedupe** (never spam duplicates);
peak bursts of 10M+ (a viral event or campaign blast); channel providers are flaky
third parties.

**Capacity:** 500M notifications/day ≈ 6k/s average, campaign spikes 100k+/s ⇒
queue-centric design is forced. Provider rate limits (SMS gateways especially) are
the real throughput ceiling — mention this.

**API:**

```
POST /notifications {user_id | segment, template_id, data, channels?, priority,
                     idempotency_key, send_at?}
GET  /notifications/{id}/status       PUT /users/{id}/preferences
```

**High-level design:**

```
 callers → notification API (validate, dedupe by idem key)
   → Kafka, PARTITIONED LANES: critical(OTP) / transactional / marketing  ◄ priority
   → workers: preference+quiet-hours check → template render (i18n) →
     rate limit per user ("max N/day") + collapse/digest →
     channel adapters: [APNs] [FCM] [SES/SMTP] [Twilio/SMS] [in-app inbox]
        each: provider rate limiter + retries + breaker + failover provider
   → delivery receipts/webhooks → status store → analytics (open/click)
   → DLQ per channel + alerting
```

**Deep dives worth offering:** priority isolation (separate topics/worker pools —
a marketing blast must never delay OTPs: bulkhead, Module 7.4); per-user frequency
capping and collapsing ("5 likes" not 5 pushes) via a short aggregation window;
idempotency at two levels (API key dedupe + channel-adapter send-once records);
device token lifecycle (invalid-token feedback from APNs/FCM prunes the registry);
provider failover (Twilio down → backup SMS route). **Scaling:** everything is
stateless workers on partitioned queues — scale consumers; segment-blast campaigns
are expanded (segment → user IDs) by a fan-out stage *into* the same pipeline.
**Failure:** provider outage → breaker + secondary provider + backlog in Kafka
(bounded by retention — shed marketing first, keep OTP lane); duplicate webhooks
from providers → idempotent status updates. **Caching:** preferences, templates,
device tokens. **Security:** only trusted internal callers (this service can spam
your entire user base), template injection safety, PII minimization in queues,
unsubscribe compliance (CAN-SPAM/GDPR). **Trade-offs:** unified service (consistent
prefs/limits, one throat to choke) vs per-team sending (autonomy, chaos); push
now vs digest (engagement vs annoyance); at-least-once+dedupe vs at-most-once
(OTP must never be lost; a rare duplicate OTP is harmless).

---

## 13.11 Search Autocomplete (Typeahead)

**Functional:** top-k suggestions per prefix as the user types; ranked by
popularity (+freshness, +personalization optionally); trending queries appear
within hours/minutes. **Non-functional:** p99 < 50–100 ms (it races keystrokes);
massive read QPS (every keystroke of every user); suggestion data eventually
consistent (rebuilt periodically) — reads must never touch the pipeline.

**Capacity:** 5B searches/day, ~4 keystrokes/query with client debounce ⇒ ~200k+
lookup QPS peak. Corpus: top ~10M queries suffice; a precomputed prefix→top-10
map ≈ few GB — **fits in RAM**; that observation is the design.

**API:** `GET /suggest?q=<prefix>&limit=10` (+user/locale) — client debounces
(~100–150 ms) and cancels stale requests.

**Deep dive — the two-plane design (the expected answer):**

```
 SERVING (read) PLANE — precomputed, in-memory:
   trie where each node stores its top-10 completions cached at the node
   (or literally a hash map: prefix(≤n chars) → [top10])  → O(1) lookup, no
   traversal at query time. Sharded by prefix range across replicas; small
   enough to replicate fully per node. CDN/edge cache for hottest prefixes.

 BUILD (write) PLANE — offline/streaming aggregation:
   search logs → Kafka → hourly/daily batch (count, decay old counts,
   filter: spam/adult/PII) → build trie/prefix tables → ship immutable
   snapshot to serving nodes (atomic swap, versioned)
   + streaming fast path for trending: last-hour counts merged into results
     with a recency boost
```

Key points to narrate: **precompute top-k at build time** (query-time ranking of
thousands of completions is unaffordable at 50 ms); weight = frequency with
time-decay (trending); atomic snapshot swap = trivially consistent serving + easy
rollback; personalization as a thin re-rank layer over global results (client or
edge merges "your recent searches"). **Scaling:** read plane scales by replication
(data is small and read-only — the easiest scaling in this whole module); build
plane is batch (Module 10.7). **Failure:** serving node dies → LB reroutes
(read-only replicas); bad build (offensive suggestion ships) → version rollback +
blocklist hotfix path. **Caching:** the serving plane *is* a cache; plus browser/
edge caching per prefix (short TTL). **Security/quality:** filter pipeline
(profanity, PII, legal removals), per-locale corpora, abuse (query-log poisoning:
rate-limit and dedupe by user before counting). **Trade-offs:** trie (memory-
efficient shared prefixes, range flexibility) vs flat prefix map (simplest, more
memory); update latency (rebuild cadence) vs freshness (streaming merge
complexity); global vs personalized (privacy + memory per user).

---

## 13.12 Web Crawler

**Functional:** given seeds, download the web: fetch → parse → extract links →
enqueue new URLs → store pages for indexing; re-crawl by freshness policy.
**Non-functional:** billions of pages; **politeness** (per-domain rate limits,
robots.txt — a crawler that DDoSes sites gets blocked/lawyered); dedupe (URL and
content); fault tolerant over weeks-long runs; prioritized (important pages first,
freshness-aware re-crawl).

**Capacity:** 1B pages in 30 days ≈ 400 pages/s sustained (peaks higher); avg page
~100 KB ⇒ ~40 MB/s ingest, 100 TB total (object storage, compressed). URL frontier:
tens of billions of URLs seen ⇒ dedupe structure must be RAM-efficient (Bloom
filter territory, Module 11.2).

**High-level design:**

```
              ┌──────────── URL FRONTIER (the heart) ─────────────┐
 seeds ──►    │ front queues: by PRIORITY (pagerank-ish, freshness)│
              │ back queues:  ONE PER DOMAIN + per-domain timer    │◄─ politeness:
              └──────┬─────────────────────────────────────────────┘   1 req/domain
                     ▼ (a fetcher leases a domain queue)                per delay
  fetchers (async I/O, DNS cache, robots.txt cache per domain)
        │ raw HTML → object storage (WARC)
        ▼
  parsers → extract text + links → normalize URLs (canonicalize, strip trackers)
        │ links → SEEN? ── Bloom filter (RAM) + exact store ──► frontier
        └ content fingerprint (SimHash) → near-duplicate? skip indexing
        ▼
  downstream: indexer / freshness scheduler (re-crawl queue by change rate)
```

**Deep dives:** the **frontier** is the interview centerpiece — it must
simultaneously enforce politeness (per-domain serialization + delay ⇒ back queue
per domain, fetchers lease domains, timers gate re-fetch) and priority (front
queues feed back queues by importance). **Dedupe at two levels**: URL-seen
(Bloom filter for the fast "definitely new" check — false positives just skip a
URL, tolerable — backed by an exact KV store) and content-seen (SimHash/MinHash
near-dup detection — mirrors, tracking-param variants). **Traps**: spider traps
(infinite calendars, session-ID URL spaces) → max depth/URL-count per domain +
pattern detection; JS-rendered pages → headless-render tier for the subset worth
it (10× cost — budget it). **Scaling:** partition frontier + fetchers **by domain
hash** (politeness state stays local — no cross-node coordination per request);
DNS resolution needs its own cache/resolver fleet (a real bottleneck at 400+
fetches/s). **Failure:** fetcher dies → domain lease expires → another picks up;
frontier checkpointed (it *is* the crawl state); fetch failures → retry with
backoff, mark dead after N (transient vs permanent, Module 5.6). **Caching:**
robots.txt (per domain, TTL 24 h), DNS, conditional GETs (ETag/If-Modified-Since —
save bandwidth on re-crawl). **Security/etiquette:** honor robots + crawl-delay,
identify honestly in User-Agent, contactable operator, avoid login areas,
malware-scan stored content (you're storing the web's worst too). **Trade-offs:**
BFS-by-priority (news first) vs pure BFS; freshness (aggressive re-crawl of hot
pages) vs coverage (crawl budget is finite — allocate by change-rate estimation);
Bloom false positives (miss a few URLs) vs exact-only dedupe (RAM/latency).

---

## 13.13 Distributed Cache (design Redis/Memcached itself)

*(Assembles Modules 3 + 11 into one system — a favorite "infra" prompt.)*

**Functional:** GET/SET/DEL with TTL; atomic ops (INCR, CAS); cluster grows/shrinks
online; optional replication. **Non-functional:** sub-ms p99; millions of ops/s
across the cluster; cache semantics (loss tolerable, availability + latency over
durability); minimal disruption on topology change.

**Capacity example:** 1 TB working set, 5M ops/s ⇒ 16–32 nodes (64 GB each,
200–500k ops/s each), ×2 for replicas + headroom.

**API:** `GET k / SET k v EX ttl / DEL k / INCR k / CAS k v version` — plus MGET
batching (protocol design point: pipelining matters more than fancy ops).

**Design:**

```
 clients (smart lib: topology map, hashing, timeouts, single-flight)
    │ consistent hashing w/ VIRTUAL NODES (Module 11.1)  or  hash-slot table
    ▼
 node = single-threaded event loop (atomicity for free) + hash table
        + LRU/LFU eviction (W-TinyLFU) + TTL wheel (lazy + periodic expiry)
        + optional async replica (failover target)
 cluster membership: gossip (Module 11.6) or small Raft metadata core (Module 8.4)
 topology change: slot/arc migration node→node while serving (MOVED redirects)
```

**Deep dives:** memory management (slab classes vs jemalloc — fragmentation is the
silent killer; eviction under pressure must be O(1)); threading model
(single-threaded loop + I/O threads vs sharded-per-core (memcached) — atomicity vs
per-node vertical scale); consistency choice — *a cache chooses AP*: async
replication, failover may serve slightly stale or lose recent sets (acceptable —
the DB is the source of truth; say it); hot keys (detection + client L1 + key
replication, Module 3.6); client library as part of the system (timeouts ~50 ms
fail-fast, backpressure, single-flight — Module 3.7). **Scaling:** add node →
consistent hashing moves ~1/N keys (misses refill from DB — plan the DB headroom);
scale reads via replicas. **Failure:** node death → its arc goes cold, DB absorbs
refill (this cascade is the #1 thing to size for); partition → prefer availability
(serve possibly-stale, no quorum reads). **Security:** network isolation, AUTH,
TLS optional (latency cost), never public. **Trade-offs:** consistent hashing
(decentralized) vs slot table (operable, explicit migration — Redis chose slots);
replication (fast failover, memory ×2) vs none (cheaper, cold-start on failure);
strong-ish consistency (WAIT/sync) vs the point of a cache.

---

## 13.14 Rate Limiter (as a system)

*(Algorithms in Module 9.5 — here, the distributed service design interviewers
ask for.)*

**Functional:** enforce configurable limits (per user/API-key/IP/endpoint;
rate + burst); return 429 + Retry-After + headers; runtime config changes; shadow
mode. **Non-functional:** added latency ≤ 1–2 ms p99; must not become the outage
(explicit fail-open/closed policy); millions of decisions/s; approximate limits
acceptable (±small % — say this, it unlocks the good designs).

**Design options (present all three, recommend per context):**

```
 A) gateway-local buckets        zero latency, limit accuracy ±N_nodes slice,
    (each node gets rate/N)      skewed traffic breaks it — fine for coarse DDoS
 B) central Redis counters       accurate global; +1 round trip (~1ms); Lua for
    (token bucket per key)       atomic check+decrement; shard by key; hot-key
                                 celebrities → local pre-allocation on top
 C) local + async sync (hybrid)  near-zero latency, near-accurate: nodes consume
    "token borrowing"            from local slice, periodically settle with a
                                 central budget — the production sweet spot
```

Redis token bucket (the snippet to whiteboard): store `{tokens, last_refill}` per
key; Lua: `tokens = min(burst, tokens + rate·Δt); if tokens≥1 then tokens-=1;
allow`. Memory: 2 floats/key × 100M active keys ≈ GBs — fine sharded. **Config
plane:** rules in a config store, pushed to enforcers (versioned, canary, shadow
mode first — enforcement bugs = self-inflicted outage). **Failure:** Redis down →
**fail-open for availability-tier APIs, fail-closed for abuse-sensitive endpoints
(login/OTP)** — a per-rule policy, the senior nuance; local fallback limiter as
middle ground. **Where it lives:** gateway middleware (Module 2.5) or sidecar;
keep decision (policy) separate from counting (state). **Trade-offs:** accuracy vs
latency (A↔B↔C); global vs per-region limits (cross-region sync is not worth it —
limit per region, cap globally via async settle); token bucket (burst-friendly
API semantics) vs sliding window (smoother, no burst) — Module 9.5.

---

## 13.15 API Gateway (as a system)

*(Role in Modules 2.5/7.3 — here, designing the gateway itself.)*

**Functional:** routing (host/path/header → service), authn (JWT/OIDC validation,
API keys), rate limiting/quotas, TLS termination, retries/timeouts/breakers,
canary + traffic splitting, request/response transforms, observability emission.
**Non-functional:** it's in front of *everything*: p99 overhead ≤ 5 ms, 99.99%+,
horizontal scale to full site traffic, config changes without restarts and without
global blast radius.

**Design:**

```
 clients → anycast/L4 (Module 2.5) → GATEWAY FLEET (stateless!)
   per request: TLS → route match → authn (JWT verify LOCALLY via cached JWKS —
   no auth-service call on hot path) → rate limit (13.14 hybrid) → transform →
   proxy (connection pools per upstream, retry budget, breaker, deadline) →
   emit metrics/traces/logs
 CONTROL PLANE (separate!): config API/GitOps → validate → version → push (xDS-
   style) to data plane; canary configs; instant rollback
 state: none locally — JWKS cache, route table cache, rate-limit via 13.14
```

**Deep dives:** data plane vs control plane separation (Envoy/xDS model — config
distribution is itself a distributed system; a bad config push is the gateway's
#1 outage cause ⇒ validation + canary + auto-rollback on error-rate spike);
zero-downtime config/binary reload (hot restart, connection draining); per-tenant
isolation (one customer's 10× spike must not eat the fleet — per-tenant concurrency
caps = bulkheads); keep business logic OUT (the anti-pattern from 7.3); BFF
variants per client type. **Scaling:** stateless horizontal; upstream connection
pooling (HTTP/2 multiplexing to services); shard by host/SNI if config becomes
huge. **Failure:** gateway node death (LB reroutes, conns re-established);
auth-provider down → cached JWKS keeps validating (tokens self-contained — a JWT
design win, Module 9.2); upstream down → breaker + fallback response.
**Caching:** JWKS, route tables, optional response caching for public GETs.
**Security:** it *is* the security perimeter — TLS policy, WAF integration, header
sanitization (strip client-sent internal headers!), request size/time limits,
mTLS to upstreams. **Trade-offs:** one shared gateway (consistency, ops leverage)
vs per-domain gateways (blast-radius isolation, team autonomy); rich gateway
(fewer sidecar concerns) vs thin gateway + mesh (east-west parity).

---

## 13.16 Logging System (Centralized Log Platform)

**Functional:** collect logs from every host/container; parse/structure; search
(near-real-time, by service/time/trace-id/full-text); retention tiers; alerts on
patterns; access control. **Non-functional:** ingest TB–PB/day (write-heavy,
Module 1.7!); search latency seconds for recent data; **lossy is unacceptable for
audit logs, acceptable-with-bounds for debug logs** (two tiers — say it); cost is
a first-class constraint (logs are the biggest observability bill).

**Capacity:** 10k hosts × 50 GB/day ≈ 500 TB/day raw ⇒ compression (10×) +
tiering + sampling are not optional. Peak ingest during incidents is 5–10× normal
— exactly when you can't drop data; buffer accordingly.

**Design:**

```
 apps → stdout → node AGENT (Fluent Bit/Vector: tail, batch, compress, spill-to-
        disk buffer — survives pipeline outages) 
   → Kafka (the shock absorber; retention = your outage budget)
   → processors: parse → structure (JSON) → enrich (k8s metadata, geo) → PII scrub
     → route by stream: 
        hot tier   (7–30 d): Elasticsearch/Loki — indexed search
        warm/cold  (1–7 y):  object storage, Parquet/compressed, queried by
                             batch engines (Athena-style) on demand
   → real-time matchers → alerts (error-pattern spikes)
```

**Deep dives:** the indexing trade-off — Elasticsearch indexes everything
(fast arbitrary search, huge write amplification + storage) vs **Loki's model**
(index only labels {service, level, pod}, grep the compressed chunks at query
time — 10× cheaper, slower needle-searches; the modern cost answer);
ordering/dedup (logs are at-least-once — consumers dedupe by (host, file, offset));
backpressure (agent disk buffers → Kafka lag → shed DEBUG before INFO before
ERROR — priority shedding); multi-tenancy (per-team quotas — one team's log loop
must not drown the platform: bulkhead again). **Scaling:** every stage partitions
by stream/tenant; ES needs index lifecycle management (daily indices, rollover,
shrink). **Failure:** ES down → Kafka buffers (size retention for your worst
honest outage), agents spill locally; the meta-problem — *the logging system's own
logs* (self-monitoring via metrics, not logs). **Caching:** recent-query results,
field-stats. **Security:** PII scrubbing at ingest (compliance), RBAC per index/
tenant, audit logs immutable (WORM object storage) + separate retention.
**Trade-offs:** index-everything vs label-index (cost vs search power);
retention length vs cost (tiering); sampling debug logs (10%) vs completeness
(never sample errors/audit).

---

## 13.17 Analytics Platform (Events → Insights)

**Functional:** ingest product events (clicks, views, transactions) from clients +
services; real-time dashboards (minutes) + historical/ad-hoc SQL (years);
funnels/retention/aggregations; feed ML/experiments. **Non-functional:** 1M+
events/s ingest; ingestion loss < 0.1%; dashboard queries seconds over billions of
rows; real-time lag ≤ 1 min; schema evolution without breakage; cost-efficient at
PB scale.

**Capacity:** 1M events/s × 1 KB ≈ 1 GB/s ≈ 85 TB/day raw → columnar+compressed
~10–20 TB/day stored. This is the definitive write-heavy system (Module 1.7).

**Design (the lambda/kappa shape, Module 10.7):**

```
 clients/SDKs (batch, retry, offline buffer) + services
   → collection endpoint (validate against SCHEMA REGISTRY, enrich, sessionize-id)
   → Kafka (partition by user/session for ordered per-user streams)
     ├─ STREAM path: Flink — windowed aggregates (event-time + watermarks),
     │   sessionization, funnels → real-time store (Druid/Pinot/ClickHouse)
     │   → live dashboards (lag: seconds–1 min)
     └─ BATCH path: raw → object-storage DATA LAKE (Parquet, partitioned
         dt/hour) → warehouse/lakehouse (Snowflake/BigQuery/Trino+Iceberg)
         → ad-hoc SQL, experiment analysis, ML features, BACKFILLS/corrections
```

**Deep dives:** **columnar storage is the whole trick** (scan 3 columns of 300 —
10–100× less I/O; +RLE/dictionary compression; partition pruning by date) — this
one paragraph answers "how do you query billions of rows in seconds";
**exactly-once-ish counting** (client dedupe IDs + Flink checkpointed state +
idempotent sink upserts — and honest reconciliation: batch recount corrects stream
drift nightly, the lambda reconciliation); **late events** (mobile offline hours →
watermarks + allowed-lateness + corrections, Module 10.7); **schema registry**
governance (typed events, compat rules — else the lake becomes a swamp); privacy
(consent flags at ingest, PII vaulting/pseudonymization, GDPR deletes in an
immutable lake → per-user encryption keys, crypto-shredding, Module 9.6).
**Scaling:** Kafka partitions; Flink parallelism; OLAP stores shard by time+tenant;
lake is object storage (infinite). **Failure:** OLAP store down → dashboards stale,
ingest unaffected (Kafka buffers — decoupling win); bad deploy corrupts aggregates
→ **replay from Kafka/lake** (kappa's superpower — recompute is a feature, design
for it). **Caching:** dashboard query cache, pre-aggregated cubes (hourly rollups)
for the hot 20 dashboards. **Security:** row/column-level access in the warehouse,
audit, tokenized joins for sensitive analysis. **Trade-offs:** stream+batch
(lambda: fast + correct, dual code) vs kappa (one path, replay for corrections);
Druid/Pinot (sub-second, ops-heavy) vs ClickHouse (simpler, powerful) vs
warehouse-only (minutes latency, cheapest ops); raw-forever (rebuild anything,
storage cost) vs aggregate-only (cheap, irreversible).

---

## Module 13 Cheat Sheet — patterns that repeat across all 27 problems

```
SEPARATE PLANES     read path vs write path vs analytics path — scale and fail
                    independently (shortener redirects, feeds, bookings, logs).
PRECOMPUTE          fan-out-on-write timelines, autocomplete top-k, materialized
                    dashboards, CDN prewarm — spend write-time to buy read-time.
CELEBRITY/HOT KEY   hybrid push-pull, L1 caches, sharded counters, per-SKU queues,
                    finer geo-cells — every domain has its celebrity.
THE ARBITER         exactly ONE strongly-consistent decision point per invariant:
                    calendar row (booking), inventory row (stock), ledger (money),
                    unique constraint (usernames). Everything else can be eventual.
HOLD + TTL + SWEEP  reservations (seats, stock, locks) expire; janitors reconcile.
IDEMPOTENCY         keys on every mutating API; dedup records in-transaction;
                    at-least-once everywhere ⇒ consumers dedupe (chat, payments,
                    notifications, analytics).
QUEUE AS SHOCK      Kafka absorbs bursts (orders, notifications, logs, events);
 ABSORBER           lag is the health metric; retention is the outage budget.
STATE MACHINES      trips, orders, payments, bookings — explicit statuses,
                    idempotent transitions, visible intermediate states.
DERIVED READ MODELS CDC → ES/caches/warehouses; rebuildable, lag-monitored;
                    final check against the arbiter catches phantoms.
GEO/DOMAIN SHARDING city for Uber, conversation for chat, seller/listing for
                    marketplaces, domain for crawlers — shard key = access pattern
                    + isolation boundary.
CLIENT AS COMPONENT debounce (autocomplete), ABR (video), resume cursors (chat),
                    offline buffers (analytics), retry+jitter — design the client.
REGENERABLE STATE   location cells, timelines, caches, read models — losable state
                    that rebuilds beats precious state that can't.
```

## Mock Interview Drill (Module 13)

Pick any problem above; give yourself 35 minutes and produce, in order:
requirements (5) → capacity (3) → API (3) → data model (5) → high-level diagram
(5) → one deep dive chosen by "what's hardest here" (10) → failure + monitoring
sweep (4). Then check: did you name the arbiter? the hot key? the queue? the
idempotency story? Those four questions catch 90% of missed points.

# Module 3 — Caching

Caching is the highest-leverage performance tool in system design and the source of
some of the nastiest production incidents (stampedes, hot keys, stale data). Every
interview design should state: what is cached, where, with which pattern, which TTL,
and how it's invalidated.

---

## 3.1 Why Caching Works (and the Cache Hierarchy)

### Why Interviewers Ask This

They want the *reasoning*, not the buzzword: caching works because of skewed access
patterns — and it fails when those assumptions don't hold.

### Core Concept

Caching exploits three facts:

1. **Temporal locality** — recently accessed data is likely accessed again.
2. **Popularity skew (Zipf)** — a tiny fraction of keys gets most traffic. Roughly, the top ~10% of items can serve ~90% of requests. This is why a cache 1/100th the size of your dataset can absorb most reads.
3. **Cost asymmetry** — RAM read (~100 ns local, ~0.5 ms networked) vs DB query (1–50 ms) vs recomputation (arbitrary).

The math that matters: **effective latency = hit_ratio × cache_latency +
(1 − hit_ratio) × miss_latency**, and **origin load = (1 − hit_ratio) × traffic**.
Going from 90% → 99% hit ratio cuts origin load **10×** — hit-ratio improvements
are logarithmic in effort but multiplicative in effect.

Where caches live (a request may hit all of these):

```
browser cache → CDN edge → API gateway cache → app in-process cache (L1)
     → distributed cache: Redis/Memcached (L2) → DB buffer pool → disk
```

- **Browser cache**: `Cache-Control`, `ETag`/`If-None-Match` (304 revalidation), immutable versioned assets. Free, per-user, zero server cost.
- **CDN cache**: Module 2.4 — shared, geographic.
- **In-process (L1)**: nanosecond access, per-instance, small (Caffeine/Guava); risk: N instances = N inconsistent copies; use short TTLs (seconds) or pub/sub invalidation.
- **Distributed (L2)**: Redis/Memcached — shared truth for the fleet, millisecond access, the main character of this module.

### Common Mistakes

- Caching data with uniform access (no skew) or write-mostly data — hit ratio will be terrible; know *why* your data caches well.
- Ignoring that a cache is a *derived* copy: every cache adds a consistency problem you must explicitly manage.

### Interview Questions

1. Your cache hit ratio is 60% — is adding RAM the fix? (Investigate first: TTL too short? key cardinality too high? churn? uniform access?)
2. Show the load math: 100k QPS at 95% vs 99% hit ratio → 5k vs 1k QPS to the DB.

---

## 3.2 Redis vs Memcached

### Why Interviewers Ask This

The default cache-technology decision; they check you know both and can justify a
choice beyond "Redis is popular".

### Core Concept & Internal Working

**Memcached**: pure, multithreaded, in-memory key→bytes LRU cache. Slab allocator
(fixed size-class chunks → no fragmentation, but memory waste per item). Scales
vertically across cores and horizontally by *client-side* consistent hashing —
servers don't know about each other. No persistence, no replication, no data
structures. Dead simple = its virtue.

**Redis**: single-threaded event loop (commands execute atomically — no locks needed;
I/O threads since 6.0 help with network overhead). Rich data structures: strings,
hashes, lists, **sets, sorted sets (leaderboards, rate limiters)**, streams, bitmaps,
HyperLogLog (approximate distinct counts in 12 KB), geo indexes. Optional
persistence: **RDB** snapshots (fast restart, may lose last minutes) and **AOF**
append-only log (fsync policies; slower, safer). **Replication** (async, leader→
replica) + **Sentinel** (failover) or **Redis Cluster** (16,384 hash slots sharded
across nodes, each slot range with replicas; client redirects via MOVED/ASK).
Also: pub/sub, Lua scripting (atomic multi-step ops), transactions, TTL per key,
eviction policies (`allkeys-lru`, `allkeys-lfu`, `volatile-ttl`...).

```
 Redis Cluster:  keys ──CRC16 mod 16384──► slot ──► node
   node A (slots 0–5460)   + replica A'
   node B (slots 5461–10922)+ replica B'      client caches slot map;
   node C (slots 10923–16383)+ replica C'     MOVED on resharding
```

### Real Production Example

Meta runs one of the largest Memcached fleets ever (the classic "Scaling Memcache at
Facebook" paper: leases to prevent stale-set races and thundering herds, regional
pools, cold-cluster warmup). Twitter/X historically ran both (Twemcache + Redis for
timelines — sorted sets are literally the timeline structure). GitHub, Stripe,
Airbnb: Redis for cache + rate limiting + queues + locks.

### Advantages / Trade-offs

| | Memcached | Redis |
|---|---|---|
| Model | bytes only, LRU | data structures, scripting |
| Threading | multithreaded (big single nodes) | single-threaded core (shard for CPU) |
| Persistence/replication | none | RDB/AOF, replicas, Cluster |
| Simplicity | extremely simple | more features, more ops surface |
| Use when | pure look-aside page/object cache at huge scale | anything else: counters, leaderboards, sessions, locks, queues, rate limits |

### Common Mistakes

- Using Redis as a durable primary store without understanding AOF/RDB loss windows and failover semantics (async replication can lose acknowledged writes on failover).
- Multi-key operations across Redis Cluster slots (not supported without hash tags `{user123}:...`).
- Storing huge values (MBs) — blocks the single thread; keep values small, use pagination/compression.

### Monitoring & Failure

- Watch: hit ratio, evictions, memory fragmentation ratio, connected clients, slow log, replication lag, keyspace per node (skew).
- Failure: eviction storms when memory is full (suddenly everything misses), full sync avalanches after failover, `KEYS *` in production blocking the loop (use SCAN).

### Interview Questions

1. Redis vs Memcached for session storage? (Redis: replication + persistence survive restarts)
2. How does Redis Cluster shard and what breaks? (hash slots; multi-key ops, big values, resharding moves)
3. Is Redis single-threaded a problem? (atomicity win; shard/Cluster for CPU; I/O threads for network)

### Best Practices

- Treat cache as ephemeral even with persistence; the DB is the source of truth.
- Small values, TTL on every key, `allkeys-lfu` for skewed workloads, hash tags for related keys, never `KEYS` in prod.

---

## 3.3 Caching Patterns: Cache-Aside, Write-Through, Write-Back, Write-Around

### Why Interviewers Ask This

The pattern determines your consistency model, failure behavior, and write latency.
"Which pattern and why" is a guaranteed follow-up to any cache in your diagram.

### Core Concept & Internal Working

**Cache-aside (lazy loading)** — the default; the *application* manages the cache:

```
READ:  get(key) → HIT: return
                → MISS: read DB → set(key, ttl) → return
WRITE: write DB → DELETE cache key   (invalidate, don't update!)
```

Why delete instead of set on write: two concurrent writes can set the cache in the
wrong order (stale value wins); delete forces the next read to fetch fresh. There is
still a small race (read misses → reads old DB value → write commits + invalidates →
stale set lands after the delete). Mitigations: TTL as backstop, or Meta-style
**leases** (cache issues a token on miss; a set is only accepted with a valid,
uninvalidated token).

**Write-through** — the cache sits in the write path; every write updates cache +
DB synchronously. Cache is always fresh for written keys; write latency = cache +
DB; you cache things that may never be read (combine with TTL).

**Write-back (write-behind)** — write to cache, ACK immediately, flush to DB
asynchronously (batched/coalesced). Fastest writes, absorbs bursts, coalesces hot-key
updates (great for counters: view counts, likes). Cost: **acknowledged data can be
lost** if the cache dies pre-flush → need replicated cache or a durable log in front;
complexity of flush ordering and retries. This is also literally how CPU caches and
OS page caches work.

**Write-around** — write to DB only (optionally invalidate); cache fills on read.
For write-heavy or write-once-rarely-read data (logs, bulk imports) so writes don't
churn the cache.

```
             write path                    read path
cache-aside   DB, then DEL cache          app fills cache on miss
write-through cache+DB sync (both fresh)  always hit for written keys
write-back    cache ACK → async DB        hit; DB is behind (loss window!)
write-around  DB only                     fills on first read (one miss)
```

### Real Production Example

Meta: cache-aside + deletes + leases at extreme scale. DynamoDB Accelerator (DAX):
write-through for a managed experience. Gaming leaderboards and metrics pipelines:
write-back through Redis with periodic flush. Analytics event ingestion:
write-around (events go to the pipeline; nobody rereads them via cache).

### Common Mistakes

- Updating (SET) the cache on write in cache-aside → the classic stale-forever race. Say "invalidate on write" in interviews.
- Proposing write-back without addressing the loss window and flush-failure handling.
- One pattern for everything: real systems mix (aside for entities, write-back for counters, around for bulk writes).

### Interview Questions

1. Walk through the cache-aside race and how leases fix it.
2. When is write-back worth the risk? (high-frequency counters, burst absorption; loss tolerable or log-backed)
3. Which pattern for a product catalog? For view counters? For log ingestion? (aside / write-back / around)

### Best Practices

- Default: cache-aside + delete-on-write + TTL backstop.
- Every key gets a TTL — TTLs are your self-healing mechanism against every missed invalidation bug.

---

## 3.4 Cache Invalidation

### Why Interviewers Ask This

"There are only two hard things in computer science: cache invalidation and naming
things." They want your strategy for keeping derived copies honest, across *all*
cache layers.

### Core Concept & Internal Working

Strategies, weakest to strongest:

1. **TTL-only**: bounded staleness, zero coordination. Choose TTL = max tolerable staleness. Add ±10–20% **jitter** so a popular deploy/warmup doesn't expire everything simultaneously.
2. **Explicit invalidation on write**: delete keys when the source changes. Hard parts: knowing *all* keys derived from a row (entity key, list pages, aggregates, search results...), multi-layer fan-out (in-process L1s on N instances + Redis + CDN), and failure between DB commit and cache delete.
3. **Event-driven invalidation**: publish DB changes via **CDC** (Debezium reading the binlog → Kafka) and have consumers invalidate/refresh caches. Decouples producers from every cache; guarantees invalidation eventually happens even if the app crashed post-commit. This is how Meta wires MySQL → memcache invalidation across regions.
4. **Versioned keys**: don't invalidate — change the key (`user:123:v42`, or key = hash of content). Old entries age out via TTL/eviction. Perfect for CDN assets and computed results.

Delivery to in-process caches: pub/sub broadcast (Redis pub/sub, Kafka topic) of
invalidation events to all instances.

### Common Mistakes

- Forgetting derived/aggregate keys (invalidate `user:123` but not `team:9:members` page cache).
- No TTL backstop ("we invalidate explicitly, TTL unnecessary") — one lost delete = stale forever.
- Invalidating *before* the DB commit (a concurrent read re-fills stale data), or not handling delete failures (retry queue).

### Interview Questions

1. Price changes must appear within 5 s across CDN + Redis + in-process caches. Design the invalidation.
2. What is CDC-based invalidation and why does Meta use it?
3. Versioned keys vs purge — when each?

### Best Practices

- TTL everywhere + explicit/event-driven invalidation on top; jitter all TTLs; prefer versioned keys wherever the key can encode the version.

---

## 3.5 Cache Stampede (Thundering Herd)

### Why Interviewers Ask This

It's the classic cache-related outage: the cache *protects* the DB until the moment
it doesn't — and the follow-up "what happens when the cache node restarts?" is nearly
guaranteed.

### Core Concept

A popular key expires (or a cache node dies) → thousands of concurrent requests miss
simultaneously → all of them hit the DB with the same expensive query → DB saturates
→ latency rises → more timeouts and retries → cascade. One key can take down the
database.

### Internal Working — the four defenses

1. **Request coalescing / single-flight**: only one request per key recomputes; others wait on the in-flight result. In-process: Go `singleflight`, Caffeine loading cache. Cross-fleet: a short-TTL Redis lock (`SET lock:key token NX PX 3000`) — winner recomputes, losers wait/poll or serve stale.
2. **Stale-while-revalidate**: keep serving the expired value while one background worker refreshes. Users see slightly-stale data; the DB sees one query.
3. **Probabilistic early expiration (XFetch)**: each reader refreshes *before* expiry with probability increasing as TTL approaches (`refresh if now − Δ·β·ln(rand()) ≥ expiry`), so refreshes desynchronize naturally — no herd forms.
4. **TTL jitter**: prevents synchronized mass expiry across many keys (deploy warms 1M keys with TTL 3600 → all expire together an hour later).

For the cold-cache case (node restart, new cluster): **cache warming** (replay top-N
keys before taking traffic) and **gradual traffic ramp**; Meta's cold-cluster warmup
fills a new cluster from a warm one rather than from the DB.

```
 without protection:            with single-flight + stale-serve:
 10,000 misses ──► DB ☠         10,000 requests ─► 9,999 get stale value
                                                └► 1 recomputes ──► DB (1 query)
```

### Real Production Example

This pattern family is in Meta's memcache paper (leases solve stampede *and* the
stale-set race with one mechanism). CDNs implement it as request collapsing.
Internet-famous incidents: sites collapsing at cache-flush moments during deploys —
the fix is always some combination of the four defenses above.

### Interview Questions

1. The cache cluster restarts empty at peak. What happens next and what did you build to survive it?
2. Implement single-flight across 200 app instances. (Redis `SET NX PX` lock + serve-stale for losers)
3. Why does TTL jitter matter after a mass warmup?

### Best Practices

- Single-flight + serve-stale on every expensive key; jitter every TTL; cap concurrent DB load with a semaphore regardless (belt and suspenders: the DB should be *unable* to receive a stampede).

---

## 3.6 Hot Keys

### Why Interviewers Ask This

Sharding distributes *keys*, not *traffic*. A celebrity posts and one Redis shard
melts while nine idle. Interviewers use it to test whether you understand skew.

### Core Concept & Internal Working

A hot key is a single key receiving a disproportionate share of ops (Zipf tail:
celebrity profile, flash-sale product, global config, viral tweet). Since one key
lives on one shard (one single-threaded Redis node ≈ 100k–1M ops/s ceiling), no
amount of horizontal scaling helps — the unit of distribution is the key.

Defenses:

1. **In-process L1 cache** for the hottest keys — even a 1–5 s local TTL absorbs virtually all reads for a viral key (each app instance asks Redis once per second instead of 10k times). The single best fix; costs bounded staleness.
2. **Key replication**: write `key#0..key#N` copies on different shards; readers pick a random replica. N× read capacity; writes must update all copies (reads-mostly keys only).
3. **Hot-key detection**: sample traffic (Redis `--hotkeys`, client-side sampling, proxy stats) and *automatically* promote hot keys to L1/replicated handling — hotness is dynamic and unpredictable.
4. For hot **counters** (likes on a viral post): shard the counter (`count:{post}:{rand%16}`, read = sum) or batch increments in-process and flush.

```
 celebrity key "user:justin" 500k reads/s
     └► shard 3 (one node) ☠
 fix: app-local L1 (ttl 2s) ──► ~N_instances reads/s to Redis  ✓
      + replicas key#0..#9  ──► 10 shards share the remainder ✓
```

### Real Production Example

Every social network. Twitter's timeline architecture treats celebrities as a
special case end-to-end (Module 13). DynamoDB historically punished hot partitions
(throughput was per-partition; adaptive capacity was built to auto-mitigate).
Alibaba/Redis operators publish hot-key detection proxies for exactly the
flash-sale scenario.

### Interview Questions

1. One product page gets 100× traffic during a flash sale — where does your cache break and what's the fix?
2. Why doesn't adding Redis shards help a hot key?
3. Design a hot-counter for likes at 1M increments/min.

### Best Practices

- Assume skew always; L1 with short TTL for read-hot, sharded counters for write-hot, automated detection because you can't predict virality.

---

## 3.7 Distributed Cache Architecture

### Why Interviewers Ask This

"Design a distributed cache" is itself a full interview question (Module 13.23), and
every real design contains one; you must know how the pieces compose.

### Core Concept & Internal Working

A distributed cache = many nodes each owning a partition of the keyspace:

- **Partitioning**: consistent hashing (client-side, or via proxy like Twemproxy/Envoy, or server-side like Redis Cluster hash slots). Consistent hashing (Module 11.1) means adding/removing a node remaps only ~1/N of keys — no global reshuffle, no fleet-wide cold cache.
- **Replication**: each partition has replicas for read scaling + fast failover; async replication = possible brief staleness/loss on failover (fine for a cache).
- **Eviction**: LRU (recency), **LFU** (frequency — better under scans and skew; Redis `allkeys-lfu`, W-TinyLFU in Caffeine), TTL-based. Memory is the budget; eviction policy decides who pays.
- **Client behavior is part of the design**: timeouts (a cache call slower than ~50 ms should fail fast — falling through to the DB is better than queueing), circuit breaking, and *degradation policy*: cache down ⇒ serve from DB with a concurrency cap + load shedding, or serve stale/default data. The DB must survive cache death — that's a capacity-planning requirement, not a hope.

```
 apps (cache-aside, single-flight, L1)
   │  consistent hashing / cluster slot map
   ▼
 ┌──────┬──────┬──────┬──────┐
 │ node1│ node2│ node3│ node4│   each owns ~25% of keys
 │  +r  │  +r  │  +r  │  +r  │   async replica per node
 └──────┴──────┴──────┴──────┘
 node2 dies → its slots fail over to replica; only ~25% of keys affected;
 single-flight + DB concurrency cap absorb the refill.
```

### Interview Questions

1. A cache node dies — trace exactly what happens to hit ratio, DB load, and latency, and what limits the damage.
2. LRU vs LFU — when does LRU fail? (scans/batch jobs evict the hot working set; LFU/W-TinyLFU resists)
3. Where do you put the partitioning logic: client, proxy, or server? (client = fewest hops but N client configs; proxy = central control + extra hop; server (Redis Cluster) = self-managing + client library support needed)

### Best Practices

- Consistent hashing + replicas + LFU for skewed workloads; aggressive client timeouts; explicit "cache is down" degradation mode, load-tested.

---

## Module 3 Cheat Sheet

```
WHY IT WORKS   Zipf skew: ~10% of keys ≈ 90% of traffic. eff_lat = h·L_hit+(1−h)·L_miss.
               90%→99% hit ratio = 10× less origin load.
LAYERS         browser → CDN → gateway → in-process L1 → Redis/Memcached L2 → DB buffer.
REDIS          single-threaded atomic core, data structures, RDB/AOF, Sentinel/Cluster
               (16384 slots). Counters, zsets, locks, rate limits, sessions.
MEMCACHED      multithreaded LRU bytes, client-side sharding, dead simple. Pure lookaside.
PATTERNS       aside: read-miss-fill, WRITE ⇒ DB then DELETE key (+leases for race).
               write-through: sync both (fresh, slower writes).
               write-back: ACK at cache, async flush (fast, LOSS WINDOW; counters).
               write-around: DB only, fill on read (bulk/write-heavy).
INVALIDATION   TTL(+jitter) always as backstop → explicit deletes → CDC/event-driven
               (Debezium→Kafka) → versioned keys (best: never invalidate).
STAMPEDE       single-flight (lock/lease), stale-while-revalidate, probabilistic early
               refresh, TTL jitter, warmup + ramp for cold clusters, DB concurrency cap.
HOT KEYS       one key = one shard = ceiling. L1 short-TTL cache, key replication #0..N,
               sharded counters, automated hot-key detection.
DISTRIBUTED    consistent hashing (≈1/N remap), replicas, LFU>LRU under scans,
               fail-fast timeouts, planned degradation: DB must survive cache death.
```

## Top Interview Questions (Module 3)

1. Design the caching for a product page (layers, pattern, TTLs, invalidation).
2. Cache-aside race + leases. 3. Full cache-cluster restart at peak — survival plan.
4. Celebrity hot key mitigation. 5. Redis vs Memcached, with a use case for each.
6. Write-back for counters: benefits + loss-window handling. 7. CDC-driven
invalidation pipeline. 8. LRU vs LFU under a table scan. 9. Multi-layer invalidation
within 5 s. 10. Why every key needs a TTL even with perfect invalidation.

## Common Mistakes Recap

SET-on-write in cache-aside • no TTL backstop • no stampede protection • ignoring
skew/hot keys • huge Redis values • Redis-as-durable-primary without understanding
failover loss • uniform TTLs (mass expiry) • no degradation plan for cache death.

## Mock Interview Exercise

*"Your e-commerce site: 150k QPS product reads, 200 writes/s (price/stock), flash
sales spike one product 500×, business tolerates 2 s price staleness."* Produce: L1
(1–2 s TTL) + Redis cluster (aside, delete-on-write via CDC, TTL 5 min jittered) +
CDN for rendered fragments; single-flight everywhere; sharded stock counters;
hot-key auto-promotion; DB capacity floor for cache-loss mode. Then defend the 2 s
staleness budget against the CDC path latency.

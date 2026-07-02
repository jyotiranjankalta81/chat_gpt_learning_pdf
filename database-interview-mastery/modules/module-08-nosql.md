# MODULE 8 — NoSQL

> System-design rounds require fluency in four systems — MongoDB, Redis, Cassandra, DynamoDB —
> plus the two mechanisms underneath them all: **LSM trees** and **consistent-hash replication**.
> The winning skill: choosing by access pattern and naming the sacrifice.

Chapters:
8.1 When to Choose NoSQL (Decision Framework)
8.2 Data Models: Document vs Key-Value vs Wide-Column
8.3 LSM Trees — The Write-Optimized Engine
8.4 MongoDB
8.5 Redis (as a Data Store)
8.6 Cassandra
8.7 DynamoDB
8.8 Replication, Sharding & CAP Across NoSQL (Comparison)

---

## Chapter 8.1 — When to Choose NoSQL

### 1. Why Interviewers Ask This
The opening move of most system-design interviews. They're screening for engineering judgment:
candidates who choose by workload numbers and access patterns vs candidates who choose by hype.

### 2. Core Concept
Choose NoSQL when you can name **which of these you're buying**:
1. **Write scale beyond one primary** (Cassandra/DynamoDB: horizontal, masterless or managed).
2. **Access-pattern simplicity at huge data volume** (get/put by key; no ad-hoc queries needed).
3. **Availability over consistency** (must accept writes during partitions).
4. **Latency floors** (Redis in-memory; DynamoDB single-digit ms at any scale).
5. **Schema volatility on cheap terms** (documents; though Postgres jsonb covers much of this).

And you must name **what you pay**: joins, ad-hoc queries, multi-row ACID (limited), constraints,
mature migrations — moved into application code. The senior framing: *"Postgres until a specific
workload breaks it, then move that workload"* — and be ready to defend the reverse when the
interviewer plays devil's advocate (known access patterns + huge scale from day one, e.g.
IoT firehose → start with Cassandra/DynamoDB for that table).

### 3. Internal Working
The reason NoSQL scales writes is architectural, not magic: **no cross-node coordination on the
write path** (per-key ownership via hashing, quorum-local decisions) + **write-optimized
storage** (LSM — 8.3) + **no global constraints/transactions to enforce**. Every capability
they dropped is a coordination cost they don't pay. That's also the precise list of what you
lose.

### 4. Visualization (ASCII)
```
Decision flow:
  need ad-hoc queries / joins / multi-row ACID?  ──yes──▶ RDBMS (+ cache/replicas)
        │ no
  access pattern = known key-based lookups?      ──no───▶ rethink; probably RDBMS/warehouse
        │ yes
  scale > single-primary write ceiling? latency floor? AP required?
        │ yes                                   │ no
        ▼                                       ▼
  KV/wide-column (Dynamo/Cassandra)         Postgres (jsonb if flexible shape)
  ephemeral/μs? → Redis    nested docs, mid-scale, rich secondary queries? → MongoDB
```

### 5. Real Production Example
Netflix: viewing history = per-member key, append-heavy, planet-scale, staleness-tolerant →
Cassandra. Billing → MySQL. Amazon: cart availability during partitions → Dynamo lineage;
orders → relational + strong consistency. Discord (famous case study): messages MongoDB →
Cassandra → ScyllaDB as scale grew, keyed by channel — the access pattern (recent messages per
channel) never changed, the engine did.

### 6. Common Interview Questions
- "SQL or NoSQL for [design prompt]?" (answer per-table/workload, not per-system)
- "What specifically breaks in Postgres at scale that Cassandra fixes?" (single-primary write
  ceiling, B+Tree random-write amplification, manual sharding)
- "What do you lose leaving Postgres?" (recite the tax list)
- "Polyglot persistence — how do you keep stores consistent?" (single source of truth + CDC;
  idempotent consumers)

### 7. Common Mistakes
- "NoSQL because scale" with no QPS/data-size numbers.
- Choosing a document DB because "schema flexibility" then hand-building joins/transactions.
- Ignoring Postgres jsonb / partitioning / replicas as the boring adequate answer.
- One database for everything (either direction) at a company past a certain size.

### 8. Best Practices
- Lead with access patterns + numbers, choose engine per workload, name the sacrifice, add the
  consistency-repair plan (CDC, reconciliation).
- Keep the system of record transactional wherever money/identity is involved.

### 9. Coding Questions
1. For a ride-hailing app, assign stores to: trips ledger, driver live locations, surge-pricing
   zones, chat, receipts search — with one-line justifications.
2. Estimate: 200k writes/s, 2KB each, key-value reads by id only, 99.9% availability across
   regions — argue Cassandra/DynamoDB over Postgres with arithmetic (per-node write ceilings,
   shard count).

### 10. SQL Examples
```sql
-- The honest middle ground first: Postgres as document store
CREATE TABLE profiles (
  user_id bigint PRIMARY KEY,
  doc jsonb NOT NULL
);
CREATE INDEX ON profiles USING gin (doc jsonb_path_ops);
SELECT doc->'settings'->>'theme' FROM profiles WHERE user_id = 42;
UPDATE profiles SET doc = jsonb_set(doc, '{settings,theme}', '"dark"') WHERE user_id = 42;
-- If this covers your "NoSQL need", you kept transactions and joins for free.
```

### 11. Optimization Techniques
- Hybrid: RDBMS system-of-record + NoSQL projections (feeds, caches, search) built via CDC —
  the architecture most FAANG answers converge to.
- Prove the bottleneck before migrating: pg_stat_statements + load tests beat vibes.

### 12. Follow-up Questions
- "Your PM wants 'flexible schema' — cheapest way to give it?" (jsonb column, not a new database)
- "When would you *start* on NoSQL day one?" (known KV pattern + guaranteed scale, e.g.
  telemetry; or team is DynamoDB-native and access patterns are stable)

---

## Chapter 8.2 — Data Models: Document, Key-Value, Wide-Column

### 1. Why Interviewers Ask This
Modeling is where NoSQL projects die. The interview form: "model X in DynamoDB/Mongo" — testing
whether you design **from queries backwards** and denormalize on purpose.

### 2. Core Concept
- **Key-Value** (Redis, DynamoDB at its simplest): opaque value by key. One access pattern:
  get/put by key. Fastest, dumbest, scale-perfect.
- **Document** (MongoDB, DynamoDB items): JSON-ish tree per key; secondary indexes on fields;
  query within documents. Model: **embed what you read together** (1:few, bounded, co-accessed);
  **reference what grows unboundedly or is shared** (1:many-unbounded, many:many).
- **Wide-column** (Cassandra): rows grouped into **partitions** by partition key; within a
  partition, rows ordered by **clustering keys**. Think "one B-tree-ish sorted structure per
  partition key." Model: **one table per query**; partition key = the WHERE equality; clustering
  keys = the ORDER BY / range.

Universal NoSQL modeling law: **you denormalize; duplication is a feature; the application
maintains consistency between copies.**

### 3. Internal Working
Embedding wins because one key fetch = one disk/network op returning everything (data locality);
referencing forces N+1 fetches (no joins server-side — Mongo `$lookup` exists but is a
single-node aggregation tool, not a scale primitive). Document size limits (Mongo 16MB;
DynamoDB item 400KB) are why unbounded arrays (comments on a viral post) must be referenced or
bucketed. Wide-column partitions map to a contiguous on-disk (LSM) run per node — in-partition
range reads are sequential and cheap; cross-partition scans are cluster-wide and forbidden by
culture.

### 4. Visualization (ASCII)
```
Document (embed vs reference):
order doc: { _id, user_id,                 user doc: { _id, name, ... }
  items: [ {sku, name, price, qty}, ... ]   ← embed: bounded, read together ✔
  status, total }
post doc:  { _id, author_id,
  comments: [ ...unbounded!... ] }          ← WRONG: reference/bucket comments ✖

Wide-column (Cassandra):
PARTITION KEY user_id │ CLUSTERING key created_at DESC
user:42 ──▶ [ (2026-07-01, order 9) (2026-06-28, order 8) (2026-06-01, order 7) ... ]
             └── sorted within partition: "last 10 orders of user 42" = one seek + scan ✔
"orders over $100 across all users" = full cluster scan ✖ (make another table for it)
```

### 5. Real Production Example
DynamoDB **single-table design** (AWS-canon): `PK=USER#42 / SK=PROFILE`,
`PK=USER#42 / SK=ORDER#2026-07-01#9`, `PK=ORDER#9 / SK=ITEM#1` — one Query by PK returns a
user's profile + recent orders in one round trip (an "item collection" replacing a join).
Discord messages: partition = `(channel_id, bucket)` (time-bucketed to cap partition size),
clustering = message_id desc — "recent messages in channel" is the one query that matters.

### 6. Common Interview Questions
- "Embed or reference for [user/orders, post/comments, product/reviews]?" (bounded? co-read?
  shared? growth?)
- "Model an e-commerce order system in DynamoDB." (single-table, item collections, GSIs)
- "Why does Cassandra require query-first modeling?" (partition-key-only access; no joins;
  duplication tables)
- "What's an unbounded-array bug in Mongo and its fix?" (16MB doc limit; bucketing pattern)

### 7. Common Mistakes
- Porting 3NF into documents (a document per SQL table + app joins = worst of both worlds).
- Embedding unbounded growth (comments, events) → document rewrite cost + size limits.
- Cassandra partition keys with unbounded partitions (partition per *user* for an IoT firehose →
  multi-GB partitions; add time buckets).
- Forgetting update fan-out: duplicated author name across 1M posts needs a rename strategy
  (async backfill + tolerate staleness — say it explicitly).

### 8. Best Practices
- Write the access-pattern table FIRST (operation, key, frequency); every table/index maps to
  rows of it.
- Bound everything: array sizes, partition sizes (Cassandra target <100MB, <~100k rows),
  item sizes.
- Duplicate immutable/slow-changing data freely; for mutable duplicates, define the sync
  mechanism and staleness budget at design time.

### 9. Coding Questions
1. Model Twitter-lite in Cassandra: tables for user timeline (fan-out-on-write), user's own
   tweets, tweet by id, followers — give full PRIMARY KEY (partition, clustering) for each.
2. Single-table DynamoDB for a hotel: entities Hotel, Room, Booking, Guest; list the access
   patterns and the PK/SK (+GSI) design that serves each.

### 10. SQL Examples
```text
-- Cassandra CQL (query-first tables)
CREATE TABLE orders_by_user (
  user_id bigint, created_at timestamp, order_id bigint,
  total decimal, status text,
  PRIMARY KEY ((user_id), created_at, order_id)
) WITH CLUSTERING ORDER BY (created_at DESC);
SELECT * FROM orders_by_user WHERE user_id = 42 LIMIT 10;   -- the one true query

-- MongoDB
db.orders.insertOne({ user_id: 42, status: "paid",
  items: [{ sku: "A1", name: "Widget", price_cents: 4999, qty: 2 }] })
db.orders.find({ user_id: 42 }).sort({ created_at: -1 }).limit(10)
db.orders.createIndex({ user_id: 1, created_at: -1 })
```

### 11. Optimization Techniques
- Bucketing pattern for unbounded lists (comments page-1 doc, page-2 doc…).
- Computed/duplicated aggregates on the parent (counts, latest) maintained on write.
- Sparse GSIs (DynamoDB) / partial indexes (Mongo) for rare-state queries.

### 12. Follow-up Questions
- "A new access pattern arrives post-launch — compare the cost in Postgres vs DynamoDB."
  (add an index vs redesign keys/backfill a GSI — the flexibility tax made concrete)
- "How do you paginate within a Cassandra partition and across partitions?" (clustering-key
  keyset within; you don't across — design a table for it)

---

## Chapter 8.3 — LSM Trees

### 1. Why Interviewers Ask This
The storage-engine question that explains *why* Cassandra/RocksDB/DynamoDB-class systems write
fast. Pairs with B+Tree (Module 4) as the fundamental engines duality; staff-level candidates
are expected to compare them fluently.

### 2. Core Concept
**Log-Structured Merge tree**: never update in place — buffer writes in memory, flush sorted
files, merge in background.

Write path: append to **WAL/commit log** (durability) → insert into **memtable** (sorted
in-memory structure) → when full, flush as an immutable sorted file (**SSTable**) →
background **compaction** merges SSTables (dedup keys, drop tombstones, maintain sorted runs).

Read path: memtable → recent SSTables → older ones; accelerated by **bloom filters** (skip
files that definitely lack the key) and per-file index/summary blocks.
Deletes = write a **tombstone** (the delete is data until compaction purges it).

Trade profile vs B+Tree:
- Writes: sequential-only I/O, no page splits → very high throughput ✔
- Reads: potentially multi-file (read amplification) ✖ (bloom filters mitigate point reads;
  range reads touch every overlapping file)
- Space: duplicates+tombstones until compaction (space amplification) ✖
- Compaction: background I/O/CPU tax that *must* keep up (write stalls when it doesn't) ✖

Compaction strategies: **size-tiered** (merge similar-sized files; write-cheap, read/space-
worse) vs **leveled** (RocksDB/LevelDB: non-overlapping levels; read/space-better, more write
amplification) — choose by read/write ratio.

### 3. Internal Working
Everything sequential: commit-log append, SSTable flush, compaction streams — the disk never
seeks on the write path (this single sentence is the "why fast" answer). SSTables immutable →
no locks for readers, trivial caching, cheap replication (ship files). Read amplification math:
point read worst case = memtable + one bloom-filter check per SSTable + 1–2 actual file reads;
range scan = k-way merge across all overlapping files. Tombstone hazards: reading a key with
millions of tombstones (queue-like workloads) scans them all — the famous "queues on Cassandra"
anti-pattern.

### 4. Visualization (ASCII)
```
WRITE:  key=42 ──▶ commit log (append, fsync) ──▶ memtable (sorted, RAM)
                                                     │ full
                                                     ▼ flush (sequential)
DISK:   SSTable-9 (newest)  SSTable-8  SSTable-7  ...  SSTable-1 (oldest)
             └──────────── compaction merges ─────────────┘
                   [k1..k9]+[k2..k7] → [k1..k9] dedup'd, tombstones dropped

READ key=42: memtable? no → bloom(SST-9)? maybe → read → found ✔
             (bloom "no" skips a file entirely)

B+Tree write: seek page, maybe split, write in place  (random I/O)
LSM    write: append, append, append                  (sequential I/O)  → 10-100x ingest
```

### 5. Real Production Example
RocksDB is the LSM everyone actually runs: it backs Kafka Streams state, CockroachDB (originally),
TiKV, MyRocks (Meta's MySQL storage engine — Meta moved user DBs to MyRocks largely for **space
amplification wins on SSDs**, ~50% storage savings), and every Cassandra-class store. Interview
staple: "your ingest is 1M events/sec — B+Tree or LSM and why?" → LSM, sequential-write
argument, then discuss the read/compaction bill.

### 6. Common Interview Questions
- "Explain LSM trees end to end." (write path, read path, compaction, tombstones)
- "LSM vs B+Tree — when each?" (write-heavy/append vs read-heavy/point-update)
- "What are bloom filters for here?" (skip SSTables on point reads; no false negatives)
- "Why are deletes expensive in LSM systems?" (tombstones live until compaction; range-delete
  pileups)
- "What are write/read/space amplification?" (define all three; compaction strategy trade)

### 7. Common Mistakes
- "LSM is faster" unqualified — faster *writes*; reads pay.
- Forgetting compaction is a first-class operational concern (falling behind = stalls, bloat).
- Queue workloads (write-then-delete) on LSM stores — tombstone hell.
- Missing that Postgres/InnoDB *also* sequence writes via WAL — the difference is the *data
  structure* maintenance (in-place B+Tree pages vs immutable merged files).

### 8. Best Practices
- Match compaction strategy to workload (size-tiered for ingest-heavy, leveled for read-heavy).
- Monitor compaction debt (pending compactions, SSTables-per-read) like you monitor vacuum in PG.
- Design keys so hot ranges don't collide with compaction (time-series: time-bucketed keys,
  TTL-based expiry drops whole SSTables free).

### 9. Coding Questions
1. Trace: write k=1..5, flush; write k=3(update),6, flush; delete k=2, flush. Show the three
   SSTables' contents, the answer to `read k=2` and `read k=3`, then the post-compaction file.
2. Estimate write amplification for leveled compaction with 10x level fanout and 5 levels
   (each byte rewritten ~once per level → ~5–10x) and compare with B+Tree page-write cost for
   random small updates.

### 10. SQL Examples
```text
-- Cassandra: observe the LSM surface
nodetool tablestats keyspace.orders_by_user   -- SSTable count, bloom fp rate
nodetool compactionstats                      -- compaction backlog (debt!)

-- TTL as free deletion (expired data drops with whole SSTables)
INSERT INTO events (...) VALUES (...) USING TTL 2592000;  -- 30 days
```

### 11. Optimization Techniques
- Rate-limit/burst-schedule compaction off-peak; provision I/O headroom for it.
- Larger memtables → fewer, bigger SSTables → less read amplification (RAM trade).
- Partition data so time-expired data dies by file drop (TTL + time-windowed compaction
  strategy), never by tombstone flood.

### 12. Follow-up Questions
- "How does a bloom filter work and what's its guarantee?" (bit array + k hashes; false
  positives possible, false negatives never — sizing math if they push)
- "Why did Meta build MyRocks instead of staying on InnoDB?" (space+write amplification on
  SSDs; compression friendliness of immutable sorted files)
- "Where does Postgres feel LSM pressure?" (it doesn't have one natively; heavy-ingest use
  cases reach for timescale/partitioning or external stores — discuss honestly)

---

## Chapter 8.4 — MongoDB

### 1. Why Interviewers Ask This
The default document DB; interviewers test whether you know what it's actually good at (rich
documents, developer velocity, built-in sharding) and its sharp edges (transactions, joins,
the modeling discipline it silently demands).

### 2. Core Concept
- Documents (BSON) in collections; `_id` primary key; secondary indexes (B+Tree, on any field,
  compound, partial, TTL, text, geo); rich query + aggregation pipeline.
- **Replica sets**: 1 primary + N secondaries, automatic elections (Raft-like). Write concern
  `w:1` (fast, loss window) → `w:"majority"` (durable); read concern/preference tune staleness
  (`readPreference: secondary` = replica-lag reads).
- **Sharding** built in: shard key (hashed or ranged), mongos routers, config servers; chunks
  auto-split/balance.
- **Transactions**: single-document atomicity always (the design center); multi-document ACID
  since 4.0 (replica set) / 4.2 (sharded) — works, but costs latency and has limits; heavy use
  signals wrong data model.
- Storage: WiredTiger — B+Tree, document-level concurrency (MVCC-ish), compression.

### 3. Internal Working
Elections: majority voting, ~seconds of write unavailability on primary failure (retryable
writes paper over it). `w:majority` + `readConcern:majority` gives read-your-majority-writes;
weaker settings can *lose acknowledged writes on failover* (the historical Jepsen findings —
know they existed and that defaults improved: MongoDB 5+ defaults `w:majority`). Aggregation
pipeline executes stages server-side ($match/$group/$lookup); $lookup is a left outer join —
single-shard-friendly, cross-shard expensive.

### 4. Visualization (ASCII)
```
Replica set:                          Sharded cluster:
   ┌─────────┐  oplog   ┌───────────┐    app ──▶ mongos (router) ──▶ shard A (RS)
w ▶│ PRIMARY │ ───────▶ │ SECONDARY │                     │        ──▶ shard B (RS)
   └────┬────┘ ───────▶ │ SECONDARY │              config servers   ──▶ shard C (RS)
        │ fails          └───────────┘    chunks of shard-key range auto-balance
        ▼ election (majority) → new primary (seconds)
w:1        = ack from primary only  → failover may LOSE the write
w:majority = ack from majority      → survives failover ✔ (slower)
```

### 5. Real Production Example
Typical fit: product catalogs (deep varied attributes per category), CMS/content, user
profiles, IoT device state — read-mostly rich documents where embedding matches the UI.
The cautionary tale (interview-famous): startups modeling relational domains (orders ↔
inventory ↔ payments) in Mongo, discovering they need multi-document transactions everywhere,
migrating to Postgres — the lesson is model-fit, not engine quality.

### 6. Common Interview Questions
- "When MongoDB over Postgres?" (document-shaped, embed-friendly data; horizontal write scale
  with built-in sharding; velocity on evolving schemas — vs jsonb rebuttal ready)
- "Explain write concern / read concern and the durability spectrum."
- "How does a Mongo failover work and what happens to in-flight writes?"
- "Is MongoDB ACID?" (nuanced: per-document yes; multi-doc since 4.0 with costs)
- "How do you choose a shard key?" (same rules as Module 7.3: cardinality, uniformity,
  monotonic-key hotspot → hashed)

### 7. Common Mistakes
- `w:1` for data you can't lose.
- Monotonic shard key (ObjectId/timestamp, ranged) → all inserts hit one chunk/shard.
- Unbounded embedded arrays; documents rewritten wholesale per append.
- Using $lookup as a general join at scale.
- Ignoring that indexes here cost like anywhere (write amplification, RAM).

### 8. Best Practices
- `w:majority` + retryable writes for anything durable; explicit staleness budget for
  secondary reads.
- Schema-on-write validation (JSON Schema in collMod) — "schemaless" ≠ ungoverned.
- Shard keys: hashed on high-cardinality id, or compound (tenant, id); test with realistic
  distribution before committing (shard key is ~forever; 5.0+ resharding exists but is heavy).

### 9. Coding Questions
1. Design the order document + indexes for: orders by user (recent first), by status (rare
   states), item-sku lookup — write `createIndex` calls (compound, partial).
2. Write an aggregation: daily revenue by country last 30 days ($match → $group on
   $dateTrunc → $sort), and state where it runs in a sharded cluster.

### 10. SQL Examples
```text
// Durability spectrum
db.orders.insertOne(doc, { writeConcern: { w: "majority" } })

// Query + covering-ish index
db.orders.createIndex({ user_id: 1, created_at: -1 })
db.orders.find({ user_id: 42 }).sort({ created_at: -1 }).limit(10)

// Partial index for rare state
db.jobs.createIndex({ created_at: 1 }, { partialFilterExpression: { status: "pending" } })

// Multi-document transaction (use sparingly)
session.withTransaction(async () => {
  await orders.insertOne(order, { session });
  await inventory.updateOne({ sku, qty: { $gte: n } }, { $inc: { qty: -n } }, { session });
});
```

### 11. Optimization Techniques
- Keep the working set (indexes + hot docs) in RAM — WiredTiger cache sizing is the #1 knob.
- Project only needed fields (documents are fat; network+cache savings).
- Pre-aggregate with $merge into summary collections for dashboards.

### 12. Follow-up Questions
- "Postgres jsonb vs MongoDB — give the honest comparison." (PG: transactions/joins/one system,
  GIN indexes; Mongo: built-in sharding, richer doc-native ops, replica-set ergonomics)
- "What did Jepsen historically find and what changed?" (stale/lost writes under weak concerns;
  defaults hardened — shows you track correctness, not marketing)

---

## Chapter 8.5 — Redis (as a Data Store)

### 1. Why Interviewers Ask This
Beyond caching (Module 7.5), interviews use Redis to test data-structure-driven design:
leaderboards, rate limiters, queues, presence — "design X" where X is a Redis structure away.

### 2. Core Concept
Data structures and their interview jobs:
- **String** + INCR: counters, locks (SET NX PX), idempotency flags.
- **Hash**: object fields (HSET user:42 name ...), partial updates without whole-value rewrite.
- **List**: simple queues (LPUSH/BRPOP), capped feeds (LTRIM).
- **Set**: uniqueness, tags, membership (SISMEMBER), intersections (mutual friends).
- **Sorted Set (ZSET)**: leaderboards (ZADD/ZRANGE/ZRANK), sliding-window rate limits,
  delayed queues (score = run_at), top-K.
- **Streams**: append-only log with consumer groups (Kafka-lite for modest scale).
- HyperLogLog (approx distinct), bitmaps (daily-active flags), geo (nearby drivers), pub/sub
  (fire-and-forget fan-out).

Persistence reality: **RDB** snapshots (lose minutes) / **AOF** everysec (lose ~1s) /
replication is async → Redis can be *a* database only for loss-tolerant, ephemeral-by-nature
data (sessions, presence, rate limits, matchmaking). Single-threaded per instance → atomic
commands + Lua/MULTI for compound atomicity; Cluster = 16384 slots (Module 7.5).

### 3. Internal Working
Event loop processes one command at a time → every command is a critical section (atomic
INCR without locks; also why O(N) commands on big keys stall everyone). ZSET = skiplist +
hash (O(log N) rank ops). Keyspace expiry: lazy + active sampling. Eviction under maxmemory by
policy (LRU/LFU approximations). Fork-based RDB/AOF-rewrite uses copy-on-write — memory spikes
on write-heavy instances (the classic "why did Redis OOM during BGSAVE" question).

### 4. Visualization (ASCII)
```
Leaderboard (ZSET):                    Sliding-window rate limit (ZSET):
ZADD lb 9812 user:42                   key = rl:user:42, member = req-id, score = now-ms
ZREVRANGE lb 0 9 WITHSCORES → top 10   ZADD rl now req; ZREMRANGEBYSCORE rl 0 now-60000
ZREVRANK lb user:42 → my rank          ZCARD rl → count in window → allow if < limit
                                       (wrap in Lua for atomicity)
Delayed job queue (ZSET):
ZADD delayed <run_at_ms> job:77
poller: ZRANGEBYSCORE delayed 0 <now> LIMIT 1 → ZREM (atomic via Lua) → run
```

### 5. Real Production Example
Uber-style driver presence/location: `GEOADD drivers lon lat driver:9`, nearby search
`GEOSEARCH` — ephemeral by nature (refreshed every few seconds), perfect Redis fit; losing it
on crash costs seconds of staleness, nothing more. Gaming leaderboards at scale are ZSETs
verbatim. Session stores everywhere. Interviewers expect you to *reject* Redis for the ledger
and *choose* it for these.

### 6. Common Interview Questions
- "Design a rate limiter." (fixed window INCR+EXPIRE → sliding-window ZSET → token bucket
  in Lua; discuss race-freedom and cost per request)
- "Design a leaderboard for 100M players." (ZSET + sharding by league/bucket; top-K global via
  merged bucket tops)
- "Can Redis be the primary database?" (loss-tolerance argument; AOF/replication limits)
- "How do distributed locks on Redis fail?" (expiry vs GC pauses, failover duplication —
  Redlock controversy; use fencing tokens / prefer DB advisory locks for correctness-critical)
- "Why is Redis single-threaded and why is that OK?" (RAM-bound ops; event loop; I/O threads
  in 6+ for network)

### 7. Common Mistakes
- Precious data in Redis-as-only-copy.
- O(N) commands on huge structures in the hot path (SMEMBERS a 10M set, KEYS, LRANGE 0 -1).
- Rate limiter with separate GET/INCR (racy) instead of atomic INCR or Lua.
- Redis pub/sub where delivery guarantees matter (fire-and-forget; use Streams/Kafka).
- One giant instance for cache + queues + locks (eviction policy conflicts — Module 7.5).

### 8. Best Practices
- Ephemeral-by-design data only, or accept AOF-everysec loss window explicitly.
- Lua (or MULTI/WATCH) for compound invariants; keep scripts O(1)-ish.
- Cap structure sizes (LTRIM, ZREMRANGEBYRANK); TTL everything; monitor big keys
  (`redis-cli --bigkeys`).
- Shard by hash tag when multi-key atomicity is needed in Cluster.

### 9. Coding Questions
1. Implement token-bucket rate limiting as an atomic Lua script (refill by elapsed time,
   consume, return allowed/deny + retry-after).
2. Build "trending hashtags last hour": per-minute ZSET buckets + ZUNIONSTORE with decay
   weights; state the memory bound and the top-K query.

### 10. SQL Examples
```text
# Idempotency guard
SET idem:req-abc "1" NX EX 86400        → nil = duplicate request

# Leaderboard ops
ZADD lb:global 9812 user:42
ZREVRANGE lb:global 0 9 WITHSCORES
ZINCRBY lb:global 50 user:42

# Distributed lock (with the caveats!)
SET lock:invoice:77 <token> NX PX 10000
# release: Lua compare-token-then-DEL (never blind DEL)

# Streams consumer group (durable-ish queue)
XADD events * type checkout user 42
XREADGROUP GROUP g1 c1 COUNT 10 BLOCK 5000 STREAMS events >
XACK events g1 <id>
```

### 11. Optimization Techniques
- Pipelining/MGET to kill round trips (cache-side N+1).
- Hashes for small objects (ziplist/listpack encoding = memory-dense).
- Split monster keys; bucket time-series structures per window so old buckets expire whole.

### 12. Follow-up Questions
- "Your Lua script takes 80ms — what happens cluster-wide?" (everything on that shard queues;
  rewrite or move to app-side with CAS)
- "Redis Streams vs Kafka — when is each right?" (scale, retention, ecosystem, exactly-once
  tooling vs operational simplicity)
- "How do you migrate a hot Redis to Cluster with no downtime?" (dual-write or proxy with slot
  migration; hash-tag audit first)

---

## Chapter 8.6 — Cassandra

### 1. Why Interviewers Ask This
The reference masterless AP system: consistent hashing + quorums + LSM in one package. Even if
you never run it, its concepts are the vocabulary of half of system design.

### 2. Core Concept
- **Masterless ring**: every node equal; data placed by consistent hashing of the partition key
  (vnodes); **RF** copies on distinct nodes. Any node coordinates any request.
- **Tunable consistency per query**: ONE / QUORUM / LOCAL_QUORUM / ALL for both reads and
  writes; `R + W > RF` ⇒ strong reads (Module 1.4). Multi-DC: LOCAL_QUORUM keeps latency
  in-region.
- **Write path**: LSM (commit log → memtable → SSTables) — writes are cheap and always
  accepted (even for updates: last-write-wins by timestamp, no read-before-write).
- **Repair machinery** (AP hygiene): hinted handoff (replay to recovered nodes), read repair
  (fix divergence seen during reads), anti-entropy repair (Merkle trees, scheduled).
- Query model: partition key equality (+ clustering ranges) ONLY. Secondary indexes exist but
  are scatter-gather traps; materialized views have a troubled history — duplicate tables
  by hand.
- **Counters** are special-cased; **lightweight transactions** (Paxos-based IF NOT EXISTS)
  exist but cost 4x round trips — avoid in hot paths.

### 3. Internal Working
Coordinator hashes the key → sends to RF replicas → acks per consistency level → returns.
Conflicts resolved cell-wise by timestamp (LWW — clock skew can silently drop writes; the
famous caveat). Reads at QUORUM compare digests across replicas, resolve newest, optionally
repair. Tombstones (8.3) + LWW make delete-heavy and read-modify-write workloads hostile.
Gossip protocol spreads membership/health; no config server, no election — availability
through symmetry.

### 4. Visualization (ASCII)
```
        ring (RF=3)
      N1 ─── N2                write user:42 (CL=QUORUM):
     /          \              coordinator ──▶ N2 ✔, N3 ✔ (2/3 acks) ──▶ OK
    N6           N3                        └─▶ N4 down → hint stored on coordinator
     \          /              read (CL=QUORUM): ask N2,N3 → newest timestamp wins
      N5 ─── N4                     divergence found → read repair N3

R+W>RF:  W=QUORUM(2) + R=QUORUM(2) > RF(3) → overlap guaranteed → strong read ✔
W=ONE + R=ONE → fastest, may read stale ✖ (eventual)
```

### 5. Real Production Example
Netflix: ~everything user-state at planetary scale (viewing history, bookmarks) — multi-region
active-active with LOCAL_QUORUM; Apple runs some of the largest Cassandra fleets (iCloud
metadata); Discord's message store (then ScyllaDB — same model, C++ engine). Common shape:
write-heavy, key-addressed, region-resilient, staleness-tolerant.

### 6. Common Interview Questions
- "How does a Cassandra write work end-to-end?" (coordinator → replicas → CL acks → hints)
- "Explain R+W>RF with numbers."
- "Why are writes so fast?" (LSM + no read-before-write + no master coordination)
- "What's LWW and its failure mode?" (clock skew drops concurrent writes silently)
- "Why is 'queue on Cassandra' an anti-pattern?" (tombstone scans)
- "Design the partition key for [time-series/chat/orders]." (bounded partitions — bucket!)

### 7. Common Mistakes
- Unbounded partitions (all events for one device forever) — bucket by time.
- Treating secondary indexes like RDBMS indexes (they're per-node; queries scatter).
- CL=ALL "for safety" (one dead node = unavailability; that's just worse CP).
- Read-modify-write patterns (racy under LWW; needs LWT and its cost).
- Ignoring repair operations until entropy bites (deleted data resurrecting via unrepaired
  replicas past gc_grace).

### 8. Best Practices
- Model one-table-per-query with bounded partitions (<100MB); duplicate writes to N tables in
  a logged batch when they share the partition key (else app-side).
- LOCAL_QUORUM writes+reads as the sane default; drop to ONE only for telemetry-grade data.
- Schedule repairs within gc_grace_seconds; monitor tombstones-per-read and SSTables-per-read.
- NTP discipline (LWW!) — or client-side timestamps from one source.

### 9. Coding Questions
1. Chat messages: design `messages_by_channel ((channel_id, bucket), message_id DESC)` with
   time-bucketing; write the CQL and the "load older messages" pagination query.
2. Given RF=3 across 2 DCs (3+3), compare CL choices (QUORUM=4 cross-DC vs LOCAL_QUORUM=2)
   for latency, consistency, and DC-failure behavior.

### 10. SQL Examples
```text
CREATE KEYSPACE app WITH replication =
  {'class':'NetworkTopologyStrategy','dc1':3,'dc2':3};

CREATE TABLE messages_by_channel (
  channel_id bigint, bucket int,            -- bucket = day number: bounds the partition
  message_id timeuuid, author_id bigint, body text,
  PRIMARY KEY ((channel_id, bucket), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);

-- newest page
SELECT * FROM messages_by_channel
WHERE channel_id=42 AND bucket=20260702 LIMIT 50;

-- consistency is per-query
CONSISTENCY LOCAL_QUORUM;
INSERT INTO messages_by_channel (...) VALUES (...);

-- LWT (sparingly)
INSERT INTO usernames (name, user_id) VALUES ('neo', 42) IF NOT EXISTS;
```

### 11. Optimization Techniques
- Time-window compaction (TWCS) for time-series — expired buckets drop whole SSTables.
- Keep clustering rows narrow; move blobs elsewhere (object storage + reference).
- Token-aware client drivers (skip the coordinator hop).

### 12. Follow-up Questions
- "Cassandra vs DynamoDB — you're choosing for a new team." (ops burden vs managed;
  cost model; multi-cloud; feature deltas — next chapter)
- "How does ScyllaDB claim 10x?" (same model, shard-per-core C++ engine, no JVM/GC)
- "Explain a scenario where a committed write disappears." (LWW clock skew, or CL=ONE write to
  a node that dies before handoff/repair)

---

## Chapter 8.7 — DynamoDB

### 1. Why Interviewers Ask This
Amazon interviews assume it; everyone else uses it as "the managed NoSQL baseline." Tests:
key design under rigid constraints, capacity/hot-partition thinking, and the single-table
mindset.

### 2. Core Concept
- Fully managed KV/document store: tables → items (≤400KB) → attributes.
  **PK = partition key (+ optional sort key)**. Data distributed by hash(partition key);
  items sharing a partition key are sorted by sort key (an "item collection").
- Query patterns: `GetItem` (point), `Query` (one partition key + sort-key conditions —
  cheap), `Scan` (full table — forbidden in hot paths).
- **GSI** (global secondary index): alternate PK/SK — an automatically-maintained, **eventually
  consistent** copy (own capacity, async from base table). LSI: same partition key, alternate
  sort key, created at table birth.
- Consistency: eventually consistent reads by default; **strongly consistent reads** on the
  base table only (not GSIs); **transactions** (`TransactWriteItems`, ≤100 items, 2x cost).
- Capacity: on-demand or provisioned RCU/WCU; **adaptive capacity** helps but a single hot key
  still caps at ~1000 WCU / 3000 RCU per partition — hot-key design still matters.
- **DynamoDB Streams**: CDC feed → Lambda (projections, invalidation, fan-out).

### 3. Internal Working
Descended from the Dynamo paper but *not* the same: DynamoDB is multi-tenant, replicated across
3 AZs with a leader-ish per-partition consensus (strong reads = read from leader), auto-split
partitions by size/throughput. Single-table design exists because (a) Query only works within a
partition key, (b) you pre-join by co-locating heterogeneous items in one item collection,
(c) fewer tables = shared capacity + streams. Global Tables = multi-region active-active with
LWW conflict resolution.

### 4. Visualization (ASCII)
```
Single-table design ("pre-joined" item collection):
PK            SK                   attributes
USER#42       PROFILE              {name, email}
USER#42       ORDER#2026-07-01#9   {total, status}     ── Query PK=USER#42:
USER#42       ORDER#2026-06-28#8   {total, status}        profile + orders,
ORDER#9       ITEM#1               {sku, qty}             ONE round trip ✔
ORDER#9       ITEM#2               {sku, qty}

GSI: PK=STATUS#pending, SK=created_at   → "all pending orders" (eventually consistent)

hot partition: PK=DATE#2026-07-02 (all today's writes → one key) ✖
fix: write sharding  PK=DATE#2026-07-02#<rand 0-9>  → read = query 10 shards, merge
```

### 5. Real Production Example
Amazon retail runs cart/order-workflow tiers on DynamoDB (the 2019+ "we moved off Oracle"
story); Lyft, Snap, and half of serverless-land use it as default OLTP. The canonical incident:
a time-keyed partition (daily leaderboard, `PK=today`) throttles at peak despite low table-wide
usage — per-partition limits + hot key; fixed by write sharding. Interviewers love this exact
scenario.

### 6. Common Interview Questions
- "Design a DynamoDB table for [entity graph] — list access patterns first." (the ritual)
- "GSI vs LSI? What consistency do GSIs give?" (eventual only; capacity separate; GSI
  throttling back-pressures base-table writes!)
- "How do you handle a hot partition?" (key sharding, caching/DAX, redesign key)
- "Strongly consistent read — when available, when not?" (base table yes, GSI no, 2x RCU)
- "Model many-to-many." (adjacency list: both directions as items; or GSI-swapped keys)

### 7. Common Mistakes
- Designing entities-first, discovering an unsupported access pattern → Scan (game over).
- Low-cardinality or time-monotonic partition keys.
- Treating GSIs as free indexes (cost, lag, throttle coupling).
- Ignoring the 400KB item limit (embed → bucket/reference, same as Mongo).
- Missing idempotency on retried writes (SDK retries + non-idempotent updates).

### 8. Best Practices
- Access-pattern table first; single-table design where patterns are stable; generic key names
  (PK/SK) + entity-type attribute.
- Version attributes + conditional writes for OCC (Module 6.5 mapped here).
- Streams → Lambda for projections instead of dual-writing.
- TTL attribute for expiry; on-demand mode until traffic is predictable.

### 9. Coding Questions
1. Design the full key schema for a URL shortener with per-user link lists, click counts, and
   "top links today" (PK/SK, one GSI, sharded counter for hot links).
2. Write the OCC update: `UpdateItem` with `ConditionExpression: version = :v`,
   `UpdateExpression: SET ... , version = version + 1` and the retry policy on
   `ConditionalCheckFailedException`.

### 10. SQL Examples
```text
// Query an item collection (profile + orders)
Query: KeyConditionExpression: "PK = :u AND begins_with(SK, :o)"
       :u = "USER#42", :o = "ORDER#"   ScanIndexForward: false, Limit: 10

// Conditional (optimistic) write
UpdateItem:
  Key: {PK:"DOC#7", SK:"META"}
  UpdateExpression: "SET body=:b, version = version + :one"
  ConditionExpression: "version = :expected"

// Transaction (bounded, 2x cost)
TransactWriteItems:
  - Put    order   (ConditionExpression: attribute_not_exists(PK))   // idempotency
  - Update inventory (ConditionExpression: qty >= :n)
```

### 11. Optimization Techniques
- DAX (managed read-through cache) for read-hot keys — mind its eventual consistency.
- Sparse GSIs (attribute present only on rare items) = cheap partial indexes.
- BatchGetItem/BatchWriteItem to collapse round trips (N+1 again).
- Compress large attributes; split hot/cold attributes across items sharing a PK.

### 12. Follow-up Questions
- "New access pattern post-launch: 'orders by SKU'. Walk the options." (new GSI + backfill
  implications; vs stream-projected table; vs the honest 'this is the flexibility tax')
- "DynamoDB vs Cassandra vs Postgres for a startup's core OLTP — decide with reasons."
  (managed+serverless vs ops control vs relational flexibility; lock-in; cost curves)
- "How do Global Tables resolve concurrent multi-region writes?" (LWW — design so conflicting
  concurrent writes don't happen or don't matter)

---

## Chapter 8.8 — Replication, Sharding & CAP Across NoSQL (Comparison)

### 1. Why Interviewers Ask This
The synthesis question: "compare these systems" — testing whether the mechanisms (leader vs
masterless, B+Tree vs LSM, sync vs quorum) transfer across brand names.

### 2. Core Concept — The Comparison Table
| | PostgreSQL | MySQL | MongoDB | Redis | Cassandra | DynamoDB |
|---|---|---|---|---|---|---|
| Model | Relational | Relational | Document | KV + structures | Wide-column | KV/Document |
| Storage engine | Heap + B+Tree, MVCC | InnoDB B+Tree (clustered), MVCC/undo | WiredTiger B+Tree | RAM (+AOF/RDB) | LSM | LSM-class (managed) |
| Replication | WAL streaming, leader | binlog, leader (+group repl.) | Replica set, elections | async, leader | masterless, RF quorums | 3-AZ managed, per-partition leader |
| Sharding | manual / Citus | manual / Vitess | built-in (mongos) | Cluster (16384 slots) | native (ring) | native (managed) |
| Consistency default | strong (single node) | strong (single node) | tunable (w/rc) | weak across replicas | tunable per query | eventual; strong opt-in |
| CAP posture (partition) | CP-ish w/ sync repl | CP-ish | CP-leaning (majority) | AP-ish (async) | AP, tunable to CP-per-op | AP-ish; strong reads in-region |
| Transactions | full ACID | full ACID | multi-doc (costly) | MULTI/Lua (single shard) | LWT (Paxos, slow) | TransactItems (≤100) |
| Best at | integrity + ad-hoc | same + read-scale ecosystems | rich documents | latency + structures | write scale, multi-DC | serverless scale, zero ops |

Mechanism clusters to reason with:
- **Leader-based replication** (PG/MySQL/Mongo/Redis): simple mental model; failover = election
  /promotion; lag = staleness; writes bottleneck on the leader.
- **Masterless quorum** (Cassandra/Dynamo-lineage): availability through symmetry; consistency
  is arithmetic (R+W vs RF); conflicts need resolution (LWW/vector clocks).
- **B+Tree engines** read-optimized; **LSM engines** write-optimized (Modules 4/8.3).

### 3. Internal Working
The deep commonality: everything is a **replicated log** — Postgres WAL, MySQL binlog, Mongo
oplog, Cassandra commit log + mutation streams, Dynamo streams. Ordering + durability of that
log determines consistency; who may append (one leader vs any replica) determines availability
and conflict complexity. Say this in a synthesis question and you sound like the interviewer.

### 4. Visualization (ASCII)
```
Leader-based:              Masterless quorum:
   W                           W (any node coordinates)
   ▼                            ▼
[LEADER] ──log──▶ [F1]     [N1][N2][N3]  ack W of RF
    │      ──log──▶ [F2]     consistency = R+W vs RF arithmetic
failover: promote F1       failure: no election needed; repair later
loss risk: unshipped log   loss risk: LWW conflicts / unrepaired divergence

Engine axis:   reads ◀── B+Tree ──────────── LSM ──▶ writes
               PG/MySQL/Mongo          Cassandra/Rocks/Dynamo
```

### 5. Real Production Example
A realistic FAANG-adjacent stack, one line each: Postgres (orders, money — CP, ACID), Redis
(sessions, rate limits — ephemeral), Cassandra/DynamoDB (events, feeds — AP write-scale),
Elasticsearch (search projection), Kafka as the spine, CDC keeping projections honest.
Interviews reward naming *why each* in one clause.

### 6. Common Interview Questions
- "Compare MongoDB and Cassandra replication." (elections+oplog vs masterless quorums)
- "Which of these lose acknowledged writes, and under what settings?" (Redis async failover;
  Mongo w:1; Cassandra CL=ONE + node loss; PG async replica promotion)
- "Map each store onto CAP/PACELC."
- "Same data, both engines: why is the LSM store faster to write and slower to read?"

### 7. Common Mistakes
- Comparing brands by adjectives instead of mechanisms.
- Assuming "NoSQL = eventual consistency" (Mongo majority, Dynamo strong reads, Cassandra
  R+W>RF all disprove it).
- Forgetting the ops axis (masterless repair, compaction, resharding are labor) when comparing
  self-hosted vs managed.

### 8. Best Practices
- Answer comparison questions on three axes: **replication topology, storage engine,
  consistency knobs** — everything else is derived.
- Keep one system of record; make every other store a rebuildable projection.

### 9. Coding Questions
1. For each system, state the setting that makes a committed write survive any single node
   loss: PG (`synchronous_standby_names` quorum), MySQL (semi-sync/group replication), Mongo
   (`w:majority`), Redis (WAIT — and its limits), Cassandra (CL≥QUORUM), DynamoDB (default).
2. Draft the polyglot data flow for an e-commerce checkout (order in PG → outbox → Kafka →
   projections in Redis/Elastic/warehouse) with the consistency contract at each hop.

### 10. SQL Examples
```text
-- One durability knob per system (know these cold):
PG:        synchronous_standby_names = 'ANY 1 (r1,r2)'
MySQL:     rpl_semi_sync_source_enabled = ON
MongoDB:   { writeConcern: { w: "majority" } }
Redis:     WAIT 1 100        -- best-effort; not a real sync guarantee
Cassandra: CONSISTENCY QUORUM
DynamoDB:  (managed: 3-AZ by default; strong read = ConsistentRead: true)
```

### 11. Optimization Techniques
- Choose the engine axis by workload write/read ratio before choosing the brand.
- Use managed offerings' guarantees (Dynamo 3-AZ, Aurora storage) to delete whole problem
  classes from your design — and say you're doing it.

### 12. Follow-up Questions
- "Where do NewSQL systems (Spanner, CockroachDB, TiDB) land in this table?" (relational +
  Raft-per-range + distributed txns — CP with latency cost; the 'have both, pay latency' cell)
- "If you could only keep two stores company-wide, which and why?" (forcing-function question:
  usually Postgres + one of {Redis, DynamoDB/Cassandra} + defend the losses)

---

# Module 8 — Practice Problems

## Easy (5)
1. Classify by data model and CAP posture: Redis, MongoDB, Cassandra, DynamoDB, PostgreSQL.
2. Cassandra RF=3: for (W=ONE,R=ONE), (W=QUORUM,R=QUORUM), (W=ALL,R=ONE) state consistency and
   what happens when one replica is down.
3. Embed or reference in MongoDB (one line each): order items; post comments; user →
   profile-settings; product → category.
4. Why are LSM writes fast? Answer in exactly two sentences using "sequential" and "compaction".
5. Pick the store (one line why): session tokens; hotel bookings; IoT telemetry (1M/s);
   product catalog with faceted search; global leaderboard.

## Medium (5)
6. Design the Cassandra schema for a Twitter-like home timeline with fan-out-on-write:
   tables, keys, bucketing, and the celebrity exception.
7. A DynamoDB table throttles at 8% of provisioned capacity. Diagnose (hot partition), show how
   to confirm (CloudWatch per-key / contributor insights), and fix with write-sharded keys
   including the read-side merge.
8. Your Mongo replica set lost acknowledged writes during a failover. Reconstruct the exact
   sequence (w:1 ack → primary crash → election → rollback of un-majority-replicated ops) and
   the two settings that prevent it.
9. Compare running a queue on: Redis Streams, Cassandra, Postgres (SKIP LOCKED), Kafka —
   for ordering, delivery guarantees, tombstone/bloat behavior, and ops. Rank for a
   10k msg/s payments pipeline.
10. Design DynamoDB single-table keys for a food-delivery app: restaurants, menus, orders by
    customer, orders by restaurant+status, courier active order. List each access pattern → key.

## Hard (5)
11. Netflix-style viewing history: 200M users, 5B events/day, reads = "continue watching" per
    user + per-title analytics. Design storage end-to-end (Cassandra keys+bucketing+TTL+TWCS,
    CDC to warehouse for analytics), including multi-region consistency choices.
12. Prove the LWW data-loss scenario: two Cassandra clients with 200ms clock skew write the
    same cell; show the timeline where the *earlier* real-world write wins, then design two
    mitigations (client-side monotonic timestamps from one tier; model as immutable events
    instead of updates).
13. Migrate a 5TB MongoDB cluster to DynamoDB with <1min write freeze: schema/key mapping
    decisions, backfill (parallel export respecting item limits), change-stream tailing,
    dual-read verification, cutover, and rollback plan.
14. Design a rate limiter service for 5M RPS across 3 regions on Redis: local vs global limits,
    Cluster key design, Lua atomicity, cross-region sync (CRDT-ish counters vs per-region
    budgets), degraded mode when Redis is down. Justify every consistency sacrifice.
15. Your company runs Postgres + Redis + Cassandra + Elasticsearch, and on-call is drowning.
    Consolidation review: for each store list the workloads on it, which could move to Postgres
    at current scale (with the math), which cannot and why — produce the target architecture
    and migration order.

---

*Next: [Module 9 — Database Design](module-09-database-design.md)*

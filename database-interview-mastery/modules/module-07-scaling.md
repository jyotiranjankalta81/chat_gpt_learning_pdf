# MODULE 7 — Database Scaling

> The system-design-round module. Every "design X at scale" interview walks this ladder:
> optimize → cache → replicate reads → partition → shard. Know the ladder, the mechanics of
> each rung, and what each rung breaks.

Chapters:
7.1 Replication & Read Replicas
7.2 Partitioning
7.3 Sharding
7.4 Connection Pooling
7.5 Caching with Redis: Patterns, Hot Keys, Invalidation

---

## Chapter 7.1 — Replication & Read Replicas

### 1. Why Interviewers Ask This
First scaling move everyone makes, with two traps built in: **replication lag** (stale reads)
and **failover data loss** (async replication). Senior candidates must articulate sync vs async
trade-offs and read-your-writes strategies.

### 2. Core Concept
- **Physical/streaming replication** (Postgres default): ship the WAL byte-stream; replicas
  replay it → byte-identical, read-only standbys. Whole-cluster granularity.
- **Logical replication**: decode WAL into row changes, publish/subscribe per table → cross-
  version migrations, selective tables, fan-in — but no DDL replication, more care required.
- **Async** (default): primary commits without waiting → zero write latency cost; replica lag =
  potential data loss window on failover (RPO > 0).
- **Sync**: commit waits for replica(s) ack (`synchronous_standby_names`, quorum `ANY 1 (...)`) →
  RPO=0 at latency cost; a dead sync standby can stall writes (why you use quorum).
- **Read replicas** scale reads only — writes still hit one primary. Lag is normal (ms–s;
  unbounded during load/vacuum storms). **Failover**: promote a replica; clients re-point;
  split-brain protection (fencing, one-writer guarantee) is the hard part — usually delegated
  to RDS/Patroni/etc.
- MySQL parallel: binlog replication (row-based), semi-sync ≈ quorum-light, GTIDs for failover
  tracking.

### 3. Internal Working
Primary walsender → replica walreceiver → WAL written → startup process replays into pages.
Replica queries run against MVCC snapshots as usual; **replication conflicts** occur when
replay needs to remove row versions a replica query still uses (vacuum cleanup records) →
replica either delays replay (`max_standby_streaming_delay`) or cancels queries; `hot_standby_feedback`
exports the replica's xmin to the primary (no cancels, but primary bloat). Lag metrics: LSN
delta (`pg_current_wal_lsn()` vs replay LSN) and time (`pg_last_xact_replay_timestamp`).

### 4. Visualization (ASCII)
```
                     WAL stream (async)
   writes ──▶ PRIMARY ═══════════▶ REPLICA-1 (reads)
                 ║     ═══════════▶ REPLICA-2 (reads)
COMMIT returns ──┘                      ▲
                                        │ lag = LSN(primary) − LSN(replayed)
user writes on primary ──▶ immediately reads replica ──▶ row "missing" (stale read!)

sync quorum (ANY 1 of r1,r2):  COMMIT waits ─▶ first ack ─▶ return   RPO=0
failover: promote replica ── if async & lagging: committed txns LOST (RPO>0)
```

### 5. Real Production Example
The classic: user updates their profile, next request lands on a lagged replica, sees the old
name, files a bug — "the save button doesn't work." Standard fixes deployed at Meta/Uber-style
stacks: **session pinning** (after a write, that session reads the primary for N seconds) or
**LSN tokens** (client carries the write's LSN; replica serves only if replayed past it).
Second classic: failover during an incident loses 4 seconds of async-replicated payments →
post-mortem moves the payments cluster to quorum-sync.

### 6. Common Interview Questions
- "Sync vs async replication — trade-offs and when each?" (latency/availability vs RPO)
- "How do you handle read-your-own-writes with replicas?" (pinning / LSN wait / stick writes-
  readers to primary)
- "What causes replication lag and how do you monitor it?" (write bursts, vacuum, big txns,
  replica I/O, long replica queries; LSN + time lag)
- "What happens to un-replicated commits on failover?"
- "Physical vs logical replication — when logical?" (upgrades, selective, cross-region fan-in,
  CDC)

### 7. Common Mistakes
- Routing all reads to replicas blindly (auth checks, post-write reads break).
- Treating replicas as backups (they replicate your DELETE too; PITR/base backups are backups).
- Single sync standby without quorum → standby death blocks all writes.
- Ignoring that replicas must replay serially-ish: a write-hot primary can outrun replica replay
  forever.
- Scaling *writes* with read replicas (they don't).

### 8. Best Practices
- Classify queries: primary-required (post-write, transactional reads) vs lag-tolerant
  (browse, analytics) — encode in the data-access layer.
- Alert on lag (bytes and seconds); cap acceptable staleness per endpoint.
- Quorum sync for money; async for the rest; measure the actual commit-latency cost.
- Use managed failover (RDS/Aurora/Patroni) and *test* failovers regularly.

### 9. Coding Questions
1. Write the lag queries: on primary (`pg_stat_replication`: sent vs replay LSN per replica,
   `write_lag/flush_lag/replay_lag`), on replica (replay timestamp delta).
2. Design the LSN-token read-your-writes flow: capture `pg_current_wal_lsn()` after commit,
   send as cookie, replica middleware compares `pg_last_wal_replay_lsn()`, waits ≤50ms, else
   forwards to primary.

### 10. SQL Examples
```sql
-- Primary: per-replica lag
SELECT application_name, state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes,
       replay_lag
FROM pg_stat_replication;

-- Replica: staleness
SELECT now() - pg_last_xact_replay_timestamp() AS lag;

-- Quorum-sync durability for the cluster (postgresql.conf)
-- synchronous_standby_names = 'ANY 1 (replica1, replica2)'
-- Per-transaction opt-out for cheap writes:
SET LOCAL synchronous_commit = local;
```

### 11. Optimization Techniques
- Dedicated replicas per workload (OLTP reads vs analytics vs backups) — isolate cache and
  conflict profiles.
- `hot_standby_feedback` on the analytics replica only (accept primary bloat there), short
  `max_standby_streaming_delay` on OLTP replicas.
- Batch/segment huge writes so replay keeps pace; avoid single 100M-row transactions.

### 12. Follow-up Questions
- "Design multi-region: writes in one region, reads everywhere — what's user-visible?"
  (cross-region lag, read-your-writes across regions, failover RPO; leads to per-region
  write partitioning)
- "Aurora claims ~10ms replica lag and fast failover — what's architecturally different?"
  (shared distributed storage; replicas read the same storage rather than replaying full WAL locally)
- "When do you reach for logical replication into Kafka?" (CDC — cache invalidation, search
  indexing, warehouse feeds; Modules 5/8 tie-in)

---

## Chapter 7.2 — Partitioning

### 1. Why Interviewers Ask This
"The table hit a billion rows" is the prompt. Partitioning is the *single-node* answer (before
sharding), and interviewers test whether you know what it does and does NOT solve, plus the
partition-key discipline.

### 2. Core Concept
Split one logical table into physical child tables by a **partition key**:
- **Range** (time, ids): time-series default; enables partition *lifecycle* (drop old months
  instantly).
- **List** (region, tenant-group): data-residency, per-class management.
- **Hash** (uniform spread): no natural range; spreads hot writes; no pruning for ranges.

What it buys: **pruning** (queries touching one partition scan 1/N of the data), **instant
bulk deletes** (`DROP/DETACH PARTITION` vs DELETE of 500M rows), smaller per-partition indexes
(fit in cache), parallelism per partition, targeted VACUUM.
What it doesn't: more write throughput on one box (same disk/CPU), cross-partition queries
(hit all partitions), and it *complicates* uniqueness: **every unique constraint / PK must
include the partition key** (no global unique indexes in Postgres).

### 3. Internal Working
Declarative partitioning (PG10+): parent is a routing shell; tuple routing at insert; planner
prunes at plan time (literal predicates) and **execution time** (parameters, join-driven —
`Subplans Removed` in EXPLAIN). Each partition = full table (own indexes, stats, vacuum).
Partition count sweet spot: dozens–low hundreds per query path (thousands inflate planning
time/locks). `DETACH PARTITION CONCURRENTLY` for non-blocking removal;
attach with a pre-added CHECK constraint to skip the validation scan.

### 4. Visualization (ASCII)
```
            events (parent — no data)
   ┌───────────┬───────────┬───────────┬───────────┐
 ev_2026_04  ev_2026_05  ev_2026_06  ev_2026_07   (range on created_at)
WHERE created_at >= '2026-06-10' AND < '2026-06-20'
        → planner prunes to ev_2026_06 only  (1/N of I/O, small hot index)
retention: DROP TABLE ev_2025_07;   -- 500M rows gone in milliseconds, no vacuum debt

anti-pattern: WHERE user_id = 42 (no partition-key predicate)
        → scans ALL partitions (N index probes) — worse than unpartitioned!
```

### 5. Real Production Example
Uber-style `trips`/`events` tables: monthly range partitions; every query carries a time
predicate by convention (enforced in the query layer); retention = cron dropping month N−13.
Before partitioning, deleting old data was a week-long DELETE causing bloat+lag; after, it's a
metadata operation. Interview probe: "you partitioned by month but the app queries by user_id —
what happens?" (all-partition scans; you chose the wrong key or need a composite approach).

### 6. Common Interview Questions
- "When do you partition and by what key?" (size/retention/pruning-driven; the key = the
  predicate every hot query carries)
- "Partitioning vs sharding?" (one node, transparent vs many nodes, app-visible)
- "Why must the PK include the partition key in Postgres?" (uniqueness enforced per-partition;
  no global index)
- "How does partitioning make deletes cheap?" (drop = unlink files, no row-by-row, no bloat)
- "What breaks if a query lacks the partition key?"

### 7. Common Mistakes
- Partitioning small tables (<~100GB) for fashion — pure overhead.
- Key mismatch with the workload (time-partitioned, id-queried).
- Thousands of tiny partitions (planning time, catalog bloat, per-partition overhead).
- Expecting global uniqueness on a non-key column (`email` unique across hash partitions —
  can't; needs a separate lookup table or app enforcement).
- Forgetting a default partition → inserts outside ranges fail (or conversely, default
  partition silently swallowing everything and killing pruning).

### 8. Best Practices
- Range-by-time for event-ish data; automate partition creation (pg_partman) and retention.
- Make the partition key mandatory in hot query paths (lint it in the data layer).
- Index per-partition to match queries; keep per-partition indexes cache-resident.
- Roll up before dropping: aggregate old partitions into summary tables, then drop.

### 9. Coding Questions
1. Write the DDL: `events` partitioned by month with per-partition `(tenant_id, created_at)`
   index, PK `(id, created_at)`, plus next-month creation and 12-month retention statements.
2. Show EXPLAIN evidence of pruning working and broken (with/without the time predicate) and
   fix the broken query.

### 10. SQL Examples
```sql
CREATE TABLE events (
  id bigint GENERATED ALWAYS AS IDENTITY,
  tenant_id bigint NOT NULL,
  created_at timestamptz NOT NULL,
  payload jsonb,
  PRIMARY KEY (id, created_at)                -- must include partition key
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2026_07 PARTITION OF events
  FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
CREATE INDEX ON events_2026_07 (tenant_id, created_at DESC);

-- Retention: instant, no bloat
ALTER TABLE events DETACH PARTITION events_2025_07 CONCURRENTLY;
DROP TABLE events_2025_07;

-- Verify pruning
EXPLAIN SELECT * FROM events
WHERE tenant_id=42 AND created_at >= '2026-07-01' AND created_at < '2026-07-08';
-- plan lists ONLY events_2026_07 ✔
```

### 11. Optimization Techniques
- Sub-partitioning (range → hash) only with strong evidence; complexity grows fast.
- Partition-wise joins/aggregates (`enable_partitionwise_join/aggregate`) for co-partitioned
  big tables.
- Keep recent partitions on fast storage, old on cheap (tablespaces) — hot/cold tiering.

### 12. Follow-up Questions
- "How do you migrate a live 2TB unpartitioned table to partitions with minimal downtime?"
  (create partitioned shadow, backfill in chunks, dual-write or logical replication, cutover)
- "Global secondary index over partitions — options?" (separate lookup table maintained
  transactionally; or accept per-partition + app fan-out)
- "How does this compare to DynamoDB's partitioning?" (transparent hash by partition key —
  the *mandatory-key* discipline is the same lesson — Module 8)

---

## Chapter 7.3 — Sharding

### 1. Why Interviewers Ask This
The end-game scaling question: writes exceed one machine. They test key choice, resharding,
and honest accounting of what you lose (cross-shard everything). Great candidates spend the
first minute arguing whether sharding is needed at all.

### 2. Core Concept
Sharding = horizontal partitioning **across machines**; each shard is an independent DB holding
a subset keyed by the **shard key**.

Strategies:
- **Hash(key) → shard**: uniform spread; loses range queries across keys; the default for
  user-keyed data. Use **consistent hashing / many virtual buckets** (e.g., 4096 slots mapped
  to shards) so resharding moves buckets, not "all keys mod N".
- **Range**: preserves key-locality/scans; hotspot risk (newest range gets all writes) —
  needs split/rebalance machinery (HBase/CockroachDB style).
- **Directory/lookup**: mapping table key→shard; maximal flexibility (per-tenant placement,
  gradual migration) at the cost of running that mapping service (often combined: hash for
  users, directory for whale tenants).

What sharding breaks — say all of these:
- **Cross-shard joins** (app-side joins, denormalize, duplicate reference tables to every shard)
- **Cross-shard transactions** (avoid by design/colocate; else sagas/outbox; 2PC rarely)
- **Global unique IDs** (Snowflake IDs, UUIDv7, per-shard sequences with shard bits)
- **Cross-shard queries/analytics** (scatter-gather with merge, or CDC → warehouse)
- **Rebalancing/resharding** (bucket moves with dual-read/write cutover)
- **Hot keys** (one celebrity tenant > one shard's capacity — sub-shard or special-case them)

Shard key rule: the key that makes your **dominant access pattern single-shard** (usually
user_id/tenant_id), immutable, high-cardinality, uniform-ish.

### 3. Internal Working
Routing layer options: client library computes bucket (Uber/Pinterest style), middleware/proxy
(Vitess for MySQL, Citus for Postgres), or coordinator nodes (Mongo mongos). Scatter-gather
reads: fan out, merge (k-way merge for sorted+limit — cursor carries per-shard positions).
Resharding playbook: double buckets → copy bucket data (snapshot + CDC tail) → dual-write or
pause-writes-per-bucket cutover → verify checksums → flip routing → clean up.

### 4. Visualization (ASCII)
```
                    router: bucket = hash(user_id) % 4096
                    bucket_map: [0..1023]→S1 [1024..2047]→S2 [2048..3071]→S3 [3072..4095]→S4
 user 42 ──▶ bucket 1732 ──▶ S2 (all of user 42's rows live together = single-shard ops ✔)

get user feed (single key)  → 1 shard ✔
"top sellers this week"     → scatter to 4 shards, gather+merge ✖ (or CDC→warehouse)
add shard S5: move buckets [3277..4095] S4→S5 (copy + tail + flip) — keys don't rehash ✔

hot key: tenant WHALE = 30% of writes → dedicated shard via directory override
```

### 5. Real Production Example
The canonical narratives interviewers expect you to know: **Instagram** sharded Postgres by
user with thousands of logical shards (schemas) mapped to few machines — logical>physical from
day one makes rebalancing "move a schema." **Vitess at YouTube/Slack**: proxy-based MySQL
sharding with resharding workflows. **Stripe/Uber**: directory-based placement for whale
accounts. Common thread: shard *late*, shard by the entity you always query by, and keep
bucket count ≫ machine count.

### 6. Common Interview Questions
- "When do you shard, and what do you try first?" (vertical, replicas, cache, partitioning,
  workload split — shard last)
- "Choose the shard key for [marketplace/chat/payments] and defend it."
- "How do you add a shard without downtime?" (bucket migration playbook)
- "How do you handle a query that needs data from all shards?"
- "What about transactions across two users on different shards?" (avoid; saga; or route both
  entities into an owning aggregate)

### 7. Common Mistakes
- Sharding by a mutable or low-cardinality key (country → 5 giant shards, US hotspot).
- `mod N` directly on servers → resharding = rehash everything.
- Ignoring the reference-data problem (joins to `products` from every shard — replicate it).
- Promising global uniqueness/constraints the design can no longer enforce (Module 1.7 tie-in).
- Under-specifying the migration: "we'll just move the data" — the dual-write/tail/verify part
  is the actual work.

### 8. Best Practices
- Many logical buckets, few physical shards; carry `bucket_id` in every row.
- Colocate all tables sharing the shard key ("shard groups") so entity-local transactions stay
  ACID on one shard.
- CDC every shard into one warehouse for analytics; never scatter-gather for BI.
- Idempotency keys everywhere (retries across routing flips).
- Instrument per-shard load; hot-shard alerts drive rebalancing.

### 9. Coding Questions
1. Design the bucket map schema (`buckets(bucket_id PK, shard_id, state)` with states
   active/migrating/moved) and write the router pseudocode handling in-flight migration
   (read-both, write-new or write-both policy).
2. Global-ish unique order numbers on 16 shards: Snowflake layout (41 bits ms timestamp,
   10 bits shard/worker, 12 bits sequence) — write the generator and collision argument.

### 10. SQL Examples
```sql
-- Per-shard DDL is normal Postgres; the sharding lives in routing metadata:
CREATE TABLE buckets (
  bucket_id int PRIMARY KEY,             -- 0..4095
  shard_id  int NOT NULL,
  state     text NOT NULL DEFAULT 'active'  -- active | migrating | moved
);

-- Scatter-gather top-N merge (app coordinates; per shard:)
SELECT * FROM orders WHERE created_at >= $1
ORDER BY created_at DESC, id DESC LIMIT 50;   -- run on each shard, k-way merge, take 50

-- Citus flavor (Postgres extension), for contrast:
SELECT create_distributed_table('orders', 'user_id');  -- co-locates by user_id
```

### 11. Optimization Techniques
- Route read-only single-key queries to shard replicas (sharding × replication compose).
- Cache the bucket map client-side with versioned invalidation (it changes rarely).
- Sub-shard hot tenants by a secondary key (tenant_id + hash(entity_id)) — accept fan-out for
  that tenant only.

### 12. Follow-up Questions
- "Why did Vitess/Citus-style middleware win over app-level sharding at many companies?"
  (centralizes routing/resharding/DDL fan-out; app stays SQL-ish)
- "How do NewSQL systems (Spanner, CockroachDB) change this conversation?" (automatic
  range-sharding + distributed transactions with consensus — you pay latency, drop the
  app-level machinery)
- "Design the un-shard: merging two shards after load dropped." (same bucket playbook, reversed)

---

## Chapter 7.4 — Connection Pooling

### 1. Why Interviewers Ask This
Connection exhaustion is a top-3 real Postgres incident, and serverless made it worse. It tests
whether you know Postgres's process-per-connection cost and the pooler modes.

### 2. Core Concept
- Postgres connection = **forked OS process** (~5–10MB + scheduler load + lock-table entries).
  A few hundred active connections is healthy; thousands degrade *everything* (context switches,
  contention on shared structures) — even idle ones cost.
- **App-side pool** (HikariCP etc.): reuse per instance. Insufficient alone: 200 instances ×
  20 conns = 4000.
- **Server-side pooler** (PgBouncer, RDS Proxy): multiplexes thousands of client connections
  onto tens of server connections. Modes:
  - **session**: 1 client ↔ 1 server conn for the session — safe, weak multiplexing.
  - **transaction** (the production standard): server conn borrowed per transaction —
    breaks session state (SET, prepared statements pre-1.21, advisory locks, LISTEN, temp tables).
  - **statement**: per statement; forbids multi-statement transactions.
- Sizing rule of thumb: active server connections ≈ cores × (2–4) for OLTP; queue the rest in
  the pooler. More is *slower*.

### 3. Internal Working
Why few connections outperform many: each backend competes for CPU, buffer-pool latches,
lock manager, and snapshot computation (ProcArray) — throughput peaks near core count and
*falls* beyond it; latency-vs-throughput curve is a classic interview sketch. PgBouncer is a
single-threaded event loop (run several instances/so_reuseport at scale). Transaction mode +
`DISCARD ALL`-style reset between borrows is how state leakage is prevented.

### 4. Visualization (ASCII)
```
2000 app conns ──▶ Postgres: 2000 backends → thrash (ctx switches, latches) ✖

2000 app conns ──▶ PgBouncer (transaction mode) ──▶ 40 server conns ──▶ PG ✔
                     └─ queue: clients wait μs-ms for a free conn

throughput
   ▲      ╭─────╮
   │     ╱       ╲____        ← peaks ≈ 2-4× cores, then DEGRADES
   │    ╱              ╲___
   └──────────────────────────▶ concurrent server connections
        40   200      2000
```

### 5. Real Production Example
Incident every team has: deploy doubles pods; each pod opens 20 conns; Postgres hits
`max_connections`, new conns refused, health checks fail, cascade. Or the serverless version:
Lambda burst opens 3000 connections. Fix: PgBouncer/RDS Proxy in transaction mode, app pools
sized down, `max_connections` modest, alerting on saturation. Interviewers often ask the
Lambda variant explicitly.

### 6. Common Interview Questions
- "Why are Postgres connections expensive?" (process model + shared-structure contention)
- "PgBouncer transaction vs session mode — what breaks in transaction mode?"
- "How do you size a pool?" (cores-based, Little's law: conns ≈ QPS × avg query time)
- "Serverless + Postgres — what's the problem and fix?"
- "Symptoms of pool exhaustion vs DB slowness — how do you tell apart?" (client wait time vs
  server query time; pooler queue metrics — Module 11)

### 7. Common Mistakes
- Raising `max_connections` to 5000 as the "fix" (institutionalizes the thrash).
- Transaction mode with session-state reliance (SET search_path, advisory locks held across
  transactions, LISTEN) — subtle breakage.
- Pools sized "generously" per service, summing past DB capacity fleet-wide.
- Long transactions/idle-in-transaction hogging pooled server conns (pool multiplexing dies —
  ties to Module 6 timeouts).

### 8. Best Practices
- PgBouncer/RDS Proxy transaction mode as default architecture; session mode only for the
  exceptional session-stateful consumers.
- Budget connections fleet-wide: Σ(app pools) < pooler client limit; pooler server pool ≈
  cores×3.
- `idle_in_transaction_session_timeout`, `statement_timeout` to protect the pool.
- Monitor: pooler queue wait, server conn saturation, PG `pg_stat_activity` state counts.

### 9. Coding Questions
1. Little's-law sizing: 8k QPS, mean query 5ms → ~40 busy conns; add p99 headroom → pool ~60.
   Show the math and what happens at mean 50ms (400 needed → redesign, don't just grow).
2. Write the monitoring query grouping `pg_stat_activity` by state (active / idle /
   idle in transaction) and flagging waits.

### 10. SQL Examples
```sql
-- Connection census
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;

-- Who's hogging: idle-in-transaction sessions
SELECT pid, usename, now()-xact_start AS txn_age, left(query,60)
FROM pg_stat_activity
WHERE state = 'idle in transaction' ORDER BY xact_start;

-- Guardrails
ALTER SYSTEM SET idle_in_transaction_session_timeout = '60s';
ALTER SYSTEM SET statement_timeout = '30s';   -- per-role/app overrides as needed
```

### 11. Optimization Techniques
- Prepared statements via pooler (PgBouncer ≥1.21 supports protocol-level named statements in
  transaction mode) to reclaim parse/plan savings.
- Separate pools per workload (web / worker / cron) so batch jobs can't starve user traffic.
- Keep transactions short (Module 6) — the pool multiplexing ratio *is* your transaction
  duration profile.

### 12. Follow-up Questions
- "Why does MySQL tolerate more connections?" (thread-per-connection, lighter than processes —
  still not free)
- "Pooler is now the SPOF — how do you deploy it?" (pairs behind a TCP LB / per-node sidecar /
  managed proxy; connection draining on deploys)
- "How does Aurora/Neon 'serverless Postgres' attack this differently?" (separated proxy/
  compute layers, connection multiplexing built-in)

---

## Chapter 7.5 — Caching with Redis: Patterns, Hot Keys, Invalidation

### 1. Why Interviewers Ask This
"Add a cache" is everyone's answer; the interview is about what follows: consistency,
invalidation, stampedes, hot keys. ("There are only two hard things…" — they will quote it.)

### 2. Core Concept
Why Redis: in-memory (μs latency), rich structures (strings, hashes, sets, sorted sets, lists,
streams), single-threaded per shard (atomic ops, no locks), Redis Cluster for sharding.

Patterns:
- **Cache-aside** (lazy; the default): read → miss → load DB → SET with TTL; write → update DB →
  **invalidate (DEL)** the key. App owns the logic.
- **Read-through / write-through**: cache layer loads/stores synchronously (consistency ↑,
  write latency ↑).
- **Write-behind**: buffer writes in cache, flush async (fast, risky — loss window).
- TTL always, even with explicit invalidation (TTL = corruption backstop).

Failure modes (the real interview content):
- **Stale reads**: DB updated, cache not yet invalidated; or race: reader loads old value and
  SETs it *after* the invalidation (fix: short TTLs, versioned keys, or CAS/Lua).
- **Stampede / dogpile**: hot key expires → thousands of concurrent DB loads. Fixes:
  per-key mutex (SET NX lock, one loader), probabilistic early refresh, background refresh,
  serve-stale-while-revalidate.
- **Hot keys**: one key (celebrity profile) saturates one Redis shard/node. Fixes: local
  in-process cache layer, key replication (`key#1..N` random read), split the value.
- **Big keys**: 10MB values / million-member sets block the single thread (`SCAN`, not `KEYS`;
  chunk values).
- **Penetration**: misses for nonexistent ids hammer the DB — cache negative results (short
  TTL) or bloom filter.
- **Eviction**: memory full → `maxmemory-policy` (allkeys-lru / volatile-ttl / lfu) — know that
  eviction ≠ invalidation.

Invalidation strategies ranked: TTL-only (simplest, staleness window) → explicit DEL on write
(precise, needs discipline at every write path) → **CDC-driven** (Debezium tails WAL → consumer
DELs keys: catches *every* write path incl. backfills; eventual by ms) → versioned keys
(never invalidate; bump version pointer).

### 3. Internal Working
Redis single-threaded event loop: every command atomic; long commands block everything
(hence big-key danger). Persistence: RDB snapshots / AOF appendfsync — cache use typically
tolerates loss; "Redis as a database" needs AOF everysec + replicas and still isn't Postgres.
Redis Cluster: 16384 hash slots over nodes; multi-key ops require same-slot (hash tags
`{user:42}:...`). Replication is async → failover can lose recent writes (don't keep the only
copy of anything precious).

### 4. Visualization (ASCII)
```
cache-aside read:                     write + invalidate race:
app ─GET k─▶ redis ─hit─▶ return      T1: read DB (v1) …slow…
   └─miss─▶ DB ─▶ SET k TTL ─▶ return T2: write DB (v2); DEL k
                                      T1: SET k = v1  ← STALE value cached! 
stampede on expiry:                    fix: TTL backstop / version in key / compare-and-set
    k expires
1000 reqs ──▶ all miss ──▶ 1000 DB queries ✖
fix: first loader takes SET k:lock NX EX 5 → loads → SET k → DEL lock
     others: brief wait/serve stale

hot key: GET celeb:99 = 500k/s → one shard pinned
fix: app-local LRU (1s TTL) in front  → shard sees 1/1000th
```

### 5. Real Production Example
Twitter/Meta-scale celebrity problem: one profile key takes 500k reads/s — a single Redis node
caps out; the answer stack: in-process cache with ~1s TTL (absorbs 99.9%), replicated keys,
and precomputed fan-out. Stampede classic: a deploy flushes cache; DB gets the entire read
load at once and falls over (thundering herd on cold cache) — mitigations: warm-up, staggered
TTLs with jitter, request coalescing. These two stories cover most cache interview follow-ups.

### 6. Common Interview Questions
- "Walk through cache-aside and its consistency guarantees." (and the SET-after-DEL race)
- "Cache invalidation strategies — compare." (TTL / write-path DEL / CDC / versioned keys)
- "What's a cache stampede and three mitigations?"
- "How do you handle a hot key?" (local cache, replication, splitting)
- "Should you cache before or after optimizing the query?" (after — cache hides, doesn't fix;
  and cold-cache = raw query cost)
- "Delete or update the cache on write?" (DEL is safer: update races produce interleaved stale
  values; recompute on next read)

### 7. Common Mistakes
- No TTL "because we invalidate correctly" (until the one write path that doesn't).
- `KEYS pattern*` in prod (O(N), blocks the loop) — `SCAN`.
- Caching before fixing an unindexed query — cold cache melts the DB.
- One Redis for cache + queues + locks + rate limits → eviction policy conflicts (evicting
  "cache" evicts your locks).
- Treating Redis replication as durable (async; failover loses tail writes).

### 8. Best Practices
- Every key: TTL + jitter; every value: version/schema tag; every miss path: stampede-guarded.
- Separate Redis instances by role (cache vs data structures vs queues) with role-appropriate
  eviction/persistence.
- Cache at the right layer: precomputed view models (per-page payloads) beat caching raw rows.
- Measure hit ratio per key-class; below ~80% question the cache's existence.
- CDC-driven invalidation for multi-writer systems.

### 9. Coding Questions
1. Implement stampede-safe cache-aside pseudocode: GET → miss → `SET lock NX PX 3000` → winner
   loads DB and SETs (TTL+jitter) → losers retry/serve stale. Handle loader crash (lock PX).
2. Design keys/TTLs/invalidation for a product page: product core (1h + CDC DEL), price+stock
   (30s TTL only), reviews first page (5m, DEL on new review), rendered payload version-keyed.

### 10. SQL Examples
```sql
-- The DB side of cache-aside: the query worth caching should still be indexed
SELECT p.*, i.quantity FROM products p
JOIN inventory i USING (product_id) WHERE p.id = $1;

-- CDC invalidation source (logical replication publication)
CREATE PUBLICATION cache_inval FOR TABLE products, inventory, reviews;
-- Debezium/consumer: on change → DEL product:{id}, DEL product_page:{id}
```

```text
# Redis command shapes to know cold:
SET product:42 "{...}" EX 3600
GET product:42 / DEL product:42
SET lock:product:42 token NX PX 3000          # stampede/mutex
INCRBY views:42 1 ; EXPIRE views:42 86400     # counters
ZADD leaderboard 9812 user:42                  # sorted set = ranking
MGET product:1 product:2 product:3             # batch (avoid N+1 to the cache!)
SCAN 0 MATCH product:* COUNT 1000              # never KEYS
```

### 11. Optimization Techniques
- Two-tier caching: in-process LRU (ms TTL, absorbs hot keys) → Redis → DB.
- Pipeline/MGET batches; hash tags to co-locate related keys in Cluster.
- Negative caching with short TTL for penetration; bloom filter for hard cases.
- TTL jitter (`ttl ± rand(10%)`) to de-synchronize mass expiry.

### 12. Follow-up Questions
- "Redis dies — what happens to your system, and what's your cold-start plan?" (degradation
  math: DB at full read load? load-shed? warm-up script?)
- "When is Redis the primary store legitimately?" (ephemeral-by-nature data: sessions, rate
  limits, presence — where loss is acceptable; Module 8)
- "How would you build rate limiting on Redis?" (INCR+EXPIRE fixed window / sorted-set sliding
  window / token bucket in Lua — classic mini-design)

---

# Module 7 — Practice Problems

## Easy (5)
1. Reads are 90% of load and the primary is CPU-bound. Ladder the next three moves in order and
   the risk each introduces.
2. Write the two lag queries (primary side and replica side) and define an alert threshold for a
   feed product vs a payments product.
3. Your `events` table is 2TB, queries always include `created_at` ranges, retention is 12
   months. Design the partitioning (key, granularity, retention op).
4. 500 Lambda instances each open a DB connection on cold start. Explain the failure and the
   fix architecture.
5. A product page's cache key expires and 2,000 requests hit the DB simultaneously. Name the
   phenomenon and implement one mitigation in pseudocode.

## Medium (5)
6. Design read-your-own-writes for: web app, primary + 4 async replicas behind a router.
   Provide the LSN-token mechanism end-to-end and the fallback policy.
7. You must delete 800M rows older than 18 months from an unpartitioned table without downtime.
   Give the chunked-delete plan (with vacuum pacing) AND the partition-migration plan; argue
   which to choose at what table size.
8. Choose shard keys and justify: (a) B2B SaaS (tenants of wildly different sizes), (b) consumer
   chat app, (c) payments ledger, (d) IoT telemetry. For each, name the query that becomes
   expensive and the mitigation.
9. PgBouncer transaction mode broke: advisory-lock-based cron dedup and `SET search_path`
   multi-tenancy. Explain both breakages and redesign each feature pool-compatibly.
10. Design the caching layer for a news homepage (1M RPS peak, editors publish continuously):
    layers, TTLs, invalidation path from CMS publish to edge, stampede control, cold-start plan.

## Hard (5)
11. Full resharding design: 4 shards → 8, zero downtime, 4096 buckets. Specify: bucket map
    states and transitions, copy + CDC-tail mechanics, write policy during migration
    (dual-write vs brief per-bucket pause — argue one), verification (checksums/row counts),
    rollback points, and cutover.
12. Multi-region active-passive Postgres: writes in us-east, read replicas in eu-west (80ms).
    Design: replication topology, EU read staleness handling, failover runbook with RPO/RTO
    numbers for async vs quorum-sync, and how EU users' read-your-writes survives failover.
13. The celebrity problem end-to-end: one user with 80M followers posts; design the fan-out
    (push vs pull threshold), the hot-key strategy for their profile/post counters, and the
    cache consistency for edit/delete of a viral post.
14. A replica serves analytics and keeps cancelling long queries (vacuum conflicts). Compare
    the four fixes (`max_standby_streaming_delay`, `hot_standby_feedback`, dedicated delayed
    replica, CDC→warehouse) with their exact costs, pick per company stage.
15. Your cache hit ratio is 97%, but DB load doubles every deploy and quarterly cache flushes
    cause brownouts. Design deploy-safe caching: versioned keys with gradual rollover, dual-read
    during version transition, warm-up pipeline driven by top-K key logs, and load-shedding
    when hit ratio drops below a floor.

---

*Next: [Module 8 — NoSQL](module-08-nosql.md)*

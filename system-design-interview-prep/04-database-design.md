# Module 4 — Database Design

The database is where most interview deep dives end up, because it's where the hard
trade-offs live: consistency vs latency, reads vs writes, normalization vs
performance. Master this module and you can defend any storage box you draw.

---

## 4.1 SQL vs NoSQL

### Why Interviewers Ask This

"Which database and why" is asked in *every* interview. The senior answer is driven
by access patterns, consistency needs, and scale numbers — not fashion.

### Core Concept

- **Relational (PostgreSQL, MySQL, Aurora)**: tables + schema-on-write, ACID transactions, joins, secondary indexes, mature query planners. Model the data once, query it many ways.
- **Document (MongoDB, DynamoDB in doc-ish usage)**: JSON-like aggregates, schema-flexible, data that's read together is stored together. Query patterns should be known upfront.
- **Wide-column (Cassandra, HBase, Bigtable)**: partition key → sorted rows; built to shard from day one; LSM write-optimized; queries only along designed key paths.
- **Key-value (Redis, DynamoDB)**: get/put by key at predictable single-digit-ms latency at any scale.
- **Graph (Neo4j, Neptune)**: relationship traversals (fraud rings, social graphs) that would be N-way self-joins in SQL.
- **Search (Elasticsearch/OpenSearch)**: inverted indexes for text/faceted queries — a *secondary* system fed from the primary.
- **NewSQL (Spanner, CockroachDB, TiDB)**: SQL + ACID *and* horizontal scale via consensus replication; pay with write latency and cost.

The real decision axes:

```
1. Access patterns known & simple?  → NoSQL fits; ad-hoc/relational queries → SQL
2. Transactions across entities?    → SQL/NewSQL (or redesign to single-partition)
3. Scale: > single-node writes?     → built-to-shard NoSQL or sharded SQL or NewSQL
4. Schema evolution speed           → document stores tolerate variance
5. Team/ops maturity                → Postgres is the best default until proven otherwise
```

### Internal Working (the storage-engine level interviewers love)

- **B-tree engines** (Postgres, MySQL/InnoDB): read-optimized, in-place pages, great point/range reads, writes cause random I/O + WAL.
- **LSM-tree engines** (Cassandra, RocksDB, LevelDB): writes append to a memtable + WAL, flushed to sorted SSTables, background **compaction** merges them. Sequential-write-optimized (huge ingest throughput); reads may touch several SSTables (mitigated by Bloom filters); compaction consumes I/O/CPU and causes latency variance.

This B-tree vs LSM distinction *is* the "why is Cassandra write-fast" answer.

### Real Production Example

Stripe: sharded MongoDB + strong internal tooling, with strict ledger-style
invariants at the application layer. Uber: moved core trip storage from Postgres to
a sharded MySQL-based system ("Schemaless", now on top of MySQL) for predictable
scaling. Netflix: Cassandra for viewing history (write-heavy, always-on,
multi-region). Amazon: DynamoDB serves Prime Day at tens of millions of requests/sec.
Meanwhile, most companies you interview at run their core on Postgres/MySQL — say
that out loud; it's credible.

### Advantages / Trade-offs / Common Mistakes

- SQL: flexibility, integrity (constraints, FKs), transactions; but single-writer ceilings and sharding is manual + painful.
- NoSQL: elastic scale, availability, predictable latency; but weak/eventual consistency by default, no joins (you denormalize and maintain copies), query patterns frozen into the schema.
- Mistakes: choosing NoSQL "for scale" at 100 QPS; claiming "NoSQL has no schema" (it has an implicit schema in the app — schema-on-read); forgetting Elasticsearch/analytics stores are *derived* systems needing a sync pipeline (CDC), not primaries.

### Interview Questions

1. Pick a database for: a banking ledger, a shopping cart, viewing-history ingestion, a fraud graph, full-text product search — justify each.
2. Why are LSM stores write-fast and what do reads cost?
3. When do you move off a single Postgres, and to what — replicas, shards, or NewSQL?

### Best Practices

- Default Postgres; add specialized stores per access pattern with CDC pipelines feeding them; never let a derived store become an unsynced second source of truth.

---

## 4.2 Replication: Leader-Follower, Multi-Leader, Leaderless (+ Read Replicas)

### Why Interviewers Ask This

Replication is how you get read scale, availability, and durability — and every mode
has a signature failure (lag, conflicts, stale quorums) they will probe.

### Core Concept & Internal Working

**Leader-follower (primary-replica)** — the default. All writes go to one leader; it
ships its WAL/binlog to followers, which replay it.

- **Sync replication**: leader waits for follower ACK → no loss on failover, higher write latency; usually "semi-sync": wait for *one* follower.
- **Async replication**: leader ACKs immediately → fast, but on leader crash the most recent writes may not have reached any follower → **lost on failover**.
- **Read replicas** scale reads: point read traffic at followers. The cost is **replication lag** (ms to minutes under load) → users may not see their own writes. Fixes: read-your-writes routing (own profile → leader, or sticky-to-leader for N seconds after a write), monotonic reads (session pinned to one replica), or accept staleness per endpoint.
- **Failover**: detect leader death (timeout — careful: slow ≠ dead), promote the most-up-to-date follower, repoint clients. Dangers: split brain (old leader comes back and takes writes — fence it: STONITH/epoch numbers) and lag-loss (async writes vanish).

**Multi-leader** — a leader per region/datacenter, each accepting writes, replicating
to the others asynchronously. Wins: local write latency in every region, region-
outage tolerance. The price: **write conflicts** (same row updated in two regions
concurrently) requiring resolution: last-writer-wins (data loss, but simple),
per-field merge, CRDTs, or application callbacks. Sane usage: partition ownership so
each record has a "home" region (user's data written only in their region) —
multi-leader topology, single-leader semantics per record.

**Leaderless (Dynamo-style: Cassandra, Riak, DynamoDB internals)** — any replica
accepts writes; the client/coordinator writes to N replicas and requires W ACKs;
reads query R replicas. **R + W > N** ⇒ overlap ⇒ latest write visible (e.g.,
N=3, W=2, R=2). Tunable per query (Cassandra `QUORUM`, `ONE`, `LOCAL_QUORUM`).
Anti-entropy: **read repair** (fix stale replicas during reads), **hinted handoff**
(neighbor holds writes for a down node), **Merkle-tree repair** (background sync).
No failover needed — no leader to fail. Conflicts still need LWW timestamps or
vector clocks.

```
 leader-follower:            multi-leader:              leaderless (N=3,W=2,R=2):
    writes                    US ldr ◄──► EU ldr          client
      │                        ▲  conflicts!  ▲             │ write to 3, ACK on 2
      ▼                        │              │             ▼
   [leader]──WAL──►[f1]     us users       eu users     [r1] [r2] [r3]
        └─────────►[f2]                                  read from 2 → overlap
    reads → followers (lag!)                             guarantees fresh
```

### Real Production Example

GitHub, Shopify, most of the industry: MySQL/Postgres semi-sync leader-follower with
orchestrated failover (orchestrator/Patroni). Netflix: Cassandra `LOCAL_QUORUM`
writes per region. CouchDB/mobile sync and some multi-datacenter MySQL setups are
true multi-leader — famous mostly for their conflict bugs; calendar/collaborative
apps use CRDTs instead.

### Common Mistakes

- Reading from replicas without addressing lag → "my comment disappeared" bugs.
- Multi-leader without a conflict story ("we'll just replicate both ways") — that's a data-corruption generator.
- Believing quorum = strong consistency in all cases (sloppy quorums, concurrent writes, and clock-skewed LWW still create anomalies).
- No fencing on failover → split brain, two leaders, divergent data.

### Monitoring / Failure

- Watch replication lag (seconds behind leader), failover time, conflict rate (multi-leader), hinted-handoff queue depth (leaderless).
- Drill failovers regularly; an untested failover is downtime waiting to happen.

### Interview Questions

1. Async vs sync replication — what exactly is lost on failover and how does semi-sync balance it?
2. Design read-your-writes on top of read replicas.
3. Cassandra N=3: pick W/R for a shopping cart vs a payment record. (cart: W=1/R=1 fast+available; payment: QUORUM/QUORUM)
4. How do you prevent split brain during failover? (quorum-based leader election + fencing tokens/epochs)

### Best Practices

- Semi-sync + automated, *fenced*, regularly-drilled failover; per-endpoint staleness policy for replica reads; per-record home-region if you need multi-region writes.

---

## 4.3 Partitioning & Sharding

### Why Interviewers Ask This

Sharding is *the* answer to "your writes/dataset outgrew one machine", and its
follow-ups (hot shards, resharding, cross-shard queries) are the deep dive in half
of all interviews.

### Core Concept

- **Partitioning**: splitting data within one logical database (Postgres declarative partitions by month — prunes queries, eases retention).
- **Sharding**: horizontal partitioning across *machines* — each shard is an independent database holding a subset of rows.

**Choosing the shard (partition) key is the single most important schema decision at
scale.** Requirements: high cardinality, even load distribution, and — critically —
*aligned with your dominant query pattern* so most queries hit ONE shard.

Strategies:

- **Hash sharding** (`hash(user_id) mod N` → better: consistent hashing / hash-range slots): uniform distribution; kills range scans; the default for entity-by-id access.
- **Range sharding** (users A–F, dates Jan–Mar; HBase/Bigtable, Spanner): efficient range queries; risk of hot ranges (monotonic keys like timestamps or auto-increment IDs write to ONE shard — the classic hot-shard anti-pattern; fix: prefix/salt the key, or use non-monotonic IDs).
- **Directory/lookup sharding**: a mapping service (tenant → shard) — maximum flexibility (move big tenants to dedicated shards), plus one more system to keep highly available (cached heavily).
- **Geo sharding**: by region for latency + data residency (Uber: city/geo cells).

The hard parts you must volunteer:

1. **Cross-shard queries** → scatter-gather (fan out to all shards, merge) — latency = slowest shard; avoid via key design or a derived/global index (async-maintained secondary index sharded by the other key).
2. **Cross-shard transactions** → avoid (choose keys so transactional units co-locate); else 2PC (blocking, fragile) or sagas (Module 7).
3. **Resharding**: with fixed `mod N`, changing N remaps nearly everything. Use **many virtual shards mapped to few physical nodes** (e.g., 4,096 vshards on 16 nodes) — scaling = moving whole vshards; or consistent hashing (~1/N movement); or range-split (Bigtable/CockroachDB auto-split hot ranges). Live migration: dual-write or CDC-backfill → verify → cut over reads → cut over writes.
4. **Hot shards**: celebrity/whale tenants — detect, split their range, isolate them on dedicated shards, or add a second-level key (`celebrity_id + bucket`).

```
                 app / query router (knows key→shard map)
                        │ user_id=812 → vshard 3112 → node B
      ┌───────────┬─────┴─────┬───────────┐
   node A       node B      node C      node D
  vshards      vshards     vshards     vshards
  0–1023      1024–2047   2048–3071   3072–4095
  each vshard: leader + replicas (sharding × replication compose)
```

### Real Production Example

- **Vitess** (YouTube → open source): sharded MySQL with vshard-style resharding — powers Slack, Square, GitHub's move.
- **Instagram**: Postgres sharded by user via thousands of logical shards in fewer physical machines; their ID scheme (timestamp + shard id + sequence) bakes the shard into the ID.
- **Discord**: messages sharded by `(channel_id, bucket)` in Cassandra/ScyllaDB — key aligned with "read a channel's recent messages".
- **Slack**: workspace(team)-sharded MySQL/Vitess — a tenant's data co-located, whale workspaces moved to their own shards.

### Common Mistakes

- Sharding too early (operational tax forever) or by the wrong key (every query becomes scatter-gather — the fatal flaw; interviewers will ask "now fetch X by *other* field").
- `mod N` with no vshard/consistent-hash layer → resharding = full rehash outage.
- Monotonic shard keys (timestamps) → one hot shard absorbing all writes.
- Forgetting unique IDs across shards (need Snowflake-style IDs — timestamp + machine + sequence — or UUIDv7).

### Monitoring / Failure

- Per-shard: size, QPS, latency, replication health; skew dashboards (max/median shard load). Failure of one shard = partial outage for its keys — degrade gracefully, don't 500 the whole product.

### Interview Questions

1. Pick the shard key for: a multi-tenant SaaS, a chat app's messages, a payments ledger. Defend against the "query by other dimension" follow-up.
2. Double the cluster with zero downtime — walk the resharding play.
3. A shard is hot because one tenant is huge — options? (split, isolate, sub-partition)

### Best Practices

- Shard late, but design IDs and schemas to be shardable early; virtual shards from day one; shard key = dominant access path; secondary access paths via derived indexes fed by CDC.

---

## 4.4 Indexing Strategy

### Why Interviewers Ask This

"The query is slow" is the most common production incident, and indexing is the
usual answer — with write-amplification trade-offs a senior engineer must quantify.

### Core Concept & Internal Working

An index is a sorted (or hashed) redundant structure mapping column values → rows.

- **B+-tree** (the default everywhere): O(log n) point + range lookups; leaves linked for scans.
- **Composite indexes**: `(a, b, c)` supports filters on `a`, `a,b`, `a,b,c` (leftmost-prefix rule) and ordering by the indexed sequence. Design them from your WHERE + ORDER BY patterns: equality columns first, then range column, then sort columns.
- **Covering index**: include all columns the query needs → index-only scan, no heap fetch — the difference between 50 ms and 0.5 ms on hot endpoints.
- **Selectivity** matters: indexing a boolean rarely helps (unless partial); indexing `email` (unique) is ideal. **Partial indexes** (`WHERE status='active'`) keep hot indexes small. Expression indexes (`lower(email)`). GIN/inverted for JSONB/arrays/full-text; geospatial (R-tree/GiST); hash indexes for pure equality.
- **The cost**: every index adds write amplification (each INSERT/UPDATE touches every index), consumes RAM (indexes compete for buffer pool), and slows down the optimizer's choices. A table with 12 indexes is a write-latency incident in progress.
- Clustered vs secondary: InnoDB stores rows *in* the PK B-tree (secondary indexes point to PK → keep PKs small; UUIDv4 PKs shred insert locality — prefer UUIDv7/Snowflake); Postgres heap + all indexes secondary.

Read the plan: `EXPLAIN ANALYZE` — seq scan on a large table under a selective
filter = missing index; index scan + huge filter = wrong composite order; sort node
= missing ORDER BY coverage.

### Real Production Example

Every mature engineering org runs slow-query monitoring (pt-query-digest,
`pg_stat_statements`) and reviews indexes in schema migrations. GitLab and Shopify
publish index-review checklists: every new query pattern ships with its index, every
index must justify its write cost.

### Common Mistakes

- Indexing every column "just in case" (write amplification, bloated buffer pool).
- Composite order wrong (`(created_at, user_id)` when queries filter by user and range by time → needs `(user_id, created_at)`).
- Functions on indexed columns in predicates (`WHERE lower(email)=...` without an expression index → seq scan).
- Ignoring index maintenance: bloat, unused indexes (drop them — measure with usage stats).

### Interview Questions

1. Design indexes for: `WHERE tenant_id=? AND status='open' ORDER BY created_at DESC LIMIT 20`. (`(tenant_id, status, created_at DESC)`, possibly partial on status)
2. Why did adding an index slow down the system? (write amplification / plan flipped / buffer-pool pressure)
3. What's a covering index and when is it worth it?

### Best Practices

- Index for the query, not the table; leftmost-prefix discipline; partial + covering for hot paths; audit unused indexes quarterly; PKs sequential-ish.

---

## 4.5 Schema Design (Normalization vs Denormalization)

### Why Interviewers Ask This

Schema decisions encode the read/write trade-off. Interviewers check you can start
normalized and denormalize *deliberately*, with a plan to keep copies consistent.

### Core Concept

- **Normalize (3NF)** for the transactional core: one fact in one place, updates are single-row, integrity by construction. Joins are the read cost.
- **Denormalize** when read patterns demand it: precomputed aggregates (`like_count` on posts — don't COUNT(*) 2M likes per render), embedded copies (order line items snapshot product name/price — historically *correct*, not just fast), fan-out tables (precomputed timelines), and derived read models (CQRS, 4.7).
- Every denormalized copy needs a stated **sync mechanism** (same transaction, trigger, CDC pipeline, or periodic rebuild) and a **repair story** (recompute from source of truth).
- NoSQL modeling inverts the process: list the queries first, then design one table/collection per access pattern, duplicating data freely (DynamoDB single-table design: partition key + sort key overloading).
- Other essentials: soft deletes vs hard deletes (audit/GDPR tension), created/updated timestamps everywhere, avoid EAV unless truly dynamic attributes (use JSONB), plan schema migrations to be online (additive changes, backfill, dual-read, contract later — never `ALTER TABLE` a 2TB table blocking writes; use gh-ost/pt-osc for MySQL).

### Real Production Example

Amazon retail order records snapshot price/title at purchase time (denormalized by
correctness requirement). Reddit/Twitter store counters denormalized with periodic
reconciliation jobs. DynamoDB's documented best practice is explicitly
"model for access patterns, denormalize, one table".

### Interview Questions

1. Where would you denormalize a marketplace schema and how do you keep each copy honest?
2. Why must order line items snapshot the product data?
3. How do you run a schema migration on a huge hot table with zero downtime?

### Best Practices

- Normalized core, denormalized edges; every copy has an owner, a sync path, and a rebuild job; counters get reconciliation.

---

## 4.6 Connection Pooling

### Why Interviewers Ask This

Connection-pool exhaustion is a top-3 real production outage, and pool sizing is a
Little's-Law arithmetic check on the candidate.

### Core Concept & Internal Working

DB connections are expensive: TCP + TLS + auth per connect, and each Postgres
connection is a *process* (MBs of RAM, scheduler load). A pool keeps N warm
connections and multiplexes app requests over them.

- App-side pools: HikariCP (JVM), pgx (Go), etc. Key knobs: max size, acquire timeout, max lifetime (recycle to survive failovers/DNS changes), idle timeout.
- **The fleet math problem**: 200 app instances × 20 pool connections = 4,000 connections vs Postgres comfort zone (~a few hundred active). Fix: an intermediary pooler — **PgBouncer** (transaction-mode pooling: a server connection is borrowed per transaction — thousands of client conns share tens of server conns) or RDS Proxy.
- **Sizing**: connections ≈ concurrency needed = QPS × avg query time (Little's Law). 1,000 QPS × 5 ms = 5 in-flight → a pool of ~10–20 suffices. Oversized pools *reduce* throughput (context switching, lock contention on the DB) — the famous HikariCP guidance: pool ≈ cores × 2 for CPU-bound DB work.
- **Exhaustion cascade**: one slow query → connections held longer → pool empties → requests queue at acquire → app threads block → upstream timeouts → retries pile on. Defenses: acquire timeout + fail fast, per-endpoint statement timeouts, circuit breaker around the DB, separate pools for critical vs batch traffic (bulkhead).

```
 200 app pods ×20 conns = 4000 ──► PgBouncer (transaction mode) ──► 50 ──► Postgres
                                    thousands of idle client conns
                                    share tens of real ones
```

### Interview Questions

1. Size the pool: 2k QPS, 10 ms avg query, 4 app instances. (≈20 in flight → ~5–10 per instance + headroom)
2. Walk the exhaustion cascade and every mitigation layer.
3. Why can a *bigger* pool make the database slower?

### Best Practices

- Small pools + fast acquire timeouts + statement timeouts; PgBouncer/proxy at fleet scale; bulkhead pools per workload class; recycle connections (max lifetime) to survive failovers.

---

## 4.7 CQRS (High Level)

### Why Interviewers Ask This

CQRS names the pattern behind most read-scaling tricks (replicas, caches, search
indexes, materialized views are all "read models"). Interviewers want you to know
when it's justified — and that it's not a default.

### Core Concept

**Command Query Responsibility Segregation**: separate the write model (normalized,
transactional, invariant-enforcing) from one or more read models (denormalized,
query-shaped), connected by an async event/CDC pipeline.

```
 commands ──► write model (Postgres, invariants, ACID)
                  │ events / CDC (outbox → Kafka)
      ┌───────────┼──────────────┬────────────────┐
      ▼           ▼              ▼                ▼
  Elasticsearch  Redis views   analytics DB   precomputed timelines
  (search)       (hot reads)   (OLAP)         (feeds)
   ── each read model is rebuildable from the event stream ──
```

Properties to state in interviews: read models are **eventually consistent** (the
pipeline has lag — design the UX for it: optimistic UI, read-your-writes from the
write side); each read model is independently scaled and *rebuildable* (replay
events); often paired with (but does not require) **event sourcing** — storing the
events as the source of truth rather than current state.

Use when: read:write ratios are extreme, read shapes diverge wildly from the write
shape (search + feed + analytics from one dataset), or teams need independent
scaling. Skip when: a CRUD app — the pipeline, lag handling, and rebuild machinery
are a heavy tax.

### Real Production Example

Any product with "DB + Elasticsearch + cache + feed" is running de facto CQRS:
LinkedIn (profile writes → Kafka → search/graph/feed read models — Kafka was born
for this), Uber (trip events → many read stores), e-commerce (order write model +
order-history and search read models).

### Interview Questions

1. The user edits a product but search shows the old title for 3 s — explain, and is it acceptable?
2. Your Elasticsearch cluster is corrupted — recovery plan? (rebuild from events/source table — this is why rebuildability is a requirement)
3. CQRS vs just read replicas — what's the actual difference? (replicas share the *same* model shape; CQRS reshapes data per query need)

### Best Practices

- Outbox pattern (Module 7) to publish events atomically with writes; version events; make every read model rebuildable and monitored for lag.

---

## Module 4 Cheat Sheet

```
CHOOSE DB      Access patterns → transactions → scale → team. Default Postgres.
               B-tree = read-optimized; LSM = write-optimized (memtable→SSTable→
               compaction, Bloom filters for reads).
REPLICATION    Leader-follower: async(fast, loss on failover)/semi-sync. Replicas
               scale reads; LAG ⇒ read-your-writes routing. Failover: fence old
               leader (split brain).
MULTI-LEADER   Write locally in each region; CONFLICTS (LWW/CRDT/merge). Sane mode:
               per-record home region.
LEADERLESS     Dynamo: W+R>N quorum, tunable; read repair, hinted handoff, Merkle
               repair. No failover; conflict resolution still needed.
SHARDING       Shard key = dominant query path, high cardinality, non-monotonic.
               Hash (uniform, no ranges) vs range (scans, hot ranges) vs directory.
               Virtual shards → cheap resharding. Cross-shard query = scatter-gather
               (avoid); cross-shard txn = saga/2PC (avoid harder). Snowflake IDs.
INDEXING       Composite: equality→range→sort (leftmost prefix). Covering = index-only.
               Partial for hot subsets. Every index = write amplification. EXPLAIN.
SCHEMA         Normalize core, denormalize deliberately w/ sync + rebuild story.
               Snapshot immutable facts (order items). Online migrations (gh-ost).
POOLING        pool ≈ QPS × latency (Little). Small pools win. PgBouncer at fleet
               scale. Acquire+statement timeouts. Bulkhead per workload.
CQRS           Write model + async-fed read models (search/cache/feed/OLAP).
               Eventually consistent, rebuildable, outbox-published. Not for CRUD.
```

## Top Interview Questions (Module 4)

1. SQL vs NoSQL for five given workloads. 2. Async vs semi-sync replication and
failover loss. 3. Read-your-writes over replicas. 4. Shard key for chat / SaaS /
payments + resharding at 2×. 5. Hot shard from a whale tenant. 6. Index for a given
query + why indexes hurt writes. 7. Zero-downtime migration of a 2 TB table.
8. Pool sizing math + exhaustion cascade. 9. Cassandra W/R tuning per use case.
10. CQRS vs read replicas; rebuild a corrupted read model.

## Common Mistakes Recap

NoSQL-for-scale at toy scale • replica reads without a lag story • shard key
misaligned with queries • mod-N sharding • monotonic keys → hot shard • index
sprawl • UUIDv4 clustered PKs • giant pools • denormalized copies without sync/
repair • treating Elasticsearch as a primary.

## Mock Interview Exercise

*"Design storage for a marketplace: 10M sellers, 500M listings, 50k reads/s, 2k
writes/s, listing search by text+facets, per-seller dashboards, strong consistency
on inventory counts at checkout."* Expected: Postgres core (sellers/listings/orders,
seller_id-aligned schema) → shard by seller_id with vshards when write volume
demands; inventory decrement single-row transactional; CDC → Elasticsearch (search
read model) + Redis (hot listing cache) + warehouse; read replicas + RYW for seller
dashboards; index plan for the top 5 queries; failover + resharding story.

# MODULE 1 — Database Fundamentals

> The module interviewers use to calibrate your level in the first 10 minutes.
> A senior engineer is expected to answer these with mechanisms and trade-offs, not definitions.

Chapters:
1.1 Why Databases Exist & Database Architecture
1.2 RDBMS vs NoSQL (SQL vs NoSQL)
1.3 ACID vs BASE
1.4 CAP Theorem & Strong vs Eventual Consistency
1.5 OLTP vs OLAP
1.6 Normalization vs Denormalization
1.7 Primary Key vs Unique Key vs Foreign Key
1.8 Transactions (Introduction — deep dive in Module 6)

---

## Chapter 1.1 — Why Databases Exist & Database Architecture

### 1. Why Interviewers Ask This
It sounds trivial, but it separates engineers who treat the DB as a magic box from those who
understand it as a **concurrent, crash-safe, indexed file manager**. If you can explain what a
database gives you *over writing to files*, you can reason about every other topic: WAL explains
replication, buffer pool explains why indexes matter, the planner explains slow queries.

### 2. Core Concept
A database solves five problems that files don't:

| Problem | File approach fails because | Database solution |
|---|---|---|
| Concurrent access | Two writers corrupt each other | Locking + MVCC |
| Crash safety | Partial write = corrupted file | Write-Ahead Log (WAL) + recovery |
| Fast lookup | Full scan of the file | Indexes (B+Tree, hash) |
| Data integrity | Nothing stops bad data | Constraints, types, FKs |
| Declarative access | You hand-code every scan | SQL + cost-based optimizer |

### 3. Internal Working (PostgreSQL architecture)
Life of a query:

1. **Client → connection**: Postgres forks one *backend process* per connection (this is why
   connection pooling matters — see Module 7/11).
2. **Parser** → parse tree. **Analyzer** resolves tables/columns. **Rewriter** expands views.
3. **Planner/Optimizer** enumerates plans (seq scan vs index scan, join orders, join algorithms),
   estimates cost using **statistics** (`pg_statistic`), picks the cheapest.
4. **Executor** pulls tuples through the plan tree (Volcano/iterator model: each node's `next()`
   calls its children).
5. **Storage**: tables are heap files split into **8KB pages**. Reads go through the
   **shared buffer pool** (RAM cache of pages). Dirty pages are flushed lazily by the
   background writer / checkpointer.
6. **Durability**: before a commit returns, the change record is appended to the **WAL** and
   fsynced. The heap page itself can be written later — if the server crashes, WAL replay
   reconstructs it. This is why sequential WAL append makes commits fast even though data
   pages are random-access.

### 4. Visualization (ASCII)
```
 Client
   │ SQL
   ▼
┌─────────────────────────────────────────────────────┐
│ Backend process (one per connection)                │
│  Parser → Analyzer → Rewriter → Planner → Executor  │
└───────────────┬─────────────────────────────────────┘
                │ reads/writes 8KB pages
                ▼
      ┌──────────────────────┐      evict/flush
      │  Shared Buffer Pool  │────────────────────┐
      │  (RAM page cache)    │                    ▼
      └──────────┬───────────┘             ┌────────────┐
                 │ miss                     │ Heap files │  (tables, random I/O)
                 ▼                          │ Index files│
          ┌────────────┐                    └────────────┘
          │    Disk    │
          └────────────┘
   COMMIT path (durability):
   change → WAL buffer → fsync WAL (sequential append) → COMMIT returns
                              │
                              └── WAL also streams to replicas (Module 7)
```

### 5. Real Production Example
**Stripe**: every payment mutation must survive a machine dying mid-write. WAL-before-data
(write-ahead logging) is the exact mechanism that guarantees a charge marked "captured" is never
lost, and the same WAL stream feeds read replicas and change-data-capture into Kafka.
When an interviewer asks "how does a DB not lose data on power failure," WAL + fsync + recovery
replay is the expected answer.

### 6. Common Interview Questions
- "Why not just store data in files / S3?"
- "Walk me through what happens when I run a query." (classic Google warm-up)
- "How does a database survive a crash mid-transaction?"
- "Why is one-connection-per-request a problem in Postgres?"
- "What is the buffer pool and why does it matter for performance?"

### 7. Common Mistakes
- Answering "databases are for storing data" — zero signal.
- Claiming COMMIT writes the data pages to disk. It writes the **WAL**; data pages flush later.
- Forgetting that Postgres connections are processes (~5–10MB each), so 5,000 app connections
  will take the DB down without a pooler.
- Confusing the query *cache* (MySQL, removed in 8.0) with the buffer pool.

### 8. Best Practices
- Frame every performance question in terms of **pages touched**: a query is fast when it reads
  few 8KB pages, and those pages are in the buffer pool.
- Know your DB's memory knobs: `shared_buffers` (~25% RAM), `work_mem` (per-sort/hash!),
  `wal_buffers`, `effective_cache_size` (planner hint, not allocation).
- Always put PgBouncer (transaction mode) or RDS Proxy in front of Postgres at scale.

### 9. Coding Questions
1. Given a 100GB table and 16GB RAM, estimate why a full scan is disk-bound and what fraction
   of the buffer pool a hot 2GB index consumes.
2. Write pseudocode for crash recovery given a WAL of `[BEGIN T1, T1: x=5, COMMIT T1, BEGIN T2, T2: y=7, CRASH]`
   (redo committed, ignore/undo uncommitted).

### 10. SQL Examples
```sql
-- See the plan and real execution (Module 5 covers reading it)
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE user_id = 42;

-- Buffer cache hit ratio (want > 0.99 for OLTP)
SELECT sum(blks_hit)::float / nullif(sum(blks_hit) + sum(blks_read), 0) AS cache_hit_ratio
FROM pg_stat_database;

-- Table size vs index size (pages on disk)
SELECT relname,
       pg_size_pretty(pg_table_size(oid))  AS table_size,
       pg_size_pretty(pg_indexes_size(oid)) AS index_size
FROM pg_class WHERE relname = 'orders';
```

### 11. Optimization Techniques
- Keep the **working set** (hot pages) in RAM; monitor cache hit ratio.
- Batch writes: 1 transaction with 1,000 inserts ≫ 1,000 transactions (one fsync vs a thousand).
- `synchronous_commit = off` for tolerable-loss workloads (metrics, logs): commit returns before
  WAL fsync — huge throughput win, risk of losing last few ms on crash (not corruption).

### 12. Follow-up Questions
- "What happens if the WAL disk is slow but data disk is fast?" (commits stall — WAL fsync is
  the commit critical path)
- "How does the WAL enable replication?" (ship/stream the same log — Module 7)
- "What's a checkpoint and why does it cause I/O spikes?" (flush all dirty pages; spread with
  `checkpoint_completion_target`)

---

## Chapter 1.2 — RDBMS vs NoSQL (SQL vs NoSQL)

### 1. Why Interviewers Ask This
It's the #1 system-design gate question. They're testing whether you choose databases based on
**access patterns, consistency needs, and scale**, or based on hype. A senior answer never says
"NoSQL is faster" — it names the specific trade-off.

### 2. Core Concept
| Dimension | RDBMS (Postgres/MySQL) | NoSQL (Mongo/Cassandra/DynamoDB/Redis) |
|---|---|---|
| Data model | Relations, rigid schema | Document / wide-column / KV / graph |
| Query model | Declarative SQL, ad-hoc joins | API by primary key; limited/no joins |
| Consistency | ACID transactions, strong by default | Mostly tunable / eventual (Dynamo, Cassandra); Mongo has multi-doc txns since 4.0 |
| Scaling | Vertical + read replicas; sharding is manual/painful | Horizontal sharding is native |
| Schema evolution | Migrations (DDL) | Flexible, app enforces shape |
| Best at | Transactions, integrity, ad-hoc queries | Massive scale on *known* access patterns |

The real dividing line: **RDBMS optimizes for flexible queries over one node's worth of data
with strong guarantees. NoSQL optimizes for one or two access patterns over unbounded data.**

### 3. Internal Working
- Postgres/MySQL: B+Tree storage, WAL, MVCC, cost-based planner — random-access read-optimized.
- Cassandra/DynamoDB-style: **LSM trees** (Module 8) — sequential-write-optimized, reads may
  check several SSTables; consistent hashing spreads partitions across nodes with no master.
- MongoDB: B+Tree (WiredTiger) documents, replica sets with a single primary, range/hash sharding.
- Redis: everything in RAM, single-threaded event loop per shard — microsecond latency.

### 4. Visualization (ASCII)
```
RDBMS (scale-up + replicas)          NoSQL (scale-out, e.g. Cassandra ring)

        ┌─────────┐                        hash(key) picks node
writes →│ Primary │                     ┌────┐
        └────┬────┘                 ┌──▶│ N1 │ keys [0-25%)
             │ WAL stream           │   └────┘
     ┌───────┼───────┐        key ──┤   ┌────┐
     ▼       ▼       ▼              ├──▶│ N2 │ keys [25-50%)
 ┌───────┐┌───────┐┌───────┐        │   └────┘
 │Replica││Replica││Replica│        ├──▶│ N3 │ ... each key replicated
 └───────┘└───────┘└───────┘        │   └────┘     to RF=3 nodes
  reads scale; writes do NOT        └──▶ ...   writes AND reads scale
```

### 5. Real Production Example
- **Uber**: trips/payments in MySQL-based Schemaless + Postgres early on (integrity), but the
  driver-location firehose (millions of writes/sec, only queried by driver_id) went to
  Cassandra-style stores and Redis.
- **Amazon**: the shopping cart famously moved to Dynamo because a cart must accept writes even
  during a partition (availability > consistency for carts); orders/payments stayed strongly
  consistent.
- **Netflix**: viewing history in Cassandra (append-heavy, per-user key), billing in MySQL.

### 6. Common Interview Questions
- "You're designing X — SQL or NoSQL? Why?"
- "What do you lose when you move from Postgres to DynamoDB?" (ad-hoc queries, joins,
  multi-row ACID by default, constraints)
- "When would you use both?" (almost always: system of record in RDBMS + NoSQL for hot paths)
- "Is MongoDB ACID?" (single-document always; multi-document transactions exist but are
  expensive and limited — using them heavily means you probably wanted an RDBMS)

### 7. Common Mistakes
- "NoSQL because we need scale" without stating the write volume or access pattern.
- Ignoring that **Postgres handles 10k+ writes/sec and multi-TB tables** fine — most startups
  never outgrow it. Premature NoSQL adoption costs you joins, transactions, and migrations agility.
- Modeling relational data (many-to-many, ad-hoc reporting) in a document store, then doing
  joins in application code.
- Saying "schemaless means no schema" — the schema moves into your application code, unversioned.

### 8. Best Practices
- Default to PostgreSQL. Move a *specific workload* to NoSQL when you can name the access
  pattern and the scale number that breaks the RDBMS.
- Choose by access pattern: key-value at huge scale → DynamoDB/Cassandra; caching/ephemeral →
  Redis; flexible nested documents, mid-scale → MongoDB; ad-hoc queries + transactions → RDBMS.
- In interviews, always state what you sacrifice — that's the senior signal.

### 9. Coding Questions
1. Model "user has many orders, order has many items" in Postgres (3 tables) and in DynamoDB
   (single table, `PK=USER#id`, `SK=ORDER#id#ITEM#n`) and list which queries each supports cheaply.
2. Given 1M writes/sec of IoT sensor readings queried only by `(device_id, time range)`, pick a
   store and justify (Cassandra/LSM wins; B+Tree random inserts + index maintenance lose).

### 10. SQL Examples
```sql
-- Relational strength: an ad-hoc question you never planned for
SELECT u.country, count(*) AS orders, avg(o.total_cents) AS avg_order
FROM orders o JOIN users u ON u.id = o.user_id
WHERE o.created_at >= now() - interval '30 days'
GROUP BY u.country ORDER BY orders DESC;
-- In DynamoDB this is a full-table export + offline job unless you pre-modeled it.

-- Postgres as a document store (often the right middle ground)
CREATE TABLE events (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  payload jsonb NOT NULL
);
CREATE INDEX ON events USING gin (payload jsonb_path_ops);
SELECT * FROM events WHERE payload @> '{"type": "checkout", "status": "failed"}';
```

### 11. Optimization Techniques
- Hybrid architecture: RDBMS as source of truth, Redis cache in front, stream changes (CDC) to
  Elasticsearch/analytics. This answers most "scale the reads" questions.
- In RDBMS, use `jsonb` for genuinely schemaless fragments instead of adopting a second database.
- In NoSQL, design the table *from the queries backwards* (Module 8).

### 12. Follow-up Questions
- "Your startup on Postgres just hit 50k writes/sec on one table — options?" (partition, shard,
  queue+batch, or move that table to Cassandra/DynamoDB; discuss trade-offs)
- "How do you keep Redis/Elasticsearch in sync with Postgres?" (CDC via WAL → Debezium/Kafka;
  discuss ordering + at-least-once)
- "What does DynamoDB single-table design cost you?" (rigid access patterns, painful evolution)

---

## Chapter 1.3 — ACID vs BASE

### 1. Why Interviewers Ask This
ACID is the most-asked database question, at every level. At senior level they push past the
acronym: *how* is each letter implemented, and what does BASE actually buy you.

### 2. Core Concept
**ACID** (per transaction):
- **Atomicity** — all statements apply or none do. No partial effects, even on crash.
- **Consistency** — the transaction moves the DB from one valid state to another; constraints
  (PK/FK/CHECK/triggers) hold. (Note: the "C" is partly the *application's* job.)
- **Isolation** — concurrent transactions behave as if serialized (to a degree set by the
  isolation level — Module 6).
- **Durability** — once COMMIT returns, the data survives crash/power loss.

**BASE** (distributed, availability-first systems):
- **Basically Available** — the system answers even during failures/partitions.
- **Soft state** — state may change without input (replicas converging).
- **Eventual consistency** — stop writing, and all replicas converge to the same value.

BASE is not "no guarantees" — it's a deliberate trade: accept stale reads and conflict
resolution in exchange for availability and horizontal write scale.

### 3. Internal Working
| Property | PostgreSQL mechanism |
|---|---|
| Atomicity | MVCC: new row versions carry the writing transaction's XID; a single atomic flip of the transaction's status in `pg_xact` (commit log) makes *all* its versions visible or dead at once. Rollback = mark aborted; dead versions cleaned by VACUUM. |
| Consistency | Constraint checks at statement/commit time; deferred constraints checked at COMMIT |
| Isolation | MVCC snapshots + row locks; SSI for SERIALIZABLE (Module 6) |
| Durability | WAL fsync before COMMIT returns; `synchronous_standby` extends this to replicas |

BASE example (DynamoDB/Cassandra): a write goes to N replicas; with `W=1` the coordinator acks
after one replica accepts; anti-entropy (hinted handoff, read repair, Merkle-tree sync) converges
the rest. Conflicts resolved by last-write-wins timestamps (Cassandra) or vector clocks (Dynamo).

### 4. Visualization (ASCII)
```
ACID commit (Postgres)                 BASE write (Cassandra, RF=3, W=1)

BEGIN                                   client ──▶ coordinator
  UPDATE a; UPDATE b;                              │ send to 3 replicas
COMMIT                                             ├─▶ R1 ✔ (ack) ──▶ client OK
  │                                                ├─▶ R2 ... slow
  ├─ WAL record ─▶ fsync ✔                         └─▶ R3 ✖ down (hint stored)
  └─ flip commit bit in pg_xact                     later: hinted handoff / read
     (atomic: a AND b visible together)             repair converges R2, R3
Reader before flip: sees neither       Reader meanwhile: may see old value
Reader after flip:  sees both          on R2/R3  → EVENTUAL consistency
```

### 5. Real Production Example
**Stripe / any payments system**: moving money between two balances *must* be atomic — debit and
credit in one transaction, or you invent/destroy money. Meanwhile the "recent transactions" feed
shown in the dashboard can be BASE — a few seconds stale is fine. Senior answer: *split the
system by invariant strength*, don't pick one model globally.

### 6. Common Interview Questions
- "Explain ACID with how each property is implemented." (the senior version)
- "Which ACID property does a crash test? A concurrent update test?" (D/A; I)
- "Is eventual consistency acceptable for a bank?" (balances: no; notification feed: yes —
  and real banks use *reconciliation*, which is eventual consistency with auditing)
- "What anomalies can users see under eventual consistency?" (stale reads, non-monotonic reads,
  read-your-own-write failures)

### 7. Common Mistakes
- Reciting the acronym with no mechanism — automatic mid-level cap.
- Saying Consistency (ACID) = Consistency (CAP). They're different words: ACID-C is about
  integrity constraints; CAP-C is linearizability across replicas.
- Believing durability is absolute: with `synchronous_commit=off` or async replication you can
  lose acknowledged writes; know your configuration.
- Thinking BASE systems can't do transactions at all (DynamoDB has `TransactWriteItems`,
  Mongo has multi-doc txns — limited and costly, but exist).

### 8. Best Practices
- Identify each business invariant and assign it a consistency budget: money movement =
  ACID + synchronous replication; feeds/counters/caches = eventual.
- For cross-service "transactions," don't distribute ACID — use sagas/outbox with idempotency
  keys (mention this; it's a favorite Stripe/Uber follow-up).
- Make writes idempotent everywhere eventual consistency or retries exist.

### 9. Coding Questions
1. Write the transfer transaction (below) and explain what happens if the process crashes
   between the two UPDATEs.
2. Design an idempotent "charge customer" API: unique idempotency key + `INSERT ... ON CONFLICT DO NOTHING`
   returning the prior result.

### 10. SQL Examples
```sql
-- Atomic money transfer
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
-- crash here? WAL has no COMMIT record → recovery discards both updates
COMMIT;

-- Consistency via constraint: overdrafts impossible even under bugs
ALTER TABLE accounts ADD CONSTRAINT non_negative CHECK (balance >= 0);

-- Idempotency for BASE-world retries
CREATE TABLE payments (
  idempotency_key text PRIMARY KEY,
  amount_cents int NOT NULL,
  status text NOT NULL DEFAULT 'pending'
);
INSERT INTO payments (idempotency_key, amount_cents)
VALUES ('req-abc-123', 4999)
ON CONFLICT (idempotency_key) DO NOTHING;
```

### 11. Optimization Techniques
- Group related writes into one transaction: atomicity for free *and* one WAL fsync.
- Keep transactions short — long transactions hold back VACUUM and increase lock/serialization
  conflicts (Module 6/11).
- Relax durability only where loss is acceptable and say so explicitly (`synchronous_commit=off`
  per-session for bulk loads).

### 12. Follow-up Questions
- "Two services must both commit or neither — how, without 2PC?" (outbox + saga with
  compensating actions; discuss why 2PC is avoided: blocking on coordinator failure)
- "How does Postgres make a multi-row transaction visible atomically?" (single commit-bit flip;
  snapshots decide visibility)
- "What's read-your-own-writes and how do you guarantee it with replicas?" (session pinning to
  primary, or wait-for-LSN on the replica)

---

## Chapter 1.4 — CAP Theorem & Strong vs Eventual Consistency

### 1. Why Interviewers Ask This
Every distributed-database decision routes through CAP. Interviewers use it to check you can
reason under failure, and to catch the common misstatement ("pick 2 of 3").

### 2. Core Concept
In a distributed system, when a **network partition** (P) happens, you must choose:
- **CP**: refuse some requests (lose availability) to stay consistent — e.g., a minority-side
  node rejects writes.
- **AP**: keep answering (stay available) and accept divergence — reconcile later.

Key corrections seniors are expected to make:
- **P is not optional.** Networks partition; the only choice is C vs A *during* the partition.
- CAP-Consistency = **linearizability** (every read sees the latest acknowledged write, as if
  one copy). Not ACID-C.
- **PACELC** extension: *if Partition, trade A vs C; Else (normal operation), trade Latency vs
  Consistency.* Even with no partition, synchronous replication costs latency.
  DynamoDB ≈ PA/EL. Postgres+sync replica ≈ PC/EC. Cassandra tunable.

Consistency spectrum (strong → weak):
`Linearizable → Sequential → Causal → Read-your-writes / Monotonic reads → Eventual`

### 3. Internal Working
- **CP systems** (Spanner, etcd, Zookeeper, Postgres with sync replication + failover):
  quorum/consensus (Paxos/Raft). A write commits when a majority accepts it; minority partitions
  can't serve linearizable reads or accept writes.
- **AP systems** (Dynamo, Cassandra with `W=1,R=1`): any replica accepts writes; sloppy quorums
  and hinted handoff keep availability; convergence via read-repair/anti-entropy; conflicts via
  LWW or vector clocks.
- **Tunable**: Cassandra per-query consistency. If `R + W > RF` (e.g. QUORUM reads + QUORUM
  writes with RF=3 → 2+2>3), read and write sets overlap → you read the latest write
  (strongly consistent read, at latency/availability cost).

### 4. Visualization (ASCII)
```
        Partition splits the cluster
   ┌──────────────┐    ✂ network ✂    ┌──────────────┐
   │  N1  N2      │                   │      N3      │
   │  (majority)  │                   │  (minority)  │
   └──────────────┘                   └──────────────┘
CP: N1,N2 keep serving (quorum=2/3).  N3 REJECTS writes & linearizable reads
    → consistent, partially unavailable
AP: all three keep serving            N3 accepts write x=5, N1 has x=4
    → available, divergent → merge later (LWW / vector clocks / CRDT)
```

### 5. Real Production Example
- **Amazon cart (AP)**: never refuse "add to cart." Divergent carts merge by union — worst case
  a deleted item reappears. Business chose availability.
- **Google Spanner (CP)**: AdWords billing needs global consistency; Spanner uses Paxos +
  TrueTime. During partition, minority regions stall — Google accepts that.
- **Netflix (AP)**: viewing state in Cassandra; a stale "continue watching" row is harmless.

### 6. Common Interview Questions
- "Explain CAP. Is CA possible?" (only in a single-node/no-partition world — i.e., not a
  distributed system guarantee)
- "Where does DynamoDB / Cassandra / Postgres / Spanner sit?"
- "How do you get a strongly consistent read from Cassandra?" (`R+W>RF`)
- "Design X: which consistency level per operation?" (the real question behind CAP)

### 7. Common Mistakes
- "Pick two of three" framing — P isn't a choice.
- Applying CAP to a single-node Postgres ("Postgres is CA") — CAP is about replicated systems.
- Treating eventual consistency as unbounded chaos: in practice convergence is ms–seconds, and
  you can layer session guarantees (read-your-writes) on top.
- Forgetting PACELC: consistency costs latency even without failures.

### 8. Best Practices
- Answer per-operation, not per-system: "checkout is CP, product views are AP."
- Name the anomaly the user would see under AP and whether the business tolerates it.
- Mention quorum arithmetic (`R+W>RF`) — it's the concrete tool interviewers want to hear.

### 9. Coding Questions
1. RF=3. Give (W,R) pairs for: fastest writes ever (W=1,R=1), strong reads with balanced cost
   (W=2,R=2), write-heavy strong (W=1,R=3). State availability impact of each.
2. Sketch read-your-own-writes for a Postgres primary + replicas: after write, capture
   `pg_current_wal_lsn()`; on replica, wait until `pg_last_wal_replay_lsn() >= lsn` or route
   that session to the primary.

### 10. SQL Examples
```sql
-- Replication lag on a Postgres replica (staleness you'd serve under async replication)
SELECT now() - pg_last_xact_replay_timestamp() AS replica_lag;

-- Synchronous replication = choosing C (and paying latency / availability)
-- postgresql.conf: synchronous_standby_names = 'ANY 1 (r1, r2)'
-- Per-transaction downgrade for non-critical writes:
SET LOCAL synchronous_commit = off;
```

### 11. Optimization Techniques
- Use causal/session consistency instead of full linearizability when possible — cheaper, fixes
  the visible anomalies (user sees own writes).
- Local quorums (`LOCAL_QUORUM`) in multi-region Cassandra: strong-ish within region without
  cross-region latency.
- CRDTs for AP counters/sets (mention: Riak, Redis CRDT modules) to make merges automatic.

### 12. Follow-up Questions
- "What does TrueTime buy Spanner?" (bounded clock uncertainty → external consistency without
  cross-region locks on reads)
- "Your AP system shows a user their comment disappearing and reappearing — fix?" (monotonic
  reads: sticky routing to the same replica, or client-tracked versions)
- "Why is 2PC not a CAP escape hatch?" (coordinator failure blocks everyone — it sacrifices A
  *and* liveness)

---

## Chapter 1.5 — OLTP vs OLAP

### 1. Why Interviewers Ask This
"Why is this analytics query killing the production DB?" is a real incident at every company.
This topic tests whether you know workloads shape storage engines — row vs column layout.

### 2. Core Concept
| | OLTP | OLAP |
|---|---|---|
| Work unit | Many tiny transactions (point reads/writes) | Few huge scans/aggregations |
| Pattern | `WHERE id = ?`, touch few rows, all columns | Touch millions of rows, few columns |
| Storage | **Row-oriented** (whole row contiguous) | **Column-oriented** (each column contiguous) |
| Index | B+Tree point/range lookups | Zone maps, min/max pruning, partitions |
| Latency target | ms | seconds–minutes acceptable |
| Systems | Postgres, MySQL, DynamoDB | Snowflake, BigQuery, Redshift, ClickHouse |

### 3. Internal Working
- **Row store**: one 8KB page holds complete rows → `SELECT * WHERE id=?` reads ~1–4 pages.
  Perfect for OLTP; terrible for "sum one column over 500M rows" (reads *every* column's bytes).
- **Column store**: `amount` values stored contiguously → scan reads only that column;
  compression is extreme (similar values together: RLE, dictionary, delta) → 10–50x less I/O;
  vectorized execution (SIMD over column batches). But updating one "row" touches many files →
  bad at OLTP.
- Bridge: **CDC/ETL** replicates OLTP data into the warehouse (minutes of lag); HTAP systems
  (TiDB, AlloyDB, SingleStore) keep both layouts internally.

### 4. Visualization (ASCII)
```
Row store page:                     Column store files:
[id1|name1|city1|amt1]              ids:   [1,2,3,4,...]  ←compressed
[id2|name2|city2|amt2]              names: [n1,n2,n3,...]
[id3|name3|city3|amt3]              citys: [c1,c1,c1,...] ←RLE crushes this
                                    amts:  [a1,a2,a3,...] ←SUM reads ONLY this
SELECT * WHERE id=2  → 1 page ✔     SELECT * WHERE id=2 → touch every file ✖
SUM(amt) 500M rows  → all pages ✖   SUM(amt) → one compressed column ✔
```

### 5. Real Production Example
**Netflix**: playback start/stop events land in OLTP-ish stores and Kafka, then flow into an
S3/Iceberg warehouse queried by Trino/Spark for engagement analytics. Nobody runs
`GROUP BY title` over the serving database. The standard incident: an analyst's dashboard query
on the production replica saturates I/O and lags replication → move analytics off OLTP.

### 6. Common Interview Questions
- "Why are column stores faster for analytics?" (I/O reduction + compression + vectorization)
- "Why not run reports on the primary / replica?" (I/O + cache pollution + replication lag +
  long transactions blocking vacuum)
- "How does data get from OLTP to the warehouse?" (CDC → Kafka → warehouse; batch ETL)
- "What's HTAP?"

### 7. Common Mistakes
- Adding indexes to make an OLAP query fast on Postgres — indexes don't help scan-90%-of-table
  queries; the layout is wrong.
- Running month-long aggregates in the request path instead of precomputing (materialized views,
  rollup tables).
- Letting BI tools hit production with `SELECT *` over years of data.

### 8. Best Practices
- Separate serving from analytics from day one: replica → then CDC to a real warehouse.
- Precompute aggregates consumed by product surfaces (counts, totals) — don't aggregate at read time.
- In Postgres, `BRIN` indexes + partitioning give "poor-man's OLAP" for append-only time-series.

### 9. Coding Questions
1. Estimate: 500M rows × 200B/row row-store vs a 4-byte column with 8x compression — how many
   bytes does `SUM(amount)` read in each? (~100GB vs ~250MB)
2. Design the pipeline: orders table → hourly revenue dashboard with <5 min lag (CDC → Kafka →
   ClickHouse/warehouse → dashboard; or Postgres materialized view if small).

### 10. SQL Examples
```sql
-- OLTP query: point lookup, index, ms
SELECT * FROM orders WHERE id = 91823;

-- OLAP query: don't run this on the OLTP primary
SELECT date_trunc('month', created_at) AS month,
       country, sum(total_cents) / 100.0 AS revenue
FROM orders
WHERE created_at >= '2025-01-01'
GROUP BY 1, 2 ORDER BY 1, 2;

-- Poor-man's OLAP in Postgres: precomputed rollup
CREATE MATERIALIZED VIEW monthly_revenue AS
SELECT date_trunc('month', created_at) AS month, sum(total_cents) AS revenue_cents
FROM orders GROUP BY 1;
REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_revenue;
```

### 11. Optimization Techniques
- Partition big fact tables by time → partition pruning replaces index for range scans.
- BRIN index on `created_at` for append-only tables: tiny index, prunes page ranges.
- Aggregate incrementally (upsert into rollup on write, or streaming) instead of re-scanning.

### 12. Follow-up Questions
- "Your replica lags whenever the ETL runs — why?" (big reads evict cache + long snapshot holds;
  fix: dedicated replica or CDC)
- "Why is `COUNT(*)` slow in Postgres but instant in a column store?" (MVCC forces visibility
  checks per row vs column-store metadata; Module 5)
- "When is HTAP worth it vs a pipeline?" (freshness requirements vs operational complexity)

---

## Chapter 1.6 — Normalization vs Denormalization

### 1. Why Interviewers Ask This
Schema-design round staple. Tests whether you understand *why* redundancy is dangerous
(anomalies) and *when* it's the right choice anyway (read-path performance). Senior candidates
are expected to defend deliberate denormalization.

### 2. Core Concept
**Normalization** removes redundancy so every fact lives in exactly one place.
- **1NF**: atomic values, no repeating groups (no CSV-in-a-column).
- **2NF**: no partial dependency — non-key columns depend on the *whole* composite key.
- **3NF**: no transitive dependency — non-key columns depend *only* on the key.
  ("The key, the whole key, and nothing but the key.")
- BCNF: every determinant is a candidate key (rarely probed beyond name-dropping).

Update/insert/delete **anomalies** are what normalization prevents: change a product's name
stored in 10M order rows and miss some → contradictory data.

**Denormalization** deliberately re-introduces redundancy to kill joins/aggregations on hot read
paths — accepting that the application must now keep copies in sync.

### 3. Internal Working
- Normalized reads = joins; each join is a B+Tree probe or hash build (Module 3). 5-way joins at
  p99 under load add up.
- Denormalized writes = multi-row/multi-table updates (fan-out). Consistency maintained by
  transactions, triggers, or async jobs — each with failure modes.
- The classic middle ground: **snapshot columns** (order stores `product_name`, `unit_price` at
  purchase time — this is *correct*, not just fast: historical facts shouldn't change) and
  **counter caches** (`users.post_count`).

### 4. Visualization (ASCII)
```
Normalized                          Denormalized read model
users(id, name)                     order_view(order_id, user_name,
orders(id, user_id, product_id)                product_name, price, ...)
products(id, name, price)                       ▲
                                                │ kept in sync by txn /
read = 3-way JOIN                               │ trigger / async consumer
write = 1 row, 1 place ✔            read = 1 row, 0 joins ✔
                                    write = N copies to update ✖
Anomaly demo (denormalized): product renamed → update 10M rows or serve two names
```

### 5. Real Production Example
**Meta / Twitter feeds**: fully normalized "read the feed" = join follows × posts × users at
request time — impossible at scale. Solution: denormalized per-user feed lists (fan-out on
write into Redis/Cassandra) — the canonical denormalization story. Meanwhile the *source of
truth* (users, posts) stays normalized in MySQL. **Amazon orders**: item name & price copied
into `order_items` forever — a price change must not rewrite history.

### 6. Common Interview Questions
- "Explain 1NF/2NF/3NF with an example." (be able to do it in 60 seconds)
- "When would you denormalize?" (measured read bottleneck on a join/aggregate hot path;
  read≫write ratio; or snapshot semantics)
- "How do you keep denormalized copies consistent?" (same-transaction, triggers, CDC/async +
  reconciliation)
- "Design an orders schema — why did you copy price into order_items?" (snapshot correctness)

### 7. Common Mistakes
- Denormalizing preemptively "for performance" with no measurement — you inherit sync bugs for nothing.
- Normalizing history away: joining `orders → products.price` shows *today's* price on old
  orders. Classic trap question.
- Storing lists as CSV/JSON arrays then needing to query by element (violates 1NF; forces
  full scans — in Postgres at least use `jsonb` + GIN if you must).
- Saying "3NF is always right" or "joins are slow" — both junior signals; indexed joins on OLTP
  point queries are fast.

### 8. Best Practices
- Normalize the write model (source of truth) to 3NF by default.
- Denormalize *read models* (CQRS-lite): rollups, counter caches, feed tables — rebuildable from
  the source of truth (that's your escape hatch when they drift).
- Snapshot immutable business facts (prices, addresses, tax rates) at event time.
- If a counter/copy can drift, schedule a reconciliation job. Say the word "reconciliation" —
  it lands well.

### 9. Coding Questions
1. Normalize `orders(id, user_email, user_name, product_names_csv, total)` to 3NF — identify
   which normal form each fix addresses.
2. Add a consistent `posts_count` to `users`: same-transaction `UPDATE users SET posts_count =
   posts_count + 1` on insert, and explain the lock contention it creates on hot users
   (and the async alternative).

### 10. SQL Examples
```sql
-- 3NF write model with snapshot columns on the read-critical child
CREATE TABLE products (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name text NOT NULL,
  price_cents int NOT NULL
);
CREATE TABLE orders (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE order_items (
  order_id bigint REFERENCES orders(id),
  product_id bigint REFERENCES products(id),
  product_name text NOT NULL,     -- snapshot: history must not change
  unit_price_cents int NOT NULL,  -- snapshot
  quantity int NOT NULL CHECK (quantity > 0),
  PRIMARY KEY (order_id, product_id)
);

-- Counter cache maintained transactionally
BEGIN;
INSERT INTO posts (user_id, body) VALUES (42, '...');
UPDATE users SET posts_count = posts_count + 1 WHERE id = 42;
COMMIT;
```

### 11. Optimization Techniques
- Prefer a **covering index** (Module 4) or **materialized view** before physically
  denormalizing base tables — cheaper to maintain, easy to drop.
- For hot counters, batch increments (accumulate in Redis, flush periodically) to avoid
  single-row lock contention.
- Keep every denormalized artifact rebuildable with one SQL statement; document it next to the DDL.

### 12. Follow-up Questions
- "Your counter cache drifted — how do you detect and fix without downtime?" (periodic diff
  against `COUNT(*)`, repair in batches)
- "Trigger vs application code vs CDC for sync — trade-offs?" (triggers: consistent but hidden
  and add write latency; CDC: decoupled but eventual)
- "How does this change in DynamoDB?" (denormalization is the *default*; you duplicate into
  item collections/GSIs by design)

---

## Chapter 1.7 — Primary Key vs Unique Key vs Foreign Key

### 1. Why Interviewers Ask This
Screener question with senior-level depth hiding inside: UUID vs sequence, FK locking costs,
and "should we drop FKs at scale" are real design fights at Uber/Stripe-scale companies.

### 2. Core Concept
| | Primary Key | Unique Constraint/Key | Foreign Key |
|---|---|---|---|
| Purpose | Row identity | Enforce alternate uniqueness | Referential integrity (child → parent) |
| NULLs | Never | Allowed (Postgres: NULLs don't collide by default; 15+ has `NULLS NOT DISTINCT`) | NULL = "no parent", allowed |
| Per table | Exactly one | Many | Many |
| Implementation | Unique B+Tree index (+ NOT NULL) | Unique B+Tree index | Constraint checked via parent's PK/unique index |
| Extra role | Target of FKs; **MySQL/InnoDB: the clustered index** | Natural-key guard | Cascades (`ON DELETE ...`) |

Surrogate keys (`bigint identity` / UUID) vs natural keys (email, SSN): natural keys change and
leak semantics — use surrogates for identity, add unique constraints on natural keys.

### 3. Internal Working
- PK/unique = B+Tree where insert descends to the leaf; if the key exists (and is committed or
  from a concurrent txn — insert *waits* on the conflicting txn) → unique violation.
- **FK enforcement**: inserting a child takes a `FOR KEY SHARE` lock on the parent row (so the
  parent can't be deleted mid-insert); deleting a parent must check the child table — **if
  there's no index on the child FK column, that check is a sequential scan per delete** and
  cascades take row locks on every child. This is the #1 FK performance trap.
- MySQL/InnoDB: the table *is* the PK B+Tree (clustered). Random PKs (UUIDv4) cause page splits
  and buffer-pool churn; sequential PKs append. Postgres heaps don't cluster, but UUIDv4 still
  bloats indexes and wrecks cache locality → prefer `bigint identity` or time-ordered UUIDv7/ULID.

### 4. Visualization (ASCII)
```
FK check on INSERT child(order_id=7):
 child row ──lookup──▶ parent PK index ──▶ row 7 exists?
                                            │ yes: lock FOR KEY SHARE, proceed
                                            │ no : ERROR fk violation
DELETE parent(7):
 parent ──must check──▶ child table WHERE order_id=7
     with index on child.order_id : B+Tree probe  ✔ fast
     without index                : FULL SCAN per delete ✖ + long row locks

UUIDv4 inserts into B+Tree:            bigint/UUIDv7 inserts:
 scattered ▼   ▼    ▼   (page splits)   append ▶▶▶ (rightmost leaf, hot cache)
[..][..][..][..][..]                    [..][..][..][▶]
```

### 5. Real Production Example
**Uber-style shard-out**: FKs can't span shards, so at extreme scale companies drop DB-level FKs
and enforce integrity in services + async auditors — a *deliberate* trade of integrity for
scalability/ownership. Conversely, **Stripe-style ledgers** keep FKs and constraints exactly
because money rows must never orphan. Know both positions and when each is right.

### 6. Common Interview Questions
- "PK vs unique key — all differences?" (NULLs, count, FK target, clustering in InnoDB)
- "UUID or auto-increment for the PK?" (discuss: guessability, sharding/merge-ability,
  B+Tree locality; answer: bigint internally or UUIDv7 if globally unique needed)
- "Why index foreign key columns?" (delete/cascade scans + join performance)
- "Would you use FKs at massive scale?" (trade-off discussion, not yes/no)

### 7. Common Mistakes
- Forgetting Postgres does **not** auto-index the child side of an FK (it only requires the
  *parent* side to be unique). Missing child indexes → slow deletes, lock pileups.
- Choosing natural PKs (email) that later change → cascading updates everywhere.
- UUIDv4 PKs on write-heavy InnoDB tables → page-split storm.
- `ON DELETE CASCADE` on huge child tables → one parent delete silently deletes millions of rows
  in one transaction (lock + WAL explosion).

### 8. Best Practices
- `bigint GENERATED ALWAYS AS IDENTITY` internal PK; expose a separate public ID (UUIDv7/ULID)
  if IDs leave the system.
- Index every FK column; add composite indexes that *start* with the FK when you filter further.
- Prefer `ON DELETE RESTRICT` + explicit application deletes for big graphs; use soft deletes
  where audit matters.
- Enforce natural uniqueness with unique constraints, not application checks (race-proof).

### 9. Coding Questions
1. Find FK columns missing indexes (join `pg_constraint` contype='f' against `pg_index` —
   write the catalog query).
2. Enforce "a user has at most one active subscription" —
   `CREATE UNIQUE INDEX ON subscriptions(user_id) WHERE status = 'active';` (partial unique).

### 10. SQL Examples
```sql
CREATE TABLE users (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  public_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,  -- exposed ID
  email citext NOT NULL UNIQUE                                -- natural key guarded
);

CREATE TABLE orders (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL REFERENCES users(id) ON DELETE RESTRICT
);
CREATE INDEX ON orders (user_id);          -- FK index: NOT automatic in Postgres

-- Race-proof "insert if new" on a natural key
INSERT INTO users (email) VALUES ('a@b.com')
ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
RETURNING id;
```

### 11. Optimization Techniques
- Time-ordered keys (identity, UUIDv7) keep B+Tree inserts append-only → fewer splits, hot
  rightmost pages cached.
- Add FKs to existing big tables with `NOT VALID` then `VALIDATE CONSTRAINT` (validation scans
  without blocking writes).
- Batch parent deletes; delete children first in chunks to bound transaction size.

### 12. Follow-up Questions
- "How do you generate unique IDs across shards?" (Snowflake IDs: timestamp+worker+sequence;
  or UUIDv7; or per-shard ranges)
- "Deferrable constraints — when?" (swap-type updates where uniqueness is violated mid-txn:
  `DEFERRABLE INITIALLY DEFERRED`)
- "What lock does an FK insert take on the parent, and what does it block?" (`FOR KEY SHARE`;
  blocks parent key updates/deletes, not normal column updates)

---

## Chapter 1.8 — Transactions (Introduction)

*(Full concurrency treatment — isolation levels, MVCC, locks, deadlocks — is Module 6. This
chapter covers what belongs in "fundamentals" rounds.)*

### 1. Why Interviewers Ask This
Transactions are where correctness meets performance. Fundamentals rounds check you know the
lifecycle and the *shape* of correct transactional code: short, idempotent, retry-aware.

### 2. Core Concept
A transaction is the unit of atomicity, isolation and durability: `BEGIN` → statements →
`COMMIT` (all effects visible atomically, durable) or `ROLLBACK` (no effects). Postgres runs
*every* statement in a transaction (autocommit wraps single statements). `SAVEPOINT` gives
partial rollback inside a transaction.

Three rules of production transactions:
1. **Short** — hold locks & snapshots for milliseconds, never across network calls or user think-time.
2. **Idempotent/retryable** — serialization failures (40001) and deadlocks (40P01) are *normal*;
   the app must retry.
3. **Right-sized** — exactly the rows that must change together; no more (lock contention),
   no less (broken invariants).

### 3. Internal Working
- `BEGIN` assigns a virtual txn ID; the first write gets a real **XID**.
- Every written row version is stamped `xmin=XID` (creator); deletes/updates stamp `xmax`
  (deleter) on the old version — updates are delete+insert in MVCC (Module 6).
- `COMMIT`: WAL commit record fsynced → commit bit set in `pg_xact` → all versions atomically
  visible to later snapshots.
- `ROLLBACK`: cheap — just mark the XID aborted; dead versions swept by VACUUM later.
- Statement failure inside a txn aborts the whole txn in Postgres (must ROLLBACK or use
  SAVEPOINTs) — unlike MySQL which by default aborts only the statement.

### 4. Visualization (ASCII)
```
BEGIN ── stmt1 ── stmt2 ── COMMIT
                    │         └─▶ WAL: [x=1][y=2][COMMIT] → fsync → visible atomically
                    └ error? txn now ABORTED: every stmt fails until ROLLBACK
row versions:  old row [xmin=90, xmax=105]   ← deleted by txn 105
               new row [xmin=105, xmax=∅ ]   ← created by txn 105
reader with snapshot taken before 105 committed → sees old row
reader after                                  → sees new row
```

### 5. Real Production Example
A checkout at **Amazon/Stripe** scale: reserve inventory, create order, record payment intent —
one transaction against one DB, *but* the external card-network call happens OUTSIDE the
transaction (never hold row locks across an HTTP call — the classic incident is a payment
provider slowdown turning into a database lock pileup). Pattern: txn1 = write `pending` +
outbox row → call provider → txn2 = finalize.

### 6. Common Interview Questions
- "What happens if a transaction fails halfway?" (nothing persists; how: WAL/MVCC)
- "Why are long transactions bad?" (hold locks; block VACUUM → bloat; snapshot forces keeping
  dead versions; replication conflicts)
- "How do you call an external API 'inside' a transaction?" (you don't — outbox pattern)
- "Difference between ROLLBACK and crash recovery?" (same end state; rollback is explicit mark,
  recovery replays WAL and discards uncommitted)

### 7. Common Mistakes
- Transactions spanning user interaction ("BEGIN, show form, COMMIT on submit") — lock disaster.
- No retry logic: treating 40001/deadlock as a bug instead of a signal to retry.
- Doing reads that don't need transactional consistency inside the write transaction, inflating
  its duration.
- Assuming autocommit batches are atomic — 1,000 separate INSERTs without BEGIN are 1,000 transactions.

### 8. Best Practices
- Wrap multi-statement invariants in explicit transactions; keep them under ~100ms.
- Acquire locks in a **consistent order** across code paths (deadlock prevention — Module 6).
- Retry on `40001`/`40P01` with jittered backoff, bounded attempts, idempotent statements.
- Use the outbox pattern for DB-write + message-publish atomicity.

### 9. Coding Questions
1. Write the inventory-safe checkout below and explain why the `CHECK`/`WHERE` guard prevents
   overselling even under concurrency.
2. Implement retry-on-serialization-failure pseudocode around a transaction block.

### 10. SQL Examples
```sql
-- Oversell-proof decrement (atomic check-and-set in one statement)
BEGIN;
UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = 77 AND quantity >= 1;
-- rowcount = 0 → out of stock → ROLLBACK and tell the user
INSERT INTO orders (user_id, product_id) VALUES (42, 77);
COMMIT;

-- Savepoints: tolerate a failing optional step
BEGIN;
INSERT INTO orders ...;
SAVEPOINT coupon;
INSERT INTO coupon_redemptions ...;   -- may violate "already used" unique
-- on error: ROLLBACK TO SAVEPOINT coupon;  (order survives)
COMMIT;
```

### 11. Optimization Techniques
- Combine per-row round trips into set-based statements (one UPDATE with a join beats N updates).
- Move derivable work (counters, projections) out of the critical transaction to async consumers
  when the invariant allows.
- Monitor long transactions: `SELECT * FROM pg_stat_activity WHERE xact_start < now() - interval '1 min';`

### 12. Follow-up Questions
- "Two replicas of your service run this transaction concurrently — walk me through the race."
  (leads into isolation levels → Module 6)
- "How does this transaction behave at READ COMMITTED vs SERIALIZABLE?"
- "What's in the WAL for this transaction, and when is it safe to tell the user 'saved'?"

---

# Module 1 — Practice Problems

## Easy (5)
1. List the ACID properties and, for each, the single Postgres mechanism that implements it.
2. A table stores `tags` as a comma-separated string. Which normal form is violated, and what
   two problems will you hit? Rewrite the schema.
3. State the difference between a primary key and a unique constraint regarding NULLs, count per
   table, and FK targeting.
4. Your read replica shows an order 800ms after the primary commits it. Name the consistency
   model the user experiences and one fix for "user doesn't see their own order."
5. Classify each as OLTP or OLAP and pick row-store or column-store: (a) fetch cart by user_id,
   (b) revenue by country by month for 3 years, (c) update shipment status, (d) funnel analysis
   over 2B events.

## Medium (5)
6. Design the consistency policy for a food-delivery app: order placement, driver GPS location,
   restaurant menu, payment capture. For each: ACID or BASE, and the user-visible anomaly you accept.
7. Cassandra RF=3. For (W=1,R=1), (W=2,R=2), (W=3,R=1): state whether reads are strongly
   consistent, and what happens to writes when one replica is down.
8. A parent table `merchants` (10k rows) and child `payments` (2B rows, FK `merchant_id`,
   no index on it). Deleting one merchant takes 40 minutes and blocks writes. Explain exactly
   why and give two fixes.
9. You must add `orders.user_email` (denormalized from `users`) to kill a hot join. Specify the
   sync mechanism, the failure mode, and the reconciliation query.
10. Your API does: BEGIN → INSERT payment → call card network (p99 = 8s) → UPDATE status →
    COMMIT. Production shows lock waits and connection exhaustion. Redesign it.

## Hard (5)
11. Design read-your-own-writes for a Postgres primary with 5 async replicas behind a load
    balancer, without pinning all traffic to the primary. (LSN token flow: capture on write,
    compare on replica, fallback route.)
12. Prove with a two-transaction interleaving that "check balance, then insert withdrawal in a
    second statement" oversells at READ COMMITTED, then give three distinct fixes
    (atomic UPDATE guard, `SELECT ... FOR UPDATE`, SERIALIZABLE + retry) with their costs.
13. You're sharding `orders` by `user_id` across 8 Postgres nodes. Enumerate everything that
    breaks: FKs to shared tables, unique constraints on `order_number`, multi-user reports,
    transactions spanning users — and give the standard mitigation for each.
14. A migration from auto-increment bigint to UUIDv4 PKs cut insert throughput 5x on MySQL but
    only ~20% on Postgres. Explain the asymmetry (clustered PK page splits vs heap+index bloat)
    and the fix that keeps global uniqueness (UUIDv7/ULID).
15. Sketch a transactional outbox end-to-end: DDL for the outbox table, the write transaction,
    the relay (poll vs logical decoding), delivery guarantees, and how consumers deduplicate.

---

*Next: [Module 2 — SQL Core](module-02-sql-core.md)*

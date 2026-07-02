# MODULE 11 — Production Debugging

> The on-call module. Senior interviews end with "the database is slow / down — go." This
> module is organized as incident runbooks: symptom → triage → root causes → fixes → prevention.
> Most mechanisms were built in Modules 4–7; here they become diagnosis flows.

Chapters:
11.1 The Universal Triage Method
11.2 Slow Queries & Missing Indexes
11.3 Connection Pool Exhaustion
11.4 Deadlocks & Lock Contention
11.5 Replication Lag
11.6 Memory Issues
11.7 Large Tables & Bloat
11.8 Pagination Problems (deep-page incidents)

---

## Chapter 11.1 — The Universal Triage Method

### 1. Why Interviewers Ask This
Incident questions grade your *process* under ambiguity. A senior answer runs a fixed loop:
scope → recent change → observe → hypothesize → verify → mitigate → root-cause → prevent.

### 2. Core Concept — The First 5 Minutes
1. **Scope**: everything slow, or one query/endpoint/tenant? Reads, writes, or both?
   Primary or replicas? Since when?
2. **What changed**: deploys, migrations, traffic spikes, data growth crossing a threshold,
   config, infra events (failover, vacuum, backup).
3. **Look at the database's own account of itself** (the queries below — memorize them):

```sql
-- Who is doing what right now
SELECT pid, state, wait_event_type, wait_event,
       now() - query_start AS runtime, left(query, 80)
FROM pg_stat_activity
WHERE state <> 'idle' ORDER BY query_start;

-- Blocked ⇄ blocker chains
SELECT pid, pg_blocking_pids(pid) AS blocked_by, left(query, 60)
FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;

-- Cumulative top offenders
SELECT calls, round(mean_exec_time,1) AS mean_ms,
       round(total_exec_time)::bigint AS total_ms, left(query, 80)
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;

-- Long transactions (the silent killer behind half of incidents)
SELECT pid, now() - xact_start AS age, state, left(query,60)
FROM pg_stat_activity WHERE xact_start IS NOT NULL ORDER BY xact_start LIMIT 5;
```

4. **Classify**: CPU-bound (plans/misestimates), I/O-bound (cache misses, scans, checkpoints),
   lock-bound (waits, not resource usage), or connection-bound (saturation ahead of the DB).
   `wait_event_type` tells you: `Lock` = lock-bound, `IO` = I/O, CPU pegged + no waits = plans.
5. **Mitigate before root-causing** when bleeding: kill the offending query
   (`pg_terminate_backend`), roll back the deploy, shed load, add the emergency index
   CONCURRENTLY. Say the mitigation/root-cause distinction out loud — it's senior signal.

### 3–12. (Method notes)
- **Visualization**:

```
symptom ──▶ scope ──▶ recent change ──▶ pg_stat_activity/statements
                                          │
        ┌────────────┬────────────┬───────┴──────┬─────────────┐
     CPU-bound    I/O-bound    lock-bound   connection-bound  external
     (plans,      (scans,      (waits,      (pool/max_conn)   (disk, noisy
      stats)      cache,        long txns)                     neighbor, failover)
                  checkpoint)
```

- **Interview traps**: jumping to "add an index" before scoping; restarting the DB as step 1
  (destroys evidence, drops cache — often makes it worse); not asking "what changed."
- **Best practice**: keep dashboards for the four classes (CPU/IO/locks/connections) + the
  four queries above as saved runbook snippets.

---

## Chapter 11.2 — Slow Queries & Missing Indexes

### 1. Why Interviewers Ask This
The most common incident. The interview version hands you symptoms ("this endpoint went from
50ms to 8s over a month") and expects a clean diagnosis chain.

### 2. Core Concept — Diagnosis Chain
1. Identify the query: APM trace / `pg_stat_statements` (sort by `total_exec_time` for
   aggregate pain, `mean_exec_time` for user pain) / `auto_explain` logs.
2. `EXPLAIN (ANALYZE, BUFFERS)` with production parameters (Module 5.1).
3. Classify the cause — the frequency-ordered list:
   - **Missing/wrong index** (Seq Scan or Filter-heavy index scan; Rows Removed by Filter huge)
   - **Stale stats / misestimates** (est vs actual >10x; after bulk loads)
   - **Non-sargable predicate** (function on column, type cast, leading wildcard — Module 4.6)
   - **Plan flip** (prepared-statement generic plan; stats change; parameter skew)
   - **Data growth crossing thresholds** (the slow-over-a-month case: working set left RAM,
     or crossover from index to seq scan)
   - **Lock waits masquerading as slowness** (check wait_event first!)
   - **N+1 at the app layer** (fast queries, slow requests — Module 5.7)
4. Fix (index CONCURRENTLY / ANALYZE / rewrite / plan_cache_mode), verify with before/after
   plans, then prevent (slow-query alerting, index review in migrations, load tests with
   production-scale data).

### 3. Internal Working — "Slow over a month" mechanics
Nothing changed except data: (a) the hot working set outgrew `shared_buffers`+page cache →
cache hit ratio slid → I/O-bound; (b) planner crossover — at 2% selectivity index scan won, at
9% it flips to seq scan (or should, but stats lag); (c) index bloat grew descent depth/cache
footprint. This gradual class is *the* senior probe — name all three.

### 4. Visualization
```
p95 latency
  ▲                                          ╭── incident
  │                          ╭───────────────╯
  │        ╭─────────────────╯   ← silent degradation: working set > RAM,
  │────────╯                        selectivity drift, bloat
  └──────────────────────────────▶ time (weeks)
Checks: cache hit ratio trend │ rows in table trend │ plan diff old vs new
```

### 5. Real Production Example
`WHERE status='pending'` job poller: brilliant at launch (1k rows), death at 400M rows with
99.9% terminal states — seq scan every 5 seconds. Fix: partial index (Module 4.4), instant.
Second: nightly ETL bulk-loads a table; every morning dashboards are slow until autoanalyze
catches up → add explicit `ANALYZE` to the ETL. Both are interview scripts, verbatim.

### 6–12. (Compressed)
- **Questions**: "walk me through debugging a slow query" (recite the chain); "it's slow only
  in production" (data volume, parameters, cache, stats — never 'works on my machine');
  "it's slow only sometimes" (plan flips, lock waits, checkpoints, noisy batch jobs —
  correlate timestamps).
- **Mistakes**: indexing without reading the plan; testing on empty staging; measuring the
  second (cached) run only; "fixing" with `enable_seqscan=off`.
- **Best practices**: `pg_stat_statements` + `auto_explain` always on; every schema migration
  PR includes EXPLAIN of affected hot queries; production-scale fixture data in perf CI.
- **Follow-ups**: "index exists but unused" (Module 4.6 catalog — run it); "how do you find
  *missing* indexes proactively?" (top statements with high `shared_blks_read`/call + seq_scan
  counters in `pg_stat_user_tables`).

---

## Chapter 11.3 — Connection Pool Exhaustion

### 1. Why Interviewers Ask This
Top-3 real outage class ("FATAL: remaining connection slots are reserved" or app-side pool
timeouts) with a counterintuitive fix (fewer connections, not more) — perfect senior filter.

### 2. Core Concept — Triage
Symptoms: app errors acquiring connections; DB *itself* often healthy and idle-ish.
First split: **pool exhausted because queries got slow** (root cause = Ch 11.2/11.4: same
throughput × longer hold time = more concurrent conns, Little's law) vs **pool exhausted
because demand rose** (deploy doubled pods, traffic spike, connection leak).

```sql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
-- many 'idle in transaction'  → app leaks transactions (missing commit/close in a code path)
-- many 'active' same query    → that query got slow → fix the query, pool recovers
-- many 'idle'                 → fleet over-provisioned connections → pooler/sizing
```

Fix ladder: kill leakers (`pg_terminate_backend`) → `idle_in_transaction_session_timeout` →
transaction-mode PgBouncer (Module 7.4) → right-size app pools fleet-wide → fix the slow query
or leak that started it.

### 3. Internal Working
The death spiral interviewers want articulated: one slow query → requests stack → each holds a
connection → pool saturates → *healthy* queries queue for connections → timeouts → retries →
more load → total outage from one bad query. Connection pressure is a **symptom amplifier**;
always ask what consumed the time-slices first.

### 4. Visualization
```
slow query (500ms→8s)                         Little's law:
   │ same 1000 RPS                            busy_conns = QPS × latency
   ▼                                          1000 × 0.05s = 50   (fine)
conns held 16x longer ──▶ pool full ──▶       1000 × 0.8s  = 800  (dead: pool=100)
timeouts ──▶ retries ──▶ MORE load ──▶ ✖
mitigation order: kill slow query → shed load → THEN tune pools
```

### 5–12. (Compressed)
- **Production example**: deploy adds a missing `await`/`close()` — every request leaks one
  `idle in transaction` conn; 20 minutes later, full outage. The `state` census finds it in
  one query.
- **Questions**: "app says pool timeout, DB looks idle — go"; "should we raise
  max_connections?" (almost never the fix — Module 7.4 throughput curve); "how do serverless
  functions make this worse?"
- **Mistakes**: raising limits everywhere (moves the cliff, adds thrash); restarting the app
  (clears symptom, loses the leak evidence); no per-service connection budget.
- **Prevention**: pooler in transaction mode, statement/idle-txn timeouts, per-service budgets
  summing under capacity, leak detection in the driver (max lifetime, abandoned tracking),
  pool-wait metrics + alerts.
- **Follow-ups**: "PgBouncer added — what breaks?" (session state — Module 7.4); "connection
  storms after failover?" (thundering reconnect — jittered backoff, connection warm-up rate
  limits).

---

## Chapter 11.4 — Deadlocks & Lock Contention

### 1. Why Interviewers Ask This
Distinguishes "knows locks exist" from "can read a lock graph at 3am." Also covers the sneaky
class: everything slow, CPU idle — pure waiting.

### 2. Core Concept — Triage
Symptoms split: **deadlocks** (errors 40P01 in logs, DETAIL shows both queries) vs **lock
contention** (no errors, just latency; `wait_event_type='Lock'` in pg_stat_activity).

Contention flow: find blocked pids → `pg_blocking_pids()` → walk to the **root blocker** →
what is it? (long transaction? idle in transaction? DDL waiting? batch job?) → kill or wait →
then design fix (shorter txns, lock ordering, SKIP LOCKED, hot-row sharding — Module 6).

Deadlock flow: collect log DETAILs → reconstruct the two access orders → impose one global
order (or single-statement atomicity) → add retries.

```sql
-- The lock-chain one-liner during an incident
SELECT a.pid, a.state, now()-a.xact_start AS txn_age,
       pg_blocking_pids(a.pid) AS blocked_by, left(a.query, 70)
FROM pg_stat_activity a
WHERE a.pid IN (SELECT unnest(pg_blocking_pids(pid)) FROM pg_stat_activity)
   OR cardinality(pg_blocking_pids(a.pid)) > 0;
```

### 3. Internal Working
The pileup shapes (from Module 6.3, now as diagnosis): hot-row convoy (all waits on one tuple —
counters, singleton config rows), DDL barrier (ACCESS EXCLUSIVE queued behind a long read,
everything queues behind it), FK contention (child inserts vs parent updates), batch-vs-OLTP
ordering deadlocks (nightly spikes). Each has a signature in the chain query: one root pid with
dozens of waiters (convoy), an `ALTER TABLE` mid-chain (DDL), etc.

### 4. Visualization
```
lock chain:  [root blocker: idle in txn, 42min]
                ▲              ▲
        [UPDATE waits]   [ALTER TABLE waits]
                                 ▲
                     [200 SELECTs wait behind DDL]  ← "the site is down"
read the tree root-first: kill/finish the ROOT, the tree drains itself
```

### 5–12. (Compressed)
- **Production example**: migrations at peak: `ALTER TABLE` queued behind an analytics query →
  full brownout (Module 6.3's story, now from the debugging side). Detection time is the metric:
  with `log_lock_waits=on` and the chain query saved, minutes; without, an hour of confusion.
- **Questions**: "DB slow, CPU 10%, disks idle — first check?" (wait events / lock chains);
  "recurring 40P01 every night at 2am" (batch ordering — reconstruct from log DETAIL);
  "how do you kill safely?" (`pg_cancel_backend` first (query), `pg_terminate_backend` if
  needed (connection); know rollback cost of killing a huge write txn).
- **Mistakes**: killing waiters instead of the root; DDL retried in a tight loop re-poisoning
  the queue; treating deadlock errors as data corruption (they're not — one txn rolled back
  cleanly).
- **Prevention**: `log_lock_waits=on`, `lock_timeout` for DDL, `deadlock` alert on log parsing,
  lock-ordering conventions, idle-in-transaction timeout (again — it prevents half this
  chapter).
- **Follow-ups**: "lock contention with no long transactions at all?" (pure hot-row throughput
  ceiling — serialize through a queue or shard the row); "how does this look in MySQL?"
  (`SHOW ENGINE INNODB STATUS`, `data_locks`; gap-lock deadlocks class Postgres lacks).

---

## Chapter 11.5 — Replication Lag

### 1. Why Interviewers Ask This
Lag incidents blend infrastructure and application: stale reads, backlogged failover risk, and
cascading cache bugs. Tests whether you know causes *and* the consumer-side contract.

### 2. Core Concept — Triage
Measure first (Module 7.1 queries): is lag growing linearly (replica can't keep up), spiky
(bursts, vacuum storms, big transactions), or plateaued (replay blocked)?

Cause catalog:
- **Write burst / bulk load** on primary (replay is more serial than primary's parallel apply).
- **One giant transaction** (100M-row UPDATE arrives as a wall of WAL; replicas stall then jump).
- **Replica query conflicts**: long replica reads force replay to wait
  (`max_standby_streaming_delay`) — lag *caused by the readers themselves*.
- **Replica hardware/IO inferior** to primary; network throughput ceiling.
- **Vacuum/checkpoint storms** generating WAL floods (full-page writes after checkpoint).

Fixes map 1:1: chunk big writes; move long reads to a dedicated replica (or
`hot_standby_feedback` with its bloat tax); scale replica IO; increase WAL bandwidth;
and on the app side — **staleness contracts** (Module 7.1: pin-after-write, LSN tokens) so
lag degrades gracefully instead of correctness-breaking.

### 3–4. Internal Working & Visualization
```
lag_bytes = pg_current_wal_lsn(primary) − replay_lsn(replica)
growth patterns:
  /````/````/  spiky: batch jobs → chunk them, schedule off-peak
  ────────/    step: one giant txn → break it up
  ↗↗↗↗↗↗↗↗     linear: replica underpowered / replay conflict-throttled → fix capacity or
                        reader placement
replay blocked check: SELECT * FROM pg_stat_activity ON REPLICA where backend blocks recovery
                      (conflict with recovery messages in logs)
```

### 5–12. (Compressed)
- **Production example**: nightly ETL UPDATE of 80M rows → 20 min replica lag → users see
  yesterday's balances → support flood. Fixes: chunked ETL + LSN-gated reads for
  balance-bearing endpoints + lag-based replica ejection from the read LB (serve primary when
  lag > threshold).
- **Questions**: "users intermittently see old data" (lag + read routing — trace one request);
  "replica lag alarms during vacuums — why?" (WAL volume from cleanup + full-page writes);
  "failover with 30s lag — what's lost?" (async: those 30s of acked writes — RPO conversation,
  Module 7.1).
- **Mistakes**: alerting only on seconds-lag (idle systems show huge time-lag with zero
  byte-lag — alert on both); hot_standby_feedback everywhere (primary bloat); assuming logical
  replication has the same profile (it's row-based, single-apply-worker bottlenecks differ).
- **Prevention**: chunked batch writes as policy; lag SLO per replica class; read-router with
  staleness budget; capacity-match replicas to primary.
- **Follow-ups**: "design the read layer so lag can never cause a correctness bug" (LSN tokens
  end-to-end — be able to draw it); "what's different in Aurora?" (shared storage: ~ms lag,
  different failure modes).

---

## Chapter 11.6 — Memory Issues

### 1. Why Interviewers Ask This
OOM kills and memory pressure are opaque until you know the Postgres memory model — a great
test of systems depth.

### 2. Core Concept — The Memory Map
- **shared_buffers** (global, fixed): page cache (~25% RAM).
- **work_mem** (per sort/hash **node**, per connection!): the multiplication bomb — 200
  connections × 4 nodes × 64MB = 51GB *potential*.
- **maintenance_work_mem** (vacuum, index builds), **wal_buffers**, per-backend overhead
  (~5–10MB × connections), OS page cache (the other half of your RAM — `effective_cache_size`
  tells the planner about it).

Incident classes:
- **OOM-killed backend / postmaster** (Linux OOM killer → crash-restart of the whole cluster):
  usually work_mem × concurrency, a runaway hash aggregate misestimate (planner thought 1k
  groups, got 100M), or too many connections.
- **Slow due to cache misses** (not OOM): working set outgrew RAM — hit ratio slide (11.2).
- **Temp-file explosions** (disk, but memory-caused): spills from undersized work_mem —
  the *safe* failure mode; don't "fix" it into the unsafe one by raising work_mem globally.

```sql
-- Cache effectiveness
SELECT sum(blks_hit)*100.0/nullif(sum(blks_hit)+sum(blks_read),0) AS hit_pct
FROM pg_stat_database;
-- Spill volume per query (find the work_mem candidates, fix locally)
SELECT left(query,60), temp_blks_written FROM pg_stat_statements
ORDER BY temp_blks_written DESC LIMIT 5;
```

### 3–4. Internal Working & Visualization
```
RAM (64GB):
[ shared_buffers 16GB ][ OS page cache ~30GB ][ backends: 200 × 10MB = 2GB ]
[ work_mem exposure: 200 conns × N nodes × work_mem  ← the UNBOUNDED slice ]
OOM story: misestimate → HashAgg plans "1k groups" → builds 100M-group table in RAM
           → grows past work_mem *estimate-based* decisions → OOM killer → cluster restart
(PG13+ hash aggs can spill; misestimates still hurt)
```

### 5–12. (Compressed)
- **Production example**: analytics query with a misestimated GROUP BY OOM-kills the primary at
  month-end, every month. Chain: auto_explain catches it → estimate fix (extended stats) +
  move to replica + session-local work_mem cap. The "monthly recurring OOM" framing is a
  common interview scenario.
- **Questions**: "walk the Postgres memory model"; "OOM killer took the DB — how do you find
  the culprit?" (kernel log timestamp → pg_stat_statements/auto_explain around it → plan);
  "why not raise work_mem globally?" (the multiplication argument — say the arithmetic).
- **Mistakes**: shared_buffers at 80% of RAM (starves OS cache + work areas);
  overcommit-enabled kernels letting the OOM killer choose Postgres (set `vm.overcommit_memory=2`,
  adjust oom_score for postmaster); confusing spill (safe, slow) with OOM (fatal).
- **Prevention**: connection caps via pooler (bounds the multiplier), per-role/session work_mem
  for heavy jobs, memory dashboards split by class, statement_timeout as a runaway bound.
- **Follow-ups**: "same question for MySQL" (innodb_buffer_pool + per-thread buffers — same
  multiplication trap); "how does work_mem interact with parallel query?" (per worker! another
  multiplier).

---

## Chapter 11.7 — Large Tables & Bloat

### 1. Why Interviewers Ask This
"The table is 3TB and everything about it is slow" — tests VACUUM understanding (Module 6.2),
partitioning judgment (7.2), and safe-operations discipline.

### 2. Core Concept — The Big-Table Playbook
Diagnose first: is it *bloat* (dead space) or *legitimate size*?

```sql
SELECT relname, n_live_tup, n_dead_tup,
       round(n_dead_tup*100.0/nullif(n_live_tup+n_dead_tup,0),1) AS dead_pct,
       last_autovacuum
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;
-- pgstattuple for precise dead-space %, pg_relation_size for the raw truth
```

- **Bloat** (dead_pct high, autovacuum behind): find the blocker (long transactions!
  replication slots! prepared transactions!) → unblock → tune autovacuum
  (scale_factor per table, cost limits) → reclaim with `pg_repack` (online) — never casual
  `VACUUM FULL` (exclusive lock).
- **Legitimately huge**: partition (7.2) for pruning + retention; archive cold data; split
  hot/cold columns; move blobs to object storage.
- **Operations on big tables have their own physics**: every ALTER/backfill/index-build must be
  chunked/CONCURRENTLY/NOT VALID+VALIDATE; a naive `UPDATE SET flag=true` on 2B rows =
  2B new row versions = self-inflicted bloat bomb + replication flood.

### 3–4. Internal Working & Visualization
```
why the 2B-row UPDATE is a disaster:
UPDATE all rows → 2B new versions (MVCC) → table doubles on disk
→ WAL flood → replicas lag hours → autovacuum weeks of debt → indexes bloat too
correct: batch 10k-100k rows per txn, sleep between, vacuum checkpoints, or
         CTAS-rebuild + swap when touching >30-50% of the table
autovacuum starvation loop: big table × default scale_factor(0.2) = vacuums only
every 400M dead rows → each run takes days → always behind → lower per-table thresholds
```

### 5–12. (Compressed)
- **Production example**: "add a column with default + backfill" on a 1TB table done naively →
  weekend outage; done right → invisible (PG11+ fast default, then chunked backfill of derived
  values, then NOT NULL via CHECK NOT VALID → VALIDATE). This migration question is asked at
  every senior loop in some form.
- **Questions**: "count of dead tuples keeps growing despite autovacuum running — why?"
  (long txn / stale replication slot pinning the horizon — find with the Module 6.2 queries);
  "delete 90% of a huge table" (don't DELETE: partition-drop, or CTAS survivors + swap);
  "why is VACUUM FULL dangerous and what replaces it?" (pg_repack).
- **Mistakes**: DELETE for retention on unpartitioned tables (bloat instead of space);
  ignoring index bloat (REINDEX CONCURRENTLY exists); disabling autovacuum on the busiest table.
- **Prevention**: partition event-like tables at design time; per-table autovacuum tuning as
  tables cross ~50GB; replication-slot and long-txn monitoring; migration playbooks with
  chunking as default.
- **Follow-ups**: "TOAST — what is it and when does it bite?" (out-of-line storage for big
  values; update patterns rewrite whole toasted values); "wraparound emergency — walk the
  runbook" (age monitoring → aggressive vacuum → single-user mode worst case).

---

## Chapter 11.8 — Pagination Problems (deep-page incidents)

### 1. Why Interviewers Ask This
A compact, real incident class that ties together Modules 5.5, 4.3, and API design — often used
as a closing practical question.

### 2. Core Concept — The Incident Catalog
- **Deep OFFSET scans**: crawler/export hits `?page=50000` → each request scans-and-discards
  1M rows → DB saturated by a single client. Detect: pg_stat_statements shows the same query
  shape with huge `rows` scanned vs tiny returned; fix: keyset pagination + hard offset caps +
  rate-limit/redirect exports to snapshots (Module 5.5).
- **Unstable pages under writes**: users see duplicated/skipped items during infinite scroll
  (rows shifting across page boundaries). Fix: keyset with unique tiebreaker (stable anchors).
- **COUNT-per-page**: every page render runs `count(*)` over the filtered set → half the
  endpoint's cost is the total nobody reads. Fix: has_more (k+1 fetch), estimates, or cached
  counts (Module 5.6).
- **Missing composite index for the sort**: pagination "works" but each page sorts the world —
  `(filter_cols, sort_col, id)` index makes pages O(page size).
- **Cursor drift on filtered lists**: cursor encodes position but filters changed between
  requests → wrong slices. Fix: encode filters (or their hash) in the cursor; reject on
  mismatch.

### 3–4. Internal Working & Visualization
```
OFFSET-depth cost:  page1 ▏ page100 ▍ page1000 █ page10000 ██████████  (O(offset))
keyset:             page1 ▏ page10000 ▏                                 (O(k))
incident signature in pg_stat_statements:
  query LIKE '%OFFSET%'  calls=40k/hr  mean=900ms  rows=20  shared_blks_read=huge
  → one API client paging to infinity
```

### 5–12. (Compressed)
- **Production example**: partner integration syncs the catalog nightly via
  `?page=N` to page 80,000; DB CPU pegs for 3 hours nightly. Fixes shipped: cursor API +
  `updated_since` incremental sync + nightly export file — and a max-offset guard (HTTP 400
  past page 500) to stop the bleeding immediately. The "stop the bleeding vs fix the API"
  sequencing is what interviewers grade.
- **Questions**: "the DB dies every night at 2am; here's pg_stat_statements — find it"
  (the OFFSET signature); "user reports seeing the same item on two consecutive pages"
  (instability under writes — keyset + tiebreaker); "how would you paginate a 100M-row export
  API?" (cursor / snapshot-to-object-storage / server-side cursor streaming).
- **Mistakes**: caching page results as a fix (position-keyed cache invalidates on every
  write); adding replicas to absorb OFFSET abuse (scales the waste); switching to keyset
  without backfilling the supporting index.
- **Prevention**: keyset-by-default in the API framework; offset caps + pagination-abuse rate
  limits; `updated_since` incremental endpoints for sync use-cases; page-depth metrics.
- **Follow-ups**: "cursor pagination across shards?" (per-shard cursors merged — Module 5.5/7.3);
  "how does Stripe's API do it?" (`starting_after`/`ending_before` object-id cursors — cite it).

---

# Module 11 — Practice Problems

## Easy (5)
1. Write the four triage queries (activity, blockers, top statements, long transactions) from
   memory and state what each rules in or out.
2. `FATAL: remaining connection slots are reserved` — list the diagnosis steps in order and the
   fix ladder.
3. pg_stat_user_tables shows n_dead_tup=800M and last_autovacuum=3 days ago on a hot table.
   Give the three most likely blockers and the query to find each.
4. An endpoint is slow only for one huge tenant. Name three mechanisms that make identical
   queries tenant-dependent and the fix for each (skew/plans, missing composite index, hot
   partition).
5. Replica time-lag alarm fires at 4am daily for 20 minutes. What do you correlate it with, and
   what are the two standard fixes?

## Medium (5)
6. Given pg_stat_statements output (queries with calls, mean, total, temp_blks, blks_read),
   triage which of five listed statements you'd attack first and why — construct the reasoning
   with total-time × user-impact.
7. The site is down; pg_stat_activity shows 300 sessions waiting, all blocked (transitively) on
   one `idle in transaction` pid from the admin VPN. Write the exact commands to confirm, kill,
   and the two config changes that prevent recurrence.
8. Design the "safe migration" checklist for a 2TB orders table: add column with default,
   backfill computed values, add NOT NULL, add an index, add an FK — each step with its lock
   profile and chunking strategy.
9. Every deploy causes 5 minutes of DB latency. List four mechanisms (cold app pools ×
   connection storm, prepared-statement re-plan, cache eviction from restarted services, ORM
   migrations taking locks) and how to confirm each from metrics.
10. Nightly OOM kill during a reporting query. Reconstruct the full chain from kernel log to
    query plan to root cause (HashAgg misestimate), and write the three-layer fix (stats,
    session work_mem, workload placement).

## Hard (5)
11. Compose the full incident: at 09:00 a deploy ships a new filter that makes a hot query
    non-sargable; by 09:20 the pool is exhausted; by 09:25 retries have tripled load and the
    replica lags 10 minutes. Write the minute-by-minute response: detection signals, mitigation
    order (and why that order), root-cause confirmation, and the three prevention items.
12. You inherit a 6TB single-table Postgres with no partitioning, 40% bloat, autovacuum always
    behind, quarterly wraparound scares, and 5s p99. Produce the six-month stabilization plan
    with dependency ordering: vacuum unblocking, repack sequencing, partition migration
    (dual-write design), index audit, and the risk register for each step.
13. Build the observability stack for databases from scratch: exact metrics per incident class
    (11.2–11.8), log lines to parse (lock waits, deadlocks, autovacuum, checkpoints, temp
    files), auto_explain config, alert thresholds with rationale, and the runbook index. Argue
    what pages a human at 3am vs what waits for morning.
14. A multi-tenant SaaS suffers noisy-neighbor incidents: one tenant's analytics queries
    starve everyone. Design the isolation ladder — statement_timeout per role, per-tenant
    connection budgets via pooler, workload routing to replicas, tenant-partitioned tables,
    and finally tenant sharding — with the trigger criteria for escalating each rung.
15. Post-mortem synthesis: pick any three incidents from this module and write the shared root
    cause taxonomy (long transactions, unbounded work, missing backpressure) — then propose the
    three platform-level invariants (timeouts everywhere, chunk-by-default batch framework,
    staleness-budgeted read routing) and prove each incident is prevented or bounded by them.

---

## You're Done — The Final Checklist

Before your interview loop, verify you can do these cold:

- [ ] Explain WAL → commit → crash recovery in 60 seconds (M1)
- [ ] Recite the clause evaluation order and the NOT IN + NULL trap (M2)
- [ ] Whiteboard all three join algorithms with when-each-wins (M3)
- [ ] Design a composite index from a query using ESR and defend column order (M4)
- [ ] Read an EXPLAIN ANALYZE bottom-up: estimates, loops, spills (M5)
- [ ] Produce lost-update and write-skew interleavings + all fixes (M6)
- [ ] Walk the scaling ladder: cache → replicas → partition → shard, with what breaks (M7)
- [ ] Compare B+Tree vs LSM and place all six databases on the comparison table (M8)
- [ ] Design hotel booking with race-proof no-double-booking, three ways (M9)
- [ ] Solve: Nth salary, dedup delete, streaks, sessionization, top-K per group (M10)
- [ ] Run the universal triage loop on any "DB is slow" prompt (M11)

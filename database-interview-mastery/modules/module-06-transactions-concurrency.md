# MODULE 6 — Transactions & Concurrency

> The deepest technical module in senior loops. Isolation levels + MVCC + locking scenarios are
> where FAANG interviewers separate senior from staff. Every anomaly below comes with the
> two-transaction interleaving you must be able to write on a whiteboard.

Chapters:
6.1 Read Anomalies & Isolation Levels (Dirty Reads, Non-Repeatable Reads, Phantoms, Lost Updates)
6.2 MVCC — How Postgres Implements Isolation
6.3 Locks — Row, Table, Advisory; FOR UPDATE / SKIP LOCKED
6.4 Deadlocks
6.5 Optimistic vs Pessimistic Locking
6.6 SERIALIZABLE & Write Skew

---

## Chapter 6.1 — Read Anomalies & Isolation Levels

### 1. Why Interviewers Ask This
The single most reliable senior-depth probe. Definitions are entry stakes; the real test is
(a) producing the interleaving that causes each anomaly, (b) knowing which level stops it,
(c) knowing the Postgres-specific deviations from the SQL standard.

### 2. Core Concept
The anomalies:
- **Dirty read**: read another transaction's *uncommitted* write. (Postgres never allows this —
  even READ UNCOMMITTED behaves as READ COMMITTED.)
- **Non-repeatable read**: read the same row twice in one txn, get different values (someone
  committed between reads).
- **Phantom read**: re-run the same *predicate* query, get different *row sets* (someone
  inserted/deleted matching rows).
- **Lost update**: two txns read-modify-write the same row; the second write silently
  overwrites the first (`balance = balance_read + x` racing).
- **Write skew**: two txns read overlapping data, write *disjoint* rows, and jointly violate an
  invariant neither violates alone (see 6.6 — the staff-level anomaly).

The levels (SQL standard × what Postgres actually does):

| Level | Dirty | Non-repeat | Phantom | Lost update | Write skew |
|---|---|---|---|---|---|
| READ UNCOMMITTED | std: possible / **PG: never** | possible | possible | possible | possible |
| READ COMMITTED (PG default) | no | possible | possible | **possible** | possible |
| REPEATABLE READ | no | no | std: possible / **PG: no** (snapshot isolation) | **prevented in PG** (first-updater-wins error) | possible |
| SERIALIZABLE | no | no | no | no | no (SSI) |

Postgres specifics worth saying unprompted:
- READ COMMITTED = **new snapshot per statement**; REPEATABLE READ = one snapshot per txn.
- PG's REPEATABLE READ is **snapshot isolation** — stronger than the standard (no phantoms) but
  still allows write skew.
- Under RR/SERIALIZABLE, write conflicts raise `40001 serialization_failure` → **retry loops
  are mandatory**.

### 3. Internal Working
Snapshots decide reads (MVCC — 6.2); write conflicts decide the rest. At READ COMMITTED, an
UPDATE that hits a row changed by a concurrent committed txn **re-reads the latest version,
re-checks the WHERE, and proceeds** (this "requery" behavior is why READ COMMITTED avoids some
naive races but still permits lost updates in read-then-write application patterns). At
REPEATABLE READ, the same situation errors (`could not serialize access due to concurrent
update`) — first-updater-wins.

### 4. Visualization (ASCII)
```
Lost update at READ COMMITTED (app-level read-modify-write):
T1: SELECT balance → 100
T2: SELECT balance → 100
T1: UPDATE balance = 100 - 30  → commits (70)
T2: UPDATE balance = 100 - 50  → commits (50)   ← T1's -30 LOST (should be 20)

Same at REPEATABLE READ:
T2's UPDATE sees the row changed since its snapshot → ERROR 40001 → retry → correct

Non-repeatable read (READ COMMITTED):
T1: SELECT price → 10        T2: UPDATE price=12; COMMIT
T1: SELECT price → 12   (new statement = new snapshot)

Phantom (READ COMMITTED):
T1: SELECT count(*) WHERE dept='eng' → 5     T2: INSERT eng row; COMMIT
T1: same query → 6
```

### 5. Real Production Example
Classic incident: coupon codes with `max_uses=1000` implemented as
`SELECT uses FROM coupons; if uses < 1000: UPDATE coupons SET uses = uses + 1` at READ
COMMITTED. Black Friday concurrency → 1,180 redemptions. Three real fixes (grade yourself on
producing all three): atomic single-statement
`UPDATE coupons SET uses=uses+1 WHERE id=? AND uses<1000` (rowcount tells you if you won),
`SELECT ... FOR UPDATE` around the read, or SERIALIZABLE + retry.

### 6. Common Interview Questions
- "Define all four anomalies with interleavings." (whiteboard-ready)
- "What's Postgres's default level and what anomalies does it allow?" (READ COMMITTED;
  non-repeatable, phantom, lost update, write skew)
- "How does PG's REPEATABLE READ differ from the SQL standard? From MySQL's?" (PG: snapshot
  isolation, no phantoms, first-updater-wins; InnoDB RR: next-key locks block phantom *writes*,
  reads are consistent snapshots, but current-reads (UPDATE/FOR UPDATE) see latest → different
  lost-update behavior)
- "Why not run everything SERIALIZABLE?" (retry rate, throughput, predicate-lock memory —
  though for many workloads it's fine; measured answer wins)

### 7. Common Mistakes
- Reciting the standard table without PG's deviations (that's the differentiating knowledge).
- Believing READ COMMITTED prevents lost updates because "the UPDATE re-checks" — the re-check
  saves single-statement arithmetic (`SET x = x - 1`), not app-level read-then-write.
- No retry logic under RR/SERIALIZABLE.
- Claiming MySQL and Postgres REPEATABLE READ are the same thing.

### 8. Best Practices
- Default READ COMMITTED + **make each critical mutation atomic in one statement** (guarded
  UPDATE with WHERE + rowcount check) — this removes most anomaly exposure without level changes.
- Escalate per-transaction, not globally: `BEGIN ISOLATION LEVEL SERIALIZABLE` for the few
  invariant-critical flows, wrapped in retry.
- Never trust "we tested it" for concurrency — reason from interleavings.

### 9. Coding Questions
1. Write the coupon fix all three ways and state the failure mode of each under 10k concurrent
   redemptions (guarded UPDATE: hot-row lock queue; FOR UPDATE: same + longer hold; SSI: retry storm).
2. Demonstrate PG's READ COMMITTED "requery" semantics: two concurrent
   `UPDATE accounts SET balance = balance - 10 WHERE balance >= 10` on balance=15 — final state
   and why (one succeeds, second re-evaluates WHERE on the new version → matches? 5 >= 10 no →
   0 rows).

### 10. SQL Examples
```sql
-- Atomic guarded mutation (the READ COMMITTED-safe idiom)
UPDATE coupons SET uses = uses + 1
WHERE id = $1 AND uses < max_uses;          -- app checks rowcount = 1

-- Per-transaction escalation with retry (app pseudocode around it)
BEGIN ISOLATION LEVEL SERIALIZABLE;
  SELECT ...; UPDATE ...;
COMMIT;   -- on SQLSTATE 40001: rollback, jittered backoff, retry (bounded)

-- Observe your current level
SHOW transaction_isolation;
```

### 11. Optimization Techniques
- Keep hot-row transactions minimal (acquire the contended lock as LATE as possible in the txn).
- Prefer single-statement atomic ops over FOR UPDATE where possible (shorter lock hold).
- Monitor serialization failure rates; a rising 40001 rate = contention hotspot to redesign
  (shard the row, queue the mutations).

### 12. Follow-up Questions
- "Interviewer: 'increment a view counter' vs 'transfer money' — same isolation needs?" (no:
  counter tolerates approximate/async; transfer needs atomic guarded logic)
- "How would you *test* for lost updates in CI?" (concurrent harness, invariant assertions,
  jepsen-style property checks)
- "What does MySQL's `SELECT ... LOCK IN SHARE MODE`/`FOR SHARE` change in these stories?"

---

## Chapter 6.2 — MVCC: Multi-Version Concurrency Control

### 1. Why Interviewers Ask This
"How can readers not block writers?" is the mechanism question behind every isolation answer.
MVCC also explains VACUUM, bloat, txn-ID wraparound — Postgres operational maturity in one topic.

### 2. Core Concept
MVCC = keep **multiple versions of each row**; give each transaction a **snapshot** deciding
which versions it sees. Readers never block writers, writers never block readers (writers still
block writers on the same row).

Postgres implementation:
- Every tuple has hidden columns: `xmin` (creating txn), `xmax` (deleting/locking txn), ctid.
- **UPDATE = insert new version + set xmax on old**; DELETE = set xmax. Old versions stay in
  the heap until VACUUM removes them.
- **Snapshot** = (xmin horizon, xmax horizon, in-progress txn list). Tuple visible if its
  creator committed before the snapshot and it isn't deleted by a committed-before-snapshot txn.
- **VACUUM** reclaims dead versions (autovacuum runs it); also maintains the visibility map
  (index-only scans!) and **freezes** old tuples to prevent **transaction ID wraparound**
  (32-bit XIDs — the famous operational cliff).

Contrast: MySQL/InnoDB keeps only the newest version in the clustered index and reconstructs old
versions from **undo logs** (rollback segments) — old versions live in undo space, purged by the
purge thread; long-running transactions bloat undo instead of the heap. Oracle likewise (undo).

### 3. Internal Working
- Commit status lives in `pg_xact`; hint bits on tuples cache "known committed/aborted" to skip
  lookups.
- **HOT updates** (Module 4.2): new version on the same page with no indexed-column change →
  no index churn.
- **Long-running transactions are toxic**: they pin the "oldest visible xmin" → VACUUM cannot
  remove any version newer than that horizon → bloat grows table- and cluster-wide, replicas
  conflict, wraparound clock keeps ticking.
- Bloat = dead-version space; monitored via `pg_stat_user_tables.n_dead_tup`, fixed by (auto)
  vacuum; only `VACUUM FULL`/`pg_repack` returns space to the OS.

### 4. Visualization (ASCII)
```
UPDATE row (id=7) by txn 200:
heap:  v1 [xmin=120, xmax=200] "amount=50"   ← old version, now "deleted by 200"
       v2 [xmin=200, xmax=∅  ] "amount=80"   ← new version

snapshot taken before 200 committed → sees v1 (50)
snapshot taken after               → sees v2 (80)
VACUUM (once no snapshot can see v1) → v1 space reclaimed

Long transaction pins the horizon:
oldest snapshot xmin=120 ─────────┐
dead versions from txns 121..900  │ ALL unvacuumable while it lives
                                  ▼ table bloats, scans slow, autovacuum spins
```

### 5. Real Production Example
The canonical Postgres incident: an analyst's psql session left `BEGIN;` open over a weekend →
autovacuum couldn't reclaim anything → hot tables tripled in size, index-only scans died
(visibility map stale), p99 crept up cluster-wide. Detection:
`pg_stat_activity` ordered by `xact_start`. Prevention: `idle_in_transaction_session_timeout`.
Every senior Postgres interview touches some version of this.

### 6. Common Interview Questions
- "How do readers avoid blocking writers in Postgres?" (versions + snapshots)
- "What exactly does UPDATE do at the storage level?" (insert new version + xmax old)
- "What is VACUUM for — all three jobs?" (dead tuples, visibility map, freeze/wraparound)
- "Why are long transactions harmful even if they only read?" (pin xmin horizon)
- "How does InnoDB's MVCC differ?" (undo-log reconstruction vs heap versions; where bloat
  accumulates)

### 7. Common Mistakes
- "MVCC means no locks" — writers still take row locks; DDL takes table locks.
- Thinking DELETE frees space immediately.
- Ignoring wraparound until the `database is not accepting commands` emergency.
- Disabling autovacuum on busy tables "because it causes I/O" (it prevents the larger disaster;
  tune, don't disable).

### 8. Best Practices
- `idle_in_transaction_session_timeout` set cluster-wide (e.g. 60s); alert on old `xact_start`.
- Tune autovacuum per hot table: lower `autovacuum_vacuum_scale_factor` (e.g. 0.01), more
  workers/cost limit on big clusters.
- Watch `n_dead_tup`, bloat estimates, and `datfrozenxid` age dashboards.
- Design for HOT: don't index churn-columns; fillfactor headroom.

### 9. Coding Questions
1. Write the monitoring query: sessions idle in transaction > 5 min, with age and query.
2. Explain the visibility decision: tuple (xmin=500 committed, xmax=520 in-progress) under a
   snapshot where 520 is in the in-progress list → visible or not? (Visible — deleter hasn't
   committed for this snapshot.)

### 10. SQL Examples
```sql
-- See version churn and vacuum health
SELECT relname, n_live_tup, n_dead_tup, last_autovacuum
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;

-- Long transaction hunt
SELECT pid, now() - xact_start AS duration, state, query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL ORDER BY xact_start LIMIT 10;

-- Wraparound safety margin
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;

-- Inspect tuple versions (educational)
SELECT xmin, xmax, ctid, * FROM accounts WHERE id = 7;
```

### 11. Optimization Techniques
- pg_repack for online bloat removal (VACUUM FULL takes an exclusive lock).
- Batch large DELETEs/UPDATEs in chunks with pauses so autovacuum keeps pace; for "delete most
  of the table" prefer partition drops or CTAS-swap.
- On replicas, `hot_standby_feedback` trade-off: stops query-vs-vacuum conflicts but exports
  replica xmin to the primary (bloat) — know both directions.

### 12. Follow-up Questions
- "Replication conflict: replica query cancelled by vacuum cleanup — explain and fix options."
  (max_standby_streaming_delay vs hot_standby_feedback vs dedicated replica)
- "Why does Postgres need freeze but MySQL doesn't?" (32-bit XID comparisons vs InnoDB's
  different versioning scheme)
- "What's the cost of MVCC for update-heavy tables vs an in-place-update engine?" (write
  amplification + vacuum debt vs undo/redo complexity)

---

## Chapter 6.3 — Locks: Row, Table, Advisory; FOR UPDATE / SKIP LOCKED

### 1. Why Interviewers Ask This
Lock questions are incident questions: "the deploy added a column and the site went down,"
"workers grab the same job." You're expected to know lock granularities, what blocks what, and
the queue-worker idiom.

### 2. Core Concept
- **Row locks** (stored on tuples, unlimited count): exclusive (UPDATE/DELETE/`FOR UPDATE`),
  plus weaker shares (`FOR NO KEY UPDATE`, `FOR SHARE`, `FOR KEY SHARE` — FK machinery).
  Writers queue per row FIFO.
- **Table locks** (8 modes): every statement takes one — SELECT takes ACCESS SHARE; most DDL
  takes ACCESS EXCLUSIVE (blocks *everything*, including SELECTs). The killer detail: a waiting
  ACCESS EXCLUSIVE **blocks all newcomers behind it** → one ALTER TABLE behind a long SELECT
  stalls the whole table.
- **`SELECT ... FOR UPDATE`**: lock rows you're about to modify (pessimistic). Modifiers:
  `NOWAIT` (error instead of wait), **`SKIP LOCKED`** (skip locked rows — the concurrent
  job-queue primitive).
- **Advisory locks**: application-defined lock IDs unrelated to rows
  (`pg_advisory_lock(key)`) — leader election, migration mutexes, dedup of cron jobs.
- Lock waits are invisible until you look: `pg_locks` + `pg_blocking_pids()`.

### 3. Internal Working
Row lock = xmax field + lock bits on the tuple (no lock-table blowup; contrast SQL Server
escalation). Waiters sleep on the transaction holding the row until it ends. Table locks live in
shared memory with a wait **queue**: conflicts are checked against holders *and* queued
requests (that's the DDL-pileup mechanism). `lock_timeout` bounds how long a statement waits;
`deadlock_timeout` (1s) is when the deadlock detector wakes.

### 4. Visualization (ASCII)
```
Row-lock queue on id=7:      DDL pileup:
T1 UPDATE (holds)            long SELECT (ACCESS SHARE, running)
T2 UPDATE (waits)               ▲
T3 UPDATE (waits)            ALTER TABLE (ACCESS EXCLUSIVE) — WAITS
  FIFO per row                  ▲
                             every new SELECT/INSERT — WAITS BEHIND THE ALTER
                             table effectively down ✖
                             fix: lock_timeout on DDL + retry

Job queue with SKIP LOCKED:
jobs: [J1][J2][J3][J4]...
W1: SELECT ... FOR UPDATE SKIP LOCKED LIMIT 1 → locks J1
W2: same query → skips J1 (locked) → locks J2   ← no contention, no double-work
```

### 5. Real Production Example
Two canonical ones:
1. **Migration outage**: `ALTER TABLE orders ADD COLUMN ...` queued behind a 10-min analytics
   query on the primary → all order traffic queued behind the ALTER → checkout down. Fix
   pattern: `SET lock_timeout='2s'` + retry loop for DDL; run analytics elsewhere.
2. **Job queue**: workers doing `SELECT ... WHERE status='pending' LIMIT 1 FOR UPDATE` all
   blocked on the same first row (or worse, without FOR UPDATE, processed it twice). The
   `FOR UPDATE SKIP LOCKED` idiom (below) is the industry-standard answer and a very common
   interview design question.

### 6. Common Interview Questions
- "What blocks what: two UPDATEs same row? UPDATE + SELECT? SELECT + ALTER TABLE?"
- "Design a Postgres-backed job queue for N concurrent workers." (SKIP LOCKED expected)
- "Why did adding a nullable column with a default lock the table?" (pre-PG11 rewrite; PG11+
  fast default — version nuance = points)
- "How do you find who's blocking whom right now?"
- "What are advisory locks for?"

### 7. Common Mistakes
- Believing plain SELECT can be blocked by row locks (it can't — MVCC) or that it takes no lock
  at all (ACCESS SHARE, conflicts with ACCESS EXCLUSIVE DDL).
- Queue workers with `LIMIT 1 FOR UPDATE` and no SKIP LOCKED → convoy.
- Long-held FOR UPDATE across external calls (Module 1.8's cardinal sin).
- Running DDL without lock_timeout on hot tables.
- Forgetting `NOWAIT`/`SKIP LOCKED` exist and building polling/retry loops around blocking waits.

### 8. Best Practices
- All migrations: `lock_timeout` + retries; know your non-blocking DDL menu (CREATE INDEX
  CONCURRENTLY, ADD COLUMN without volatile default, ADD CONSTRAINT NOT VALID + VALIDATE,
  DETACH PARTITION CONCURRENTLY).
- Lock ordering discipline + acquire late, release fast (commit promptly).
- Job queues: `FOR UPDATE SKIP LOCKED` + status transitions + visibility timeout for crashes.
- Dashboards: lock waits (`pg_locks` granted=false), blocking chains, lock_timeout error rates.

### 9. Coding Questions
1. Write the worker dequeue transaction (below) and explain crash-recovery (row lock released on
   crash → job re-claimable; add attempts counter).
2. Write the blocking-chain query using `pg_blocking_pids()`.

### 10. SQL Examples
```sql
-- Concurrent-safe dequeue
BEGIN;
SELECT id, payload FROM jobs
WHERE status = 'pending' AND run_at <= now()
ORDER BY run_at
FOR UPDATE SKIP LOCKED
LIMIT 10;
UPDATE jobs SET status='running', started_at=now() WHERE id = ANY($claimed);
COMMIT;   -- process, then mark done/failed in a new txn

-- Who blocks whom
SELECT pid, pg_blocking_pids(pid) AS blocked_by, state, wait_event_type, query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;

-- Safe DDL pattern
SET lock_timeout = '2s';
ALTER TABLE orders ADD COLUMN note text;   -- retried by the migration tool on timeout

-- Advisory lock: single-flight cron
SELECT pg_try_advisory_lock(hashtext('daily-billing'));  -- false → someone else runs it
```

### 11. Optimization Techniques
- Shard hot rows (counters, single-row config) to spread lock queues.
- Replace lock-wait polling with LISTEN/NOTIFY for queue wakeups.
- Use `FOR NO KEY UPDATE` instead of `FOR UPDATE` when you won't touch key columns — doesn't
  block FK inserts referencing the row.

### 12. Follow-up Questions
- "SKIP LOCKED worker dies mid-job after COMMIT of the claim — how does the job recover?"
  (visibility timeout / heartbeat + reaper; idempotent processing)
- "Compare with SQL Server lock escalation — why doesn't Postgres escalate?" (locks on tuples,
  not in a lock table)
- "When is an advisory lock better than a row lock?" (no row to lock yet — e.g., 'create if
  absent per key' without unique-violation churn; cross-table critical sections)

---

## Chapter 6.4 — Deadlocks

### 1. Why Interviewers Ask This
"Explain a deadlock you debugged" is a standard behavioral-technical hybrid. They test: the
cycle definition, how DBs handle it (detection, not prevention), and *code patterns* that
prevent it.

### 2. Core Concept
Deadlock = a cycle in the waits-for graph: T1 holds A waits for B; T2 holds B waits for A.
Databases **detect and kill** (Postgres: after `deadlock_timeout` (1s), check the graph, abort
one victim with error 40P01) — they don't prevent. Prevention is *your* job:

1. **Consistent lock ordering** — all code paths touch shared resources in the same global
   order (sort ids before multi-row updates!).
2. **Lock everything at once** — one `SELECT ... FOR UPDATE` with all target rows sorted,
   instead of incremental acquisition.
3. **Short transactions** — narrow the collision window.
4. **Retry on 40P01** — deadlocks may still happen; treat like serialization failures.

Subtle sources interviewers probe: FK locks (parent `FOR KEY SHARE` vs parent UPDATE), unique
index insert waits, two multi-row UPDATEs with different scan orders, lock upgrades
(FOR SHARE → UPDATE).

### 3. Internal Working
Postgres's detector runs in the *waiting* backend after deadlock_timeout: build local waits-for
graph from the lock table, find cycles, abort the waiter that detected it (roughly — the victim
choice is implementation detail; MySQL InnoDB picks the smaller-undo victim). The killed txn
gets `deadlock detected` with DETAIL naming both queries — the log line you must know how to
read. Multi-row UPDATE deadlocks happen because row lock acquisition follows *scan order*,
which can differ between plans.

### 4. Visualization (ASCII)
```
T1: UPDATE accounts SET .. WHERE id=1;   -- holds row1
T2: UPDATE accounts SET .. WHERE id=2;   -- holds row2
T1: UPDATE accounts SET .. WHERE id=2;   -- waits on T2
T2: UPDATE accounts SET .. WHERE id=1;   -- waits on T1 → CYCLE

waits-for:  T1 ──▶ T2
             ▲      │
             └──────┘   detector: abort one (40P01), other proceeds

Fix (ordering): both transfer functions lock LEAST(id) then GREATEST(id):
T1: lock 1, lock 2.  T2: lock 1 (waits behind T1) — serialized, no cycle ✔
```

### 5. Real Production Example
Payments transfer service: `transfer(from, to)` locked `from` then `to`. Concurrent A→B and
B→A = textbook cycle; at scale, hundreds of 40P01/hour. Fix: lock accounts in `ORDER BY id`
inside one `SELECT ... FOR UPDATE`, plus retries. Second favorite: batch jobs updating rows in
index order while OLTP updates them in a different order — nightly deadlock spikes; fix by
chunking the batch in PK order with small transactions.

### 6. Common Interview Questions
- "What's a deadlock and how does the DB resolve it?"
- "Write transfer(from,to) so it can't deadlock." (ordering)
- "Deadlock between an INSERT and an UPDATE — how?" (FK/unique-index waits)
- "How do you investigate recurring deadlocks in prod?" (log lines with both queries →
  reconstruct interleaving → find inconsistent ordering)
- "Difference between deadlock and lock wait/timeout?"

### 7. Common Mistakes
- "Fixing" by lengthening deadlock_timeout (just detects later; waits longer).
- Retrying non-idempotent logic blindly.
- Ordering by business fields ("from before to") instead of a global total order (ids).
- Missing that a *single* multi-row UPDATE can deadlock against another due to scan order —
  "one statement" ≠ "atomic lock acquisition."

### 8. Best Practices
- Codify lock-ordering (sort ids) in shared helpers; review multi-entity transactions for it.
- Log and alert on deadlock rate; each recurring pair of queries in DETAIL is a bug ticket.
- Prefer designs that lock one row (single-owner mutations via queues) over multi-row locking.
- Keep `log_lock_waits = on` to see near-deadlocks (long waits) too.

### 9. Coding Questions
1. Write deadlock-free `transfer(a, b, amount)` (lock both rows sorted, verify balances, update
   both) with the retry wrapper.
2. Given the log: `Process 111 waits for ShareLock on transaction 222; blocked by process 333...
   DETAIL: Process 111: UPDATE orders SET ...; Process 333: UPDATE inventory SET ...` —
   reconstruct the interleaving and propose the ordering fix.

### 10. SQL Examples
```sql
-- Deadlock-free transfer core
BEGIN;
SELECT id, balance FROM accounts
WHERE id IN (:a, :b)
ORDER BY id                 -- global total order
FOR UPDATE;                 -- both locks acquired here, atomically from our view
UPDATE accounts SET balance = balance - :amt WHERE id = :a AND balance >= :amt;
-- check rowcount; then:
UPDATE accounts SET balance = balance + :amt WHERE id = :b;
COMMIT;

-- Chunked batch update in stable order (plays nice with OLTP)
UPDATE items SET price = price * 1.02
WHERE id IN (SELECT id FROM items WHERE category=7 ORDER BY id LIMIT 1000 OFFSET :i);
```

### 11. Optimization Techniques
- Reduce multi-row transactions to single-row via redesign (event per entity, saga).
- `SELECT FOR UPDATE ... ORDER BY` before UPDATE guarantees acquisition order regardless of
  update plan.
- In InnoDB, smaller transactions + same-index access paths reduce gap-lock deadlocks
  (know that MySQL RR gap/next-key locks create deadlocks Postgres doesn't have).

### 12. Follow-up Questions
- "Can SELECTs deadlock in Postgres?" (plain MVCC reads: no; FOR SHARE/UPDATE: yes; and DDL
  vs DML can)
- "Deadlocks across two *databases*/services — who detects?" (nobody — distributed deadlock
  needs timeouts; another reason to avoid distributed transactions)
- "Why do gap locks make MySQL deadlock-prone on inserts?" (adjacent-range locking under RR)

---

## Chapter 6.5 — Optimistic vs Pessimistic Locking

### 1. Why Interviewers Ask This
Application-level concurrency design — the question is "how would you prevent two users
overwriting each other?" and they want you to *choose* based on contention math, not recite
definitions.

### 2. Core Concept
- **Pessimistic**: assume conflict; take the lock before working (`SELECT ... FOR UPDATE`).
  Nobody else can even start. Costs: held locks (throughput ceiling), needs an open transaction
  spanning the operation → unusable across user think-time/HTTP requests.
- **Optimistic (OCC)**: assume no conflict; read a **version** with the data; write with
  `UPDATE ... WHERE id=? AND version=?` (and version=version+1). Rowcount 0 = someone else won →
  reload/merge/retry or surface a conflict. No locks held while thinking; cost = wasted work +
  retries under contention.

Decision rule: **contention low / operation long / spans requests → optimistic. Contention
high / operation short / in-transaction → pessimistic (or better: atomic single statements).**
Related: ETags/If-Match are OCC over HTTP; CAS in Redis (`WATCH/MULTI`) and DynamoDB
(ConditionExpression) are the same idea.

### 3. Internal Working
OCC's guarded UPDATE is atomic because the row lock is taken *during* the update and the
predicate re-checked against the current version (READ COMMITTED requery semantics working *for*
you). Version column can be an integer, `xmin` (Postgres system column — neat trick), or a
timestamp (beware clock resolution). Pessimistic `FOR UPDATE` parks competitors on the row's
lock queue; with `NOWAIT`/`SKIP LOCKED` you convert waiting into control flow.

### 4. Visualization (ASCII)
```
OPTIMISTIC (version column):
T1: read (doc, v=5) ── user edits 3 min ──▶ UPDATE ... WHERE v=5 → v=6 ✔
T2: read (doc, v=5) ── user edits 4 min ──▶ UPDATE ... WHERE v=5 → 0 rows ✖
                                             → "document changed" → merge/retry
no locks held during the 4 minutes ✔

PESSIMISTIC:
T1: BEGIN; SELECT ... FOR UPDATE ──── work ────▶ COMMIT
T2:        SELECT ... FOR UPDATE ──── waits ───▶ proceeds after T1
throughput = serialized per row; safe but queued
```

### 5. Real Production Example
- **Optimistic**: CMS/document editing (two editors, minutes-long edits) — version column +
  conflict UI. Also every JPA `@Version`, Elasticsearch `_seq_no`, DynamoDB conditional writes.
- **Pessimistic**: warehouse inventory allocation during checkout — short transaction, high
  contention on hot SKUs; `FOR UPDATE` (or single-statement guarded decrement) is correct;
  optimistic here would retry-storm on popular items during a drop.

### 6. Common Interview Questions
- "Two admins edit the same record — design the protection." (OCC + conflict UX)
- "Implement optimistic locking in SQL." (guarded UPDATE, rowcount)
- "When does optimistic locking perform worse?" (high contention: retries × wasted work exceed
  lock waits)
- "How do you do pessimistic locking across two HTTP requests?" (you don't — that's a *lease*:
  locked_by/locked_until columns, expiry, still OCC underneath)

### 7. Common Mistakes
- OCC without handling rowcount=0 (silently dropping the loser's write = the lost update you
  were preventing).
- Version check on read but not in the UPDATE's WHERE (TOCTOU).
- Holding `FOR UPDATE` transactions across user interaction / external APIs.
- Timestamp versions with second resolution (two updates same second).
- Using OCC for aggregate invariants across rows (that's write skew territory — 6.6).

### 8. Best Practices
- Default OCC for user-facing edits; version column + clear conflict responses (HTTP 409/412).
- Pessimistic (or atomic statements) for hot, short, machine-driven mutations.
- Leases (not held locks) for long exclusive claims: `claimed_by, claimed_until` + guarded
  claim UPDATE + expiry reaper.
- Bound retries with jitter; surface repeated conflicts, don't loop forever.

### 9. Coding Questions
1. Full OCC flow for a profile edit: read (id, version, fields) → guarded UPDATE → rowcount 0
   path returning the fresh row for merge.
2. Lease-based claim: `UPDATE tasks SET claimed_by=$w, claimed_until=now()+'5 min' WHERE id=$t
   AND (claimed_by IS NULL OR claimed_until < now()) RETURNING *;` — explain every predicate.

### 10. SQL Examples
```sql
-- Optimistic concurrency
SELECT id, version, title, body FROM docs WHERE id = 42;      -- returns version=5
UPDATE docs
SET title=$1, body=$2, version = version + 1, updated_at = now()
WHERE id = 42 AND version = 5;                                 -- rowcount 0 ⇒ conflict

-- xmin trick (no schema change)
SELECT id, xmin AS version, ... FROM docs WHERE id=42;
UPDATE docs SET ... WHERE id=42 AND xmin = $version::text::xid;

-- Pessimistic with control flow instead of blocking
SELECT * FROM inventory WHERE sku=$1 FOR UPDATE NOWAIT;  -- 55P03 ⇒ tell user "busy, retry"
```

### 11. Optimization Techniques
- Reduce contention before choosing a scheme: shard hot rows, queue mutations to a single
  writer, batch increments.
- Combine: optimistic fast path, fall back to pessimistic after k conflicts.
- Keep versioned payloads small (don't re-write megabyte JSON per version bump — split hot
  fields).

### 12. Follow-up Questions
- "How does this map to DynamoDB / Mongo?" (ConditionExpression / findAndModify with query on
  version — same guarded-write shape)
- "OCC retry rate is 30% on one row — now what?" (it's a hot row: redesign — queue, shard,
  CRDT-style merge, or pessimistic)
- "What HTTP machinery expresses OCC to clients?" (ETag + If-Match → 412)

---

## Chapter 6.6 — SERIALIZABLE & Write Skew

### 1. Why Interviewers Ask This
Write skew is the staff-level discriminator: an anomaly that survives snapshot isolation and
breaks real invariants (on-call rosters, budgets, double-booking). Explaining SSI marks you as
genuinely deep in Postgres.

### 2. Core Concept
**Write skew**: T1 and T2 each read a shared predicate, then write **different** rows, each
preserving the invariant *given what they read* — but together violating it.
Canonical: "≥1 doctor must remain on call." Both on-call doctors check
`count(on_call)=2 ≥ 2` and each takes *themselves* off call → 0 on call. No row was written by
both → no write-write conflict → **snapshot isolation (PG REPEATABLE READ) permits it**.

**SERIALIZABLE in Postgres = SSI** (Serializable Snapshot Isolation, PG 9.1+): optimistic —
runs like snapshot isolation while tracking read/write dependencies (predicate locks, "SIReadLocks");
when a dangerous dependency cycle appears, one transaction is aborted with 40001. No blocking,
no extra locks held; cost = tracking overhead + retries + false positives (predicate locks can
be page/relation-granular).

Alternatives when you can't/won't use SERIALIZABLE:
- **Materialize the conflict**: make the invariant a *row* both transactions must touch —
  e.g., a `shift_slots` row per slot updated on every change (turns skew into a write-write
  conflict), or `SELECT ... FOR UPDATE` on a parent/guard row.
- **Constraints**: unique / exclusion constraints check against *current* data, not snapshots —
  `EXCLUDE USING gist (room WITH =, during WITH &&)` kills double-booking outright.

### 3. Internal Working
SSI theory: snapshot-isolation anomalies always contain two consecutive **rw-antidependency**
edges (T1 reads what T2 later writes) in the serialization graph. Postgres tracks rw-edges via
SIRead locks taken by reads (kept until overlapping transactions finish); on detecting a
T_a →rw→ T_b →rw→ T_c pattern with a committed pivot, abort one. False positives arise from
lock granularity promotion (row → page → relation under memory pressure:
`max_pred_locks_per_transaction`).

### 4. Visualization (ASCII)
```
Write skew (both at REPEATABLE READ — permitted!):
invariant: at least 1 doctor on call.  state: alice=on, bob=on
T1: SELECT count(*) WHERE on_call → 2      T2: SELECT count(*) WHERE on_call → 2
T1: UPDATE alice SET on_call=false          T2: UPDATE bob SET on_call=false
T1: COMMIT ✔                                T2: COMMIT ✔      → 0 on call ✖✖

Under SERIALIZABLE (SSI):
T1 read the predicate T2 wrote to, and vice versa → rw-cycle detected
→ one gets ERROR 40001 → retries → sees count=1 → refuses. invariant holds ✔

Materialized conflict alternative:
both must  UPDATE oncall_guard SET version=version+1  → write-write conflict → serialized
```

### 5. Real Production Example
Real-world write skews interviewers recognize: double-booking a meeting room (both check "no
overlap", insert different rows); spending a budget from two services (both read remaining,
insert different expense rows); issuing the last two support slots twice. Stripe-class systems
solve the money ones with **exclusion/unique constraints + single-row guards**, reserving
SERIALIZABLE for genuinely predicate-shaped invariants. Booking systems (Module 9) use
`EXCLUDE ... WITH &&` as the bedrock.

### 6. Common Interview Questions
- "Give an anomaly snapshot isolation does NOT prevent." (write skew, with the doctors example)
- "How does Postgres implement SERIALIZABLE without two-phase locking?" (SSI summary)
- "Prevent double-booking without SERIALIZABLE." (exclusion constraint / guard row FOR UPDATE)
- "What operational costs come with SERIALIZABLE?" (retries mandatory, predicate-lock memory,
  false positives, all-or-nothing per involved txns)
- "Why must the *whole set* of cooperating transactions be SERIALIZABLE?" (a READ COMMITTED
  bystander can still observe/create anomalies against them)

### 7. Common Mistakes
- Claiming REPEATABLE READ prevents "all anomalies except phantoms" — write skew survives.
- Using SERIALIZABLE without retry loops (40001 is expected behavior, not failure).
- Modeling invariants only in application checks when a constraint could enforce them
  against current data.
- Thinking SSI blocks like 2PL — it aborts instead; latency profile is different (fast until
  it isn't).

### 8. Best Practices
- Prefer declarative enforcement (unique/exclusion constraints) > materialized conflicts >
  SERIALIZABLE > hope.
- If SERIALIZABLE: keep transactions short, retry with backoff, watch
  `pg_stat_database.serialization_failures`-style metrics, size
  `max_pred_locks_per_transaction`.
- Document each invariant with *which mechanism* guards it — the artifact interviewers wish
  every team had.

### 9. Coding Questions
1. Doctors on call: write the schema, show the skew at RR, then fix three ways (SERIALIZABLE +
   retry; guard row; CHECK-via-trigger with FOR UPDATE) and rank them.
2. Meeting rooms: DDL with `EXCLUDE USING gist (room_id WITH =, during WITH &&)` and the insert
   that safely fails on overlap.

### 10. SQL Examples
```sql
-- Exclusion constraint: overlap-proof bookings (needs btree_gist)
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE bookings (
  room_id int NOT NULL,
  during  tstzrange NOT NULL,
  EXCLUDE USING gist (room_id WITH =, during WITH &&)
);
-- concurrent overlapping inserts: exactly one succeeds, other gets 23P01 ✔

-- SERIALIZABLE with retry (shape)
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT count(*) FROM doctors WHERE on_call;
UPDATE doctors SET on_call = false WHERE id = $me;  -- only if count would stay >= 1
COMMIT;  -- app retries on 40001

-- Materialized conflict (guard row)
BEGIN;
SELECT 1 FROM oncall_guard WHERE team=$t FOR UPDATE;   -- serialize the invariant check
-- re-check count, then update
COMMIT;
```

### 11. Optimization Techniques
- Scope SERIALIZABLE to the few endpoints owning the invariant; leave the rest at READ COMMITTED.
- `SET default_transaction_isolation` per service/role rather than sprinkling BEGIN options.
- Reduce false positives: smaller transactions, avoid seq scans inside serializable txns
  (relation-level SIRead locks), enough predicate-lock memory.

### 12. Follow-up Questions
- "How would MySQL handle the doctors case at SERIALIZABLE?" (2PL-style: reads take shared
  locks → blocks instead of aborting — different failure mode: deadlocks/waits)
- "Can you get write skew across microservices with per-service DBs?" (yes — and no DB fixes
  it; needs a coordinator/saga/single-owner design)
- "What's `SERIALIZABLE READ ONLY DEFERRABLE` for?" (waits for a known-safe snapshot: heavy
  reports with zero abort risk and zero tracking cost)

---

# Module 6 — Practice Problems

## Easy (5)
1. Match each anomaly (dirty read, non-repeatable read, phantom, lost update, write skew) to
   the weakest PG isolation level that prevents it.
2. Two concurrent `UPDATE counters SET n = n + 1 WHERE id=1` at READ COMMITTED — is an increment
   ever lost? Why (single-statement atomicity + row lock queue)?
3. What error codes do you retry, and what's the retry recipe? (40001, 40P01; bounded jittered
   backoff; idempotent bodies.)
4. Why does a plain SELECT never block an UPDATE in Postgres, and what statement *does* a plain
   SELECT block?
5. Write the SKIP LOCKED dequeue for a `jobs` table, claiming up to 10 jobs.

## Medium (5)
6. Reproduce a lost update with two psql sessions at READ COMMITTED (exact command sequence),
   then show the same sequence failing at REPEATABLE READ.
7. An ALTER TABLE on a hot table caused a 90-second full outage though it only needed 200ms of
   work. Reconstruct the queue mechanics and write the safe-DDL runbook.
8. Inventory oversell: `SELECT stock; if stock>0: UPDATE stock=stock-1` under 500 concurrent
   buyers. Show the race, then fix with (a) one guarded statement, (b) FOR UPDATE, (c)
   SERIALIZABLE — and compare throughput on ONE hot SKU.
9. Nightly job deadlocks with OLTP ~50x/night; logs show the job updating in category order,
   OLTP updating in id order. Design the fix (chunked PK-ordered batches + retries) and explain
   why ordering works.
10. Choose optimistic or pessimistic (and justify): (a) wiki page edits, (b) seat selection at
    checkout, (c) cron job leader election, (d) bank ledger postings, (e) shopping cart updates.

## Hard (5)
11. Design the on-call invariant ("≥1 doctor per team on call") for a team-scale product:
    schema, the write-skew proof at RR, chosen mechanism (guard row vs SSI vs trigger), retry
    policy, and monitoring for violation attempts.
12. A REPEATABLE READ report transaction runs 40 minutes on the primary. Enumerate every harm
    (vacuum horizon, bloat, wraparound clock, lock exposure on any writes, replica conflict if
    moved) and produce the architecture that removes it (replica + snapshot exports, or
    SERIALIZABLE DEFERRABLE on standby).
13. Build a double-booking-proof reservation system for 10k hotels without SERIALIZABLE:
    exclusion constraints per resource, hot-resource sharding, waitlist path on conflict, and
    the idempotency layer for client retries. Prove each concurrent scenario.
14. SSI false-positive storm: serialization failures spike 100x during a batch import touching
    the same pages as OLTP serializable txns. Explain predicate-lock granularity promotion,
    confirm via pg_locks (SIReadLock modes), and fix (batch at READ COMMITTED + constraints,
    memory sizing, schedule isolation).
15. Compare Postgres SSI vs MySQL InnoDB SERIALIZABLE (2PL, gap locks) for a ticket-sales
    workload: failure modes (aborts vs deadlocks/waits), throughput under hot rows, developer
    ergonomics, and which you'd pick with justification.

---

*Next: [Module 7 — Database Scaling](module-07-scaling.md)*

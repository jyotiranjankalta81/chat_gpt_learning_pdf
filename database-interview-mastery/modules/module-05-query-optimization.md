# MODULE 5 — Query Optimization

> The "can you actually fix a slow query?" module. Interviewers hand you a plan or a scenario
> and watch your process. Have a *method*, not vibes.

Chapters:
5.1 EXPLAIN & EXPLAIN ANALYZE — Reading Execution Plans
5.2 The Cost-Based Optimizer & Statistics
5.3 Plan Transformations: Predicate Pushdown & Join Reordering
5.4 Sorting & Filtering at Scale
5.5 Pagination (OFFSET vs Keyset)
5.6 COUNT Optimization
5.7 The N+1 Query Problem

---

## Chapter 5.1 — EXPLAIN & EXPLAIN ANALYZE

### 1. Why Interviewers Ask This
"Here's a slow query — what do you do first?" The expected first move is always EXPLAIN
(ANALYZE, BUFFERS). Then they hand you output and grade how you read it.

### 2. Core Concept
- `EXPLAIN` — the plan and **estimates** only (doesn't run the query).
- `EXPLAIN ANALYZE` — runs it, adds **actual** times, row counts, loops. (Careful: it executes —
  wrap DML in `BEGIN; ... ROLLBACK;`.)
- `BUFFERS` — pages touched (shared hit = cache, read = disk, written, temp = spills). The
  honest cost currency.
- Plans are trees; execution flows leaves → root. Read inner/deepest nodes first.

The five things to extract, in order:
1. **Estimate vs actual rows** per node — the #1 diagnostic. Off by >10x = stats problem, and
   every decision above that node is suspect.
2. **loops=** — a node's true cost is `actual time × loops` (nested loop inners run N times).
3. **Where the time actually goes** — find the node(s) owning the elapsed time.
4. **Spills** — `Sort Method: external merge Disk: ...`, `Batches: >1`, lossy bitmaps → work_mem.
5. **Scan/join choices vs your expectation** — Filter vs Index Cond, unexpected Seq Scan or Sort.

### 3. Internal Working
Costs are in abstract units: `cost=startup..total`; `rows` = estimated output rows; `width` =
avg row bytes. ANALYZE adds `actual time=first..last rows=N loops=M`. `Rows Removed by Filter`
shows wasted reads (fetched then discarded — an index-shape smell). BUFFERS distinguishes
"slow because disk" from "slow because CPU/rows". `auto_explain` logs plans of slow production
queries with real parameters — the way you catch what you can't reproduce.

### 4. Visualization (ASCII)
```
Limit (actual time=0.1..812.4 rows=50)
  └─ Sort (actual time=812.3.. rows=50)          ← time lives HERE
       Sort Method: external merge  Disk: 480MB  ← spill! work_mem
       └─ Hash Join (rows est=1200 actual=9,400,000)   ← 7,800x misestimate!
            ├─ Seq Scan on orders (Filter: status='paid'
            │        Rows Removed by Filter: 88,000,000)  ← index-shape smell
            └─ Hash └─ Seq Scan on users

Reading order: bottom-up. Root cause chain: misestimate → wrong join input sizes →
oversized sort → disk spill. Fix stats & index BEFORE touching work_mem.
```

### 5. Real Production Example
The universal incident: ORM-generated query is fine for months, then a customer with 4M rows
(vs median 200) hits it. `auto_explain` captures the plan: nested loop chosen on a 12-row
estimate, actual 4M → 4M index probes. Fix: extended statistics + a composite index; the deeper
fix is testing with skewed tenants. Interviewers replay exactly this with printed plans.

### 6. Common Interview Questions
- "Walk me through this EXPLAIN output." (practice verbalizing: bottom-up, estimates vs actuals,
  time attribution)
- "EXPLAIN vs EXPLAIN ANALYZE — and when is ANALYZE dangerous?" (DML executes; also its timing
  overhead can distort very hot nodes)
- "What does `Rows Removed by Filter: 88M` tell you?"
- "Query is slow in prod, fast in staging — what do you compare?" (plans, stats, data volume,
  parameters, cache, settings)

### 7. Common Mistakes
- Reading only the top line / total cost and stopping.
- Ignoring `loops` and blaming the wrong node.
- Fixing the symptom node (raise work_mem) when a misestimate below caused it.
- Comparing one warm-cache run vs one cold run and declaring victory (run twice; check BUFFERS
  hit vs read).

### 8. Best Practices
- Always `EXPLAIN (ANALYZE, BUFFERS)`; format JSON + a visualizer (explain.dalibo / pev2) for
  big plans.
- Enable `pg_stat_statements` (aggregate top offenders) + `auto_explain` (individual bad runs)
  in every production system.
- Keep a before/after plan in every optimization PR — plans are the proof.

### 9. Coding Questions
1. Given a plan with `Nested Loop (rows=3 actual rows=1)` wrapping
   `Index Scan (loops=1,200,000, actual time=0.04)`, compute where the time went and name the fix.
2. Write the pg_stat_statements query returning the top 10 statements by total time with mean
   time and call counts.

### 10. SQL Examples
```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT ...;

-- Safe ANALYZE for DML
BEGIN; EXPLAIN ANALYZE DELETE FROM jobs WHERE ...; ROLLBACK;

-- Top offenders
SELECT calls, round(total_exec_time)::bigint AS total_ms,
       round(mean_exec_time,1) AS mean_ms, rows, query
FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;

-- Log every plan slower than 500ms
-- postgresql.conf: shared_preload_libraries='pg_stat_statements,auto_explain'
--                  auto_explain.log_min_duration='500ms'  auto_explain.log_analyze=on
```

### 11. Optimization Techniques
- Diagnosis order: estimates → access paths → join algorithms → memory/spills → rewrite →
  (last) config. Say this order in interviews.
- `track_io_timing = on` for real read/write ms in BUFFERS output.

### 12. Follow-up Questions
- "Estimates are perfect but the query is still slow — next?" (it's doing exactly what you
  asked: reduce work — rewrite, pre-aggregate, cache, better index shape)
- "How do you EXPLAIN a query you can't reproduce?" (auto_explain with real params;
  pg_stat_statements to find it)

---

## Chapter 5.2 — The Cost-Based Optimizer & Statistics

### 1. Why Interviewers Ask This
"Why did the planner do that?" questions test whether you model the optimizer as a deterministic
cost machine driven by statistics — because then every weird plan has a findable cause.

### 2. Core Concept
The optimizer: enumerate equivalent plans (access paths per table × join orders × join
algorithms) → estimate each plan's cost from **statistics** and **cost parameters** → execute
the cheapest. It is only as good as:
- **Statistics**: per-column n_distinct, MCV lists, histograms, correlation (from ANALYZE /
  autovacuum's analyze); extended statistics for column correlations; expression statistics.
- **Cost parameters**: `seq_page_cost=1`, `random_page_cost` (lower on SSD!), `cpu_tuple_cost`,
  `effective_cache_size` (how much of the index/table it may assume cached), `work_mem`.
- **Cardinality propagation**: output-row estimates flow up the tree; errors compound
  multiplicatively through joins.

Postgres deliberately has **no hints** (core) — the philosophy: fix the inputs (stats, indexes,
sargability), not the output. Know that MySQL/Oracle/SQL Server do have hints, and pg_hint_plan
exists for emergencies.

### 3. Internal Working
- ANALYZE samples 300 × stats_target rows (default target 100 → 30k rows) — huge tables get
  sampling error, especially for n_distinct (systematically underestimated).
- Join size estimate: |A ⋈ B| ≈ |A|×|B| × selectivity(join pred), assuming independence and
  containment — skewed keys break it.
- Search space: exhaustive (dynamic programming) up to `geqo_threshold` (12 rels), then genetic
  algorithm (plans get nondeterministic!); `join_collapse_limit` (8) bounds reorder freedom —
  beyond it, your written join order partially binds.
- Plan caching: prepared statements switch to a **generic plan** after ~5 executions if it looks
  competitive — parameter-skew regressions appear exactly then (`plan_cache_mode` overrides).

### 4. Visualization (ASCII)
```
             statistics             cost params
     (n_distinct, MCV, histogram,  (random_page_cost,
      correlation, ext-stats)       work_mem, cache size)
              └──────────┬──────────────┘
                         ▼
  plan space ──▶ [cost each plan] ──▶ argmin ──▶ executor
  A⋈(B⋈C), (A⋈B)⋈C, ...   ▲
  idx vs seq per table      └── garbage in → confidently wrong plan out
Error compounding: est(A)=10 (real 10k) → join est 100 (real 10M) → NL chosen → meltdown
```

### 5. Real Production Example
After a Black-Friday-scale backfill inserts 400M rows, dashboards die. Nothing changed but the
data: autovacuum's ANALYZE hadn't caught up, the planner still believed the table had 2M rows,
picked nested loops everywhere. On-call runs `ANALYZE big_table;` — recovery in seconds. This
"stats after bulk load" story is a standard senior screen scenario, verbatim.

### 6. Common Interview Questions
- "How does a cost-based optimizer decide between plans?"
- "What statistics does Postgres keep and how do they become stale?"
- "Why no hints in Postgres, and what do you do instead?"
- "What's the risk of prepared statements at plan level?" (generic plan vs skewed params)
- "Same query, different plan on two identical replicas — how?" (stats timing, config drift,
  GEQO nondeterminism)

### 7. Common Mistakes
- Assuming autovacuum keeps stats fresh through bulk operations (thresholds are proportional —
  10% of a 2B-row table is 200M changes).
- Cranking work_mem globally (it's per sort/hash node per connection — OOM factory).
- "The optimizer is broken" — it's deterministic; find the wrong input.
- Forgetting expression stats: `WHERE lower(email)=...` has no column stats unless an expression
  index (or PG14 extended expression statistics) exists.

### 8. Best Practices
- Bulk load runbook ends with `ANALYZE` (and often `VACUUM (ANALYZE)`).
- Raise `default_statistics_target` (or per-column) for large skewed tables; add extended
  statistics for known correlations.
- Set `random_page_cost≈1.1`, `effective_cache_size≈75% RAM` on SSD/cloud boxes.
- Treat plan flips as incidents with a cause: diff stats & settings, check autoanalyze
  timestamps (`pg_stat_user_tables.last_autoanalyze`).

### 9. Coding Questions
1. Estimate like the planner: table 10M rows, `WHERE status='pending'` (MCV freq 0.02) AND
   `region='EU'` (freq 0.25) → independent estimate 50k rows. Real: pending is EU-only → 200k.
   What plan damage results and which feature fixes the estimate?
2. Write the query to find tables whose stats are stale relative to churn
   (`pg_stat_user_tables`: n_mod_since_analyze vs reltuples).

### 10. SQL Examples
```sql
-- What the planner believes about a table
SELECT reltuples::bigint AS est_rows, relpages FROM pg_class WHERE relname='orders';
SELECT last_analyze, last_autoanalyze, n_mod_since_analyze
FROM pg_stat_user_tables WHERE relname='orders';

-- Deeper stats for a skewed column + correlated pair
ALTER TABLE orders ALTER COLUMN status SET STATISTICS 1000;
CREATE STATISTICS orders_dep (dependencies) ON status, region FROM orders;
ANALYZE orders;

-- Force per-execution planning for a skew-sensitive prepared statement
SET plan_cache_mode = force_custom_plan;
```

### 11. Optimization Techniques
- For truly untamable queries: pg_hint_plan, or shape the SQL (materialized CTE as an
  optimization fence, `OFFSET 0` trick historically) — declare these last resorts.
- Partition big tables partly *for the planner*: per-partition stats are finer-grained.

### 12. Follow-up Questions
- "How would you detect a plan regression automatically?" (pg_stat_statements mean-time deltas,
  plan hash tracking, canary EXPLAIN in CI against a prod-stats snapshot)
- "What's the equivalent story in MySQL?" (persistent stats tables, ANALYZE TABLE, optimizer
  hints + histograms since 8.0)

---

## Chapter 5.3 — Plan Transformations: Predicate Pushdown & Join Reordering

### 1. Why Interviewers Ask This
These two transformations explain most "why is this equivalent query 100x faster" puzzles, and
they're the vocabulary of data-engineering interviews too (Spark/warehouse pushdown).

### 2. Core Concept
- **Predicate pushdown**: apply filters as close to the data as possible — below joins, into
  subqueries/views/CTEs (PG12+), into partition pruning, into the index itself (Index Cond),
  down to remote sources (FDW) or storage formats (Parquet row groups). Less data flows up.
- **Join reordering**: join order changes intermediate result sizes by orders of magnitude; the
  planner searches orders to minimize intermediate rows (start with the most filtered/smallest
  effective inputs). Constrained by outer-join semantics and `join_collapse_limit`.

What *blocks* pushdown (know this list):
- Volatile functions, `LIMIT`/`OFFSET` inside the subquery, window functions/DISTINCT/GROUP BY
  boundaries (can't push a filter below an aggregate over different grain), `MATERIALIZED` CTEs,
  security barriers (RLS views), type-mismatched predicates.

### 3. Internal Working
The rewriter/planner hoists subqueries into the main query ("subquery pullup") when legal, then
distributes quals to the lowest legal level. Equivalence classes propagate predicates across
join keys: `a.id = b.a_id AND a.id = 5` ⇒ `b.a_id = 5` derived automatically. Outer joins
restrict: a filter on the nullable side can't move below the join without changing semantics
(the Module 3 ON/WHERE distinction is the user-visible face of the same rule).

### 4. Visualization (ASCII)
```
Naive:                          Pushed down:
      σ country='DE'                    ⋈ user_id
          │                            /          \
      ⋈ user_id              σ country='DE'   σ created>=…
      /        \                  │                │
users(50M)  orders(500M)      users→80k        orders→2M (partition pruned)
join input: 50M × 500M        join input: 80k × 2M   (≈ 4 orders of magnitude less)

Join order: ((F ⋈ small_dim) ⋈ big_dim) vs ((F ⋈ big_dim) ⋈ small_dim)
intermediate sizes differ 1000x — same result, different universe of cost
```

### 5. Real Production Example
A BI view `v_orders_enriched` (5-way join) queried as
`SELECT * FROM v_orders_enriched WHERE tenant_id=? AND day=?`. Because views inline, the
predicates push through to every base table and prune partitions — milliseconds. Someone
"optimizes" by materializing the view's subquery per-day with a MATERIALIZED CTE → fence →
five full scans. Undo → fast. Interviews test this as "why did adding MATERIALIZED slow it down?"

### 6. Common Interview Questions
- "What is predicate pushdown? Where does it apply in Postgres / Spark / Parquet?"
- "Why does join order matter if results are identical?"
- "What prevents a filter from being pushed into this subquery?"
- "Explain how `a.id=b.id AND a.id=5` filters b too." (equivalence classes)

### 7. Common Mistakes
- Filtering after aggregation in hand-written SQL when the filter is on the group key (put it in
  WHERE, not HAVING — pushdown by hand).
- MATERIALIZED CTEs / OFFSET-0 fences left in code as cargo cult.
- 10-way joins written in arbitrary order assuming infinite planner freedom
  (join_collapse_limit).
- Expecting pushdown through window functions or DISTINCT.

### 8. Best Practices
- Write filters at the lowest level you semantically can; don't rely on the planner for
  clarity-critical cases.
- Keep views thin and inlinable; avoid stacking aggregates in views that consumers will filter.
- For >8-table joins, write the join order you mean or raise `join_collapse_limit`.

### 9. Coding Questions
1. Rewrite so the date filter prunes partitions:
   `SELECT * FROM (SELECT *, row_number() OVER (...) rn FROM events) t WHERE t.day='2026-07-01'`
   (move the day predicate inside — legality argument included).
2. Given tables F(1B), D1(1k), D2(100M) and filters making D2 contribute 500 rows, argue the
   optimal join order and what estimate error would flip it.

### 10. SQL Examples
```sql
-- Pushdown-friendly view usage: predicates inline through the view
CREATE VIEW v_paid AS
SELECT o.*, u.country FROM orders o JOIN users u ON u.id=o.user_id
WHERE o.status='paid';
EXPLAIN SELECT * FROM v_paid WHERE country='DE' AND created_at >= '2026-06-01';
-- both predicates appear as Index/Seq conditions on base tables ✔

-- Fence demonstration
WITH c AS MATERIALIZED (SELECT * FROM orders)         -- fence: full scan of orders
SELECT * FROM c WHERE id = 5;
WITH c AS NOT MATERIALIZED (SELECT * FROM orders)     -- inlined: index scan on id
SELECT * FROM c WHERE id = 5;
```

### 11. Optimization Techniques
- Partition pruning is pushdown's biggest win — verify with EXPLAIN (`Subplans Removed`, or
  only some partitions listed).
- For foreign tables (FDW), check the remote SQL in EXPLAIN VERBOSE — unpushed quals mean
  shipping whole tables over the network.
- Pre-filter fact tables into CTE-per-branch before UNION ALL merges.

### 12. Follow-up Questions
- "Why can't the filter on the LEFT JOIN's right side be pushed below the join?" (padding rows
  semantics — ties back to Module 3)
- "How does this concept map to microservice APIs?" (filter at the source — same principle,
  wider audience answer interviewers enjoy)

---

## Chapter 5.4 — Sorting & Filtering at Scale

### 1. Why Interviewers Ask This
Sorts are the silent killer in real plans (top-N, GROUP BY, window functions, DISTINCT, merge
joins all sort). "How do you make ORDER BY cheap?" has one senior answer: don't sort — read in
order.

### 2. Core Concept
- In-memory sort: quicksort within `work_mem`. Bigger → **external merge sort** on temp files
  (`Sort Method: external merge Disk: ...`).
- **Top-N heapsort**: `ORDER BY ... LIMIT k` keeps only k rows in a heap — tiny memory, huge win;
  but only if the sort node knows about the limit.
- **Best sort is no sort**: a B+Tree index on the ORDER BY prefix (matching directions,
  compatible collation) streams rows pre-sorted; with LIMIT it reads k entries and stops.
- Incremental sort (PG13+): input sorted by (a) and you need (a,b) — sorts small per-a batches.
- Filtering at scale: cheapest predicate order is the planner's job, but *shape* is yours —
  sargable predicates (Module 4.6), pre-filtering before expensive functions
  (`WHERE cheap_cond AND expensive_fn(...)`), avoiding row-by-row regex over billions
  (trigram index, generated columns).

### 3. Internal Working
External sort: produce sorted runs of work_mem size → merge runs (multi-way); cost ≈ read+write
data × passes. Parallel sorts split by workers then merge. `DISTINCT`/`GROUP BY` choose
HashAggregate (no order, memory-bound, spillable PG13+) vs Sort+Group (ordered, index-friendly).
Collation matters: `ORDER BY text_col` under ICU/libc locales is expensive comparison-wise and
must match the index's collation to reuse it (`COLLATE "C"` indexes for byte order).

### 4. Visualization (ASCII)
```
ORDER BY created DESC LIMIT 20:
without index: scan 300M rows → top-N heap (keep 20) → 20      [reads everything]
with (created DESC) index:  read 20 leaf entries → done        [reads 20 + descent]

External merge sort (work_mem=64MB, data=6GB):
pass1: 96 sorted runs of 64MB → disk
pass2: merge 96 runs → output          Disk traffic ≈ 2×6GB (plus reread)
EXPLAIN: "Sort Method: external merge  Disk: 6291456kB" ← the smoking gun
```

### 5. Real Production Example
"Recent activity" endpoint sorting a user's merged events: fine at 1k events, times out for
power users with 2M. Plan shows external sort. Fix: index `(user_id, created_at DESC)` on each
source, per-branch LIMIT before merge, keyset pagination — sort nodes vanish. The pattern
(indexed order + limit pushdown + merge) is the standard senior answer for any feed.

### 6. Common Interview Questions
- "How does the database sort data that doesn't fit in memory?"
- "How do you make `ORDER BY created_at DESC LIMIT 20` O(20)?"
- "GROUP BY: hash vs sort aggregation — trade-offs and how to influence it?"
- "Why did DISTINCT add 30s to this query?" (dedup = sort/hash over everything)

### 7. Common Mistakes
- Raising work_mem globally to silence spills (per-node × per-connection multiplication → OOM).
- Index exists but unusable for the sort: direction mismatch, expression mismatch, collation
  mismatch, or a bitmap scan discarded the order.
- Sorting wide rows (`SELECT *`) when only keys are needed — sort payload matters; sort ids,
  join details after.
- DISTINCT slapped on to fix join multiplication (Module 3) — pay dedup forever.

### 8. Best Practices
- Feed sorts from indexes for anything user-facing; reserve real sorts for batch/analytics.
- Sort narrow: order by keys, fetch wide rows afterwards (deferred join / late row lookup).
- Set work_mem per-session for known heavy jobs (`SET LOCAL work_mem='512MB'` in the report
  transaction), not globally.

### 9. Coding Questions
1. Rewrite wide sort as deferred join:
   `SELECT * FROM posts ORDER BY score DESC LIMIT 20` on a 300-column-ish table →
   `SELECT p.* FROM posts p JOIN (SELECT id FROM posts ORDER BY score DESC LIMIT 20) t USING (id) ORDER BY p.score DESC;`
   Explain when this wins (payload width × spill).
2. Given `GROUP BY user_id` over 2B rows with 50M groups: estimate hash-agg memory, decide
   hash vs sort strategy, and propose the pre-aggregated alternative.

### 10. SQL Examples
```sql
-- Diagnose spills
EXPLAIN (ANALYZE, BUFFERS) SELECT ... ORDER BY ...;
-- "Sort Method: quicksort Memory: 25kB"        good
-- "Sort Method: top-N heapsort Memory: 26kB"   good (LIMIT)
-- "Sort Method: external merge Disk: 480MB"    fix me

-- Session-scoped memory for a legit big sort
BEGIN; SET LOCAL work_mem = '512MB';
COPY (SELECT ... ORDER BY ...) TO STDOUT;
COMMIT;

-- Index-fed order, mixed directions
CREATE INDEX ON posts (user_id, score DESC, id DESC);
SELECT * FROM posts WHERE user_id=42 ORDER BY score DESC, id DESC LIMIT 20;
```

### 11. Optimization Techniques
- Incremental sort exploitation: index on (a), ORDER BY a,b — near-free.
- `COLLATE "C"` (or ICU deterministic) indexes for machine-sorted text (ids, codes) — faster
  compares, index/sort reuse.
- Parallel query for honest big sorts/aggregations: check workers actually launched.

### 12. Follow-up Questions
- "Why does the same ORDER BY use the index with LIMIT 10 but sort with LIMIT 100000?"
  (cost crossover: random-ish index reads × N vs one scan+sort)
- "Top 20 posts per user for all users — why is this harder than global top 20, and what are
  the two plans?" (window sort vs per-key lateral probes — Module 2/4 tie-in)

---

## Chapter 5.5 — Pagination (OFFSET vs Keyset)

### 1. Why Interviewers Ask This
Every list endpoint paginates, and OFFSET pagination is the most common self-inflicted
performance wound in production. This is a guaranteed API-design + DB question at Stripe/Meta.

### 2. Core Concept
- **OFFSET/LIMIT**: `... ORDER BY x LIMIT 20 OFFSET 100000` — the executor must **produce and
  discard** 100,000 rows first. Cost grows linearly with page depth; deep pages = O(offset).
  Also *unstable*: concurrent inserts/deletes shift rows between pages (skipped/duplicated items).
- **Keyset (cursor/seek) pagination**: remember the last row's sort key; next page =
  `WHERE (x, id) < (last_x, last_id) ORDER BY x DESC, id DESC LIMIT 20` — a pure index descent:
  O(page size) at any depth, and stable under concurrent writes.
- Requirements: deterministic total order (unique tiebreaker column!), an index matching it, and
  an opaque cursor in the API (encode the keyset, don't expose raw columns).
- Trade-off: no "jump to page 47" (offer filters/date-jumps instead), and bidirectional paging
  needs the reversed condition.

### 3. Internal Working
OFFSET plan: Index Scan → Limit node that *counts off* offset rows (they're fully fetched —
heap and all) then emits 20. Keyset plan: the composite predicate `(x,id) < (a,b)` is a
**row-value comparison** that maps directly to a B+Tree position — descend once, read 20 leaf
entries. This is why Postgres row-value syntax matters (MySQL 8 optimizes it too; otherwise
expand to `x < a OR (x = a AND id < b)`).

### 4. Visualization (ASCII)
```
OFFSET 100000 LIMIT 20:
index ▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶[discard 100,000 rows]▶[emit 20]
page 1: 3ms   page 500: 90ms   page 5000: 1.4s  (and heap-fetches all discards)

Keyset  WHERE (created,id) < ('2026-06-01T10:31', 88123):
index ──descend to key──▶[emit 20]      any page: 3ms

Stability under concurrent insert:
OFFSET: new row shifts everything → item seen twice on next page
keyset: position anchored to a value → unaffected
```

### 5. Real Production Example
Public API at a Stripe-like company: `GET /v1/charges?page=4000` from a crawler = worst query in
the fleet. Migration to cursor pagination (`starting_after=<opaque id>`) — exactly what Stripe's
real API does — made page depth irrelevant and killed the incident class. Also the standard
infinite-scroll answer for feeds at Meta.

### 6. Common Interview Questions
- "Why does OFFSET get slower with depth? Fix it." (guaranteed)
- "Design pagination for an API — what's in the cursor?"
- "What breaks with OFFSET pagination under concurrent writes?"
- "How do you paginate a non-unique sort key?" (tiebreaker in key and index)
- "When is OFFSET acceptable?" (small bounded depth, admin UIs, jump-to-page requirement)

### 7. Common Mistakes
- Keyset without a unique tiebreaker → skipped/duplicated rows on ties.
- Cursor as raw `WHERE id < ?` while sorting by a different column (key must be the full sort key).
- Expanded OR form without row-value comparison in engines that then can't use the index cleanly.
- Returning total page count (requires COUNT of everything — see 5.6; return `has_more` instead).

### 8. Best Practices
- Keyset by default for anything user-scrollable; index = exactly the sort key including
  tiebreaker.
- Opaque, signed cursors (base64 of keyset) — API stability + no client-forged positions.
- Deep-export use cases: don't paginate — stream (server-side cursor, COPY) or snapshot to
  object storage.

### 9. Coding Questions
1. Write page-1 and page-N queries for a feed ordered by `(score DESC, created_at DESC, id
   DESC)` with its index, plus the previous-page query.
2. Design the cursor payload for a filtered list (`status='paid'` + sort key) and explain why
   filters must be inside the cursor or re-validated.

### 10. SQL Examples
```sql
CREATE INDEX ON orders (user_id, created_at DESC, id DESC);

-- page 1
SELECT * FROM orders WHERE user_id = 42
ORDER BY created_at DESC, id DESC LIMIT 20;

-- next page (cursor = last row's (created_at, id))
SELECT * FROM orders
WHERE user_id = 42
  AND (created_at, id) < ('2026-06-01 10:31:00+00', 88123)
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- previous page (reverse, then re-sort in app or wrap)
SELECT * FROM (
  SELECT * FROM orders
  WHERE user_id = 42 AND (created_at, id) > ('2026-06-01 10:31:00+00', 88123)
  ORDER BY created_at ASC, id ASC LIMIT 20
) t ORDER BY created_at DESC, id DESC;
```

### 11. Optimization Techniques
- Row-value comparisons `(a,b) < (?,?)` — index-perfect in Postgres; verify the plan.
- `has_more` via LIMIT k+1 (fetch one extra) instead of COUNT.
- For hybrid needs (page numbers + speed), precompute page anchors periodically
  (every 1000th key) and keyset from the nearest anchor.

### 12. Follow-up Questions
- "How does this work across shards?" (query k from each shard by keyset, merge-heap, return k;
  cursor stores per-shard keys — Module 7 tie-in)
- "User re-sorts by a different column — what happens to your cursor design?" (cursor is
  sort-specific; new sort = new cursor space + supporting index decision)

---

## Chapter 5.6 — COUNT Optimization

### 1. Why Interviewers Ask This
"Why is COUNT(*) slow in Postgres?" is a top-5 senior screen question because the correct
answer requires MVCC understanding, and the fix requires product thinking (do you even need the
exact number?).

### 2. Core Concept
`SELECT count(*) FROM big_table` is slow in Postgres because **MVCC visibility lives in the
rows**: no central "row count" is maintained per snapshot, so the executor must visit every row
(heap, or index+visibility-map) and test visibility. It's O(N) by design — not a bug.

The decision tree (memorize):
- **Exact count of everything** → estimated count from stats
  (`pg_class.reltuples`) is almost always what the product needs.
- **Exact filtered count, small result** → normal indexed count is fine.
- **Big filtered count, repeated** → **counter table/rollup** maintained transactionally or
  async (with reconciliation).
- **Approximate distinct** → HyperLogLog.
- **Pagination totals** → don't. `has_more`, or "about 1,200 results" (estimate from EXPLAIN).
- `count(*)` vs `count(col)` vs `count(distinct col)`: rows vs non-null vs distinct-non-null;
  `count(1)` = `count(*)` (same plan — kill that myth in the interview).

### 3. Internal Working
Index-only-scan counting still checks the visibility map per page (all-visible pages counted
from the index alone; others fetch heap). After heavy churn, VM coverage drops → counts slow
until VACUUM. MySQL InnoDB has the same O(N) property (MyISAM's free count is the historical
confusion). Column stores / Redshift-style engines keep per-block metadata → near-free counts.
Estimated counts: planner's `rows` for arbitrary predicates via
`EXPLAIN (FORMAT JSON)` — good for "~how many."

### 4. Visualization (ASCII)
```
count(*) on 800M rows:
heap: [page][page][page]... visit ALL, test visibility per row  → minutes
index-only: [leaf][leaf]... + VM lookup per page                → better, still O(N)

counter table:
writes ─┬─▶ orders                          read: SELECT n FROM counters
        └─▶ UPDATE counters SET n=n+1              WHERE key='orders:paid'   → 0.1ms
             (same txn, or async+reconcile)
tradeoff: hot-row contention on the counter ← shard the counter into K rows if hot
```

### 5. Real Production Example
Dashboard tile "Total orders: 84,213,991" recomputed per page view = a minute-long seq scan per
load. Fixes shipped in order: cached count (5-min TTL) → counter table with async increments +
nightly reconciliation → product change to "84.2M". The interview wants you to walk exactly that
escalation, including asking "does anyone need the last digit?"

### 6. Common Interview Questions
- "Why is COUNT(*) O(N) in Postgres? Isn't there an index?" (MVCC visibility answer)
- "Fast approximate row count — how?" (reltuples; EXPLAIN rows)
- "Design a correct-enough live counter for likes at Instagram scale." (sharded counters,
  batched flush, reconciliation)
- "COUNT(*) vs COUNT(1) vs COUNT(col)?"

### 7. Common Mistakes
- Adding an index "to speed up count(*)" with no predicate — barely helps without VM hygiene,
  never changes O(N).
- Transactional counter on one hot row at high write rates → lock convoy (shard it).
- Exact totals in paginated APIs (double the cost of every list call).
- Using reltuples right after bulk load without ANALYZE (stale).

### 8. Best Practices
- Ask "what precision does the product need?" before optimizing — the senior move.
- Counter tables: increment in-transaction for correctness-critical, async batched for
  high-volume; either way schedule reconciliation.
- Keep autovacuum healthy for index-only counting paths.

### 9. Coding Questions
1. Implement a sharded counter: table `counters(key, shard, n)`, increment =
   `ON CONFLICT ... DO UPDATE` on random shard, read = `SUM(n)`; explain the contention math
   (K shards ≈ K× less conflict).
2. Return an estimated count for an arbitrary filtered query from `EXPLAIN (FORMAT JSON)` in
   application code (parse Plan Rows).

### 10. SQL Examples
```sql
-- Instant estimate (whole table)
SELECT reltuples::bigint FROM pg_class WHERE relname = 'orders';

-- Counter table
CREATE TABLE counters (key text, shard int, n bigint NOT NULL DEFAULT 0,
                       PRIMARY KEY (key, shard));
-- increment (random shard 0..7)
INSERT INTO counters VALUES ('orders:paid', floor(random()*8)::int, 1)
ON CONFLICT (key, shard) DO UPDATE SET n = counters.n + 1;
-- read
SELECT sum(n) FROM counters WHERE key = 'orders:paid';

-- has_more instead of total
SELECT * FROM orders WHERE user_id=42 ORDER BY id DESC LIMIT 21;  -- 21st row ⇒ has_more
```

### 11. Optimization Techniques
- `count(*) FILTER (WHERE ...)` to get many counts in one scan instead of N queries.
- HLL for distinct counts across time windows (mergeable sketches).
- For batch analytics, run counts on the replica/warehouse, never the primary.

### 12. Follow-up Questions
- "Your async counter drifted 2% — detect, fix, prevent." (reconciliation diff job, idempotent
  consumers, versioned events)
- "Why is count fast in ClickHouse/BigQuery?" (columnar metadata, no per-row MVCC visibility)

---

## Chapter 5.7 — The N+1 Query Problem

### 1. Why Interviewers Ask This
The most common real performance bug in application code, and a favorite because it spans ORM,
SQL, and system thinking. "Page is slow, DB is idle-ish, APM shows 400 queries per request" —
they want the instant diagnosis.

### 2. Core Concept
N+1: fetch N parent rows (1 query), then loop fetching children per parent (N queries).
Each query is fast; the *request* dies of round trips (N × (network RTT + parse/plan/execute)).

Fixes, in order of preference:
1. **Batch load**: one query with `WHERE parent_id = ANY($ids)` (or `IN`), group in app —
   what ORM "eager loading" does (`includes`/`selectinload`/DataLoader).
2. **JOIN** parent+child in one query (beware row multiplication with multiple child
   collections — Module 3; often better as separate batched queries per collection).
3. **Lateral top-k per parent** when you need only a few children each.
4. **Denormalize/cache** for read-hot aggregates (child counts on the parent).

GraphQL note: resolvers are N+1 factories → **DataLoader pattern** (batch + per-request cache)
is the expected vocabulary.

### 3. Internal Working
Why 400 tiny queries ≫ 1 medium query: per-query cost = RTT (0.5–2ms in-VPC) + parse/plan
(unless prepared) + executor startup + row fetch. 400 × ~2ms ≈ 800ms of pure overhead before
any real work — while one `ANY($ids)` query is a single round trip resolving to one index
bitmap/loop over 400 keys. Also: connection-pool occupancy scales with query count → N+1
under load exhausts pools (Module 11 tie-in).

### 4. Visualization (ASCII)
```
N+1:                                  batched:
app ──q──▶ db   (users: 1 query)      app ──q──▶ db   users
app ──q──▶ db   orders u1             app ──q──▶ db   orders WHERE user_id=ANY([u1..u100])
app ──q──▶ db   orders u2                 2 round trips total ✔
 ...×100                              app-side: group rows by user_id
102 round trips ✖ (~200ms network alone)

timeline per request:  |q|q|q|q|q|q|q|...      |query|query|
                        └─ death by a thousand RTTs
```

### 5. Real Production Example
Uber-style trip-history screen: ORM lazily loads `trip.driver`, `trip.payment`, `trip.city` →
1 + 3N queries; at N=50 that's 151 queries per screen. APM flamegraph shows the staircase.
Fix: eager-load the three associations (3 batched queries) + a covering index each; p95 from
1.8s → 90ms. Every company has this incident; interviewers just change the nouns.

### 6. Common Interview Questions
- "What's the N+1 problem and how do you detect it in production?" (APM query counts per
  request; `pg_stat_statements` calls column exploding)
- "Eager loading vs JOIN — when is each right?" (multiple hasMany collections multiply in a
  join; batched selects keep grains separate)
- "How does DataLoader solve N+1 in GraphQL?" (per-tick batch + cache by key)
- "Fix N+1 without touching the ORM query code?" (harder: view/denormalized read model/cache;
  usually the answer is 'touch the code')

### 7. Common Mistakes
- "Fixing" with one giant JOIN across three one-to-many collections → cartesian blowup
  (rows = orders × items × shipments per user).
- Batch queries with 100k-id IN lists (plan/parse bloat, parameter limits) — chunk the batches.
- Caching each child individually (N cache round trips — same problem, new backend; use MGET).
- Not noticing write-path N+1: per-row UPDATE loops instead of one set-based UPDATE.

### 8. Best Practices
- Turn on ORM lazy-load warnings/strict mode in dev; assert max-queries-per-request in tests.
- Standard access patterns: batch by key list, chunked `ANY($1)`, prepared statements.
- For aggregates-of-children shown in lists (counts, latest item), maintain them on the parent
  (denormalized) instead of loading children at all.

### 9. Coding Questions
1. Given `users` page (100 rows) needing latest order + order count each: write the two batched
   queries (lateral top-1 with `= ANY`, grouped count with `= ANY`) and the app-side merge.
2. Rewrite a per-row update loop (`for id in ids: UPDATE ... WHERE id=?`) as one statement with
   `unnest($ids, $values)`.

### 10. SQL Examples
```sql
-- Batch children for a page of parents
SELECT * FROM orders WHERE user_id = ANY($1::bigint[]) ORDER BY user_id, created_at DESC;

-- Batch latest-order-per-parent (lateral over the id list)
SELECT o.* FROM unnest($1::bigint[]) AS u(id)
JOIN LATERAL (
  SELECT * FROM orders o WHERE o.user_id = u.id
  ORDER BY created_at DESC LIMIT 1
) o ON true;

-- Set-based write instead of update loop
UPDATE products p SET price_cents = v.price
FROM (SELECT unnest($1::bigint[]) AS id, unnest($2::int[]) AS price) v
WHERE p.id = v.id;
```

### 11. Optimization Techniques
- Cap batch sizes (~1–5k keys) and parallelize chunks if needed.
- Prepared statements + pooler to amortize parse/plan for the remaining queries.
- Request-scoped memoization (DataLoader cache) to dedupe repeated key loads within one request.

### 12. Follow-up Questions
- "Your fix made one query slow instead of 400 fast ones — how do you know you won?" (total
  latency + pool occupancy + DB CPU; measure request-level, not query-level)
- "Same problem calling a microservice per item — carry the lesson over." (batch APIs, the
  N+1 lesson generalizes; interviewers love this bridge)

---

# Module 5 — Practice Problems

## Easy (5)
1. In an EXPLAIN ANALYZE node: `(cost=0.43..8.45 rows=1 width=8) (actual time=0.031..0.032
   rows=412 loops=850)` — extract every fact and name the concern.
2. Why is `SELECT count(*)` slow on an 800M-row Postgres table, in two sentences including the
   word "visibility"?
3. Convert to keyset pagination: `SELECT * FROM posts ORDER BY created_at DESC LIMIT 20 OFFSET
   4000` (include the tiebreaker and the index).
4. `Sort Method: external merge Disk: 2.1GB` — give three distinct remedies in preference order.
5. A request issues 1 query for 50 carts + 50 queries for items. Write the single batched item
   query and describe the app-side regrouping.

## Medium (5)
6. A prepared statement flipped to a generic plan on its 6th execution and latency went 10x for
   skewed parameters. Explain the mechanism and give three fixes with trade-offs.
7. Query joins events (1B, partitioned by day) to users, filters `day BETWEEN ...` inside a
   subquery wrapped by a window function. Partitions aren't pruned. Explain why and restructure.
8. Design "search results: about 12,400 items, pages of 20, infinite scroll" — cursor format,
   the has_more trick, the estimate source, and the index.
9. `pg_stat_statements` shows a statement with calls=48M/day, mean=0.4ms, total=5.3h/day.
   Nothing is "slow." Argue whether and how to optimize (N+1 batch consolidation, caching,
   prepared statements — total-time thinking).
10. A nightly report sets work_mem='2GB' globally via ALTER SYSTEM "so sorts don't spill."
    Enumerate the failure modes and rewrite the change correctly (SET LOCAL in the job).

## Hard (5)
11. You get this plan shape: NestedLoop(est 40 rows) → over HashJoin(est 39, actual 2.2M) →
    over two SeqScans with accurate estimates. The misestimate is in the join selectivity
    itself. What causes join-selectivity misestimates (FK skew, cross-column correlation,
    non-uniform key distribution), how do you confirm, and what are your options when extended
    statistics can't express it? (rewrite: pre-aggregate/temp table with ANALYZE; pg_hint_plan
    last resort.)
12. Build the plan-regression safety net for a deploy pipeline: pg_stat_statements baselines,
    query fingerprinting, canary EXPLAIN against production-stats snapshot, auto_explain
    sampling in prod, alert thresholds. Specify what each layer catches that the others miss.
13. An API must serve "page 5000" (regulatory export). OFFSET is banned. Design anchored
    pagination: precomputed keyset anchors every N rows (materialized, refreshed), anchor lookup
    + keyset from anchor, staleness math, and the fallback when anchors are stale.
14. COUNT problem at Instagram-likes scale: 500k increments/sec on hot posts. Design the full
    pipeline: client dedup, sharded in-memory accumulation, batched DB flush, exact
    reconciliation from the event log, read path with staleness bound. State what each layer
    tolerates and what invariant survives crashes at every point.
15. A 14-way reporting join is planner-nondeterministic (GEQO) and occasionally 100x slow.
    Options: raise geqo_threshold/join_collapse_limit (planning-time explosion?), decompose into
    materialized stages with ANALYZE between, or precompute star-schema style. Design the
    decomposition, argue where the stage boundaries go and prove the plan is now stable.

---

*Next: [Module 6 — Transactions & Concurrency](module-06-transactions-concurrency.md)*

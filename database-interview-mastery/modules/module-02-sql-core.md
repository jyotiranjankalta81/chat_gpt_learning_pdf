# MODULE 2 — SQL Core

> The screening-round module. Senior candidates fail SQL screens not on syntax but on
> **logical execution order, NULL semantics, and window functions**. Those three carry this module.

Chapters:
2.1 Logical Query Execution Order (SELECT, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT, DISTINCT, CASE)
2.2 Subqueries, Correlated Subqueries, EXISTS / IN / ANY / ALL
2.3 CTEs & Recursive CTEs
2.4 Views & Materialized Views
2.5 UNION vs UNION ALL (Set Operations)
2.6 Window Functions (the interview kingmaker)
2.7 Aggregate, Date & String Functions

---

## Chapter 2.1 — Logical Query Execution Order

### 1. Why Interviewers Ask This
80% of "why is this query wrong?" screen questions reduce to execution order: why you can't use
a SELECT alias in WHERE, why HAVING exists, how DISTINCT interacts with ORDER BY. It's also the
mental model you need to reason about what the optimizer may rearrange.

### 2. Core Concept
SQL is written `SELECT ... FROM ... WHERE ...` but **evaluated logically** as:

```
FROM / JOIN  →  WHERE  →  GROUP BY  →  HAVING  →  SELECT (expressions, aliases)
→  DISTINCT  →  ORDER BY  →  LIMIT / OFFSET
```

Consequences you must be able to recite:
- **WHERE** runs before grouping → cannot reference aggregates (`WHERE count(*) > 5` is invalid) → that's **HAVING**'s job.
- **SELECT aliases** don't exist yet in WHERE/GROUP BY/HAVING (Postgres allows them in GROUP BY/ORDER BY as an extension — don't rely on it in interviews).
- **ORDER BY** runs after SELECT → it *can* use aliases and, with DISTINCT, may only order by selected expressions.
- **LIMIT without ORDER BY** returns *arbitrary* rows — a classic trap.
- **WHERE filters rows; HAVING filters groups.** Put every non-aggregate condition in WHERE (it prunes before the expensive grouping).

**CASE** is an expression (not control flow), usable anywhere an expression goes — including
inside aggregates (`SUM(CASE WHEN ... THEN 1 ELSE 0 END)` = conditional counting, better written
in Postgres as `COUNT(*) FILTER (WHERE ...)`).

### 3. Internal Working
The planner turns logical order into a physical plan and may reorder aggressively as long as
results are equivalent: predicates are pushed down below joins, `LIMIT` can stop an index scan
early (top-N), `DISTINCT`/`GROUP BY` become HashAggregate or Sort+Unique, `ORDER BY` is satisfied
either by an explicit Sort node (spills to disk beyond `work_mem`) or **for free by an index**
that already returns rows in order. `ORDER BY x LIMIT 10` with an index on `x` = read 10 index
entries and stop — this powers all fast pagination (Module 5).

### 4. Visualization (ASCII)
```
written order            logical evaluation            physical plan (example)
SELECT c, count(*)   ┌─▶ FROM orders                    Limit(10)
FROM orders          │   WHERE status='paid'              └─ Sort DESC / or IndexScan
WHERE status='paid'  │   GROUP BY c                          └─ HashAggregate
GROUP BY c           │   HAVING count(*)>5                      └─ SeqScan
HAVING count(*)>5    │   SELECT c, count(*)                        Filter: status='paid'
ORDER BY 2 DESC      │   ORDER BY count DESC
LIMIT 10             └── LIMIT 10
alias visibility: WHERE ✖ │ GROUP BY ✖(std) │ HAVING ✖ │ ORDER BY ✔
```

### 5. Real Production Example
A Netflix-style dashboard query: "top 10 titles by completed plays yesterday." The difference
between `WHERE event_date = yesterday` (prunes billions of rows before aggregation, hits the
partition) and putting the date check in HAVING-adjacent logic (aggregating everything, then
filtering) is minutes vs milliseconds. Filter-early is not style — it's the whole game.

### 6. Common Interview Questions
- "Why does `WHERE total_spend > 100` fail when `total_spend` is a SELECT alias?"
- "Difference between WHERE and HAVING? Which is faster for a non-aggregate condition and why?"
- "What does LIMIT 1 without ORDER BY return?"
- "Count paid vs unpaid orders in one query." (CASE/FILTER inside aggregates)
- "What's the logical order of clause evaluation?" (recite it)

### 7. Common Mistakes
- `HAVING status = 'paid'` — works if `status` is grouped, but forces the condition after
  aggregation; belongs in WHERE.
- `SELECT DISTINCT user_id ORDER BY created_at` — invalid/ambiguous: which `created_at` for a
  deduped user? (Postgres errors; fix with GROUP BY + aggregate, or `DISTINCT ON`.)
- Relying on implicit ordering ("it always came back sorted") — plans change, order changes.
- `WHERE x <> 'a'` silently dropping NULL rows (NULL comparisons are UNKNOWN → filtered).
  NULL handling: use `IS DISTINCT FROM` for null-safe inequality.

### 8. Best Practices
- Push every sargable condition into WHERE; reserve HAVING strictly for aggregate conditions.
- Always pair LIMIT with a **deterministic** ORDER BY (add a unique tiebreaker column: `ORDER BY created_at DESC, id DESC`).
- Prefer `COUNT(*) FILTER (WHERE ...)` over `SUM(CASE ...)` in Postgres — clearer, same plan.
- Know `DISTINCT ON (col)` (Postgres): "one row per key, pick which by ORDER BY" — the idiomatic
  greatest-n-per-group tool.

### 9. Coding Questions
1. One scan, one row per country: total orders, paid orders, paid ratio, only countries with
   >1000 orders, top 10 by paid ratio.
2. "Latest order per user" three ways: `DISTINCT ON`, window function `ROW_NUMBER`, and a
   correlated subquery — and rank them by expected performance with an index on `(user_id, created_at DESC)`.

### 10. SQL Examples
```sql
-- Conditional aggregation + correct clause placement
SELECT u.country,
       count(*)                                   AS orders,
       count(*) FILTER (WHERE o.status = 'paid')  AS paid_orders,
       round(count(*) FILTER (WHERE o.status='paid')::numeric / count(*), 3) AS paid_ratio
FROM orders o JOIN users u ON u.id = o.user_id
WHERE o.created_at >= now() - interval '30 days'     -- row filter: BEFORE grouping
GROUP BY u.country
HAVING count(*) > 1000                                -- group filter: aggregates only
ORDER BY paid_ratio DESC
LIMIT 10;

-- DISTINCT ON: latest order per user (Postgres idiom)
SELECT DISTINCT ON (user_id) user_id, id, created_at
FROM orders
ORDER BY user_id, created_at DESC;

-- CASE as expression: bucketing
SELECT CASE WHEN total_cents < 1000  THEN 'small'
            WHEN total_cents < 10000 THEN 'medium'
            ELSE 'large' END AS bucket,
       count(*)
FROM orders GROUP BY 1;
```

### 11. Optimization Techniques
- Make ORDER BY free: index matching the sort (`(created_at DESC, id DESC)`) lets
  `ORDER BY ... LIMIT k` read k entries and stop.
- Filter before aggregating; aggregate before joining when the join is only for labels
  (aggregate the fact table, then join dimension tables).
- Watch `Sort Method: external merge Disk:` in EXPLAIN ANALYZE — raise `work_mem` for that
  session or add the index.

### 12. Follow-up Questions
- "Your GROUP BY query spills to disk — what are your options?" (work_mem, pre-filter,
  index-ordered GroupAggregate, pre-aggregated rollup)
- "Why can `LIMIT` change which join algorithm wins?" (startup cost vs total cost — nested loop
  streams first rows early; hash join must build first)
- "How would you make `paid_ratio` per country available at 10ms p99?" (rollup table /
  materialized view — Chapter 2.4)

---

## Chapter 2.2 — Subqueries, Correlated Subqueries, EXISTS / IN / ANY / ALL

### 1. Why Interviewers Ask This
They test two things: can you express "rows that have / don't have related rows" correctly, and
do you know the **NOT IN + NULL** landmine and the performance difference between correlated and
uncorrelated forms.

### 2. Core Concept
- **Scalar subquery**: returns one value — usable anywhere an expression goes.
- **Uncorrelated subquery**: independent of the outer row; executed once.
- **Correlated subquery**: references outer-row columns; *logically* re-executed per outer row.
- **EXISTS (SELECT 1 ...)**: true if the subquery returns ≥1 row; stops at the first match
  (semi-join). `NOT EXISTS` = anti-join.
- **IN (subquery)**: membership test. **`NOT IN` with any NULL in the subquery returns zero
  rows** — because `x <> NULL` is UNKNOWN, so no row can ever pass. The most famous SQL trap.
- **ANY/SOME**: `x = ANY(sub)` ≡ `x IN (sub)`; useful with other operators (`> ANY` = greater
  than the minimum). **ALL**: must hold vs every row (`> ALL` = greater than the maximum;
  vacuously true on empty set — second trap).

### 3. Internal Working
Postgres rewrites aggressively:
- `IN`/`EXISTS` subqueries → **semi-joins** (hash or nested-loop) — usually identical plans, so
  the "EXISTS is faster than IN" folklore is mostly false *in Postgres* (was true in old MySQL).
- `NOT EXISTS` → **anti-join** (efficient). `NOT IN` often *cannot* become an anti-join unless
  the planner proves non-nullability → materializes the subquery and probes with three-valued
  logic → slower **and** semantically dangerous.
- Correlated subqueries the planner can't decorrelate become a **SubPlan**: executed per outer
  row (O(N×cost)). EXPLAIN shows `SubPlan` — a red flag on big outer sets unless the inner probe
  is a cheap index hit or it's a *hashed* SubPlan.

### 4. Visualization (ASCII)
```
Semi-join (EXISTS/IN):                    Correlated SubPlan:
outer row ──▶ probe inner hash/index      for each of 1,000,000 outer rows:
  match found? emit once, stop              run inner query (index probe: OK,
  (never duplicates outer rows)              seq scan: catastrophe)

NOT IN with NULL:
ids in subquery: {1, 2, NULL}
x NOT IN (1,2,NULL) ⇒ x<>1 AND x<>2 AND x<>NULL
                                   └── UNKNOWN ⇒ whole predicate UNKNOWN ⇒ row dropped
RESULT: empty set, silently.  Use NOT EXISTS.
```

### 5. Real Production Example
Churn query at a Stripe-like company: "customers with no successful payment in 90 days."
Written with `NOT IN (SELECT customer_id FROM payments ...)`, it returned zero rows for a week
because one legacy payment row had `customer_id NULL` — a silent correctness incident, not a
performance one. Rewritten with `NOT EXISTS`, correct and anti-join fast.

### 6. Common Interview Questions
- "Find users with no orders" — expected: `NOT EXISTS` (or LEFT JOIN ... IS NULL), and *why not*
  `NOT IN`.
- "EXISTS vs IN — semantics and performance?"
- "When does a correlated subquery hurt, and how do you rewrite it?" (as a join or window function)
- "What does `salary > ALL (SELECT salary FROM emp WHERE dept='X')` return when dept X is empty?" (all rows — vacuous truth)

### 7. Common Mistakes
- `NOT IN` against a nullable column — the #1 trap; know it cold.
- Correlated aggregate per row (`(SELECT count(*) FROM orders o WHERE o.user_id = u.id)`) on a
  large outer table without an index on `orders(user_id)`.
- Using `IN` to deduplicate a join — `EXISTS` never multiplies rows; a JOIN does.
- Scalar subquery returning >1 row → runtime error that only appears with production data.

### 8. Best Practices
- Default to `EXISTS`/`NOT EXISTS` for presence/absence — null-safe, dup-safe, plans well.
- Rewrite per-row correlated aggregates as a grouped join or window function when reading many rows.
- `= ANY(array)` is the idiomatic Postgres way to bind a list parameter (`WHERE id = ANY($1::bigint[])`).
- Keep subqueries sargable: correlate on indexed columns.

### 9. Coding Questions
1. "Users whose *every* order is over $100" — two ways: `NOT EXISTS` (an order ≤ 100) and
   `100 < ALL (subquery)`; explain the empty-set semantics difference (users with no orders).
2. Rewrite this per-row subquery as a join:
   `SELECT u.*, (SELECT max(created_at) FROM orders o WHERE o.user_id=u.id) FROM users u;`

### 10. SQL Examples
```sql
-- Presence: users with at least one refunded order (semi-join, no duplicates)
SELECT u.* FROM users u
WHERE EXISTS (SELECT 1 FROM orders o
              WHERE o.user_id = u.id AND o.status = 'refunded');

-- Absence done safely (anti-join)
SELECT u.* FROM users u
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);

-- The trap, for contrast: returns 0 rows if ANY orders.user_id IS NULL
SELECT u.* FROM users u
WHERE u.id NOT IN (SELECT o.user_id FROM orders o);

-- Correlated → join rewrite
SELECT u.id, u.name, m.last_order_at
FROM users u
LEFT JOIN (SELECT user_id, max(created_at) AS last_order_at
           FROM orders GROUP BY user_id) m ON m.user_id = u.id;

-- ANY with an array parameter
SELECT * FROM orders WHERE status = ANY(ARRAY['paid','shipped']);
```

### 11. Optimization Techniques
- Check EXPLAIN for `SubPlan` (per-row execution) vs `Hash Semi Join`/`Hash Anti Join`
  (set-based) — rewrite until you get the latter on large inputs.
- Ensure the correlated column is the leading column of an index on the inner table.
- For "top/latest per group" prefer `DISTINCT ON` or window functions over correlated
  `= (SELECT max(...))` — one scan instead of N probes.

### 12. Follow-up Questions
- "Why can't the planner turn NOT IN into an anti-join here?" (nullable column; add NOT NULL or
  `WHERE sub.col IS NOT NULL` and re-plan)
- "The EXISTS probe is fast but runs 10M times — what now?" (decorrelate: aggregate inner once,
  hash join)
- "Semi-join vs inner join + DISTINCT — result and cost differences?" (same rows here, but
  DISTINCT pays for dedup after multiplication)

---

## Chapter 2.3 — CTEs & Recursive CTEs

### 1. Why Interviewers Ask This
CTEs test query decomposition; **recursive CTEs are the only standard SQL for hierarchies/graphs**
(org charts, category trees, dependency chains) — a fixture of Amazon/Google SQL rounds. Bonus
signal: knowing the Postgres 12 materialization change.

### 2. Core Concept
- `WITH name AS (...)` names a subquery for reuse and readability; CTEs can chain (later CTEs
  reference earlier ones).
- **Postgres ≥12**: CTEs referenced once are **inlined** (predicates push into them, indexes
  usable). Referenced multiple times, containing writes (`INSERT ... RETURNING`), or marked
  `AS MATERIALIZED` → computed once into a tuplestore. `AS NOT MATERIALIZED` forces inlining.
  Pre-12 (and lore you'll hear): CTEs were *always* optimization fences.
- **Recursive CTE** = iteration until fixpoint:

```sql
WITH RECURSIVE r AS (
  <base case / anchor>
  UNION ALL
  <recursive step referencing r>   -- runs on the PREVIOUS iteration's rows only
)
SELECT * FROM r;
```

`UNION` (vs `UNION ALL`) additionally dedups each iteration — that's how you survive cycles.

### 3. Internal Working
Executor keeps a **working table** (last iteration's rows). Each step joins the recursive term
against the working table only (not all accumulated rows), appends results to the output and
makes them the next working table; stops when an iteration yields zero rows. Total cost ≈
depth × (per-level join cost) — so an index on the join key (`parent_id`) is mandatory.
Cycle without protection = infinite loop; Postgres 14+ adds `CYCLE col SET is_cycle USING path`.

### 4. Visualization (ASCII)
```
employees(id, manager_id): reports chain of CEO(1)
iter 0 (anchor): {1}
iter 1: children of {1}        → {2,3}
iter 2: children of {2,3}      → {4,5,6}
iter 3: children of {4,5,6}    → {}  → STOP
output = 1,2,3,4,5,6 with depth/path accumulated per row

working table (small, last level only) ──join on parent_id──▶ employees (indexed)
```

### 5. Real Production Example
Amazon-style product taxonomy: "all products under 'Electronics'" where categories nest
arbitrarily deep. Recursive CTE walks category → descendants, then joins products. At very high
read volume, teams precompute a **closure table** or use `ltree`/materialized paths — a follow-up
interviewers love ("what if this tree is read a million times a minute?").

### 6. Common Interview Questions
- "Employees under manager X, with depth and path." (the canonical one)
- "Detect a cycle in the reporting chain."
- "Generate a row per day for the last 30 days and left-join sales onto it" (recursive CTE or
  `generate_series` — know both; the series version is the Postgres answer).
- "Are CTEs optimization fences?" (version-aware answer = senior signal)

### 7. Common Mistakes
- `UNION ALL` on cyclic data → infinite recursion (killed only by memory/`statement_timeout`).
- Filtering *outside* the recursion what could be filtered *inside* (walk the whole tree, then
  discard — push predicates into the recursive term when semantics allow).
- Assuming the recursive term can reference `r` twice or use aggregation over it — not allowed.
- Using a chain of CTEs where each one scans a huge table separately instead of reusing one scan.

### 8. Best Practices
- Always carry `depth` and a `path` array — costs little, answers the follow-ups (ordering,
  cycle check via `id = ANY(path)`).
- Cap depth defensively: `WHERE depth < 20` in the recursive term.
- Name CTEs like functions (`active_users`, `daily_totals`) — interviewers grade readability.
- Know the alternatives for hot hierarchies: closure table, materialized path, `ltree`.

### 9. Coding Questions
1. Org chart: all reports of employee 42 with depth and full path, cycle-safe.
2. Running dependency resolution: given `tasks(id, depends_on)`, output a valid execution order
   (topological sort via recursive CTE with depth, order by max depth).

### 10. SQL Examples
```sql
-- Subordinates with depth & path, cycle-safe
WITH RECURSIVE reports AS (
  SELECT id, name, manager_id, 1 AS depth, ARRAY[id] AS path
  FROM employees WHERE id = 42
  UNION ALL
  SELECT e.id, e.name, e.manager_id, r.depth + 1, r.path || e.id
  FROM employees e
  JOIN reports r ON e.manager_id = r.id
  WHERE NOT e.id = ANY(r.path)          -- cycle guard
    AND r.depth < 20                    -- depth cap
)
SELECT * FROM reports ORDER BY path;

-- Calendar spine + left join (report with zero-filled days)
SELECT d::date AS day, coalesce(sum(o.total_cents), 0) AS revenue
FROM generate_series(current_date - 29, current_date, interval '1 day') d
LEFT JOIN orders o ON o.created_at::date = d::date
GROUP BY 1 ORDER BY 1;

-- Materialization control (Postgres 12+)
WITH heavy AS MATERIALIZED (SELECT ... expensive, reused 3x ...)
SELECT ... FROM heavy h1 JOIN heavy h2 ON ...;
```

### 11. Optimization Techniques
- Index the recursion join key (`employees(manager_id)`) — turns each level into index probes.
- For read-heavy trees: closure table (`ancestor, descendant, depth` rows) trades O(depth)
  recursion for O(1) lookup at write-time cost.
- Use `NOT MATERIALIZED` when a filter from the outer query should push into the CTE.

### 12. Follow-up Questions
- "This tree has 50M nodes and the query runs 10k times/sec — now what?" (closure table /
  cached subtree sets / denormalized path column)
- "How do you paginate a recursive result stably?" (order by path, keyset on path)
- "Same query in MySQL?" (MySQL 8.0 `WITH RECURSIVE` — nearly identical; know it exists)

---

## Chapter 2.4 — Views & Materialized Views

### 1. Why Interviewers Ask This
Views test whether you know the difference between an **abstraction** (view = stored query) and
a **precomputation** (matview = stored result) — and the staleness/refresh trade-off is a mini
CAP question inside SQL.

### 2. Core Concept
| | View | Materialized View |
|---|---|---|
| Storage | None — macro expanded at plan time | Real table of results on disk |
| Freshness | Always current | Stale until `REFRESH` |
| Read cost | Cost of the underlying query | Cost of reading a (indexable!) table |
| Write path | N/A (simple views auto-updatable) | Refresh: full recompute in PG |
| Use | API stability, security (column/row hiding), DRY | Expensive aggregates read often, written rarely |

### 3. Internal Working
- View: rewriter splices the view definition into the query tree, then the planner optimizes
  the *whole* thing — predicates push into the view; performance identical to writing the full
  query (footgun: stacking views 5 deep hides a monster join).
- Matview: `REFRESH MATERIALIZED VIEW` re-runs the query and swaps the heap (locks readers);
  `REFRESH ... CONCURRENTLY` diffs against the old contents using a **unique index** (required)
  and applies deltas without blocking reads — slower to run, non-blocking to readers.
  Postgres has no built-in incremental matview maintenance (unlike Oracle) — that's what
  rollup-table + trigger/CDC patterns are for.

### 4. Visualization (ASCII)
```
View:    query ──rewrite──▶ [query ⋈ view definition] ──plan──▶ execute (fresh, full cost)

Matview:                     write path            read path
 base tables ──REFRESH──▶ [stored result table] ◀──index scan, ms
                 ▲ cron/trigger                    (stale by up to refresh interval)
CONCURRENTLY: new snapshot ──diff via unique idx──▶ apply deltas (readers unblocked)
```

### 5. Real Production Example
A LinkedIn-style "profile view stats" page: counting 90 days of view events per user at request
time = OLAP query on the OLTP path. Matview (or rollup table) refreshed every 10 minutes serves
it in single-digit ms; product accepts the staleness and the UI says "updated recently." That
sentence — *the product accepted staleness* — is what interviewers want to hear.

### 6. Common Interview Questions
- "View vs materialized view — when each?"
- "Does a view improve performance?" (no — it's the same query; matviews do)
- "How do you refresh a matview without downtime?" (`CONCURRENTLY` + unique index)
- "How would you keep a matview near-real-time?" (you wouldn't — incremental rollup via
  triggers/CDC, or streaming aggregation)

### 7. Common Mistakes
- Believing views cache results.
- Matview without a unique index → `REFRESH CONCURRENTLY` fails; plain refresh blocks reads.
- View-on-view-on-view stacks where nobody can find the 12-way join anymore.
- Using matviews for data that must be fresh (inventory counts at checkout).

### 8. Best Practices
- Views for security boundaries (expose `users_public` without PII) and query DRY.
- Matviews for expensive, read-heavy, staleness-tolerant aggregates; always index them like tables.
- Schedule refreshes off-peak; monitor refresh duration growth (it's a full recompute).
- When freshness matters, prefer an incrementally-maintained rollup table.

### 9. Coding Questions
1. Create a security view exposing users without email/phone and grant a read-only role access
   to the view but not the table.
2. Build `daily_revenue` as a matview with the unique index required for concurrent refresh.

### 10. SQL Examples
```sql
-- Security view
CREATE VIEW users_public AS
SELECT id, display_name, country, created_at FROM users;
GRANT SELECT ON users_public TO analyst_role;

-- Materialized aggregate + concurrent refresh
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT created_at::date AS day,
       count(*) AS orders,
       sum(total_cents) AS revenue_cents
FROM orders GROUP BY 1;

CREATE UNIQUE INDEX ON daily_revenue (day);      -- required for CONCURRENTLY
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_revenue;

-- Incremental rollup alternative (fresh, no full recompute)
CREATE TABLE daily_revenue_rt (day date PRIMARY KEY, orders bigint, revenue_cents bigint);
INSERT INTO daily_revenue_rt VALUES (current_date, 1, 4999)
ON CONFLICT (day) DO UPDATE
SET orders = daily_revenue_rt.orders + 1,
    revenue_cents = daily_revenue_rt.revenue_cents + EXCLUDED.revenue_cents;
```

### 11. Optimization Techniques
- Index matviews on their query patterns — they're tables.
- Partition-wise refresh: split the matview per time range so only recent partitions recompute.
- If the view is hot and simple, check the plan — sometimes a covering index on the base table
  beats maintaining a matview at all.

### 12. Follow-up Questions
- "Refresh takes 30 min and runs hourly — trajectory and fix?" (incremental rollup / only
  recompute recent window)
- "How does MySQL handle this?" (no matviews — summary tables by hand)
- "Row-level security vs views for multi-tenant isolation?" (RLS policies are enforced on the
  table for all paths; views can be bypassed by direct table access)

---

## Chapter 2.5 — UNION vs UNION ALL (Set Operations)

### 1. Why Interviewers Ask This
Small topic, reliable trap: the hidden cost of deduplication, and NULL/type alignment rules.
Also a favorite in "combine data from two sources" questions.

### 2. Core Concept
- `UNION ALL`: concatenate results. No dedup. Cheap — essentially free append.
- `UNION`: concatenate **then deduplicate whole rows** (implicit DISTINCT across the combined set).
- `INTERSECT` / `EXCEPT`: rows in both / in first-not-second (also dedup by default; `ALL`
  variants exist).
- Rules: same column count, compatible types; column names come from the **first** branch;
  `ORDER BY` applies to the final combined result only.
- Set ops treat `NULL = NULL` as equal for dedup purposes (unlike `=` in WHERE) — a subtle
  interview point.

### 3. Internal Working
`UNION ALL` = Append node streaming children (and enables partition-style pruning per branch:
branches whose WHERE contradicts the outer predicate can be skipped). `UNION` = Append +
HashAggregate (or Sort+Unique) over *all* columns of the combined set — memory/spill cost
proportional to total rows. On 100M+2M rows, that dedup is the whole query cost.

### 4. Visualization (ASCII)
```
UNION ALL                       UNION
  Append ──▶ out                 HashAggregate(all cols)  ← dedup cost lives here
   ├─ scan A (stream)              └─ Append
   └─ scan B (stream)                  ├─ scan A
rows: |A|+|B|, streaming           └─ scan B
                                rows: distinct(|A|+|B|), blocking, can spill
```

### 5. Real Production Example
Uber-style "activity feed" merging `trips`, `eats_orders`, `payments` into one timeline:
`UNION ALL` with a `source` tag column, ordered by time, keyset-paginated. Using `UNION` here
would burn CPU deduplicating rows that *cannot* collide (different sources) — a real code-review
catch that interviewers simulate.

### 6. Common Interview Questions
- "UNION vs UNION ALL — difference and performance?"
- "When is UNION actually required?" (true duplicates across branches must collapse)
- "JOIN vs UNION — when each?" (JOIN widens columns; UNION stacks rows)
- "Simulate FULL OUTER JOIN with UNION" (left join UNION ALL right-anti part — MySQL <8 lacks FULL JOIN)

### 7. Common Mistakes
- Defaulting to `UNION` "to be safe" — silently deduplicates legitimate duplicate business rows
  *and* pays the sort/hash.
- Mismatched column order across branches (types align positionally — `id, name` vs `name, id`
  may still run if types coerce, returning garbage).
- Putting `ORDER BY`/`LIMIT` intended for one branch without parentheses — it binds to the whole
  set operation.

### 8. Best Practices
- Default `UNION ALL`; use `UNION` only when dedup is a stated requirement.
- Add a discriminator column (`'trip' AS source`) when merging heterogeneous rows.
- Parenthesize branches when applying per-branch ORDER BY/LIMIT.
- For "top 10 across N sources": take top 10 per branch (indexed), UNION ALL, then top 10
  overall — bounds the work.

### 9. Coding Questions
1. Merge `web_events` and `mobile_events` into one ordered, keyset-paginated feed with a source tag.
2. Given `employees_2024` and `employees_2025`, produce: joined both years (INTERSECT), left in
   2025 (EXCEPT), and explain the NULL-equality behavior if `team` is nullable.

### 10. SQL Examples
```sql
-- Heterogeneous feed
SELECT 'trip'  AS source, id, created_at, driver_id::text AS ref FROM trips   WHERE user_id = 42
UNION ALL
SELECT 'order' AS source, id, created_at, restaurant::text      FROM eats     WHERE user_id = 42
ORDER BY created_at DESC
LIMIT 20;

-- Per-branch limits done right
(SELECT * FROM trips ORDER BY created_at DESC LIMIT 10)
UNION ALL
(SELECT * FROM eats  ORDER BY created_at DESC LIMIT 10)
ORDER BY created_at DESC LIMIT 10;

-- Set difference: users active last month but not this month (churn)
SELECT user_id FROM activity WHERE month = '2026-05-01'
EXCEPT
SELECT user_id FROM activity WHERE month = '2026-06-01';
```

### 11. Optimization Techniques
- Push filters/limits into each branch (planner often does, but write it explicitly).
- Matching indexes per branch + `Merge Append` keeps the merged stream ordered without a sort.
- Replace `UNION` with `UNION ALL` + a smarter key when you can prove disjointness.

### 12. Follow-up Questions
- "The combined ORDER BY ... LIMIT is slow — how do you avoid sorting |A|+|B| rows?"
  (per-branch indexed top-k, then merge)
- "EXCEPT vs NOT EXISTS?" (EXCEPT dedups and compares whole rows with NULL-safe equality;
  NOT EXISTS is per-key and keeps duplicates)

---

## Chapter 2.6 — Window Functions

### 1. Why Interviewers Ask This
**The single highest-yield SQL topic.** Ranking, dedup, running totals, moving averages,
gaps/islands, sessionization — the entire Module 10 problem set is window functions. Screens at
Meta/Amazon/Stripe assume fluency.

### 2. Core Concept
A window function computes over a set of rows **related to the current row, without collapsing
rows** (unlike GROUP BY).

```sql
fn(...) OVER (PARTITION BY ...   -- restart per group
              ORDER BY ...       -- ordering within partition
              frame)             -- which neighbors: ROWS/RANGE BETWEEN ...
```

The functions that matter:
- **Ranking**: `ROW_NUMBER()` (unique 1,2,3), `RANK()` (ties share, gaps: 1,1,3),
  `DENSE_RANK()` (ties share, no gaps: 1,1,2). Interviewers *always* probe the difference.
- **Offsets**: `LAG(col, n)`, `LEAD(col, n)` — previous/next row's value.
- **Edges**: `FIRST_VALUE`, `LAST_VALUE` (⚠ default frame makes LAST_VALUE = current row — the
  classic trap; fix the frame), `NTH_VALUE`.
- **Aggregates as windows**: `SUM/AVG/COUNT/MIN/MAX ... OVER (...)` — running totals, moving averages.
- **Distribution**: `NTILE(n)`, `PERCENT_RANK()`, `CUME_DIST()`.

**Frames**: default with ORDER BY is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`
(peers-inclusive!). For "previous 6 rows" moving windows use
`ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`. ROWS = physical rows; RANGE = value distance;
GROUPS = peer groups.

Evaluation position: windows are computed **after WHERE/GROUP BY/HAVING, before ORDER BY/LIMIT**
→ you cannot filter on a window function directly; wrap it in a subquery/CTE (this is
`QUALIFY` in Snowflake/BigQuery — Postgres needs the wrap).

### 3. Internal Working
WindowAgg node: sort rows by `PARTITION BY, ORDER BY` (or consume an index providing that
order), then stream, maintaining per-partition state. Running aggregates are O(N); frame-based
ones may buffer the frame. Multiple window clauses with the *same* window spec share one sort;
different specs = multiple sorts — a real cost on big data. Big sorts spill to disk
(`work_mem`).

### 4. Visualization (ASCII)
```
PARTITION BY user ORDER BY day    SUM(amt) OVER (... ROWS UNBOUNDED PRECEDING)
user day amt │ running
u1   d1  10  │ 10
u1   d2  20  │ 30    ◀ state carried within partition
u1   d3   5  │ 35
u2   d1   7  │  7    ◀ state RESET at partition boundary
u2   d2   3  │ 10

RANK vs DENSE_RANK vs ROW_NUMBER on scores 90,90,80:
score  ROW_NUMBER  RANK  DENSE_RANK
 90        1        1        1
 90        2        1        1
 80        3        3        2
```

### 5. Real Production Example
Stripe-style "flag the second-and-later charge attempts on the same card within a day"
(`ROW_NUMBER() OVER (PARTITION BY card_id, day ORDER BY created_at)` > 1); Netflix-style
7-day rolling watch-hours per profile (`AVG ... ROWS 6 PRECEDING`); dedup pipelines everywhere
(`ROW_NUMBER() = 1` per business key keeps the newest record).

### 6. Common Interview Questions
- "ROW_NUMBER vs RANK vs DENSE_RANK?" (near-guaranteed)
- "Top 3 earners per department." (partition + rank + wrap)
- "Running total / 7-day moving average."
- "Compare each row to the previous one" (LAG — month-over-month growth)
- "Delete duplicates, keep newest." (ROW_NUMBER in a CTE, delete rn>1)
- "Why can't I put ROW_NUMBER() in WHERE?"

### 7. Common Mistakes
- `LAST_VALUE` with the default frame (returns current row) — fix with
  `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`.
- Filtering on the window function in the same SELECT's WHERE.
- Wrong tool for "Nth highest": `RANK()` skips values after ties; "3rd highest *salary value*"
  needs `DENSE_RANK`.
- Moving average with `RANGE` when you mean `ROWS` (peers collapse) — or vice versa for
  time-based windows with gaps.
- Forgetting `PARTITION BY` → one global window; or partitioning by an unindexed expression on
  huge data → giant sort.

### 8. Best Practices
- Name windows once: `WINDOW w AS (PARTITION BY user_id ORDER BY created_at)` then `OVER w` —
  readable and guarantees shared sorts.
- Always pick the tiebreaker consciously (`ORDER BY created_at DESC, id DESC`) — nondeterministic
  ROW_NUMBER is a real prod bug.
- For time-based moving windows with gaps, either densify with a calendar spine or use
  `RANGE BETWEEN interval '7 days' PRECEDING AND CURRENT ROW` (Postgres 11+).
- Index `(partition_cols, order_cols)` to feed WindowAgg without a sort.

### 9. Coding Questions
1. Top 3 products by revenue per category, ties included (RANK ≤ 3).
2. Month-over-month revenue growth % with LAG, handling the first month (NULLIF/COALESCE).
3. Deduplicate `users` on email keeping the most recently active row — as a DELETE.

### 10. SQL Examples
```sql
-- Top-N per group
SELECT * FROM (
  SELECT e.*, DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rnk
  FROM employees e
) t WHERE rnk <= 3;

-- Running total + 7-row moving average
SELECT day, revenue,
       SUM(revenue) OVER (ORDER BY day)                                    AS running_total,
       AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma7
FROM daily_revenue;

-- MoM growth
SELECT month, revenue,
       round(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 1) AS growth_pct
FROM monthly_revenue;

-- Dedup delete (keep newest per email)
DELETE FROM users u
USING (
  SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY last_seen DESC, id DESC) rn
  FROM users
) d
WHERE u.id = d.id AND d.rn > 1;

-- Named window (shared sort)
SELECT user_id, created_at,
       ROW_NUMBER() OVER w AS attempt_no,
       LAG(created_at) OVER w AS prev_attempt
FROM logins
WINDOW w AS (PARTITION BY user_id ORDER BY created_at);
```

### 11. Optimization Techniques
- One window spec per query where possible (shared sort); check EXPLAIN for stacked
  WindowAgg+Sort pairs.
- Pre-filter partitions before windowing (window runs after WHERE — use it).
- For top-N per group over huge tables, compare with `DISTINCT ON` / lateral top-N per key
  (`JOIN LATERAL (... ORDER BY ... LIMIT n)`) which can use the index per key instead of
  sorting everything.

### 12. Follow-up Questions
- "The window sort spills 200GB — options?" (partition pruning first, lateral per-key top-N,
  pre-aggregation, more work_mem, index-fed order)
- "How is `SUM OVER` different from a self-join running total?" (O(N) vs O(N²); pre-window-function
  interviews used the self-join — know it historically)
- "Sessionize these events with a 30-minute gap rule." (LAG + conditional flag + running SUM —
  Module 10 covers it fully)

---

## Chapter 2.7 — Aggregate, Date & String Functions

### 1. Why Interviewers Ask This
Not to test memorization — to catch three recurring bugs: **NULLs in aggregates, timezone
handling, and non-sargable function calls on indexed columns**.

### 2. Core Concept
**Aggregates**: `COUNT(*)` counts rows; `COUNT(col)` counts non-NULL; `COUNT(DISTINCT col)`
non-NULL distinct. `SUM/AVG/MIN/MAX` **ignore NULLs**; `SUM` of no rows = NULL (not 0 — wrap in
COALESCE). `AVG` of int is numeric in PG but int division bites elsewhere: `sum(a)::numeric/count(*)`.
High-value extras: `FILTER (WHERE ...)`, `string_agg`, `array_agg`, `bool_or/bool_and`,
`percentile_cont` (Module 10).

**Dates**: `timestamptz` stores UTC instant, renders in session TZ — use it, not `timestamp`.
`date_trunc('month', ts)` for bucketing; `age()/extract(epoch from ...)` for durations;
intervals do calendar math (`+ interval '1 month'` handles month lengths). Half-open ranges
(`>= start AND < end`) avoid boundary bugs and stay index-friendly.

**Strings**: `lower/upper`, `substring`, `position`, `split_part`, `concat_ws`, `trim`,
regex (`~`, `regexp_replace`), `LIKE 'abc%'` (can use btree index with `text_pattern_ops`) vs
`LIKE '%abc%'` (cannot — needs `pg_trgm` GIN). `citext` or `lower()` expression index for
case-insensitive uniqueness.

**Sargability rule**: wrapping the **column** in a function defeats the index
(`WHERE date(created_at) = '2026-01-01'` → seq scan) — move the function to the constant side or
create an expression index.

### 3. Internal Working
Aggregates run as HashAggregate (hash per group; memory-bound; can spill PG13+) or
GroupAggregate (requires sorted input — pairs beautifully with an index). `COUNT(DISTINCT)` forces
per-group dedup state — expensive; approximate alternative is HyperLogLog (`postgresql-hll`,
or `approx_count_distinct` in warehouses). Expression indexes store the computed value
(`lower(email)`, `date(created_at)`) so the function call becomes indexable.

### 4. Visualization (ASCII)
```
COUNT semantics on col = [1, NULL, 2, 2]:
COUNT(*)=4   COUNT(col)=3   COUNT(DISTINCT col)=2   SUM(col)=5   AVG(col)=5/3 (NULL ignored)

Sargability:
WHERE date(created_at) = '2026-01-01'      WHERE created_at >= '2026-01-01'
      └── f(column): index UNUSABLE          AND created_at <  '2026-01-02'
          → Seq Scan                              └── bare column: Index Scan ✔
```

### 5. Real Production Example
Timezone incident every company has: daily revenue computed with `created_at::date` (session TZ)
disagreeing with finance's UTC-based numbers around midnight boundaries → all rollups
re-specified as `date_trunc('day', created_at AT TIME ZONE 'UTC')`. And the perf twin:
`WHERE lower(email) = lower($1)` scanning 50M rows until someone adds
`CREATE INDEX ON users (lower(email))`.

### 6. Common Interview Questions
- "COUNT(*) vs COUNT(col) vs COUNT(1)?" (COUNT(1)=COUNT(*); COUNT(col) skips NULLs)
- "Why does AVG differ from SUM/COUNT here?" (NULLs in col)
- "Query all of yesterday's orders — write the WHERE." (half-open range, index-safe, TZ-explicit)
- "Case-insensitive email uniqueness — how?" (unique expression index on lower(email) or citext)
- "Why did the index stop being used when we added date()/lower()?"

### 7. Common Mistakes
- `sum(...)` returning NULL on empty sets breaking downstream math (COALESCE it).
- `BETWEEN '2026-01-01' AND '2026-01-31'` on timestamps — silently drops Jan 31 after midnight;
  use `< '2026-02-01'`.
- `timestamp` (no TZ) columns in multi-region systems.
- `COUNT(DISTINCT user_id)` over billions of rows in a dashboard (use HLL sketches / rollups).
- String concatenation with `||` where a NULL nukes the whole string (use `concat_ws`).

### 8. Best Practices
- Store instants as `timestamptz`, money as integer cents (or `numeric` — never float),
  case-insensitive text as `citext`/lower-indexed.
- Bucket with `date_trunc`, filter with half-open ranges, always state the timezone.
- `FILTER (WHERE ...)` for multi-metric single-scan queries.
- Keep predicates sargable; when you can't, create the expression index and remember it must
  match the query's expression *exactly*.

### 9. Coding Questions
1. One scan over `orders`: per month — orders, revenue, distinct buyers, refund rate,
   avg order value excluding refunds.
2. Parse `full_name` into first/last with `split_part`, flag rows that don't fit the pattern.

### 10. SQL Examples
```sql
-- Multi-metric single scan
SELECT date_trunc('month', created_at AT TIME ZONE 'UTC') AS month,
       count(*)                                            AS orders,
       coalesce(sum(total_cents), 0)                       AS revenue_cents,
       count(DISTINCT user_id)                             AS buyers,
       round(count(*) FILTER (WHERE status='refunded')::numeric / count(*), 4) AS refund_rate,
       avg(total_cents) FILTER (WHERE status <> 'refunded') AS aov_cents
FROM orders
WHERE created_at >= '2026-01-01' AND created_at < '2026-07-01'
GROUP BY 1 ORDER BY 1;

-- Sargable "yesterday" + expression index pattern
SELECT * FROM orders
WHERE created_at >= (current_date - 1)::timestamptz
  AND created_at <  current_date::timestamptz;

CREATE UNIQUE INDEX ON users (lower(email));   -- makes lower(email)=... indexable AND unique

-- String utilities
SELECT split_part(email, '@', 2)                   AS domain,
       string_agg(DISTINCT country, ', ' ORDER BY country) AS countries
FROM users GROUP BY 1;
```

### 11. Optimization Techniques
- Replace `COUNT(DISTINCT)` at scale with HLL or pre-aggregated distinct-count rollups.
- Feed GroupAggregate with an index on the GROUP BY column to skip hashing entirely for
  ordered output.
- `%text%` search → `pg_trgm` GIN index; prefix search → `text_pattern_ops` btree; full-text →
  `tsvector` GIN.

### 12. Follow-up Questions
- "Your expression index on `date(created_at)` isn't used by `date_trunc('day', created_at)` —
  why?" (expression must match exactly)
- "AVG over money in float drifted by cents — why and fix?" (binary float representation;
  numeric/integer cents)
- "How would you compute distinct daily users over a year, fast and approximately?"
  (daily HLL sketches, union them)

---

# Module 2 — Practice Problems

## Easy (5)
1. Per status, count orders in the last 7 days; only statuses with >100 orders; order by count.
   State which clause each condition belongs in and why.
2. `COUNT(*)`=1000, `COUNT(discount)`=700, `AVG(discount)`=5. What is `SUM(discount)`, and what
   happens to AVG if the NULLs were really "no discount = 0"?
3. Latest login per user: write it with `DISTINCT ON` and with `ROW_NUMBER`.
4. Explain the output difference of RANK, DENSE_RANK, ROW_NUMBER over salaries 100, 100, 90, 80.
5. Rewrite non-sargable to sargable: `WHERE year(created_at)=2026 AND lower(status)='paid'`.

## Medium (5)
6. Users who ordered in May 2026 but not June 2026 — solve twice: EXCEPT and NOT EXISTS; explain
   the duplicate/NULL semantics difference.
7. 7-day *time-based* moving average of daily revenue where some days have no rows — produce
   correct values (calendar spine or RANGE frame; explain why plain `ROWS 6 PRECEDING` is wrong).
8. Category tree: all descendant categories of id=5 with depth and path, cycle-safe; then
   count products per *subtree*.
9. A report uses `UNION` across 6 monthly tables and takes minutes. Diagnose (dedup sort over
   everything) and fix (UNION ALL + why it's safe, or partitioned table).
10. Write a DELETE that removes duplicate `payments` rows sharing `idempotency_key`, keeping the
    earliest, and explain why you partition by the key and order by `created_at, id`.

## Hard (5)
11. Percent of each department's payroll earned by its top earner, one scan, no self-join
    (window SUM per dept + window MAX or RANK; handle ties).
12. Given `events(user_id, ts)`, compute per user the longest streak of consecutive *days* with
    activity (dedup to days, LAG/day-diff, gap flag, running group id, count — write it fully).
13. A matview refresh (45 min, hourly) powers a customer-facing dashboard needing <2 min
    staleness. Design the replacement: incremental rollup DDL, the upsert on write path, the
    backfill, and the reconciliation query proving correctness.
14. `WHERE id NOT IN (subquery)` returns 0 rows in prod, correct rows in staging. Explain the
    exact three-valued-logic evaluation, find the data difference, and give two fixes.
15. You need "top 20 posts per user for 10M users" and the window-sort approach spills terabytes.
    Design the lateral-join-per-key alternative with its supporting index, and explain when it
    beats WindowAgg and when it loses.

---

*Next: [Module 3 — Joins](module-03-joins.md)*

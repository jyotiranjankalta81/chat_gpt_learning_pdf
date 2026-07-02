# MODULE 3 — Joins

> Two layers, both examined: **logical** (which rows come back — INNER/LEFT/RIGHT/FULL/CROSS/SELF)
> and **physical** (how the engine computes them — Nested Loop / Hash / Merge).
> Senior interviews live in the second layer and in the traps between the two.

Chapters:
3.1 Logical Joins: INNER, LEFT, RIGHT, FULL, CROSS, SELF
3.2 Physical Joins: Nested Loop, Hash Join, Merge Join
3.3 Join Traps & Optimization Playbook

---

## Chapter 3.1 — Logical Joins

### 1. Why Interviewers Ask This
Everyone claims to know joins; interviewers filter with three probes: **row multiplication**,
**WHERE vs ON placement on outer joins**, and **NULL behavior in join keys**. Getting these right
is table stakes for the SQL screen.

### 2. Core Concept
| Join | Returns | Typical use |
|---|---|---|
| INNER | Only matching pairs | Facts that must have both sides |
| LEFT (OUTER) | All left rows + matches (right side NULL-padded when absent) | Optional relationships, "with or without" |
| RIGHT | Mirror of LEFT (rewrite as LEFT — everyone does) | Rarely written |
| FULL | All rows both sides, NULL-padded where unmatched | Reconciliation/diff of two sets |
| CROSS | Cartesian product (m×n) | Generating combinations (calendar × products) |
| SELF | Table joined to itself (any type) | Hierarchies, pairs, sequential comparison |

Three rules that decide interview questions:
1. **Multiplication**: joins are pair-matching. If the key isn't unique on one side, rows
   duplicate; if not unique on *both* sides, rows multiply (m×n per key). Every "why did my
   SUM double?" bug is this.
2. **ON vs WHERE on outer joins**: `ON` decides *matching*; `WHERE` filters the *result*.
   A WHERE condition on the right table's column (other than `IS NULL`) discards the NULL-padded
   rows → **silently converts LEFT JOIN to INNER JOIN**. The single most-tested join trap.
3. **NULL keys never match**: `NULL = NULL` is UNKNOWN. Rows with NULL join keys vanish from
   INNER joins.

Anti-join idioms: "left rows with no match" = `LEFT JOIN ... WHERE right.id IS NULL` or
`NOT EXISTS` (prefer the latter — intent-revealing and plans as Anti Join directly).

### 3. Internal Working
The planner treats logical join type as a *constraint* on reordering: inner joins commute and
associate freely (join reordering — Module 5); outer joins restrict reorder legality. It also
tries **outer-join simplification**: if a later predicate rejects NULLs from the right side, the
LEFT JOIN is internally converted to INNER (which is exactly the WHERE-vs-ON trap, done on
purpose by the optimizer). FULL JOIN limits algorithm choice (hash full join supported in
recent PG; merge join handles it naturally).

### 4. Visualization (ASCII)
```
users u LEFT JOIN orders o ON o.user_id = u.id
u: (1,ann) (2,bob) (3,cat)      o: (10,u1) (11,u1) (12,u3)

result:               1|ann|10          -- ann duplicated: 2 matches
                      1|ann|11
                      2|bob|NULL        -- padded: bob kept
                      3|cat|12

...WHERE o.status='paid'    → bob's row has o.status = NULL → dropped
                              LEFT JOIN just became INNER JOIN (trap!)
...ON  o.status='paid'      → bob kept (padded); ann keeps only paid orders ✔

NULL key: u4 with id NULL never equals anything → absent from INNER result
```

### 5. Real Production Example
A Meta-style metrics bug: "signups with their first payment" written as
`LEFT JOIN payments p ... WHERE p.status='completed'` silently dropped all non-paying signups
from a conversion funnel — the funnel showed 100% conversion for a quarter. The fix (move the
condition into ON) is a one-line diff; the interview question "what changed?" is asked verbatim.
FULL JOIN in the wild: reconciling internal `payments` vs the processor's settlement file —
mismatched rows on either side are exactly the NULL-padded rows.

### 6. Common Interview Questions
- "Difference between putting the filter in ON vs WHERE on a LEFT JOIN?" (near-guaranteed)
- "Users with zero orders — write it twice (anti-join both idioms)."
- "Why did the revenue SUM double after adding a join?" (one-to-many multiplication)
- "When is CROSS JOIN legitimate?" (spines: dates × products for zero-filled reports)
- "Employees earning more than their manager." (classic self-join)

### 7. Common Mistakes
- The WHERE-kills-LEFT-JOIN trap (both directions: causing it, and not spotting it in review).
- Joining one-to-many then aggregating without dedup — `SUM` counts parents multiple times
  (fix: pre-aggregate the many side in a subquery/CTE *before* joining).
- `COUNT(*)` vs `COUNT(right.id)` after LEFT JOIN: `COUNT(*)` counts padded rows as 1;
  users with zero orders show 1 unless you count the right column.
- Accidental cross join via missing ON in comma-syntax (`FROM a, b WHERE ...` and the WHERE gets
  edited away) — always use explicit JOIN ... ON.
- Self-join without aliasing both sides distinctly.

### 8. Best Practices
- Left-table = the set you must not lose; conditions on the optional side go in ON.
- Pre-aggregate the many side to one row per key before joining when you'll aggregate the
  one side.
- Prefer `NOT EXISTS` over LEFT-JOIN-IS-NULL for anti-joins (clearer, and immune to being broken
  by later WHERE edits).
- Every FK you join on should be indexed (Module 4) — logical joins are only as good as the
  physical access path.

### 9. Coding Questions
1. Per user: name, order count, lifetime revenue — including users with zero orders showing 0
   (LEFT JOIN + COUNT(o.id) + COALESCE(SUM)) — then rewrite with a pre-aggregated subquery and
   explain when the second wins.
2. Pairs of employees in the same department with the same salary, each pair once
   (self-join with `e1.id < e2.id`).
3. Full reconciliation: rows only in `ledger`, only in `settlement`, and amount mismatches —
   one FULL JOIN query with a CASE classification column.

### 10. SQL Examples
```sql
-- Correct optional-side filtering
SELECT u.id, u.name, count(o.id) AS paid_orders, coalesce(sum(o.total_cents),0) AS revenue
FROM users u
LEFT JOIN orders o ON o.user_id = u.id AND o.status = 'paid'   -- condition in ON
GROUP BY u.id, u.name;

-- Anti-join, both idioms
SELECT u.* FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE o.id IS NULL;                       -- idiom 1

SELECT u.* FROM users u
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);  -- idiom 2 (preferred)

-- Self join: employee vs manager
SELECT e.name AS employee, m.name AS manager
FROM employees e JOIN employees m ON m.id = e.manager_id
WHERE e.salary > m.salary;

-- CROSS JOIN spine: zero-filled daily sales per product
SELECT d::date AS day, p.id AS product_id, coalesce(sum(s.qty),0) AS qty
FROM generate_series(current_date-6, current_date, '1 day') d
CROSS JOIN products p
LEFT JOIN sales s ON s.product_id = p.id AND s.sold_on = d::date
GROUP BY 1, 2;

-- FULL JOIN reconciliation
SELECT coalesce(l.txn_id, s.txn_id) AS txn_id,
       CASE WHEN l.txn_id IS NULL THEN 'missing_internally'
            WHEN s.txn_id IS NULL THEN 'missing_at_processor'
            WHEN l.amount <> s.amount THEN 'amount_mismatch'
            ELSE 'ok' END AS status
FROM ledger l FULL JOIN settlement s ON s.txn_id = l.txn_id
WHERE l.txn_id IS NULL OR s.txn_id IS NULL OR l.amount <> s.amount;
```

### 11. Optimization Techniques
- Reduce before you join: filter and pre-aggregate each side to the minimal row set.
- Join on compact, indexed, same-typed keys (type mismatch `int = varchar` blocks index use).
- For "one row from the many side" (latest order per user), `JOIN LATERAL (...ORDER BY...LIMIT 1)`
  probes the index per user instead of joining everything.

### 12. Follow-up Questions
- "Rewrite this RIGHT JOIN chain as LEFT JOINs — why do teams ban RIGHT JOIN?" (reading order)
- "The anti-join is slow on 100M rows — what plan do you want to see?" (Hash Anti Join, not a
  per-row SubPlan)
- "What happens to join results when the key is nullable on both sides, and how does that differ
  in a FULL JOIN's output?"

---

## Chapter 3.2 — Physical Joins: Nested Loop, Hash Join, Merge Join

### 1. Why Interviewers Ask This
This is the difference between "knows SQL" and "can fix a slow query." Reading EXPLAIN output
means recognizing which algorithm fired and whether it was the right one for the cardinalities.
Google/Uber onsite favorite: "here's a plan, tell me why it's slow."

### 2. Core Concept
| Algorithm | How | Best when | Cost shape |
|---|---|---|---|
| **Nested Loop** | For each outer row, find matches in inner | Outer is SMALL and inner probe is an **index hit**; also the only option for non-equi joins (`<`, `BETWEEN`, `LIKE`) | O(outer × inner-probe). Index probe: great. Inner seq scan: O(m×n) disaster |
| **Hash Join** | Build hash table on smaller side, probe with larger | Large unsorted inputs, **equality** keys, enough memory | O(m + n), memory for build side; spills to disk in batches if > work_mem |
| **Merge Join** | Sort both sides (or use index order), zipper through | Both sides **already sorted** (indexes!), huge inputs, or FULL joins | O(m + n) after order; sorts cost n·log n if needed |

Rules of thumb the interviewer expects:
- Few outer rows + indexed inner → Nested Loop wins (best startup time too — pairs with LIMIT).
- Two big tables, equi-join → Hash Join wins.
- Both sides indexed on the join key / pre-sorted → Merge Join wins, output comes out sorted
  (can eliminate a later ORDER BY).
- Only Nested Loop handles arbitrary (non-equality) join conditions.

### 3. Internal Working
- **Nested Loop**: `for o in outer: for i in inner_lookup(o.key): emit`. Planner picks inner
  path per outer row — parameterized index scan (`Index Cond: user_id = o.id`). Chosen based on
  *estimated* outer rows: if stats say 10 but reality is 100k, you get 100k index probes —
  the classic misestimate blowup.
- **Hash Join**: build phase hashes the (estimated) smaller input into `work_mem`; probe phase
  streams the big side. Overflow → **batching**: both inputs partitioned to disk by hash and
  joined batch-by-batch (`Batches: 16` in EXPLAIN = spilling). Wrong side chosen for build
  (misestimate) → giant hash table, memory pressure.
- **Merge Join**: both inputs in key order — from B+Tree index scans (free order) or explicit
  Sorts. Two cursors advance; duplicate keys on both sides cause mini cross-products with
  rescans ("mark/restore"). Handles FULL OUTER naturally.

### 4. Visualization (ASCII)
```
NESTED LOOP                      HASH JOIN                      MERGE JOIN
outer (5 rows)                   build: small side → hash tbl   A sorted: 1 3 5 7 9
  │ per row                        {k1:[r],k2:[r],...} (RAM)    B sorted: 1 2 3 3 7
  ▼                              probe: big side streams        zipper:  advance the
inner INDEX probe ──▶ emit         hash(k) → bucket → emit        smaller cursor, emit
cost ≈ 5 index descents          cost ≈ read A + read B           on equality
✔ tiny outer, LIMIT-friendly     ✖ spills if build > work_mem   ✔ order for free from
✖ 1M outer rows = 1M probes        (EXPLAIN: Batches > 1)          indexes; output sorted
```

### 5. Real Production Example
Uber-scale incident pattern: a query joining `trips` to `cities` runs fine (nested loop, 20
outer rows) until a code change removes a filter — outer side becomes 40M rows, planner stats
are stale so it *still* picks nested loop → 40M index probes → p99 explodes and connections
pile up. Fix: `ANALYZE` (fresh stats flip it to hash join). The interview version:
"same query, fast yesterday, slow today, no code change — go" (stats drift / plan flip).

### 6. Common Interview Questions
- "Explain the three join algorithms and when the planner picks each."
- "What does `Hash Join ... Batches: 32` mean?" (work_mem overflow, disk partitioning)
- "Why is nested loop sometimes the fastest and sometimes the worst?" (outer cardinality ×
  inner path)
- "Which algorithm for `a.ts BETWEEN b.start AND b.end`?" (nested loop — no equality key;
  mention range-type GiST index as the real fix)
- "Why did adding LIMIT 10 change the join algorithm?" (startup cost: NL streams immediately)

### 7. Common Mistakes
- Reading EXPLAIN top-down only and missing that the *inner* node runs `loops=N` times —
  multiply `actual time × loops`.
- Blaming the algorithm when the real issue is a **misestimate** (compare `rows=` estimated vs
  actual in EXPLAIN ANALYZE — Module 5).
- Disabling nested loops globally (`enable_nestloop=off`) as a "fix" — punishes every
  small-outer query.
- Forgetting Merge Join may include hidden Sort nodes — the sort, not the join, is the cost.
- Missing index on the join FK → hash join forced for even tiny lookups, or NL with inner
  seq scan (worst case).

### 8. Best Practices
- Index every join key (FKs first); it enables NL-with-index and merge join, and gives the
  planner options.
- Keep stats fresh (`ANALYZE`, autovacuum analyze thresholds tuned down for big tables).
- Size `work_mem` so common hash joins run `Batches: 1` — but remember it's per-node,
  per-query, per-connection (multiply!).
- When diagnosing: check estimated-vs-actual rows first, algorithm second, indexes third.

### 9. Coding Questions
1. Given `EXPLAIN ANALYZE` output showing `Nested Loop (actual rows=2,400,000 loops=1)` with
   inner `Index Scan (loops=2400000)` — state the problem, the two possible fixes
   (stats / rewrite), and the plan you expect after.
2. For `orders (500M) JOIN users (50M) ON user_id` filtered to one day of orders (~1M):
   predict the chosen algorithm and build side; then predict again with no date filter.

### 10. SQL Examples
```sql
-- See the algorithm and the estimates vs reality
EXPLAIN (ANALYZE, BUFFERS)
SELECT u.country, count(*)
FROM orders o JOIN users u ON u.id = o.user_id
WHERE o.created_at >= now() - interval '1 day'
GROUP BY u.country;
-- Look for: Hash Join / Nested Loop / Merge Join, rows= vs actual rows=, Batches:, loops=

-- Force-compare algorithms while investigating (session-local, never in prod code)
SET enable_hashjoin = off;   -- re-run EXPLAIN ANALYZE, compare
RESET enable_hashjoin;

-- Give the planner what it needs
CREATE INDEX ON orders (user_id);            -- join key
CREATE INDEX ON orders (created_at);         -- filter
ANALYZE orders;                              -- fresh stats
```

### 11. Optimization Techniques
- Shrink the build side: filter/aggregate before joining so the hash table is small.
- Feed merge joins from indexes to avoid explicit sorts; exploit its sorted output to erase a
  later `ORDER BY`.
- Batch key lookups from the app (`= ANY($ids)`) so one indexed NL/hash query replaces N
  round-trip queries (N+1 problem — Module 5).
- Partition-wise joins: joining two tables partitioned identically on the join key joins
  partition-pairs (parallelizable, smaller hashes).

### 12. Follow-up Questions
- "work_mem is 4MB and the build side is 4GB — walk through exactly what the executor does."
  (multi-batch grace hash join, disk partitions, recursive re-partitioning if skewed)
- "One join key value holds 30% of rows (skew) — which algorithm suffers and why?"
  (hash: one huge bucket / batch; merge: mini cross-product rescans; discuss salting)
- "How do distributed engines join across shards?" (broadcast vs shuffle joins — nice bridge
  to Module 7/8)

---

## Chapter 3.3 — Join Traps & Optimization Playbook

### 1. Why Interviewers Ask This
Senior loops end joins with a debugging scenario. This chapter is the checklist you run.

### 2. Core Concept — The Playbook
When a join query is slow or wrong, check in order:

1. **Wrong results first**: row multiplication? LEFT-turned-INNER via WHERE? NULL keys dropped?
2. **Cardinality**: how many rows does each side contribute *after* filters? (EXPLAIN ANALYZE
   actual rows)
3. **Estimates vs actuals**: off by >10x → stale stats (`ANALYZE`), correlated columns
   (extended statistics), or non-representable predicates.
4. **Access paths**: is every join key indexed? Types identical? Expression mismatch?
5. **Algorithm sanity**: NL with big outer? Hash with `Batches > 1`? Merge with giant Sorts?
6. **Shape rewrites**: pre-aggregate, LATERAL for top-1-per-key, `EXISTS` instead of JOIN+DISTINCT,
   split OR-joins into UNION ALL.

### 3. Internal Working
Why joins go quadratic: the planner's row estimates multiply through the join tree, so one bad
estimate at the bottom corrupts every decision above it (join order, algorithms, memory grants).
That's why "fix the estimate" (stats, extended stats, rewrite) usually beats "hint the plan."

### 4. Visualization (ASCII)
```
Estimate error propagates upward:
            Hash Join (est 100 rows, actual 8M)  ← everything above is misplanned
           /        \
   IndexScan A     Hash
   est 10 act 4000  └─ SeqScan B  ← root cause: stale stats on A's filter column
FIX ORDER: stats → indexes → rewrite → (last resort) planner knobs
```

### 5. Real Production Example
Stripe-style reporting join across `charges`, `refunds`, `disputes` where each is one-to-many:
joining all three multiplies rows (charge × refunds × disputes) and inflates SUMs. Production
fix: aggregate each child to one row per charge in CTEs, then join three tiny aggregates —
also what turns three hash joins of 100M rows into three of 1M.

### 6. Common Interview Questions
- "SUM tripled after adding the disputes join — why, and fix it live."
- "This 5-table join is slow; the plan shows all seq scans — walk your checklist."
- "When do you denormalize instead of joining?" (measured hot path, after covering indexes fail
  — bridges Module 1.6)

### 7. Common Mistakes
- Fixing symptoms with `DISTINCT` on a multiplied result instead of pre-aggregating (hides the
  bug, keeps the cost).
- Adding indexes to fix a join that spills — the spill is `work_mem`/build-side size, not
  access path.
- OR in join conditions (`ON a.x=b.x OR a.y=b.y`) — kills hash/merge; split into UNION ALL of
  two equi-joins.

### 8. Best Practices
- One-row-per-key discipline: know the grain of every table in the join and assert it (unique
  index) — most wrong-join bugs are grain bugs.
- Keep join keys `bigint`-typed and identical across tables; never join `text` to `int`.
- Standard rewrite kit memorized: pre-aggregate / LATERAL top-N / EXISTS semi-join /
  UNION-ALL-split OR / calendar-spine cross join.

### 9. Coding Questions
1. Fix live: `SELECT c.id, sum(r.amount), sum(d.amount) FROM charges c LEFT JOIN refunds r ON
   r.charge_id=c.id LEFT JOIN disputes d ON d.charge_id=c.id GROUP BY c.id;` (multiplied sums —
   pre-aggregate each child).
2. Rewrite `ON o.user_id = u.id OR o.guest_email = u.email` as UNION ALL of two indexable joins,
   handling the overlap (dedup on a business key).

### 10. SQL Examples
```sql
-- Grain-safe multi-child aggregation
WITH r AS (SELECT charge_id, sum(amount) AS refunded FROM refunds  GROUP BY 1),
     d AS (SELECT charge_id, sum(amount) AS disputed FROM disputes GROUP BY 1)
SELECT c.id, coalesce(r.refunded,0) AS refunded, coalesce(d.disputed,0) AS disputed
FROM charges c
LEFT JOIN r ON r.charge_id = c.id
LEFT JOIN d ON d.charge_id = c.id;

-- Top-1-per-key via LATERAL (index-driven, no giant sort)
SELECT u.id, o.*
FROM users u
LEFT JOIN LATERAL (
  SELECT * FROM orders o WHERE o.user_id = u.id
  ORDER BY o.created_at DESC LIMIT 1
) o ON true;
-- supporting index: orders(user_id, created_at DESC)
```

### 11. Optimization Techniques
- Extended statistics for correlated filter columns feeding joins:
  `CREATE STATISTICS s (dependencies) ON city, country FROM users; ANALYZE users;`
- Parallel hash joins (PG 11+) — check `Workers Planned/Launched` for big analytic joins.
- `join_collapse_limit` awareness: beyond ~8 tables the planner stops exhaustive reordering —
  write the critical join order explicitly or raise the limit.

### 12. Follow-up Questions
- "The plan is optimal but still too slow — what's left?" (data volume: pre-aggregate,
  denormalize, cache, move to OLAP store)
- "How would you catch grain bugs before prod?" (unique indexes as executable documentation,
  row-count assertions in tests)

---

# Module 3 — Practice Problems

## Easy (5)
1. Products never ordered — both anti-join idioms; which plan node do you want to see?
2. Predict the output row count: `A(5 rows, key k unique)` INNER JOIN `B(8 rows, 3 rows with
   k=1, others unmatched)` — then for LEFT JOIN both directions.
3. Spot the bug: `FROM users u LEFT JOIN orders o ON o.user_id=u.id WHERE o.created_at >
   now()-interval '30 days'` — what does it return and how do you fix it two ways?
4. Employees and their managers' names, including employees with no manager.
5. Which join algorithm and why: 12-row `countries` joined to 300M-row `events` on
   `country_code` with an index on `events(country_code)`?

## Medium (5)
6. Per user: signup date, first order date, days-to-convert, including never-converted users —
   without a correlated subquery.
7. `EXPLAIN ANALYZE` shows `Hash Join ... Batches: 64, actual rows 90M` under a `Sort` feeding
   `Limit 50`. Give three independent fixes and the plan you'd expect from each.
8. Sessions table has `(user_id, started_at, ended_at)`. Find overlapping session *pairs* per
   user (self non-equi join), then explain why this can't hash-join and how a GiST index on
   `tstzrange(started_at, ended_at)` changes the game.
9. Reconcile `inventory_counts` (system) vs `warehouse_scan` (physical): produce
   missing-in-system, missing-in-warehouse, and quantity mismatches in one FULL JOIN pass.
10. A 6-table reporting join is correct but 40s. Only 2 tables are large. Restructure it
    (aggregate-then-join) and state the expected algorithm for each remaining join.

## Hard (5)
11. Skewed join: 25% of `events` share `user_id = 0` (anonymous). The hash join stalls on one
    batch. Show the split: handle `user_id=0` branch separately (pre-aggregated) UNION ALL the
    normal join, and explain why this fixes both memory and parallelism.
12. Design the indexes so `orders JOIN users` filtered by `orders.created_at` range and
    `users.country='DE'`, ordered by `orders.created_at DESC LIMIT 50`, runs as
    NL-with-index without a sort. Explain each index column's role.
13. Interval join at scale: match each `payment(ts)` to the `fx_rate` valid at that instant
    (`valid_from <= ts < valid_to`, 200M payments, 100k rates). Compare NL+btree,
    LATERAL top-1, and range-type GiST approaches with expected costs.
14. Prove (with a 3-row example) that `LEFT JOIN` then `WHERE right.col = X` differs from
    `ON right.col = X`, and that the WHERE form equals INNER JOIN — then find the one condition
    for which WHERE placement on the right side is legitimate. (`IS NULL` anti-join.)
15. You must join two 1B-row tables on `session_id` nightly. Both are partitioned by day.
    Design a partition-wise join strategy (co-partitioning, per-partition hash joins,
    parallelism), and what breaks if one table is partitioned by week instead.

---

*Next: [Module 4 — Indexes](module-04-indexes.md)*

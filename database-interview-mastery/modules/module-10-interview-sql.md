# MODULE 10 — Interview SQL: The Problems That Actually Get Asked

> ~90% of SQL screen questions are instances of the 10 patterns below. Learn the *pattern*,
> and the "top 100 problems" become variations you improvise. Each pattern: why it's asked,
> the template, worked solutions, traps, and follow-ups.
>
> Standard tables used throughout:
> `employees(id, name, dept_id, salary, manager_id)`
> `orders(id, user_id, total_cents, status, created_at)`
> `events(user_id, event_type, ts)`
> `logins(user_id, login_date)`

---

## Pattern 1 — Ranking & Nth Highest (ROW_NUMBER / RANK / DENSE_RANK)

**Why asked**: the fastest window-function fluency check; "second highest salary" is the most
famous SQL interview question in existence.

**Template**: rank in a subquery/CTE, filter outside (windows can't go in WHERE).

```sql
-- Second highest salary (value): DENSE_RANK handles ties correctly
SELECT DISTINCT salary
FROM (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
      FROM employees) t
WHERE rnk = 2;

-- Nth highest as a parameter
SELECT salary FROM (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk FROM employees
) t WHERE rnk = :n LIMIT 1;

-- Classic no-window alternatives (know them — they still get asked):
SELECT max(salary) FROM employees
WHERE salary < (SELECT max(salary) FROM employees);          -- 2nd highest

SELECT DISTINCT salary FROM employees e1
WHERE :n - 1 = (SELECT count(DISTINCT salary) FROM employees e2
                WHERE e2.salary > e1.salary);                 -- Nth, correlated

-- Top 3 per department, ties included
SELECT * FROM (
  SELECT e.*, DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) rnk
  FROM employees e
) t WHERE rnk <= 3;
```

**Traps**: RANK skips positions after ties (1,1,3) — "3rd highest *value*" needs DENSE_RANK;
"3rd highest *row*" needs ROW_NUMBER with a declared tiebreaker; Nth highest must return NULL
(not empty tantrum) when fewer than N distinct values — `LIMIT 1` + scalar subquery shape, or
LeetCode's `SELECT (SELECT ...)` wrapper.
**Follow-ups**: "which of the three functions and why"; "do it without window functions";
"what index helps?" (`(dept_id, salary DESC)` feeds the partition sort).

---

## Pattern 2 — Duplicate Records (find, count, delete)

**Why asked**: real data-cleanup skill + window-function DELETE synthesis.

```sql
-- Find duplicated business keys
SELECT email, count(*) FROM users GROUP BY email HAVING count(*) > 1;

-- Full duplicate rows with ids (window version — shows all copies)
SELECT * FROM (
  SELECT u.*, count(*) OVER (PARTITION BY email) AS copies
  FROM users u
) t WHERE copies > 1;

-- Delete duplicates, keep lowest id (the canonical answer)
DELETE FROM users u
USING users u2
WHERE u.email = u2.email AND u.id > u2.id;

-- Delete keeping the most recent, arbitrary tie policy declared
DELETE FROM users
WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY email
                                  ORDER BY last_seen DESC, id DESC) rn
    FROM users) t
  WHERE rn > 1
);
```

**Traps**: defining "duplicate" (whole row vs business key) — ask; keeping which copy —
declare the ORDER BY; on huge tables, batch the delete and add the unique index *after*
cleanup (`CREATE UNIQUE INDEX CONCURRENTLY`) so duplicates can't return.
**Follow-ups**: "prevent them forever" (unique index — the real answer); "the table is 2B rows"
(batched deletes by id range; or CTAS the survivors + swap).

---

## Pattern 3 — Running Totals & Moving Averages

**Why asked**: frames (ROWS/RANGE) separate people who *use* windows from people who understand
them.

```sql
-- Running total per user
SELECT user_id, created_at, total_cents,
       SUM(total_cents) OVER (PARTITION BY user_id ORDER BY created_at, id) AS running
FROM orders;

-- 7-row moving average (physical rows)
SELECT day, revenue,
       AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma7
FROM daily_revenue;

-- 7-DAY moving average (time-correct even with missing days)
SELECT day, revenue,
       AVG(revenue) OVER (ORDER BY day
                          RANGE BETWEEN interval '6 days' PRECEDING AND CURRENT ROW) AS ma7
FROM daily_revenue;

-- Month-over-month growth (LAG)
SELECT month, revenue,
       round(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 1) AS growth_pct
FROM monthly_revenue;

-- Cumulative % of total (running / grand total)
SELECT day, revenue,
       SUM(revenue) OVER (ORDER BY day)::numeric
         / SUM(revenue) OVER () AS cum_share
FROM daily_revenue;
```

**Traps**: `ROWS` vs `RANGE` when days are missing or duplicated (ROWS counts rows; RANGE
counts value-distance — the 7-day question is a RANGE or calendar-spine question); default
frame with ORDER BY is RANGE-to-current-row *including peers*; always add a unique tiebreaker
to ORDER BY for deterministic running sums.
**Follow-ups**: "running total without window functions" (self-join `b.day <= a.day` — O(N²),
say why it's worse); "reset the running total every month" (add month to PARTITION BY).

---

## Pattern 4 — Top-K per Group

**Why asked**: the workhorse pattern (top 3 products per category, latest order per user);
tests both correctness and the performance alternatives.

```sql
-- Window version (general)
SELECT * FROM (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY user_id
                                 ORDER BY created_at DESC, id DESC) rn
  FROM orders o
) t WHERE rn <= 3;

-- Latest-one-per-group: DISTINCT ON (Postgres idiom, terse)
SELECT DISTINCT ON (user_id) *
FROM orders ORDER BY user_id, created_at DESC, id DESC;

-- LATERAL version (index-driven; wins when groups ≪ rows)
SELECT o.* FROM users u
JOIN LATERAL (
  SELECT * FROM orders o WHERE o.user_id = u.id
  ORDER BY created_at DESC, id DESC LIMIT 3
) o ON true;      -- index: orders(user_id, created_at DESC, id DESC)
```

**Traps**: ROW_NUMBER vs RANK for "top 3 with ties" (RANK/DENSE_RANK ≤ 3 may return >3 rows —
clarify the requirement); nondeterminism without a tiebreaker; the window version sorts
*everything* — mention the LATERAL alternative for perf and you jump a level.
**Follow-ups**: "which is fastest on 1B orders / 10M users?" (LATERAL probes 10M × index-top-3
vs global sort — depends on group count; discuss); "top 3 by SUM per group" (aggregate first,
then rank the aggregates).

---

## Pattern 5 — Gaps & Islands

**Why asked**: the hardest common pattern; tests the row_number-difference trick. Shows up as
consecutive login streaks, continuous sensor coverage, seat-range grouping.

**The trick**: for consecutive integers/dates, `value - ROW_NUMBER()` is constant within a
consecutive run ("island") — group by that constant.

```sql
-- Longest consecutive-day login streak per user
WITH days AS (          -- dedup multiple logins per day
  SELECT DISTINCT user_id, login_date FROM logins
), grp AS (
  SELECT user_id, login_date,
         login_date - (ROW_NUMBER() OVER (PARTITION BY user_id
                                          ORDER BY login_date))::int AS island
  FROM days
)
SELECT user_id,
       count(*)          AS streak_len,
       min(login_date)   AS streak_start,
       max(login_date)   AS streak_end
FROM grp
GROUP BY user_id, island
ORDER BY streak_len DESC;

-- Gaps: missing id ranges in a sequence
SELECT prev_id + 1 AS gap_start, id - 1 AS gap_end
FROM (SELECT id, LAG(id) OVER (ORDER BY id) AS prev_id FROM tickets) t
WHERE id - prev_id > 1;

-- Islands with a tolerance (new island when gap > 30 min) — general LAG method
WITH flagged AS (
  SELECT *, CASE WHEN ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts)
                      > interval '30 minutes'
                 THEN 1 ELSE 0 END AS new_island
  FROM events
), numbered AS (
  SELECT *, SUM(new_island) OVER (PARTITION BY user_id ORDER BY ts) AS island_id
  FROM flagged
)
SELECT user_id, island_id, min(ts), max(ts), count(*) FROM numbered
GROUP BY user_id, island_id;
```

**Traps**: duplicates break the row_number-difference trick (dedup first!); the difference
trick only works for evenly-spaced values — irregular spacing needs the LAG+flag+running-sum
method (which is also the sessionization solution); date arithmetic types (`date - int` works
in PG; timestamps need care).
**Follow-ups**: "streak *ending today*" (filter islands where max = current_date); "merge
overlapping intervals" (same flag method with `start <= max(prev_end)` running max).

---

## Pattern 6 — Sessionization

**Why asked**: the analytics-engineering classic (Meta/Amazon product analytics): split an
event stream into sessions with a 30-minute inactivity rule. It's Gaps & Islands in disguise —
say that out loud.

```sql
WITH flagged AS (
  SELECT user_id, ts,
         CASE WHEN ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts)
                   > interval '30 minutes'
              OR LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) IS NULL
         THEN 1 ELSE 0 END AS session_start
  FROM events
), sessions AS (
  SELECT *, SUM(session_start) OVER (PARTITION BY user_id ORDER BY ts) AS session_no
  FROM flagged
)
SELECT user_id, session_no,
       min(ts) AS session_start,
       max(ts) AS session_end,
       max(ts) - min(ts) AS duration,
       count(*) AS events
FROM sessions
GROUP BY user_id, session_no;

-- Follow-on metrics interviewers ask next:
-- avg sessions/user/day, avg session duration, bounce sessions (events = 1)
```

**Traps**: forgetting the first event (LAG NULL) must open a session; timezone bucketing when
reporting per-day; global vs per-user ordering (always PARTITION BY user).
**Follow-ups**: "do it for 10B events" (this exact shape in Spark/warehouse; or incremental
sessionization with state); "session ids stable across reruns?" (derive from user_id +
session_start).

---

## Pattern 7 — Median & Percentiles

**Why asked**: tests knowledge of ordered-set aggregates (and the honest "SQL median is not
AVG" check).

```sql
-- Median (interpolated) and p95
SELECT percentile_cont(0.5)  WITHIN GROUP (ORDER BY total_cents) AS median,
       percentile_cont(0.95) WITHIN GROUP (ORDER BY total_cents) AS p95,
       percentile_disc(0.5)  WITHIN GROUP (ORDER BY total_cents) AS median_actual_value
FROM orders;

-- Per group
SELECT dept_id,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary
FROM employees GROUP BY dept_id;

-- Median as a window (per-row context): PERCENTILE_CONT isn't a window fn in PG →
-- use two ROW_NUMBERs (the classic manual median):
WITH r AS (
  SELECT salary,
         ROW_NUMBER() OVER (ORDER BY salary)  rn,
         COUNT(*)     OVER ()                 n
  FROM employees
)
SELECT avg(salary) AS median FROM r WHERE rn IN ((n+1)/2, (n+2)/2);

-- Decile bucketing
SELECT id, salary, NTILE(10) OVER (ORDER BY salary) AS decile FROM employees;
```

**Traps**: `percentile_cont` interpolates (may return a value not in the data) vs
`percentile_disc`; even-count median = average of middle two (the manual version must handle
it — the `(n+1)/2, (n+2)/2` trick does); MySQL <8 has none of this → manual method is the
portable answer.
**Follow-ups**: "p99 latency over a rolling window" (percentile per time bucket; exact
percentiles don't decompose — mention t-digest/HLL-style sketches for streaming).

---## Pattern 8 — Hierarchies & Recursive Queries

**Why asked**: org charts and category trees (Module 2.3's recursive CTE, in problem form).

```sql
-- All reports (direct+indirect) of manager 42, with depth and path
WITH RECURSIVE sub AS (
  SELECT id, name, manager_id, 1 AS depth, ARRAY[id] AS path
  FROM employees WHERE manager_id = 42
  UNION ALL
  SELECT e.id, e.name, e.manager_id, s.depth+1, s.path || e.id
  FROM employees e JOIN sub s ON e.manager_id = s.id
  WHERE NOT e.id = ANY(s.path)
)
SELECT * FROM sub ORDER BY path;

-- Chain UP: an employee's management chain to the CEO
WITH RECURSIVE chain AS (
  SELECT id, name, manager_id, 1 AS lvl FROM employees WHERE id = :emp
  UNION ALL
  SELECT e.id, e.name, e.manager_id, c.lvl+1
  FROM employees e JOIN chain c ON e.id = c.manager_id
)
SELECT * FROM chain;

-- Aggregate over subtree: headcount + total salary under each manager
WITH RECURSIVE sub AS (
  SELECT id AS root, id FROM employees
  UNION ALL
  SELECT s.root, e.id FROM employees e JOIN sub s ON e.manager_id = s.id
)
SELECT root, count(*) - 1 AS reports FROM sub GROUP BY root;

-- Employees earning more than their manager (the self-join classic)
SELECT e.name FROM employees e JOIN employees m ON m.id = e.manager_id
WHERE e.salary > m.salary;
```

**Traps**: infinite loops on cyclic data (path guard / PG14 `CYCLE` clause); UNION vs UNION ALL
in the recursion (dedup per iteration vs not); the subtree-aggregate version fans out — fine
for org charts, quadratic-ish for deep wide trees (closure table alternative).
**Follow-ups**: "same in MySQL?" (8.0 WITH RECURSIVE — yes); "10M-node tree read constantly"
(closure table / ltree / materialized path — Module 2.3).

---

## Pattern 9 — Pivots, Conditional Aggregation & Attribution

**Why asked**: reshaping rows→columns and funnel/attribution logic — the analytics screen staples.

```sql
-- Pivot: orders by status per month (rows → columns)
SELECT date_trunc('month', created_at) AS month,
       count(*) FILTER (WHERE status = 'paid')      AS paid,
       count(*) FILTER (WHERE status = 'cancelled') AS cancelled,
       count(*) FILTER (WHERE status = 'refunded')  AS refunded
FROM orders GROUP BY 1 ORDER BY 1;

-- Funnel: view → cart → purchase conversion within 7 days
WITH v AS (SELECT user_id, min(ts) AS t FROM events WHERE event_type='view'     GROUP BY 1),
     c AS (SELECT user_id, min(ts) AS t FROM events WHERE event_type='cart'     GROUP BY 1),
     p AS (SELECT user_id, min(ts) AS t FROM events WHERE event_type='purchase' GROUP BY 1)
SELECT count(v.user_id)                              AS viewed,
       count(c.user_id)                              AS carted,
       count(p.user_id) FILTER (WHERE p.t <= v.t + interval '7 days') AS purchased
FROM v LEFT JOIN c USING (user_id) LEFT JOIN p USING (user_id);

-- First-touch attribution: the channel of each user's first visit
SELECT DISTINCT ON (user_id) user_id, channel AS first_touch
FROM visits ORDER BY user_id, ts;

-- Retention: % of January signups active in each subsequent month (cohort)
SELECT date_trunc('month', a.ts) AS month,
       count(DISTINCT a.user_id)::numeric
         / (SELECT count(*) FROM users
            WHERE created_at >= '2026-01-01' AND created_at < '2026-02-01') AS retention
FROM events a
JOIN users u ON u.id = a.user_id
WHERE u.created_at >= '2026-01-01' AND u.created_at < '2026-02-01'
GROUP BY 1 ORDER BY 1;
```

**Traps**: funnel steps must be *ordered in time* (cart after view — join conditions on
timestamps, not just existence); COUNT(DISTINCT) semantics in cohorts; pivot with dynamic
columns isn't SQL's job (app/BI layer, or crosstab extension — say so).
**Follow-ups**: "windowed funnel (step within 1h of previous step)" (conditional joins on time
deltas or window LEAD over typed events).

---

## Pattern 10 — Set Operations, Anti-Joins & Data Diff

**Why asked**: "who churned / what's missing / reconcile these tables" — anti-join fluency plus
the NOT IN trap (Module 2.2) in problem form.

```sql
-- Customers who never ordered
SELECT u.* FROM users u
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);

-- Churn: active last month, absent this month
SELECT user_id FROM activity WHERE month = '2026-05-01'
EXCEPT
SELECT user_id FROM activity WHERE month = '2026-06-01';

-- Table diff (schema-identical tables a, b): rows that differ in either direction
(TABLE a EXCEPT TABLE b) UNION ALL (TABLE b EXCEPT TABLE a);

-- Users who bought product X AND product Y (relational division, the sneaky one)
SELECT user_id FROM orders o JOIN order_items i ON i.order_id = o.id
WHERE i.product_id IN (10, 20)
GROUP BY user_id
HAVING count(DISTINCT i.product_id) = 2;

-- Users who bought EVERY product in a category (full relational division)
SELECT o.user_id
FROM orders o JOIN order_items i ON i.order_id = o.id
JOIN products p ON p.id = i.product_id AND p.category_id = 7
GROUP BY o.user_id
HAVING count(DISTINCT p.id) = (SELECT count(*) FROM products WHERE category_id = 7);
```

**Traps**: `NOT IN` + NULL (the module-2 landmine — reflex answer: NOT EXISTS); EXCEPT dedups
(EXCEPT ALL if multiplicity matters); relational division via `HAVING count(DISTINCT) = total`
is the expected idiom.
**Follow-ups**: "make the never-ordered query fast on 100M users" (anti hash join + index on
orders(user_id); or maintained `last_order_at` column).

---

# The Top-100 Checklist (grouped by pattern)

Work through these; every one maps to a pattern above. ✅ = solved cold, in one pass.

**Ranking / Nth (1–12)**: second highest salary · Nth highest salary · top 3 per department ·
rank scores (with each of the 3 functions) · department top earner with ties · first purchase
per user · latest login per user · best-selling product per category · rank with gaps
explanation · median rank · dense rank change after delete · top earner per dept per month.

**Duplicates (13–20)**: find dup emails · delete dups keep lowest id · delete dups keep newest ·
count fully-duplicate rows · dedupe with a business-key priority · find near-duplicates
(same name, different email) · prevent duplicates (DDL) · dedupe a billion-row table (strategy).

**Aggregation & CASE (21–32)**: paid vs unpaid counts one scan · monthly revenue + growth % ·
AOV excluding refunds · revenue share per category · conditional sums by status · histogram
buckets · percent of total per row · weighted average · min/max with their dates ·
count distinct buyers per month · first/last value per group · HAVING vs WHERE cases.

**Joins & anti-joins (33–44)**: customers with no orders · products never sold · users with
orders in Jan but not Feb · employees vs managers salary · same-manager pairs · orders with
all items in stock · reconcile ledger vs settlement · users with ≥2 distinct categories bought ·
self-join sequential events · full-join diff two snapshots · every-product buyers (division) ·
X-and-Y buyers.

**Windows: running/offset (45–58)**: running total · running total reset monthly · 7-row MA ·
7-day MA with gaps · MoM growth · YoY same-month growth · days between consecutive orders ·
LAG price change detection · cumulative distinct users · first-order flag per row ·
percent-of-running-total · rolling 30-day distinct actives · rank of each day within its month ·
biggest single-day jump.

**Gaps & Islands / Sessions (59–70)**: longest login streak · current streak ending today ·
missing ids · missing dates · consecutive seats free · merge overlapping intervals ·
sessionize with 30-min gap · avg session duration · bounce rate · sessions per user per day ·
longest session · concurrent sessions max (interval overlap counting).

**Hierarchy / recursion (71–78)**: all reports of X · management chain up · tree depth ·
subtree headcount · cycle detection · category tree with product counts · BOM cost rollup ·
generate date series report.

**Median / percentiles (79–84)**: median salary · median per dept · p95 latency per endpoint ·
deciles · manual median (no percentile_cont) · trimmed mean.

**Design-flavored SQL (85–92)**: keyset pagination page-N · has_more trick · counter update
race-free · upsert with conflict · idempotent insert · soft-delete-aware unique · queue claim
SKIP LOCKED · optimistic-lock update.

**Classic LeetCode-style named problems (93–100)**: Employees earning more than managers ·
Duplicate emails · Customers who never order · Department highest salary · Department top three
salaries · Rank scores · Consecutive numbers (3+ in a row — islands) · Trips and users
(cancellation rate with filters).

---

# Module 10 — Practice Problems

## Easy (5)
1. Second-highest salary — three ways (window, max-below-max, OFFSET) — and state what each
   returns when the table has one distinct salary.
2. Find and delete duplicate `(user_id, product_id)` wishlist rows keeping the earliest;
   add the constraint preventing recurrence.
3. Monthly order counts pivoted into columns for statuses paid/cancelled/refunded, one scan.
4. Customers who never ordered — and explain why you didn't use NOT IN.
5. Rank scores per game with DENSE_RANK; return only players ranked ≤ 3, ties included.

## Medium (5)
6. Longest daily-login streak per user (full solution), then modify to "streak still alive
   today."
7. 7-day time-correct moving average of revenue with missing days, two ways (RANGE frame;
   calendar spine) — and when the answers differ.
8. Sessionize clickstream (30-min rule), then compute per user: sessions, avg duration,
   bounce rate — one query chain.
9. For each user: first order channel, last order channel, lifetime orders, days active span —
   one scan with windows/aggregates (no self-joins).
10. Consecutive-numbers problem: find numbers appearing ≥3 times consecutively (by id) —
    LAG/LEAD version and islands version.

## Hard (5)
11. Max concurrent sessions: given `(start_ts, end_ts)` rows, find the peak concurrency and
    when it occurred (event decomposition: +1/-1 rows, running sum, argmax).
12. Cohort retention triangle: for each signup month, retention % in months 0..5 — produce the
    month × offset grid in one query.
13. Median per department *as of each month end* over a year (percentiles over a moving
    population — window population construction + lateral percentile).
14. "Top 3 products per category by trailing-28-day revenue, refreshed daily, on a 2B-row
    order_items table" — write the query AND the incremental materialization design that makes
    it servable.
15. Gap-tolerant device uptime: sensors ping ~every 60s; compute per-device daily uptime %
    counting gaps >5 min as downtime (islands with tolerance + per-day slicing of intervals —
    handle intervals crossing midnight).

---

*Next: [Module 11 — Production Debugging](module-11-production-debugging.md)*

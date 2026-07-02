# MODULE 4 — Indexes (Highest Priority)

> If you master one module, master this one. "How do indexes work / why is my index ignored /
> design the index for this query" appears in virtually every senior backend loop.

Chapters:
4.1 B+Tree Internals
4.2 Clustered vs Non-Clustered Indexes
4.3 Composite Indexes & the Leftmost Prefix Rule
4.4 Covering, Partial & Unique Indexes
4.5 Scan Types: Index Scan, Index-Only Scan, Bitmap Scan, Sequential Scan
4.6 When Indexes Fail: Cardinality, Selectivity & Why Queries Ignore Indexes
4.7 How to Choose Indexes (Design Method)

---

## Chapter 4.1 — B+Tree Internals

### 1. Why Interviewers Ask This
"How does an index work?" is the canonical depth probe. The B+Tree answer separates candidates
who can predict costs (log N descent, range scans via leaf chain, write amplification) from
those who say "it makes queries fast."

### 2. Core Concept
A **B+Tree** is a balanced, high-fanout ordered tree:
- **Internal nodes**: only separator keys + child pointers (no data) → huge fanout.
- **Leaf nodes**: all keys in sorted order + pointers to table rows (TIDs in Postgres),
  linked left↔right into a chain → range scans are sequential leaf walks.
- **Balanced**: every leaf at the same depth; lookup = fixed log_fanout(N) page reads.

Fanout math you should say out loud: 8KB page ÷ ~40B per entry ≈ 200–400 entries/page →
**height 3–4 covers billions of rows**. Root and internal levels are almost always cached, so a
point lookup ≈ 1–2 actual disk reads worst case.

Why B+Tree and not a hash or binary tree:
- vs hash: B+Tree supports **range, prefix, ORDER BY**; hash only equality.
- vs binary tree: fanout 300 vs 2 → height 4 vs 30 → 4 page reads, not 30 (disk pages are the
  unit of cost).

### 3. Internal Working
- **Search**: binary-search the root for the child range, descend, repeat; scan the leaf.
- **Range scan**: descend to the first match, then follow the leaf chain — no re-descent.
- **Insert**: descend to the leaf; if full → **page split** (half the entries move to a new
  page, separator key inserted into the parent; splits can cascade upward, growing the tree by
  raising the root). Sequential keys always hit the rightmost leaf → cheap, cache-hot appends;
  random keys (UUIDv4) split everywhere → write amplification + cold cache.
- **Delete**: mark/remove entries; Postgres cleans dead index entries via VACUUM (index bloat
  when deletes/updates churn).
- **Every secondary index adds write cost**: each INSERT touches every index; each UPDATE of an
  indexed column touches that index (Postgres non-HOT updates touch *all* indexes — see 4.2).

### 4. Visualization (ASCII)
```
                       root [ 40 | 80 ]
                      /       |        \
        [10|25]            [55|70]           [90|95]        internal: keys only
       /   |   \          /   |   \         /   |   \
   leaf  leaf  leaf   leaf  leaf  leaf   leaf  leaf  leaf   leaves: keys + row ptrs
   [1..9]→[10..24]→[25..39]→[40..54]→[55..69]→[70..79]→[80..89]→[90..94]→[95..99]
      └────────────── doubly-linked leaf chain: range scan = walk right ─────────┘

Point lookup 57:  root→[55|70]→leaf[55..69] = 3 pages
Range 25..70:     descend once to 25, walk chain to 70

Page split on insert into full leaf:
  [10,12,14,16] + insert 13 → [10,12,13] [14,16] + push "14" up to parent
```

### 5. Real Production Example
Payments table at Stripe scale: `charges(id bigint)` grows by billions of rows; because ids are
monotonically increasing, all B+Tree inserts append to the rightmost leaf — index stays fast and
hot. A team switches to UUIDv4 for "security" → inserts scatter across the whole tree, page
splits everywhere, buffer pool churns, p99 insert latency triples. Fix: UUIDv7 (time-ordered)
or keep bigint internally. This exact story is a Meta/Uber interview favorite.

### 6. Common Interview Questions
- "Explain how a B+Tree index finds a row." (with page-count arithmetic)
- "B+Tree vs B-Tree vs hash index?" (B+Tree: data only in leaves + leaf chain; hash: equality only)
- "Why are databases' trees wide and shallow?" (page = I/O unit; minimize page reads)
- "What happens inside the index during INSERT? During a range query?"
- "Why do random UUIDs hurt insert performance?"

### 7. Common Mistakes
- Saying data is stored in internal nodes (that's B-Tree, not B+Tree; and matters for fanout).
- Ignoring write cost: "just add an index" on a table with 10 indexes and heavy writes.
- Missing that ORDER BY on the indexed column is free (leaf chain is sorted) — huge for
  pagination.
- Thinking index lookup is O(1) or "instant" — it's log with a small base, plus heap access
  (see 4.5).

### 8. Best Practices
- Time-ordered keys for high-insert tables (bigint identity / UUIDv7 / ULID).
- Watch index bloat on churny tables (`pgstattuple`, `REINDEX CONCURRENTLY` to rebuild).
- Count your indexes: each one taxes every write; delete unused ones
  (`pg_stat_user_indexes.idx_scan = 0`).
- Know the specialized types exist and when: GIN (jsonb, arrays, full-text, trigram),
  GiST (ranges, geometry), BRIN (huge append-only, correlated columns), Hash (rarely worth it).

### 9. Coding Questions
1. Compute tree height: 2B rows, 8KB pages, 40B index entries. (fanout ≈ 200 → 200³ = 8M,
   200⁴ = 1.6B < 2B → height ≈ 4–5; with realistic fanout 300+: 4.)
2. Estimate pages read for `WHERE id BETWEEN 1000 AND 2000` (height descents = 3, plus
   1000 entries ÷ ~200/leaf ≈ 5 leaf pages, plus heap pages per 4.5).

### 10. SQL Examples
```sql
CREATE INDEX CONCURRENTLY idx_orders_created ON orders (created_at);
-- CONCURRENTLY: builds without blocking writes (mandatory on live tables; can't run in a txn)

-- Inspect the tree
CREATE EXTENSION IF NOT EXISTS pageinspect;
SELECT * FROM bt_metap('idx_orders_created');           -- root, level (height)
SELECT avg_leaf_density, leaf_fragmentation
FROM pgstatindex('idx_orders_created');                 -- bloat check (pgstattuple ext)

-- Find dead-weight indexes
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes ORDER BY idx_scan ASC LIMIT 10;
```

### 11. Optimization Techniques
- `REINDEX CONCURRENTLY` (or `pg_repack`) for bloated indexes on churn-heavy tables.
- Postgres 13+ **B+Tree deduplication** compresses duplicate keys automatically — low-cardinality
  btrees got much smaller (worth mentioning).
- `fillfactor < 100` on indexes for update-heavy tables leaves split headroom.

### 12. Follow-up Questions
- "Index is 5x the size it should be — why and what do you do?" (bloat from churn; REINDEX
  CONCURRENTLY; autovacuum tuning)
- "Why might an index speed reads but be net-negative for the system?" (write amplification,
  cache pressure, maintenance)
- "How does an LSM tree differ for the same workload?" (Module 8 bridge: write-optimized vs
  read-optimized)

---

## Chapter 4.2 — Clustered vs Non-Clustered Indexes

### 1. Why Interviewers Ask This
Classic MySQL-vs-Postgres discriminator question, and it explains real phenomena: why MySQL
secondary lookups are double lookups, why hot ranges are fast in InnoDB, why Postgres has HOT
updates and visibility maps.

### 2. Core Concept
- **Clustered index**: the table rows are physically stored *in* the index's leaf pages, in key
  order. One per table (data can only be in one order). **InnoDB: the PK is always the
  clustered index** — the table *is* a B+Tree on the PK.
- **Non-clustered (secondary) index**: separate structure whose leaves point to the row —
  in InnoDB, secondary leaves store **the PK value** (→ lookup = secondary tree + PK tree =
  two descents); in Postgres, **all** indexes are secondary and leaves store the **TID**
  (physical page, slot) into the heap.
- **Postgres has no clustered index.** `CLUSTER` physically reorders the heap once (not
  maintained). Correlation between index order and heap order is tracked in stats and matters
  for range-scan cost.

### 3. Internal Working
- InnoDB point lookup by PK: single tree descent, row is right there. By secondary key: descend
  secondary → get PK → descend PK tree ("back to the clustered index"). Wide PKs inflate *every*
  secondary index.
- Postgres lookup: descend index → TID → fetch heap page. Updates write a **new row version**
  at a new TID; normally all indexes need new entries — unless the update touches no indexed
  columns and the new version fits on the same page (**HOT update**: heap-only tuple, indexes
  untouched — a big deal for write performance).
- Range scans: clustered = sequential disk reads of the data itself; Postgres range scan on a
  poorly-correlated column = random heap hops (planner may switch to bitmap scan — 4.5).

### 4. Visualization (ASCII)
```
InnoDB (clustered on PK)                 Postgres (heap + secondary indexes)
      PK B+Tree                           idx_email B+Tree        HEAP (unordered)
   [10|20|30...]                           [a@x → (p3,s7)]       page1 [rowA][rowB]
   leaves = FULL ROWS                      [b@y → (p1,s2)]       page2 [rowC][rowD]
                                                    │             page3 [rowE]...
secondary idx_email:                                └──TID───────────▶ direct fetch
   [a@x → PK 20] ──▶ descend PK tree ──▶ row
   (two tree descents)                   (one descent + heap page fetch)

UPDATE non-indexed column:
InnoDB: rewrite row in place (clustered page)
PG: new version; HOT if same page & no indexed col changed → indexes untouched ✔
```

### 5. Real Production Example
A multi-tenant SaaS on MySQL keys `events` with PK `(tenant_id, created_at, id)` — all a
tenant's recent events are physically contiguous → tenant dashboards read a handful of pages.
The same schema ported to Postgres lost that locality (heap is insert-ordered); the fix was
BRIN/btree on `(tenant_id, created_at)` + periodic `pg_repack` ordering, or partitioning by
tenant bucket. Interviewers use this to test whether you know the storage difference has
*design* consequences.

### 6. Common Interview Questions
- "Clustered vs non-clustered index?" (and "how does Postgres differ from MySQL here?")
- "Why does InnoDB secondary lookup do two tree traversals?"
- "Why should InnoDB PKs be small and sequential?" (secondary index size; page splits)
- "What's a HOT update?" (Postgres senior signal)
- "What does CLUSTER do in Postgres and what's its catch?" (one-time, exclusive lock, not maintained)

### 7. Common Mistakes
- Saying "the PK is the clustered index" about Postgres.
- Choosing UUID PKs in InnoDB → clustered page-split storm *and* fat secondary indexes.
- Overlooking that in InnoDB a covering secondary index avoids the second descent
  (index contains the PK implicitly).
- Assuming physical order persists in Postgres after `CLUSTER`.

### 8. Best Practices
- InnoDB: small monotonic PK always; put frequently-range-scanned dimension first in the PK
  only when the access pattern justifies it.
- Postgres: rely on indexes + correlation; consider partitioning for locality; design for HOT
  (avoid indexing hot-updated columns; `fillfactor` 85–90 on churn tables).
- Know which engine your interview question is about — ask if ambiguous; it changes the answer.

### 9. Coding Questions
1. For InnoDB table `orders(PK id bigint, INDEX(user_id))`: count tree descents for
   (a) `WHERE id=5`, (b) `WHERE user_id=7` selecting `*`, (c) `WHERE user_id=7` selecting
   `user_id, id` only.
2. Postgres table with indexes on (a) `status` (updated constantly) — explain why removing that
   index doubled write throughput (non-HOT → HOT updates).

### 10. SQL Examples
```sql
-- Postgres: check index/heap correlation (drives range-scan cost)
SELECT attname, correlation FROM pg_stats
WHERE tablename = 'orders' AND attname IN ('id','created_at','user_id');

-- One-time physical reorder (locks table exclusively!)
CLUSTER orders USING idx_orders_created;

-- HOT update ratio (are updates dodging index maintenance?)
SELECT n_tup_upd, n_tup_hot_upd,
       round(n_tup_hot_upd::numeric / nullif(n_tup_upd,0), 2) AS hot_ratio
FROM pg_stat_user_tables WHERE relname = 'orders';
```

### 11. Optimization Techniques
- InnoDB: exploit clustering — design the PK so your hottest range scan is a physical scan.
- Postgres: `fillfactor=90` + drop indexes on frequently-updated columns to maximize HOT.
- `pg_repack` for online physical reordering / bloat removal without CLUSTER's lock.

### 12. Follow-up Questions
- "Why do Postgres index-only scans need a visibility map?" (heap holds MVCC visibility;
  see 4.5)
- "You migrate MySQL→Postgres and tenant queries slow down 5x — hypothesis?" (lost clustering
  locality)
- "InnoDB: why can a covering index be even more valuable than in Postgres?" (skips the second
  descent entirely)

---

## Chapter 4.3 — Composite Indexes & the Leftmost Prefix Rule

### 1. Why Interviewers Ask This
The most practical index question there is: "given this query, design the index" — and it's
almost always a composite. Column *order* is where candidates fail.

### 2. Core Concept
A composite index on `(a, b, c)` sorts entries by `a`, then `b` within `a`, then `c` within
`(a,b)` — like a phone book (last name, first name, middle).

**Leftmost prefix rule**: the index can efficiently serve predicates that constrain a
*contiguous prefix* of the columns:
- `a = ?` ✔  `a = ? AND b = ?` ✔  `a = ? AND b = ? AND c = ?` ✔
- `b = ?` alone ✖ (b values are scattered across all a's)
- `a = ? AND c = ?` → index navigates on `a`, then **filters** c inside the a-range (c isn't
  contiguous without b).

**Range stops the key**: after a range/inequality on a column, later columns can't be used for
navigation — `a = ? AND b > ? AND c = ?` navigates on (a, b-range), filters c.
Hence the design rule: **equality columns first, then the (one) range column, then
ORDER BY/covering columns**. ("ESR": Equality, Sort, Range — MongoDB's mnemonic, works for SQL
with the nuance that sort-then-range vs range-then-sort depends on which preserves order.)

**ORDER BY**: an index on `(a, b)` serves `WHERE a = ? ORDER BY b` with zero sorting. Mixed
directions need matching index directions (`(a ASC, b DESC)`).

Column order also decides **reusability**: `(a,b)` serves a-only queries → an extra `(a)` index
is redundant.

### 3. Internal Working
The B+Tree key is the concatenation `(a,b,c)`; comparison is lexicographic. `a=5 AND b=7`
descends directly to the `(5,7,*)` leaf range and walks it. `b=7` alone would require probing
inside every distinct `a` — Postgres *can* still choose the index and filter (or in some
engines "skip scan"), but it reads the whole index → usually not worth it → planner picks
seq scan → "why is my index ignored" (4.6).

### 4. Visualization (ASCII)
```
Index (city, age):  entries sorted lexicographically
(Austin,22) (Austin,25) (Austin,31) │ (Boston,19) (Boston,25) │ (Cairo,40) ...
└────── city=Austin contiguous ─────┘

WHERE city='Boston' AND age=25   → descend to (Boston,25): direct ✔
WHERE city='Boston' AND age>20   → descend to (Boston,20), walk while city=Boston ✔
WHERE age=25                     → 25s scattered: (Austin,25),(Boston,25)... ✖ full index
WHERE city>'B' AND age=25        → range on city first → age unusable for navigation
                                   (equality first, THEN range!)

ORDER BY: WHERE city='Austin' ORDER BY age  → rows come out pre-sorted, no Sort node ✔
```

### 5. Real Production Example
Uber-style trips query: `WHERE driver_id = ? AND status = 'completed' AND started_at >= ?
ORDER BY started_at DESC LIMIT 20`. Correct index: `(driver_id, status, started_at DESC)` —
two equalities, then the range/sort column (here range and sort are the same column: ideal).
The team originally had `(started_at, driver_id)` — planner scanned weeks of index for one
driver. Flipping column order took p99 from 900ms to 3ms. This *exact* shape is the most common
index-design interview exercise.

### 6. Common Interview Questions
- "Index on (a,b,c): which of these five WHERE clauses can use it, and how fully?"
- "Design the index for this query." (state the ESR reasoning aloud)
- "Does `(a,b)` make a separate `(a)` index unnecessary? What about `(b)`?"
- "Why is `(range_col, eq_col)` worse than `(eq_col, range_col)`?"
- "How do you index `WHERE a=? ORDER BY b DESC LIMIT 10`?"

### 7. Common Mistakes
- Putting the range/timestamp column first "because we always filter by date."
- One index per column (`(a)`, `(b)`, `(c)`) expecting them to combine like a composite —
  bitmap-AND exists but is far weaker than the right composite.
- Ignoring ORDER BY when designing — the sort is often the expensive part LIMIT-queries need
  the index for.
- Redundant indexes (`(a)` alongside `(a,b)`) taxing every write.
- Believing "most selective column first" universally — for a *single* query the prefix-usability
  and ESR rules dominate; selectivity-first matters when comparing equality columns that are
  all always present.

### 8. Best Practices
- Design from the query set, not the table: list the WHERE/ORDER BY shapes, then cover them
  with the fewest composites exploiting prefixes.
- Equality columns (always-present ones first) → then the sort column if it lets LIMIT
  short-circuit → then range → then INCLUDE covering columns (4.4).
- Verify with `EXPLAIN`: you want `Index Cond:` to contain all intended columns; anything under
  `Filter:` is being checked row-by-row after navigation.

### 9. Coding Questions
1. Given queries: `(tenant_id=?, created_at range, ORDER BY created_at DESC)`,
   `(tenant_id=?, status=?)`, `(tenant_id=? , status=?, created_at range)` — design the minimal
   index set. (One index `(tenant_id, status, created_at DESC)` + one `(tenant_id, created_at DESC)`.)
2. For `WHERE a=1 AND c=3` on index `(a,b,c)`: describe exactly which part navigates and which
   filters, and estimate rows read if a=1 has 100k rows and c=3 matches 1%.

### 10. SQL Examples
```sql
CREATE INDEX CONCURRENTLY idx_trips_driver
ON trips (driver_id, status, started_at DESC);

EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM trips
WHERE driver_id = 42 AND status = 'completed'
  AND started_at >= now() - interval '30 days'
ORDER BY started_at DESC
LIMIT 20;
-- Want: Index Scan using idx_trips_driver
--       Index Cond: (driver_id=42 AND status='completed' AND started_at >= ...)
--       (no Sort node, Limit stops after 20 entries)

-- Anti-pattern check: is a column being filtered instead of navigated?
-- "Filter: (status = 'completed')" under an index scan = wrong column order.
```

### 11. Optimization Techniques
- Merge overlapping indexes into one composite serving multiple query shapes via prefixes.
- Match index direction to ORDER BY for mixed-direction sorts.
- If you truly need `b`-only queries too, that's a second index — measure whether the write tax
  is worth it.

### 12. Follow-up Questions
- "MySQL 8 / Oracle have skip scans — what do they do and when do they help?" (iterate distinct
  a values, probe b within each; helps only when a has few distinct values)
- "Index is `(a,b)` and the query is `WHERE a IN (1,2,3) AND b = 5` — how does the scan work?"
  (three sub-descents, one per a value — IN behaves like multiple equalities)
- "Why might `(a,b)` beat `(b,a)` even if b is more selective?" (a is the always-present
  equality / prefix reuse for a-only queries / ORDER BY b within a)

---

## Chapter 4.4 — Covering, Partial & Unique Indexes

### 1. Why Interviewers Ask This
These three are the "senior toolkit": covering indexes remove heap access entirely, partial
indexes exploit workload skew, unique indexes are correctness tools. Interviewers use them to
see if you optimize with intent rather than blanket indexing.

### 2. Core Concept
- **Covering index**: contains every column the query needs → **Index-Only Scan**, heap never
  touched. Postgres: either put columns in the key or use
  `INCLUDE (col, ...)` (payload-only: not sortable/searchable, but covering — keeps the key
  compact and works with UNIQUE).
- **Partial index**: `CREATE INDEX ... WHERE predicate` — indexes only matching rows. Tiny,
  cheap to maintain, and *only* usable when the query's WHERE provably implies the predicate.
  Killer feature for skewed data: index the 0.1% `status='pending'` rows, ignore the billions
  of `'done'`.
- **Unique index**: enforces uniqueness (it *is* how PK/UNIQUE constraints are implemented);
  combines with partial → **conditional uniqueness** ("one active subscription per user") and
  with expressions → **normalized uniqueness** (`lower(email)`).

### 3. Internal Working
- Index-only scans in Postgres must still answer MVCC visibility: the **visibility map** marks
  heap pages where all tuples are visible to everyone; for those, no heap check. Pages dirtied
  since last VACUUM force heap fetches (`Heap Fetches: N` in EXPLAIN — high N = vacuum needed).
- Partial index maintenance: writes touch it only when the row matches the predicate — this is
  why it's nearly free on the write path for rare states.
- Unique enforcement: insert descends; on existing equal key, if the owning transaction is
  still in flight, the inserter **waits** (this serializes concurrent same-key inserts — the
  mechanism behind `ON CONFLICT`).

### 4. Visualization (ASCII)
```
Normal index scan:            Index-Only Scan:
index leaf → TID → HEAP page  index leaf (has all needed cols) → done
   (extra random I/O per row)     └─ visibility map says "page all-visible" ✔
                                     else fallback heap fetch (Heap Fetches: N)

Partial index on WHERE status='pending' (0.1% of 1B rows):
full index: 1B entries, ~30GB        partial: 1M entries, ~30MB → fits in cache
write to 'done' rows: no index touch ✔

Conditional uniqueness:
UNIQUE (user_id) WHERE status='active'
user 7: [active]✔ [cancelled][cancelled] — second 'active' insert → violation
```

### 5. Real Production Example
Job-queue pattern (used at every company): workers poll
`SELECT id FROM jobs WHERE status='pending' ORDER BY created_at LIMIT 100`. Table is 500M rows,
99.9% terminal states. Partial index `ON jobs (created_at) WHERE status='pending'` is a few MB,
always cached, and the poll is a sub-ms index-only-ish scan. Without it: full index (or seq
scan) over half a billion rows every few seconds. Follow-up they'll ask: pair it with
`FOR UPDATE SKIP LOCKED` (Module 6) for concurrent workers.

### 6. Common Interview Questions
- "What's a covering index / index-only scan, and what can prevent the 'only' part in Postgres?"
  (visibility map / vacuum)
- "INCLUDE vs putting the column in the key?" (payload not searchable/sortable; smaller
  internal pages; works with UNIQUE)
- "How do you index a status column where 99% of rows are 'done'?" (partial — NOT a plain index
  on the low-cardinality column)
- "Enforce one active session per user at the DB level."
- "Why did `Heap Fetches` spike and the index-only scan get slow?" (bloat/dirty pages → vacuum)

### 7. Common Mistakes
- Covering "just in case" with many INCLUDEs → fat index, write amplification, less of it cached.
- Partial index whose predicate the query doesn't literally imply (`WHERE status = ANY($1)` can't
  use `WHERE status='pending'` index) — parameterized predicates break partial-index matching.
- Expecting index-only scans without healthy autovacuum.
- Application-level uniqueness checks (SELECT then INSERT) instead of unique indexes — race
  conditions; the DB check is the only atomic one.

### 8. Best Practices
- Design covering indexes for the handful of hottest, narrowest queries (id-list fetches,
  existence checks, pagination keys).
- Partial indexes for: rare states (pending/failed), soft-delete filters
  (`WHERE deleted_at IS NULL`), tenant-specific hot subsets.
- Express business uniqueness in DDL: partial unique + expression unique indexes are executable
  specifications.
- Monitor `Heap Fetches` and `n_dead_tup`; tune autovacuum per hot table
  (`autovacuum_vacuum_scale_factor` down).

### 9. Coding Questions
1. Make this an index-only scan: `SELECT user_id, created_at FROM orders WHERE user_id = ?
   AND created_at >= ?` — write the index (key `(user_id, created_at)`; nothing else needed —
   explain why INCLUDE is unnecessary here).
2. Enforce: at most one default payment method per user; emails unique case-insensitively;
   SKU unique among non-deleted products. (Three indexes.)

### 10. SQL Examples
```sql
-- Covering with INCLUDE (key stays compact & unique-compatible)
CREATE UNIQUE INDEX idx_users_email ON users (lower(email)) INCLUDE (id, display_name);

-- Partial: hot subset only
CREATE INDEX idx_jobs_pending ON jobs (created_at) WHERE status = 'pending';

-- Conditional uniqueness
CREATE UNIQUE INDEX one_default_pm ON payment_methods (user_id) WHERE is_default;

-- Soft-delete-aware uniqueness
CREATE UNIQUE INDEX sku_live ON products (sku) WHERE deleted_at IS NULL;

-- Verify index-only behavior
EXPLAIN (ANALYZE, BUFFERS)
SELECT user_id, created_at FROM orders WHERE user_id = 42 AND created_at >= '2026-01-01';
-- Want: Index Only Scan ... Heap Fetches: 0
```

### 11. Optimization Techniques
- Aggressive autovacuum on tables backing index-only scans (visibility map freshness is the
  whole trick).
- Replace `(status)` full index with partial per hot status; drop the full one.
- Covering index as a "vertical partition": for a wide table with one hot narrow query, the
  covering index acts as a narrow copy of the table.

### 12. Follow-up Questions
- "The partial index stopped being used after switching to a prepared statement with $1 for
  status — why?" (planner can't prove predicate implication for parameters; generic plan)
- "How would you do 'one active per user' in MySQL, which lacks partial indexes?" (generated
  column trick: nullable column = user_id when active else NULL, unique on it)
- "When does a covering index become the wrong call?" (write-heavy column in payload; index
  approaching table size)

---

## Chapter 4.5 — Scan Types: Sequential, Index, Index-Only, Bitmap

### 1. Why Interviewers Ask This
Reading EXPLAIN requires knowing the four access paths and — the senior twist — **why seq scan
is often correct**. "Why is Postgres not using my index?" is the most common real-world question
this knowledge answers.

### 2. Core Concept
| Scan | What it does | When optimal |
|---|---|---|
| **Seq Scan** | Read the whole heap, sequentially | Large fraction of rows needed (rule of thumb: >5–10%), tiny tables, no usable index |
| **Index Scan** | Descend B+Tree, fetch heap row per match (random I/O) | Few rows, high selectivity, or ORDER BY exploitation |
| **Index-Only Scan** | Index Scan without heap fetches (covering + visibility map) | Covering queries on well-vacuumed tables |
| **Bitmap Index/Heap Scan** | Collect all matching TIDs into a bitmap, sort by page, then fetch heap pages sequentially | Medium selectivity (thousands–millions of rows); combining multiple indexes (BitmapAnd/Or) |

The core economics: an index scan costs a **random heap page read per row** (worst case); a seq
scan costs **every page once, sequentially**. There's a crossover — around a few percent of the
table — where seq scan wins. Bitmap scan is the middle ground: index precision + sequential heap
access, at the cost of losing index order (needs a Sort if you wanted ORDER BY).

### 3. Internal Working
- Planner computes: seq = pages × seq_page_cost; index = descents + matched_rows ×
  (random_page_cost × correlation-adjusted heap cost); bitmap = index read + bitmap build +
  sorted page fetches. `random_page_cost` default 4 assumes spinning disk — on SSD/cloud set
  1.1–1.5 or the planner over-penalizes index scans (a real, common misconfiguration).
- Correlation matters: index on a column physically correlated with heap order (like
  insert-time timestamps) makes index range scans nearly sequential → cheap.
- Bitmap can degrade to **lossy** mode when `work_mem` is exceeded (stores pages, not tuples →
  rechecks rows: `Recheck Cond`).

### 4. Visualization (ASCII)
```
selectivity →  0.001%          0.1%            5%              80%
best path  →  Index Scan   Index/Bitmap    Bitmap/Seq        Seq Scan

Index Scan heap access:        Bitmap Scan heap access:
idx→p9, idx→p2, idx→p9,        idx→{p2,p2,p5,p9,p9,p9}
idx→p5 (random, p9 twice!)      └─ sort TIDs → read p2,p5,p9 once each, in order

BitmapAnd (two single-col indexes standing in for a missing composite):
idx_a(a=1) → bitmap A ┐
                      ├─ AND → fetch only pages in both
idx_b(b=2) → bitmap B ┘
```

### 5. Real Production Example
Analytics-ish query on the OLTP DB: `WHERE created_at >= now() - interval '90 days'` on a table
where 90 days = 40% of rows. Engineer adds an index, planner ignores it, engineer force-hints…
and it gets *slower* (40% of a TB via random I/O). Correct outcomes: accept the seq scan,
partition by month (prune to 3 partitions), or BRIN. The interview form: "the planner ignores
my index — is it wrong?" — the senior answer starts with "maybe it's right."

### 6. Common Interview Questions
- "When is a full table scan faster than an index scan?" (guaranteed question)
- "What's a bitmap heap scan and why does Postgres use it?"
- "Explain `Recheck Cond` / lossy bitmaps."
- "Why does `random_page_cost` matter and what should it be on SSDs?"
- "Query uses index for `LIMIT 10` but seq scan for `LIMIT 10000` — why?" (cost crossover)

### 7. Common Mistakes
- Treating Seq Scan in EXPLAIN as automatically bad.
- Comparing timings with cold vs warm cache and concluding the plan changed.
- Not knowing bitmap scans discard index ordering (surprise Sort node appears).
- Assuming `count(*)` uses "the index" trivially — it can index-only scan but still must check
  visibility (Module 5 covers COUNT).

### 8. Best Practices
- Judge plans by **pages touched** (`BUFFERS`) not by scan-type prejudice.
- Tune `random_page_cost` to storage reality; `effective_cache_size` to actual RAM.
- For medium-selectivity recurring filters, prefer a better composite/partial index over relying
  on BitmapAnd of single-column indexes.

### 9. Coding Questions
1. Table 100GB, 12.8M pages. Query matches 2M rows spread uniformly. Compare page reads:
   seq scan (12.8M sequential) vs index scan (≈2M random) vs bitmap (≈min(2M pages, clustered
   subset) sequentialized) — which wins on SSD vs HDD?
2. From `EXPLAIN (ANALYZE, BUFFERS)` output showing `Bitmap Heap Scan ... Heap Blocks: exact=
   41235 lossy=182000`, diagnose and fix (work_mem too small for the bitmap).

### 10. SQL Examples
```sql
-- Watch the crossover live
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE created_at >= now() - interval '1 hour';
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE created_at >= now() - interval '1 year';
-- hour → Index Scan; year → Seq Scan (both correct)

-- SSD-appropriate costing
ALTER SYSTEM SET random_page_cost = 1.1;
SELECT pg_reload_conf();

-- Investigate "index ignored" honestly (session-local experiment)
SET enable_seqscan = off;      -- if index plan is now CHOSEN but SLOWER, planner was right
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
RESET enable_seqscan;
```

### 11. Optimization Techniques
- Increase correlation for hot range columns: partitioning, or BRIN on naturally-ordered data.
- Cluster occasionally (pg_repack) if one range access pattern dominates.
- Parallel seq scans (PG9.6+) make honest big scans much faster — check `Workers Launched`.

### 12. Follow-up Questions
- "Same query, index scan on replica but seq scan on primary — how?" (different stats/settings/
  cache: e.g., ANALYZE timing or cost params differ)
- "How does this decision change in MySQL?" (optimizer cost model differs; no bitmap scans in
  InnoDB — index_merge instead; clustered PK changes heap-fetch economics)
- "What plan do you expect for `WHERE a=1 OR b=2` with separate indexes on a and b?" (BitmapOr)

---

## Chapter 4.6 — When Indexes Fail: Cardinality, Selectivity & Ignored Indexes

### 1. Why Interviewers Ask This
"Why is my index not being used?" is the highest-frequency database question in real work.
The answer catalog below *is* the interview answer.

### 2. Core Concept
**Cardinality** = number of distinct values in a column (`n_distinct`).
**Selectivity** = fraction of rows a predicate matches (matched/total; lower = more selective).
Indexes pay off when predicates are selective. The planner estimates selectivity from
statistics (histograms + most-common-values lists) and compares plan costs — the index loses
when estimated selectivity is poor **or** when the estimate is wrong.

**The "index ignored" catalog** (memorize — this answers the question in any interview):
1. **Low selectivity**: predicate matches too much (status='done' on 95% of rows) — seq scan is
   genuinely cheaper.
2. **Function/expression on the column**: `WHERE date(created_at)=...`, `lower(email)=...` —
   needs a matching expression index.
3. **Type mismatch / implicit cast**: `WHERE bigint_col = '42'::text`-ish situations, joining
   varchar to int, numeric literal against text column — the cast wraps the column.
4. **Leading wildcard / pattern**: `LIKE '%foo'` (no prefix to navigate). Also plain `LIKE`
   under non-C collation needs `text_pattern_ops`.
5. **Leftmost prefix violated**: composite `(a,b)` with only `b` predicated.
6. **OR across columns**: may need BitmapOr or a UNION rewrite; single index can't serve it.
7. **Inequality/NOT**: `<>`, `NOT IN` — matches almost everything.
8. **Stale/insufficient statistics**: planner thinks the predicate matches 40% when it matches
   0.01% (or vice versa) — `ANALYZE`, raise the stats target, extended statistics for
   correlated columns.
9. **Cost misconfiguration**: `random_page_cost=4` on SSD biases against index scans.
10. **Tiny table**: everything fits in one page — seq scan is correct, stop worrying.
11. **Parameterized/generic plans**: prepared statement generic plan can't use a partial index
    or assumes average selectivity (`plan_cache_mode`).
12. **NULL semantics**: `col = NULL` never true; `IS NULL` *is* indexable (btree stores NULLs) —
    but expression/partial coverage may be needed.

### 3. Internal Working
Stats pipeline: `ANALYZE` samples rows → per-column `n_distinct`, MCV list (most common values +
frequencies), equi-depth histogram → selectivity for `col = x`: if x in MCV use its frequency,
else (1 − MCV mass)/(n_distinct − MCV count); ranges use histogram bucket interpolation.
Multi-predicate selectivities multiply assuming **independence** — correlated columns
(city→country) get catastrophically underestimated → `CREATE STATISTICS ... (dependencies)`.
Wrong stats → wrong cost → wrong plan, regardless of what indexes exist.

### 4. Visualization (ASCII)
```
Histogram (created_at):  [Jan|Feb|Mar|...|Dec]  each bucket = 1/12 of rows
WHERE created_at >= Dec-01 → est. ~8% → index viable
WHERE created_at >= Feb-01 → est. ~92% → seq scan

MCV (status): done:0.94  cancelled:0.04  pending:0.02
WHERE status='pending' → 2% → maybe bitmap/partial idx
WHERE status='done'    → 94% → seq scan (index correctly ignored)

Correlation trap: WHERE city='SF' AND state='CA'
independent est: P(city)×P(state) = 0.01×0.03 = 0.0003 (way low if all SF is in CA)
→ planner picks NL for "3 rows", gets 300k → disaster.  Fix: extended statistics.
```

### 5. Real Production Example
Netflix-scale table, query `WHERE country='US' AND platform='tv' AND event_date = yesterday`.
Planner multiplies three independent selectivities, estimates 900 rows, picks nested loop into a
join — actual 40M rows (US+tv are correlated), query melts a replica. Fix:
`CREATE STATISTICS (dependencies, ndistinct) ON country, platform` + `ANALYZE`. Second act
interviewers love: after a bulk backfill, everything is slow until `ANALYZE` runs — stale stats
after mass writes.

### 6. Common Interview Questions
- "List reasons an index gets ignored." (rapid-fire the catalog)
- "Define cardinality vs selectivity; how does the planner estimate selectivity?"
- "Index on `email` exists; `WHERE lower(email)=?` seq-scans — fix it two ways."
  (expression index; citext)
- "Query fast with literal, slow as prepared statement — why?" (generic plan/parameter sniffing)
- "When is indexing a boolean column worthwhile?" (almost never plain; partial index on the
  rare value)

### 7. Common Mistakes
- Force-hinting (`enable_seqscan=off` in prod code) instead of fixing stats/predicates.
- Indexing low-cardinality columns whole instead of partial indexes on the rare states.
- Missing that ORMs generate casts/functions (e.g., timezone conversions) that silently break
  sargability.
- Never running `ANALYZE` after bulk loads/migrations.

### 8. Best Practices
- Sargable predicates by habit: bare column on the left, constants/expressions on the right.
- After bulk changes: `ANALYZE` explicitly; for skewed big tables raise per-column stats target
  (`ALTER TABLE ... ALTER COLUMN ... SET STATISTICS 1000`).
- Extended statistics for known correlated pairs.
- Test with production-shaped data — 1k-row dev tables seq-scan everything and hide all of this.

### 9. Coding Questions
1. For each, say if the index on the mentioned column is used and why:
   `WHERE upper(code)='X'`; `WHERE price*1.1 > 100`; `WHERE created_at::date = current_date`;
   `WHERE id IN (1,2,3)`; `WHERE name LIKE 'ab%'`; `WHERE name LIKE '%ab'`.
2. Write the fix for each broken one (expression index / rewrite to sargable / trigram index).

### 10. SQL Examples
```sql
-- Inspect what the planner believes
SELECT attname, n_distinct, most_common_vals, most_common_freqs
FROM pg_stats WHERE tablename = 'orders' AND attname = 'status';

-- Correlated-column fix
CREATE STATISTICS orders_geo (dependencies, ndistinct) ON country, platform FROM events;
ANALYZE events;

-- Expression index to restore sargability
CREATE INDEX ON users (lower(email));
-- and/or rewrite: WHERE created_at >= d AND created_at < d + 1 instead of ::date

-- Trigram index for %substring% search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX ON products USING gin (name gin_trgm_ops);
SELECT * FROM products WHERE name ILIKE '%widget%';   -- now indexable
```

### 11. Optimization Techniques
- `auto_explain` with `log_min_duration` to capture real bad plans with real parameters.
- `plan_cache_mode = force_custom_plan` for statements whose parameter skew breaks generic plans.
- Periodic index audit: unused indexes (drop), missing indexes (from `pg_stat_statements`
  top offenders — Module 5/11).

### 12. Follow-up Questions
- "n_distinct is wildly wrong on a 2B-row table — why and what do you do?" (sampling limits;
  set n_distinct manually via ALTER TABLE ... SET (n_distinct=...))
- "How do hints work in MySQL/Oracle and why does Postgres refuse them?" (philosophy: fix
  inputs, not outputs; pg_hint_plan exists if forced)
- "Explain exactly why the generic plan can't use a partial index." (predicate proof requires
  the parameter value)

---

## Chapter 4.7 — How to Choose Indexes (Design Method)

### 1. Why Interviewers Ask This
This is the synthesis question: "here's the workload — design the indexes." It tests everything
above at once, plus the discipline of *not* over-indexing.

### 2. Core Concept — The Method
1. **Inventory the queries** (from code / pg_stat_statements), not the table. Rank by
   frequency × latency.
2. For each hot query, write the ideal index: **equality columns → sort column → range column →
   INCLUDE covering columns**; partial WHERE for skewed constant predicates.
3. **Merge**: collapse indexes that are prefixes of others; one composite often serves several
   queries.
4. **Price the writes**: each index taxes every insert and non-HOT update; on write-heavy tables
   demand stronger justification.
5. **Verify** with EXPLAIN (ANALYZE, BUFFERS) against production-scale data; confirm
   Index Cond vs Filter, no unexpected Sort, Heap Fetches ≈ 0 where intended.
6. **Monitor and prune**: unused-index report monthly; every index must earn its keep.

### 3. Internal Working
Why merging works: a B+Tree on `(a,b,c)` *contains* perfect indexes on `(a)` and `(a,b)` as
prefixes. Why pricing writes matters: an insert into a table with k indexes does 1 heap write +
k index descents/inserts (plus WAL for each); index count linearly scales write cost and
vacuum work.

### 4. Visualization (ASCII)
```
Query set                                   Index plan
Q1: WHERE user_id=? ORDER BY created DESC   ┐
Q2: WHERE user_id=? AND created>=?          ├─▶ (user_id, created_at DESC)   [serves Q1,Q2]
Q3: WHERE user_id=? AND status=? ORDER BY created DESC
                                            └─▶ (user_id, status, created_at DESC) [Q3; also Q1? no—
                                                status gap breaks prefix for Q1's sort]
Q4: WHERE status='pending' (0.1%)           ──▶ partial (created_at) WHERE status='pending'
write cost: 3 indexes ≈ acceptable; audit quarterly
```

### 5. Real Production Example
Stripe-like `payments` table review: 14 indexes accreted over years; write p99 degrading and
autovacuum永 behind. Audit finds 5 unused, 3 redundant prefixes, 2 replaceable by one composite +
partial. Down to 6 indexes: insert latency −40%, index storage −60%, no read regressions. The
interview lesson: index design is a *portfolio* problem, not per-query.

### 6. Common Interview Questions
- "Design indexes for this schema + these five queries." (the standard exercise)
- "How do you decide an index is worth its write cost?"
- "How do you find missing and unused indexes in production?"
- "What changes about indexing strategy for a write-heavy vs read-heavy table?"

### 7. Common Mistakes
- Indexing every column / every FK reflexively without workload evidence (FK child columns are
  usually justified — but by the delete/join pattern, cite it).
- Designing for one query in isolation and accumulating near-duplicates.
- Never revisiting: indexes for deleted features running forever.
- Skipping the verify step — "should use the index" is not "does."

### 8. Best Practices
- Keep an "index ledger": every index annotated with the queries it serves.
- Standard per-table starting kit: PK; FK columns used in joins/deletes; the main
  list-view composite `(tenant/user, created_at DESC)`; partial for hot rare states. Everything
  else must argue its way in.
- Create with `CONCURRENTLY`, drop with `CONCURRENTLY` (PG 14+ for drop), always.

### 9. Coding Questions
1. Given `messages(id, chat_id, sender_id, created_at, is_deleted, body)` and queries:
   recent messages per chat (paginated), unread count per chat, user's sent messages by date,
   full-text search in a chat — produce the full index DDL with justifications.
2. Write the two monitoring queries: top time-consuming statements missing indexes
   (pg_stat_statements join) and unused indexes (pg_stat_user_indexes).

### 10. SQL Examples
```sql
-- The chat example answered:
CREATE INDEX ON messages (chat_id, created_at DESC) WHERE NOT is_deleted;  -- feed + pagination
CREATE INDEX ON messages (sender_id, created_at DESC);                      -- user's messages
CREATE INDEX ON messages USING gin (to_tsvector('english', body));          -- search
-- unread: usually a per-member counter table, not an index (design > index)

-- Unused index report
SELECT s.indexrelname, s.idx_scan,
       pg_size_pretty(pg_relation_size(s.indexrelid)) AS size
FROM pg_stat_user_indexes s
JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE s.idx_scan = 0 AND NOT i.indisunique
ORDER BY pg_relation_size(s.indexrelid) DESC;
```

### 11. Optimization Techniques
- HypoPG extension: hypothetical indexes — test whether the planner *would* use an index before
  paying to build it.
- Stage big index builds off-peak; on partitioned tables build per-partition then attach.
- For multi-tenant systems, lead almost every index with `tenant_id` — locality + prefix reuse.

### 12. Follow-up Questions
- "An index build with CONCURRENTLY failed halfway — what state is the system in?" (INVALID
  index: taxes writes, serves no reads — must drop/rebuild)
- "How would your strategy differ on the read replica vs primary?" (same physical indexes —
  streaming replicas can't diverge; that's a partitioning-of-workload argument, or logical
  replication if you truly need different indexes)
- "Index or partition — how do you decide?" (selectivity/pruning granularity vs maintenance;
  Module 7)

---

# Module 4 — Practice Problems

## Easy (5)
1. Index `(customer_id, order_date, status)` exists. For each query say used/partially
   used/unused: `WHERE customer_id=1`; `WHERE order_date>'2026-01-01'`; `WHERE customer_id=1
   AND status='paid'`; `WHERE customer_id=1 AND order_date>'2026-01-01' ORDER BY order_date`.
2. Why can `LIKE 'john%'` use a btree but `LIKE '%john'` cannot? What index fixes the latter?
3. Compute approximate B+Tree height for 50M rows with fanout 250, and the max page reads for a
   point lookup with a cold cache.
4. `WHERE status='active'` matches 60% of rows. Index or not? What if it matches 0.5%?
5. Explain `Heap Fetches: 48210` on an Index Only Scan and the fix.

## Medium (5)
6. Design the minimal index set for: `WHERE seller_id=? AND state=? ORDER BY listed_at DESC
   LIMIT 24`; `WHERE seller_id=? ORDER BY listed_at DESC`; `WHERE state='pending_review'`
   (0.2% of rows) — justify each column position.
7. A prepared statement runs 200x slower than the same query with literals. Explain generic vs
   custom plans, how partial-index matching fails, and two fixes.
8. InnoDB table, PK is UUIDv4 char(36), five secondary indexes, heavy inserts. Enumerate every
   cost this design incurs and the migration path.
9. `EXPLAIN (ANALYZE, BUFFERS)` shows: `Bitmap Heap Scan (Recheck Cond..., Heap Blocks:
   exact=1200 lossy=890000)` under `BitmapAnd` of two indexes. Diagnose both problems and fix
   (work_mem; replace BitmapAnd with a composite).
10. Soft-deleted rows are 70% of a table; all queries filter `deleted_at IS NULL`. Redesign the
    indexing (partial everything) and estimate the size/perf impact.

## Hard (5)
11. Time-series table, 4B rows, insert-only, queries are `device_id + time range`. Compare
    btree `(device_id, ts)`, BRIN on `ts`, and monthly partitions + `(device_id, ts)` per
    partition — for insert cost, query cost, and storage. Recommend and defend.
12. The planner estimates 12 rows, actual is 2.1M, for `WHERE city='SF' AND category='food'`.
    Walk the full diagnosis (MCV/histogram inspection, independence assumption) and fix chain
    (ANALYZE → stats target → extended statistics → rewrite), explaining what each step changes.
13. Design uniqueness for: "an email may be reused after account deletion, but only one live
    account per email; deleted accounts keep their email for audit." Write the DDL and prove the
    race-safety of concurrent signups.
14. A covering index made reads perfect but write p99 regressed 30% and autovacuum can't keep
    up. Explain the mechanics (non-HOT updates, index churn, visibility map invalidation) and
    design the compromise (drop payload columns, fillfactor, split hot/cold columns to a
    separate table).
15. You may add exactly ONE index to `events(tenant_id, user_id, type, ts, payload)` serving:
    (a) tenant dashboard: `tenant_id + ts range ORDER BY ts DESC`; (b) user timeline:
    `tenant_id + user_id ORDER BY ts DESC`; (c) type analytics: `tenant_id + type + ts range`.
    Choose, quantify what each query pays with your choice, and argue why no single index serves
    all three optimally.

---

*Next: [Module 5 — Query Optimization](module-05-query-optimization.md)*

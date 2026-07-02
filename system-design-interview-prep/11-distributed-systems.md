# Module 11 — Distributed Systems Toolkit

The named techniques interviewers expect at senior/staff level. Each is a small
idea with outsized leverage; each appears by name in follow-up questions ("how
would you avoid rehashing everything?" — they're fishing for consistent hashing).

---

## 11.1 Consistent Hashing

### Why Interviewers Ask This

It's the standard answer to "you added a cache/DB node — now what?" and the core of
Dynamo, Cassandra, and most distributed caches. Expect to explain the ring *and*
virtual nodes.

### Core Concept & Internal Working

Problem: `hash(key) mod N` remaps nearly *every* key when N changes → a scaling
event becomes a fleet-wide cold cache / data migration.

Consistent hashing: hash servers and keys onto a circular space (0..2^64); each key
belongs to the first server clockwise from it. Adding/removing a server only moves
the keys in its arc — **~K/N keys move instead of ~all**.

```
        0 ─────────────► 2^64 (wraps)
   ──[S3]───k1──[S1]──k2─k3──[S2]───k4──[S3...]──
   k1→S1, k2,k3→S2, k4→S3
   add S4 between S1 and S2: only k2,k3's arc splits; k1,k4 untouched ✓
```

**Virtual nodes** fix the two remaining problems (uneven arcs; a leaving node dumps
its whole load on one neighbor): each physical server gets 100–1000 tokens on the
ring, so load evens out statistically, departures spread across many neighbors, and
heterogeneous hardware gets proportional token counts. Replication: store each key
on the next R distinct physical successors.

Variants worth naming: **jump consistent hash** (no ring state, perfect balance,
but only append/remove-at-end), **rendezvous (HRW) hashing** (highest-random-weight;
simple, great for small N), Maglev hashing (LB lookup tables).

### Real Production Example

DynamoDB/Cassandra/Riak partitioning; Memcached client libraries (ketama);
Envoy/HAProxy ring-hash LB for session/cache affinity; Discord's ring for routing
guilds to nodes.

### Interview Questions

1. Why does mod-N break, quantitatively? (changing N=10→11 remaps ~10/11 of keys)
2. What exactly do virtual nodes buy? (balance, smooth rebalancing, weighting)
3. How do you get replication out of the ring? (next R distinct successors)

---

## 11.2 Bloom Filters

### Core Concept & Internal Working

A probabilistic set membership structure: bit array of m bits + k hash functions.
Insert: set k bits. Query: if any bit is 0 → **definitely not present**; if all
1 → **probably present** (false-positive rate tunable: ~1% at ~10 bits/element;
no false negatives; no deletes in the basic form — counting Bloom filters allow
them at 4× space).

The design move it enables: **skip expensive lookups for things that don't exist**.

- LSM storage engines (RocksDB, Cassandra, HBase): a Bloom filter per SSTable — a read checks the filter before touching disk; misses skip whole files. This is *the* answer to "how do LSM reads stay fast".
- Cache-penetration defense: filter of "keys that exist" in front of DB, so attackers querying random missing keys don't hammer it.
- CDN "cache on second hit" (Akamai: filter of seen-once URLs keeps one-hit wonders out of cache), Chrome's old malicious-URL check, distributed joins, dedup in crawlers ("have I seen this URL?").

Sizing soundbite: 1B items at 1% FP ≈ 1.2 GB — a billion-key existence check in RAM.
Cousins to name-drop: **Cuckoo filters** (deletes, better space at low FP),
**HyperLogLog** (cardinality counting, 12 KB for billions ±2% — "count distinct
daily users"), **Count-Min Sketch** (approximate frequencies — heavy-hitter/hot-key
detection).

### Interview Questions

1. Where does a Bloom filter sit in an LSM read path and what does it save?
2. A false positive occurs — what happens in each of your use cases? (harmless extra lookup; must be tolerable by design)
3. Count unique visitors across 1B events in near-zero memory? (HyperLogLog)

---

## 11.3 Merkle Trees (Overview)

### Core Concept

A tree of hashes: leaves = hashes of data blocks; parents = hash of children; the
**root hash summarizes the entire dataset**. Compare two replicas: roots equal ⇒
identical (one comparison); differ ⇒ descend only into differing subtrees ⇒ locate
divergent blocks in **O(log n)** comparisons instead of shipping/scanning
everything.

Where it earns its name in interviews: **anti-entropy repair** in Dynamo-style
stores (Cassandra `nodetool repair` builds Merkle trees per range and syncs only
differing partitions), **Git** (commits point to hash trees — cheap diff/integrity/
dedup), **blockchains** (transaction inclusion proofs in O(log n)), certificate
transparency logs, and file-sync/dedup systems (content-addressed chunks).

```
        root=H(AB,CD)          replicas compare roots → differ
       /            \          → compare H(AB): equal → skip whole left half
   H(AB)            H(CD)      → compare H(CD): differ → descend → block D differs
   /   \            /   \      → transfer ONLY block D
 H(A) H(B)       H(C) H(D)
```

### Interview Question

"Two 10 TB replicas may have diverged after a partition — how do you find and fix
the differences without comparing 10 TB?"

---

## 11.4 Vector Clocks (Overview)

### Core Concept

Logical clocks that capture **causality** without synchronized time. Each node
keeps a vector of counters (one slot per node); increment your slot on local
events, merge (element-wise max) on receive.

- VC(A) < VC(B) element-wise ⇒ A **happened-before** B (B knew about A — safe to overwrite A).
- Neither ≤ the other ⇒ **concurrent** ⇒ a true conflict that timestamps would have silently destroyed (last-writer-wins picks an arbitrary winner under clock skew).

That's the interview point: vector clocks *detect* concurrent writes so the system
can keep **siblings** and resolve them (Dynamo returned conflicting cart versions
to the app, which merged by union; Riak exposed siblings). Costs: O(nodes) metadata
per key, pruning complexity — which is why many systems (Cassandra) accept LWW
instead, and modern designs often prefer **CRDTs** (data types that merge
automatically: G-counters, OR-sets — collaborative editing, distributed counters).
Name **Lamport clocks** as the scalar little sibling: total order, but can't
distinguish concurrency.

### Interview Question

"Two clients update the same key on opposite sides of a partition. How does the
system even *know* it's a conflict, and what are the resolution options?"
(vector clocks/siblings → app merge, CRDT, or LWW with data-loss acknowledged)

---

## 11.5 Leader Election

### Core Concept & Internal Working

Many workloads need exactly-one-active: DB primaries, job schedulers, partition
owners, cron singletons. Election = choosing it safely; the hard part is the old
leader that doesn't know it lost (Module 8.5).

Implementations, in the order you should offer them:

1. **Lease-based on a coordination service** (the practical default): candidates race to create an ephemeral node / lease key in ZooKeeper/etcd/Consul (`create /leader` ephemeral; or etcd lease + campaign). Holder = leader; must keep renewing (session heartbeat); crash/partition ⇒ lease expires ⇒ others elect. Kubernetes controllers do exactly this (Lease objects). **Always pair with fencing tokens** (the monotonically increasing election/term number) checked by downstream systems, because a paused ex-leader can wake and act.
2. **Consensus-native** (Raft, Module 8.4): election is built into the replication protocol — for systems that *are* the replicated state (databases, Kafka controllers).
3. Classical algorithms (Bully, ring) — name-check only; production uses 1 or 2.

```
 candidates ──try acquire──► etcd lease "svc/leader" (TTL 10s, term=42)
 winner: leads; renews every 3s; stamps all actions with term 42
 GC-paused winner: lease lapses → new leader term 43 → storage rejects term-42 writes ✓
```

### Interview Questions

1. Elect a singleton job scheduler across 5 instances — design it and kill it with a GC pause; what saves correctness? (fencing)
2. Why not just use a Redis `SETNX` lock as the "election"? (fine informally, but see Redlock caveats — no fencing, replication async; use a real coordination service for correctness-critical roles)

---

## 11.6 Gossip Protocol (Overview)

### Core Concept

Epidemic information spread: every interval, each node exchanges state with a few
random peers; information reaches all N nodes in **O(log N)** rounds with no
coordinator, no SPOF, and per-node load independent of cluster size.

What it carries in practice: **membership and failure detection** (who's in the
cluster, who seems down — Cassandra, Consul/Serf via SWIM, DynamoDB internals),
cluster metadata (schema versions, token ownership), and lightweight aggregates.
SWIM's trick: instead of timeout-only suspicion, ping through *indirect* probes
(ask k others to ping the suspect) → fewer false positives from your own bad link;
"suspect → confirmed" states with incarnation numbers to refute false rumors.

Trade-offs: eventual (seconds of propagation delay — membership views briefly
disagree), bandwidth tuning, and rumors need versioning to die. Contrast with
consensus: gossip disseminates *facts loosely* (scales to thousands of nodes);
consensus decides *values strictly* (small clusters). Big systems use both:
gossip for membership, Raft for the metadata core.

### Interview Question

"How does a 1,000-node Cassandra cluster know a node died without a central
monitor, and why might two nodes briefly disagree about it?"

---

## 11.7 Distributed Locks

### Why Interviewers Ask This

"Prevent double-processing / double-booking" appears in most designs, a naive Redis
lock is subtly broken, and the Kleppmann–Redlock debate is assumed knowledge at
staff level.

### Core Concept & Internal Working

Single-Redis lock done *correctly-for-efficiency*:

```
 acquire: SET lock:{res} {random_token} NX PX 30000     (atomic, owner-tagged, TTL)
 release: Lua — GET == my token ? DEL : no-op            (never delete another's lock)
 extend:  watchdog renews TTL while still working
```

Why TTL: crashed holders must not deadlock the system. Why token: your lock may
have *expired* mid-work and been granted to someone else — blind DEL releases
*their* lock.

The fundamental flaw (Kleppmann): a GC pause / network delay can suspend the holder
past its TTL; it resumes and writes concurrently with the new holder. **The lock
alone cannot guarantee mutual exclusion end-to-end** — the protected resource must
check **fencing tokens** (monotonic lock generation number; storage rejects writes
with a stale token). **Redlock** (quorum of 5 independent Redis nodes) raises
availability of the *lock service* but still doesn't produce fencing tokens or fix
the pause problem — know the critique.

Decision framework to recite:

- **Efficiency lock** (avoid duplicate work; a rare double-run is tolerable — cache refresh, cron): single Redis SET NX is perfect.
- **Correctness lock** (double-run = corruption/money): ZooKeeper/etcd (sessions + monotonic zxid/revision = built-in fencing) **plus token-checking at the resource** — or better, remove the lock: route all ops for a resource to **one partition owner** (Kafka-keyed serialization), or use **DB-native protection** (unique constraints, `SELECT ... FOR UPDATE`, optimistic version checks) — the database is often the best lock manager you already have.

### Interview Questions

1. Implement a Redis lock; now break it with a 40 s GC pause; now fix it. (token + fencing at storage)
2. Efficiency vs correctness locks — classify: cache warmer, seat booking, nightly report, payment capture.
3. When is "no lock" the right answer? (single-writer partition ownership; DB constraints)

---

## 11.8 Clock Synchronization

### Core Concept

Every machine's clock drifts (ppm-level ⇒ ms/day); NTP syncs to ~1–10 ms typical
(worse under load/network jitter) and can **step time backwards**. Consequences you
must design around: cross-machine timestamp ordering is unreliable (LWW conflict
resolution silently loses newer writes under skew — the Cassandra caveat),
timeouts/leases measured across machines are approximate, TTL/cert validation
breaks with bad clocks, and monotonic operations (rate limiting windows, Snowflake
ID generation) must use **monotonic clocks** locally (never wall-clock deltas) and
handle backward steps (Snowflake generators stall or error if time regresses).

The famous fix: **Google TrueTime** (GPS + atomic clocks per datacenter) exposes a
**bounded uncertainty interval** [earliest, latest]; Spanner assigns commit
timestamps and **waits out the uncertainty** (~few ms) before acknowledging —
buying *external consistency* (global serializability with real-time order) at the
cost of that wait. AWS TimeSync/precision hardware clocks now offer microsecond
bounds; CockroachDB approximates with NTP + max-offset assumptions (HLC — hybrid
logical clocks combine physical time with Lamport counters: name-drop worthy).

Rule of thumb to state: **use physical clocks for humans and metrics; use logical
clocks (Lamport/vector/sequence numbers) or single-writer ordering for
correctness.**

### Interview Questions

1. Why is last-writer-wins dangerous, exactly? (skew ⇒ "later" write can carry an *earlier* timestamp ⇒ silent loss)
2. What does TrueTime provide and what does Spanner do with it?
3. Your rate limiter misbehaved when NTP stepped the clock back 2 s — why, and the fix? (wall clock used for interval math → monotonic clock)

---

## 11.9 Eventual Consistency (Revisited, Mechanically)

Module 1.4 placed it on the spectrum; here's the machinery interviewers probe:

- **Convergence mechanisms**: read repair (fix stale replicas on read), hinted handoff (hold writes for down peers), anti-entropy with Merkle trees (background full sync), gossip dissemination. Together: "if writes stop, replicas converge."
- **Conflict handling** (concurrent writes will happen): LWW (simple, lossy), vector clocks + siblings (app merges), **CRDTs** (mathematically mergeable types: counters, sets, maps — Figma/collaborative apps, Riak, Redis CRDTs in Active-Active).
- **What you promise the user**: session guarantees (read-your-writes, monotonic reads — Module 4.2 routing tricks), bounded staleness ("search results ≤ 30 s stale"), and explicit UX for pending states.
- **What you must add operationally**: staleness/lag metrics per replica pipeline, reconciliation jobs (counters re-computed from source), and idempotent consumers everywhere (Module 5.5) because redelivery is part of the deal.

### Interview Question

"Walk me through everything that happens after a partition heals in a Dynamo-style
store." (hinted handoffs replay → read repair on touched keys → Merkle anti-entropy
for the cold rest → conflicts surfaced via vector clocks → app/CRDT merge)

---

## Module 11 Cheat Sheet

```
CONSISTENT HASH  ring 0..2^64, key→next server clockwise; add/remove moves ~K/N.
                 Virtual nodes (100–1000/server): balance + smooth rebalance +
                 weighting. Replicas = next R distinct successors.
BLOOM FILTER     k hashes → bits; "no" is certain, "yes" is probabilistic (~1% @
                 10 bits/elem). LSM SSTable skip, cache-penetration shield, dedup.
                 Cousins: Cuckoo (deletes), HLL (count distinct), CMS (frequencies).
MERKLE TREE      hash tree; compare roots, descend diffs: O(log n) divergence
                 location. Cassandra repair, Git, cert transparency.
VECTOR CLOCK     per-node counters; detects CONCURRENT vs ordered (LWW can't).
                 Siblings → app merge; CRDTs merge automatically; Lamport = scalar.
LEADER ELECTION  etcd/ZK lease + ephemeral + renewal; or Raft-native. ALWAYS
                 fencing tokens (terms) checked downstream. K8s Lease objects.
GOSSIP           random peer exchange, O(log N) spread, no SPOF; SWIM indirect
                 probes + incarnation numbers. Membership/failure detection at
                 1000s of nodes. Loose facts vs consensus's strict values.
DIST. LOCKS      SET NX PX + owner token + Lua release + watchdog. GC pause breaks
                 mutual exclusion ⇒ fencing at the resource. Redlock ≠ fix.
                 Efficiency lock (Redis) vs correctness (ZK/etcd + fencing) vs
                 NO lock (partition ownership, DB constraints) — prefer the last.
CLOCKS           NTP ~ms + backward steps; monotonic clocks for intervals; logical
                 clocks/single-writer for ordering; TrueTime = bounded uncertainty
                 + commit-wait (Spanner external consistency); HLC hybrid.
EVENTUAL        read repair + hinted handoff + Merkle anti-entropy + gossip;
                 conflicts: LWW / siblings / CRDT; session guarantees for UX;
                 reconciliation jobs + lag metrics operationally.
```

## Top Interview Questions (Module 11)

1. mod-N vs ring, with numbers. 2. Virtual nodes' three benefits. 3. Bloom filter
in the LSM read path. 4. Sync two diverged 10 TB replicas cheaply. 5. Detect (not
just resolve) write conflicts. 6. Leader election + GC pause + fencing. 7. Why
Redlock is contested. 8. SWIM failure detection. 9. LWW under clock skew.
10. TrueTime/commit-wait. 11. Post-partition healing sequence in Dynamo-style
stores. 12. When to prefer partition ownership over any lock.

## Common Mistakes Recap

mod-N sharding • rings without virtual nodes • Bloom filters where false positives
aren't tolerable • trusting cross-machine timestamps • locks without TTL, owner
tokens, or fencing • treating Redlock as correctness-grade • election without
term checks downstream • forgetting reconciliation/lag metrics in eventually-
consistent designs.

## Mock Interview Exercise

*"Design the coordination layer for a distributed cron service: 10k scheduled jobs,
each must run exactly once per schedule across a 50-node worker fleet, workers
crash freely."* Expected: jobs partitioned across workers via consistent hashing
(vnodes) → each partition has a lease-based owner (etcd) with fencing tokens →
job-run records with unique `(job_id, scheduled_time)` constraint as the final
idempotency backstop (DB as the true arbiter) → gossip or etcd watch for membership
→ missed-run detection via a sweeper. Then defend "exactly once" honestly:
at-least-once triggering + idempotent execution.

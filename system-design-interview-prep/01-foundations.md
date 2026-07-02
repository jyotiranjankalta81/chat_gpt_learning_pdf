# Module 1 — Foundations

The vocabulary of every system design interview. You will use every concept in this
module in every design you ever draw. Interviewers rarely ask these as standalone
questions at senior level — instead they listen for whether you use them *correctly
and quantitatively* while designing.

---

## 1.1 Latency vs Throughput

### Why Interviewers Ask This

It is the fastest way to detect whether a candidate thinks quantitatively. Senior
candidates are expected to know that the two are different axes, that improving one
can hurt the other, and that tail latency — not average — is what pages you at 3am.

### Core Concept

- **Latency**: time for a single operation to complete (ms). What one user feels.
- **Throughput**: operations completed per unit time (QPS/RPS). What the fleet handles.

They are related through concurrency by **Little's Law**:

```
concurrency = throughput × latency
(L = λ × W)
```

A service doing 1,000 QPS at 200 ms average latency has ~200 requests in flight at
any moment. That single formula sizes your thread pools, connection pools, and
load balancer limits.

### Internal Working

Latency decomposes into a pipeline; know the rough magnitudes cold:

| Operation | Typical latency |
|---|---|
| L1 cache reference | ~1 ns |
| Main memory reference | ~100 ns |
| Read 1 MB sequentially from memory | ~10 µs |
| SSD random read | ~100 µs |
| Read 1 MB from SSD | ~1 ms |
| Round trip within same datacenter | ~0.5 ms |
| Read 1 MB over 1 Gbps network | ~10 ms |
| Disk seek (HDD) | ~10 ms |
| Round trip US East ↔ US West | ~60–70 ms |
| Round trip US ↔ Europe | ~80–100 ms |
| Round trip US ↔ Asia | ~150–250 ms |

Throughput is limited by the narrowest stage of the pipeline (the bottleneck). Adding
capacity anywhere else changes nothing.

Latency is reported as a distribution, never an average:

- **p50** (median): the typical experience
- **p95 / p99**: the tail — slow requests caused by GC pauses, cold caches, lock contention, retries
- **p99.9**: matters at scale — at 1B requests/day, p99.9 is still 1M slow requests/day

Tail latency compounds with **fan-out**: if one page requires 100 parallel backend
calls and each has p99 = 1s, then ~63% of pages hit at least one slow call
(1 − 0.99¹⁰⁰). This is why Google and Amazon obsess over tails ("The Tail at Scale",
Dean & Barroso).

### Visual Architecture

```
  Request latency budget (example: 200 ms page load SLO)

  Client ──► DNS ──► TLS ──► LB ──► App ──► Cache ──► DB
              5ms    30ms    1ms    40ms     1ms      20ms
                                     │
                                     ├──► Service B (parallel)  35ms
                                     └──► Service C (parallel)  60ms  ◄── critical path
  Total ≈ 5+30+1+40+60+... : the SLOWEST parallel branch defines latency
```

### Real Production Example

Amazon famously measured that every +100 ms of latency cost ~1% in sales. Google
found +500 ms in search page load dropped traffic ~20%. Netflix keeps its API
gateway p99 budget in tens of milliseconds and uses request hedging (send a backup
request if the first is slow) to clip the tail.

### Advantages / Trade-offs of Optimizing Each

- Optimizing **latency**: better UX, but often costs money (more caching, more replicas closer to users, hedged requests double load).
- Optimizing **throughput**: better cost efficiency via batching/queueing/pipelining — but batching *adds* latency (you wait to fill the batch). Kafka is the canonical example: huge throughput, deliberately relaxed per-message latency.

### Common Mistakes

- Quoting averages. "Average latency is 50 ms" hides a 2-second p99.
- Assuming more servers reduce latency. Horizontal scaling raises throughput; a single request is not faster.
- Ignoring queueing: as utilization → 100%, latency → ∞ (queueing theory hockey stick). Run hot at 70–80%, not 95%.
- Forgetting fan-out amplification of tail latency.

### Scaling Considerations

- Throughput scales horizontally (more machines) if the workload is partitionable.
- Latency scales geographically (CDN, edge, regional replicas) — you cannot beat the speed of light, so move data closer.
- Past ~80% utilization, every extra percent of load disproportionately inflates tail latency.

### Failure Scenarios

- **Retry storms**: a latency spike causes clients to retry, multiplying load, raising latency further — a metastable failure. Mitigate with exponential backoff + jitter and retry budgets.
- **Slow dependency, not down dependency**: a service that answers in 5s is far more dangerous than one that fails fast, because it holds threads/connections hostage. Timeouts are a latency tool.

### Monitoring & Debugging

- Dashboards: p50/p95/p99/p99.9 latency histograms per endpoint, QPS, utilization, queue depth.
- Debug a latency regression with distributed tracing: find which span grew. Correlate with deploys, GC logs, cache hit ratio drops, DB slow-query logs.

### Interview Questions

1. Your p50 is 20 ms but p99 is 2 s. What are the likely causes and how do you investigate?
2. How does Little's Law help you size a connection pool?
3. Your service must go from 1k QPS to 100k QPS — what changes? Must latency change?

### Follow-up Questions

- "Would you hedge requests? What does that do to backend load?" (roughly doubles tail-triggered load; cap hedges at ~5% of traffic)
- "Why does batching improve throughput but hurt latency?"

### Best Practices

- Define a per-endpoint latency budget and allocate it across dependencies.
- Alert on p99, capacity-plan on throughput, and keep utilization headroom (≈30%).
- Measure at the client or LB, not just inside the service (you'll miss queueing and network time otherwise).

### Hands-on Design Exercise

Your API must serve 50k QPS with p99 < 100 ms. Each request does one cache lookup
(1 ms, 95% hit) and, on miss, one DB query (20 ms). Estimate: (a) DB QPS, (b) in-flight
requests, (c) the app instance count if one instance handles 500 concurrent requests.
*(Answers: 2.5k DB QPS; ≈ 50,000 × ~0.002s ≈ 100–150 in flight overall depending on mix;
work through it — then double everything for headroom.)*

---

## 1.2 Horizontal vs Vertical Scaling

### Why Interviewers Ask This

Every design eventually gets the question "what happens at 10x load?" The interviewer
wants to see that you know scaling out is an *architectural property you must design
for* (statelessness, partitionability), not a knob you turn later.

### Core Concept

- **Vertical scaling (scale up)**: bigger machine — more CPU, RAM, faster disks.
- **Horizontal scaling (scale out)**: more machines behind a load balancer or partitioning scheme.

Vertical is simple but has a hard ceiling and a single point of failure. Horizontal is
theoretically unbounded but forces you to solve distribution problems: state,
coordination, partial failure.

### Internal Working

Horizontal scaling of **stateless** services is trivial: LB + N replicas + health
checks + autoscaling. Horizontal scaling of **stateful** systems (databases) is the
hard part and requires replication (copies for reads/HA) and sharding (partitioning
for writes/capacity) — Module 4.

**Amdahl's law** governs the ceiling: if fraction *s* of the work is serialized
(a lock, a single leader, a hot row), maximum speedup is 1/s no matter how many
machines you add.

### Visual Architecture

```
 Vertical:                     Horizontal:
 ┌──────────────┐                        ┌────────┐
 │  1 machine   │              client ──►│   LB   │
 │  128 cores   │                        └───┬────┘
 │  2 TB RAM    │                ┌───────┬───┴────┬───────┐
 │  $$$$$       │                ▼       ▼        ▼       ▼
 └──────────────┘             ┌────┐  ┌────┐   ┌────┐  ┌────┐
  ceiling + SPOF              │app1│  │app2│   │app3│  │app4│  ... appN
                              └────┘  └────┘   └────┘  └────┘
                              stateless replicas, autoscaled
```

### Real Production Example

Stack Overflow famously ran for years on a handful of very large SQL Server boxes
(vertical) — simplicity was a feature. Google, Meta, and Amazon scale horizontally on
commodity hardware because at their size no single machine is big enough and failure
is constant. Stripe scales its API tier horizontally but scales its primary databases
with a mix of vertical headroom plus sharding.

### Advantages

- **Vertical**: no code changes, no distributed-systems complexity, strong single-node consistency, great for relational databases early on.
- **Horizontal**: near-unlimited capacity, fault tolerance (N−1 survives), cost-efficient commodity hardware, enables rolling deploys.

### Trade-offs

- Vertical: exponential cost curve, downtime to resize, hard ceiling, SPOF.
- Horizontal: needs statelessness or partitioning, introduces network hops, partial failures, data consistency questions, operational complexity (orchestration, service discovery).

### Common Mistakes

- Jumping to "shard everything" for a system doing 200 QPS. Senior answer: one Postgres primary + replicas + cache covers a surprisingly large scale; shard when write volume or dataset size forces you.
- Claiming horizontal scaling is "infinite" while the design contains a single leader, a global lock, or one hot partition.
- Forgetting that scaling the app tier just moves the bottleneck to the database.

### Scaling Considerations

- Scale reads first (replicas, cache), then writes (sharding), because reads usually dominate and are easier.
- Autoscaling policies need warm-up time and should scale on leading indicators (CPU, queue depth, concurrency), with limits to prevent runaway cost.

### Failure Scenarios

- Vertical: hardware failure = full outage; resize = downtime window.
- Horizontal: cascading failure when one replica dies and its load overwhelms the rest (always provision N+1/N+2); thundering herd on cold start of many new instances (cold caches).

### Monitoring & Debugging

- Fleet-wide: instance count, per-instance CPU/memory, LB request distribution (detect skew), autoscaler activity.
- Debug skew: one hot instance usually means sticky sessions, a bad hash, or a hot key.

### Interview Questions

1. When would you choose vertical scaling despite the SPOF?
2. Your write-heavy DB is at capacity — walk through your scaling options in order.
3. What prevents a service from scaling horizontally?

### Follow-up Questions

- "You doubled instances but throughput didn't move. Why?" (bottleneck is downstream: DB, lock, external API)
- "How does Amdahl's law show up in real architectures?" (single leader, sequence generators, global rate limiter)

### Best Practices

- Design services stateless from day one; externalize state to Redis/DB.
- Scale up until it's expensive or risky, then scale out — in that order for databases.
- Always run N+2 for critical tiers across ≥3 availability zones.

### Hands-on Design Exercise

An image-resizing service is CPU-bound: 1 instance = 50 resizes/s. Traffic is 2,000
resizes/s peak, 200 off-peak. Design the fleet: instance count, autoscaling signal,
and what you'd do if a batch client suddenly submits 50,000 images. *(Expect: ~40+
headroom at peak, scale on queue depth not CPU alone, absorb the batch with a queue
rather than autoscaling to absurdity.)*

---

## 1.3 The Core "-ilities": Availability, Reliability, Scalability, Durability

### Why Interviewers Ask This

These words appear in the first five minutes of every interview ("what are your
non-functional requirements?"). Interviewers check that you attach *numbers* to them
and understand they conflict — you cannot maximize all four for free.

### Core Concept

| Property | Question it answers | Measured by |
|---|---|---|
| **Availability** | Can I reach the system right now? | uptime %, error rate |
| **Reliability** | Does it do the *correct* thing consistently? | MTBF, defect rate, correctness |
| **Scalability** | Does it keep working as load grows? | throughput vs resources curve |
| **Durability** | Once acknowledged, is my data safe forever? | probability of data loss |

Availability ≠ reliability: a service that is up but returns wrong data is available
and unreliable. Durability ≠ availability: S3 can be unreachable for an hour (availability
incident) without losing a single byte (durability intact).

### Internal Working

**Availability math** (know these cold):

| Nines | Downtime/year | Downtime/day |
|---|---|---|
| 99% | 3.65 days | 14.4 min |
| 99.9% | 8.77 hours | 1.44 min |
| 99.99% | 52.6 min | 8.6 s |
| 99.999% | 5.26 min | 0.86 s |

Composition rules:

```
Serial (A depends on B):   Availability = A × B
   two 99.9% services in series → 99.8%
Parallel (either works):   Availability = 1 − (1−A)(1−B)
   two 99% replicas in parallel → 99.99%
```

Serial chains destroy availability; redundancy multiplies it. That is the entire
mathematical justification for replication and for keeping dependency chains short.

**Durability** comes from replication (3 copies, ideally across AZs), write-ahead
logs with fsync, erasure coding (S3 style: 11 nines), backups, and — critically —
protection against *correlated* failures (same rack, same firmware bug, same
`rm -rf` script). Replication is not backup: replication faithfully copies your
accidental DELETE to every replica.

### Visual Architecture

```
 Availability through redundancy (3 AZs):

            ┌──────────── Region ────────────┐
            │   AZ-a        AZ-b       AZ-c  │
 client ──► │  ┌────┐     ┌────┐     ┌────┐  │
            │  │app │     │app │     │app │  │   any one AZ can die
            │  └─┬──┘     └─┬──┘     └─┬──┘  │
            │  ┌─▼──┐     ┌─▼──┐     ┌─▼──┐  │
            │  │ DB │◄───►│ DB │◄───►│ DB │  │   quorum replication
            │  │ ldr│     │flw │     │flw │  │   → durability + availability
            │  └────┘     └────┘     └────┘  │
            └────────────────────────────────┘
```

### Real Production Example

Amazon S3 advertises 99.999999999% (11 nines) durability via erasure coding across
devices and AZs, but "only" 99.99% availability — an honest admission that the two
are different engineering problems. Google Spanner offers 99.999% availability for
multi-region deployments by paying for synchronous cross-region replication.

### Advantages / Trade-offs

- Each extra nine of availability roughly **10x-es the cost and complexity**: more redundancy, multi-region, automated failover, and it constrains deploy velocity (less room for bad deploys — which cause most outages).
- Higher durability (synchronous replication, fsync per write) directly costs write latency.
- Know your real requirement: an internal analytics tool does not need 99.99%.

### Common Mistakes

- Promising "five nines" casually. 5 minutes of downtime *per year* means fully automated failover, multi-region, and near-zero-risk deploys. Most businesses need 99.9–99.99%.
- Ignoring dependency math: your service cannot be more available than the serial chain of its hard dependencies.
- Conflating replication with backup.
- Treating scalability as binary rather than "scales linearly up to X, then bottleneck Y".

### Scaling Considerations

At larger scale, failures stop being rare events and become a constant rate (with
100k disks, disks die *daily*). Architecture must treat failure as routine:
automated detection, automated replacement, graceful degradation.

### Failure Scenarios

- **Correlated failure** defeats redundancy: whole-AZ outage, shared config push, a bad deploy hitting all replicas simultaneously. Mitigate with AZ isolation, staged rollouts, cell-based architecture.
- **Gray failure**: node is "up" per health checks but slow/wrong — often worse than clean death.

### Monitoring & Debugging

- Availability: success rate SLI at the load balancer (user-facing), synthetic probes from outside your network.
- Durability: checksum scrubbing (S3 continuously verifies data integrity), backup restore drills — an untested backup is not a backup.

### Interview Questions

1. Your service depends on 5 services, each 99.9%. What's your ceiling? *(≈99.5%)*
2. How do you design for 99.99% when your cloud provider's single region offers 99.9%?
3. Difference between durability and availability for a storage system?

### Follow-up Questions

- "The business demands five nines. What do you push back with?" (cost, deploy freeze implications, whether the dependency chain even allows it)
- "How would you *verify* your durability claim?" (restore drills, scrubbing, chaos testing)

### Best Practices

- State explicit numeric targets in the first 5 minutes of any design.
- Minimize hard (serial) dependencies; convert them to soft dependencies with graceful degradation (serve stale cache if DB is down).
- Deploy gradually (canary → 1% → 10% → 100%) — deploys cause most incidents.

### Hands-on Design Exercise

You run a checkout service (must be 99.99%) that calls: payments provider (99.95%),
inventory service (99.9%), email service (99.5%). Rework the architecture so email
and inventory failures don't count against checkout availability. *(Expect: async
email via queue; inventory check with cached fallback or optimistic reserve +
reconcile.)*

---

## 1.4 Consistency (and the Consistency Spectrum)

### Why Interviewers Ask This

Consistency choices drive database selection, replication mode, and UX. Senior
candidates must place a use case on the consistency spectrum and justify it, not
just chant "eventual consistency" at every problem.

### Core Concept

Consistency = do all observers see the same data at the same time? It is a spectrum:

```
STRONG ◄──────────────────────────────────────────────► WEAK
Linearizable   Sequential   Causal   Read-your-writes   Eventual
(acts like     (global      (causes  (I see my own      (replicas converge
one copy)      order)       before   updates)            ...eventually)
                            effects)
```

- **Linearizable / strong**: every read sees the latest acknowledged write. Needed for: account balances, inventory decrement, unique username claims, lock services.
- **Causal**: if B was caused by A, everyone sees A before B (comment appears after the post it replies to).
- **Read-your-writes**: a user always sees their own updates (profile edits) — often implemented by pinning that user's reads to the leader or their own session replica.
- **Monotonic reads**: a user never sees data go *backwards* in time between requests.
- **Eventual**: replicas converge if writes stop. Fine for: like counts, follower counts, feeds, DNS.

### Internal Working

Strong consistency in a replicated system requires coordination on the write path:
either a single leader that serializes writes plus reads served by the leader (or
quorum reads), or a consensus protocol (Raft/Paxos) per write. Quorums: with N
replicas, write to W, read from R; if **R + W > N**, read and write sets overlap so
reads see the latest write (e.g., N=3, W=2, R=2). Eventual consistency drops the
coordination: accept writes anywhere/asynchronously, replicate in background,
resolve conflicts (last-writer-wins, vector clocks, CRDTs).

### Real Production Example

- Meta: your own profile edit is read-your-writes (session pinned to region of write via a "write-through" cookie); friend's like counts are eventual.
- Bank ledgers, Stripe payments: strongly consistent, serialized per account/idempotency key.
- Amazon DynamoDB: eventually consistent reads by default, strongly consistent reads on request at double the read cost — a literal price tag on consistency.

### Advantages / Trade-offs

- Strong: simple to reason about, no anomalies — but higher latency (coordination round trips), lower availability under partition, doesn't span regions cheaply.
- Eventual: fast, available, partition-tolerant — but the application must tolerate anomalies (stale reads, conflicting writes) and sometimes resolve conflicts.

### Common Mistakes

- Applying one consistency level to the whole system. Real systems mix levels per data type — say this explicitly in interviews.
- Believing eventual consistency means "wrong": it means *temporarily stale*, with convergence guarantees.
- Ignoring the user-facing anomaly: "user posts a comment, refreshes, comment disappears" = missing read-your-writes.

### Interview Questions

1. Which operations in an e-commerce site need strong consistency? *(inventory decrement at checkout, payment; not product views or reviews)*
2. How do you implement read-your-writes over async replicas?
3. Explain R+W>N quorum consistency.

### Best Practices

- Classify every entity in your design: strong / causal / eventual — and say why.
- Push strong consistency to the smallest possible scope (a single row, a single partition) so the rest of the system can be fast and available.

### Hands-on Design Exercise

For a Twitter-like app, assign a consistency level to: tweet publish, timeline read,
follower count, DM delivery, username registration. Justify each in one line.

---

## 1.5 CAP Theorem and PACELC

### Why Interviewers Ask This

It's the classic filter question — but at senior level the interviewer wants the
*correct, nuanced* version, and PACELC, because CAP alone is widely misquoted.

### Core Concept

**CAP**: when a network **P**artition happens, a distributed system must choose
between **C**onsistency (every read sees the latest write, or errors) and
**A**vailability (every request gets a non-error response, possibly stale). Partition
tolerance is not optional — networks *will* partition — so the real choice is only
what to do *during* a partition:

- **CP**: refuse/fail some requests to stay consistent (ZooKeeper, etcd, HBase, Spanner).
- **AP**: keep answering, possibly stale, reconcile later (Dynamo-style: Cassandra, Riak, DynamoDB defaults, DNS).

**PACELC** completes the picture: *if Partition, trade Availability vs Consistency;
Else (normal operation), trade Latency vs Consistency.*

```
              ┌── Partition? ──┐
             yes               no
              │                 │
        A  vs  C           L  vs  C
   (keep serving?     (fast async replication?
    or stay correct?)  or slow sync replication?)
```

- Cassandra: **PA/EL** — available under partition, low latency normally (async).
- Spanner, CockroachDB: **PC/EC** — consistent under partition, pays latency normally (sync/consensus).
- MongoDB (default): **PC/EC**-leaning (primary steps down during partition).
- DynamoDB: **PA/EL** default with per-read strong option.

### Internal Working

During a partition, a CP system with a leader on the minority side must stop
accepting writes (it can't reach quorum); the majority side elects a new leader and
continues — so "unavailability" is usually partial and lasts seconds. An AP system
lets both sides accept writes, creating divergent versions that must be merged
after healing (vector clocks, LWW timestamps, CRDTs, or application-level merge like
Amazon's shopping cart union).

### Real Production Example

Amazon's original Dynamo paper chose AP for the shopping cart: it is better to accept
an add-to-cart on a stale replica and merge carts later than to show an error at the
moment a customer wants to buy. Google Spanner chooses CP plus TrueTime to get
externally consistent transactions — and eats the write latency of cross-region
Paxos because ad billing data must be correct.

### Common Mistakes

- "Choose 2 of 3." Wrong — you can't choose CA in a distributed system; partitions happen. CAP only constrains behavior *during* partitions.
- Ignoring that CAP says nothing about latency in normal operation — that's why PACELC exists and why interviewers love hearing it unprompted.
- Treating a whole database as CP or AP when many (DynamoDB, Cassandra, Cosmos DB) are *tunable per request*.

### Interview Questions

1. Why can't you sacrifice partition tolerance?
2. Classify Cassandra, ZooKeeper, and Spanner under PACELC and justify.
3. Your two datacenters lose connectivity for 5 minutes. Walk through what your design does.

### Best Practices

- In interviews, phrase it as: "During partitions this component chooses X because
  business requirement Y; in normal operation I replicate asynchronously/synchronously
  because of the latency budget."

### Hands-on Design Exercise

Design the partition behavior for a ticket-booking system spanning 2 regions: what
happens to seat purchases in each region when the inter-region link dies?
*(Expect: partition seat inventory by region/event home region — CP within the owning
region, degrade the remote region to read-only or queued intents.)*

---

## 1.6 SLA, SLO, SLI

### Why Interviewers Ask This

They reveal operational maturity — whether you've actually run a service. Staff-level
answers connect these to error budgets and engineering decisions (deploy velocity vs
reliability).

### Core Concept

```
SLI  →  what you MEASURE      "successful requests / total requests"
SLO  →  what you TARGET       "99.9% success over rolling 30 days"
SLA  →  what you PROMISE      "99.5% or you get service credits" (contract, penalty)
```

SLA < SLO always: promise externally less than you target internally, so the buffer
absorbs bad months.

**Error budget** = 1 − SLO. At 99.9% monthly, you may "spend" 43.8 minutes of
unavailability. Budget healthy → ship fast, take risks. Budget exhausted → freeze
features, work on reliability. This converts reliability from a religious argument
into a resource-allocation decision — the core idea of Google SRE.

### Internal Working

Good SLIs are user-centric and measured as a ratio of good events / valid events at
the point closest to the user (load balancer, client-side):

- Availability SLI: non-5xx responses / total
- Latency SLI: requests faster than 300 ms / total (a threshold ratio — better than tracking "p99" directly as SLI because it composes over time windows)
- Freshness/durability SLIs for pipelines and storage

Windows: rolling 28–30 days is standard. Burn-rate alerts fire when the budget is
consumed too fast (e.g., 14.4× burn over 1 hour = page; 6× over 6 hours = page;
1× over 3 days = ticket).

### Real Production Example

Google SRE runs the error-budget policy: if a product team exhausts the budget,
launches halt until reliability work restores it. Stripe publishes API SLAs and is
known for 99.999%-level API uptime targets internally. AWS SLAs pay service credits
(e.g., EC2 region-level < 99.99% monthly → credits) — note the SLA is weaker than
what they actually deliver, by design.

### Common Mistakes

- Conflating the three terms (instant mid-level signal).
- 100% SLO targets — impossible and wasteful; every extra nine costs ~10x.
- Measuring SLIs inside the server (misses network/LB failures the user sees).
- Alerting on causes (CPU) instead of symptoms (SLO burn).

### Interview Questions

1. Define an SLI/SLO for a payment API and the alerting around it.
2. What is an error budget and how does it change team behavior?
3. Why should the SLA be weaker than the SLO?

### Best Practices

- 2–4 SLOs per service, user-journey oriented; review quarterly.
- Multi-window burn-rate alerting (fast burn pages, slow burn tickets).

### Hands-on Design Exercise

Write the SLIs, SLOs, and a burn-rate alert policy for a file-upload service (uploads
must complete, must be durable, and must be < 5 s for files < 10 MB).

---

## 1.7 Load Patterns & Read-heavy vs Write-heavy Systems

### Why Interviewers Ask This

The read/write ratio is the single most design-determining number in an interview.
Say it out loud in the first ten minutes and derive the architecture from it.

### Core Concept

**Load patterns:**

- **Diurnal**: daily peaks (social apps: evening peak 2–5× trough). Plan capacity for peak, autoscale the difference.
- **Spiky / event-driven**: flash sales, ticket drops, breaking news — 10–100× baseline in seconds. Autoscaling is too slow; you need queues, pre-provisioning, load shedding, waiting rooms.
- **Seasonal**: Black Friday, tax season.
- **Thundering herd**: synchronized clients (cron at :00, cache expiry, push notification sent to 10M users who all open the app). Add jitter everywhere.

**Read-heavy** (100:1 to 1000:1 — Twitter timelines, Netflix browse, Google search):
optimize with caching layers, read replicas, CDNs, denormalization, precomputation
(materialized views, fan-out-on-write feeds).

**Write-heavy** (metrics ingestion, IoT, logging, chat): optimize with partitioning/
sharding, LSM-tree storage engines (Cassandra, RocksDB) that turn random writes into
sequential I/O, batching, and buffering through Kafka; keep indexes minimal (every
index is write amplification).

### Visual Architecture

```
 READ-HEAVY                              WRITE-HEAVY
 client                                  clients (many)
   │                                        │
   ▼                                        ▼
  CDN ──hit──► done                      ┌───────┐   absorb burst,
   │miss                                 │ Kafka │   decouple producers
   ▼                                     └───┬───┘
 cache (Redis) ──hit──► done                 ▼
   │miss                                 consumers (batch writes)
   ▼                                         ▼
 read replicas ◄── async ── leader       sharded LSM store
 (scale reads)         (all writes)      (scale writes by partition)
```

### Real Production Example

Twitter: ~300k QPS timeline reads vs ~6k tweet writes → fan-out-on-write (precompute
home timelines into Redis at tweet time), with fan-out-on-read fallback for
celebrities. Conversely, Datadog/metrics pipelines are write-dominated: millions of
points/sec into Kafka, then into columnar/LSM stores, with reads being rare
aggregations.

### Common Mistakes

- Designing for average instead of peak (and for peak instead of *spike*).
- Adding read replicas to fix a write bottleneck (replicas replay every write too — they don't add write capacity).
- Caching a write-heavy dataset with low re-read rates (cache hit ratio will be terrible).

### Interview Questions

1. How does a 1000:1 read ratio change your database architecture?
2. Design intake for a ticket sale where 1M users click "buy" in the first minute for 50k seats.
3. Why are LSM trees favored for write-heavy workloads? *(sequential I/O, batched memtable flushes; cost: read amplification + compaction)*

### Best Practices

- State read:write ratio and peak:average ratio during capacity estimation, always.
- For spikes: queue + shed + waiting room; for diurnal: autoscale; for herds: jitter.

### Hands-on Design Exercise

You ingest 500k sensor readings/sec (write-heavy) but ops dashboards query only
per-minute aggregates (read-light). Sketch the pipeline and storage choice, and state
where you'd batch. *(Expect: Kafka → stream aggregator → columnar/TSDB; raw data to
object storage.)*

---

## 1.8 Stateless vs Stateful Services

### Why Interviewers Ask This

Statelessness is the property that makes horizontal scaling, autoscaling, rolling
deploys, and failover trivial. Interviewers check that you know *where you moved the
state to* — because the state never disappears, it just relocates.

### Core Concept

- **Stateless service**: any instance can serve any request; nothing request-relevant lives only in instance memory. State is externalized to databases, Redis, object storage, or carried in the request (JWT).
- **Stateful service**: correctness depends on local state — databases, WebSocket connection servers, game servers, stream processors with local RocksDB state (Kafka Streams/Flink).

### Internal Working

Making a service stateless in practice:

- Sessions → Redis or signed tokens (JWT) instead of in-memory session maps.
- File uploads → stream to S3, not local disk.
- In-memory caches are OK only as *disposable* performance layers.

When state is unavoidable, you manage it explicitly: **sticky routing** (consistent
hashing of user → connection server), **replication + failover** (databases),
**partitioned ownership** (each instance owns a shard of state, with rebalancing
protocols — this is how Kafka consumer groups and Flink operate).

### Visual Architecture

```
 Stateless tier (easy):                Stateful tier (managed carefully):

   LB ──► app1                           user123 ─┐
      ├─► app2   any instance,           user456 ─┼─► hash ring ─► ws-server-7
      └─► app3   kill/scale freely       user789 ─┘   (sticky: that server holds
             │                                         the open socket + presence)
             ▼                                        + session state also in Redis
       Redis / DB / S3                                  so another server can resume
       (the state lives HERE)                           on failure
```

### Real Production Example

Netflix's API/edge tiers are stateless and autoscale by thousands of instances
daily. WhatsApp's chat servers are stateful (millions of long-lived TCP connections
per box in its famous Erlang setup); a crashed chat server drops connections, clients
reconnect through the LB, and durable message state lives in the message store — the
connection state is sacrificial, the message state is not.

### Advantages / Trade-offs

- Stateless: trivial scaling/deploys/failover; but per-request latency to fetch state externally, and the external state store becomes the thing you must scale.
- Stateful: data locality (fast), enables long-lived connections and stream processing; but rebalancing, draining before deploys, and failover protocols are on you.

### Common Mistakes

- "Stateless" services with hidden state: local caches that matter for correctness, sticky sessions in the LB nobody remembers, cron state on one box.
- Forgetting that WebSockets make the connection tier inherently stateful — you need a routing layer (who holds user X's socket?) and a pub/sub backplane (Redis pub/sub, Kafka) to deliver messages across servers.
- Moving all state to Redis and then treating Redis as infinitely scalable/free.

### Interview Questions

1. How do you deploy a new version of a WebSocket server fleet without dropping a million connections uncleanly? *(connection draining, client reconnect with backoff+jitter, resume via session state in Redis)*
2. Where does session state go when you make the app tier stateless, and what's the trade-off of JWT vs server-side sessions? *(JWT: no lookup, but revocation is hard; Redis session: revocable, but adds a dependency)*
3. How do Kafka Streams / Flink handle stateful failover? *(changelog topics / checkpoints restore local state on another node)*

### Best Practices

- Default stateless; document and justify every piece of state that stays local.
- For stateful tiers: plan the rebalance story (consistent hashing), the drain story (deploys), and the recovery story (where is the source of truth?) before anything else.

### Hands-on Design Exercise

Design the connection tier for a chat app with 10M concurrent WebSocket users:
how many servers (assume 100k conns/server), how a message from user A reaches
user B on another server, and what happens when one server dies. *(Expect: ~100
servers + headroom, registry mapping user→server in Redis, pub/sub or direct
server-to-server routing, reconnect + resume from message store on failure.)*

---

## Module 1 Cheat Sheet

```
LATENCY vs THROUGHPUT   L = time per op (report p50/p95/p99); T = ops/sec
                        Little's Law: concurrency = T × L. Tail compounds w/ fan-out.
SCALING                 Up: simple, ceiling, SPOF. Out: needs stateless/partitionable.
                        Amdahl: serial fraction caps speedup. Scale reads → then writes.
AVAILABILITY            Serial: multiply (chain kills you). Parallel: 1−∏(1−a).
                        99.9%=8.8h/yr  99.99%=53min/yr  99.999%=5min/yr (each 9 ≈ 10x cost)
DURABILITY              Replication ≠ backup. WAL+fsync, 3x replicas, erasure coding, restore drills.
CONSISTENCY SPECTRUM    linearizable > sequential > causal > RYW > monotonic > eventual
                        Quorum: R+W>N ⇒ strong reads. Mix levels per entity.
CAP                     Partition ⇒ choose C (refuse) or A (serve stale). No "CA".
PACELC                  Else: Latency vs Consistency. Cassandra PA/EL; Spanner PC/EC.
SLI/SLO/SLA             measure / target / promise (SLA < SLO). Error budget = 1−SLO.
                        Burn-rate alerts on symptoms, measured at the edge.
LOAD PATTERNS           diurnal→autoscale; spike→queue+shed+prewarm; herd→jitter.
READ-HEAVY              cache, CDN, replicas, precompute (fan-out-on-write).
WRITE-HEAVY             partition, LSM engines, batch, buffer via Kafka, few indexes.
STATELESS               externalize state (Redis/DB/S3); enables scale & deploys.
STATEFUL                sticky routing, ownership+rebalance, drain, changelog recovery.
```

## Top Interview Questions (Module 1)

1. p50 20 ms / p99 2 s — diagnose. 2. Size a connection pool with Little's Law.
3. Five 99.9% serial dependencies — availability ceiling? 4. CP vs AP for a booking
system, per component. 5. PACELC classification of Cassandra vs Spanner. 6. Define
SLO + error budget policy for a payments API. 7. Architecture for 1000:1 read ratio.
8. Flash-sale intake design. 9. Deploying stateful WebSocket fleets. 10. Why
replication is not backup.

## Common Mistakes Recap

Averages instead of percentiles • "infinite" horizontal scaling with a hidden serial
bottleneck • five-nines promises without costing them • one consistency level for the
whole system • "CA systems" • SLI measured inside the server • designing for average
load • hidden state in "stateless" services.

## Mock Interview Exercise

*"Design a global product-catalog read API: 200k QPS reads, 50 writes/sec, p99
< 80 ms worldwide, catalog must never lose updates."* Spend 20 minutes. You should
produce: read:write ratio observation → CDN + regional Redis + read replicas;
async cross-region replication (PA/EL, eventual reads are fine for catalog);
strong consistency only on the write path to the leader; SLOs + burn alerts; and
the failure story for a region loss. Grade yourself against the rubric in the
introduction.

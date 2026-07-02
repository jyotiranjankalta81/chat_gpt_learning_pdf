# Module 7 — Microservices & Resilience Patterns

This module is where staff-level interviews live: distributed transactions,
idempotency, and the resilience patterns (circuit breaker, bulkhead, timeout
budgets) that decide whether one slow dependency takes down your whole product.

---

## 7.1 Monolith vs Microservices

### Why Interviewers Ask This

It's an architecture-judgment question. The wrong answer is dogma in either
direction; the senior answer is that microservices are an *organizational* scaling
tool that trades local complexity for distributed complexity.

### Core Concept

- **Monolith**: one deployable, one process, in-process calls, one database, one transaction boundary. A *modular* monolith (enforced internal boundaries) is the modern respectable default.
- **Microservices**: independently deployable services, each owning its **own data** (no shared database — the defining rule), communicating over the network (gRPC/REST/events).

What microservices actually buy: independent deploys (team velocity at 50+
engineers — Conway's law is the real driver), independent scaling (resize only the
hot service), fault isolation (if designed for it), tech heterogeneity. What they
cost: every in-process call becomes a network call (latency, partial failure,
retries), every transaction becomes a saga, every debug session becomes distributed
tracing, and you now run a platform (discovery, mesh, CI/CD, observability).

```
 Monolith:  [ UI | orders | payments | inventory ]──[ one DB ]  1 deploy, ACID
 Micro:     [orders svc]──DB₁   [payments svc]──DB₂   [inventory svc]──DB₃
                └── network calls + events; consistency = YOUR problem now
```

### Real Production Example

Amazon and Netflix decomposed monoliths when team count, deploy contention, and
scaling asymmetry forced it. Counter-examples interviewers respect: Shopify runs a
famously successful *modular monolith* at enormous scale; Amazon Prime Video
published a 2023 case where merging microservices back into a monolith cut costs
~90% for that workload. Segment's "goodbye microservices" post is another classic.
Moral: decomposition is contextual, not virtuous.

### Common Mistakes

- Distributed monolith: services that must deploy together and share a database — all of the costs, none of the benefits. The shared-DB smell is the #1 thing to call out.
- Microservices at a 6-person startup ("you must be this tall": platform maturity, observability, on-call capacity).
- Nano-services: a service per entity; boundaries should follow *business domains* (DDD bounded contexts) sized so one team owns each.

### Interview Questions

1. What forces would make you split a monolith, and what must be true first?
2. What defines a good service boundary? (domain-driven, own data, low chattiness across the boundary, one team)
3. What is a distributed monolith and how do you detect one? (lockstep deploys, shared DB, chatty synchronous chains)

---

## 7.2 Service Discovery

### Core Concept & Internal Working

In a dynamic fleet (autoscaling, deploys, failures), "where is service B right now"
needs an answer that updates in seconds.

- **Registry-based**: instances register (and heartbeat) with a registry — Consul, Eureka, etcd/ZooKeeper, or the Kubernetes API. **Client-side discovery**: clients fetch the instance list and load-balance themselves (fewer hops, smarter LB — Netflix Eureka+Ribbon lineage). **Server-side**: clients hit a stable VIP/LB that resolves instances (simpler clients — Kubernetes Services, cloud LBs).
- **DNS-based**: SRV/headless-service records — simple, but caching makes it sluggish.
- **Service mesh** (Istio/Linkerd, Envoy sidecars): discovery + LB + mTLS + retries + telemetry pushed into a sidecar proxy via a control plane (xDS) — the app just calls `localhost`; the mesh does the rest.
- Health-integration is the point: discovery must *stop* routing to bad instances (heartbeats, readiness probes, outlier ejection). Registry availability matters: Eureka chose AP (serve stale instance lists during partitions — stale routing beats no routing); ZooKeeper-based systems chose CP.

```
 pod starts ─register/heartbeat─► registry (Consul/K8s API)
 client ─"who is payments?"────► registry ─► [10.0.3.7, 10.0.9.2, ...]
 client ── picks instance (P2C) ──► payments pod   (or Envoy sidecar does all this)
```

### Interview Questions

1. Client-side vs server-side discovery trade-offs?
2. Why did Eureka choose availability over consistency for the registry?
3. What does a service mesh move out of application code, and what does the sidecar cost? (per-hop latency ~ms, fleet resource overhead, control-plane blast radius)

---

## 7.3 API Gateway in a Microservice Architecture

(Networking view in Module 2.5; here, the architecture role.)

- One front door: routing to services, authn/z (validate JWT once, pass claims), rate limiting/quotas, canary/traffic splitting, protocol translation (REST outside, gRPC inside), response aggregation.
- **BFF pattern** (Backend-for-Frontend): a gateway variant per client type (mobile/web) that shapes and aggregates APIs per experience — avoids one generic gateway becoming everyone's compromise; this is how Netflix's edge evolved.
- Anti-pattern to name: business logic creeping into the gateway → a shared bottleneck owned by no product team ("the ESB reborn"). Keep it to cross-cutting concerns; keep it horizontally scaled and stateless.

### Interview Questions

1. Gateway vs service mesh — which handles what? (gateway = north-south/edge; mesh = east-west/inter-service)
2. When do BFFs beat one gateway?

---

## 7.4 Resilience: Timeout, Retry, Circuit Breaker, Bulkhead

### Why Interviewers Ask This

This quartet is *the* "senior engineer who has been paged" question set. The
scenario is always: one dependency degrades — does your system degrade
proportionally, or collapse entirely?

### Core Concept & Internal Working

**Timeouts** — every network call has one, sized from the dependency's p99 (~p99 ×
1.5, not a folklore 30 s). No timeout = threads/connections accumulate behind a slow
dependency until exhaustion (the actual kill mechanism in most cascades). **Deadline
propagation**: the edge sets a total budget (e.g., 800 ms); each hop passes the
remaining budget down (gRPC does this natively) so nobody works on a request the
user already abandoned.

**Retries** — handle *transient* failures. Rules: only idempotent operations (or
with idempotency keys), exponential backoff **+ jitter**, small caps (2–3), and a
**retry budget** (e.g., retries ≤ 10% of requests) so retries can't multiply load
during an incident. The amplification trap: 3 layers each retrying 3× = up to 27×
traffic onto the struggling dependency — retry at *one* layer (usually the caller
closest to the failure), not every layer.

**Circuit breaker** — stop calling a dependency that's failing; fail fast and give
it room to recover.

```
        CLOSED ──failure rate > 50% over window──► OPEN
          ▲                                          │ (all calls fail fast /
          │ successes                                │  serve fallback)
          └────── HALF-OPEN ◄── cooldown (e.g. 30s)──┘
                  (let N probes through; success → CLOSED, failure → OPEN)
```

Fail-fast matters twice: your latency stays flat (no waiting on a corpse), and the
dependency isn't hammered while it recovers. Every breaker needs a **fallback**:
cached/stale data, default value, degraded feature, or an honest error. Modern
placement: in the mesh/sidecar (Envoy outlier detection) or libraries (Resilience4j;
Hystrix is the ancestor).

**Bulkhead** — partition resources so one failing dependency can't consume
everything: separate connection pools / thread pools / semaphores *per dependency*
(payment pool ≠ recommendation pool), per-tenant quotas, even per-workload
deployments (batch vs interactive). Named after ship compartments: one flooded
compartment shouldn't sink the ship. The cascade it prevents: recommendations
slows → all 200 worker threads end up parked waiting on it → checkout (which never
needed recommendations) has no threads left → total outage from a cosmetic feature.

### Real Production Example

Netflix built and open-sourced Hystrix after exactly these cascades; their standard
story: recommendations down → serve popular titles (fallback), checkout unaffected
(bulkhead). AWS SDKs ship retry budgets + adaptive retry. Google SRE codified
deadline propagation and "retry amplification" postmortems.

### Common Mistakes

- Retrying non-idempotent calls (double charge), retrying on every layer, no jitter (synchronized retry waves), timeout longer than the caller's own deadline.
- Circuit breaker without fallback (= faster errors, same outage UX).
- One global thread/connection pool for all dependencies.

### Interview Questions

1. Payment provider p99 went from 200 ms → 20 s. Walk through what happens with and without each pattern.
2. How do you size timeouts and where do deadlines come from?
3. Explain retry amplification and how budgets bound it.

---

## 7.5 Idempotency

### Why Interviewers Ask This

Retries + at-least-once delivery are everywhere (7.4, Module 5), so duplicate
requests are a *certainty*. Idempotency is what makes them safe; payments
interviews hinge on it.

### Core Concept & Internal Working

An operation is idempotent if executing it N times has the same effect as once.
GET/PUT/DELETE are naturally idempotent; "create order", "charge card",
"increment balance" are not — you make them idempotent with **idempotency keys**:

```
POST /charges  Idempotency-Key: 7f3e-...-a12b   (client-generated UUID per logical op)

server, atomically (single DB transaction):
  INSERT INTO idempotency_keys(key, status='in_progress') ON CONFLICT →
     • conflict + completed  → return the STORED response (no re-execution)
     • conflict + in_progress→ 409/retry-later (a concurrent duplicate is running)
  ... execute business logic, write business rows ...
  UPDATE idempotency_keys SET status='completed', response=...   -- same txn/commit
```

Design points interviewers probe:

- The key must cover the *logical operation* (client retries reuse it; a genuinely new attempt gets a new key) — key scoping is a client-contract question.
- Dedup record and business effect must commit **atomically** (same DB transaction, or a unique constraint on the business row itself, e.g., `UNIQUE(order_id)` on payments). A Redis-based "seen set" checked before a separate DB write has a crash window that breaks the guarantee.
- Store the original *response* so retries return identical results.
- Keys expire (Stripe: 24 h) — bounded storage, and clients shouldn't retry across days.
- Alternative formulations: natural idempotency by design (`SET status='paid'`; insert-only ledgers keyed by event ID; state machines where transitions are idempotent), and **fencing/versioning** (optimistic concurrency: `UPDATE ... WHERE version=7`) for stale-duplicate protection.

### Real Production Example

Stripe's `Idempotency-Key` header is the industry-reference design (they return the
stored response byte-for-byte). Every serious payment, ordering, and provisioning
API does the equivalent internally.

### Interview Questions

1. Client timeout on POST /orders → user clicks again. Walk both requests through your idempotent design.
2. Why is check-then-act in Redis + DB insufficient?
3. Make "transfer $100 A→B" idempotent. (transfer row keyed by transfer_id, ledger entries derived from it, unique constraints enforce once)

---

## 7.6 Distributed Transactions: 2PC vs Saga

### Why Interviewers Ask This

Once each service owns its DB, "order + payment + inventory must all succeed" has no
ACID answer. This is the definitive staff-level microservices question.

### Core Concept & Internal Working

**Two-Phase Commit (2PC)**: coordinator asks all participants to *prepare* (lock +
promise), then *commit*. Gives atomicity, but: **blocking** (participants hold locks
while waiting; a crashed coordinator leaves everyone stuck "in doubt"), coordinator
SPOF, latency of 2 round trips × slowest participant, and poor availability
(any participant down = no transaction). Used inside databases and some brokers
(XA, Kafka's internal transactions), avoided *between* microservices.

**Saga**: break the transaction into a sequence of *local* transactions, each with a
**compensating action** to semantically undo it if a later step fails.

```
 Order saga:  create order → reserve inventory → charge payment → confirm
 failure at charge:                ▲                   ✗
   compensate ◄── release inventory ◄── cancel order   (run compensations in reverse)
```

- **Orchestrated saga**: a coordinator (state machine — Temporal, AWS Step Functions, or a saga table + worker) explicitly commands each step and each compensation. Visible, debuggable, testable; the orchestrator must itself be durable (its state in a DB / workflow engine).
- **Choreographed saga**: each service reacts to the previous event (OrderCreated → InventoryReserved → PaymentCharged...). No central coordinator, but the workflow is invisible and cyclic-dependency-prone; fine for 2–3 steps, painful beyond.
- Sagas are **not ACID**: no isolation — intermediate states are visible (order exists while payment pending) → model them explicitly as statuses ("PENDING_PAYMENT") and design the UX for them; compensations can fail (retry + DLQ + human escalation queue); every step and compensation must be **idempotent** (messages redeliver).
- Some things can't be compensated (sent email, fired missile) — order steps so the hardest-to-undo runs **last** ("pivot" step), or use reservations (auth-then-capture in payments is exactly this: authorization is reversible, capture is the pivot).

### Real Production Example

Uber trip lifecycle and Airbnb reservations run saga-style flows (Airbnb built and
open-sourced ideas around this; Uber built Cadence → Temporal precisely to make
orchestration durable). Payment auth/capture is the everyday saga everyone has used.

### Common Mistakes

- Proposing 2PC across microservices without naming blocking/availability costs.
- Sagas without idempotent + retryable compensations, or without visible intermediate states.
- Forgetting the pivot-step ordering trick.

### Interview Questions

1. Book flight + hotel + charge card atomically — design it and enumerate every failure point.
2. Why is 2PC "blocking" and what does that mean operationally?
3. Orchestration vs choreography for a 7-step fulfillment flow?

---

## 7.7 Outbox Pattern (and the Dual-Write Problem)

### Why Interviewers Ask This

Every event-driven design contains the sentence "the service writes the DB *and*
publishes an event". Interviewers pounce: those are two systems — one can fail. The
outbox is the canonical fix and a reliable senior discriminator.

### Core Concept & Internal Working

**Dual-write bug**: `commit to DB; publish to Kafka` — crash between them ⇒ state
changed but no event (downstream never learns), or reversed order ⇒ event for a
rolled-back change. There is no distributed transaction across DB + broker (worth
having).

**Outbox**: write the event *into the same database transaction* as the state
change, then a separate mechanism ships it to the broker.

```
 BEGIN;
   UPDATE orders SET status='PLACED' WHERE id=42;
   INSERT INTO outbox(id, aggregate, type, payload) VALUES (uuid,'order-42','OrderPlaced',{...});
 COMMIT;                     -- atomic: both or neither
        │
        ├── relay option A: poller — SELECT unpublished → publish → mark published
        └── relay option B: CDC — Debezium tails the WAL/binlog → Kafka (no polling,
                            lower latency, no extra write load)
 Delivery is AT-LEAST-ONCE (relay can crash post-publish pre-mark) ⇒ consumers
 must be idempotent (7.5). Ordering: publish per-aggregate in commit order, key
 by aggregate ID. Prune published rows.
```

The inverse sibling: **listen-to-yourself / CDC-first** (write only the event, derive
state from it) and the transactional-log-tailing family. For inbound messages,
the **inbox pattern** mirrors it (store message ID + effects atomically —
i.e., 7.5's idempotency table).

### Real Production Example

Debezium's outbox router is the de facto standard implementation; documented in
production at scores of companies (e.g., banking and e-commerce engineering blogs).
Any "DB + Kafka + no lost events" claim in your interview design should say
"outbox via CDC" to be credible.

### Interview Questions

1. Why not just publish to Kafka inside the request handler after commit? (crash window; also before commit is worse — event for nothing)
2. Poller vs CDC relay trade-offs? (latency, DB load, ops complexity, ordering control)
3. What delivery guarantee does the outbox give and what must consumers do? (at-least-once; idempotency)

---

## Module 7 Cheat Sheet

```
MONO vs MICRO   Microservices = org-scaling tool; costs: network, sagas, tracing,
                platform. Own-your-data rule; distributed monolith = worst of both.
                Modular monolith is a respectable default (Shopify).
DISCOVERY       registry+heartbeats (Consul/K8s) client-side vs server-side; mesh
                sidecars (Envoy/xDS) add LB+mTLS+retries+telemetry. Registry is AP
                by design (stale beats none).
GATEWAY         edge concerns only (auth, rate limit, routing, BFF aggregation);
                north-south; mesh = east-west. No business logic.
TIMEOUT         every call; ≈p99×1.5; propagate DEADLINES down the chain.
RETRY           idempotent-only, backoff+JITTER, cap 2–3, retry BUDGET, one layer
                only (amplification: 3×3×3=27×).
CIRCUIT BREAKER closed→open (fail fast + FALLBACK)→half-open probes→closed.
BULKHEAD        pools/quotas per dependency & tenant; cosmetic feature must not
                starve checkout.
IDEMPOTENCY     client key per logical op; dedup record + effect in SAME txn;
                store response; unique constraints; version/fencing for stale dupes.
2PC             atomic but blocking, coordinator SPOF, in-doubt locks — not between
                microservices.
SAGA            local txns + compensations; orchestrated (durable coordinator,
                visible) vs choreographed (≤3 steps); no isolation → explicit
                PENDING states; pivot (hardest-to-undo) last; all steps idempotent.
OUTBOX          event INSERT in same txn as state change; relay via poller or CDC
                (Debezium); at-least-once ⇒ idempotent consumers; fixes dual-write.
```

## Top Interview Questions (Module 7)

1. Split this monolith: boundaries, order, prerequisites. 2. One dependency at 20 s
p99 — full resilience walkthrough. 3. Retry amplification math. 4. Stripe-style
idempotency implementation detail. 5. Flight+hotel+payment saga with failure at
each step. 6. Why 2PC is avoided between services. 7. Dual-write bug + outbox/CDC.
8. Mesh vs gateway responsibilities. 9. Choreography vs orchestration at 7 steps.
10. Design "exactly-once-looking" order placement over at-least-once infrastructure.

## Common Mistakes Recap

Shared database between services • retry-everywhere without budgets/jitter •
timeouts unset or unpropagated • breaker without fallback • one pool for all
dependencies • idempotency check outside the transaction • sagas without
compensations/idempotency/visible states • dual writes • business logic in the
gateway • microservices without platform maturity.

## Mock Interview Exercise

*"Design checkout for a marketplace: order service, inventory service, payment
service (external PSP), notification service. Requirements: no double charges, no
overselling, PSP p99 sometimes spikes to 10 s, notifications may lag."* Expected:
orchestrated saga (reserve inventory → auth payment → confirm → capture) with
compensations (release, void); idempotency keys end-to-end (client → order →
PSP); outbox+CDC for events; PSP wrapped in timeout (deadline-derived) + breaker +
fallback (queue order in PENDING_PAYMENT, async complete); bulkheaded PSP pool;
notification as lagging consumer group; enumerate the crash points and show each is
safe.

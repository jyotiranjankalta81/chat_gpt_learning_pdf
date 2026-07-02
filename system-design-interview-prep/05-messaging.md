# Module 5 — Messaging & Event-Driven Architecture

Queues and logs are how large systems decouple, absorb bursts, and survive partial
failure. Interviewers probe three things relentlessly: delivery semantics, ordering,
and what happens when consumers fall behind or poison messages arrive.

---

## 5.1 Core Model: Queues, Topics, Producers, Consumers, Consumer Groups

### Why Interviewers Ask This

Vocabulary precision here determines whether the rest of your messaging discussion
makes sense. "Queue vs topic" and "how do consumer groups scale" are standard warm-ups.

### Core Concept

- **Producer**: writes messages. **Consumer**: reads and processes them.
- **Queue (point-to-point)**: each message is processed by exactly ONE consumer among competing workers. Work distribution. (SQS, RabbitMQ queue.)
- **Topic (publish-subscribe)**: each message is delivered to ALL subscriber groups. Event broadcast. (Kafka topic, SNS, RabbitMQ fanout exchange.)
- **Consumer group**: a set of consumer instances sharing one logical subscription; the broker partitions work among them. Each *group* gets every message once; *within* a group, each message goes to one member. Kafka: partitions are assigned to group members (max parallelism = partition count). This is how the same event stream feeds the search indexer group AND the analytics group AND the notification group independently.

```
                         topic "order-events" (3 partitions)
 producers ──► P0 ▓▓▓▓▓▓   P1 ▓▓▓▓▓   P2 ▓▓▓▓▓▓
                     │            │          │
   group "search-indexer": c1←P0  c2←P1,P2      (each partition → one member)
   group "analytics":      c1←P0,P1,P2          (independent offsets, own pace)
   group "notifications":  c1←P0  c2←P1  c3←P2
```

Why queues at all (the interview answer): **decoupling** (producer doesn't know or
wait for consumers), **burst absorption** (queue soaks the flash sale; consumers
drain at their sustainable rate), **failure isolation** (email service down ≠ order
placement down), **fan-out of one fact to many systems**, and **retryability**
(redelivery instead of lost work).

### Common Mistakes

- Using a queue where a synchronous call is required (the user needs the answer *now* — payment authorization is sync; the receipt email is async).
- Expecting more parallelism than partitions (Kafka: 3 partitions = max 3 active consumers in a group).

---

## 5.2 Kafka (Deep Dive)

### Why Interviewers Ask This

Kafka is the backbone of event-driven architecture at nearly every large company;
"how does Kafka work" and "why Kafka over a queue" are direct senior questions.

### Core Concept

Kafka is not a queue — it is a **distributed, partitioned, replicated append-only
log**. Messages are appended to partitions and *retained* (time/size based, or
forever with compaction), and consumers track their own position (**offset**).
Consumption doesn't delete data, so many groups read the same stream at their own
pace, and you can **replay** history — the property that makes CDC pipelines, read
model rebuilds, and reprocessing possible.

### Internal Working

- **Topic → partitions**; each partition is an ordered log on disk. Ordering is guaranteed **within a partition only**. Producer chooses partition by key hash (`key=user_id` ⇒ all events of a user are ordered).
- **Replication**: each partition has a leader + followers (replication factor 3 typical). Producers/consumers talk to the leader. **ISR** (in-sync replicas): followers caught up. `acks=all` + `min.insync.replicas=2` ⇒ a write is ACKed only when a quorum has it — no loss on single-broker failure. `acks=1` ⇒ faster, loss window on leader crash.
- **Why it's fast**: sequential disk I/O (append-only), OS page cache, zero-copy sendfile, producer batching + compression, consumers pull in batches. Millions of msgs/sec per modest cluster.
- **Consumer groups & rebalancing**: group coordinator assigns partitions; member death triggers rebalance (brief pause — cooperative rebalancing reduces it). Offsets committed to an internal topic; commit *after* processing = at-least-once (duplicates possible on crash); commit *before* = at-most-once (loss possible).
- **Exactly-once (EOS)**: idempotent producer (sequence numbers dedupe broker-side retries) + transactions (atomic write to multiple partitions + offset commit) ⇒ exactly-once *within Kafka-to-Kafka pipelines* (Kafka Streams). The moment a side effect leaves Kafka (call an API, write a DB), you're back to at-least-once + idempotency (see 5.5).
- **Log compaction**: retain the latest value per key — a changelog that doubles as a table (CDC, state restore).
- KRaft (built-in Raft) replaced ZooKeeper for metadata/controller consensus.

```
 topic "payments", partition 1 (leader on broker B, replicas A,C):
 offset: 0    1    2    3    4    5    6  ──► append only
        [m0] [m1] [m2] [m3] [m4] [m5] [m6]
                        ▲              ▲
              group X committed=3   group Y committed=6
              (replayable: reset offset to 0 anytime within retention)
```

### Real Production Example

LinkedIn built Kafka (now trillions of messages/day) to unify activity data and
feed every downstream system from one log. Uber: trip events through Kafka to
pricing, fraud, analytics, driver matching. Netflix: all telemetry and CDC flows.
Stripe: event backbone with strict idempotent consumers for money movement.

### Advantages / Trade-offs

- Wins: throughput, durability, replay, fan-out to unlimited groups, ordering per key, stream processing ecosystem (Kafka Streams, Flink, Connect/Debezium).
- Costs: operational weight (self-managed), no per-message routing/priority/delay semantics (that's RabbitMQ territory), consumer-side complexity (rebalances, offset management), partition count = a semi-rigid scaling decision (repartitioning breaks key ordering during the transition).

### Common Mistakes

- Claiming global ordering across a topic (per-partition only).
- Choosing a low-cardinality partition key (all events on 2 of 50 partitions) or keying by something hot (one celebrity ⇒ one hot partition).
- "Kafka guarantees exactly-once" without the Kafka-boundary caveat.
- Unbounded consumer lag ignored until retention deletes unread data (data loss by neglect).

### Monitoring / Failure

- The metric: **consumer lag** (messages behind) per group/partition — alert on growth rate, not absolute value. Also: ISR shrinks, under-replicated partitions, rebalance frequency, produce/fetch latency.
- Failures: broker loss (leader election from ISR — clean if `acks=all`), rebalance storms from flapping consumers (tune session timeouts; static membership), poison messages stalling a partition (see DLQ 5.6).

### Interview Questions

1. How does Kafka achieve both durability and throughput? (sequential log + replication + batching)
2. You need per-user ordering and 100k msg/s — design topic/partitions/keys.
3. What exactly does `acks=all, min.insync.replicas=2` buy you, and what does it cost?
4. Consumer lag is growing — enumerate causes and fixes. (slow processing → scale consumers up to partition count / optimize handler / batch; hot partition → rekey; rebalance churn)

---

## 5.3 RabbitMQ, ActiveMQ, Amazon SQS (and choosing among them)

### Why Interviewers Ask This

"Kafka vs RabbitMQ vs SQS" is a canonical trade-off question; the senior answer maps
message *semantics needed* to broker *model*.

### Core Concept & Internal Working

**RabbitMQ** — a smart **broker-centric** message router (AMQP). Producers publish
to **exchanges**; exchanges route to queues via **bindings**: direct (exact routing
key), topic (wildcard patterns `order.*.eu`), fanout (broadcast), headers.
Per-message ACK/NACK with redelivery, per-queue TTL, **priority queues**, **delayed
delivery**, per-consumer prefetch (backpressure), dead-letter exchanges built in.
Messages are *deleted on ACK* — it's a post office, not a log. Quorum queues (Raft)
for replicated durability. Great at: task/job distribution, complex routing, RPC
patterns, per-message control. Ceiling: throughput well below Kafka; no replay.

**ActiveMQ (/Artemis)** — the JMS-standard broker of the Java enterprise world;
feature-similar to RabbitMQ (queues, topics, selectors, XA transactions). In
interviews: mention it as the legacy/JMS-compat choice; Artemis is the modern core.

**Amazon SQS** — fully managed queue-as-a-service. **Standard**: near-unlimited
throughput, at-least-once, best-effort ordering (duplicates and reordering happen —
by contract). **FIFO**: ordered + exactly-once-ish dedup within a 5-min window,
throughput limited per message group. Mechanics: poll → message becomes *invisible*
(visibility timeout) → consumer processes → deletes it; timeout expiry without
delete = automatic redelivery (crash-safe by design). `ReceiveCount` + redrive
policy → DLQ built in. Long polling to cut empty receives. Pairs with **SNS**
(pub/sub fan-out: SNS topic → many SQS queues) and Lambda.

```
 Decision sketch:
 need replay / event log / many independent readers / streams  → KAFKA
 need routing / priorities / delays / per-job semantics        → RABBITMQ
 on AWS, want zero ops, simple work queue                      → SQS (+SNS fanout)
 JMS/legacy Java estate                                        → ActiveMQ Artemis
```

### Real Production Example

Shopify and many fintechs: Kafka for events + RabbitMQ/SQS for job queues —
*both*, because they solve different problems. Reddit historically ran RabbitMQ for
async jobs. Amazon internally: SQS everywhere for decoupling (it predates Kafka).

### Common Mistakes

- Treating the three as interchangeable "queues" — replay and fan-out (Kafka) vs routing and job semantics (Rabbit) vs zero-ops (SQS) are different products.
- Ignoring SQS standard's duplicates/reordering contract, then debugging "impossible" double-sends.
- Setting SQS visibility timeout shorter than processing time (guaranteed duplicate processing).

### Interview Questions

1. Order events must feed search, analytics, and email — which broker(s) and why?
2. SQS standard vs FIFO: what do you give up for ordering?
3. Explain the visibility-timeout mechanism and its failure semantics.

---

## 5.4 Ordering

### Why Interviewers Ask This

Ordering bugs cause real money loss ("shipped" processed before "paid"). They want
to hear: global ordering doesn't scale — scope ordering to a key.

### Core Concept & Internal Working

- **Global ordering** requires a single serialization point (1 partition / FIFO with one group) — throughput ceiling. Almost never actually required.
- **Per-key ordering** is what businesses need: all events *for one order / one user / one account* in order. Kafka: partition by key. SQS FIFO: `MessageGroupId`. Kinesis: partition key.
- What breaks ordering even with keyed partitions: producer **retries** without idempotence (msg2 succeeds, msg1's retry lands after — fix: `enable.idempotence=true`, `max.in.flight≤5` with idempotence, or =1), **repartitioning** (key→partition mapping changes), consumer-side **parallel processing** of one partition's batch (process per-key serially), and DLQ/retry paths (a retried message leaves its slot — see 5.6).
- If out-of-order is unavoidable, make consumers order-tolerant: **version numbers / sequence checks** on the entity (ignore stale updates), or buffer-and-reorder windows (stream processing watermark techniques).

### Interview Questions

1. Payment events for the same order must be ordered; you need 50k msg/s across all orders. Design it. (key by order_id; scale via partitions — per-key serial, global parallel)
2. Producer retry reorders messages — why, and which settings fix it?
3. A consumer sees `order_shipped` before `order_paid`. List every place that could have reordered them.

---

## 5.5 Delivery Semantics: At-Most-Once, At-Least-Once, Exactly-Once

### Why Interviewers Ask This

This is the single most-tested messaging concept, because it decides whether you
double-charge customers. The expected senior take: *exactly-once delivery is
impossible over a network; exactly-once processing = at-least-once + idempotency.*

### Core Concept & Internal Working

The problem: producer sends, network drops the ACK. Did the broker get it? You must
choose: don't retry (**at-most-once** — possible loss) or retry (**at-least-once**
— possible duplicate). Same dilemma consumer-side: ACK before processing
(at-most-once: crash after ACK loses the message) vs ACK after processing
(at-least-once: crash after processing, before ACK ⇒ redelivery ⇒ duplicate).

```
 semantics      loss?   dupes?   cost                    use
 at-most-once   yes     no       cheapest                metrics, telemetry ticks
 at-least-once  no      YES      idempotent consumers    the default for everything
 exactly-once   no      no       heavy coordination,     Kafka→Kafka streams;
                                 narrow scope            elsewhere: build it yourself
```

**Building exactly-once *effect*** (the answer interviewers want):

1. **Idempotency keys**: every message/command carries a unique ID; consumer records processed IDs (unique constraint / `INSERT ... ON CONFLICT DO NOTHING` in the *same transaction* as the business write) — duplicates become no-ops. This is how Stripe's API works (`Idempotency-Key` header: same key ⇒ same result returned, charge executed once).
2. **Naturally idempotent operations**: `SET status='shipped'` (safe to repeat) vs `balance += 100` (not — convert to an insert of an immutable ledger entry keyed by event ID).
3. **Transactional coupling**: store the offset/message-ID with the state change in one ACID transaction; on restart, resume from stored position.
4. Kafka EOS: covers Kafka-in → process → Kafka-out atomically (idempotent producer + transactions); the moment you touch an external system, revert to (1).

### Real Production Example

Stripe idempotency keys (public API design). Every payment processor's consumer:
`processed_events(event_id PK)` table checked in-transaction. Kafka Streams EOS for
internal aggregation pipelines at LinkedIn/Confluent scale.

### Common Mistakes

- "We use Kafka so we have exactly-once" (only within Kafka; your DB write + Kafka consume is not atomic without your own idempotency).
- Deduplicating in a cache (Redis set of seen IDs) *outside* the business transaction — crash between them and the guarantee evaporates. The dedup record and the effect must commit together.
- Choosing at-most-once by accident (auto-ACK/auto-commit before processing).

### Interview Questions

1. Prove exactly-once delivery is impossible; then design exactly-once *payment processing* anyway.
2. Where exactly must the idempotency check live relative to the business write, and why?
3. Which semantics for: clickstream analytics, order emails, ledger postings?

---

## 5.6 Retries, Dead Letter Queues, Backpressure

### Why Interviewers Ask This

Retry design separates people who've run consumers in production from people who've
read about them. A bad retry strategy *causes* outages (retry storms) and stalls
pipelines (poison pills).

### Core Concept & Internal Working

**Retry strategy:**

- **Exponential backoff + jitter** (1s, 2s, 4s... ×random) — jitter prevents synchronized retry waves.
- **Retry budget/cap** (e.g., max 5 attempts) — infinite retries on a permanent failure is a stuck pipeline.
- **Classify errors**: transient (timeout, 503, deadlock) → retry; permanent (validation, 400, business rule) → straight to DLQ, retrying can't help.
- **In-broker patterns**: SQS redelivers automatically via visibility timeout + `maxReceiveCount` → DLQ redrive. Kafka has no built-in delay/retry: standard pattern is **tiered retry topics** (`orders-retry-5m`, `orders-retry-1h`) — failed message forwarded to a retry topic with delayed consumption, finally to `orders-dlq`. Note this *sacrifices per-key ordering* for the retried key — if ordering matters, either park the whole key (track keys-in-retry and divert their subsequent messages to the retry path too) or block the partition briefly instead.
- **Poison pill**: a message that fails deterministically (bad schema, corrupt payload). Without a DLQ + max attempts it stalls its partition forever (Kafka) or burns redeliveries (Rabbit/SQS).

**Dead Letter Queue**: the quarantine for messages that exhausted retries. A DLQ is
only useful with: **alerting** on arrival (a silent DLQ is a data-loss bin),
**tooling to inspect + redrive** after the bug is fixed, and retention long enough
to survive a slow incident response. DLQ entries should carry failure metadata
(exception, attempt count, original topic/offset).

**Backpressure** (consumers falling behind): the queue *is* the buffer — monitor
**lag/queue depth and its derivative**. Responses, in order: scale consumers (up to
partition count in Kafka — then add partitions), batch processing, optimize the
handler (usually a slow downstream call — parallelize per-key-safe work), shed or
degrade (skip enrichment), and rate-limit producers if the contract allows.
RabbitMQ: prefetch limits + flow control; Kafka: pull model means consumers
naturally take only what they can, lag absorbs the rest — until retention.

### Real Production Example

Uber's and Airbnb's engineering blogs both document the tiered-retry-topic + DLQ
Kafka pattern. AWS prescribes DLQs on every SQS queue and Lambda event source.
Retry storms feature in half of all public postmortems — the fix is always jitter +
budgets + circuit breaking.

### Interview Questions

1. Design the retry/DLQ pipeline for order processing on Kafka, preserving per-order ordering.
2. What's a poison pill and what happens without a DLQ?
3. Consumer lag doubled after a downstream API slowed — walk your response playbook.

---

## 5.7 Event-Driven Architecture (EDA)

### Why Interviewers Ask This

EDA is the architectural context for everything above, and its pitfalls (implicit
coupling, debugging pain, eventual consistency UX) are staff-level discussion bait.

### Core Concept

Services communicate by publishing immutable **facts** ("OrderPlaced") rather than
sending commands ("SendEmail"). Producers don't know consumers; new consumers attach
without touching producers.

```
                    ┌────────────► inventory svc (reserve stock)
 order svc ──OrderPlaced──► Kafka ─► payment svc  (charge)
   (writes DB +           │        ─► email svc    (receipt)
    outbox → publish)     └────────► analytics    (warehouse)
 adding "fraud-check svc" later = new consumer group, zero producer changes
```

Key design points:

- **Events vs commands**: events are facts, past tense, no expected reply; commands are directed requests. Mixing them muddles ownership.
- **Event schema is a public API**: version it (schema registry — Avro/Protobuf, compatibility rules), never break consumers. Thin events (IDs, fetch details) vs fat events (full payload — self-contained but stale-prone and big): choose deliberately.
- **Choreography** (services react to each other's events — loose coupling, but the workflow is invisible, spread across services) **vs orchestration** (a coordinator like Temporal/Step Functions drives the flow — visible, debuggable, one more component). Long multi-step business flows usually deserve orchestration (see Sagas, Module 7).
- **Consistency**: the system is eventually consistent between services — design UX for it (order shows "processing"), and use the **outbox pattern** (Module 7.7) so DB-write + event-publish can't diverge.
- The honest costs: harder debugging (need correlation IDs + tracing across async hops), duplicate handling everywhere (5.5), and *implicit* coupling through event schemas that's easy to underestimate.

### Real Production Example

Uber (trip lifecycle as events through Kafka), LinkedIn (everything-as-a-stream —
the origin of Kafka), Netflix (playback + operational events), Amazon (EventBridge/
SNS/SQS fabric between retail services).

### Interview Questions

1. When do events beat synchronous calls, and what do you lose? (decoupling, resilience, fan-out vs immediacy, debuggability, consistency)
2. Choreography vs orchestration for a 6-step order fulfillment flow?
3. How do you evolve an event schema without breaking 12 consumer teams?

---

## Module 5 Cheat Sheet

```
MODEL       queue = 1 consumer/message (work). topic = all groups get all (facts).
            consumer group: partitions split among members; parallelism ≤ partitions.
KAFKA       partitioned replicated LOG; retention + offsets ⇒ replay + multi-reader.
            Ordering per partition (key!). acks=all+min.isr=2 = no-loss quorum.
            Fast: sequential I/O, page cache, zero-copy, batching. Lag = the metric.
            EOS only Kafka→Kafka; else idempotent consumers.
RABBITMQ    exchanges→bindings→queues (direct/topic/fanout). ACK/NACK, priority,
            delay, prefetch, DLX. Deleted on ACK — no replay. Jobs + routing.
SQS         managed; standard = at-least-once, unordered, ∞ throughput.
            FIFO = ordered per MessageGroupId + 5-min dedup. Visibility timeout
            (must exceed processing time!). +SNS for fanout. Redrive→DLQ built in.
ORDERING    global ordering doesn't scale; order per KEY (partition key / msg group).
            Breakers: producer retries (fix: idempotence), repartitioning, parallel
            handlers, retry paths. Consumers: version checks tolerate disorder.
SEMANTICS   exactly-once DELIVERY impossible. at-least-once + IDEMPOTENCY = exactly-
            once EFFECT. Dedup record must commit IN the business transaction.
            Ledger inserts (keyed) > in-place increments.
RETRY/DLQ   backoff + jitter + max attempts; classify transient vs permanent.
            Kafka: tiered retry topics (mind ordering); SQS: visibility+redrive.
            DLQ needs alerting + inspect/redrive tooling. Poison pill stalls partitions.
BACKPRESSURE lag & its slope; scale consumers ≤ partitions, batch, optimize handler,
            shed, rate-limit producers. Retention is the deadline.
EDA         events = immutable facts; schema = versioned public API (registry).
            choreography (invisible flow) vs orchestration (coordinator).
            Outbox for atomic write+publish. Correlation IDs for debugging.
```

## Top Interview Questions (Module 5)

1. Kafka vs RabbitMQ vs SQS for three given workloads. 2. Per-user ordering at 100k
msg/s. 3. Exactly-once payment processing end to end. 4. Retry + DLQ design that
preserves ordering. 5. Consumer lag runbook. 6. acks/ISR trade-offs. 7. Visibility
timeout semantics. 8. Outbox pattern (why dual-write is broken). 9. Choreography vs
orchestration. 10. Schema evolution across many consumers.

## Common Mistakes Recap

Global-ordering claims • low-cardinality/hot partition keys • "Kafka = exactly-once"
• dedup outside the transaction • visibility timeout < processing time • infinite
retries / no DLQ / silent DLQ • retry topics silently breaking per-key order • async
where the user needs a sync answer • unversioned event schemas.

## Mock Interview Exercise

*"Design order processing for a flash-sale e-commerce site: 30k orders/min peak,
each order → charge payment, reserve inventory, send confirmation; payment
double-charging is unacceptable; email may lag minutes."* Expected: API writes order
+ outbox row in one transaction → Kafka `orders` keyed by order_id → payment
consumer with idempotency table in-transaction → tiered retries + DLQ + alerting →
inventory via reservation events with version checks → email as an independent
lagging group → lag/DLQ/duplicate-rate monitoring; explain every duplicate and
reordering path and why the design survives it.

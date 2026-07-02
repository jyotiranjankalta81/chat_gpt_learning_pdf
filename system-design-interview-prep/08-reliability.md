# Module 8 — Reliability & High Availability

This module turns Module 1's availability math into architecture: redundancy,
failover, disaster recovery, health checking, and just enough consensus (Raft) to
survive a deep dive.

---

## 8.1 High Availability & Redundancy

### Why Interviewers Ask This

"Make it highly available" is in every prompt. They grade whether you apply
redundancy *at every layer* and understand that redundancy without automated
failover and without protection from correlated failure is decoration.

### Core Concept

HA = eliminating single points of failure so component failures don't become
outages. Redundancy models:

- **Active-active**: all replicas serve traffic (LB across them). Capacity is used, failover is instant (traffic just shifts), but state must be shared/synchronized.
- **Active-passive**: standby takes over on failure. Simpler state story; failover takes detection + promotion time; the standby is money doing nothing — and untested standbys rot ("the failover that never works when finally needed").
- **N+1 / N+2 provisioning**: capacity such that losing 1 (or 2) units leaves enough. N+2 lets you do maintenance (1 down) and still survive a failure (another down).

Redundancy must be applied per layer and *across failure domains*:

```
 layer          redundancy                       failure domain to cross
 DNS            multi-provider                   provider
 LB             ≥2, anycast/VRRP                 host, AZ
 app            N+2 stateless replicas           host, AZ
 cache          replicas per shard               host, AZ
 DB             leader + replicas, quorum        host, AZ (region for DR)
 region         multi-region (8.3)               region, provider(!)
```

The enemy is **correlated failure**: two "redundant" replicas on one rack, one AZ,
one bad config push, one shared certificate, one deploy train. Real-world outages
are dominated by correlated causes (config/deploys), which is why gradual rollouts
and cell-based isolation matter as much as replica count.

### Real Production Example

AWS builds AZs as physically separate failure domains and tells you to spread
across ≥3 — a quorum needs a majority, and with 2 AZs a whole-AZ loss removes half
your nodes. Google and AWS both run **cell-based architectures** (independent
shards-of-everything called cells; a bad deploy or poison request takes out one
cell, not the fleet) — AWS explicitly describes this for its control planes.

### Interview Questions

1. Why 3 AZs and not 2? (majority quorums; 2 AZs = split-brain-or-downtime dilemma)
2. Active-active vs active-passive for a database tier?
3. Your two replicas share a rack switch — what's your actual availability?

---

## 8.2 Failover, Health Checks, Heartbeats

### Why Interviewers Ask This

Failover is where HA succeeds or fails in practice, and it hides the hardest
problem in distributed systems: *you cannot distinguish "dead" from "slow/
partitioned" over a network*.

### Core Concept & Internal Working

**Detection** — heartbeats and health checks:

- **Liveness** ("process is alive — restart if not") vs **readiness** ("can serve traffic — route away if not") — Kubernetes encodes the distinction; conflating them causes restart storms of overloaded-but-healthy pods.
- **Shallow checks** (port open, `/healthz` returns 200) vs **deep checks** (can reach DB/dependencies). Deep checks catch more but propagate dependency failures: if the DB blips, every instance "fails" its deep check simultaneously and the LB removes the entire fleet. Rule: fail deep checks only for *local* problems; report dependency state separately. Add **hysteresis** (fail after 3 consecutive misses, restore after 2 passes) to stop flapping.
- Heartbeat tuning: interval × threshold = detection time. 1 s × 3 = fast but false-positive-prone (GC pause = "death"); 10 s × 3 = calm but 30 s of black hole. There is no correct constant — say the trade-off aloud (phi-accrual detectors adapt it statistically; Cassandra uses this).

**Failover mechanics** (DB leader example):

```
 1. detect      leader misses N heartbeats (is it dead? or a partition? unknowable)
 2. elect       remaining nodes pick new leader — must be QUORUM-based (8.4)
 3. fence       old leader must be prevented from acting if it returns:
                epoch/fencing tokens (storage rejects writes from old epoch),
                or STONITH ("shoot the other node in the head")
 4. repoint     clients/proxies discover the new leader (service discovery, VIP)
 5. verify      data: async-replication tail may be LOST (Module 4.2) — reconcile
```

**Failback** (returning to the original) is a second, deliberate operation — never
automatic ping-pong.

### Real Production Example

GitHub's 2018 43-second network partition triggered automated cross-DC MySQL
failover; the old primary had writes the new one lacked → hours of reconciliation
and degraded service. It's the canonical case study: failover automation +
async replication + no clean fencing = split-brain data divergence. Patroni
(Postgres) and orchestrator (MySQL) implement quorum + fencing to get this right.

### Common Mistakes

- Deep health checks that fail fleet-wide on a dependency blip.
- Failover without fencing (split brain), or failover that's never been drilled.
- Aggressive detection timers that failover on a GC pause; DNS-based repointing with TTL assumptions (clients cache).

### Interview Questions

1. Walk me through DB leader failover step by step — where can it go wrong?
2. Liveness vs readiness; shallow vs deep — design the health checks for an API pod.
3. How do fencing tokens prevent a zombie leader from corrupting state?

---

## 8.3 Disaster Recovery (DR)

### Why Interviewers Ask This

"A whole region goes down" is a guaranteed follow-up in senior interviews. They
want RTO/RPO vocabulary, the strategy ladder, and honesty about cost.

### Core Concept

- **RTO** (Recovery Time Objective): how long until service is restored.
- **RPO** (Recovery Point Objective): how much data you may lose (time since last replication/backup).

The strategy ladder — each step ~10× the cost of the previous:

```
 strategy          RTO         RPO          cost   how
 backup & restore  hours–days  hours        $      backups in object storage,
                                                   cross-region copies, IaC to rebuild
 pilot light       tens of min minutes      $$     data replicated continuously;
                                                   minimal core infra idling in DR region
 warm standby      minutes     seconds–min  $$$    scaled-down full stack running;
                                                   scale up + shift traffic
 multi-site        ~0          ~0 (sync)    $$$$   active-active regions, traffic
 active-active                                     split, data replicated (hard part!)
```

Active-active's hard part is the data plane: sync cross-region replication costs
50–200 ms per write (physics), so most designs choose per-record home regions or
async + conflict handling (Module 4.2) and accept a small RPO.

Non-negotiables interviewers listen for: **DR that isn't tested doesn't exist**
(game days, chaos drills — Netflix Chaos Kong simulated region evacuation
regularly); backups must be restore-*tested* and isolated from the primary blast
radius (separate account/credentials — ransomware and fat-fingered deletes follow
your replication); dependencies (DNS, auth, secrets, container registry!) must also
survive the region loss or your recovery tooling is down too.

### Real Production Example

The 2021 OVH datacenter fire destroyed customer data whose "backups" lived in the
same building. AWS's us-east-1 incidents repeatedly took down *other* regions'
control planes for customers whose tooling depended on us-east-1 — the "hidden
global dependency" lesson. Netflix evacuates a region in minutes because they
rehearse it.

### Interview Questions

1. Define RTO/RPO for a payments system vs a photo archive, and pick strategies.
2. Your region died. Recovery step one? (traffic off via DNS/anycast — then data story)
3. What commonly breaks *during* DR that planning missed? (auth/secrets/DNS/registry dependencies, stale runbooks, capacity not reserved in DR region)

---

## 8.4 Consensus & Raft (Interview Level)

### Why Interviewers Ask This

Consensus underlies leader election, distributed locks, and every "how does etcd/
ZooKeeper actually work" follow-up. Interview-level Raft — roles, election, log
replication, quorum intuition — is expected at staff level.

### Core Concept

Consensus = getting a cluster of unreliable nodes to agree on a sequence of values
(a replicated log) such that agreement survives minority failure and never forks.
FLP impossibility says you can't guarantee liveness in a fully async network —
practical systems (Paxos, Raft, ZAB) use timeouts/randomization and guarantee
**safety always, liveness usually**.

The quorum arithmetic that answers half of all follow-ups: with **2f+1** nodes you
tolerate **f** failures (3→1, 5→2). Two majorities always intersect — that
intersection is why committed data can't be lost or forked, and why **even node
counts add nothing** (4 nodes still tolerate only 1).

### Internal Working — Raft in one page

```
 roles:    FOLLOWER ──election timeout (randomized 150–300ms)──► CANDIDATE
           CANDIDATE ──majority votes──► LEADER ──heartbeats──► followers
           (higher term seen at any time → step down to follower)

 election: candidate++term, votes for self, requests votes.
           voters grant one vote per term, and ONLY to candidates whose log is
           at least as up-to-date  ◄── this rule preserves committed entries.
           Randomized timeouts make split votes rare (retry with new term).

 log replication:
   client → LEADER: append entry to local log
   leader → AppendEntries RPC to all followers
   majority ACK  → entry COMMITTED → apply to state machine → reply to client
   followers learn commit index via subsequent heartbeats
   conflicting follower logs are overwritten to match the leader (leader's log wins)

 terms:    logical clock; every message carries it; stale-term messages rejected —
           this is the built-in FENCING that neutralizes zombie leaders.
```

Extras worth one sentence each: **log compaction/snapshots** (logs can't grow
forever), **membership changes** go through the log (joint consensus/single-server
changes), **leases/ReadIndex** let leaders serve linearizable reads without a full
log round trip, and Multi-Paxos ≈ Raft in steady state (Raft's contribution is
understandability: strong leader + explicit rules).

Where it runs: etcd (Kubernetes' brain), Consul, ZooKeeper (ZAB), CockroachDB/
TiDB/Spanner (consensus per data range), Kafka KRaft, cloud control planes.
Consensus is expensive (quorum round trip per write) — use it for *coordination
and metadata* (locks, leases, leader election, configs, schema), not bulk data.

### Common Mistakes

- Deploying even-numbered clusters; putting a 3-node quorum in 2 AZs.
- Using etcd/ZK as a general database (it's a coordination kernel; small data, modest write rates).
- Claiming a Raft leader can serve stale-free reads with zero protocol (needs lease/ReadIndex — otherwise a deposed leader can serve stale reads).

### Interview Questions

1. Why odd cluster sizes? Why does 5 tolerate 2? What breaks across 2 AZs?
2. Walk through a Raft election after leader death; how are split votes avoided; why can't a stale-log node win?
3. Why is committed data safe across leader changes? (majority intersection + up-to-date vote rule)

---

## 8.5 Split Brain

### Why Interviewers Ask This

It's the catastrophic failure mode of every HA design — two nodes both believing
they're the leader, both accepting writes, data diverging irreversibly. Interviewers
inject it as "what if the network partitions?"

### Core Concept & Internal Working

Cause: partition (or pause — GC, VM freeze) makes the standby think the leader died;
both act as leader. Async-replicated pairs with naive failover are the classic
victims.

Defenses (say all three):

1. **Quorum**: only the side with a majority may elect/serve as leader; the minority side steps down (this is *the* reason for 3+ nodes / 3 AZs). A 2-node pair fundamentally cannot self-arbitrate — it needs a third witness/tiebreaker.
2. **Fencing**: make the old leader *harmless* even if it doesn't know it's deposed — monotonically increasing **fencing tokens/epochs** checked by the storage layer (writes stamped with term 7 rejected once term 8 exists; Raft terms, ZooKeeper zxid, Kafka controller epoch), or STONITH (power off the old node), or storage-level reservations (SCSI-3).
3. **Leases**: leadership expires unless renewed; a paused/partitioned leader's lease lapses before a new one is granted (requires bounded clock drift — mention the GC-pause caveat from Kleppmann's Redlock critique: the pause can outlive the lease *and* the writes land after resume, hence tokens, not just leases).

```
   AZ-a │ AZ-b            partition splits 1 vs 2:
 [node1]│[node2 node3]    left: 1/3 nodes → NO quorum → steps down (read-only/halt)
   old  │  elects new     right: 2/3 → quorum → new leader, term++
 leader │  leader t=8     old leader's t=7 writes → REJECTED by storage (fenced) ✓
```

### Real Production Example

GitHub 2018 (above) is the canonical split-brain-adjacent incident. Elasticsearch
pre-7.x clusters with `minimum_master_nodes` misconfigured split-brained routinely —
the fix (7.x) was building a proper quorum-based coordination layer. Every
DB-failover tool's docs (Patroni, orchestrator) are essentially split-brain
prevention manuals.

### Interview Questions

1. Design leader failover for a 2-node primary/standby pair. (trap: add a witness/quorum — 2 nodes can't do it safely)
2. GC pauses the leader for 40 s; it wakes and keeps writing. What saves you? (fencing tokens at the storage layer — leases alone don't)
3. Where does split brain hide in application-level designs? (job schedulers, cron leaders, cache warmers — anything "only one of me should run")

---

## Module 8 Cheat Sheet

```
REDUNDANCY   active-active (capacity used, instant shift) vs active-passive (rots
             untested). N+2. Cross failure domains: host<rack<AZ<region<provider.
             Correlated failure (config/deploy) beats replica count — canary, cells.
HEALTH       liveness (restart) vs readiness (route away). Deep checks: local
             failures only, else fleet-wide self-ejection. Hysteresis. Detection
             time = interval × threshold; slow ≠ dead.
FAILOVER     detect → quorum elect → FENCE (epoch/STONITH) → repoint → reconcile
             async tail. Drill it. Failback is manual.
DR           RTO (time) / RPO (data). backup→pilot light→warm→active-active
             (≈10× cost each). Test restores; isolate backups; DNS/auth/secrets/
             registry must survive too. Untested DR = no DR.
CONSENSUS    2f+1 tolerates f (3→1, 5→2); majorities intersect ⇒ no forks; odd
             sizes; 3 AZs. Safety always, liveness usually (FLP). For coordination
             & metadata, not bulk data.
RAFT         follower→candidate (randomized timeout)→leader (majority vote, only
             up-to-date logs electable). Commit = majority append. Terms = fencing.
             Snapshots for compaction; lease/ReadIndex for linearizable reads.
SPLIT BRAIN  quorum (minority steps down) + fencing tokens checked at storage +
             leases (mind GC pauses). 2-node pairs need a witness.
```

## Top Interview Questions (Module 8)

1. Why 3 AZs / odd quorums. 2. Full DB failover walkthrough with failure points.
3. Health-check design that survives a DB blip. 4. RTO/RPO ladder for payments vs
photos. 5. Raft election + why committed entries survive. 6. Zombie leader after a
GC pause. 7. What breaks during DR that planning missed. 8. Active-active data
plane options across regions. 9. Cell-based architecture rationale. 10. Two-node
HA pair — why it can't self-arbitrate.

## Common Mistakes Recap

Redundancy in one failure domain • deep health checks ejecting the fleet •
failover without fencing • untested standbys/backups/DR • even-sized quorums •
etcd/ZK as a database • leases without tokens • automatic failback ping-pong •
forgetting recovery tooling's own dependencies.

## Mock Interview Exercise

*"Your single-region service (LB → 20 pods → Postgres primary + 2 async replicas +
Redis) must reach 99.99% and survive region loss with RPO ≤ 1 min, RTO ≤ 15 min."*
Expected: 3-AZ spread; Patroni-style quorum failover with fencing (semi-sync to cut
RPO within region); readiness vs liveness done right; warm standby region: WAL
streaming (async, lag-monitored ≤1 min), scaled-down stack, DNS/anycast shift
runbook, quarterly game day; backup vault in separate account; enumerate correlated-
failure defenses (staged deploys, config canaries).

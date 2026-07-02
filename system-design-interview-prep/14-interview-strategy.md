# Module 14 — Interview Strategy

Everything before this module is knowledge; this module is execution. A candidate
with 80% of the knowledge and a disciplined process beats a candidate with 100%
of the knowledge who rambles. Interviewers grade the *process* as much as the
design.

---

## 14.1 The 45–60 Minute Structure (with time budget)

```
 ┌────────────────────────── 45-minute version ──────────────────────────┐
 0–5    Requirements gathering (functional + non-functional + scope cuts)
 5–8    Capacity estimation (only the numbers that change the design)
 8–12   API design + data model sketch
 12–20  High-level architecture (whole system, end to end, working)
 20–35  DEEP DIVES (2–3, interviewer-steered) — where senior signal lives
 35–40  Scaling, bottlenecks, failure handling sweep
 40–45  Monitoring, security, trade-off recap, wrap-up
 └── 60-min version: stretch deep dives to ~25 min and add a 3rd dive ──┘
```

Two meta-rules: **narrate constantly** (silent whiteboarding is unassessable —
think out loud, including uncertainty: "two options here, X is simpler, Y scales
better; given our 10k QPS I'd start with X"), and **drive, but check in** ("I'll
design the write path first, then reads — sound good?"). The interviewer's
redirections are *gifts*: they're steering you toward the signal they need.

---

## 14.2 Requirement Gathering (minutes 0–5)

Never design an unscoped problem — jumping straight to boxes is the #1 rejection
pattern at senior level.

**Functional:** "Who are the users? What are the 3–5 core operations? What's
explicitly OUT of scope?" Cut scope aloud: "I'll focus on posting and feeds;
search and DMs out of scope unless you want them." (Scope-cutting is a *positive*
signal — it's what staff engineers do all day.)

**Non-functional — extract numbers, not adjectives:**

- Scale: DAU? QPS? read:write ratio? data size + growth?
- Latency: p99 targets per operation?
- Availability: how bad is downtime? (drives redundancy spend)
- Consistency: per operation — what *must* be strong? (Module 1.4 spectrum)
- Special: multi-region? compliance? spiky traffic?

If the interviewer says "you decide" — decide, state the assumption, move on
("Assuming 100M DAU and read-heavy 100:1 — correct me if you want a different
scale"). Assumption-stating is graded; dithering is not.

---

## 14.3 Capacity Estimation (minutes 5–8)

Estimate **only what changes the design** — the goal is decisions, not arithmetic
theater. Keep numbers round (powers of 10).

```
 The five numbers that matter:
 1. write QPS  = daily writes / 86,400 ≈ /10⁵, then ×2–5 for peak
 2. read QPS   = write QPS × read ratio
 3. storage    = items/day × size × retention (×replication)
 4. bandwidth  = QPS × payload (matters for media/video only)
 5. memory     = hot working set (cache sizing: ~20% of data serves ~80%+)

 Numbers to know cold: 1M/day ≈ 12/s. 100M DAU × 10 actions ≈ 12k/s avg.
 1 server ≈ thousands of simple QPS. Redis node ≈ 100k+ ops/s.
 SQL node ≈ low thousands of writes/s. Kafka ≈ effectively unbounded (partition).
```

Then *use* them aloud: "6k writes/s — a single Postgres can't take that long-term
⇒ shard or buffer through Kafka. 300k reads/s ⇒ cache-first architecture." That
sentence — numbers forcing decisions — is precisely what's graded.

---

## 14.4 API Design & Data Model (minutes 8–12)

- APIs: 4–6 core endpoints, REST-ish, with pagination cursors, idempotency keys on mutations, and auth noted. Don't enumerate CRUD for every entity.
- Data model: main entities, keys, and **the shard/partition key with justification** (Module 4.3 — this is the moment to align storage with access patterns). Note which store type each entity gets and why (Module 4.1).
- Flag the consistency class per entity as you go ("inventory row: strong; view counts: eventual").

---

## 14.5 High-Level Design (minutes 12–20)

Draw the complete request path(s) end to end — client → edge → services → data —
for the top 2–3 operations, *before* zooming anywhere. A working whole beats a
perfect fragment. Standard shape:

```
 client → DNS/CDN → LB → gateway (auth, rate limit) → services → cache → DB
                                        └→ queue → async workers → derived stores
```

Then annotate: which paths are sync vs async, where the arbiter of each invariant
lives (Module 13 cheat sheet), what's stateless vs stateful. Invite steering:
"Where would you like to go deep — the fan-out, the storage, or the failure story?"

---

## 14.6 Deep Dives (minutes 20–35) — where offers are decided

The interviewer picks 2–3 hard spots (or you propose the hardest honestly). The
expected *shape* of a senior deep-dive answer:

1. State the problem crisply ("celebrity fan-out: 100M timeline inserts for one tweet").
2. Offer 2–3 approaches with trade-offs (push / pull / hybrid).
3. **Pick one and justify with the requirements' numbers.**
4. Detail the mechanics (data structures, exact flow, edge cases).
5. Volunteer the failure modes and how you'd detect them.

Depth probes to expect, per topic: exact SQL/locking for double-booking;
idempotency-record transactionality for payments; rebalancing for sharded
anything; ordering for messaging; stampede/hot-key for caching. (All covered in
Modules 3–13 — this is what those "Interview Questions" sections were training.)

---

## 14.7 Bottlenecks, Scaling, Failure Sweep (minutes 35–40)

Run a systematic sweep — out loud, layer by layer:

- **Bottleneck hunt:** "At 10× load, what breaks first?" (usually: DB writes → shard/buffer; then hot keys; then the queue's consumers).
- **Failure walk:** kill each box in the diagram — LB, service, cache, DB leader, a whole AZ, the queue — and say what users experience and what recovers automatically (Modules 7–8 vocabulary: timeouts, breakers, failover, fencing, DR tiers).
- **Degradation plan:** what gets shed first, what serves stale, what fails closed (Module 3.7, 9.5).

Volunteering failure analysis *unprompted* is one of the strongest staff signals.

---

## 14.8 Monitoring, Security, Final Review (minutes 40–45)

- Monitoring: name the 3–5 SLIs, the burn-rate paging policy, and the one metric per subsystem (consumer lag, cache hit ratio, replication lag, DLQ depth) — Module 12.
- Security: authn/authz placement, rate limits, encryption, the invariant-protecting bits (idempotency, tokenization) — Module 9, two minutes max.
- **Final review (do not skip):** restate requirements → confirm the design meets each, with the number ("300k reads/s ⇒ 99% cache hit ⇒ 3k DB reads/s ✓"); recap the 2–3 biggest trade-offs you consciously made; name what you'd do next with more time. This closing loop is disproportionately memorable to interviewers.

---

## 14.9 How Interviewers Evaluate You

The rubric behind the scorecard (names vary by company; the axes don't):

| Axis | Mid-level looks like | Senior/Staff looks like |
|---|---|---|
| Problem structuring | jumps to solution | scopes, prioritizes, states assumptions |
| Technical depth | names components | explains internals 3 levels down on demand |
| Trade-off reasoning | one memorized answer | 2–3 options, chooses via requirements' numbers |
| Quantitative sense | skips or fumbles math | numbers drive decisions |
| Failure thinking | waits to be asked | volunteers failure modes + detection + degradation |
| Communication | silent or rambling | narrated, structured, checks in, adapts to hints |
| Pragmatism | over-engineers (or under-) | simplest thing that meets requirements; complexity budgeted |

Calibration signals per level: **senior** = owns the whole design, deep on 2–3
components, sound trade-offs; **staff** = additionally frames the problem better
than given, connects to org/operational reality (migrations, on-call, cost),
handles adversarial follow-ups ("your cache died at peak — now what?") without
wobbling. Instant negative signals: buzzwords without mechanics ("just use
Kafka"), one-size answers ("NoSQL scales"), ignoring interviewer hints twice,
no numbers anywhere, and inventing requirements to fit a rehearsed design.

---

## 14.10 Common Failure Patterns (and the fix)

1. **The memorized-design dump** — answering the question you prepared, not the one asked. *Fix: requirements first; let their numbers pick the architecture.*
2. **Depth-first rabbit hole** — 25 minutes on ID generation, no end-to-end system. *Fix: breadth first, then interviewer-guided depth.*
3. **The silent artist** — beautiful diagram, no narration. *Fix: think out loud; the diagram is evidence, the reasoning is the product.*
4. **Adjective engineering** — "highly scalable, super available" with no numbers. *Fix: every claim gets a number or a mechanism.*
5. **Happy-path only** — no failure story until asked, then improvised. *Fix: the 14.7 sweep, always.*
6. **Hint-deafness** — interviewer says "interesting, what about writes?" three times. *Fix: treat every interviewer question as the syllabus.*
7. **Over-engineering** — 12 services and 4 databases for 200 QPS. *Fix: start simple, add complexity only when a stated number forces it — and say which number.*

---

## 14.11 Preparation Plan & Mock Protocol

**Drill cadence (using this guide):** for each of Modules 1–12, do the module's
mock exercise cold, then grade against its cheat sheet. For Module 13: two
problems per sitting, 35 minutes each, spoken aloud (recording yourself is
brutal and effective), using the drill checklist (arbiter? hot key? queue?
idempotency?).

**Mock-interview protocol (with a partner or solo-recorded):** 45 minutes strict;
partner plays a steering interviewer (interrupts, redirects, asks "why" three
times on one component); afterwards score both content (rubric 14.9) and process
(time budget 14.1). Rotate problem categories: one feed-like (read-heavy fan-out),
one booking-like (consistency arbiter), one pipeline-like (write-heavy streaming),
one infra-like (cache/limiter/gateway) — these four archetypes cover nearly every
question you'll face.

**The night before:** re-read the Module 13 cross-cutting cheat sheet and the
latency/capacity numbers in 14.3 — those two pages are the highest-density review
in this guide.

---

## Module 14 Cheat Sheet — the one-page interview script

```
 0–5   SCOPE      users, 3–5 core ops, OUT-of-scope aloud; numbers for scale/
                  latency/availability/consistency; state assumptions and move.
 5–8   NUMBERS    write QPS, read QPS, storage, hot set. Round. Then USE them:
                  "6k writes/s ⇒ shard or buffer." 1M/day≈12/s.
 8–12  API+DATA   4–6 endpoints (cursors, idempotency keys); entities + SHARD KEY
                  justified; consistency class per entity.
 12–20 HIGH-LEVEL end-to-end paths for top ops; sync vs async; name the ARBITER
                  of each invariant; stateless vs stateful; invite steering.
 20–35 DEEP DIVE  problem → 2–3 options → choose via numbers → mechanics →
                  failure modes. Expect: locking, idempotency, rebalancing,
                  ordering, stampede/hot-key.
 35–40 SWEEP      10× bottleneck hunt; kill every box (user impact + recovery);
                  degradation order (shed, stale, fail-closed list).
 40–45 CLOSE      SLIs + paging; security in 2 min; RESTATE requirements vs
                  design with numbers; recap top 3 trade-offs; next steps.
 ALWAYS narrate; follow hints; numbers over adjectives; simplest thing that
 meets requirements; volunteer failures before being asked.
```

## Final Mock Interview Exercise

Full-dress rehearsal: *"Design a global event-ticketing platform (Ticketmaster):
100M users, ticket drops sell 50k seats to 2M concurrent buyers in minutes, zero
double-selling, fans see live seat maps, payments must be exact."* 45 minutes,
recorded, strict time budget. It combines every archetype: spike load (queue +
waiting room, Module 1.7), the arbiter (seat rows + holds with TTL, 13.7), hot
keys (one event = one shard's nightmare, 3.6), payment sagas + idempotency
(7.5–7.6, 13.8), real-time push (2.6), and degradation under load (14.7). Grade
yourself with 14.9's rubric — then go book the real interview.

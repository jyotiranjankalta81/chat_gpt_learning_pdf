# Module 12 — Observability

"How do you know it's working?" is the closing question of most interviews, and a
concrete answer — named metrics, alert policy, debug workflow — reliably earns the
operational-maturity checkmark. This module also covers how engineers actually
debug production.

---

## 12.1 The Three Pillars: Logs, Metrics, Traces

### Why Interviewers Ask This

They want you to know what each signal is *for*, what each costs, and how they
compose into a debugging workflow — not just recite the triad.

### Core Concept

| Signal | Answers | Shape | Cost profile |
|---|---|---|---|
| **Metrics** | "is something wrong? how much? trend?" | numeric time series, pre-aggregated | cheap to store/query; cardinality is the danger |
| **Logs** | "what exactly happened in this case?" | per-event records | expensive at volume; sampling/retention tiers |
| **Traces** | "where in the call graph did it happen?" | request tree with timed spans | sampled; the glue across services |

**Logging (production-grade):** structured (JSON key-value, not printf prose) so
it's queryable; **correlation/trace IDs on every line** (the single highest-value
logging practice — without it, microservice logs are confetti); levels used
honestly (ERROR pages someone); no secrets/PII (scrubbing); centralized (stdout →
collector → Elasticsearch/Loki/cloud) with retention tiers (hot 7–30 d, archive to
object storage); sample high-volume INFO, never sample ERROR. Anti-pattern to name:
logs as metrics ("count ERROR lines to alert") — brittle and expensive; emit a
counter instead.

**Metrics:** counters (requests_total), gauges (queue_depth), **histograms**
(latency distributions — percentiles come from these). Two framing standards to
cite: **RED** per service (Rate, Errors, Duration) and **USE** per resource
(Utilization, Saturation, Errors); Google's four golden signals = latency, traffic,
errors, saturation. **Cardinality discipline**: labels multiply series
(`endpoint × status × region` fine; `user_id` in a label = series explosion that
takes down the metrics system itself — the classic observability self-own).

**Tracing:** a request gets a **trace ID** at the edge; each hop creates **spans**
(operation, start, duration, tags, parent) and **propagates context** in headers
(W3C `traceparent`); the backend (Jaeger/Tempo/Zipkin/Datadog) assembles the tree:

```
 trace 8f3a…  POST /checkout                      total 1.9s
 ├─ gateway (12ms)
 ├─ order-svc (1.85s)
 │   ├─ inventory-svc GET /stock (35ms)
 │   ├─ payment-svc POST /charge (1.72s)  ◄── there's your problem
 │   │    └─ psp-external (1.70s)         ◄── and its cause
 │   └─ db INSERT order (18ms)
 └─ notification enqueue (3ms)
```

Sampling is mandatory at scale: head-based (decide at start, e.g. 1%) vs
**tail-based** (decide after completion — keep all errors and slow traces, sample
the boring; more infra, far better signal).

### Real Production Example

Google Dapper (2010) birthed modern tracing; Uber built Jaeger; Netflix Atlas
handles ~billions of metrics series with aggressive cardinality control. Every
serious postmortem you read follows the metrics→traces→logs funnel below.

### Interview Questions

1. Which signal do you reach for first when p99 spikes, and in what order do you use the rest?
2. Why is `user_id` fine in logs but catastrophic as a metric label?
3. Head vs tail sampling — what do you lose with 1% head sampling? (most errors and rare slow paths never captured)

---

## 12.2 Monitoring & Alerting

### Why Interviewers Ask This

Bad alerting causes both missed outages and burned-out on-call rotations; your
alert philosophy reveals whether you've carried a pager.

### Core Concept

- **Symptom-based paging, cause-based dashboards**: page on what users feel (SLO burn: error rate, latency, availability — Module 1.6); CPU/disk/replication-lag alerts are tickets or dashboard context, not 3am pages. Every page must be: actionable, urgent, and novel (else it's noise training people to ignore pages).
- **Burn-rate alerting** (the modern standard): page when the error budget is being consumed at e.g. 14× rate over 1 h (fast burn) or 6× over 6 h (slow burn) — catches both cliff-falls and slow bleeds without flapping on blips.
- Alert hygiene: multi-window confirmation, hysteresis, alert on *absence* of data too (a dead exporter looks like perfect health), runbook links in every alert, weekly review of pages (each page → fix, tune, or delete).
- **Synthetic monitoring / probers**: scripted user journeys from outside your network — catches DNS/TLS/CDN/login failures your internal metrics can't see. **Dashboards**: per-service standard layout (RED top, resources below, dependencies' health beside) so responders navigate by muscle memory.

### Interview Questions

1. Design the alerts for a payments API with a 99.95% SLO. (burn-rate pages, latency-threshold SLI, synthetic probe on the full payment journey, DLQ-depth ticket)
2. Your on-call gets 40 pages/week — triage the alert catalog.
3. Why symptom-based paging? What's the failure mode of paging on CPU?

---

## 12.3 Prometheus & Grafana (and the metrics pipeline)

### Core Concept & Internal Working

**Prometheus**: **pull-based** scraper — services expose `/metrics` (text
exposition), Prometheus scrapes every 15–60 s, stores locally in a TSDB, evaluates
**PromQL** alert rules, fires to **Alertmanager** (dedup, grouping, silences,
routing to PagerDuty/Slack). Service discovery (K8s) auto-finds scrape targets —
pull means the monitoring system *knows* when a target vanishes (vs push, where
silence is ambiguous); push gateway exists for short-lived jobs.

PromQL fluency (one line each is enough in interviews):

```
 rate(http_requests_total{status=~"5.."}[5m])            error rate
 histogram_quantile(0.99, rate(latency_bucket[5m]))      p99 from histogram
 sum by (endpoint) (rate(http_requests_total[5m]))       traffic per endpoint
```

Scaling story (expected at senior level): a single Prometheus is vertical-only and
local-disk — federate or use **Thanos/Cortex/Mimir** (global query over many
Prometheis + object-storage long-term retention + HA dedup). Histograms: buckets
are pre-defined (native histograms improve this); percentiles are per-scrape-target
— aggregate with care (you can't average percentiles; aggregate the buckets).

**Grafana**: the visualization/alerting layer over Prometheus (and Loki logs +
Tempo traces — the open-source LGTM stack), with variables/templating for
per-service dashboard reuse, and annotations (deploy markers — the single most
useful debugging overlay: 80% of incidents correlate with a deploy).

### Interview Questions

1. Pull vs push trade-offs? (target liveness knowledge, scrape control, firewall/ephemeral-job friction)
2. How do you get a *global* p99 across 200 pods? (aggregate histogram buckets, then quantile — never average per-pod p99s)
3. Prometheus retention is 15 days local — long-term + HA story? (Thanos/Mimir + object storage)

---

## 12.4 OpenTelemetry (High Level)

### Core Concept

The vendor-neutral standard unifying all three signals: one **API + SDK** per
language for producing metrics/logs/traces, **automatic instrumentation** for
common frameworks (HTTP/gRPC/DB clients — trace context propagation for free), the
**OTLP** wire protocol, and the **OTel Collector** — a pipeline component that
receives, processes (batch, scrub PII, tail-sample, add metadata), and exports
telemetry to any backend (Prometheus, Jaeger, Datadog, vendor X).

The architectural argument interviewers like: instrument **once** with the
standard, choose/replace backends freely (no vendor lock-in at the code layer), and
put governance (sampling, scrubbing, routing) in the collector instead of every
service.

```
 services (OTel SDK, auto-instr) ──OTLP──► OTel Collector ──► Prometheus/Mimir
                                            (batch, sample,  ├─► Tempo/Jaeger
                                             scrub, route)   └─► Loki / vendor
```

### Interview Question

"Your org runs three observability vendors across teams — how do you rationalize
telemetry?" (OTel SDKs + collectors as the abstraction; backends become swappable)

---

## 12.5 How Engineers Actually Debug Production Issues

### Why Interviewers Ask This

This is the war-story filter. The expected shape is a disciplined funnel, not tool
name-dropping.

### The workflow

```
 1. DETECT     page fires (SLO burn) — or worse, users/support report first
 2. SCOPE      dashboards: which service, endpoint, region, percentile, cohort?
               blast radius → severity → do we need incident command?
 3. CORRELATE  what changed? deploy markers, feature flags, config pushes,
               dependency status, traffic anomalies. ~most incidents are changes:
               MITIGATE FIRST (rollback/flag off/failover/shed) — root cause later.
 4. NARROW     traces: which span grew? errors: which exception class exploded?
               one bad pod (skew) or fleet-wide? upstream or downstream?
 5. INSPECT    logs by trace ID for exemplar requests; DB slow log; queue lag;
               connection pools; GC; recent schema changes.
 6. MITIGATE   rollback, scale out, breaker/flag, shed load, warm caches, failover.
 7. VERIFY     SLIs recover; watch for the second wave (retry storms, cold caches).
 8. POSTMORTEM blameless; timeline; contributing factors; action items with owners
               — the incident's value is the prevention it buys.
```

Habits that mark seniority: mitigate before root-causing; check deploys/flags
*first*; distrust single signals (a healthy dashboard + screaming users = your
telemetry is lying — probe from outside); keep hypotheses falsifiable ("if it were
the DB, we'd see X"); write down the timeline as you go.

### Interview Questions

1. Checkout errors at 2%: walk me through your first 10 minutes, out loud.
2. Metrics look healthy but users are down — how is that possible? (edge/DNS/CDN failure outside your measurement, wrong SLI vantage point, telemetry pipeline itself down → synthetic probes)
3. What makes a postmortem useful vs theater? (blameless, contributing factors over single cause, tracked action items)

---

## Module 12 Cheat Sheet

```
PILLARS    metrics = cheap aggregate "what/how much"; logs = per-event "exactly
           what" (structured + trace IDs, scrubbed, sampled INFO never ERROR);
           traces = "where in the call graph" (context propagation, tail sampling).
FRAMEWORKS RED (rate/errors/duration per service), USE (util/saturation/errors per
           resource), golden signals. Histograms → percentiles; cardinality kills.
ALERTING   page on SYMPTOMS (SLO burn-rate multi-window); causes → tickets/
           dashboards. Actionable+urgent+novel. Alert on absence. Runbooks.
           Synthetic probes from outside.
PROMETHEUS pull /metrics, TSDB, PromQL, Alertmanager; K8s discovery; Thanos/Mimir
           for HA + long retention; aggregate buckets not percentiles.
GRAFANA    dashboards + LGTM stack; deploy annotations = fastest correlation tool.
OTEL       one SDK for all signals, auto-instrumentation, OTLP → Collector
           (batch/scrub/sample/route) → any backend. Kills vendor lock-in.
DEBUGGING  detect → scope → correlate CHANGES (mitigate first!) → narrow via
           traces → logs by trace ID → mitigate → verify (second wave) →
           blameless postmortem with owned actions.
```

## Top Interview Questions (Module 12)

1. Design observability for a new microservice (what you emit, what pages).
2. p99 spike: which signal first and the full funnel. 3. Cardinality explosion —
cause and guardrails. 4. Burn-rate alerting mechanics. 5. Global p99 across pods.
6. Pull vs push. 7. Tail vs head sampling. 8. OTel's architectural value.
9. "Dashboards green, users down." 10. First 10 minutes of an incident.

## Common Mistakes Recap

Unstructured logs • no trace IDs • user_id metric labels • paging on CPU •
alert fatigue (non-actionable pages) • averaging percentiles • 1% head sampling
losing all errors • no synthetic probes • root-causing before mitigating • logs-as-
metrics alerting • no deploy markers.

## Mock Interview Exercise

*"You inherit a 30-service platform with printf logs, no tracing, and a single
'CPU > 80%' alert. Design the observability program and the rollout order."*
Expected: OTel auto-instrumentation first (traces + RED metrics nearly free) →
structured logging with trace IDs → SLOs per user journey + burn-rate paging +
synthetic probes → Prometheus/Mimir + Grafana standard dashboards with deploy
annotations → tail-sampled tracing → alert catalog review cadence. Justify the
order by debugging value per unit effort.

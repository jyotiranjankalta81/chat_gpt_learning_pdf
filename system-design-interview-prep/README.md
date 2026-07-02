# System Design Interview Mastery

A production-grade system design interview prep guide for Senior, Staff, and
Backend engineers (5+ years experience). No beginner theory — only concepts that
repeatedly appear in real interviews and real production systems.

**📄 The complete guide: [`System_Design_Interview_Mastery.pdf`](System_Design_Interview_Mastery.pdf)** (118 pages)

## Contents

| Module | File | Topics |
|---|---|---|
| Intro | `00-introduction.md` | How the guide works, interviewer rubric |
| 1 | `01-foundations.md` | Latency/throughput, scaling, CAP/PACELC, SLA/SLO/SLI, load patterns, stateless vs stateful |
| 2 | `02-networking.md` | HTTP/1.1–3, TCP/UDP/QUIC, HTTPS/TLS, DNS, CDN, LB/proxy/gateway, NAT, WebSocket, gRPC |
| 3 | `03-caching.md` | Redis vs Memcached, cache patterns, invalidation, stampede, hot keys, distributed cache |
| 4 | `04-database-design.md` | SQL vs NoSQL, replication modes, sharding, indexing, schema design, pooling, CQRS |
| 5 | `05-messaging.md` | Kafka, RabbitMQ, ActiveMQ, SQS, ordering, delivery semantics, DLQ/retries, EDA |
| 6 | `06-storage.md` | Object/block/file/blob storage, distributed file systems (GFS/HDFS), trade-offs |
| 7 | `07-microservices.md` | Boundaries, discovery, gateway, circuit breaker/retry/timeout/bulkhead, idempotency, 2PC vs saga, outbox |
| 8 | `08-reliability.md` | HA, redundancy, failover, DR (RTO/RPO), health checks, consensus, Raft, split brain |
| 9 | `09-security.md` | Authn/authz, sessions vs JWT, OAuth 2.0/OIDC, API keys, rate limiting, TLS/encryption, secrets |
| 10 | `10-performance.md` | Bottleneck analysis, profiling, slow queries, pool exhaustion, N+1, compression, pagination, batch/streaming |
| 11 | `11-distributed-systems.md` | Consistent hashing, Bloom filters, Merkle trees, vector clocks, leader election, gossip, distributed locks, clocks |
| 12 | `12-observability.md` | Logs/metrics/traces, alerting, Prometheus/Grafana, OpenTelemetry, production debugging |
| 13 | `13a-…` / `13b-design-problems-*.md` | 27 classic problems: URL shortener, feeds, WhatsApp, YouTube/Netflix, Drive/Dropbox, Uber, bookings, payments, e-commerce/inventory, notifications, autocomplete, crawler, distributed cache, rate limiter, API gateway, logging, analytics |
| 14 | `14-interview-strategy.md` | The 45–60 min playbook, capacity math, evaluation rubric, failure patterns, mock protocol |

Every core topic follows a 15-part template (why it's asked → internals → ASCII
diagram → production example → trade-offs → failures → monitoring → interview
questions → exercise), and every module ends with a cheat sheet, top questions,
common mistakes, and a mock interview exercise.

## Rebuilding the PDF

```bash
pip install markdown weasyprint
python3 generate_pdf.py
```

# System Design Interview Mastery

## A Production-Grade Guide for Senior, Staff, and Backend Engineers

This guide is written for engineers with 5+ years of backend experience preparing for
Senior Software Engineer, Staff Engineer, and Backend Engineer system design interviews
at companies like Google, Meta, Amazon, Netflix, Uber, Stripe, Microsoft, Airbnb,
LinkedIn, and Cloudflare.

It deliberately skips beginner material and academic theory. Every topic here is
included because it (a) appears repeatedly in real interviews and (b) is used daily in
real production systems.

### How This Guide Is Organized

| Module | Focus |
|---|---|
| 1 | Foundations: latency, scaling, CAP/PACELC, SLA/SLO/SLI, load patterns |
| 2 | Networking: HTTP/1.1–3, TCP/UDP/QUIC, DNS, CDN, LB, gRPC, WebSocket |
| 3 | Caching: Redis, Memcached, patterns, stampede, hot keys |
| 4 | Database design: replication, sharding, indexing, CQRS |
| 5 | Messaging: Kafka, RabbitMQ, SQS, delivery semantics, DLQ, EDA |
| 6 | Storage: object/block/file/blob, distributed file systems |
| 7 | Microservices: discovery, circuit breakers, sagas, outbox, idempotency |
| 8 | Reliability: HA, failover, DR, consensus, Raft, split brain |
| 9 | Security: authn/authz, JWT, OAuth 2.0, OIDC, rate limiting, TLS |
| 10 | Performance: bottlenecks, profiling, N+1, pagination, streaming |
| 11 | Distributed systems: consistent hashing, Bloom filters, locks, clocks |
| 12 | Observability: logs, metrics, traces, Prometheus, Grafana, OTel |
| 13 | 27 classic system design problems, solved end to end |
| 14 | Interview strategy: how to run a 45–60 minute interview and how you are graded |

### The Topic Template

Every core topic follows the same 15-part structure so you can drill it into a
repeatable mental model:

1. **Why interviewers ask this** — the signal they are probing for
2. **Core concept** — the one-paragraph mental model
3. **Internal working** — what actually happens under the hood
4. **Visual architecture** — an ASCII diagram
5. **Real production example** — how a large company uses it
6. **Advantages** — when it wins
7. **Trade-offs** — what you pay for it
8. **Common mistakes** — what weak candidates say
9. **Scaling considerations** — behavior at 10x and 100x
10. **Failure scenarios** — how it breaks in production
11. **Monitoring & debugging** — what to measure and how to investigate
12. **Interview questions** — direct questions you will be asked
13. **Follow-up questions** — the second-order probes that separate senior from mid-level
14. **Best practices** — production rules of thumb
15. **Hands-on design exercise** — apply it yourself

Where topics are tightly coupled (for example SLA/SLO/SLI), they are taught together
so the comparisons — which are what interviewers actually grade — stay in one place.

### How Interviewers Grade You (Preview)

Interviewers at senior+ level are not checking whether you know what a load balancer
is. They are grading:

- **Requirement discipline** — do you scope before you design?
- **Quantitative reasoning** — can you estimate QPS, storage, and bandwidth and let the numbers drive the design?
- **Trade-off fluency** — do you present two or three options and argue for one, or do you dump a single memorized architecture?
- **Failure thinking** — do you volunteer what breaks, or wait to be asked?
- **Depth on demand** — when the interviewer says "zoom into X", can you go three levels deep?
- **Communication** — can a colleague implement your design from your whiteboard?

Keep this rubric in mind through every module. Module 14 expands it into a full
playbook.

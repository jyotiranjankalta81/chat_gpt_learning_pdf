# Topic Priority Matrix
## What to Learn First — Ranked by Interview Weight and Career Impact

---

## Priority Tiers

### Tier 1 — Master These First (Critical Path)
*Learn these before any other topic. They appear in every interview.*

| Topic | Section | Time to Learn | Interview Frequency |
|-------|---------|---------------|---------------------|
| Java OOP, Generics, Collections | 1 | 1 week | Every Java interview |
| Streams & Lambdas | 1 | 3 days | Very high |
| Spring DI + Bean Lifecycle | 3 | 4 days | Every Spring interview |
| Spring MVC + REST APIs | 3 | 3 days | Very high |
| @Transactional internals | 3, 5 | 2 days | Very high |
| Node.js → Java mapping | 14 | Ongoing | Your bridge concept |
| JVM Heap/Stack/GC basics | 2 | 3 days | High |
| CompletableFuture basics | 7 | 2 days | High |
| SQL optimization + JPA N+1 | 5 | 4 days | Very high |
| Concurrency basics (sync, volatile, AtomicXxx) | 7 | 1 week | Very high |

---

### Tier 2 — Learn Within Month 2 (Differentiators)
*These topics set senior candidates apart from junior ones.*

| Topic | Section | Time to Learn | Interview Frequency |
|-------|---------|---------------|---------------------|
| Spring Security + JWT + OAuth2 | 9 | 1 week | High (banks) |
| Transaction isolation levels | 5 | 3 days | High (banks) |
| Kafka producers/consumers | 6 | 1 week | Very high |
| Circuit breaker + Retry | 4 | 3 days | High |
| ThreadPoolExecutor internals | 7 | 3 days | High |
| GC algorithms + tuning | 2 | 1 week | Medium-High |
| HikariCP sizing | 5 | 1 day | Medium |
| Idempotency patterns | 4 | 2 days | High (payments) |
| Redis patterns (cache-aside, locks) | 10 | 3 days | High |
| System design fundamentals | 10 | Ongoing | Very high |

---

### Tier 3 — Learn Within Month 3 (Depth)
*Needed for senior/staff roles and deep specialization.*

| Topic | Section | Time to Learn | Interview Frequency |
|-------|---------|---------------|---------------------|
| Saga pattern + distributed transactions | 6 | 1 week | High (banks) |
| Event sourcing + CQRS | 6 | 1 week | Medium-High |
| CAP theorem + PACELC | 6 | 3 days | Medium |
| AOP internals | 3 | 3 days | Medium |
| Spring WebFlux (reactive) | 3 | 1 week | Medium |
| Flyway/Liquibase migrations | 5 | 2 days | Medium |
| OWASP + secure coding | 9 | 1 week | High (banks) |
| JVM profiling + thread dumps | 2 | 1 week | Medium |
| Deadlock prevention + race conditions | 7 | 3 days | High |
| K8s deployment for Java | 8 | 3 days | Medium |

---

### Tier 4 — Learn Within Month 4-5 (Mastery)
*Needed for top-tier companies and principal/staff-level roles.*

| Topic | Section | Time to Learn | Interview Frequency |
|-------|---------|---------------|---------------------|
| Virtual threads (Project Loom) | 7 | 2 days | Growing |
| GraalVM native images | 8 | 3 days | Low-Medium |
| Lock-free programming (CAS) | 7 | 1 week | High (FAANG) |
| JVM bytecode and classloading | 2 | 1 week | Medium (staff) |
| Spring autoconfiguration internals | 3 | 3 days | Medium |
| Elasticsearch integration | 10 | 1 week | Medium |
| API gateway design | 4, 10 | 1 week | Medium |
| Advanced Kafka (transactions, streams) | 6 | 1 week | Medium-High |
| DDD + aggregate design | 6, 13 | 2 weeks | High (banks) |
| Architecture decision records | 12, 13 | Ongoing | Growing |

---

## Company-Specific Priority

### FAANG Companies (Google, Amazon, Meta, Apple, Netflix)

```
MUST master (ranked):
1. DSA — LeetCode Medium/Hard fluency (non-negotiable)
2. System Design HLD — design at scale (millions of users)
3. Behavioral (Amazon: Leadership Principles, Google: Googliness)
4. Java concurrency — thread safety, deadlocks, CompletableFuture
5. JVM internals — GC, heap, performance tuning
6. Distributed systems — Kafka, consistency, CAP

Good to have:
- Spring expertise (assumed, not deeply tested at FAANG)
- Specific database internals
- Cloud-specific tools
```

### Global Banks (HSBC, Goldman, JP Morgan, Morgan Stanley)

```
MUST master (ranked):
1. Spring ecosystem — deep knowledge (DI, security, data)
2. Transaction management — isolation levels, distributed transactions
3. Security — OAuth2, JWT, OWASP, PCI-DSS awareness
4. Kafka + event-driven — message ordering, idempotency
5. JPA/Hibernate — N+1, caching, pessimistic/optimistic locking
6. Compliance patterns — audit logging, immutable audit trails

Good to have:
- DSA (asked, but medium difficulty is sufficient)
- System design (asked, but financial systems focus)
- Saga/event sourcing (asked in senior roles)
```

### Product Companies (Stripe, Atlassian, Uber, Adobe)

```
MUST master (ranked):
1. API design quality — REST best practices, versioning
2. Microservices resilience — CB, retry, timeouts
3. Kafka / event-driven architecture
4. Observability — metrics, tracing, logging
5. DSA — Medium level solid, Hard exposure
6. System design — product-specific systems

Good to have:
- Spring expertise
- Database optimization
- Cloud infrastructure (AWS/GCP)
```

---

## Learning Time Investment Guide

```
Weeks 1-2:  Tier 1 core language (20h/week = 40h total)
Weeks 3-4:  Tier 1 Spring + first project (20h/week)
Weeks 5-8:  Tier 2 topics + second project (15h/week)
Weeks 9-12: Tier 3 topics + interview prep starts (15h/week)
Weeks 13-20: Interview prep + Tier 4 topics + mock interviews (15h/week)

Total investment: ~300 hours over 5 months for interview-ready proficiency
                  ~500 hours for staff-level depth
```

---

## Quick Assessment: Are You Ready?

### Junior Ready (6-12 month target at mid-tier companies)
- [ ] Can write a Spring Boot CRUD API without help
- [ ] Understand @Transactional and its main pitfalls
- [ ] Can solve LeetCode Easy problems in Java fluently
- [ ] Know the main JPA annotations and can avoid N+1
- [ ] Can explain JWT authentication flow

### Senior Ready (Target: HSBC, Atlassian, Stripe)
- [ ] Can design a microservices system from scratch
- [ ] Know Kafka producer/consumer patterns cold
- [ ] Can explain transaction isolation levels and when to use each
- [ ] Proficient in LeetCode Medium problems
- [ ] Can implement circuit breaker and retry patterns
- [ ] Know OAuth2 client credentials flow deeply

### Staff Ready (Target: FAANG, Goldman, Stripe senior)
- [ ] Can design a global payment system with 100k TPS
- [ ] Deep JVM knowledge (GC tuning, thread dump diagnosis)
- [ ] Can implement event sourcing and CQRS
- [ ] LeetCode Hard familiarity
- [ ] Can articulate trade-offs for major architectural decisions
- [ ] Can lead technical design discussions with clear, structured thinking

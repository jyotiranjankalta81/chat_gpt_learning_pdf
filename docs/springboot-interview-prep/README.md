# Spring Boot & Microservices Interview Mastery — Senior SWE Track

A complete, interview-focused course for engineers transitioning from
Node.js / Express / MERN to **Java & Spring Boot**, targeting **Senior Software
Engineer / Backend / Spring Boot Developer** roles.

Every topic is taught with the same structure: *why interviewers ask it → core
concept → internal working → lifecycle/flow → ASCII diagram → production example →
advantages → trade-offs → common mistakes → performance → debugging → interview
questions → follow-ups → hands-on exercise → best practices*, and every module
ends with a **one-page cheat sheet, top questions, common mistakes, and a mock
interview**.

## Modules
1. Core Java for Spring Interviews (JVM, memory, GC, collections, streams, concurrency)
2. Spring Core (IoC, DI, bean lifecycle, scopes, autowiring, circular deps, profiles)
3. Spring Boot (auto-configuration, starters, embedded Tomcat, validation, actuator)
4. Spring MVC (DispatcherServlet request lifecycle, message converters, content negotiation)
5. Spring Data JPA & Hibernate (persistence context, dirty checking, N+1, transactions, locking)
6. Spring Security (filter chain, AuthN flow, JWT/OAuth2/OIDC, CSRF/CORS)
7. Microservices (gateway, discovery, resilience, saga, outbox, idempotency, gRPC)
8. Messaging (Kafka & RabbitMQ, ordering, delivery guarantees, DLQ)
9. Redis (caching strategies, distributed lock, session store, rate limiting)
10. Database (ACID, isolation levels, indexes, query optimization, HikariCP, migrations)
11. Observability (Actuator, Micrometer, Prometheus, Grafana, tracing, OpenTelemetry)
12. Docker & Kubernetes (images, Compose, pods/deployments/services, config/secrets, probes)
13. Production Scenarios (memory leaks, high CPU, slow APIs, deadlocks, pool exhaustion, lag)
14. Frequently Asked Coding Questions (REST, pagination, upload, validation, retry, async)
15. Company Interview Questions (Google, Amazon, Netflix, Uber, LinkedIn, JPMorgan, etc.)

## Layout
- `src/module-XX-*.md` — Markdown source for each module.
- `build_pdfs.py` — renders per-module PDFs + a cumulative **Master PDF**.
- Generated PDFs are written to the parent `docs/` directory:
  - `../SpringBoot_Interview_Module_XX_*.pdf`
  - `../SpringBoot_Interview_Master.pdf`

## Build the PDFs
```bash
pip install markdown weasyprint
python3 docs/springboot-interview-prep/build_pdfs.py
```

Each PDF includes a cover page, table of contents, page numbers, ASCII/flow
diagrams, code examples, cheat sheets, and mock interviews with consistent
formatting.

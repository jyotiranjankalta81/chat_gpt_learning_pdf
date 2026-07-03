# Enterprise Engineering Checklist
## Production-Ready Java Service Standards

---

## API Layer Checklist

- [ ] REST endpoints follow naming conventions (`/api/v{n}/resources/{id}`)
- [ ] HTTP methods used correctly (GET=read, POST=create, PUT=replace, PATCH=update, DELETE=remove)
- [ ] Response status codes correct (201 for created, 204 for no content, 422 for validation errors)
- [ ] Input validation with `@Valid` on all request bodies
- [ ] Custom validation for business rules
- [ ] Paginated responses for list endpoints (Pageable, Page<T>)
- [ ] Idempotency key header for mutating operations
- [ ] Request ID / trace ID propagated through service calls
- [ ] API versioning strategy defined (URI versioning recommended)
- [ ] `@ControllerAdvice` for global exception handling
- [ ] No internal exception details in API responses
- [ ] API documentation (Springdoc/OpenAPI configured)

---

## Security Checklist

- [ ] Authentication implemented (JWT, OAuth2, or API key)
- [ ] Authorization checked for every endpoint (not just "is authenticated")
- [ ] Row-level security: users can only access their own resources
- [ ] Password hashing with BCrypt (cost factor ≥ 10)
- [ ] Account lockout after failed login attempts
- [ ] Rate limiting on authentication endpoints
- [ ] CORS configured (not `allowedOrigins("*")` in production)
- [ ] CSRF protection enabled (or disabled only for stateless JWT APIs)
- [ ] Security headers configured (HSTS, X-Frame-Options, CSP)
- [ ] Sensitive data excluded from logs and error responses
- [ ] Secrets in environment variables or secrets manager (never in code)
- [ ] Dependencies scanned for CVEs (OWASP dependency check in CI)
- [ ] Input validation prevents SQL injection, XSS
- [ ] Audit logging for sensitive operations (financial, admin, PII)

---

## Database Checklist

- [ ] Database migrations use Flyway/Liquibase (not DDL auto)
- [ ] `ddl-auto: validate` in production
- [ ] All migrations tested on staging with production-like data
- [ ] Proper indexes for all frequent query patterns
- [ ] N+1 queries eliminated (SQL logging enabled in dev, counted)
- [ ] `FetchType.LAZY` on all `@OneToMany` and `@ManyToMany`
- [ ] `@Version` on entities with concurrent update scenarios
- [ ] `BigDecimal` for all monetary/financial calculations
- [ ] Transaction isolation level explicitly chosen (not default)
- [ ] `@Transactional(readOnly = true)` on read operations
- [ ] Connection pool sized appropriately (HikariCP config present)
- [ ] Connection pool metrics monitored
- [ ] Database credentials in secrets management, not application.yml

---

## Resilience Checklist

- [ ] Circuit breaker on all external service calls
- [ ] Retry with exponential backoff and jitter
- [ ] Timeout configured on all HTTP clients
- [ ] Timeout configured on all database queries
- [ ] Bulkhead configured (separate thread pools for critical paths)
- [ ] DLQ (Dead Letter Queue) for all async message processing
- [ ] Idempotent message consumers (deduplication)
- [ ] Graceful degradation strategy documented for each downstream dependency
- [ ] Rate limiting on public endpoints

---

## Observability Checklist

- [ ] Structured JSON logging in production
- [ ] MDC populated with: traceId, requestId, userId on every request
- [ ] MDC cleared after each request (prevent thread pool leakage)
- [ ] Distributed tracing configured (Micrometer Tracing / OTel)
- [ ] Custom business metrics registered (payments processed, failures, durations)
- [ ] Prometheus endpoint enabled (`/actuator/prometheus`)
- [ ] Dashboards exist for: error rates, latency (P50/P95/P99), throughput, saturation
- [ ] Alerts configured for: error rate spikes, latency degradation, pod restarts
- [ ] Health endpoints: `/actuator/health/liveness` and `/actuator/health/readiness`
- [ ] Custom `HealthIndicator` for critical dependencies (DB, external APIs)
- [ ] Log level configurable without restart (`/actuator/loggers`)

---

## Performance Checklist

- [ ] JVM heap sized appropriately (`-Xms` = `-Xmx` to avoid resize GC)
- [ ] GC algorithm chosen for workload (G1GC default, ZGC for low-latency)
- [ ] Container support enabled (`-XX:+UseContainerSupport`)
- [ ] Maximum RAM percentage set (`-XX:MaxRAMPercentage=75.0`)
- [ ] Thread pool sizes configured (not using defaults)
- [ ] Redis or local cache for frequently-read reference data
- [ ] Database queries optimized (EXPLAIN ANALYZE reviewed for new queries)
- [ ] Pagination for all list operations (no unbounded queries)
- [ ] Lazy loading used for collections (not EAGER)
- [ ] Heap dump on OOM configured (`-XX:+HeapDumpOnOutOfMemoryError`)
- [ ] GC logging enabled in production (`-Xlog:gc*`)

---

## Kubernetes Deployment Checklist

- [ ] Liveness probe configured with appropriate `initialDelaySeconds`
- [ ] Readiness probe configured (traffic only when truly ready)
- [ ] Resource requests AND limits defined (memory and CPU)
- [ ] `preStop` hook with sleep for graceful load balancer deregistration
- [ ] `terminationGracePeriodSeconds` >= application shutdown timeout
- [ ] `server.shutdown: graceful` in Spring Boot config
- [ ] Secrets stored in k8s Secrets or external secrets manager
- [ ] ConfigMap for non-sensitive configuration
- [ ] HPA configured (CPU-based or custom metrics)
- [ ] Pod disruption budget (ensure minimum availability during rolling updates)
- [ ] Pod anti-affinity (prevent all pods on same node)
- [ ] Non-root user in Dockerfile
- [ ] Read-only filesystem where possible

---

## Testing Checklist

- [ ] Unit tests for all business logic (no Spring context needed)
- [ ] Integration tests with Testcontainers (real DB, real Kafka)
- [ ] MockMvc tests for API layer (request/response validation)
- [ ] Test coverage threshold configured (e.g., JaCoCo ≥ 80%)
- [ ] Architecture tests with ArchUnit (layer dependency rules enforced)
- [ ] Contract tests for inter-service APIs (Pact or Spring Cloud Contract)
- [ ] Performance/load tests for critical paths (JMeter / Gatling)
- [ ] Security tests (OWASP ZAP in CI pipeline)
- [ ] Tests run in CI before any deployment

---

## Team Engineering Checklist

- [ ] Code review process defined (who reviews, what to look for)
- [ ] PR template exists (description, testing steps, checklist)
- [ ] Branching strategy defined (main, develop, feature/*)
- [ ] Code style enforced (Checkstyle or Google Java Style in CI)
- [ ] Architecture Decision Records (ADRs) for significant decisions
- [ ] Runbook for common operational tasks
- [ ] On-call rotation and escalation path defined
- [ ] Post-mortem process for production incidents
- [ ] Technical debt tracked (backlog, not ignored)
- [ ] API changelog maintained for external consumers

---

## Pre-Production Release Checklist

- [ ] All automated tests pass in CI
- [ ] Security scan (OWASP, SonarQube) passed
- [ ] Performance tested against production-like load
- [ ] Database migration reviewed (backward-compatible, tested on staging)
- [ ] Rollback plan documented (can we roll back? In how many minutes?)
- [ ] Feature flag configured (if gradual rollout needed)
- [ ] Monitoring dashboards + alerts ready for the new feature
- [ ] Team notified of deployment window
- [ ] On-call engineer designated for immediate post-deploy monitoring
- [ ] Canary deployment if significant change (route 5% traffic first)

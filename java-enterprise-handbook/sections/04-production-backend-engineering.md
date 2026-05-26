# Section 4: Production Backend Engineering

> **The Real World:** Knowing Spring Boot syntax gets you an interview. Knowing how to build systems that handle 100k RPS with 99.9% availability, survive partial failures, and can be debugged at 3 AM gets you the senior/staff role at Stripe, Goldman Sachs, or Google.

---

## 4.1 Microservices Architecture — Enterprise Reality

### From Monolith to Microservices

```
Monolith:
┌──────────────────────────────────────────────────────┐
│  UserService │ PaymentService │ NotificationService   │
│  OrderService│ ReportService  │ AccountService        │
└──────────────────────────────────────────────────────┘
          Single JVM process, single deployment

Microservices:
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ UserService  │  │PaymentService│  │NotificationService│
│  :8081       │  │  :8082       │  │  :8083            │
└──────────────┘  └──────────────┘  └──────────────────┘
  Independent deploy, independent scale, independent failure
```

### Service Decomposition — When to Split

**Good split criteria:**
- Independent scalability requirements (payment service needs 10x more CPU than user service)
- Independent deployment frequency (notifications deploy daily, core banking weekly)
- Different team ownership
- Different compliance/security boundaries (PCI scope isolation)

**Premature decomposition problems:**
- Distributed transaction complexity
- Network latency on what was method calls
- Operational overhead of 50 services
- Service-to-service versioning hell

**Bank reality:** Most enterprise Java shops run large "macro-services" (5-15 bounded contexts), not 100s of nano-services.

---

## 4.2 API Gateway Pattern

```
                    ┌─────────────────────────────────────────┐
Internet ──────────▶│           API Gateway                   │
                    │  - Rate limiting                        │
                    │  - Authentication (JWT validation)      │
                    │  - Request routing                      │
                    │  - SSL termination                      │
                    │  - Request/response transformation      │
                    │  - Logging / Tracing                    │
                    └─────────────────┬───────────────────────┘
                                      │
              ┌───────────────────────┼──────────────────────┐
              ▼                       ▼                       ▼
     ┌──────────────┐      ┌──────────────────┐    ┌──────────────────┐
     │ UserService  │      │  PaymentService  │    │  AccountService  │
     └──────────────┘      └──────────────────┘    └──────────────────┘
```

### Spring Cloud Gateway Configuration

```java
@Configuration
public class GatewayConfig {

    @Bean
    public RouteLocator routeLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("payment-service", r -> r
                .path("/api/v1/payments/**")
                .filters(f -> f
                    .stripPrefix(2)
                    .addRequestHeader("X-Internal-Source", "gateway")
                    .retry(retryConfig -> retryConfig
                        .setRetries(3)
                        .setStatuses(HttpStatus.SERVICE_UNAVAILABLE)
                        .setMethods(HttpMethod.GET))
                    .circuitBreaker(cb -> cb
                        .setName("paymentCB")
                        .setFallbackUri("forward:/fallback/payment")))
                .uri("lb://payment-service"))  // Load-balanced via service discovery
            .build();
    }
}
```

---

## 4.3 Service Discovery

```
Problem: In k8s/cloud, service IPs change. How does Service A find Service B?

Solution: Service Registry
┌────────────┐  register  ┌──────────────────┐
│PaymentSvc  │───────────▶│  Eureka / Consul  │
└────────────┘            │  (Service Registry│
┌────────────┐  register  │   - PaymentSvc    │
│AccountSvc  │───────────▶│     10.0.1.5:8082 │
└────────────┘            │   - AccountSvc    │
┌────────────┐  discover  │     10.0.1.6:8083 │
│API Gateway │◀───────────│   - UserSvc       │
│  → route   │            │     10.0.1.7:8084 │
└────────────┘            └──────────────────┘

In Kubernetes: kube-dns handles this natively
  payment-service.default.svc.cluster.local → Service IP
```

### Spring Cloud Netflix Eureka

```java
// Server
@SpringBootApplication
@EnableEurekaServer
public class DiscoveryServer { ... }

// Client (every microservice)
@SpringBootApplication
@EnableEurekaClient
public class PaymentService { ... }

# application.yml
eureka:
  client:
    service-url:
      defaultZone: http://eureka:8761/eureka
    register-with-eureka: true
    fetch-registry: true
  instance:
    prefer-ip-address: true
    health-check-url-path: /actuator/health
```

---

## 4.4 Circuit Breaker Pattern

**The Problem:** Service B is slow/failing. Service A keeps calling it. Service A's threads fill up waiting. Service A dies too. **Cascading failure.**

**The Solution:** Circuit breaker opens after N failures. Fast-fail until service recovers.

```
Circuit Breaker States:
CLOSED (normal) → calls pass through, track failures
    ↓ failure rate > threshold
OPEN (tripped) → fast fail, no calls to downstream
    ↓ after wait window
HALF-OPEN → allow test call
    ↓ test call succeeds → CLOSED
    ↓ test call fails → OPEN
```

```java
// Resilience4j — industry standard for Java
@Configuration
public class Resilience4jConfig {

    @Bean
    public CircuitBreakerConfig paymentCircuitBreakerConfig() {
        return CircuitBreakerConfig.custom()
            .failureRateThreshold(50)              // Open if 50% fail
            .slowCallRateThreshold(80)             // Open if 80% are slow
            .slowCallDurationThreshold(Duration.ofSeconds(2))
            .waitDurationInOpenState(Duration.ofSeconds(30))
            .permittedNumberOfCallsInHalfOpenState(3)
            .slidingWindowSize(10)                 // Based on last 10 calls
            .recordExceptions(IOException.class, TimeoutException.class)
            .build();
    }
}

@Service
public class PaymentGatewayClient {

    @CircuitBreaker(name = "payment-gateway", fallbackMethod = "fallbackProcess")
    @Retry(name = "payment-gateway")
    @TimeLimiter(name = "payment-gateway")
    public CompletableFuture<PaymentResult> processPayment(PaymentRequest request) {
        return CompletableFuture.supplyAsync(() ->
            httpClient.post(gatewayUrl, request, PaymentResult.class));
    }

    // Fallback — executed when circuit is open or retries exhausted
    public CompletableFuture<PaymentResult> fallbackProcess(
            PaymentRequest request, Exception e) {
        log.warn("Payment gateway unavailable, queuing for retry: {}", e.getMessage());
        // Queue to Kafka for async retry
        kafkaTemplate.send("payment.retry.queue", request);
        return CompletableFuture.completedFuture(
            PaymentResult.pending("Payment queued for processing"));
    }
}
```

---

## 4.5 Retry Mechanisms — Enterprise Patterns

```java
// Retry with exponential backoff + jitter (prevents thundering herd)
@Bean
public RetryConfig retryConfig() {
    return RetryConfig.custom()
        .maxAttempts(3)
        .waitDuration(Duration.ofMillis(500))
        .intervalFunction(IntervalFunction.ofExponentialRandomBackoff(
            500,      // initial interval ms
            2.0,      // multiplier
            0.5,      // randomization factor (jitter)
            30000     // max interval ms
        ))
        .retryExceptions(IOException.class, TimeoutException.class)
        .ignoreExceptions(BusinessValidationException.class)  // Don't retry validation errors
        .build();
}

// Spring Retry annotation approach
@Service
public class ExternalApiClient {

    @Retryable(
        value = {RestClientException.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 1000, multiplier = 2, random = true)
    )
    public ExternalResponse call(Request request) {
        return restTemplate.postForObject(url, request, ExternalResponse.class);
    }

    @Recover
    public ExternalResponse fallback(RestClientException ex, Request request) {
        // Called after all retries exhausted
        alertingService.raiseAlert("External API unavailable: " + ex.getMessage());
        throw new ExternalServiceUnavailableException(request.getId());
    }
}
```

---

## 4.6 Distributed Tracing — Observability

```
Request flow across services:

[Browser] → [API Gateway] → [User Service] → [Payment Service] → [Database]
                                     ↓
                          All share: traceId = "abc-123"
                          Each span has own: spanId

Trace: abc-123
├── Span 1: API Gateway (5ms)
├── Span 2: User Service validation (15ms)
└── Span 3: Payment Service (120ms)
    ├── Span 4: DB query (45ms)
    └── Span 5: Kafka publish (8ms)
```

```java
// Spring Boot 3 + Micrometer Tracing (replaces Sleuth)
// Auto-configured with spring-boot-starter-actuator + micrometer-tracing-bridge-otel

@Service
@Slf4j
public class PaymentService {

    private final Tracer tracer;

    public PaymentResult processPayment(PaymentRequest request) {
        // Current span auto-populated from MDC
        log.info("Processing payment amount={} currency={}", // Logs include traceId automatically
            request.getAmount(), request.getCurrency());

        Span dbSpan = tracer.nextSpan().name("db.findAccount").start();
        try (Tracer.SpanInScope ws = tracer.withSpan(dbSpan)) {
            Account account = accountRepo.findById(request.getAccountId());
            return processWithAccount(account, request);
        } finally {
            dbSpan.end();
        }
    }
}

// application.yml
management:
  tracing:
    sampling:
      probability: 0.1  # Sample 10% in production (100% in dev)
  zipkin:
    tracing:
      endpoint: http://zipkin:9411/api/v2/spans
```

---

## 4.7 Logging — Production Standards

```java
// Structured logging with SLF4J + Logback
// ALWAYS use parameterized logging — NEVER string concatenation
log.info("Payment processed: amount={} currency={} accountId={}",
    amount, currency, accountId);
// NOT: log.info("Payment processed: amount=" + amount + "...");

// MDC (Mapped Diagnostic Context) — correlate logs across calls
// Set at request entry point (filter/interceptor)
MDC.put("traceId", request.getHeader("X-Trace-ID"));
MDC.put("userId", authentication.getName());
MDC.put("requestId", UUID.randomUUID().toString());
// MDC values appear in every log line for this thread
// MUST clear after request: MDC.clear() in finally block

// Logging levels — production strategy
// ERROR: System errors that need immediate attention (PagerDuty alert)
// WARN:  Unexpected but handled (retry, fallback activated)
// INFO:  Business events (payment created, order completed)
// DEBUG: Technical details (turned off in production)
// TRACE: Very detailed (never in production)
```

### Logback Production Configuration

```xml
<!-- logback-spring.xml -->
<configuration>
    <springProfile name="prod">
        <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
            <encoder class="net.logstash.logback.encoder.LogstashEncoder">
                <!-- JSON output for log aggregation (ELK/Splunk/Datadog) -->
                <includeMdcKeyName>traceId</includeMdcKeyName>
                <includeMdcKeyName>userId</includeMdcKeyName>
                <includeMdcKeyName>requestId</includeMdcKeyName>
            </encoder>
        </appender>

        <root level="INFO">
            <appender-ref ref="STDOUT"/>
        </root>

        <!-- Reduce Spring framework noise -->
        <logger name="org.springframework" level="WARN"/>
        <logger name="org.hibernate" level="WARN"/>
        <!-- Your app at INFO/DEBUG as needed -->
        <logger name="com.bank.payment" level="INFO"/>
    </springProfile>
</configuration>
```

---

## 4.8 Monitoring and Observability — Metrics

### Spring Actuator + Micrometer + Prometheus

```java
// Auto-configured metrics with Spring Boot Actuator

// Custom business metrics
@Service
public class PaymentMetricsService {

    private final MeterRegistry meterRegistry;
    private final Counter paymentSuccessCounter;
    private final Counter paymentFailureCounter;
    private final Timer paymentProcessingTimer;
    private final Gauge activePaymentsGauge;

    public PaymentMetricsService(MeterRegistry meterRegistry,
                                  PaymentRepository repo) {
        this.meterRegistry = meterRegistry;

        this.paymentSuccessCounter = Counter.builder("payment.processed")
            .description("Number of successfully processed payments")
            .tag("status", "success")
            .register(meterRegistry);

        this.paymentFailureCounter = Counter.builder("payment.processed")
            .tag("status", "failure")
            .register(meterRegistry);

        this.paymentProcessingTimer = Timer.builder("payment.processing.duration")
            .description("Time to process a payment")
            .publishPercentiles(0.5, 0.95, 0.99)  // p50, p95, p99 latencies
            .register(meterRegistry);

        // Gauge reads live value each time Prometheus scrapes
        Gauge.builder("payment.pending.count", repo, PaymentRepository::countPending)
            .description("Number of pending payments")
            .register(meterRegistry);
    }

    public void recordPayment(BigDecimal amount, Duration duration, boolean success) {
        paymentProcessingTimer.record(duration);
        if (success) paymentSuccessCounter.increment();
        else paymentFailureCounter.increment();

        meterRegistry.summary("payment.amount.distribution")
            .record(amount.doubleValue());
    }
}
```

### Health Checks — Production-Grade

```java
@Component
public class PaymentGatewayHealthIndicator implements HealthIndicator {

    @Override
    public Health health() {
        try {
            ResponseEntity<String> response = restTemplate
                .getForEntity(gatewayUrl + "/health", String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                return Health.up()
                    .withDetail("gateway", "available")
                    .withDetail("responseTime", measureLatency())
                    .build();
            } else {
                return Health.down()
                    .withDetail("status", response.getStatusCode())
                    .build();
            }
        } catch (Exception e) {
            return Health.down()
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}

# application.yml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus,loggers
  endpoint:
    health:
      show-details: when_authorized
      probes:
        enabled: true  # /health/liveness, /health/readiness for k8s
```

---

## 4.9 Rate Limiting

```java
// Bucket4j — token bucket algorithm
@Configuration
public class RateLimitConfig {

    @Bean
    public Map<String, Bucket> rateLimiters() {
        Map<String, Bucket> buckets = new ConcurrentHashMap<>();
        return buckets;
    }
}

@Component
public class RateLimitFilter extends OncePerRequestFilter {

    private final Map<String, Bucket> rateLimiters;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws IOException, ServletException {
        String clientId = extractClientId(request);

        Bucket bucket = rateLimiters.computeIfAbsent(clientId, this::createBucket);

        ConsumptionProbe probe = bucket.tryConsumeAndReturnRemaining(1);
        if (probe.isConsumed()) {
            response.setHeader("X-Rate-Limit-Remaining",
                String.valueOf(probe.getRemainingTokens()));
            chain.doFilter(request, response);
        } else {
            long retryAfterSeconds = TimeUnit.NANOSECONDS.toSeconds(
                probe.getNanosToWaitForRefill());
            response.setHeader("Retry-After", String.valueOf(retryAfterSeconds));
            response.setHeader("X-Rate-Limit-Remaining", "0");
            response.sendError(HttpStatus.TOO_MANY_REQUESTS.value(),
                "Rate limit exceeded");
        }
    }

    private Bucket createBucket(String clientId) {
        return Bucket.builder()
            .addLimit(Bandwidth.classic(100, Refill.intervally(100, Duration.ofMinutes(1))))
            .build();
    }
}
```

---

## 4.10 Idempotency — Critical for Financial Systems

```java
// Idempotency ensures duplicate requests have no side effects
// Essential for: payment APIs, order creation, booking systems

@Service
@Transactional
public class IdempotentPaymentService {

    private final PaymentRepository paymentRepo;
    private final IdempotencyKeyRepository idempotencyRepo;

    public PaymentResponse createPayment(CreatePaymentRequest request,
                                          String idempotencyKey) {
        // Check if we've processed this request before
        Optional<IdempotencyRecord> existing =
            idempotencyRepo.findByKey(idempotencyKey);

        if (existing.isPresent()) {
            IdempotencyRecord record = existing.get();
            if (record.isCompleted()) {
                // Return cached response — safe to repeat
                return objectMapper.readValue(record.getResponse(), PaymentResponse.class);
            } else if (record.isProcessing()) {
                throw new ConflictException("Payment is already being processed");
            }
        }

        // Lock the idempotency key (prevent concurrent duplicate requests)
        idempotencyRepo.save(new IdempotencyRecord(idempotencyKey, "PROCESSING"));

        try {
            PaymentResponse response = processPaymentInternal(request);
            // Save response for future duplicate requests
            idempotencyRepo.updateCompleted(idempotencyKey,
                objectMapper.writeValueAsString(response));
            return response;
        } catch (Exception e) {
            idempotencyRepo.updateFailed(idempotencyKey);
            throw e;
        }
    }
}
```

---

## 4.11 Event-Driven Architecture with Spring

```java
// Spring Events — within single application
@Service
public class OrderService {

    private final ApplicationEventPublisher publisher;

    public Order createOrder(CreateOrderRequest request) {
        Order order = orderRepo.save(new Order(request));
        // Publish event — other services within same app react
        publisher.publishEvent(new OrderCreatedEvent(order));
        return order;
    }
}

@Component
public class NotificationHandler {

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    // AFTER_COMMIT — only notify if order transaction actually committed
    public void onOrderCreated(OrderCreatedEvent event) {
        emailService.sendOrderConfirmation(event.getOrder());
    }
}

// Kafka-based cross-service events (see Section 6 for deep dive)
@Service
public class PaymentEventPublisher {

    private final KafkaTemplate<String, PaymentEvent> kafkaTemplate;

    public void publishPaymentCompleted(Payment payment) {
        PaymentEvent event = PaymentEvent.completed(payment);
        kafkaTemplate.send("payments.completed", payment.getId(), event)
            .addCallback(
                result -> log.info("Event published: {}", payment.getId()),
                failure -> {
                    log.error("Failed to publish event", failure);
                    // Outbox pattern: save to outbox table, retry via scheduler
                    outboxRepo.save(new OutboxMessage(event));
                }
            );
    }
}
```

---

## Section Summary: Production Readiness Checklist

**Every production Spring service should have:**

- [ ] Health endpoints (liveness + readiness probes)
- [ ] Structured JSON logging with MDC (traceId, requestId, userId)
- [ ] Distributed tracing (Micrometer/OpenTelemetry)
- [ ] Business metrics (custom Micrometer counters/timers/gauges)
- [ ] Circuit breakers on all external service calls
- [ ] Retry with exponential backoff + jitter
- [ ] Rate limiting on public endpoints
- [ ] Idempotency for mutating operations
- [ ] Graceful shutdown (spring.lifecycle.timeout-per-shutdown-phase)
- [ ] Thread pool configuration (don't use defaults in production)
- [ ] Connection pool sizing (HikariCP, not defaults)
- [ ] Timeout configuration on all HTTP clients
- [ ] Sensitive config externalized (never in code or git)
- [ ] Security headers (Content-Security-Policy, HSTS, etc.)
- [ ] Input validation on all API endpoints
- [ ] Audit logging for security-sensitive operations

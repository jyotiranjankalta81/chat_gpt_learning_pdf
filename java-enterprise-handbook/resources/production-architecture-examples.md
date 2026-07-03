# Production Architecture Examples
## Real-World Enterprise Java System Designs

---

## Example 1: Banking Payment Processing Platform

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Banking Payment Platform                               │
│                                                                               │
│  External Channels                                                            │
│  Mobile App ──┐                                                               │
│  Web App   ──►│                                                               │
│  Partner API──┘                                                               │
│               ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                     API Gateway (Spring Cloud Gateway)                  │ │
│  │  • JWT validation     • Rate limiting       • SSL termination           │ │
│  │  • Request routing    • Audit logging        • DDoS protection          │ │
│  └───────────────────────────────────┬─────────────────────────────────────┘ │
│                                       │                                       │
│  ┌────────────────────────────────────┼─────────────────────────────────────┐ │
│  │ Core Services                      │                                     │ │
│  │  ┌──────────────┐ ┌───────────────┐│ ┌──────────────┐ ┌──────────────┐  │ │
│  │  │ Auth Service │ │Payment Service││ │Account Svc   │ │Transfer Svc  │  │ │
│  │  │ (JWT/OAuth2) │ │               ││ │              │ │(SWIFT/ACH)   │  │ │
│  │  └──────┬───────┘ └───────┬───────┘│ └──────┬───────┘ └──────┬───────┘  │ │
│  └─────────┼─────────────────┼────────┼────────┼────────────────┼───────────┘ │
│             │                 │        │        │                │             │
│  ┌──────────┼─────────────────┼────────┼────────┼────────────────┼───────────┐ │
│  │          ▼                 ▼        ▼        ▼                ▼           │ │
│  │                     Kafka Event Bus                                       │ │
│  │  Topics: payment.initiated  payment.completed  payment.failed             │ │
│  │          account.updated    transfer.initiated  fraud.alert               │ │
│  └──────────────────────────────┬────────────────────────────────────────────┘ │
│                                  │                                              │
│  ┌───────────────────────────────┼──────────────────────────────────────────┐  │
│  │ Downstream Services           │                                          │  │
│  │  ┌────────────┐ ┌─────────────▼┐ ┌──────────────┐ ┌──────────────────┐ │  │
│  │  │Notification│ │Fraud Engine  │ │ Audit Service│ │  Reporting Svc   │ │  │
│  │  │Service     │ │(ML scoring)  │ │ (immutable   │ │  (Elasticsearch) │ │  │
│  │  └────────────┘ └─────────────┘ │  ledger)     │ └──────────────────┘ │  │
│  └────────────────────────────────┴──────────────────────────────────────────┘  │
│                                                                               │
│  Data Layer                                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ PostgreSQL   │ │    Redis     │ │Elasticsearch │ │   S3 / Object    │   │
│  │ (Primary +   │ │ (Cache,Rate  │ │ (Reporting,  │ │   Store          │   │
│  │  Replicas)   │ │  Limit,      │ │  Search)     │ │ (Statements,     │   │
│  │              │ │  Sessions)   │ │              │ │  Documents)      │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Details

**Payment Service — Core Domain**
```
Tech: Spring Boot 3.2, Java 21
Database: PostgreSQL (primary) + read replica
Cache: Redis (idempotency keys, 24h TTL; rate limits)
Kafka: Producer (payment.initiated, payment.failed)
Resilience: Circuit breaker on external gateway, retry on transient failures
Throughput: 50,000 TPS peak
Latency: P99 < 500ms
```

**Fraud Engine — ML-Powered**
```
Tech: Spring Boot + Python microservice (via gRPC)
Input: Kafka consumer (payment.initiated)
Features: velocity, device fingerprint, behavioral anomaly
Output: APPROVE / REVIEW / DECLINE with score
Latency budget: 100ms synchronous (real-time blocking) or 500ms async
```

---

## Example 2: Microservices Communication Patterns

### Synchronous vs Asynchronous Decision Matrix

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Communication Pattern Decision                         │
│                                                                           │
│  Query (GET data)                   → REST/gRPC (synchronous)            │
│  Command needing immediate response → REST/gRPC (synchronous)            │
│  Command with fire-and-forget       → Kafka (asynchronous)               │
│  Cross-domain event propagation     → Kafka (asynchronous)               │
│  Real-time streaming                → Kafka / WebSocket                  │
│  Bulk data transfer                 → Batch job / S3                     │
│                                                                           │
│  Decision factors:                                                        │
│  • Does caller need immediate result? → Sync                             │
│  • Can caller proceed without result? → Async                            │
│  • Multiple consumers of event?     → Kafka (fan-out)                   │
│  • Need event replay capability?    → Kafka                              │
│  • Need strong consistency?         → Sync (same DB transaction ideal)  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Service Mesh Configuration (Istio)

```yaml
# Service-to-service retry policy
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: payment-service
spec:
  http:
    - route:
        - destination:
            host: payment-service
      timeout: 10s
      retries:
        attempts: 3
        perTryTimeout: 3s
        retryOn: gateway-error,connect-failure,retriable-4xx
```

---

## Example 3: Event-Driven Order Processing

### Choreography Saga

```
Order Service    Payment Service    Inventory Service    Notification Service
     │                  │                   │                     │
  Create Order           │                   │                     │
  Publish:               │                   │                     │
  order.created ─────────►                   │                     │
                 Process Payment             │                     │
                 Publish:                   │                     │
                 payment.completed ──────────►                     │
                                   Reserve Stock                   │
                                   Publish:                        │
                                   stock.reserved ────────────────►
                                                          Send Confirmation
                                                          Email/SMS

Rollback (if stock.reserved fails):
  stock.reservation_failed ──────────►
                              Refund Payment
                              Publish:
                              payment.refunded ──────────────────►
                                                        Send Cancellation
                                                        Notification
```

### Spring Implementation

```java
// Each service listens to relevant events
@Component
public class PaymentSagaParticipant {

    @KafkaListener(topics = "order.created")
    @Transactional
    public void onOrderCreated(OrderCreatedEvent event) {
        try {
            PaymentResult result = paymentGateway.charge(
                event.getCustomerId(),
                event.getTotalAmount(),
                event.getOrderId()  // Idempotency key
            );

            if (result.isSuccessful()) {
                kafkaTemplate.send("payment.completed",
                    new PaymentCompletedEvent(event.getOrderId(), result.getTransactionId()));
            } else {
                kafkaTemplate.send("payment.failed",
                    new PaymentFailedEvent(event.getOrderId(), result.getDeclineReason()));
            }
        } catch (Exception e) {
            // Compensating action: publish failure event
            kafkaTemplate.send("payment.failed",
                new PaymentFailedEvent(event.getOrderId(), "INTERNAL_ERROR"));
        }
    }
}
```

---

## Example 4: High-Availability Architecture

### Multi-Region Active-Active

```
                    Global Load Balancer (Route53 / Cloudflare)
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
          US-EAST-1    EU-WEST-1   AP-SOUTHEAST-1
          │               │               │
    ┌─────┴─────┐   ┌─────┴─────┐   ┌────┴──────┐
    │  AZ-A     │   │  AZ-A     │   │  AZ-A     │
    │  AZ-B     │   │  AZ-B     │   │  AZ-B     │
    │  AZ-C     │   │  AZ-C     │   │  AZ-C     │
    └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
          │               │               │
    ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
    │ PostgreSQL│   │ PostgreSQL│   │ PostgreSQL│
    │  Primary  │   │  Primary  │   │  Primary  │
    │ (writes)  │◄──┤ (replica) │   │ (replica) │
    └───────────┘   └───────────┘   └───────────┘
    Kafka region     Kafka region    Kafka region
    + MirrorMaker2   + MirrorMaker2  + MirrorMaker2
    (cross-region replication)
```

**Java/Spring considerations for multi-region:**
```yaml
# application.yml — region-aware configuration
spring:
  datasource:
    # Writes to primary (current region primary)
    url: ${DB_PRIMARY_URL}
  # Reads from replica (local region for latency)
  jpa:
    properties:
      hibernate:
        read-only.url: ${DB_REPLICA_URL}

# Kafka: produce to local cluster, MirrorMaker2 replicates cross-region
spring:
  kafka:
    bootstrap-servers: ${KAFKA_LOCAL_BOOTSTRAP_SERVERS}
    consumer:
      group-id: ${SERVICE_NAME}-${AWS_REGION}  # Region-specific consumer group
```

---

## Example 5: CQRS + Event Sourcing for Account Management

### Data Flow

```
Command Flow (Write):
CreateAccountCommand → AccountCommandHandler → Account.openAccount()
                                             → AccountOpenedEvent → EventStore
                                             → EventPublisher → Kafka

Query Flow (Read):
GET /accounts/{id} → AccountQueryHandler → AccountReadModel (Elasticsearch)
                                         ← Populated by: AccountProjector (Kafka consumer)

AccountProjector (Kafka consumer):
  AccountOpenedEvent → create AccountDocument in Elasticsearch
  MoneyDepositedEvent → update balance in AccountDocument
  AccountFrozenEvent → update status in AccountDocument
```

### Event Store Schema

```sql
CREATE TABLE event_store (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_id   VARCHAR(100) NOT NULL,   -- e.g., "account-ACC-123"
    stream_type VARCHAR(50) NOT NULL,    -- e.g., "Account"
    version     BIGINT NOT NULL,
    event_type  VARCHAR(100) NOT NULL,   -- "AccountOpened", "MoneyDeposited"
    payload     JSONB NOT NULL,
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (stream_id, version),         -- Optimistic concurrency
    CHECK (version >= 0)
);

CREATE INDEX idx_event_store_stream ON event_store(stream_id, version);
CREATE INDEX idx_event_store_type_time ON event_store(event_type, created_at);
```

---

## Example 6: Real-Time Risk Management System

### Architecture for Financial Risk (Sub-100ms requirement)

```
Market Data Feed (WebSocket)
    │
    ▼
Market Data Normalizer (Spring WebFlux, Reactor)
    │
    ▼
Kafka (market.prices) ──────────────────────────────────────►
                                                              Risk Calculator
                                                              (Java, 20 threads)
    Positions DB ──────────────────────────────────────────► │
    (Redis - sub-ms reads)                                    │
                                                              ▼
                                                        Risk Metrics
                                                        (VaR, PnL, Greeks)
                                                              │
                                                              ▼
                                                        Risk Aggregator
                                                        → Kafka: risk.updates
                                                        → WebSocket: trader dashboards
                                                        → Alert: limit breaches
```

**Performance techniques for sub-100ms risk:**
```java
// Pre-computed position cache (Redis, updated by position service)
// Loaded at startup into JVM heap for zero-latency reads
@Service
public class PositionCache {
    private final ConcurrentHashMap<String, Position> positions =
        new ConcurrentHashMap<>(100_000);

    @PostConstruct
    public void loadFromRedis() {
        // Load all active positions into memory at startup
        redisTemplate.opsForHash().entries("positions:active")
            .forEach((k, v) -> positions.put((String) k, (Position) v));
    }

    // O(1) lookup — no network round trip
    public Position get(String instrumentId) {
        return positions.get(instrumentId);
    }
}

// Parallel risk computation using ForkJoinPool
public RiskReport computePortfolioRisk(List<Position> positions) {
    ForkJoinPool pool = new ForkJoinPool(Runtime.getRuntime().availableProcessors());
    return pool.invoke(new RiskComputationTask(positions, 0, positions.size()));
}
```

---

*These architecture examples represent patterns used at global banks, fintech companies, and large-scale platforms. Understanding them deeply and being able to discuss trade-offs, scaling strategies, and failure modes is what separates senior from staff-level engineers.*

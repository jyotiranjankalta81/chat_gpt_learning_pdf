# Section 15: Practical Learning — Projects, Architecture & Anti-Patterns

> **Build to Understand:** Reading is passive. Building is active. This section gives you a curated set of projects that, when built, will cement every concept in this handbook. Each project is sized for 2-8 weeks and mirrors real enterprise work.

---

## 15.1 Learning Project Portfolio

### Project 1: Banking API (Weeks 1-4) — Foundation

**Purpose:** Learn Spring Boot, JPA, REST API design, security, migrations  
**Stack:** Spring Boot, PostgreSQL, Spring Security (JWT), Flyway, JUnit 5

```
bank-api/
├── src/main/java/com/bank/
│   ├── BankApplication.java
│   ├── config/
│   │   ├── SecurityConfig.java
│   │   └── SwaggerConfig.java
│   ├── account/
│   │   ├── Account.java          (Entity)
│   │   ├── AccountRepository.java
│   │   ├── AccountService.java
│   │   └── AccountController.java
│   ├── payment/
│   │   ├── Payment.java
│   │   ├── PaymentRepository.java
│   │   ├── PaymentService.java
│   │   └── PaymentController.java
│   ├── auth/
│   │   ├── AuthService.java
│   │   └── JwtService.java
│   └── shared/
│       ├── exception/
│       ├── dto/
│       └── config/
├── src/main/resources/
│   ├── application.yml
│   ├── application-test.yml
│   └── db/migration/
│       ├── V1__create_accounts.sql
│       ├── V2__create_payments.sql
│       └── V3__add_indexes.sql
└── src/test/
    ├── unit/           (Mockito unit tests)
    └── integration/    (Testcontainers + @SpringBootTest)
```

**What you learn:**
- Spring Boot project structure
- JPA entity design, relationships, migrations
- Spring Security JWT authentication
- REST API design: pagination, sorting, filtering
- Unit testing with Mockito, integration testing with Testcontainers
- BigDecimal for monetary values, transaction management

---

### Project 2: Event-Driven Payment Platform (Weeks 5-8) — Intermediate

**Purpose:** Learn Kafka, microservices, circuit breakers, async processing  
**Stack:** Spring Boot × 3 services, Kafka, Redis, PostgreSQL, Resilience4j

```
payment-platform/
├── payment-service/          ← Initiates payments
├── notification-service/     ← Sends emails/SMS
├── fraud-detection-service/  ← Kafka consumer, ML scoring
├── docker-compose.yml        ← Local environment
└── k8s/                      ← Kubernetes manifests
```

**What you learn:**
- Multi-service communication via Kafka
- Saga pattern (payment saga across 3 services)
- Idempotency (deduplication across services)
- Circuit breaker + retry (Resilience4j)
- Redis for rate limiting and caching
- Docker Compose for local development
- Kubernetes deployment basics

**Kafka topics to implement:**
```
payment.initiated    → Fraud service evaluates
payment.approved     → Payment service debits
payment.completed    → Notification service sends
payment.failed       → Saga compensates
payment.retry.queue  → Retry failed events
payment.DLT          → Dead letter topic
```

---

### Project 3: CQRS Event Store (Weeks 9-12) — Advanced

**Purpose:** Learn event sourcing, CQRS, projections, temporal queries  
**Stack:** Spring Boot, PostgreSQL (event store), Elasticsearch (read model), Kafka

```java
// Account aggregate with full event sourcing
public class Account {
    private UUID id;
    private BigDecimal balance;
    private AccountStatus status;
    private long version;

    // Events: AccountOpened, MoneyDeposited, MoneyWithdrawn,
    //         AccountFrozen, AccountClosed

    // Commands: OpenAccount, DepositMoney, WithdrawMoney
    // Projections: AccountBalanceView, AccountHistoryView
}
```

**What you learn:**
- Event sourcing from scratch (no framework)
- CQRS: separate command and query models
- Elasticsearch for read projections
- Temporal queries: "what was the balance on Jan 15?"
- Snapshot optimization for long event streams
- Event schema versioning

---

### Project 4: Production-Ready Microservice Template (Ongoing)

**Purpose:** Reference implementation of enterprise patterns  
**Stack:** Spring Boot, comprehensive observability

```java
// This is your "golden template" — production-ready from day one

payment-service-template/
├── src/main/java/com/template/
│   ├── config/
│   │   ├── SecurityConfig.java         (JWT + OAuth2)
│   │   ├── CacheConfig.java            (Redis + Caffeine)
│   │   ├── KafkaConfig.java
│   │   ├── DataSourceConfig.java       (HikariCP tuning)
│   │   ├── ActuatorConfig.java         (health, metrics)
│   │   └── AsyncConfig.java            (thread pool)
│   ├── common/
│   │   ├── exception/                  (exception hierarchy)
│   │   ├── logging/                    (MDC filter, audit aspect)
│   │   ├── metrics/                    (custom Micrometer metrics)
│   │   ├── resilience/                 (CB, retry, rate limit)
│   │   └── validation/                 (custom validators)
│   └── domain/
│       └── payment/
│           ├── api/                    (controller, DTOs)
│           ├── domain/                 (entities, events)
│           ├── service/                (business logic)
│           └── infrastructure/        (repo, kafka, external clients)
├── src/test/
│   ├── architecture/                   (ArchUnit architecture tests)
│   ├── unit/
│   ├── integration/                    (Testcontainers)
│   └── contract/                       (Pact consumer-driven tests)
├── k8s/                               (complete k8s manifests)
├── helm/                              (Helm chart)
├── .github/workflows/                 (CI/CD pipelines)
└── docker-compose.yml
```

---

## 15.2 Production-Ready Project Structure

```
src/
├── main/
│   ├── java/com/company/service/
│   │   ├── Application.java              ← @SpringBootApplication entry
│   │   │
│   │   ├── api/                          ← HTTP layer
│   │   │   ├── controller/               ← @RestController
│   │   │   ├── dto/                      ← Request/Response records
│   │   │   ├── filter/                   ← Servlet filters (logging, rate limit)
│   │   │   └── interceptor/              ← Spring interceptors
│   │   │
│   │   ├── domain/                       ← Business logic (pure Java, no Spring)
│   │   │   ├── model/                    ← Domain entities, value objects
│   │   │   ├── service/                  ← Domain services
│   │   │   ├── event/                    ← Domain events
│   │   │   ├── repository/               ← Repository interfaces (ports)
│   │   │   └── exception/               ← Domain exceptions
│   │   │
│   │   ├── infrastructure/               ← Adapters for external systems
│   │   │   ├── persistence/              ← JPA entities, repos (adapters)
│   │   │   │   ├── entity/
│   │   │   │   └── repository/
│   │   │   ├── kafka/                    ← Producers, consumers
│   │   │   ├── redis/                    ← Cache, rate limiter, locks
│   │   │   └── client/                   ← External HTTP clients
│   │   │
│   │   └── config/                       ← Spring configuration
│   │       ├── SecurityConfig.java
│   │       ├── KafkaConfig.java
│   │       └── CacheConfig.java
│   │
│   └── resources/
│       ├── application.yml
│       ├── application-local.yml
│       ├── application-prod.yml
│       └── db/migration/
│
└── test/
    ├── java/com/company/service/
    │   ├── architecture/                 ← ArchUnit layer tests
    │   ├── domain/                       ← Pure unit tests (no Spring)
    │   ├── api/                          ← MockMvc tests
    │   ├── integration/                  ← @SpringBootTest + Testcontainers
    │   └── contract/                     ← Pact tests
    └── resources/
        └── application-test.yml
```

---

## 15.3 Anti-Patterns — Learn to Recognize and Avoid

### Spring Anti-Patterns

```java
// 1. God Service — one service doing everything
@Service
public class PaymentService {
    // 5000 lines, handles: payment, refund, dispute, reporting,
    // notification, fraud check, ledger, audit...
    // Fix: Split by bounded context
}

// 2. Anemic Domain Model — entities with no behavior
@Entity
public class Order {
    private BigDecimal total;
    // Just getters/setters — no business logic
    // Fix: Move business logic INTO the entity
    public void addItem(OrderItem item) {
        // Validate, add, recalculate total here
    }
}

// 3. Constructor injection avoided in favor of field injection
@Service
public class BadService {
    @Autowired
    private SomeDependency dep;  // Cannot mock without Spring context
    // Fix: Constructor injection
}

// 4. @Transactional on every method (lazy safety blanket)
@Service
@Transactional  // On CLASS — wraps every method including read-only queries
public class ServiceWithUnnecessaryTransactions {
    // Fix: @Transactional(readOnly = true) on reads, @Transactional on writes
}

// 5. Catching Exception everywhere
try { ... }
catch (Exception e) {
    log.error("Error", e);
    // returns null or default — caller has no idea what happened
}
// Fix: let domain exceptions propagate, handle at boundary (@ControllerAdvice)
```

### Database Anti-Patterns

```java
// 1. N+1 queries
List<Order> orders = orderRepo.findAll();
for (Order order : orders) {
    // Each call fires a SQL query!
    String customerName = order.getCustomer().getName();
}
// Fix: JOIN FETCH or @EntityGraph

// 2. Loading entire table
List<User> allUsers = userRepo.findAll();  // 10 million users → OOM
// Fix: Pageable or streaming

// 3. hibernate.ddl-auto = create-drop in production
# application-prod.yml
spring.jpa.hibernate.ddl-auto: validate  # ALWAYS validate in production

// 4. Missing transaction on multi-step operations
public void transfer(from, to, amount) {
    account1.debit(amount);   // Committed
    // CRASH HERE → money lost!
    account2.credit(amount);  // Never runs
}
// Fix: @Transactional on the whole method

// 5. Synchronous Hibernate load in loop (variant of N+1)
for (String id : accountIds) {
    Account a = accountRepo.findById(id).get();  // N queries!
}
// Fix: accountRepo.findAllById(accountIds)  → single IN query
```

### Concurrency Anti-Patterns

```java
// 1. Unsynchronized shared state
@Service  // Singleton — shared by all requests!
public class StatefulService {
    private Map<String, Object> requestState = new HashMap<>();  // NOT thread-safe
}
// Fix: ConcurrentHashMap, or better: don't store per-request state in singleton

// 2. Incorrect double-checked locking (pre-Java 5)
if (instance == null) {
    synchronized (this) {
        if (instance == null) {
            instance = new Expensive();  // Without volatile, broken!
        }
    }
}
// Fix: volatile instance field, or use enum singleton, or Spring singleton bean

// 3. Blocking in reactive pipeline
Mono.fromCallable(() -> blockingDatabaseCall())  // Blocks reactor thread!
// Fix: subscribeOn(Schedulers.boundedElastic())  or use non-blocking R2DBC

// 4. Thread pool starvation
// All threads waiting for another thread pool to respond → deadlock
@Async("poolA")
public void taskA() {
    poolBService.taskB().get();  // Waits for poolB
}
@Async("poolA")  // SAME pool — poolB is also poolA, all threads waiting for each other
public void taskB() { }
// Fix: Use separate thread pools for dependent tasks
```

---

## 15.4 Debugging Exercises

### Exercise 1: Find the N+1 Query

```
Given: User complaints that the "transactions" page is slow
Given: The following service code:

List<Account> accounts = accountRepo.findByUserId(userId);
for (Account account : accounts) {
    List<Transaction> txns = account.getTransactions();  // ?
    txns.forEach(t -> dashboard.add(t.getSummary()));
}

Task: 
1. Enable SQL logging: spring.jpa.show-sql=true
2. Count the queries executed
3. Fix the N+1 problem
4. Verify query count reduced to 1
```

### Exercise 2: Diagnose Thread Pool Exhaustion

```
Given: API returns 503 intermittently under load
Given: Log shows: "Unable to acquire JDBC Connection"

Task:
1. Write HikariCP metrics monitoring code
2. Simulate the problem with high concurrency test
3. Add leak detection: hikari.leak-detection-threshold=2000
4. Find the connection leak (a missing try-with-resources)
5. Fix it and verify the issue is resolved
```

### Exercise 3: Fix a Race Condition

```java
// Given: This service intermittently creates duplicate promotions
@Service
public class PromotionService {
    public Promotion createFirstTimePromotion(String userId) {
        if (promotionRepo.existsByUserId(userId)) {
            throw new DuplicatePromotionException();
        }
        // Concurrent requests BOTH pass the check above!
        return promotionRepo.save(new Promotion(userId));
    }
}

// Task:
// 1. Write a concurrent test that reproduces the duplicate creation
// 2. Fix using database unique constraint + exception handling
// 3. Alternative: fix using Redis distributed lock
// 4. Compare the trade-offs of both approaches
```

---

## 15.5 Key Libraries to Know

```xml
<!-- Spring Boot Starters (know these by heart) -->
spring-boot-starter-web           <!-- REST API (Tomcat) -->
spring-boot-starter-webflux       <!-- Reactive API (Netty) -->
spring-boot-starter-data-jpa      <!-- Hibernate + Spring Data -->
spring-boot-starter-security      <!-- Spring Security -->
spring-boot-starter-actuator      <!-- Health, metrics, info -->
spring-boot-starter-validation    <!-- Bean Validation (Jakarta) -->
spring-boot-starter-cache         <!-- Caching abstraction -->
spring-boot-starter-test          <!-- JUnit 5 + Mockito + AssertJ -->

<!-- Production essentials -->
spring-kafka                      <!-- Apache Kafka -->
spring-cloud-starter-circuitbreaker-resilience4j  <!-- Circuit breaker -->
micrometer-tracing-bridge-otel    <!-- Distributed tracing -->
micrometer-registry-prometheus    <!-- Prometheus metrics -->
flyway-core                       <!-- DB migrations -->
lombok                            <!-- Reduce boilerplate -->

<!-- Testing -->
testcontainers-postgresql         <!-- Real DB in tests -->
testcontainers-kafka              <!-- Real Kafka in tests -->
rest-assured                      <!-- API integration tests -->
archunit                          <!-- Architecture tests -->

<!-- Utilities -->
jackson-databind                  <!-- JSON serialization -->
mapstruct                         <!-- DTO mapping -->
bucket4j-core                     <!-- Rate limiting -->
redisson                          <!-- Redis distributed locks -->
caffeine                          <!-- In-memory caching -->
```

---

## 15.6 6-Month Learning Schedule

```
Month 1: Java Language Mastery
  Week 1-2: Section 1 (Fundamentals) + Section 14 (Node.js mapping)
  Week 3-4: Section 2 (JVM) + Start Project 1 (Banking API)
  Daily: 2 LeetCode Easy problems

Month 2: Spring Mastery
  Week 5-6: Section 3 (Spring ecosystem) — complete Project 1
  Week 7-8: Section 5 (Databases) — add advanced DB features to Project 1
  Daily: 2 LeetCode Medium problems

Month 3: Distributed Systems
  Week 9-10: Section 6 (Kafka, distributed systems) — Start Project 2
  Week 11-12: Section 7 (Concurrency) — complete Project 2
  Daily: 2 LeetCode Medium problems

Month 4: Production Engineering
  Week 13-14: Section 4 (Production patterns) + Section 8 (Cloud/DevOps)
  Week 15-16: Section 9 (Security) + Section 10 (System Design)
  Weekly: 1 system design study

Month 5: Interview Preparation
  Week 17-18: Section 11 (Interview prep) — Start mock interviews
  Week 19-20: Section 12-13 (AI era, enterprise) — Finalize project portfolio
  Daily: 3 LeetCode problems (mix easy/medium/hard)
  Weekly: 2 mock interviews

Month 6: Mastery Sprint
  Target companies research + tailored preparation
  Weekly: 3+ mock interviews
  Build: Project 3 or 4 based on target company focus
  Contributions: Open source Spring projects
```

---

## Section Summary: Build Everything You Can

The fastest path to enterprise Java fluency is not reading — it's building. Each project forces you to confront the gaps between knowing a concept and actually implementing it.

**The learning flywheel:**
1. Read concept → understand abstractly
2. Build project → encounter real problems
3. Debug and fix → deeply understand behavior
4. Review code with experienced engineers → learn production standards
5. Teach concept to someone else → solidify understanding

**Your Node.js advantage on projects:** You'll build things that actually work quickly because the architectural patterns are familiar. Use that momentum to dive into Java-specific depth (JVM tuning, Spring AOP internals, JPA optimization) in your second pass.

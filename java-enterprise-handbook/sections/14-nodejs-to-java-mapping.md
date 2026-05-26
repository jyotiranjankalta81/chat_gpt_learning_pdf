# Section 14: Node.js → Java Complete Mapping

> **Your Bridge:** This is the most important section for your transition. Every concept you understand in Node.js maps to something in Java. Use this as your primary reference for the first 3 months — find the Node.js concept you know, learn the Java equivalent, understand the differences.

---

## 14.1 Runtime & Execution Model

| Dimension | Node.js | Java |
|-----------|---------|------|
| Runtime | V8 Engine | JVM (HotSpot/GraalVM) |
| Compilation | JIT at runtime | Bytecode → JIT (tiered C1/C2) |
| Concurrency model | Single thread + event loop | Multi-threaded (OS threads) |
| I/O model | Non-blocking (libuv) | Blocking (default) or async (NIO/WebFlux) |
| Memory management | V8 GC | Pluggable GC (G1, ZGC, etc.) |
| Warm-up | Fast | JIT warm-up (30-60s) |
| Startup time | ~100-500ms | 3-8s (JVM) / 50-200ms (Native) |
| Memory footprint | 50-150MB | 200-500MB (JVM overhead) |

### Concurrency Deep Comparison

```javascript
// Node.js: single thread, non-blocking I/O
// 1000 requests handled concurrently by one thread via event loop
app.get('/payments', async (req, res) => {
    const payments = await db.find({});  // Non-blocking — event loop continues
    res.json(payments);
});
```

```java
// Java: thread per request (Tomcat default: 200 threads)
// Each request blocks its thread while waiting for DB
@GetMapping("/payments")
public List<Payment> getPayments() {
    return paymentRepo.findAll();  // Blocks thread for DB duration
}

// Java WebFlux: non-blocking like Node.js
@GetMapping("/payments")
public Flux<Payment> getPayments() {
    return paymentRepo.findAll();  // Reactive — doesn't block thread
}
```

**Implication:** In Java blocking model, 200 concurrent requests = 200 threads. In Node.js, 200 concurrent requests = 1 thread handling all I/O asynchronously.

---

## 14.2 Package Management & Build

| Dimension | Node.js | Java |
|-----------|---------|------|
| Package registry | npm / yarn registry | Maven Central / JFrog Artifactory |
| Build file | package.json | pom.xml (Maven) / build.gradle (Gradle) |
| Build tool | npm, yarn, pnpm | Maven, Gradle |
| Lock file | package-lock.json | pom.xml is deterministic (with versions) |
| Script runner | npm scripts | Maven plugins / Gradle tasks |
| Local packages | node_modules/ | ~/.m2/repository (global local cache) |

```json
// package.json (Node.js)
{
  "name": "payment-service",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.0",
    "mongoose": "^7.0.0"
  },
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  }
}
```

```xml
<!-- pom.xml (Java/Maven) -->
<project>
  <groupId>com.bank</groupId>
  <artifactId>payment-service</artifactId>
  <version>1.0.0</version>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.5</version>
  </parent>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
  </dependencies>
</project>
```

---

## 14.3 Web Framework Mapping

| Dimension | Node.js | Java |
|-----------|---------|------|
| Framework | Express/Fastify/Koa | Spring MVC/WebFlux |
| Router | express.Router() | @RequestMapping, @GetMapping |
| Middleware | app.use(middleware) | Filter, Interceptor, AOP |
| Request object | req | HttpServletRequest |
| Response object | res | HttpServletResponse |
| Body parser | body-parser | @RequestBody (auto) |
| Path variables | req.params.id | @PathVariable |
| Query params | req.query.page | @RequestParam |
| Headers | req.headers | @RequestHeader |
| Error handling | app.use(errorMiddleware) | @ControllerAdvice |

```javascript
// Express.js
const app = express();
app.use(authMiddleware);
app.use('/api/payments', paymentRouter);

const paymentRouter = express.Router();
paymentRouter.post('/', async (req, res) => {
    const { fromAccount, toAccount, amount } = req.body;
    try {
        const result = await paymentService.transfer(fromAccount, toAccount, amount);
        res.status(201).json(result);
    } catch (err) {
        next(err);
    }
});
```

```java
// Spring Boot
@RestController
@RequestMapping("/api/payments")
public class PaymentController {

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public PaymentResponse createPayment(@Valid @RequestBody PaymentRequest request) {
        return paymentService.transfer(request);
    }
}
// Auth handled by Spring Security filter (equivalent to Express middleware)
// Error handling in @ControllerAdvice (equivalent to Express error middleware)
```

---

## 14.4 Database & ORM

| Dimension | Node.js | Java |
|-----------|---------|------|
| ORM | Mongoose, TypeORM, Sequelize | Hibernate, Spring Data JPA |
| Query builder | Knex, Drizzle | QueryDSL, JPA Criteria API |
| Connection pool | pg-pool, mongoose pool | HikariCP |
| Schema | Mongoose schema, TypeORM entity | @Entity, JPA annotations |
| Migrations | Knex migrate, TypeORM migrate | Flyway, Liquibase |
| Raw SQL | pg, mysql2 | JdbcTemplate, JOOQ |

```javascript
// TypeORM (Node.js)
@Entity()
export class Payment {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ type: 'decimal', precision: 19, scale: 4 })
    amount: number;

    @Column()
    @CreateDateColumn()
    createdAt: Date;
}

// Repository
const payments = await paymentRepo.find({
    where: { status: 'PENDING', createdAt: MoreThan(cutoffDate) },
    order: { createdAt: 'DESC' },
    take: 20
});
```

```java
// Spring Data JPA (Java)
@Entity
@Table(name = "payments")
public class Payment {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, precision = 19, scale = 4)
    private BigDecimal amount;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private Instant createdAt;
}

// Repository
List<Payment> payments = paymentRepo
    .findByStatusAndCreatedAtAfter(PaymentStatus.PENDING, cutoffDate);
// OR with Pageable:
Page<Payment> page = paymentRepo.findByStatus(status,
    PageRequest.of(0, 20, Sort.by("createdAt").descending()));
```

---

## 14.5 Async & Promises → CompletableFuture

```javascript
// Node.js: async/await
async function processPayment(payment) {
    const account = await accountService.findById(payment.fromAccount);
    const fxRate = await fxService.getRate(payment.currency);
    const result = await ledger.record(payment, fxRate);
    return result;
}

// Parallel:
const [account, fxRate] = await Promise.all([
    accountService.findById(payment.fromAccount),
    fxService.getRate(payment.currency)
]);

// Error handling:
const result = await someAsyncOperation()
    .catch(err => handleError(err));
```

```java
// Java: CompletableFuture
public CompletableFuture<PaymentResult> processPayment(Payment payment) {
    return accountService.findById(payment.getFromAccount())
        .thenCombine(
            fxService.getRate(payment.getCurrency()),
            (account, fxRate) -> new ProcessingContext(account, fxRate)
        )
        .thenCompose(ctx -> ledger.record(payment, ctx.getFxRate()))
        .exceptionally(ex -> handleError(ex));
}

// Parallel:
CompletableFuture<Account> accountFuture = accountService.findById(fromId);
CompletableFuture<FxRate> rateFuture = fxService.getRate(currency);
CompletableFuture.allOf(accountFuture, rateFuture).join();
Account account = accountFuture.join();
FxRate rate = rateFuture.join();
```

---

## 14.6 Environment Config & Secrets

| Dimension | Node.js | Java |
|-----------|---------|------|
| Env vars | process.env.DB_URL | ${DB_URL} in application.yml |
| Config file | .env (dotenv) | application.yml / application.properties |
| Typed config | zod schema, joi | @ConfigurationProperties |
| Multiple environments | .env.production | application-prod.yml |
| Secrets | .env.local, AWS SSM | AWS Secrets Manager, Vault, k8s secrets |

```javascript
// Node.js .env
DB_URL=postgres://localhost:5432/mydb
JWT_SECRET=supersecret
PORT=3000

// Access:
const dbUrl = process.env.DB_URL;
```

```yaml
# application.yml (Java)
spring:
  datasource:
    url: ${DB_URL:jdbc:postgresql://localhost:5432/mydb}
    password: ${DB_PASSWORD}
server:
  port: ${PORT:8080}

# Typed config:
# @ConfigurationProperties(prefix = "payment")
# → payment.timeout-ms=5000
```

---

## 14.7 Testing

| Dimension | Node.js | Java |
|-----------|---------|------|
| Unit testing | Jest, Mocha | JUnit 5, TestNG |
| Mocking | Jest mocks, Sinon | Mockito, MockMvc |
| Assertions | Jest expect, Chai | AssertJ (fluent) |
| Integration testing | Supertest | MockMvc, TestRestTemplate, Testcontainers |
| Test containers | testcontainers-node | Testcontainers |
| Code coverage | Istanbul/NYC | JaCoCo |

```javascript
// Jest unit test
describe('PaymentService', () => {
    let service;
    let mockRepo;

    beforeEach(() => {
        mockRepo = { findById: jest.fn(), save: jest.fn() };
        service = new PaymentService(mockRepo);
    });

    it('should throw when account not found', async () => {
        mockRepo.findById.mockResolvedValue(null);
        await expect(service.transfer('ACC-1', 'ACC-2', 100))
            .rejects.toThrow('Account not found');
    });
});
```

```java
// JUnit 5 + Mockito
@ExtendWith(MockitoExtension.class)
class PaymentServiceTest {

    @Mock
    private AccountRepository accountRepo;

    @InjectMocks
    private PaymentService paymentService;

    @Test
    void shouldThrowWhenAccountNotFound() {
        when(accountRepo.findById(any())).thenReturn(Optional.empty());

        assertThatThrownBy(() ->
            paymentService.transfer("ACC-1", "ACC-2", new BigDecimal("100")))
            .isInstanceOf(AccountNotFoundException.class)
            .hasMessageContaining("Account not found");
    }
}

// Integration test with Testcontainers
@SpringBootTest
@Testcontainers
class PaymentIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
        .withDatabaseName("testdb");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
    }

    @Autowired
    private PaymentService paymentService;

    @Test
    void shouldPersistPayment() {
        PaymentResponse response = paymentService.createPayment(testRequest);
        assertThat(response.getPaymentId()).isNotNull();
    }
}
```

---

## 14.8 Error Handling

```javascript
// Node.js: Error subclassing
class PaymentError extends Error {
    constructor(message, code, statusCode) {
        super(message);
        this.name = 'PaymentError';
        this.code = code;
        this.statusCode = statusCode;
    }
}

// Express error middleware
app.use((err, req, res, next) => {
    if (err instanceof PaymentError) {
        res.status(err.statusCode).json({ code: err.code, message: err.message });
    } else {
        res.status(500).json({ error: 'Internal server error' });
    }
});
```

```java
// Java: Exception hierarchy
public class PaymentException extends RuntimeException {
    private final ErrorCode code;
    public PaymentException(ErrorCode code, String message) {
        super(message);
        this.code = code;
    }
}

// Spring @ControllerAdvice (equivalent to Express error middleware)
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(PaymentException.class)
    public ResponseEntity<ErrorResponse> handlePayment(PaymentException ex) {
        return ResponseEntity.status(ex.getCode().httpStatus())
            .body(new ErrorResponse(ex.getCode().name(), ex.getMessage()));
    }
}
```

---

## 14.9 Logging

```javascript
// Node.js: Winston/Pino
const logger = winston.createLogger({
    format: winston.format.json(),
    transports: [new winston.transports.Console()]
});
logger.info('Payment processed', { paymentId, amount, userId });
```

```java
// Java: SLF4J + Logback
@Slf4j  // Lombok annotation — creates log field
public class PaymentService {
    public void process(Payment payment) {
        log.info("Payment processed: paymentId={} amount={} userId={}",
            payment.getId(), payment.getAmount(), payment.getUserId());
        // MDC.put("traceId", ...) for correlation
    }
}
```

---

## 14.10 Streaming / Events

| Dimension | Node.js | Java |
|-----------|---------|------|
| Event emitter | EventEmitter | ApplicationEventPublisher |
| Streams | Node.js Streams | Java NIO, Reactive Streams |
| Reactive | RxJS | Project Reactor (Flux/Mono) |
| Message queue | BullMQ, bee-queue | Spring AMQP, Spring Kafka |
| Server-sent events | SSE module | Spring WebFlux SSE |
| WebSocket | ws, socket.io | Spring WebSocket (STOMP) |

---

## 14.11 Performance Characteristics Comparison

| Scenario | Node.js | Java |
|----------|---------|------|
| I/O-bound (DB, HTTP) | Excellent | Excellent (blocking OK, or WebFlux) |
| CPU-bound | Single thread → bottleneck | Multiple threads → scales |
| Memory per connection | Very low (~KB) | Higher (thread stack = 256KB-1MB each) |
| Throughput (HTTP) | High (event loop) | High (thread pool, Virtual Threads) |
| Latency consistency | Very consistent | More variance (GC pauses) |
| Startup time | Sub-second | 3-8s (JVM), ms (Native) |
| Long-running tasks | Worker threads needed | Natural (just a thread) |

---

## 14.12 When Java Wins vs When Node.js Wins

### Java Advantages

```
✓ CPU-intensive computation (thread parallelism)
✓ Complex type systems (catches bugs at compile time)
✓ Large team codebases (refactoring safety with types)
✓ Ecosystem maturity (Spring, Hibernate, thousands of enterprise libs)
✓ JVM performance at scale (JIT optimization over time)
✓ Regulated industries (compliance tooling, audit libraries)
✓ Long-running processes (JVM overhead amortized)
✓ Thread-based parallelism without worker complexity
```

### Node.js Advantages

```
✓ Rapid prototyping (no compilation, fast iteration)
✓ I/O-bound microservices (event loop efficiency)
✓ Real-time (WebSocket, SSE — natural async)
✓ Serverless/edge functions (fast cold start)
✓ Full-stack JavaScript teams (same language frontend/backend)
✓ Small payload transformations (API gateways, BFF)
✓ npm ecosystem for utilities
✓ Lower memory for I/O-bound services
```

---

## Section Summary

The key insight from this comparison: **you already understand the concepts**. DI is DI whether it's done by `nest-di` or Spring. Kafka consumers are Kafka consumers whether you write them in JavaScript or Java. Transactions are transactions.

Your transition challenge is not conceptual — it's about:
1. Learning Java's type system and how to work with it efficiently
2. Understanding Spring's idioms and conventions
3. Learning JVM behavior and tuning
4. Internalizing Java's concurrency model (biggest mindset shift)

Everything else maps directly.

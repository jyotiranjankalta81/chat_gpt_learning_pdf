# Spring Boot Cheatsheet
## Essential Patterns for Enterprise Java

---

## Spring Boot Starter Dependencies

```xml
<!-- pom.xml essential starters -->

<!-- Web API -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>

<!-- Security -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>

<!-- Database -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
</dependency>

<!-- Redis Cache -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>

<!-- Kafka -->
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka</artifactId>
</dependency>

<!-- Actuator (health, metrics) -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>

<!-- Validation -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>

<!-- Testing -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
<dependency>
    <groupId>org.testcontainers</groupId>
    <artifactId>junit-jupiter</artifactId>
    <scope>test</scope>
</dependency>
```

---

## application.yml Reference

```yaml
# Server
server:
  port: 8080
  shutdown: graceful
  servlet:
    context-path: /

# Spring
spring:
  application:
    name: payment-service
  profiles:
    active: ${APP_ENV:local}

  # Database
  datasource:
    url: ${DB_URL:jdbc:postgresql://localhost:5432/payments}
    username: ${DB_USER:postgres}
    password: ${DB_PASSWORD:secret}
    hikari:
      maximum-pool-size: 10
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
      pool-name: PaymentPool

  # JPA
  jpa:
    hibernate:
      ddl-auto: validate          # NEVER create/update in production
    show-sql: false               # true only for debugging
    open-in-view: false           # Disable OSIV — avoid lazy loading in view layer
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true
        default_batch_fetch_size: 100   # Batch lazy loads

  # Redis
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      password: ${REDIS_PASSWORD:}
      timeout: 2000ms

  # Cache
  cache:
    type: redis
    redis:
      time-to-live: 300000ms     # 5 minutes default

  # Lifecycle
  lifecycle:
    timeout-per-shutdown-phase: 30s

# Actuator
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus,loggers
  endpoint:
    health:
      show-details: when-authorized
      probes:
        enabled: true
  metrics:
    export:
      prometheus:
        enabled: true
  tracing:
    sampling:
      probability: 0.1

# Logging
logging:
  level:
    root: INFO
    com.bank: DEBUG
    org.hibernate.SQL: DEBUG      # Enable for query debugging
    org.springframework.web: INFO
  pattern:
    console: "%d{ISO8601} [%thread] %-5level %logger{36} [%X{traceId},%X{spanId}] - %msg%n"
```

---

## REST Controller Patterns

```java
@RestController
@RequestMapping("/api/v1/payments")
@Validated
@Slf4j
public class PaymentController {

    private final PaymentService service;

    // Constructor injection — always
    public PaymentController(PaymentService service) {
        this.service = service;
    }

    // GET list with pagination
    @GetMapping
    public Page<PaymentResponse> list(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String status,
            @SortDefault(sort = "createdAt", direction = Sort.Direction.DESC)
            Pageable pageable) {
        return service.findAll(status, pageable);
    }

    // GET by ID
    @GetMapping("/{id}")
    public PaymentResponse getById(@PathVariable UUID id) {
        return service.findById(id);
    }

    // POST create
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public PaymentResponse create(
            @Valid @RequestBody CreatePaymentRequest request,
            @RequestHeader("X-Idempotency-Key") String idempotencyKey) {
        return service.create(request, idempotencyKey);
    }

    // PUT update
    @PutMapping("/{id}")
    public PaymentResponse update(
            @PathVariable UUID id,
            @Valid @RequestBody UpdatePaymentRequest request) {
        return service.update(id, request);
    }

    // DELETE
    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable UUID id) {
        service.delete(id);
    }
}

// Global exception handler
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(NotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(NotFoundException ex) {
        return new ErrorResponse("NOT_FOUND", ex.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ValidationErrorResponse handleValidation(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors()
            .forEach(e -> errors.put(e.getField(), e.getDefaultMessage()));
        return new ValidationErrorResponse("VALIDATION_ERROR", errors);
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorResponse handleGeneral(Exception ex) {
        log.error("Unhandled exception", ex);
        return new ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred");
    }
}
```

---

## Service Layer Patterns

```java
@Service
@Transactional(readOnly = true)  // Default read-only for all methods
@Slf4j
public class PaymentService {

    private final PaymentRepository paymentRepo;
    private final AccountRepository accountRepo;
    private final ApplicationEventPublisher eventPublisher;

    public PaymentService(PaymentRepository paymentRepo,
                          AccountRepository accountRepo,
                          ApplicationEventPublisher eventPublisher) {
        this.paymentRepo = paymentRepo;
        this.accountRepo = accountRepo;
        this.eventPublisher = eventPublisher;
    }

    public Page<PaymentResponse> findAll(String status, Pageable pageable) {
        Specification<Payment> spec = status != null
            ? (root, q, cb) -> cb.equal(root.get("status"), PaymentStatus.valueOf(status))
            : Specification.where(null);
        return paymentRepo.findAll(spec, pageable).map(PaymentResponse::from);
    }

    public PaymentResponse findById(UUID id) {
        return paymentRepo.findById(id)
            .map(PaymentResponse::from)
            .orElseThrow(() -> new NotFoundException("Payment not found: " + id));
    }

    @Transactional  // Override to write transaction
    public PaymentResponse create(CreatePaymentRequest request, String idempotencyKey) {
        // Check idempotency
        paymentRepo.findByIdempotencyKey(idempotencyKey).ifPresent(existing -> {
            throw new DuplicateOperationException("Payment already processed: " + idempotencyKey);
        });

        // Load and validate
        Account fromAccount = accountRepo.findByIdForUpdate(request.getFromAccountId())
            .orElseThrow(() -> new NotFoundException("Account: " + request.getFromAccountId()));

        if (fromAccount.getBalance().compareTo(request.getAmount()) < 0) {
            throw new InsufficientFundsException(request.getAmount(), fromAccount.getBalance());
        }

        // Execute
        fromAccount.debit(request.getAmount());
        Payment payment = paymentRepo.save(Payment.create(request, idempotencyKey));

        // Publish event (after commit — @TransactionalEventListener)
        eventPublisher.publishEvent(new PaymentCreatedEvent(payment));

        log.info("Payment created: id={} amount={}", payment.getId(), payment.getAmount());
        return PaymentResponse.from(payment);
    }
}
```

---

## JPA Repository Patterns

```java
@Repository
public interface PaymentRepository extends JpaRepository<Payment, UUID>,
                                            JpaSpecificationExecutor<Payment> {

    // Method naming query
    Optional<Payment> findByIdempotencyKey(String key);
    List<Payment> findByStatusAndCreatedAtAfter(PaymentStatus status, Instant cutoff);
    boolean existsByIdempotencyKey(String key);
    long countByStatus(PaymentStatus status);

    // Custom JPQL
    @Query("SELECT p FROM Payment p WHERE p.accountId = :id AND p.amount > :min ORDER BY p.amount DESC")
    List<Payment> findLargeByAccount(@Param("id") String accountId,
                                      @Param("min") BigDecimal minAmount);

    // Pessimistic lock
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT p FROM Payment p WHERE p.id = :id")
    Optional<Payment> findByIdForUpdate(@Param("id") UUID id);

    // Projection
    List<PaymentSummary> findByAccountId(String accountId);

    // Streaming (large datasets)
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "500"))
    Stream<Payment> findAllByStatus(PaymentStatus status);

    // Native query
    @Query(value = "SELECT * FROM payments WHERE amount > :amount ORDER BY created_at DESC LIMIT 100",
           nativeQuery = true)
    List<Payment> findTopLargePayments(@Param("amount") BigDecimal amount);
}

// Projection interface
public interface PaymentSummary {
    UUID getId();
    BigDecimal getAmount();
    PaymentStatus getStatus();
    Instant getCreatedAt();
}
```

---

## Kafka Producer & Consumer

```java
// Producer
@Service
public class PaymentEventProducer {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    public void publishPaymentCreated(Payment payment) {
        PaymentCreatedEvent event = PaymentCreatedEvent.from(payment);
        kafkaTemplate.send("payment.created", payment.getId().toString(), event)
            .whenComplete((result, ex) -> {
                if (ex != null) {
                    log.error("Failed to publish event: {}", payment.getId(), ex);
                    outboxService.saveForRetry(event);
                } else {
                    log.debug("Event published: partition={} offset={}",
                        result.getRecordMetadata().partition(),
                        result.getRecordMetadata().offset());
                }
            });
    }
}

// Consumer
@Component
@Slf4j
public class PaymentEventConsumer {

    @KafkaListener(topics = "payment.created", groupId = "notification-service")
    public void handle(
            @Payload PaymentCreatedEvent event,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment ack) {

        log.info("Processing: id={} partition={} offset={}", event.getPaymentId(), partition, offset);

        try {
            // Idempotency check
            if (processedEventRepo.existsByEventId(event.getEventId())) {
                log.info("Duplicate, skipping: {}", event.getEventId());
                ack.acknowledge();
                return;
            }

            notificationService.notifyPaymentCreated(event);
            processedEventRepo.markProcessed(event.getEventId());
            ack.acknowledge();

        } catch (Exception e) {
            log.error("Failed to process event: {}", event.getEventId(), e);
            throw e;  // Trigger retry/DLQ
        }
    }
}
```

---

## Testing Patterns

```java
// Unit test
@ExtendWith(MockitoExtension.class)
class PaymentServiceTest {

    @Mock PaymentRepository paymentRepo;
    @Mock AccountRepository accountRepo;
    @Mock ApplicationEventPublisher eventPublisher;
    @InjectMocks PaymentService paymentService;

    @Test
    void createPayment_shouldDebitAccount() {
        Account account = Account.withBalance(new BigDecimal("1000.00"));
        when(accountRepo.findByIdForUpdate(any())).thenReturn(Optional.of(account));
        when(paymentRepo.save(any())).thenAnswer(inv -> inv.getArgument(0));

        paymentService.create(new CreatePaymentRequest("ACC-1", "ACC-2",
            new BigDecimal("100.00")), "IDEM-1");

        assertThat(account.getBalance()).isEqualByComparingTo("900.00");
        verify(eventPublisher).publishEvent(any(PaymentCreatedEvent.class));
    }
}

// Integration test with Testcontainers
@SpringBootTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class PaymentIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

    @Container
    static KafkaContainer kafka = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.6.0"));

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }

    @Autowired MockMvc mockMvc;
    @Autowired ObjectMapper objectMapper;

    @Test
    void createPayment_returnsCreated() throws Exception {
        mockMvc.perform(post("/api/v1/payments")
                .contentType(MediaType.APPLICATION_JSON)
                .header("X-Idempotency-Key", UUID.randomUUID().toString())
                .content(objectMapper.writeValueAsString(testRequest)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.paymentId").isNotEmpty())
            .andExpect(jsonPath("$.status").value("PENDING"));
    }
}
```

---

## Configuration Patterns

```java
// Type-safe configuration
@ConfigurationProperties(prefix = "payment")
@Validated
@Data  // Lombok
public class PaymentConfig {

    @NotNull
    @Valid
    private Limits limits;

    @Min(100) @Max(60000)
    private int timeoutMs = 5000;

    @NotBlank
    private String processorUrl;

    @Data
    public static class Limits {
        @NotNull @DecimalMin("0.01")
        private BigDecimal maxSinglePayment;

        @NotNull @DecimalMin("0.01")
        private BigDecimal dailyLimit;
    }
}

// Enable in main class or config
@EnableConfigurationProperties(PaymentConfig.class)
@SpringBootApplication
public class Application { ... }
```

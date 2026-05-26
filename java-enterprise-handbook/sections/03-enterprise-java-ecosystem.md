# Section 3: Enterprise Java Ecosystem — Spring Boot & Beyond

> **The Reality:** Spring Boot is NOT just a framework. It is the operating system of enterprise Java. Understanding how Spring's IoC container, AOP proxy model, and autoconfiguration work is what makes you fluent in enterprise Java codebases at JP Morgan, HSBC, and every FAANG Java backend.

---

## 3.1 Spring Boot Architecture — What It Actually Does

### The Spring Application Context

```
Spring Application Context = Dependency Injection Container
                           = Object graph manager
                           = Configuration resolver
                           = Bean lifecycle orchestrator
```

When you call `SpringApplication.run()`, Spring:
1. Scans classpath for `@Component`, `@Service`, `@Repository`, `@Controller`
2. Reads `@Configuration` classes and `@Bean` methods
3. Resolves `application.properties` / `application.yml`
4. Runs autoconfiguration (100+ auto-configs based on classpath)
5. Creates and wires all beans (resolves dependencies)
6. Starts embedded Tomcat/Netty
7. Fires `ApplicationReadyEvent`

### Node.js → Spring Boot Mental Model

```
Express app bootstrap        →   Spring Boot @SpringBootApplication
express.use(middleware)      →   @Bean or @Component registration
app.use('/api', router)      →   @RequestMapping on @Controller
require('./config')          →   @ConfigurationProperties
process.env.PORT             →   ${server.port} or @Value("${server.port}")
module.exports = service     →   @Service class (Spring manages lifecycle)
new Service(dep1, dep2)      →   Constructor injection (Spring injects)
```

---

## 3.2 Dependency Injection — The Core Principle

### Why DI Exists in Enterprise Software

In a 50-engineer team working on a monorepo, you need:
1. **Testability:** Replace real DB with mock without changing service code
2. **Modularity:** Swap implementations (StripePayment → BraintreePayment) without changing callers
3. **Lifecycle management:** Centralized creation, destruction, pooling of objects
4. **Cross-cutting concerns:** Add logging/metrics/security to any bean without touching its code

### Three Ways to Inject Dependencies

```java
// 1. Constructor Injection — PREFERRED (immutable, testable, explicit)
@Service
public class PaymentService {
    private final PaymentRepository repository;
    private final NotificationService notificationService;
    private final KafkaProducer<String, PaymentEvent> producer;

    // Spring injects when creating PaymentService
    // If any dependency missing → fail at startup (not at runtime)
    public PaymentService(
            PaymentRepository repository,
            NotificationService notificationService,
            KafkaProducer<String, PaymentEvent> producer) {
        this.repository = repository;
        this.notificationService = notificationService;
        this.producer = producer;
    }
}

// 2. Field Injection — AVOID (not testable without Spring context)
@Service
public class BadService {
    @Autowired
    private PaymentRepository repository;  // Cannot inject in unit tests without Spring
}

// 3. Setter Injection — for optional dependencies only
@Service
public class ConfigurableService {
    private MetricsClient metricsClient;

    @Autowired(required = false)
    public void setMetricsClient(MetricsClient metricsClient) {
        this.metricsClient = metricsClient;
    }
}
```

### Bean Scopes

```java
@Component
@Scope("singleton")    // DEFAULT — one instance per Spring context
public class UserService { }

@Component
@Scope("prototype")    // New instance every time it's injected/requested
public class ReportBuilder { }

@Component
@RequestScope          // New instance per HTTP request (web apps)
public class RequestContext { }

@Component
@SessionScope          // One instance per HTTP session
public class UserPreferences { }
```

**Interview question:** "When would you use prototype scope?"  
Answer: Stateful beans that cannot be shared (e.g., a builder that accumulates state, a non-thread-safe processor).

---

## 3.3 Spring Bean Lifecycle

```
1. BeanDefinition read (from @Component, @Bean, XML)
2. BeanDefinition registered in BeanFactory
3. BeanFactoryPostProcessor runs (modifies bean definitions)
4. Bean instantiation (constructor called)
5. Dependency injection (fields/setters if applicable)
6. BeanPostProcessor.postProcessBeforeInitialization()
7. @PostConstruct method
8. InitializingBean.afterPropertiesSet()
9. Custom init-method
10. BeanPostProcessor.postProcessAfterInitialization()
    ← AOP PROXIES ARE CREATED HERE
11. Bean is READY (in context)

...application runs...

12. @PreDestroy
13. DisposableBean.destroy()
14. Custom destroy-method
```

```java
@Service
@Slf4j
public class CacheWarmingService {
    private final CacheService cache;
    private final ConfigRepository configRepo;

    public CacheWarmingService(CacheService cache, ConfigRepository configRepo) {
        this.cache = cache;
        this.configRepo = configRepo;
        // Don't load data here — dependencies may not be ready yet
    }

    @PostConstruct
    public void warmUp() {
        // ALL dependencies are injected by now — safe to use them
        log.info("Warming up configuration cache");
        configRepo.findAll().forEach(config ->
            cache.put(config.getKey(), config.getValue()));
    }

    @PreDestroy
    public void shutdown() {
        log.info("Flushing cache before shutdown");
        cache.flush();
    }
}
```

---

## 3.4 Spring MVC — Request Lifecycle

```
HTTP Request
    ↓
DispatcherServlet (Front Controller)
    ↓
HandlerMapping → find @Controller and @RequestMapping
    ↓
HandlerInterceptor.preHandle() (auth checks, logging)
    ↓
ArgumentResolver (deserialize request body, path variables, headers)
    ↓
@Controller method executes
    ↓
HandlerInterceptor.postHandle()
    ↓
MessageConverter (serialize response to JSON)
    ↓
HandlerInterceptor.afterCompletion()
    ↓
HTTP Response
```

### Controller Best Practices

```java
@RestController
@RequestMapping("/api/v1/payments")
@Validated
@Slf4j
public class PaymentController {

    private final PaymentService paymentService;

    public PaymentController(PaymentService paymentService) {
        this.paymentService = paymentService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<PaymentResponse> createPayment(
            @Valid @RequestBody CreatePaymentRequest request,
            @RequestHeader("X-Idempotency-Key") String idempotencyKey,
            @RequestHeader("X-Request-ID") String requestId) {

        log.info("Creating payment requestId={} idempotencyKey={}", requestId, idempotencyKey);
        PaymentResponse response = paymentService.createPayment(request, idempotencyKey);
        return ApiResponse.success(response);
    }

    @GetMapping("/{paymentId}")
    public ApiResponse<PaymentResponse> getPayment(
            @PathVariable String paymentId,
            @RequestParam(required = false, defaultValue = "false") boolean includeHistory) {

        PaymentResponse response = paymentService.findById(paymentId, includeHistory);
        return ApiResponse.success(response);
    }

    @GetMapping
    public Page<PaymentResponse> listPayments(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String status,
            @SortDefault(sort = "createdAt", direction = Sort.Direction.DESC) Pageable pageable) {

        return paymentService.findAll(status, pageable);
    }
}
```

### Request/Response DTOs — Best Practices

```java
// Request: validate inputs
public record CreatePaymentRequest(
    @NotBlank String fromAccountId,
    @NotBlank String toAccountId,
    @NotNull @DecimalMin("0.01") @DecimalMax("1000000.00") BigDecimal amount,
    @NotBlank @Size(min = 3, max = 3) @Pattern(regexp = "[A-Z]{3}") String currency,
    @Size(max = 500) String description,
    @NotNull @FutureOrPresent LocalDate valueDate
) {}

// Response: never expose internal fields directly
public record PaymentResponse(
    String paymentId,
    String status,
    BigDecimal amount,
    String currency,
    Instant createdAt,
    Instant completedAt
) {
    public static PaymentResponse from(Payment payment) {
        return new PaymentResponse(
            payment.getId(),
            payment.getStatus().name(),
            payment.getAmount(),
            payment.getCurrency(),
            payment.getCreatedAt(),
            payment.getCompletedAt()
        );
    }
}
```

---

## 3.5 Spring Security — Architecture Deep Dive

```
Request
   ↓
SecurityFilterChain (ordered chain of filters)
   ├── SecurityContextPersistenceFilter  (load security context from session/JWT)
   ├── UsernamePasswordAuthenticationFilter (form login)
   ├── BearerTokenAuthenticationFilter  (JWT)
   ├── BasicAuthenticationFilter
   └── ExceptionTranslationFilter
   ↓
FilterSecurityInterceptor → check @PreAuthorize, URL patterns
   ↓
Controller (if authorized)
```

### JWT Authentication Configuration

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity  // Enables @PreAuthorize, @PostAuthorize
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())  // Stateless API — no CSRF needed
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/auth/**").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthFilter(), UsernamePasswordAuthenticationFilter.class)
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(customAuthEntryPoint())
                .accessDeniedHandler(customAccessDeniedHandler())
            )
            .build();
    }

    @Bean
    public JwtAuthenticationFilter jwtAuthFilter() {
        return new JwtAuthenticationFilter(jwtService);
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);  // Cost factor 12 — standard for banking
    }
}

// JWT Filter
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws IOException, ServletException {
        String header = request.getHeader("Authorization");
        if (header == null || !header.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        String token = header.substring(7);
        try {
            Claims claims = jwtService.validateAndExtract(token);
            UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                claims.getSubject(),
                null,
                extractAuthorities(claims)
            );
            SecurityContextHolder.getContext().setAuthentication(auth);
        } catch (JwtException e) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return;
        }

        filterChain.doFilter(request, response);
    }
}
```

### Method-Level Security

```java
@Service
public class AccountService {

    @PreAuthorize("hasRole('ADMIN') or @accountSecurity.isOwner(#accountId, authentication)")
    public Account getAccount(String accountId) { ... }

    @PreAuthorize("hasRole('ADMIN')")
    @PostAuthorize("returnObject.balance < 10000 or hasRole('COMPLIANCE')")
    public Account getHighValueAccount(String accountId) { ... }

    @PreFilter("filterObject.ownerId == authentication.name")
    public List<Account> processAccounts(List<Account> accounts) { ... }
}
```

---

## 3.6 Spring Data JPA — Enterprise Persistence

```java
// Repository interface — Spring generates implementation at startup
public interface PaymentRepository extends JpaRepository<Payment, UUID> {

    // Method naming → SQL generation (JPQL)
    List<Payment> findByStatusAndCreatedAtAfter(PaymentStatus status, Instant cutoff);

    Optional<Payment> findByIdempotencyKey(String idempotencyKey);

    // Custom JPQL
    @Query("SELECT p FROM Payment p WHERE p.accountId = :accountId AND p.amount > :threshold")
    List<Payment> findLargePayments(@Param("accountId") String accountId,
                                    @Param("threshold") BigDecimal threshold);

    // Native SQL (when you need DB-specific features)
    @Query(value = """
        SELECT * FROM payments
        WHERE account_id = :accountId
        AND created_at >= NOW() - INTERVAL '30 days'
        ORDER BY amount DESC
        LIMIT :limit
        """, nativeQuery = true)
    List<Payment> findRecentLargeNative(@Param("accountId") String accountId,
                                         @Param("limit") int limit);

    // Projection — fetch only needed columns (avoid N+1 and over-fetching)
    List<PaymentSummary> findByAccountId(String accountId);

    // Streaming for large datasets (avoid loading all into memory)
    @QueryHints(@QueryHint(name = HINT_FETCH_SIZE, value = "500"))
    Stream<Payment> findAllByStatus(PaymentStatus status);

    // Paging
    Page<Payment> findByAccountId(String accountId, Pageable pageable);

    // Exists check (more efficient than findBy + null check)
    boolean existsByIdempotencyKey(String idempotencyKey);

    // Count
    long countByStatusAndCreatedAtAfter(PaymentStatus status, Instant cutoff);
}
```

### JPA Entity Best Practices

```java
@Entity
@Table(name = "payments",
       indexes = {
           @Index(name = "idx_payments_account_id", columnList = "account_id"),
           @Index(name = "idx_payments_idempotency", columnList = "idempotency_key", unique = true),
           @Index(name = "idx_payments_status_created", columnList = "status, created_at")
       })
@EntityListeners(AuditingEntityListener.class)  // Automatic audit fields
public class Payment {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "account_id", nullable = false, length = 50)
    private String accountId;

    @Column(nullable = false, precision = 19, scale = 4)
    private BigDecimal amount;

    @Column(length = 3, nullable = false)
    @Enumerated(EnumType.STRING)  // Store as "PENDING" not 0
    private PaymentStatus status;

    @Column(name = "idempotency_key", unique = true, length = 100)
    private String idempotencyKey;

    @CreatedDate  // Spring Data Auditing
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private Instant updatedAt;

    @Version  // Optimistic locking — prevents lost updates in concurrent scenarios
    private Long version;

    // Relationships
    @ManyToOne(fetch = FetchType.LAZY)  // ALWAYS use LAZY for ManyToOne
    @JoinColumn(name = "account_id", insertable = false, updatable = false)
    private Account account;

    @OneToMany(mappedBy = "payment",
               cascade = CascadeType.ALL,
               orphanRemoval = true,
               fetch = FetchType.LAZY)
    private List<PaymentItem> items = new ArrayList<>();
}
```

---

## 3.7 Aspect-Oriented Programming (AOP)

AOP is how Spring adds cross-cutting concerns (logging, security, transactions, caching) without polluting business code.

```
Without AOP:
PaymentService.transfer() {
    log.info("starting transfer");  // logging
    checkAuth();                     // security
    startTransaction();              // transaction
    doTransfer();                    // business logic
    commitTransaction();             // transaction
    updateCache();                   // caching
    logAudit();                      // audit
    emitMetrics();                   // metrics
}

With AOP:
PaymentService.transfer() {
    doTransfer();  // ONLY business logic
}
// All cross-cutting concerns added by Spring AOP interceptors
```

### AOP Concepts

```java
@Aspect
@Component
@Slf4j
public class PerformanceMonitorAspect {

    // Pointcut: match all methods in service layer
    @Pointcut("within(@org.springframework.stereotype.Service *)")
    public void serviceLayer() {}

    // Around advice: wraps method execution
    @Around("serviceLayer()")
    public Object measureTime(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().toShortString();
        long start = System.currentTimeMillis();
        try {
            Object result = joinPoint.proceed();  // Execute actual method
            long duration = System.currentTimeMillis() - start;
            log.debug("Method {} took {}ms", methodName, duration);
            meterRegistry.timer("service.method.duration",
                "method", methodName).record(duration, TimeUnit.MILLISECONDS);
            return result;
        } catch (Exception e) {
            meterRegistry.counter("service.method.errors",
                "method", methodName, "exception", e.getClass().getSimpleName()).increment();
            throw e;
        }
    }
}

// AOP for audit logging
@Aspect
@Component
public class AuditAspect {

    @AfterReturning(
        pointcut = "@annotation(auditLog)",
        returning = "result"
    )
    public void logAudit(JoinPoint joinPoint, AuditLog auditLog, Object result) {
        String userId = SecurityContextHolder.getContext()
            .getAuthentication().getName();
        auditLogRepository.save(new AuditEntry(
            userId, auditLog.action(), auditLog.resource(), Instant.now()
        ));
    }
}
```

### @Transactional — AOP in Action

`@Transactional` is implemented via AOP. Spring creates a proxy around your bean and intercepts calls to transactional methods.

```java
@Service
public class TransferService {

    @Transactional(
        isolation = Isolation.SERIALIZABLE,    // Highest isolation for transfers
        propagation = Propagation.REQUIRED,    // Join existing or create new tx
        rollbackFor = Exception.class,         // Rollback on ANY exception
        timeout = 30                           // Fail if transaction > 30 seconds
    )
    public void transfer(String fromId, String toId, BigDecimal amount) {
        Account from = accountRepo.findByIdWithLock(fromId);  // SELECT FOR UPDATE
        Account to = accountRepo.findById(toId).orElseThrow();

        if (from.getBalance().compareTo(amount) < 0) {
            throw new InsufficientFundsException(amount, from.getBalance());
        }

        from.debit(amount);
        to.credit(amount);

        accountRepo.save(from);
        accountRepo.save(to);
        // On method exit: Spring commits transaction
        // On exception: Spring rolls back
    }
}

// COMMON @Transactional PITFALLS:
// 1. Self-invocation — calling @Transactional method from same class bypasses proxy
// 2. Rollback on checked exceptions — by default only RuntimeException causes rollback
// 3. @Transactional on private methods — ignored (proxy can't intercept)
```

---

## 3.8 Spring WebFlux — Reactive Programming

WebFlux is Spring's reactive framework — like Node.js event loop but explicit:

```java
// Node.js: async/await is implicit non-blocking
async function getUser(id) {
    const user = await db.findUser(id);
    return user;
}

// Spring WebFlux: explicit reactive types
@GetMapping("/users/{id}")
public Mono<User> getUser(@PathVariable String id) {
    return userRepository.findById(id)  // Reactive repo
        .switchIfEmpty(Mono.error(new UserNotFoundException(id)));
}

// Multiple async operations
@GetMapping("/dashboard/{userId}")
public Mono<Dashboard> getDashboard(@PathVariable String userId) {
    Mono<User> userMono = userRepo.findById(userId);
    Mono<List<Account>> accountsMono = accountRepo.findByUserId(userId);
    Mono<List<Transaction>> txMono = transactionRepo.findRecentByUser(userId, 10);

    return Mono.zip(userMono, accountsMono, txMono)
        .map(tuple -> new Dashboard(tuple.getT1(), tuple.getT2(), tuple.getT3()));
    // All three DB calls execute in parallel!
}

// Streaming large datasets
@GetMapping(value = "/reports/transactions", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<Transaction> streamTransactions() {
    return transactionRepo.findAllAsFlux()  // Don't load all into memory
        .delayElements(Duration.ofMillis(10));  // Backpressure-aware
}
```

### When to Use WebFlux vs MVC

```
Use Spring MVC (blocking) when:
- CRUD apps with traditional JDBC
- Team is familiar with blocking model
- Using blocking libraries (most Spring Data JDBC/JPA)
- Simpler code, easier debugging

Use Spring WebFlux (reactive) when:
- High concurrency with many I/O-bound operations
- Streaming large datasets to clients
- Integrating with reactive systems (Cassandra, MongoDB reactive, R2DBC)
- Building API gateways
```

---

## 3.9 Spring Configuration — Enterprise Patterns

```yaml
# application.yml — base config
spring:
  application:
    name: payment-service
  profiles:
    active: ${APP_ENV:local}

# application-prod.yml — production overrides
spring:
  datasource:
    url: ${DB_URL}           # Always externalize sensitive config
    username: ${DB_USER}
    password: ${DB_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: validate     # NEVER use create/update in production!
    show-sql: false

# application-local.yml — local dev
spring:
  datasource:
    url: jdbc:h2:mem:testdb  # In-memory DB for local
  h2:
    console.enabled: true
```

### Type-Safe Configuration

```java
@ConfigurationProperties(prefix = "payment")
@Validated
@Data
public class PaymentProperties {

    @NotNull
    private Limits limits;

    @NotBlank
    private String processorUrl;

    @Min(1000) @Max(30000)
    private int timeoutMs = 5000;

    @Data
    public static class Limits {
        @DecimalMin("0.01")
        private BigDecimal maxSinglePayment;

        @DecimalMin("0.01")
        private BigDecimal dailyLimit;
    }
}

// payment.limits.max-single-payment=10000.00
// payment.limits.daily-limit=100000.00
// payment.timeout-ms=8000
// payment.processor-url=https://payments.internal.bank.com
```

---

## Section Summary: Spring Interview Essentials

**Must-know Spring concepts:**

1. **DI container internals** — how beans are created, wired, scoped
2. **AOP proxy model** — `@Transactional` pitfalls (self-invocation, visibility)
3. **Request lifecycle** — DispatcherServlet → Interceptors → Controller
4. **Security filter chain** — JWT validation, `SecurityContextHolder`
5. **JPA patterns** — N+1 problem, lazy loading, optimistic locking
6. **`@Transactional` isolation levels** — when each level is appropriate
7. **Spring Boot autoconfiguration** — how it works, how to override it
8. **Profiles** — managing config across environments

**Most common Spring bug in interviews:** "What happens when `@Transactional` calls another `@Transactional` method in the same class?"  
Answer: The inner method's transaction settings are IGNORED because self-invocation bypasses the AOP proxy. You must inject the bean into itself or refactor.

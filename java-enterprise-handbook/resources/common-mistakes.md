# Common Mistakes to Avoid
## Java & Spring Anti-Patterns That Will Hurt You in Production and Interviews

---

## Java Language Mistakes

### 1. Using `==` for String/Object Comparison
```java
// WRONG
if (status == "ACTIVE") { }  // Always false for non-literal strings!
if (user1 == user2) { }       // Compares references, not content

// CORRECT
if ("ACTIVE".equals(status)) { }  // Null-safe: literal on left
if (user1.equals(user2)) { }
if (Objects.equals(user1, user2)) { }  // Null-safe both sides
```

### 2. Float/Double for Money
```java
// WRONG — floating point imprecision
double price = 0.1 + 0.2;  // 0.30000000000000004
double fee = 100.0 * 0.029;  // 2.8999999999999996 (not 2.90!)

// CORRECT
BigDecimal price = new BigDecimal("0.1").add(new BigDecimal("0.2"));  // 0.3 exactly
BigDecimal fee = new BigDecimal("100.00")
    .multiply(new BigDecimal("0.029"))
    .setScale(2, RoundingMode.HALF_UP);  // 2.90
```

### 3. Modifying Collection While Iterating
```java
// WRONG — ConcurrentModificationException
for (String item : list) {
    if (shouldRemove(item)) list.remove(item);
}

// CORRECT
list.removeIf(this::shouldRemove);  // Or use Iterator.remove()
// OR
List<String> toRemove = list.stream()
    .filter(this::shouldRemove)
    .collect(Collectors.toList());
list.removeAll(toRemove);
```

### 4. Not Closing Resources
```java
// WRONG — connection never closed if exception thrown
Connection conn = dataSource.getConnection();
conn.prepareStatement(sql).execute();
conn.close();  // Skipped if exception above!

// CORRECT
try (Connection conn = dataSource.getConnection();
     PreparedStatement stmt = conn.prepareStatement(sql)) {
    stmt.execute();
}  // Auto-closed
```

### 5. Null Return Instead of Optional
```java
// WRONG — forces callers to do null checks everywhere
public User findUser(String id) {
    return userRepo.findById(id);  // Returns null if not found
}

// CORRECT — explicit in signature that value may be absent
public Optional<User> findUser(String id) {
    return userRepo.findById(id);
}
// Callers: service.findUser(id).orElseThrow(() -> new UserNotFoundException(id))
```

### 6. String Concatenation in Loops
```java
// WRONG — creates N intermediate String objects
String result = "";
for (String item : items) {
    result += item + ", ";  // O(n²) memory allocation!
}

// CORRECT
StringBuilder sb = new StringBuilder();
for (String item : items) sb.append(item).append(", ");
// OR: String.join(", ", items)
// OR: items.stream().collect(Collectors.joining(", "))
```

---

## Spring Mistakes

### 7. Field Injection Instead of Constructor Injection
```java
// WRONG — cannot test without Spring context, hides dependencies
@Service
public class PaymentService {
    @Autowired
    private PaymentRepository repo;  // Hidden dependency
}

// CORRECT — explicit, testable, immutable
@Service
public class PaymentService {
    private final PaymentRepository repo;

    public PaymentService(PaymentRepository repo) {
        this.repo = repo;
    }
}
```

### 8. @Transactional Self-Invocation
```java
// WRONG — self-invocation bypasses proxy, no transaction!
@Service
public class OrderService {
    public void processOrder(Order order) {
        this.placeOrder(order);  // Calls own method — NO transaction!
    }

    @Transactional
    public void placeOrder(Order order) { ... }
}

// CORRECT — inject self via ApplicationContext, or refactor
@Service
public class OrderService {
    private final OrderService self;  // Self-injection via Spring
    // OR: extract placeOrder to separate @Service
}
```

### 9. @Transactional on Private Methods
```java
// WRONG — Spring proxy cannot intercept private methods
@Service
public class PaymentService {
    @Transactional
    private void updateBalance(String id, BigDecimal amount) {
        // @Transactional is IGNORED — no proxy for private!
    }
}

// CORRECT — must be public (or at minimum protected)
@Transactional
public void updateBalance(String id, BigDecimal amount) { ... }
```

### 10. Checked Exceptions Not Rolling Back @Transactional
```java
// WRONG — checked exceptions don't roll back by default
@Transactional
public void processPayment(Payment payment) throws PaymentException {
    accountRepo.debit(payment.getFromAccount(), payment.getAmount());
    // EXCEPTION THROWN HERE → transaction COMMITS debit!
    if (!externalGateway.charge(payment)) {
        throw new PaymentException("Gateway declined");  // Checked!
    }
}

// CORRECT
@Transactional(rollbackFor = Exception.class)  // Roll back on any exception
public void processPayment(Payment payment) throws PaymentException { ... }

// OR: use unchecked exception
public class PaymentException extends RuntimeException { }  // Rolls back automatically
```

---

## JPA/Database Mistakes

### 11. N+1 Query Problem
```java
// WRONG — fires 1 + N queries
List<Order> orders = orderRepo.findAll();  // 1 query
for (Order order : orders) {
    String name = order.getCustomer().getName();  // N queries!
}

// CORRECT — 1 query with JOIN FETCH
@Query("SELECT o FROM Order o JOIN FETCH o.customer")
List<Order> findAllWithCustomer();
```

### 12. FetchType.EAGER on Collections
```java
// WRONG — loads ALL items every time you load an Order
@OneToMany(fetch = FetchType.EAGER)  // NEVER on collections
private List<OrderItem> items;

// CORRECT — lazy load, fetch when needed
@OneToMany(fetch = FetchType.LAZY)  // Default for collections — keep it!
private List<OrderItem> items;
// Use @EntityGraph or JOIN FETCH to load when needed
```

### 13. Missing @Version for Concurrent Updates
```java
// WRONG — concurrent updates: last-write-wins (silently)
@Entity
public class Account {
    private BigDecimal balance;  // Two threads update: one update lost!
}

// CORRECT — optimistic locking
@Entity
public class Account {
    private BigDecimal balance;
    @Version
    private Long version;  // Throws OptimisticLockException on conflict
}
```

### 14. hibernate.ddl-auto = update in Production
```yaml
# WRONG — Hibernate might drop columns with data!
spring.jpa.hibernate.ddl-auto: update

# CORRECT — validate schema matches entities, use Flyway for migrations
spring.jpa.hibernate.ddl-auto: validate
```

### 15. Loading All Records Without Pagination
```java
// WRONG — 10 million records → OOM
List<User> users = userRepo.findAll();

// CORRECT — paginate or stream
Page<User> page = userRepo.findAll(PageRequest.of(0, 100));
// OR for batch processing:
userRepo.findAllAsStream().forEach(this::process);  // Stream
```

---

## Concurrency Mistakes

### 16. HashMap in Singleton Service
```java
// WRONG — HashMap not thread-safe, multiple HTTP threads share this!
@Service  // Singleton
public class CacheService {
    private Map<String, Object> cache = new HashMap<>();  // RACE CONDITION!
}

// CORRECT
private Map<String, Object> cache = new ConcurrentHashMap<>();
```

### 17. Raw Thread Creation in Production
```java
// WRONG — uncontrolled, unbounded thread creation
new Thread(() -> processPayment(payment)).start();  // Can create millions!

// CORRECT — bounded thread pool
@Async("paymentExecutor")
public void processPaymentAsync(Payment payment) { ... }
```

### 18. Blocking in Reactive Pipeline
```java
// WRONG — blocks reactor thread, defeats reactive purpose
Mono.fromCallable(() -> {
    return jdbcTemplate.queryForObject(sql, String.class);  // BLOCKING!
});

// CORRECT
Mono.fromCallable(() -> jdbcTemplate.queryForObject(sql, String.class))
    .subscribeOn(Schedulers.boundedElastic());  // Offload to bounded thread pool
```

### 19. ThreadLocal Leak in Thread Pool
```java
// WRONG — thread reused from pool, ThreadLocal from previous request still there
MDC.put("userId", userId);
// ... handle request ...
// Missing: MDC.clear()!

// CORRECT — always clean up in finally
try {
    MDC.put("userId", userId);
    handleRequest();
} finally {
    MDC.clear();  // Prevent leaking to next request on this thread
}
```

---

## Security Mistakes

### 20. Dynamic SQL with User Input
```java
// WRONG — SQL injection vulnerability
String sql = "SELECT * FROM users WHERE name = '" + userInput + "'";
// userInput = "' OR '1'='1" → returns all users!

// CORRECT
@Query("SELECT u FROM User u WHERE u.name = :name")
Optional<User> findByName(@Param("name") String name);
```

### 21. Logging Sensitive Data
```java
// WRONG — PII/credentials in logs
log.info("Processing card: {}", cardDetails);  // Logs full card number!
log.debug("User password: {}", password);       // NEVER!

// CORRECT
log.info("Processing card ending in: {}", cardNumber.substring(cardNumber.length() - 4));
log.debug("Authentication attempt for user: {}", userId);  // Log ID, not credentials
```

### 22. Returning Internal Exception Details
```java
// WRONG — reveals stack trace/schema to attackers
@ExceptionHandler(Exception.class)
public ResponseEntity<String> handleError(Exception e) {
    return ResponseEntity.status(500).body(e.getMessage());  // Internal detail!
}

// CORRECT — log internally, return safe message
@ExceptionHandler(Exception.class)
public ResponseEntity<ErrorResponse> handleError(Exception e) {
    log.error("Internal error", e);  // Full detail for internal analysis
    return ResponseEntity.status(500)
        .body(new ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred"));
}
```

---

## Production/Operations Mistakes

### 23. No Heap Limits in Container
```yaml
# WRONG — JVM will try to use all container/host memory
# → Kubernetes OOMKilled without mercy

# CORRECT
resources:
  limits:
    memory: "1Gi"

# AND in Java args:
JAVA_OPTS: "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"
```

### 24. Ignoring Connection Timeouts
```java
// WRONG — hangs indefinitely on slow external service
RestTemplate restTemplate = new RestTemplate();

// CORRECT — always configure timeouts
HttpComponentsClientHttpRequestFactory factory = new HttpComponentsClientHttpRequestFactory();
factory.setConnectTimeout(5000);   // 5s to establish connection
factory.setReadTimeout(30000);     // 30s to read response
RestTemplate restTemplate = new RestTemplate(factory);
```

### 25. No Graceful Shutdown
```yaml
# WRONG — abrupt kill on pod restart → in-flight requests fail
# (no configuration = default abrupt shutdown)

# CORRECT
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

---

## Interview Red Flags (Don't Say These)

```
✗ "I put @Transactional on everything to be safe"
✗ "I use HashMap because it's the most common"
✗ "I don't worry about N+1, the database is fast"
✗ "I always use double for numeric calculations"
✗ "I catch Exception at the top level to handle everything"
✗ "We test in production" (without clarifying intent)
✗ "The API validates the input so I don't need to in the service"
✗ "I use FetchType.EAGER so I always have the data"
✗ "I restart the service when there's a memory leak"
✗ "I disable CSRF because it's annoying"
```

---

*Every mistake in this list represents a real production incident, security breach, or performance degradation that has affected real systems at real companies. Learn from others' mistakes.*

# Section 1: Java Fundamentals

> **Node.js Engineer's Lens:** Java is TypeScript taken to its logical extreme — fully compiled, deeply typed, with a runtime (JVM) that has been battle-hardened for 30 years. If you can write TypeScript confidently, Java syntax will feel familiar within 2 weeks.

---

## 1.1 Java Syntax Basics

### The Compilation Model

```
Node.js:   source.js ──→ V8 JIT ──→ machine code (at runtime)
Java:      source.java ──→ javac ──→ bytecode (.class) ──→ JVM ──→ JIT ──→ machine code
```

Java compiles to **bytecode** (platform-independent), not machine code directly. The JVM interprets and JIT-compiles it at runtime. This is why "write once, run anywhere" is real.

### Hello World — What It Actually Means

```java
public class HelloWorld {           // Every .java file = one public class
    public static void main(String[] args) {  // Entry point (JVM calls this)
        System.out.println("Hello, World!");  // System.out = stdout stream
    }
}
```

**Mapping from Node.js:**
- `public class HelloWorld` → like a named module export
- `public static void main` → like `index.js` entry point
- `System.out.println` → `console.log`
- No semicolons are optional — they are **mandatory**

### The `public static void main` Contract
This is the JVM-defined entry contract. `static` means the JVM calls it without instantiating the class. This is why your Spring Boot apps have:
```java
@SpringBootApplication
public class MyApp {
    public static void main(String[] args) {
        SpringApplication.run(MyApp.class, args);  // Hands off to Spring container
    }
}
```

---

## 1.2 Variables and Data Types

### Primitive Types (Stack-allocated, value semantics)

| Java Type | Size | Range | Node.js Equivalent |
|-----------|------|-------|-------------------|
| `byte` | 8-bit | -128 to 127 | Number (no equiv) |
| `short` | 16-bit | -32768 to 32767 | Number |
| `int` | 32-bit | ~±2.1 billion | Number |
| `long` | 64-bit | ~±9.2 quintillion | BigInt |
| `float` | 32-bit | IEEE 754 | — |
| `double` | 64-bit | IEEE 754 | Number |
| `char` | 16-bit | Unicode char | — |
| `boolean` | — | true/false | Boolean |

**Critical production insight:** In banking systems, **never use `float` or `double` for money**. Use `BigDecimal`:
```java
// WRONG — floating point precision issues
double price = 0.1 + 0.2;  // 0.30000000000000004

// CORRECT — exact decimal arithmetic
BigDecimal price = new BigDecimal("0.1").add(new BigDecimal("0.2"));
// Result: 0.3 (exact)
```

### Reference Types (Heap-allocated, reference semantics)

```java
String name = "Alice";          // Object on heap, variable holds reference
int[] numbers = {1, 2, 3};     // Array object on heap
List<String> list = new ArrayList<>();  // Collection on heap
```

**The `null` problem — Java's billion-dollar mistake:**
```java
String name = null;
name.length();  // NullPointerException — crashes the JVM thread

// Modern Java: Use Optional (like Node's optional chaining but explicit)
Optional<String> safeName = Optional.ofNullable(name);
safeName.map(String::length).orElse(0);  // Returns 0 if null
```

### `var` — Java 10+ Type Inference

```java
var list = new ArrayList<String>();     // Compiler infers ArrayList<String>
var map = new HashMap<String, Integer>(); // Inferred, not dynamic like JS
```

`var` is **still statically typed** — the compiler infers the type at compile time. This is NOT JavaScript's dynamic typing.

### String — More Than You Think

```java
// String is immutable in Java — like Python strings
String s1 = "hello";
String s2 = s1.toUpperCase();  // Returns NEW string, s1 unchanged

// String pool — interning for memory efficiency
String a = "hello";    // Stored in string pool
String b = "hello";    // Reuses same pool object
System.out.println(a == b);       // true (same reference from pool)
System.out.println(a.equals(b));  // true (content comparison)

// ALWAYS use .equals() for string comparison, NEVER ==
String input = getUserInput();  // New String object
input == "expected"            // WRONG — compares references
input.equals("expected")       // CORRECT — compares content
```

**StringBuilder for performance (critical in hot paths):**
```java
// Node.js: strings are immutable, JS engines optimize concatenation
// Java: explicit StringBuilder is required for performance in loops

// WRONG — creates N intermediate string objects in loop
String result = "";
for (int i = 0; i < 10000; i++) {
    result += i;  // Each += creates a new String object
}

// CORRECT
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 10000; i++) {
    sb.append(i);
}
String result = sb.toString();
```

---

## 1.3 Object-Oriented Programming

### Classes and Objects

```java
// Equivalent to a TypeScript class
public class BankAccount {
    // Fields (instance variables) — private by default in good design
    private final String accountId;  // final = cannot be reassigned
    private BigDecimal balance;
    private final String owner;

    // Constructor
    public BankAccount(String accountId, String owner, BigDecimal initialBalance) {
        this.accountId = accountId;
        this.owner = owner;
        this.balance = initialBalance;
    }

    // Method
    public void deposit(BigDecimal amount) {
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Deposit amount must be positive");
        }
        this.balance = this.balance.add(amount);
    }

    // Getter
    public BigDecimal getBalance() {
        return balance;
    }

    // toString — like Node's inspect/toString
    @Override
    public String toString() {
        return String.format("BankAccount{id=%s, owner=%s, balance=%s}",
            accountId, owner, balance);
    }
}
```

### The Four Pillars — Enterprise Application

**1. Encapsulation** — hide implementation details
```java
// Bad: public fields — any code can mutate state
public class Order {
    public List<OrderItem> items;  // Any class can call items.clear()!
}

// Good: controlled access
public class Order {
    private final List<OrderItem> items = new ArrayList<>();

    public void addItem(OrderItem item) {
        validateItem(item);
        items.add(item);
        recalculateTotal();
    }

    public List<OrderItem> getItems() {
        return Collections.unmodifiableList(items);  // Read-only view
    }
}
```

**2. Inheritance** — extend behavior
```java
public abstract class BaseEntity {
    private Long id;
    private Instant createdAt;
    private Instant updatedAt;
    // Common JPA fields — every entity inherits these
}

public class User extends BaseEntity {
    private String email;
    private String passwordHash;
}
```

**3. Polymorphism** — same interface, different behavior
```java
// Strategy pattern — common in enterprise payment systems
public interface PaymentProcessor {
    PaymentResult process(PaymentRequest request);
}

public class StripeProcessor implements PaymentProcessor {
    @Override
    public PaymentResult process(PaymentRequest request) {
        // Stripe-specific implementation
    }
}

public class BraintreeProcessor implements PaymentProcessor {
    @Override
    public PaymentResult process(PaymentRequest request) {
        // Braintree-specific implementation
    }
}

// Runtime polymorphism — client doesn't know which processor
public class PaymentService {
    private final PaymentProcessor processor;  // Injected via Spring DI

    public void processPayment(PaymentRequest request) {
        PaymentResult result = processor.process(request);  // Polymorphic call
    }
}
```

**4. Abstraction** — hide complexity behind contracts

---

## 1.4 Interfaces vs Abstract Classes

This is a frequently tested Java concept:

```
                    Interface                Abstract Class
────────────────────────────────────────────────────────────────
State               No instance state        Can have fields
Constructor         None                     Yes
Multiple inherit    YES (a class can         NO (single extends)
                    implement many)
Default methods     Yes (Java 8+)            Yes
When to use         Define a contract        Share code + state
                    (can-do capability)      (is-a relationship)
```

```java
// Interface — defines a CAPABILITY contract
public interface Auditable {
    void logAccess(String userId, String action);  // abstract by default
    
    default String getAuditPrefix() {  // Default implementation
        return "[AUDIT]";
    }
}

public interface Cacheable {
    String getCacheKey();
    Duration getTTL();
}

// A class can implement BOTH capabilities
public class UserService implements Auditable, Cacheable {
    @Override
    public void logAccess(String userId, String action) { ... }
    
    @Override
    public String getCacheKey() { return "user:" + userId; }
    
    @Override
    public Duration getTTL() { return Duration.ofMinutes(5); }
}

// Abstract class — defines shared state + partial implementation
public abstract class BaseRepository<T, ID> {
    protected final EntityManager em;  // Shared state
    
    public BaseRepository(EntityManager em) {
        this.em = em;
    }
    
    public Optional<T> findById(ID id) {
        // Common implementation all repos share
        return Optional.ofNullable(em.find(getEntityClass(), id));
    }
    
    // Subclasses MUST implement this
    protected abstract Class<T> getEntityClass();
}
```

**Enterprise rule:** In Spring applications, prefer interfaces for service contracts (allows proxying, mocking, multiple implementations). Use abstract classes for shared persistence or utility logic.

---

## 1.5 Collections Framework

### The Hierarchy That Matters

```
Collection
├── List (ordered, allows duplicates)
│   ├── ArrayList    — dynamic array, O(1) get, O(n) insert middle
│   └── LinkedList   — doubly linked, O(1) insert, O(n) get
├── Set (no duplicates)
│   ├── HashSet      — O(1) ops, no order (HashMap internally)
│   ├── LinkedHashSet — preserves insertion order
│   └── TreeSet      — sorted, O(log n) ops (Red-Black tree)
└── Queue/Deque
    ├── ArrayDeque   — fast double-ended queue
    └── PriorityQueue — heap-based, min/max priority

Map (key-value, not Collection)
├── HashMap          — O(1) avg, unordered
├── LinkedHashMap    — insertion-ordered HashMap
├── TreeMap          — sorted by key, O(log n)
└── ConcurrentHashMap — thread-safe HashMap (critical in Java)
```

### Choosing the Right Collection

```java
// ArrayList — default choice for ordered lists
List<Transaction> transactions = new ArrayList<>();

// LinkedList — when you frequently insert/remove at head/tail
Deque<Event> eventQueue = new LinkedList<>();

// HashSet — when uniqueness matters, order doesn't
Set<String> processedEventIds = new HashSet<>();

// LinkedHashMap — LRU cache implementation
Map<String, CachedValue> lruCache = new LinkedHashMap<>(100, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry eldest) {
        return size() > 100;
    }
};

// TreeMap — sorted by key (useful for range queries, leaderboards)
TreeMap<LocalDate, List<Transaction>> txByDate = new TreeMap<>();

// ConcurrentHashMap — multi-threaded environments (NO HashMap in threads!)
ConcurrentHashMap<String, RateLimiter> rateLimiters = new ConcurrentHashMap<>();
```

### Node.js → Java Collections Mapping

```
Node.js Array        →  ArrayList<T>
Node.js Set          →  HashSet<T>
Node.js Map          →  HashMap<K,V>
Node.js Object {}    →  HashMap<String,Object> or a proper DTO class
Node.js Array methods →  Java Streams API
```

---

## 1.6 Streams and Functional Programming

Streams are Java's answer to JavaScript's `.map()`, `.filter()`, `.reduce()`. They are **lazy**, **declarative**, and **pipeline-based**.

### Stream Operations

```java
List<Transaction> transactions = getTransactions();

// Equivalent to:
// transactions
//   .filter(t => t.getAmount() > 1000)
//   .map(t => t.getCustomerId())
//   .filter((v, i, a) => a.indexOf(v) === i)  // distinct
//   .sort()

List<String> highValueCustomers = transactions.stream()
    .filter(t -> t.getAmount().compareTo(new BigDecimal("1000")) > 0)  // filter
    .map(Transaction::getCustomerId)                                     // map
    .distinct()                                                          // dedupe
    .sorted()                                                            // sort
    .collect(Collectors.toList());                                       // terminal

// Group by (like lodash groupBy)
Map<String, List<Transaction>> txByCustomer = transactions.stream()
    .collect(Collectors.groupingBy(Transaction::getCustomerId));

// Aggregate
BigDecimal totalVolume = transactions.stream()
    .map(Transaction::getAmount)
    .reduce(BigDecimal.ZERO, BigDecimal::add);

// Statistics
DoubleSummaryStatistics stats = transactions.stream()
    .mapToDouble(t -> t.getAmount().doubleValue())
    .summaryStatistics();
// stats.getAverage(), stats.getMax(), stats.getCount()

// Parallel processing (use carefully — has overhead for small lists)
long count = transactions.parallelStream()
    .filter(t -> t.isHighRisk())
    .count();
```

### Lazy Evaluation — Why It Matters

```java
// Streams are LAZY — intermediate operations don't execute until terminal
Stream<Transaction> stream = transactions.stream()
    .filter(t -> {
        System.out.println("filtering: " + t.getId()); // Won't print yet
        return t.getAmount().compareTo(BigDecimal.ZERO) > 0;
    })
    .map(t -> {
        System.out.println("mapping: " + t.getId()); // Won't print yet
        return t;
    });

// Terminal operation triggers execution
stream.findFirst();  // Only processes until first match!
```

**Production insight:** Use `Stream.of(...)` or `.stream()` for in-memory processing. For large datasets, never load everything into memory — use database cursors or `JdbcTemplate.queryForStream()`.

---

## 1.7 Lambda Expressions

```java
// Syntax: (parameters) -> expression  OR  (parameters) -> { statements }

// Node.js: (x) => x * 2
// Java:
Function<Integer, Integer> doubler = x -> x * 2;

// Node.js: (a, b) => a + b
BinaryOperator<Integer> add = (a, b) -> a + b;

// Multi-line
Predicate<String> isValidEmail = email -> {
    if (email == null || email.isEmpty()) return false;
    return email.contains("@") && email.contains(".");
};

// Method references (cleaner than lambdas when method already exists)
// Node.js: arr.map(x => x.toString()) → Java:
List<String> strings = numbers.stream()
    .map(Object::toString)       // instance method
    .collect(Collectors.toList());

List<String> upper = strings.stream()
    .map(String::toUpperCase)    // unbound instance method
    .collect(Collectors.toList());

// Static method reference
.filter(Objects::nonNull)        // Objects.nonNull(x)

// Constructor reference
.map(User::new)                  // new User(x)
```

### Functional Interfaces

```java
// The four core functional interfaces
Function<T, R>       — takes T, returns R (map)
Predicate<T>         — takes T, returns boolean (filter)
Consumer<T>          — takes T, returns void (forEach)
Supplier<T>          — takes nothing, returns T (lazy init)

// Common usage
Function<String, Integer> parser = Integer::parseInt;
Predicate<User> isAdmin = user -> user.hasRole("ADMIN");
Consumer<Event> logger = event -> log.info("Event: {}", event);
Supplier<UUID> idGenerator = UUID::randomUUID;
```

---

## 1.8 Exception Handling

### Checked vs Unchecked — A Critical Java Distinction

```
Throwable
├── Error (JVM-level: OutOfMemoryError, StackOverflowError) — don't catch
└── Exception
    ├── RuntimeException (UNCHECKED — no throws declaration required)
    │   ├── NullPointerException
    │   ├── IllegalArgumentException
    │   ├── IllegalStateException
    │   └── (your custom runtime exceptions)
    └── IOException, SQLException, etc. (CHECKED — must declare or catch)
```

```java
// CHECKED exception — must handle or declare
public void readFile(String path) throws IOException {
    // If you don't catch it, you must declare throws
    Files.readAllBytes(Paths.get(path));
}

// UNCHECKED exception — runtime, no declaration needed
public User findUser(String id) {
    User user = repo.findById(id);
    if (user == null) {
        throw new UserNotFoundException("User not found: " + id);  // RuntimeException
    }
    return user;
}

// Try-with-resources (ALWAYS use for I/O, DB connections)
try (Connection conn = dataSource.getConnection();
     PreparedStatement stmt = conn.prepareStatement(sql)) {
    // Resources auto-closed even if exception thrown
    return stmt.executeQuery();
} catch (SQLException e) {
    log.error("DB error on query: {}", sql, e);
    throw new DataAccessException("Failed to execute query", e);  // Wrap and rethrow
}
```

### Custom Exception Hierarchy — Enterprise Pattern

```java
// Base application exception
public class AppException extends RuntimeException {
    private final ErrorCode errorCode;
    private final String correlationId;

    public AppException(ErrorCode errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
        this.correlationId = MDC.get("correlationId");  // From logging context
    }
}

// Domain-specific exceptions
public class InsufficientFundsException extends AppException {
    private final BigDecimal requested;
    private final BigDecimal available;

    public InsufficientFundsException(BigDecimal requested, BigDecimal available) {
        super(ErrorCode.INSUFFICIENT_FUNDS,
              String.format("Requested %.2f but only %.2f available", requested, available));
        this.requested = requested;
        this.available = available;
    }
}

// Spring exception handler — maps exceptions to HTTP responses
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(InsufficientFundsException.class)
    public ResponseEntity<ErrorResponse> handleInsufficientFunds(InsufficientFundsException ex) {
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
            .body(new ErrorResponse(ex.getErrorCode(), ex.getMessage()));
    }
}
```

---

## 1.9 Generics

Generics are like TypeScript generics — compile-time type safety:

```java
// Generic class
public class ApiResponse<T> {
    private final T data;
    private final String requestId;
    private final Instant timestamp;

    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(data, generateRequestId(), Instant.now());
    }
}

// Usage
ApiResponse<User> userResponse = ApiResponse.success(user);
ApiResponse<List<Transaction>> listResponse = ApiResponse.success(transactions);

// Bounded type parameters
public <T extends Comparable<T>> T findMax(List<T> list) {
    return list.stream().max(Comparator.naturalOrder()).orElseThrow();
}

// Wildcards
public void printAll(List<? extends Shape> shapes) {
    shapes.forEach(s -> System.out.println(s.area()));  // PECS: producer extends
}

public void addToList(List<? super Integer> list) {
    list.add(42);  // PECS: consumer super
}
```

**Type erasure — the key JVM concept:** Generic types are erased at runtime. `List<String>` and `List<Integer>` are both `List` at the bytecode level. This affects reflection and some serialization patterns.

---

## 1.10 Enums

Java enums are far more powerful than TypeScript enums:

```java
// Simple enum
public enum TransactionStatus {
    PENDING, PROCESSING, COMPLETED, FAILED, REVERSED
}

// Enum with fields and methods (very common in enterprise code)
public enum PaymentMethod {
    CREDIT_CARD("CC", true, 0.029),
    DEBIT_CARD("DC", true, 0.01),
    BANK_TRANSFER("BT", false, 0.0),
    CRYPTO("CRYPTO", false, 0.001);

    private final String code;
    private final boolean requiresCVV;
    private final double feeRate;

    PaymentMethod(String code, boolean requiresCVV, double feeRate) {
        this.code = code;
        this.requiresCVV = requiresCVV;
        this.feeRate = feeRate;
    }

    public BigDecimal calculateFee(BigDecimal amount) {
        return amount.multiply(BigDecimal.valueOf(feeRate));
    }

    // Factory method pattern with enum
    public static PaymentMethod fromCode(String code) {
        return Arrays.stream(values())
            .filter(pm -> pm.code.equals(code))
            .findFirst()
            .orElseThrow(() -> new IllegalArgumentException("Unknown code: " + code));
    }
}

// Usage
PaymentMethod method = PaymentMethod.CREDIT_CARD;
BigDecimal fee = method.calculateFee(new BigDecimal("100.00")); // 2.90
```

---

## 1.11 Annotations

Annotations are metadata decorators (like TypeScript decorators, but baked into the language):

```java
// Built-in annotations
@Override           // Compiler check: must override parent method
@Deprecated         // Marks API as deprecated
@SuppressWarnings   // Suppress compiler warnings
@FunctionalInterface // Marks interface as having single abstract method

// Spring annotations (most common in enterprise code)
@Component          // Register as Spring bean
@Service            // Semantic: business logic layer
@Repository         // Semantic: data access layer + exception translation
@Controller/@RestController  // HTTP endpoint handler
@Autowired          // Inject dependency
@Value("${prop}")   // Inject property value
@Transactional      // Wrap in database transaction
@Cacheable          // Cache method result
@Async              // Execute in thread pool
@Scheduled          // Cron/fixed-rate scheduling

// Custom annotation example
@Target(ElementType.METHOD)           // Can be applied to methods
@Retention(RetentionPolicy.RUNTIME)   // Available at runtime via reflection
@Documented
public @interface AuditLog {
    String action();
    String resource() default "";
}

// Usage
@AuditLog(action = "TRANSFER", resource = "account")
public void transfer(String fromId, String toId, BigDecimal amount) {
    // Spring AOP intercepts this call and logs the audit
}
```

---

## 1.12 Records — Modern Java (Java 16+)

Records are immutable data carriers — like TypeScript interfaces with auto-generated constructors:

```java
// Java 16+: Records (immutable DTOs)
public record TransferRequest(
    String fromAccountId,
    String toAccountId,
    BigDecimal amount,
    String currency,
    String description
) {
    // Compact constructor for validation
    public TransferRequest {
        Objects.requireNonNull(fromAccountId, "fromAccountId required");
        Objects.requireNonNull(toAccountId, "toAccountId required");
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
    }
}

// Auto-generated: constructor, getters, equals, hashCode, toString
TransferRequest req = new TransferRequest("ACC-1", "ACC-2",
    new BigDecimal("500.00"), "USD", "Rent payment");
req.amount(); // BigDecimal(500.00) — getter named after field, not getAmount()
```

---

## 1.13 Sealed Classes — Modern Java (Java 17+)

```java
// Like TypeScript discriminated unions
public sealed interface Shape
    permits Circle, Rectangle, Triangle {
}

public record Circle(double radius) implements Shape {}
public record Rectangle(double width, double height) implements Shape {}
public record Triangle(double base, double height) implements Shape {}

// Pattern matching switch (Java 21)
double area = switch (shape) {
    case Circle c -> Math.PI * c.radius() * c.radius();
    case Rectangle r -> r.width() * r.height();
    case Triangle t -> 0.5 * t.base() * t.height();
};
```

---

## 1.14 Key Syntax Reference

```java
// Variable declaration
int count = 0;
final String NAME = "constant";  // final = const in JS
var list = new ArrayList<String>();

// Control flow
if (condition) { } else if (other) { } else { }

// Enhanced for loop (like JS for...of)
for (String item : collection) { }

// Traditional for
for (int i = 0; i < n; i++) { }

// While
while (condition) { }

// Switch expression (Java 14+)
String result = switch (status) {
    case PENDING -> "Waiting";
    case COMPLETED -> "Done";
    default -> "Unknown";
};

// Ternary
String label = isActive ? "Active" : "Inactive";

// String formatting
String msg = "User %s has balance %,.2f".formatted(name, balance); // Java 15+
String msg2 = String.format("User %s has balance %,.2f", name, balance);

// Text blocks (Java 15+) — like template literals
String json = """
    {
        "name": "%s",
        "amount": %s
    }
    """.formatted(name, amount);

// Null safety
String result = Optional.ofNullable(getValue())
    .map(String::trim)
    .filter(s -> !s.isEmpty())
    .orElse("default");

// instanceof pattern matching (Java 16+)
if (obj instanceof String s) {
    System.out.println(s.toUpperCase()); // s already cast
}
```

---

## Section Summary: What Matters for Interviews

**FAANG interviewers expect:**
- Fluent Java syntax (no Googling basics)
- Deep understanding of generics and type erasure
- Collections API mastery (choosing the right data structure)
- Streams for data processing problems
- Exception hierarchy and checked vs unchecked

**Bank interviewers additionally ask:**
- BigDecimal for monetary calculations
- Null safety strategies (Optional, annotations)
- Custom exception hierarchies
- Annotation-driven enterprise patterns

**What to practice:**
1. Rewrite 5 of your Node.js utility functions in Java
2. Use Streams to solve 10 LeetCode array problems
3. Design a custom exception hierarchy for a payment system
4. Build a generic `Repository<T, ID>` interface

# Java Syntax Cheatsheet
## Quick Reference for Node.js Engineers

---

## Variables & Types

```java
// Primitives (stack)
int count = 0;
long bigCount = 10_000_000_000L;  // L suffix for long
double price = 9.99;
boolean active = true;
char letter = 'A';

// Reference types (heap)
String name = "Alice";
Integer boxed = 42;                    // Autoboxed int
BigDecimal money = new BigDecimal("100.00"); // ALWAYS for money

// Constants
static final int MAX_RETRIES = 3;      // Convention: SCREAMING_SNAKE_CASE

// Type inference (Java 10+)
var list = new ArrayList<String>();
var map = new HashMap<String, Integer>();

// Null safety
String value = null;
Optional<String> safe = Optional.ofNullable(value);
String result = safe.orElse("default");
String orThrow = safe.orElseThrow(() -> new IllegalStateException("missing"));
```

---

## Control Flow

```java
// If-else
if (x > 0) {
    // positive
} else if (x < 0) {
    // negative
} else {
    // zero
}

// Switch expression (Java 14+)
String label = switch (status) {
    case PENDING   -> "Waiting";
    case ACTIVE    -> "Running";
    case COMPLETED -> "Done";
    default        -> "Unknown";
};

// Pattern switch (Java 21)
String describe = switch (obj) {
    case Integer i   -> "int: " + i;
    case String s    -> "string: " + s;
    case null        -> "null";
    default          -> "other";
};

// Ternary
String type = amount > 1000 ? "large" : "small";

// For loops
for (int i = 0; i < 10; i++) { }           // traditional
for (String item : collection) { }          // enhanced for (like for...of)
collection.forEach(item -> process(item));   // functional

// While / Do-while
while (condition) { }
do { } while (condition);

// Try-catch-finally
try {
    riskyOperation();
} catch (SpecificException e) {
    handle(e);
} catch (IOException | SQLException e) {  // Multi-catch
    handleMultiple(e);
} finally {
    cleanup();  // Always runs
}

// Try-with-resources (auto-close)
try (InputStream is = new FileInputStream(file);
     BufferedReader br = new BufferedReader(new InputStreamReader(is))) {
    return br.readLine();
}
```

---

## Classes & Objects

```java
// Class definition
public class PaymentService {
    // Fields
    private final PaymentRepository repo;   // final = assigned once
    private static final Logger log = LoggerFactory.getLogger(PaymentService.class);

    // Constructor
    public PaymentService(PaymentRepository repo) {
        this.repo = repo;
    }

    // Method
    public Payment createPayment(BigDecimal amount) {
        // ...
        return payment;
    }

    // Static method
    public static String generateId() {
        return UUID.randomUUID().toString();
    }
}

// Interfaces
public interface Auditable {
    void audit(String action);

    default String prefix() {   // Default method (Java 8+)
        return "[AUDIT]";
    }
}

// Abstract class
public abstract class BaseService {
    protected final Logger log = LoggerFactory.getLogger(getClass());

    protected abstract String getServiceName(); // Must implement

    public void logStart() {
        log.info("Starting {}", getServiceName());
    }
}

// Records (Java 16+) — immutable data carriers
public record TransferRequest(
    String fromId,
    String toId,
    BigDecimal amount
) {}

// Enums
public enum Status {
    PENDING("P"), ACTIVE("A"), CLOSED("C");

    private final String code;
    Status(String code) { this.code = code; }
    public String getCode() { return code; }
}
```

---

## Generics

```java
// Generic class
public class Pair<A, B> {
    private final A first;
    private final B second;
    // ...
}

// Generic method
public <T> Optional<T> findFirst(List<T> items, Predicate<T> filter) {
    return items.stream().filter(filter).findFirst();
}

// Bounded types
public <T extends Comparable<T>> T max(List<T> items) {
    return items.stream().max(Comparator.naturalOrder()).orElseThrow();
}

// Wildcards
void processAll(List<? extends Animal> animals) { }  // Producer Extends
void addToList(List<? super Cat> list) { }            // Consumer Super
```

---

## Collections

```java
// List
List<String> list = new ArrayList<>();         // mutable
List<String> immutable = List.of("a", "b");    // immutable (Java 9+)
list.add("x");
list.get(0);
list.remove("x");
list.size();
list.contains("x");
list.sort(Comparator.naturalOrder());

// Map
Map<String, Integer> map = new HashMap<>();
map.put("key", 1);
map.get("key");                                // Returns null if missing
map.getOrDefault("key", 0);                   // Safe default
map.putIfAbsent("key", 0);
map.computeIfAbsent("key", k -> new ArrayList<>());
map.entrySet().forEach(e -> process(e.getKey(), e.getValue()));
Map<String, Integer> immutableMap = Map.of("a", 1, "b", 2);  // Java 9+

// Set
Set<String> set = new HashSet<>();
set.add("x");
set.contains("x");
set.remove("x");

// Queue / Stack
Deque<String> deque = new ArrayDeque<>();
deque.push("first");    // Stack: push to front
deque.pop();            // Stack: pop from front
deque.offer("last");    // Queue: add to back
deque.poll();           // Queue: remove from front
```

---

## Streams

```java
List<Transaction> txns = getTransactions();

// Filter + Map + Collect
List<String> ids = txns.stream()
    .filter(t -> t.getAmount().compareTo(BigDecimal.ZERO) > 0)
    .map(Transaction::getId)
    .collect(Collectors.toList());  // Or .toList() in Java 16+

// Reduce
BigDecimal total = txns.stream()
    .map(Transaction::getAmount)
    .reduce(BigDecimal.ZERO, BigDecimal::add);

// Group by
Map<String, List<Transaction>> byStatus = txns.stream()
    .collect(Collectors.groupingBy(t -> t.getStatus().name()));

// Count / Sum / Average
long count = txns.stream().filter(t -> t.isHighRisk()).count();
double avg = txns.stream().mapToDouble(t -> t.getAmount().doubleValue()).average().orElse(0);

// FlatMap (flatten nested lists)
List<OrderItem> allItems = orders.stream()
    .flatMap(order -> order.getItems().stream())
    .collect(Collectors.toList());

// Distinct / Sorted / Limit / Skip
List<String> unique = txns.stream()
    .map(Transaction::getCategory)
    .distinct()
    .sorted()
    .limit(10)
    .collect(Collectors.toList());

// anyMatch / allMatch / noneMatch
boolean hasLarge = txns.stream().anyMatch(t -> t.getAmount().compareTo(largeThreshold) > 0);

// findFirst / findAny
Optional<Transaction> first = txns.stream().filter(Transaction::isPending).findFirst();
```

---

## Functional Interfaces

```java
// The core four
Function<String, Integer>   parser = Integer::parseInt;         // T → R
Predicate<String>           isEmpty = String::isEmpty;          // T → boolean
Consumer<String>            printer = System.out::println;      // T → void
Supplier<UUID>              idGen = UUID::randomUUID;           // () → T

// Composing
Function<String, Integer> parseAndDouble = parser.andThen(n -> n * 2);
Predicate<String> notBlank = isEmpty.negate().and(s -> !s.isBlank());

// BiFunction, BiPredicate, BiConsumer
BiFunction<String, Integer, String> repeat = String::repeat;
```

---

## Lambdas & Method References

```java
// Lambda forms
Runnable r1 = () -> System.out.println("Hello");
Runnable r2 = () -> {
    System.out.println("Line 1");
    System.out.println("Line 2");
};

// Method references
// Static:    ClassName::staticMethod
// Instance:  instance::method  OR  ClassName::instanceMethod
// Constructor: ClassName::new

Function<String, Integer> parse = Integer::parseInt;      // static
Consumer<String> log = logger::info;                      // instance
Supplier<List<String>> factory = ArrayList::new;          // constructor
```

---

## String Operations

```java
String s = "  Hello, World!  ";

s.trim()                           // Remove whitespace
s.strip()                          // Unicode-aware trim (Java 11+)
s.toLowerCase() / s.toUpperCase()
s.contains("World")
s.startsWith("Hello")
s.endsWith("!")
s.indexOf("World")                 // -1 if not found
s.substring(7, 12)                 // "World"
s.replace("World", "Java")
s.split(",")                       // String[] {"  Hello", " World!  "}
s.split(",", 2)                    // Limit splits
s.isEmpty() / s.isBlank()         // "" vs "   "
s.formatted("name=%s age=%d", name, age) // Java 15+
s.chars()                          // IntStream of char codes

// Join
String joined = String.join(", ", list);
String joined2 = list.stream().collect(Collectors.joining(", "));

// StringBuilder
StringBuilder sb = new StringBuilder();
sb.append("Hello").append(", ").append("World");
String result = sb.toString();

// Text block (Java 15+)
String json = """
    {
        "name": "%s"
    }
    """.formatted(name);
```

---

## Annotations Reference

```java
// Core Java
@Override              // Must override superclass method
@Deprecated            // Mark as deprecated (use @since in Javadoc)
@SuppressWarnings      // Suppress compiler warning
@FunctionalInterface   // Single abstract method interface

// Spring
@SpringBootApplication // Main app entry point
@Component             // Generic Spring bean
@Service               // Business logic bean
@Repository            // Data access bean (+ exception translation)
@RestController        // HTTP controller (includes @Controller + @ResponseBody)
@RequestMapping        // Map HTTP requests
@GetMapping @PostMapping @PutMapping @DeleteMapping @PatchMapping
@PathVariable          // URL path variable
@RequestParam          // Query parameter
@RequestBody           // Deserialize request body
@RequestHeader         // HTTP header
@ResponseStatus        // Set response HTTP status
@Autowired             // Inject dependency (prefer constructor injection)
@Value("${prop}")      // Inject property value
@Configuration         // Spring configuration class
@Bean                  // Define a Spring bean
@Transactional         // Wrap in database transaction
@Cacheable / @CacheEvict / @CachePut  // Cache operations
@Async                 // Execute asynchronously
@Scheduled             // Scheduled task
@Valid / @Validated    // Trigger validation
@ConditionalOnProperty // Conditional bean creation

// JPA / Hibernate
@Entity                // JPA entity (maps to table)
@Table(name = "...")   // Specify table name
@Id                    // Primary key
@GeneratedValue        // Auto-generate ID
@Column                // Column mapping
@OneToMany / @ManyToOne / @OneToOne / @ManyToMany
@JoinColumn            // Foreign key column
@Transient             // Not persisted to DB
@Version               // Optimistic locking version
@Enumerated(STRING)    // Store enum as string
@CreatedDate / @LastModifiedDate  // Audit timestamps

// Validation
@NotNull @NotBlank @NotEmpty
@Size(min, max)
@Min @Max @DecimalMin @DecimalMax
@Email @Pattern(regexp)
@Positive @PositiveOrZero @Negative
@Past @Future @FutureOrPresent
```

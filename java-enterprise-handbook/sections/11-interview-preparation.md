# Section 11: Interview Preparation

> **Elite Performance:** FAANG and top banks don't just test knowledge — they test how you think, communicate, and handle ambiguity. This section gives you the exact preparation strategy, question banks, and mental models to perform at the highest level.

---

## 11.1 DSA for Experienced Engineers

### The Right Mindset

You are interviewing as a senior engineer. Companies expect:
- LeetCode Medium fluency (< 20 minutes)
- LeetCode Hard recognition (explain approach even if not fully coded)
- Optimal time/space complexity
- Clean, readable code (not just working code)
- Edge case awareness
- Code review quality

### Data Structures You Must Know Cold

```java
// 1. HashMap patterns — constant time lookups
// "Two Sum" pattern applied to finance: find pairs of transactions summing to X
public int[] twoSum(int[] nums, int target) {
    Map<Integer, Integer> seen = new HashMap<>();
    for (int i = 0; i < nums.length; i++) {
        int complement = target - nums[i];
        if (seen.containsKey(complement)) {
            return new int[]{seen.get(complement), i};
        }
        seen.put(nums[i], i);
    }
    return new int[]{};
}

// 2. Sliding Window — rate limiting, moving averages
// "Max sum of K consecutive elements"
public int maxSumWindow(int[] arr, int k) {
    int sum = 0;
    for (int i = 0; i < k; i++) sum += arr[i];
    int maxSum = sum;
    for (int i = k; i < arr.length; i++) {
        sum += arr[i] - arr[i - k];
        maxSum = Math.max(maxSum, sum);
    }
    return maxSum;
}

// 3. Stack — expression evaluation, bracket matching
// Applied in: query parsers, undo/redo systems
public boolean isValidBrackets(String s) {
    Deque<Character> stack = new ArrayDeque<>();
    Map<Character, Character> pairs = Map.of(')', '(', ']', '[', '}', '{');
    for (char c : s.toCharArray()) {
        if ("([{".indexOf(c) >= 0) {
            stack.push(c);
        } else {
            if (stack.isEmpty() || stack.pop() != pairs.get(c)) return false;
        }
    }
    return stack.isEmpty();
}

// 4. BFS/DFS — dependency graphs, permission trees, graph traversal
// Applied in: permission hierarchy, dependency resolution
public List<Integer> topologicalSort(int n, int[][] edges) {
    Map<Integer, List<Integer>> graph = new HashMap<>();
    int[] inDegree = new int[n];
    for (int[] edge : edges) {
        graph.computeIfAbsent(edge[0], k -> new ArrayList<>()).add(edge[1]);
        inDegree[edge[1]]++;
    }
    Queue<Integer> queue = new LinkedList<>();
    for (int i = 0; i < n; i++) {
        if (inDegree[i] == 0) queue.offer(i);
    }
    List<Integer> result = new ArrayList<>();
    while (!queue.isEmpty()) {
        int node = queue.poll();
        result.add(node);
        for (int neighbor : graph.getOrDefault(node, List.of())) {
            if (--inDegree[neighbor] == 0) queue.offer(neighbor);
        }
    }
    return result.size() == n ? result : List.of();  // Empty = cycle detected
}

// 5. Binary Search — O(log n) search in sorted data
// Applied in: finding transaction in sorted timeline, search optimization
public int binarySearch(int[] arr, int target) {
    int left = 0, right = arr.length - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;  // Avoid overflow
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

// 6. Dynamic Programming — optimization problems
// Applied in: resource scheduling, rate optimization
public int maxProfit(int[] prices) {  // LeetCode 121 — Buy/Sell Stock
    int minPrice = Integer.MAX_VALUE, maxProfit = 0;
    for (int price : prices) {
        minPrice = Math.min(minPrice, price);
        maxProfit = Math.max(maxProfit, price - minPrice);
    }
    return maxProfit;
}
```

### Top 20 Patterns — Recognize → Solve

```
1. Two Pointers        → Sorted arrays, palindrome, remove duplicates
2. Sliding Window      → Subarray problems, moving window
3. HashMap/HashSet     → Frequency counting, deduplication, O(1) lookup
4. Stack               → Balanced brackets, next greater element, monotonic
5. Queue/BFS           → Level-order traversal, shortest path
6. DFS/Recursion       → Tree problems, backtracking
7. Binary Search       → Sorted array search, search space reduction
8. Merge Sort / Sort   → Interval merging, K sorted arrays
9. Heap/PriorityQueue  → K largest/smallest, merge K lists
10. Dynamic Programming → Optimal substructure, memoization
11. Graph (BFS/DFS)    → Connected components, shortest path, cycle detection
12. Union-Find         → Connected components, network connectivity
13. Trie               → Prefix search, word problems
14. Bit Manipulation   → Single number, counting bits, XOR tricks
15. Greedy             → Activity selection, interval scheduling
16. Backtracking       → Permutations, combinations, N-Queens
17. Divide & Conquer   → Merge sort, binary search variants
18. Tree Traversal     → Inorder/preorder/postorder patterns
19. String Manipulation → Substring, pattern matching, anagram
20. Math               → Modular arithmetic, prime numbers, GCD
```

---

## 11.2 Java Interview Questions

### Core Java

**Q: What is the difference between `==` and `.equals()` in Java?**

`==` compares references (memory addresses). `.equals()` compares content. For `String`, `Integer` (cached -128 to 127), always use `.equals()`. For `null` check, use `==`.

**Q: Explain the contract between `equals()` and `hashCode()`.**

If `a.equals(b)` is true, then `a.hashCode()` must equal `b.hashCode()`. The reverse is not required. Violating this breaks HashMap/HashSet behavior.

**Q: What is the difference between `HashMap`, `LinkedHashMap`, and `TreeMap`?**

`HashMap`: Unordered, O(1) average. `LinkedHashMap`: Insertion-ordered, O(1). `TreeMap`: Sorted by key, O(log n). Java 8+ HashMap uses trie-based buckets (TreeMap structure) for buckets with > 8 entries.

**Q: What are the different ways to create a thread in Java? Which is preferred?**

`Thread` subclass, `Runnable` lambda, `ExecutorService` (preferred). Raw thread creation in production is an anti-pattern. Use `ThreadPoolExecutor` or Spring's `@Async`.

**Q: Explain `volatile` vs `synchronized`.**

`volatile`: Guarantees visibility (reads/writes directly to main memory, not CPU cache). Does NOT guarantee atomicity for compound operations. `synchronized`: Guarantees both visibility AND atomicity (mutual exclusion). Use `volatile` for simple flag variables; `synchronized` or `AtomicXxx` for compound operations.

**Q: What is `Comparable` vs `Comparator`?**

`Comparable`: Object's natural ordering (implements `compareTo`). Used by `TreeMap`/`TreeSet` by default. `Comparator`: External comparison strategy. Used when you need multiple sort orderings or can't modify the class.

---

## 11.3 Spring Interview Questions

**Q: How does Spring dependency injection work internally?**

Spring creates a `BeanFactory` (or `ApplicationContext`). At startup, it scans for `@Component`, `@Bean`, `@Configuration`. It creates `BeanDefinition` objects describing each bean. Then it instantiates beans, resolves constructor/setter dependencies, applies `BeanPostProcessor`s (where AOP proxies are created), calls `@PostConstruct` methods, and marks beans as ready.

**Q: What is the difference between `@Component`, `@Service`, `@Repository`, and `@Controller`?**

All four are `@Component` specializations — functionally equivalent for DI purposes. The semantic difference: `@Repository` enables exception translation (converts SQL exceptions to Spring DataAccessException). `@Service`, `@Controller` are documentation/tooling hints. Use them consistently for code clarity.

**Q: Explain the `@Transactional` pitfalls.**

1. **Self-invocation:** Calling `@Transactional` method from same class bypasses proxy — no transaction.
2. **Visibility:** `@Transactional` on private methods is silently ignored.
3. **Rollback rules:** By default, only `RuntimeException` rolls back (not checked exceptions).
4. **Propagation:** `REQUIRES_NEW` suspends outer transaction — completely separate transaction.
5. **Isolation levels:** Higher isolation = more locking = lower throughput.

**Q: What is Spring AOP and how does it work?**

Spring AOP creates proxy objects around beans (JDK dynamic proxy for interface-based or CGLIB subclass proxy). Method calls go through the proxy, which checks for applicable advice (Before, After, Around, AfterReturning, AfterThrowing). `@Transactional`, `@Cacheable`, `@Async`, `@Retryable` all use AOP.

**Q: How does Spring Boot autoconfiguration work?**

Spring Boot reads `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (or `spring.factories` in older versions). These are `@Configuration` classes with `@ConditionalOnClass`, `@ConditionalOnMissingBean` conditions. Example: `DataSourceAutoConfiguration` activates only if `DataSource` class is on classpath and no `DataSource` bean is already defined.

---

## 11.4 LLD (Low-Level Design) Questions

### Design a Thread-Safe LRU Cache

```java
// LRU Cache: O(1) get and put
// Data structure: HashMap + Doubly Linked List
public class LRUCache<K, V> {
    private final int capacity;
    private final Map<K, Node<K, V>> map = new LinkedHashMap<>() {
        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > capacity;
        }
    };

    // Thread-safe version
    private final Map<K, V> cache = Collections.synchronizedMap(
        new LinkedHashMap<>(16, 0.75f, true) {
            @Override
            protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
                return size() > capacity;
            }
        }
    );

    // Better: Caffeine (production-grade caching library)
    // Caffeine.newBuilder()
    //     .maximumSize(1000)
    //     .expireAfterWrite(5, MINUTES)
    //     .recordStats()
    //     .build()
}
```

### Design a Rate Limiter

```java
// Token Bucket Algorithm
public class TokenBucketRateLimiter {
    private final long capacity;
    private final long refillRate;       // tokens per second
    private AtomicLong tokens;
    private volatile long lastRefillTime;

    public synchronized boolean tryAcquire() {
        refill();
        if (tokens.get() > 0) {
            tokens.decrementAndGet();
            return true;
        }
        return false;
    }

    private void refill() {
        long now = System.currentTimeMillis();
        long elapsed = now - lastRefillTime;
        long tokensToAdd = elapsed * refillRate / 1000;
        if (tokensToAdd > 0) {
            tokens.set(Math.min(capacity, tokens.get() + tokensToAdd));
            lastRefillTime = now;
        }
    }
}

// Sliding Window Counter
public class SlidingWindowRateLimiter {
    private final Deque<Long> timestamps = new ArrayDeque<>();
    private final int maxRequests;
    private final long windowMs;

    public synchronized boolean isAllowed() {
        long now = System.currentTimeMillis();
        // Remove timestamps outside window
        while (!timestamps.isEmpty() && timestamps.peekFirst() <= now - windowMs) {
            timestamps.pollFirst();
        }
        if (timestamps.size() < maxRequests) {
            timestamps.addLast(now);
            return true;
        }
        return false;
    }
}
```

### Design Patterns — Must Know for LLD

```
Creational:
  Singleton   → Spring beans (ApplicationContext manages)
  Factory     → PaymentProcessorFactory.create(type)
  Builder     → Request/Response objects, complex configs
  Prototype   → Clone-able entities

Structural:
  Decorator   → Logging wrapper, cache wrapper around service
  Adapter     → Integrate legacy system with new interface
  Facade      → Simplify complex subsystem (PaymentFacade → multiple services)
  Proxy       → Spring AOP, lazy loading, access control

Behavioral:
  Strategy    → PaymentStrategy (Stripe/Braintree/PayPal)
  Observer    → Event publishing (ApplicationEventPublisher)
  Template Method → BaseService with abstract processBusiness()
  Command     → Undo/redo, queued operations
  Chain of Responsibility → Filter chain, validation pipeline
```

---

## 11.5 HLD (High-Level Design) Questions

### Framework for Any Design Question

```
1. Understand the problem
   → What are we building? Who uses it?
   → Scale: users, requests per second, data volume
   → Consistency requirements: strong vs eventual
   → Availability: 99.9%? 99.99%?

2. Define the API
   → REST endpoints or events
   → Request/Response contracts

3. High-level components
   → Draw the boxes: clients, API gateway, services, databases, queues
   → Draw the data flows between components

4. Data model
   → Key entities and relationships
   → Which database type? SQL vs NoSQL rationale

5. Scale and deep dive
   → Where are the bottlenecks?
   → Caching strategy
   → Scaling strategy (horizontal, sharding, read replicas)
   → Failure scenarios and mitigation

6. Trade-offs
   → What did you optimize for? What did you sacrifice?
   → What would you do differently at 10x scale?
```

---

## 11.6 Behavioral Interview — STAR Method

### FAANG Behavioral Principles (Amazon LPs)

```
Ownership:         "Tell me about a time you took ownership beyond your role"
Dive Deep:         "Tell me about a production incident you debugged"
Bias for Action:   "When did you make a decision with insufficient data?"
Disagree+Commit:   "When did you push back on a technical decision?"
Customer Obsession:"How did you build something users actually needed?"
Invent+Simplify:   "When did you simplify a complex system?"
Think Big:         "Describe a long-term architectural vision you drove"
Deliver Results:   "Most impactful technical contribution in your career"
```

### STAR Format

```
Situation: Set the context (team size, scale, company stage)
Task:      What was your specific responsibility?
Action:    What did YOU specifically do? (Use "I", not "we")
Result:    Quantifiable outcome (latency, uptime, cost, velocity)

Example: "Production incident response"

Situation: Our payment service was dropping 5% of transactions 
           at 3 AM on a Friday. High-severity P0 incident.
           
Task:      I was on-call. My responsibility: diagnose and resolve 
           within our 30-minute SLA.
           
Action:    I pulled thread dumps and found all HTTP handler threads 
           BLOCKED waiting for HikariCP connections. 
           Checked metrics: DB connection pool 100% utilized.
           Found a new query without an index doing full table scans,
           holding connections for 30+ seconds.
           Added the index (online, no lock), deployed in 12 minutes.
           
Result:    Error rate dropped to 0% within 2 minutes of index creation.
           Implemented automated slow query alerting to prevent recurrence.
           P99 latency improved 40% as bonus from the index.
```

---

## 11.7 Real FAANG-Level Expectations

### What "Senior" Means at Google/Amazon/Stripe

```
Junior → Senior → Staff → Principal

At Senior level (L5 Google, SDE2 Amazon, Senior Stripe):
- Design and implement features independently
- Identify technical risks and mitigation strategies
- Mentor junior engineers
- Make architectural decisions for your service
- On-call: diagnose and resolve incidents
- Code review: spot security, performance, correctness issues

Interview signal they're looking for:
- Do you think beyond the happy path?
- Do you consider scale without being asked?
- Do you ask clarifying questions or make assumptions?
- Can you communicate trade-offs clearly?
- Do you write code like it's going to production?
```

### Code Quality Standards in Interviews

```java
// Mediocre (gets functional credit):
public List<Integer> findDups(List<Integer> list) {
    List<Integer> result = new ArrayList<>();
    for (int i = 0; i < list.size(); i++) {
        for (int j = i+1; j < list.size(); j++) {
            if (list.get(i).equals(list.get(j))) {
                result.add(list.get(i));
            }
        }
    }
    return result;
}

// Excellent (gets strong hire):
public Set<Integer> findDuplicates(List<Integer> numbers) {
    // Handle null input
    if (numbers == null || numbers.isEmpty()) return Set.of();

    Set<Integer> seen = new HashSet<>();
    Set<Integer> duplicates = new HashSet<>();

    for (int num : numbers) {
        if (!seen.add(num)) {  // add returns false if already present
            duplicates.add(num);
        }
    }
    return Collections.unmodifiableSet(duplicates);
    // O(n) time, O(n) space — explain why this is better than O(n²)
}
```

---

## Section Summary: Interview Strategy

**90-Day Interview Sprint Plan:**

**Month 1: Foundation**
- LeetCode Easy: 50 problems (all patterns)
- LeetCode Medium: 30 problems
- Java fundamentals + Spring concepts

**Month 2: Depth**
- LeetCode Medium: 50 more problems
- LeetCode Hard: 10 problems
- System design: study 5 real designs
- Mock interviews: 2/week with peers

**Month 3: Polish**
- Mock interviews: 5/week
- Behavioral stories: 10 prepared STAR stories
- Revisit weak areas
- Company-specific research (tech blog, engineering papers)

**Day-of interview tips:**
1. Think aloud — interviewers want to see your reasoning
2. Clarify before coding — always
3. Start with brute force, then optimize
4. Test with examples on paper before running
5. Handle edge cases explicitly (null, empty, single element)

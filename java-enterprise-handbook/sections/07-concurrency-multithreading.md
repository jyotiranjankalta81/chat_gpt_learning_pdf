# Section 7: Concurrency & Multithreading

> **This Is Where Java Shines and Burns:** Concurrency is Java's most powerful feature and most dangerous pitfall. At every senior Java interview at FAANG and banks, you WILL get concurrency questions. This is the section that separates Java engineers from Node.js engineers who "just switched."

---

## 7.1 The Fundamental Shift from Node.js

```
Node.js Concurrency Model:
─────────────────────────
Single thread → event loop → async I/O
No shared mutable state (same thread sees everything)
No race conditions on simple data reads/writes
Concurrency via: callbacks, promises, async/await

Java Concurrency Model:
──────────────────────
Multiple threads → true parallelism → shared heap
Same object can be modified by multiple threads simultaneously
Race conditions, deadlocks, memory visibility issues are REAL
Concurrency via: synchronized, locks, concurrent collections, thread pools
```

The key mindset shift: **in Java, any shared mutable state is a potential data race unless explicitly synchronized.**

---

## 7.2 Thread Basics

### Creating and Managing Threads

```java
// Don't create raw threads in production — use thread pools
// But understand this for interviews:

// Method 1: Extend Thread
Thread t = new Thread() {
    @Override
    public void run() {
        System.out.println("Running in: " + Thread.currentThread().getName());
    }
};
t.start();

// Method 2: Runnable (preferred — separates task from execution)
Runnable task = () -> processPayment(paymentId);
new Thread(task).start();

// Method 3: Virtual Thread (Java 21+) — million lightweight threads
Thread.ofVirtual().name("payment-handler").start(() -> {
    // Can block freely — JVM handles scheduling
    processWithBlockingDB(payment);
});
```

### Thread States Revisited

```java
Thread t = new Thread(task);
// State: NEW

t.start();
// State: RUNNABLE (executing or ready to execute)

synchronized (lock) {
    // Another thread holds lock → State: BLOCKED (waiting for monitor)
}

Object.wait();      // State: WAITING (indefinite)
Thread.sleep(1000); // State: TIMED_WAITING
join();             // Wait for another thread to finish

// After run() completes → State: TERMINATED
```

---

## 7.3 Synchronization — The Foundation

### The `synchronized` Keyword

```java
public class BankAccount {
    private BigDecimal balance;

    // Method-level: locks on 'this' instance
    public synchronized void deposit(BigDecimal amount) {
        balance = balance.add(amount);
        // Only one thread can execute this at a time per account instance
    }

    // Block-level: more granular
    public void transfer(BankAccount target, BigDecimal amount) {
        // Lock ordering to prevent deadlock
        BankAccount first = this.id < target.id ? this : target;
        BankAccount second = first == this ? target : this;

        synchronized (first) {
            synchronized (second) {
                this.balance = this.balance.subtract(amount);
                target.balance = target.balance.add(amount);
            }
        }
    }

    // Static synchronized: locks on CLASS object, not instance
    public static synchronized void globalOperation() {
        // Only one thread across ALL instances
    }
}
```

### The `volatile` Keyword

```java
// Problem: CPU caches — each core may cache variables locally
// Thread 1 updates running = false but Thread 2's cache still shows true

// Solution: volatile ensures visibility across threads
public class ServiceShutdownCoordinator {
    private volatile boolean running = true;  // Visible to all threads immediately

    public void shutdown() {
        this.running = false;  // Immediately visible to all threads
    }

    public void processLoop() {
        while (running) {  // Reads fresh value, not cached
            processNextBatch();
        }
    }
}

// volatile guarantees: visibility (read/write atomic for longs/doubles too)
// volatile does NOT guarantee: compound operations (check-then-act, read-modify-write)

// WRONG: volatile doesn't make this atomic
volatile int counter = 0;
counter++;  // Read, increment, write — not atomic! Use AtomicInteger
```

---

## 7.4 Thread-Safe Data Structures

```java
// WRONG in multi-threaded environment:
Map<String, Integer> cache = new HashMap<>();  // Not thread-safe!

// CORRECT:
Map<String, Integer> cache = new ConcurrentHashMap<>();  // Thread-safe, high performance

// ConcurrentHashMap internals:
// - Segment locking (bucket-level locks, not whole map)
// - Reads are lock-free in most cases
// - Writes lock only affected bucket

// Thread-safe collections:
CopyOnWriteArrayList<String> list = new CopyOnWriteArrayList<>();  // Reads fast, writes copy
CopyOnWriteArraySet<String> set = new CopyOnWriteArraySet<>();
ConcurrentLinkedQueue<Task> queue = new ConcurrentLinkedQueue<>();
ArrayBlockingQueue<Task> bounded = new ArrayBlockingQueue<>(1000);  // Blocks on full/empty
LinkedBlockingQueue<Task> unbounded = new LinkedBlockingQueue<>();

// Atomic variables — lock-free operations using CAS (Compare-And-Swap)
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();                   // Atomic read-modify-write
counter.compareAndSet(5, 10);               // CAS: if value==5, set to 10

AtomicReference<Config> config = new AtomicReference<>(initialConfig);
config.updateAndGet(old -> new Config(old.withUpdatedSetting()));  // Atomic update

// LongAdder — better than AtomicLong for high-contention counters
LongAdder hitCounter = new LongAdder();
hitCounter.increment();                      // Low contention via striping
long total = hitCounter.sum();               // Merge all stripes
```

---

## 7.5 Lock API — Beyond synchronized

```java
// java.util.concurrent.locks — more flexible than synchronized

// ReentrantLock: same as synchronized but with try-lock, timeout
ReentrantLock lock = new ReentrantLock(true); // fair = FIFO ordering

lock.lock();
try {
    // critical section
} finally {
    lock.unlock();  // ALWAYS in finally!
}

// Try-lock — avoid blocking indefinitely
if (lock.tryLock(100, TimeUnit.MILLISECONDS)) {
    try {
        // Got the lock
    } finally {
        lock.unlock();
    }
} else {
    // Could not acquire lock — fail fast or try later
}

// ReadWriteLock — multiple readers OR one writer
ReadWriteLock rwLock = new ReentrantReadWriteLock();
Lock readLock = rwLock.readLock();
Lock writeLock = rwLock.writeLock();

// Many threads can hold read lock simultaneously
readLock.lock();
try { return cache.get(key); } finally { readLock.unlock(); }

// Only one thread can hold write lock (excludes all readers)
writeLock.lock();
try { cache.put(key, value); } finally { writeLock.unlock(); }

// StampedLock — optimistic reads (Java 8+, better performance)
StampedLock stampedLock = new StampedLock();

// Optimistic read — no actual lock acquisition
long stamp = stampedLock.tryOptimisticRead();
double x = this.x, y = this.y;
if (!stampedLock.validate(stamp)) {
    // Data was modified — fall back to regular read lock
    stamp = stampedLock.readLock();
    try { x = this.x; y = this.y; }
    finally { stampedLock.unlockRead(stamp); }
}
```

---

## 7.6 ExecutorService — Thread Pool Management

```java
// NEVER create raw Thread in production — use thread pools

// Fixed thread pool: N threads always alive
ExecutorService fixedPool = Executors.newFixedThreadPool(10);

// Cached thread pool: grows/shrinks — DANGER in production (unbounded!)
ExecutorService cached = Executors.newCachedThreadPool();  // Can create 1000s of threads!

// Scheduled pool: for periodic/delayed tasks
ScheduledExecutorService scheduled = Executors.newScheduledThreadPool(5);
scheduled.scheduleAtFixedRate(task, 0, 60, TimeUnit.SECONDS);

// Production-grade thread pool configuration:
ThreadPoolExecutor executor = new ThreadPoolExecutor(
    5,                              // corePoolSize: always-alive threads
    20,                             // maximumPoolSize: max threads under load
    60, TimeUnit.SECONDS,           // keepAliveTime: idle thread lifetime
    new ArrayBlockingQueue<>(1000), // workQueue: bounded! rejects when full
    new ThreadFactoryBuilder()       // named threads for better debugging
        .setNameFormat("payment-worker-%d")
        .setDaemon(false)
        .build(),
    new ThreadPoolExecutor.CallerRunsPolicy()  // When queue full: caller executes task
    // Alternatives:
    // AbortPolicy: throw RejectedExecutionException (default)
    // DiscardPolicy: silently drop
    // DiscardOldestPolicy: drop oldest queued task
);

// In Spring — use @Async with configured executor
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {

    @Override
    @Bean(name = "taskExecutor")
    public Executor getAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(200);
        executor.setThreadNamePrefix("async-payment-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}

@Service
public class ReportService {

    @Async("taskExecutor")
    public CompletableFuture<Report> generateReport(ReportRequest request) {
        // Runs in taskExecutor thread pool, not HTTP request thread
        Report report = heavyComputation(request);
        return CompletableFuture.completedFuture(report);
    }
}
```

---

## 7.7 CompletableFuture — Async Programming

```java
// Node.js Promise → Java CompletableFuture

// Single async operation
CompletableFuture<User> userFuture = CompletableFuture.supplyAsync(
    () -> userService.findById(userId),  // Runs in ForkJoinPool.commonPool()
    customExecutor                        // Or specific thread pool
);

// Chain operations (like .then())
CompletableFuture<UserProfile> profileFuture = userFuture
    .thenApply(user -> buildProfile(user))           // Synchronous transform
    .thenApplyAsync(profile -> enrichProfile(profile)) // Async transform
    .exceptionally(ex -> {
        log.error("Failed to fetch profile", ex);
        return UserProfile.defaultProfile();          // Fallback
    });

// Parallel execution (like Promise.all())
CompletableFuture<User> userFuture = fetchUserAsync(userId);
CompletableFuture<List<Account>> accountsFuture = fetchAccountsAsync(userId);
CompletableFuture<CreditScore> creditFuture = fetchCreditScoreAsync(userId);

CompletableFuture.allOf(userFuture, accountsFuture, creditFuture)
    .thenApply(v -> new Dashboard(
        userFuture.join(),      // join() gets result (already complete)
        accountsFuture.join(),
        creditFuture.join()
    ))
    .get(5, TimeUnit.SECONDS); // Overall timeout

// First to complete (like Promise.race())
CompletableFuture.anyOf(primaryFuture, fallbackFuture)
    .thenAccept(result -> process(result));

// Exception handling
userFuture
    .thenApply(this::process)
    .handle((result, ex) -> {  // Always called, regardless of success/failure
        if (ex != null) return handleError(ex);
        return result;
    });

// Banking example: parallel enrichment
public CompletableFuture<EnrichedPayment> enrichPayment(Payment payment) {
    CompletableFuture<Account> fromAccount =
        CompletableFuture.supplyAsync(() -> accountService.get(payment.getFromId()));
    CompletableFuture<Account> toAccount =
        CompletableFuture.supplyAsync(() -> accountService.get(payment.getToId()));
    CompletableFuture<FxRate> fxRate =
        CompletableFuture.supplyAsync(() -> fxService.getRate(payment.getCurrency()));

    return CompletableFuture.allOf(fromAccount, toAccount, fxRate)
        .thenApply(v -> new EnrichedPayment(
            payment,
            fromAccount.join(),
            toAccount.join(),
            fxRate.join()
        ));
}
```

---

## 7.8 Race Conditions and Deadlocks

### Race Condition Example and Fix

```java
// RACE CONDITION: check-then-act
public class InventoryService {
    private int stock = 10;

    // WRONG: Thread 1 reads stock=1, Thread 2 reads stock=1, both proceed!
    public boolean reserve(int quantity) {
        if (stock >= quantity) {           // Thread 1 passes
            // Context switch happens here!
            stock -= quantity;             // Both threads subtract!
            return true;                   // Both return true — oversold!
        }
        return false;
    }

    // CORRECT: atomic check-and-act
    public synchronized boolean reserve(int quantity) {
        if (stock >= quantity) {
            stock -= quantity;
            return true;
        }
        return false;
    }

    // BETTER: AtomicInteger for simple increment/decrement
    private final AtomicInteger atomicStock = new AtomicInteger(10);

    public boolean reserveAtomic(int quantity) {
        while (true) {
            int current = atomicStock.get();
            if (current < quantity) return false;
            if (atomicStock.compareAndSet(current, current - quantity)) return true;
            // CAS failed — another thread changed value — retry
        }
    }
}
```

### Deadlock — Detailed Example

```java
// DEADLOCK: Account A → Account B and Account B → Account A
Object lockA = new Object();
Object lockB = new Object();

Thread t1 = new Thread(() -> {
    synchronized (lockA) {
        Thread.sleep(100);
        synchronized (lockB) { /* ... */ }  // Waiting for lockB
    }
});

Thread t2 = new Thread(() -> {
    synchronized (lockB) {
        Thread.sleep(100);
        synchronized (lockA) { /* ... */ }  // Waiting for lockA
    }
});
// t1 holds A, wants B. t2 holds B, wants A → deadlock!

// Prevention: consistent lock ordering
private void transferSafe(Account from, Account to) {
    Account first = from.getId().compareTo(to.getId()) < 0 ? from : to;
    Account second = first == from ? to : from;

    synchronized (first) {
        synchronized (second) {
            // Lock order is always smaller-ID first → no deadlock
        }
    }
}

// Detection: jstack <pid> will show:
// "Found one Java-level deadlock:"
// Thread X waiting for lock held by Thread Y
// Thread Y waiting for lock held by Thread X
```

---

## 7.9 Java 21 Virtual Threads — Project Loom

```java
// Traditional: 1 OS thread per request → expensive, limited to ~10,000
// Virtual Thread: millions of lightweight JVM-managed threads

// Virtual threads with executor
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 100_000).forEach(i -> {
        executor.submit(() -> {
            // Each of 100,000 requests gets its own virtual thread
            // Blocking DB call is fine — JVM unmounts and remounts
            String result = database.query("SELECT * FROM accounts WHERE id = " + i);
            return result;
        });
    });
}  // Awaits all tasks, then shuts down

// Spring Boot 3.2+: enable virtual threads globally
spring:
  threads:
    virtual:
      enabled: true  # All Tomcat threads become virtual threads

// Impact: I/O-bound services can handle dramatically more concurrency
// without reactive programming complexity

// Limitations of virtual threads:
// - Pinning: synchronized blocks pin to OS thread (performance concern)
//   → Prefer ReentrantLock over synchronized in virtual thread code
// - CPU-bound work: no benefit (virtual threads don't parallelize CPU)
// - Thread-local variables work but may hold more data than expected
```

---

## 7.10 Concurrent Collections — Production Patterns

```java
// ConcurrentHashMap advanced operations (all atomic)
ConcurrentHashMap<String, Integer> counts = new ConcurrentHashMap<>();

// Atomic computeIfAbsent — create entry only if missing
RateLimiter limiter = limiters.computeIfAbsent(clientId,
    id -> Bucket4j.builder()
        .addLimit(Bandwidth.classic(100, Refill.greedy(100, Duration.ofMinutes(1))))
        .build());

// Atomic merge — update or create
counts.merge(category, 1, Integer::sum);  // Atomically increment counter

// Atomic compute — read-modify-write atomically
counts.compute(key, (k, v) -> v == null ? 1 : v + 1);

// forEach with concurrency level (parallelism threshold)
counts.forEach(4, (key, val) -> process(key, val));  // 4 parallel threads

// Search (returns first non-null result)
String hotKey = counts.search(4, (k, v) -> v > 1000 ? k : null);

// BlockingQueue — producer-consumer pattern
BlockingQueue<Task> taskQueue = new ArrayBlockingQueue<>(1000);

// Producer
executor.submit(() -> {
    while (running) {
        Task task = generateTask();
        taskQueue.put(task);  // Blocks if queue full — backpressure!
    }
});

// Consumer
executor.submit(() -> {
    while (running) {
        Task task = taskQueue.poll(1, TimeUnit.SECONDS);  // Wait 1s for task
        if (task != null) process(task);
    }
});
```

---

## Section Summary: Concurrency Interview Must-Know

**Java concurrency is different from Node.js — demonstrate you understand this:**

1. **Explain Java memory model** — happens-before relationship, visibility
2. **synchronized vs volatile vs AtomicInteger** — when to use which
3. **Thread pool sizing** — core pool, max pool, queue capacity, rejection policy
4. **CompletableFuture chains** — map, flatMap, allOf, anyOf, exception handling
5. **Deadlock** — demonstrate prevention strategy with lock ordering
6. **ConcurrentHashMap vs Collections.synchronizedMap** — performance difference
7. **ReadWriteLock** — when multiple readers benefit
8. **Virtual threads** — what they are, benefits, limitations (pinning)
9. **ThreadLocal** — usage, and why you MUST clear it in thread pools
10. **Race condition** — identify and fix check-then-act patterns

**Most common interview bug:** Write a thread-safe counter without using synchronized on the method. Expected: AtomicInteger or CAS loop.

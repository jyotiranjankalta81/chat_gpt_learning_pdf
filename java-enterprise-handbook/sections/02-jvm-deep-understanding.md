# Section 2: JVM Deep Understanding

> **Why This Matters:** JVM internals are tested at every senior Java interview at FAANG and banks. More importantly, understanding the JVM is what separates engineers who can diagnose production incidents from those who can only write code that works in development.

---

## 2.1 JVM Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        JVM Architecture                          │
│                                                                   │
│  ┌──────────────────┐     ┌──────────────────────────────────┐  │
│  │   Class Loader   │────▶│          Runtime Data Areas       │  │
│  │   Subsystem      │     │  ┌────────────┐ ┌─────────────┐  │  │
│  │                  │     │  │   Heap     │ │  Method Area│  │  │
│  │ - Bootstrap CL   │     │  │ (shared)   │ │ (Metaspace) │  │  │
│  │ - Extension CL   │     │  └────────────┘ └─────────────┘  │  │
│  │ - Application CL │     │  ┌────────────┐ ┌─────────────┐  │  │
│  └──────────────────┘     │  │  JVM Stack │ │    PC Reg   │  │  │
│                            │  │(per thread)│ │ (per thread)│  │  │
│  ┌──────────────────┐     │  └────────────┘ └─────────────┘  │  │
│  │  Execution Engine│     │  ┌────────────┐                   │  │
│  │                  │     │  │Native Stack│                   │  │
│  │ - Interpreter    │     │  └────────────┘                   │  │
│  │ - JIT Compiler   │     └──────────────────────────────────┘  │
│  │ - GC             │                                            │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Node.js vs JVM Runtime

```
Node.js (V8 Engine)              Java (JVM)
─────────────────────────────────────────────────────────
Single process, event loop       Multi-threaded by default
V8 heap (all objects)            Heap (GC-managed objects)
V8 stack (call frames)           Stack per thread
Node native modules              JNI (Java Native Interface)
V8 JIT compilation               JVM JIT (C1+C2 compilers)
Automatic GC (V8 GC)             Pluggable GC (G1, ZGC, etc.)
No warm-up concept               JIT warm-up critical
```

---

## 2.2 Memory Architecture — Deep Dive

### Heap Memory

The heap is where all objects live. It is shared across all threads (which is why thread safety matters in Java).

```
Java Heap (shared, GC-managed)
├── Young Generation
│   ├── Eden Space      — new objects allocated here
│   ├── Survivor S0     — objects that survived 1 GC
│   └── Survivor S1     — objects that survived 2 GC cycles
└── Old Generation (Tenured)
    └── long-lived objects promoted from Young Gen

Off-Heap (NOT in GC scope)
├── Metaspace         — class metadata, method bytecode (was PermGen pre-Java 8)
├── Direct Buffer     — ByteBuffer.allocateDirect() — used in Netty/NIO
└── Native Memory     — JNI, malloc()
```

### Stack Memory (per thread)

```
Each Thread has its own Stack:
├── Frame 1: main()
│   ├── local variables (primitives stored by value, refs stored as address)
│   └── operand stack
├── Frame 2: processPayment()
│   ├── local variables
│   └── partial results
└── Frame 3: validateAmount()
    └── local variables
```

**Critical insight:**
- **Primitives in methods** → Stack (cheap, no GC)
- **Objects** → Heap (GC-managed, more expensive)
- **Stack frames** are automatically reclaimed when method returns
- `StackOverflowError` = too deep recursion (stack runs out of space)

### Practical Memory Model

```java
public void processOrder(String orderId) {           // New stack frame created
    int retryCount = 0;                              // int on stack (value)
    Order order = orderService.findById(orderId);    // reference on stack,
                                                     // Order object on heap
    List<OrderItem> items = order.getItems();        // reference on stack

    for (OrderItem item : items) {                   // item ref on stack
        processItem(item);                           // new stack frame
    }
    // All local refs go out of scope — objects become GC eligible
}                                                    // Stack frame popped
```

---

## 2.3 Garbage Collection — Production Knowledge

### GC Fundamentals

```
Object lifecycle:
Eden Space → (Minor GC) → Survivor → (if age > threshold) → Old Gen
                                                           → (Major/Full GC)
```

**Minor GC** (Young Gen collection):
- Frequent, fast (milliseconds)
- "Stop the world" but brief
- Most objects die young (infant mortality hypothesis)

**Major/Full GC** (includes Old Gen):
- Infrequent, slow (can be seconds)
- "Stop the world" pauses affect latency
- What causes your `P99` latency spikes in production

### GC Algorithms — Choosing for Production

| GC | Default | Latency | Throughput | Use Case |
|----|---------|---------|------------|----------|
| Serial GC | No | High pauses | Low | Single-core/small apps |
| Parallel GC | Java 8 default | Medium | High | Batch processing |
| G1 GC | Java 9+ default | Low pauses | Good | General purpose |
| ZGC | Java 15+ production | Sub-millisecond | Good | Low-latency apps |
| Shenandoah | Available | Sub-millisecond | Good | Red Hat OpenJDK |

**For banking/FAANG APIs — use G1GC or ZGC:**
```
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200      # Target max pause
-XX:G1HeapRegionSize=16m      # Region size

# For ultra-low latency (trading systems, real-time APIs):
-XX:+UseZGC
-XX:SoftMaxHeapSize=4g
```

### GC Tuning — What You'll See in Production

```bash
# Common JVM flags in enterprise docker-compose / k8s manifests
java \
  -Xms2g \                          # Initial heap (set equal to Xmx to avoid GC on startup)
  -Xmx4g \                          # Max heap
  -XX:+UseG1GC \                    # GC algorithm
  -XX:MaxGCPauseMillis=200 \        # GC pause target
  -XX:+HeapDumpOnOutOfMemoryError \ # OOM heap dump for post-mortem
  -XX:HeapDumpPath=/var/log/dumps \ # Where to write dumps
  -XX:+PrintGCDetails \             # GC logs (critical for tuning)
  -Xlog:gc*:file=/var/log/gc.log \  # GC log file
  -jar app.jar
```

### Memory Leaks — What Causes Them in Java

Unlike Node.js where memory leaks are common (event listeners, closures), Java's GC is more forgiving. But leaks still happen:

```java
// 1. Static collections that grow unboundedly
public class BadCache {
    private static final Map<String, Object> CACHE = new HashMap<>();
    // Objects never removed → OOM eventually
}

// 2. Listener not deregistered
eventBus.register(listener);  // If never unregistered, listener object is retained

// 3. ThreadLocal not cleaned up
private static final ThreadLocal<UserContext> context = new ThreadLocal<>();
// In thread pools (like in Spring), threads are reused!
// Must call context.remove() after request handling

// 4. Inner class holding outer class reference
class MyRunnable implements Runnable {
    void doSomething() {
        OuterClass.this.someField;  // Implicit reference to OuterClass
    }
}
// If MyRunnable lives longer than OuterClass intends, OuterClass is not GC'd
```

---

## 2.4 JIT Compilation — Why Java Is Fast

### The Tiered Compilation Model

```
Code execution path:
1. Interpreter        — immediate start, slow (profiling)
2. C1 Compiler        — quick compile, moderate speed (client compiler)
3. C2 Compiler        — deep optimize after profiling, fast (server compiler)

Tiered: C1 → profiling data → C2 → optimized native code
```

**JVM warm-up phenomenon:**
```
Node.js: V8 optimizes quickly, warm-up ~seconds
Java:    Full C2 optimization takes 30-60 seconds or more of real load

This is why:
- Don't benchmark immediately after startup
- Kubernetes readiness probes must account for warm-up
- Spring Boot + GraalVM native images eliminate warm-up (AOT compilation)
```

### JIT Optimizations You Should Know

**Inlining:** The JIT inlines small/frequently-called methods into the call site, eliminating method call overhead. This is why Java tiny getter/setter methods are "free."

**Escape Analysis:** Objects that don't "escape" a method (not returned or shared) can be allocated on the stack, eliminating GC pressure:
```java
public void process() {
    Point p = new Point(1, 2);  // May be stack-allocated if JIT determines it doesn't escape
    int sum = p.x + p.y;
    // p is never returned or stored — JIT may optimize away heap allocation
}
```

**Dead Code Elimination:** Unreachable branches are removed at JIT level, which is why some micro-benchmarks give misleading results.

---

## 2.5 Thread Model — Fundamental Difference from Node.js

```
Node.js:  Single main thread + libuv thread pool (I/O)
          → Never blocks main thread (async everything)
          → No shared mutable state issues (single thread)

Java:     True OS threads, many per JVM
          → Can block on I/O (but has async APIs too)
          → Shared mutable state = concurrency bugs
          → Need synchronization, thread-safe data structures
```

### Thread States

```
NEW → RUNNABLE → BLOCKED/WAITING/TIMED_WAITING → TERMINATED

BLOCKED: waiting for a monitor lock (synchronized block)
WAITING: waiting indefinitely (Object.wait(), LockSupport.park())
TIMED_WAITING: waiting with timeout (Thread.sleep(), wait(timeout))
```

### Thread Pools — How Java Applications Actually Run

```java
// Spring HTTP request handling (default: embedded Tomcat)
// 200 threads handle 200 concurrent requests
// Each request gets its own thread, can block on DB/I/O freely

// vs Node.js: single thread handles all requests via event loop
// blocking I/O would freeze the entire server

// Spring configures Tomcat thread pool:
server.tomcat.threads.max=200
server.tomcat.threads.min-spare=10

// Virtual Threads (Java 21+) — Project Loom
// Lightweight threads — millions of them, JVM-managed (like goroutines)
Thread.ofVirtual().start(() -> {
    // Can block freely — JVM parks virtual thread, OS thread continues
    var result = database.query(...);  // Blocking call is fine now
});
```

---

## 2.6 Class Loading

```
Class Loading Process:
Source: MyClass.java
Compiled: MyClass.class (bytecode)
Runtime: ClassLoader finds .class → loads into Method Area

Class Loader Hierarchy:
Bootstrap ClassLoader (JDK core: java.lang, java.util)
    └── Platform/Extension ClassLoader (JDK extensions)
            └── Application ClassLoader (your app's classpath)

Delegation model: child asks parent first (parent-first)
```

**Why it matters:**
- Hot reload in development (Spring DevTools) works by using a separate ClassLoader
- OSGi, plugin systems use ClassLoader isolation
- Certain reflection patterns require explicit ClassLoader handling

---

## 2.7 JVM Profiling — Production Tooling

### Profiling Tools

```
CPU Profiling:
- async-profiler   — low-overhead, production-safe flame graphs
- JFR (Java Flight Recorder) — built-in, minimal overhead
- VisualVM         — GUI, good for development

Memory Profiling:
- MAT (Eclipse Memory Analyzer) — heap dump analysis
- JFR heap events
- jmap -heap <pid>  — quick heap summary

Thread Analysis:
- jstack <pid>      — thread dump (debug deadlocks)
- thread dump in VisualVM
```

### Reading a Thread Dump (critical for incident response)

```
"http-nio-8080-exec-1" #25 daemon prio=5
   java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Unsafe.java)
        at java.util.concurrent.locks.LockSupport.park(LockSupport.java:175)
        at HikariCP.waitForConnection(...)    ← WAITING FOR DB CONNECTION POOL
        at MyService.processPayment(...)      ← Your code stalled here

Diagnosis: HikariCP pool exhausted — DB connections maxed out
Fix: Increase pool size or find connection leak
```

### Java Flight Recorder — Production Profiling

```java
// Start JFR programmatically
Recording recording = new Recording();
recording.enable("jdk.CPULoad").withPeriod(Duration.ofSeconds(1));
recording.enable("jdk.GarbageCollection");
recording.start();
// ... run workload ...
recording.dump(Paths.get("/tmp/app.jfr"));
recording.close();
// Open .jfr in JDK Mission Control (JMC) for visual analysis
```

---

## 2.8 JVM Performance Tuning Checklist

### Startup Performance
```bash
# Slow startup? Consider:
# 1. Spring Boot lazy initialization
spring.main.lazy-initialization=true

# 2. Class Data Sharing (CDS)
java -Xshare:dump          # Create archive
java -Xshare:on -jar app.jar  # Use archive on startup

# 3. GraalVM Native Image (AOT — best startup)
# Startup in milliseconds, but no JIT optimization at runtime
```

### Runtime Performance
```bash
# Heap sizing — CRITICAL
# Set Xms = Xmx to avoid heap resizing GC overhead
-Xms4g -Xmx4g

# For containerized environments (Docker/k8s):
-XX:+UseContainerSupport          # Read cgroup limits (Java 8u191+)
-XX:MaxRAMPercentage=75.0         # Use 75% of container memory for heap
# Leave 25% for Metaspace, thread stacks, direct buffers, OS

# G1GC tuning for API servers
-XX:+UseG1GC
-XX:MaxGCPauseMillis=200
-XX:G1NewSizePercent=30          # 30% of heap for young gen
-XX:G1MaxNewSizePercent=40
```

### Container/Kubernetes Specifics

```yaml
# k8s pod spec — proper JVM resource configuration
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"    # MUST set — OOMKilled without it
    cpu: "2000m"

# JVM startup args (via JAVA_OPTS env):
env:
  - name: JAVA_OPTS
    value: "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+ExitOnOutOfMemoryError"
    # ExitOnOutOfMemoryError: better to crash + restart than zombie process
```

---

## 2.9 Common JVM Production Issues

### OOM (OutOfMemoryError) — Types and Diagnosis

```
java.lang.OutOfMemoryError: Java heap space
→ Heap exhausted: memory leak or undersized heap
→ Action: Heap dump + MAT analysis, check for unbounded caches

java.lang.OutOfMemoryError: Metaspace
→ Class metadata exhausted: class loader leak (in app servers, OSGi)
→ Action: -XX:MaxMetaspaceSize=256m, investigate class loader leaks

java.lang.OutOfMemoryError: GC overhead limit exceeded
→ JVM spending >98% time in GC with <2% reclamation
→ Action: Increase heap or find memory leak

java.lang.OutOfMemoryError: Direct buffer memory
→ Off-heap ByteBuffers exhausted (NIO, Netty)
→ Action: -XX:MaxDirectMemorySize=512m
```

### Performance Degradation Patterns

```
Symptom: Latency spikes every ~60 seconds
Cause: Full GC pause
Action: -XX:+UseG1GC, tune region sizes, reduce old gen promotion

Symptom: CPU spikes to 100%
Cause: Tight loop, infinite retry loop, CPU-bound thread
Action: Thread dump, look for tight loops in RUNNABLE threads

Symptom: Thread pool exhausted (RejectedExecutionException)
Cause: Task arrival rate > processing rate
Action: Queue metrics, increase pool or use backpressure

Symptom: Memory grows steadily, never freed
Cause: Memory leak (unbounded cache, listener, ThreadLocal)
Action: Heap dump comparison (before vs after load), MAT
```

---

## Section Summary: JVM Interview Essentials

**Questions you must answer confidently:**

1. "What is the difference between heap and stack in Java?"
2. "Explain Young Generation, Old Generation, and how promotion works"
3. "What causes a Full GC and how do you reduce them?"
4. "How does the JIT compiler work and what is JVM warm-up?"
5. "Explain memory leaks in Java — how do they happen and how do you detect them?"
6. "What JVM flags would you set for a production microservice in Kubernetes?"
7. "How would you diagnose a thread deadlock in production?"
8. "What is the difference between thread states BLOCKED and WAITING?"
9. "Explain Java class loading — what is the delegation model?"
10. "What is escape analysis and how does it optimize performance?"

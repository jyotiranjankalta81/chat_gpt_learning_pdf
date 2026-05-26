# Interview Preparation Sequence
## Week-by-Week Sprint to Interview Readiness

---

## Phase 1: Foundation Fluency (Weeks 1-4)

### Week 1: Java Language Confidence
```
Day 1: Core types, strings, collections (HashMap, ArrayList, HashSet)
Day 2: OOP — classes, interfaces, abstract classes, enums
Day 3: Generics, wildcards, type erasure
Day 4: Streams, lambdas, functional interfaces
Day 5: Exception handling, try-with-resources
Day 6-7: Code katas — rewrite 5 Node.js functions in Java

Self-test: Can you code these without IDE help?
  □ Two Sum using HashMap
  □ Group a list by a property using Streams
  □ Custom exception with error code
  □ Generic Pair<A, B> class
  □ Fibonacci with memoization
```

### Week 2: Spring Foundations
```
Day 1: DI container, bean lifecycle, scopes
Day 2: Spring MVC — request lifecycle, @Controller, @RestController
Day 3: Spring Data JPA — entities, repositories, queries
Day 4: Spring Security — filter chain, JWT
Day 5: @Transactional — propagation, isolation, pitfalls
Day 6-7: Build mini CRUD API (no reference code)

Self-test:
  □ Explain @Transactional pitfalls (3 of them)
  □ Explain N+1 problem and 3 ways to fix it
  □ Implement JWT filter from scratch
  □ Write JPA repository with custom query
```

### Week 3: JVM + Concurrency
```
Day 1: Heap, stack, GC fundamentals
Day 2: GC algorithms, GC tuning flags
Day 3: Thread model, synchronized, volatile, AtomicXxx
Day 4: ThreadPoolExecutor, CompletableFuture
Day 5: Race conditions, deadlocks, prevention
Day 6-7: Concurrent programming exercises

Self-test:
  □ What JVM flags would you set for a 2GB container?
  □ Implement thread-safe counter 3 different ways
  □ Find the deadlock in given code
  □ Write CompletableFuture chain with parallel fetches
```

### Week 4: First Mock Interview
```
Format: 45-minute coding mock (use Pramp or peer)
Topics: LeetCode Medium problem in Java
Focus: Clean code, edge cases, time complexity explanation
```

---

## Phase 2: Depth Building (Weeks 5-8)

### Week 5-6: Distributed Systems
```
Topics:
  → Kafka: producers, consumers, partitions, offsets
  → Delivery guarantees: at-most, at-least, exactly-once
  → DLQ pattern
  → CAP theorem with examples
  → Circuit breaker

Practice:
  □ Implement Kafka producer with retry
  □ Implement idempotent Kafka consumer
  □ Explain CAP theorem for: PostgreSQL, Redis, Kafka
  □ Design DLQ handling strategy
```

### Week 7-8: System Design Fundamentals
```
Study 5 designs:
  1. URL shortener (LLD + HLD)
  2. Rate limiter (token bucket + sliding window)
  3. Notification system
  4. Payment processing
  5. Cache design with Redis

Practice: whiteboard each design in 45 minutes

Self-test:
  □ Design URL shortener (45 min, no notes)
  □ Design rate limiter at API gateway level
  □ Explain trade-offs between synchronous and async for payments
```

---

## Phase 3: Interview Simulation (Weeks 9-12)

### Weekly Mock Interview Schedule
```
Monday:    Coding interview (1 LeetCode Medium/Hard, 45 min)
Wednesday: System Design mock (45 min, one of the 10 key designs)
Friday:    Behavioral mock (STAR stories, 30 min)
Weekend:   Review feedback, study weak areas
```

### LeetCode Target Progress
```
Week 9:  Total solved: 80+ (Easy: 40, Medium: 35, Hard: 5)
Week 10: Total solved: 100+ (Easy: 40, Medium: 50, Hard: 10)
Week 11: Total solved: 120+ (Medium: 60, Hard: 15)
Week 12: Total solved: 140+ (Medium: 70, Hard: 20)
```

### Behavioral Stories Bank (Prepare All 10)

```
1. Most impactful technical contribution
   → STAR: Situation (scale/context), Task (your role), Action (what YOU did),
     Result (measurable: latency, uptime, cost, velocity)

2. Production incident response
   → Demonstrate: systematic diagnosis, calm under pressure, root cause analysis

3. Technical disagreement with peer/manager
   → Demonstrate: data-driven argument, listening, commit after decision

4. Simplified a complex system
   → Demonstrate: architectural thinking, reduced complexity, measurable benefit

5. Worked across teams to deliver something
   → Demonstrate: collaboration, alignment, communication

6. Took on something outside your scope
   → Demonstrate: ownership, initiative, leadership potential

7. Mentored or helped a junior engineer
   → Demonstrate: communication, patience, knowledge transfer

8. Made decision with incomplete information
   → Demonstrate: risk management, bias for action, reversibility thinking

9. Failed and what you learned
   → Demonstrate: self-awareness, learning mindset, constructive framing

10. Long-term technical vision you drove
    → Demonstrate: strategic thinking, influence, architectural judgment
```

---

## Phase 4: Company-Specific Preparation (Weeks 13-16)

### For Amazon
```
Focus:
  → 14 Leadership Principles (know all, story for each)
  → LeetCode: Amazon-tagged problems (Graph, DP heavy)
  → System design: design at Amazon scale (millions of users, global)

Amazon-specific questions:
  □ "Tell me about a time you disagreed with your manager" (Backbone)
  □ "Describe a complex problem you solved" (Dive Deep)
  □ "How did you handle a customer complaint?" (Customer Obsession)
  □ "What's the most innovative thing you've built?" (Invent and Simplify)
```

### For Google
```
Focus:
  → Algorithm and data structure depth (harder problems)
  → System design: scalability, reliability, observability
  → Code quality: clean, readable, optimal

Google-specific:
  □ Expect 2-3 coding rounds + 1-2 system design
  □ Googleyness round: collaboration, intellectual humility
  □ Optimal solutions expected — brute force then optimize
```

### For Goldman Sachs / JP Morgan
```
Focus:
  → Spring ecosystem depth (DI, AOP, Security, Data)
  → Transaction management (isolation levels, distributed transactions)
  → Security (OAuth2, JWT, PCI-DSS awareness)
  → Financial domain knowledge (FX, payments, settlements)

Bank-specific questions:
  □ "How would you design a system to prevent duplicate payments?"
  □ "Explain database isolation levels with a banking example"
  □ "How do you audit all sensitive operations?"
  □ "How would you handle a SWIFT transfer that partially fails?"
  □ "Explain optimistic vs pessimistic locking for concurrent balance updates"
```

### For Stripe
```
Focus:
  → API design excellence (REST best practices, idempotency)
  → Payment system knowledge
  → Kafka and event-driven architecture
  → Resilience engineering (retry, CB, idempotency)

Stripe-specific:
  □ "Design Stripe's idempotency key system"
  □ "How do you ensure exactly-once payment processing?"
  □ "Design the Stripe webhook delivery system"
  □ "How would you scale to 100x current payment volume?"
```

---

## Daily Interview Prep Routine (During Active Job Search)

```
Morning (1 hour):
  • 1 LeetCode problem, timed (25 min)
  • Review solution and alternatives (10 min)
  • Practice explaining solution out loud (10 min)
  • Read 1 section from handbook (20 min)

Evening (30 min):
  • Review 5 behavioral questions (rotate through bank of stories)
  • Practice answering 1 system design question to yourself
  • Read engineering blog from target company

Weekend (4 hours):
  • Full mock interview (coding + system design) with peer/recording
  • Review and improve weak behavioral stories
  • Study 1 new system design from architecture examples
  • Cold coding: pick any hard problem, code without looking at solutions
```

---

## Quick Interview Reference Cards

### Coding Interview Checklist
```
Before coding:
  □ Clarify requirements (1-2 minutes)
  □ Discuss examples (happy path + edge cases)
  □ Propose approach BEFORE coding
  □ Agree on approach with interviewer

During coding:
  □ Think aloud continuously
  □ Write clean variable names (not a, b, temp)
  □ Handle null/empty inputs
  □ Modularize with helper methods

After coding:
  □ Trace through with example
  □ State time and space complexity
  □ Discuss alternative approaches
  □ Mention test cases you'd write
```

### System Design Checklist
```
□ Requirements clarification (5 min)
□ Scale estimation (5 min)
□ API design (5 min)
□ High-level diagram: boxes and arrows (10 min)
□ Data model (5 min)
□ Deep dive on critical component (10 min)
□ Scaling, bottlenecks, trade-offs (5 min)
□ Failure scenarios and mitigation (5 min)
```

### Java/Spring Quick Answers
```
@Transactional pitfall → self-invocation bypasses AOP proxy
N+1 fix → JOIN FETCH or @EntityGraph
Thread-safe collection → ConcurrentHashMap (not HashMap in singleton)
Connection pool → HikariCP: size = core_count * 2 + spindles
GC pause spikes → Check GC logs, tune MaxGCPauseMillis, add heap
JWT vulnerability → alg:none, missing exp check, missing iss/aud check
Idempotency → Redis with setIfAbsent + DB unique constraint
Circuit breaker → Resilience4j: failureRateThreshold, waitDurationInOpenState
```

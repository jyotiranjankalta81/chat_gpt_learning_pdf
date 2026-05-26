# Section 13: Real Enterprise Engineering

> **Day 1 at HSBC or Amazon:** You join, get access to a 500k-line Java codebase, attend standup, and are expected to contribute a bug fix by week 2. This section prepares you for the real experience — navigating legacy code, production incidents, PR culture, and team collaboration.

---

## 13.1 Navigating Enterprise Codebases

### How to Onboard to a New Java Codebase

```
Week 1: Orientation
1. Find the entry points:
   - main() → @SpringBootApplication → understand the bootstrap
   - List all @Controller/@RestController classes → understand the API surface
   - List all @KafkaListener classes → understand event consumers
   - List all @Scheduled methods → understand background jobs

2. Understand the data model:
   - Find all @Entity classes → this is the domain model
   - Examine the Flyway/Liquibase migrations → understand schema evolution history
   - Find the main @Repository interfaces → understand data access patterns

3. Understand the configuration:
   - application.yml → core config
   - application-prod.yml → production overrides
   - @ConfigurationProperties classes → strongly-typed config beans

4. Find the tests:
   - Unit tests → understand service logic
   - Integration tests → understand component interactions
   - @SpringBootTest → understand full-stack behavior

Week 2: First Contribution
- Take a small bug fix or well-defined feature
- Follow existing patterns exactly
- Write tests like the existing tests
- Match the code style (checkstyle/spotless rules)
- Ask questions in PR comments, not in Slack (creates knowledge record)
```

### Reading Unfamiliar Java Code

```java
// 1. Read signatures before bodies
public Optional<TransferResult> processInternationalTransfer(
        TransferRequest request,
        SwiftRoutingInfo routing,
        ComplianceContext compliance) throws ComplianceViolationException {
// Tells you: optional return (may fail/not apply), 3 inputs, checked exception
// → Already understand the contract before reading implementation

// 2. Identify the layers
// Controller (HTTP) → Service (business) → Repository (data) → Entity (model)
// Follow the call chain from the HTTP endpoint down to understand one feature fully

// 3. Find the tests first for unfamiliar code
// Tests document expected behavior more clearly than production code

// 4. Use the git log (your best documentation)
git log --follow -p src/main/java/com/bank/payment/PaymentService.java
// Shows WHY each change was made (if commit messages are good)
// Find the ticket/PR that introduced a pattern you don't understand

// 5. IDE structure navigation
// - Find Usages (Cmd+Click on interface → find implementations)
// - Call Hierarchy (who calls this method?)
// - Type Hierarchy (what implements this interface?)
```

---

## 13.2 Code Review — Giving and Receiving

### What Great PR Reviews Look For

```
Security:
- SQL injection via string concat in queries?
- Missing input validation (@Valid on request bodies)
- Sensitive data logged?
- Missing authorization check (can user X access resource Y?)
- New library with known CVEs?

Correctness:
- Race conditions in concurrent code?
- NullPointerException risk? (unchecked Optional.get())
- Integer overflow? (int for count that could exceed 2B)
- Transaction boundaries correct? (@Transactional on right method)
- Exception handling appropriate? (silently caught?)

Performance:
- N+1 query? (lazy-loaded collection in loop)
- Missing index for new query?
- Unbounded collection? (could grow to millions)
- Expensive operation in tight loop?
- Cache miss patterns?

Maintainability:
- Is this testable? (can it be unit tested without Spring context?)
- Does it follow existing patterns in the codebase?
- Are names clear and accurate?
- Is it unnecessarily complex?
- Will the next engineer understand this in 6 months?

Architecture:
- Does this belong in this layer?
- Does this create unwanted coupling?
- Will this scale to 10x the current load?
- Does this violate domain boundaries?
```

### Giving Feedback Effectively

```
Nit: Minor style suggestion (not blocking)
"Nit: Consider extracting this into a named constant for readability"

Question: Seeking understanding
"Question: Why are we using pessimistic locking here vs optimistic?
 Want to understand the trade-off being made."

Concern: Potential issue (blocking if unaddressed)
"Concern: This HashMap in a @Service singleton is not thread-safe.
 Concurrent requests could corrupt the state. Use ConcurrentHashMap."

Blocker: Must fix (defect, security issue, violation)
"Blocker: This query appends user input directly to SQL string —
 SQL injection vulnerability. Use parameterized query."

Praise: Acknowledge good patterns
"Nice use of the builder pattern here — much cleaner than the factory
 approach in the old code."
```

---

## 13.3 Production Incidents — The Real Test

### Incident Response Framework

```
1. DETECT (0-5 minutes)
   - Alert fires (PagerDuty, Datadog)
   - Check dashboards: error rate, latency, traffic
   - Is it gradual degradation or sudden failure?
   - Is it all users or subset? All regions or one?

2. COMMUNICATE (immediately)
   - Post in incident Slack channel: "Investigating elevated error rate on payment API"
   - Tag relevant teams
   - Start incident timer

3. DIAGNOSE (5-20 minutes)
   - Recent deployments? (git log, deployment history)
   - Infrastructure changes? (Terraform logs, k8s events)
   - Check logs: filter by error level + service name
   - Check traces: find failing requests, look at span details
   - Thread dump if CPU spike or thread pool exhaustion

4. MITIGATE (varies)
   - Can you roll back the last deployment?
   - Can you toggle a feature flag to disable new behavior?
   - Can you increase a timeout/pool size?
   - Can you redirect traffic to healthy region?
   - Mitigation BEFORE root cause — stop the bleeding first

5. RESOLVE + COMMUNICATE
   - Confirm metrics return to normal
   - Post resolution in incident channel
   - Keep stakeholders updated

6. POST-MORTEM (within 48 hours)
   - Write blameless RCA
   - Timeline of events
   - Root cause (technical)
   - Contributing factors (process)
   - Action items with owners and deadlines
```

### Common Production Issues — Java Specific

```
Issue: Memory leak (heap grows continuously)
Symptoms: GC time increasing, OOM eventually
Diagnosis:
  jmap -histo:live <pid>  → object histogram (what's growing?)
  Heap dump + MAT analysis → find GC roots holding objects
Common causes: ThreadLocal not cleared, static Map growing, listener not removed

Issue: Thread pool exhaustion
Symptoms: RejectedExecutionException, slow response (threads queueing)
Diagnosis:
  jstack <pid> → thread dump, look for many threads in same state
  Actuator /actuator/metrics/executor.pool.size
  HikariCP metrics → connection pool stats
Common causes: DB slow (connections held), pool too small, processing too slow

Issue: GC pressure causing latency spikes
Symptoms: P99/P999 latency spikes every ~60 seconds
Diagnosis:
  GC logs: -Xlog:gc*:file=/var/log/gc.log
  JFR: java -XX:StartFlightRecording duration=120s
  Grafana: gc.pause metric spikes
Common causes: Heap too small, long-lived objects in old gen, allocation rate too high

Issue: Connection leak
Symptoms: HikariCP connection timeout, "Unable to acquire JDBC Connection"
Diagnosis:
  spring.datasource.hikari.leak-detection-threshold=2000
  Check for try-with-resources everywhere DB connections used
Common causes: Exception path skips connection.close()
```

---

## 13.4 Refactoring Legacy Code

### Safe Refactoring Strategy

```
The Strangler Fig Pattern — migrate legacy incrementally

Legacy Monolith → New Microservice (incrementally)

Step 1: Add feature flag
  if (featureFlags.isEnabled("new-payment-service", userId)) {
      return newPaymentService.process(request);
  } else {
      return legacyPaymentService.process(request);
  }

Step 2: Route small % to new service (canary)
  5% → new service → validate behavior matches legacy

Step 3: Shadow mode — run both, compare results
  newService.process(request);
  legacyResult = legacyService.process(request);
  if (!resultsMatch(newResult, legacyResult)) {
      alert.warning("Divergence detected: " + requestId);
  }
  return legacyResult;  // Still serving legacy until confident

Step 4: Gradually increase % to new service
  5% → 25% → 50% → 100%

Step 5: Remove legacy code (satisfying!)
```

### Dealing with Code You Inherited

```java
// Don't touch it without tests.
// First, write characterization tests — tests that document WHAT THE CODE DOES.

@Test
public void testLegacyCalculation_documentsBehavior() {
    // You don't know if this is "right" — you document what it does
    LegacyCalculator calc = new LegacyCalculator();
    BigDecimal result = calc.computeFee(new BigDecimal("100.00"), "USD");
    // Whatever this returns IS the expected behavior until someone decides to change it
    assertEquals(new BigDecimal("2.50"), result);
}

// Now you have a safety net. THEN refactor.
// After refactoring: all tests still pass = behavior preserved.
```

---

## 13.5 Coding Standards — What Matters at Enterprise Companies

### Style and Standards

```java
// Checkstyle / SpotBugs / PMD / SonarQube — automated enforcement

// Google Java Style Guide (most companies follow this or similar):
// - 2 or 4 spaces indentation (never tabs)
// - 100-120 character line limit
// - K&R brace style (opening brace on same line)
// - Blank line between class members
// - @Override always present when overriding

// Lombok usage (reduces boilerplate, common in enterprises)
@Getter
@Builder
@ToString(exclude = {"password", "ssn"})
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
@Entity
public class User {
    @EqualsAndHashCode.Include
    private UUID id;

    private String email;
    private String password;
    @ToString.Exclude  // Don't log PII
    private String ssn;
}

// Naming conventions:
// Classes: PascalCase (PaymentService, not paymentService)
// Methods/variables: camelCase (createPayment, paymentId)
// Constants: SCREAMING_SNAKE_CASE (MAX_RETRY_COUNT)
// Packages: lowercase, reverse domain (com.hsbc.payment.service)
```

---

## 13.6 Agile Execution — What Senior Engineers Do Differently

### Sprint-Level Engineering Excellence

```
Story sizing:
- Senior engineers can identify hidden complexity ("this looks like 3 points 
  but the auth integration alone is 8 — let me explain why")
- Know what to spike vs estimate
- Know when to pull in an architect

PR strategy:
- Break large features into small, reviewable PRs
- Each PR should be independently mergeable (not depend on next PR)
- Feature flags for large features deployed incrementally

Estimation honesty:
- "I don't know, I need a day to spike" is the right answer
- Padding for code review, testing, documentation is legitimate
- Always ask: "is there an existing library or pattern for this?"

Technical debt management:
- Log debt immediately (tech debt ticket in backlog)
- Quantify the cost ("this N+1 query adds 200ms to every page load for 100k users")
- Advocate for scheduled debt payment ("we need 1 sprint per quarter for cleanup")
```

---

## Section Summary: Real Enterprise Engineering Mindset

**What distinguishes enterprise engineers:**

1. **Code review culture:** Every change reviewed. Reviews are about knowledge sharing, not gatekeeping.

2. **Documentation as first-class:** ADRs, runbooks, post-mortems are engineering artifacts.

3. **Testing discipline:** Unit tests, integration tests, contract tests — not optional.

4. **Observability by default:** Every service has health checks, metrics, distributed tracing from day one.

5. **Production ownership:** If you deployed it, you're responsible for its behavior in production.

6. **Blameless culture:** Post-mortems identify systemic issues, not scapegoats. "How did the system allow this mistake?" not "who made this mistake?"

7. **Gradual rollout:** Feature flags, canary deployments, blue-green — never ship directly to 100% of users.

8. **Backward compatibility:** APIs are contracts. Breaking changes need versioning and migration paths.

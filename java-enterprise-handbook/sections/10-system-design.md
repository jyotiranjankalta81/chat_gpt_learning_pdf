# Section 10: System Design

> **The Highest-Signal Interview Round:** System design interviews reveal your architectural thinking, trade-off judgment, and engineering maturity. At FAANG and banks, you're expected to design systems that handle millions of transactions reliably. This section gives you the frameworks, patterns, and real-world examples.

---

## 10.1 System Design Framework — How to Approach Interviews

### The 45-Minute Blueprint

```
Minutes 1-5:   Requirements clarification
Minutes 5-10:  Capacity estimation + constraints
Minutes 10-20: High-level design (HLD) — components and data flow
Minutes 20-35: Deep dive into critical components
Minutes 35-45: Trade-offs, bottlenecks, scaling strategies
```

### Clarifying Questions Template

```
Functional Requirements:
- What are the core use cases?
- Who are the users? What's the access pattern?
- Read-heavy or write-heavy?
- Real-time or eventual consistency acceptable?

Non-Functional Requirements:
- Scale: How many users/transactions per day?
- Latency: P99 < 200ms? P50 < 50ms?
- Availability: 99.9%? 99.99%? (9s vs 52 min/year downtime)
- Consistency: Strong vs eventual?
- Durability: How much data loss is acceptable?
- Geography: Single region or global?
```

---

## 10.2 Banking Payment System Design

### Problem: Design a Real-Time Payment Processing System

**Requirements:**
- 50,000 transactions/second peak
- P99 latency < 500ms
- Exactly-once processing (no duplicate payments)
- Immutable audit trail
- Regulatory compliance (all transactions logged)
- Multi-currency support

### Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Payment System Architecture                        │
│                                                                          │
│  Mobile/Web App                                                          │
│       │                                                                  │
│       ▼                                                                  │
│  ┌──────────┐    Rate     ┌─────────────────────────────────────────┐  │
│  │   API    │   Limit     │              API Gateway                │  │
│  │ Gateway  │◀────────────│  - Auth (JWT validation)                │  │
│  └──────────┘             │  - Rate limiting (per user/IP)          │  │
│       │                   │  - Request routing                      │  │
│       │                   └─────────────────────────────────────────┘  │
│       │                                                                  │
│  ┌────▼──────────────────────────────────────────────────────────────┐ │
│  │              Payment Service (Spring Boot, stateless)             │ │
│  │  - Idempotency check (Redis)                                      │ │
│  │  - Validation                                                     │ │
│  │  - Balance reservation                                            │ │
│  │  - Event publishing                                               │ │
│  └───────────────┬──────────────────────────────────────────────────┘ │
│                  │                                                       │
│         ┌────────▼──────────────────────────┐                          │
│         │        Kafka (Event Bus)           │                          │
│         │  Topics: payment.initiated         │                          │
│         │          payment.completed         │                          │
│         │          payment.failed            │                          │
│         └────────┬─────────────┬────────────┘                          │
│                  │             │                                         │
│      ┌───────────▼──┐    ┌────▼───────────┐                           │
│      │  Clearing    │    │ Notification   │                            │
│      │  Engine      │    │ Service        │                            │
│      │  (SWIFT/ACH) │    │ (SMS/Email)    │                            │
│      └──────────────┘    └────────────────┘                            │
│                                                                          │
│  Databases:                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ PostgreSQL   │  │    Redis     │  │Elasticsearch │                 │
│  │ (Accounts,  │  │ (Idempotency,│  │ (Transaction │                 │
│  │  Payments)  │  │  Sessions,   │  │  Search,     │                 │
│  │  Primary +  │  │  Rate limit) │  │  Reporting)  │                 │
│  │  Replicas   │  └──────────────┘  └──────────────┘                 │
│  └──────────────┘                                                       │
└────────────────────────────────────────────────────────────────────────┘
```

### Deep Dive: Exactly-Once Payment Processing

```java
@Service
@Slf4j
public class PaymentProcessor {

    @Transactional
    public PaymentResponse initiatePayment(PaymentRequest request, String idempotencyKey) {

        // 1. Check idempotency (Redis — fast, distributed)
        String cached = redisTemplate.opsForValue().get("idem:" + idempotencyKey);
        if (cached != null) {
            return objectMapper.readValue(cached, PaymentResponse.class);
        }

        // 2. Reserve idempotency slot (with expiry to handle crashes)
        Boolean reserved = redisTemplate.opsForValue()
            .setIfAbsent("idem:" + idempotencyKey, "PROCESSING", Duration.ofMinutes(5));
        if (!Boolean.TRUE.equals(reserved)) {
            throw new ConflictException("Payment already in progress");
        }

        try {
            // 3. Validate and reserve funds
            Account fromAccount = accountRepo.findByIdForUpdate(request.getFromAccountId());
            validateAndReserveFunds(fromAccount, request.getAmount());

            // 4. Create payment record
            Payment payment = paymentRepo.save(new Payment(request, PaymentStatus.RESERVED));

            // 5. Publish to Kafka with Outbox pattern (transactional)
            outboxRepo.save(new OutboxMessage(
                "payment.initiated",
                payment.getId().toString(),
                objectMapper.writeValueAsString(PaymentEvent.from(payment))
            ));

            PaymentResponse response = PaymentResponse.from(payment);

            // 6. Cache response for idempotency
            redisTemplate.opsForValue().set("idem:" + idempotencyKey,
                objectMapper.writeValueAsString(response),
                Duration.ofHours(24));

            return response;

        } catch (Exception e) {
            redisTemplate.delete("idem:" + idempotencyKey);
            throw e;
        }
    }
}
```

---

## 10.3 Distributed Caching with Redis — Patterns

### Cache Patterns

```java
// Cache-Aside (most common)
@Service
public class AccountService {

    public Account getAccount(String accountId) {
        // 1. Check cache
        Account cached = redisTemplate.opsForValue().get("account:" + accountId);
        if (cached != null) return cached;

        // 2. Cache miss — query DB
        Account account = accountRepo.findById(accountId)
            .orElseThrow(() -> new AccountNotFoundException(accountId));

        // 3. Populate cache
        redisTemplate.opsForValue().set("account:" + accountId, account, Duration.ofMinutes(5));
        return account;
    }

    // Invalidate on update
    @CacheEvict(value = "accounts", key = "#account.id")
    public Account updateAccount(Account account) {
        return accountRepo.save(account);
    }
}

// Write-Through — write to cache and DB simultaneously
@Transactional
public void updateBalance(String accountId, BigDecimal newBalance) {
    accountRepo.updateBalance(accountId, newBalance);
    redisTemplate.opsForValue().set("balance:" + accountId, newBalance, Duration.ofMinutes(10));
}

// Read-Through — Spring @Cacheable (auto cache + DB)
@Cacheable(value = "currencies", key = "#code", unless = "#result == null")
public Currency getCurrency(String code) {
    return currencyRepo.findByCode(code).orElse(null);
}
```

### Redis Data Structures for Enterprise Use

```java
// Rate limiting with sliding window (Redis sorted set)
public boolean isAllowed(String clientId) {
    long now = System.currentTimeMillis();
    long windowStart = now - WINDOW_SIZE_MS;
    String key = "ratelimit:" + clientId;

    // Remove expired entries
    redisTemplate.opsForZSet().removeRangeByScore(key, 0, windowStart);

    // Count requests in window
    Long count = redisTemplate.opsForZSet().count(key, windowStart, now);
    if (count < MAX_REQUESTS) {
        redisTemplate.opsForZSet().add(key, now + "-" + UUID.randomUUID(), now);
        redisTemplate.expire(key, Duration.ofMillis(WINDOW_SIZE_MS));
        return true;
    }
    return false;
}

// Distributed lock (Redisson)
RLock lock = redisson.getLock("transfer:" + accountId);
try {
    if (lock.tryLock(3, 10, TimeUnit.SECONDS)) {  // Wait 3s, hold 10s max
        try {
            performTransfer(accountId, amount);
        } finally {
            lock.unlock();
        }
    } else {
        throw new ConcurrentTransferException("Transfer already in progress");
    }
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    throw new RuntimeException("Lock interrupted", e);
}

// Leaderboard (sorted set)
redisTemplate.opsForZSet().incrementScore("payment:volumes:daily", merchantId, amount.doubleValue());
Set<ZSetOperations.TypedTuple<String>> topMerchants =
    redisTemplate.opsForZSet().reverseRangeWithScores("payment:volumes:daily", 0, 9);
```

### Cache Invalidation Strategies

```
1. TTL-based (simplest): data expires after N seconds
   → Risk: stale data up to TTL
   → Use for: reference data (currencies, countries), user preferences

2. Event-driven invalidation:
   PaymentUpdated event → evict payment:* keys
   → Use for: frequently-changing data that needs near-real-time consistency

3. Cache stampede prevention:
   When cache expires, many requests hit DB simultaneously
   → Solution: Probabilistic early expiration (refresh before expiry)
   → Solution: Locking (only one thread fetches, rest wait)

4. Write-through/write-behind:
   Always write to cache + DB
   → Guarantees freshness
   → Use for: hot data (balances, session state)
```

---

## 10.4 Notification System Design

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                     Notification Platform                        │
│                                                                   │
│  Events from services → Kafka → Notification Service            │
│                                                                   │
│  Notification Service:                                           │
│  1. Consume event                                                │
│  2. Load user preferences (channel: email/SMS/push)             │
│  3. Load template                                                │
│  4. Route to appropriate channel                                 │
│                                                                   │
│  Channels:                                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Email   │ │  SMS     │ │  Push    │ │  In-App (WebSocket│  │
│  │ (SES/    │ │ (Twilio/ │ │  (FCM/   │ │   / SSE)         │   │
│  │ SendGrid)│ │ AWS SNS) │ │  APNs)   │ │                  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│                                                                   │
│  Delivery tracking: status updates back to Kafka                 │
└─────────────────────────────────────────────────────────────────┘
```

```java
// Template-driven notification system
@Service
public class NotificationService {

    @KafkaListener(topics = "payment.completed")
    public void handlePaymentCompleted(PaymentCompletedEvent event) {
        UserPreferences prefs = userPrefService.getPreferences(event.getUserId());

        NotificationContext context = NotificationContext.builder()
            .userId(event.getUserId())
            .templateId("PAYMENT_COMPLETED")
            .data(Map.of(
                "amount", event.getAmount(),
                "currency", event.getCurrency(),
                "recipientName", event.getRecipientName(),
                "timestamp", event.getCompletedAt()
            ))
            .build();

        // Send via preferred channels
        if (prefs.isEmailEnabled()) {
            emailChannel.send(context, prefs.getEmail());
        }
        if (prefs.isSmsEnabled()) {
            smsChannel.send(context, prefs.getPhoneNumber());
        }
        if (prefs.isPushEnabled()) {
            pushChannel.send(context, prefs.getDeviceTokens());
        }
    }
}
```

---

## 10.5 URL Shortener — LLD + HLD

**This is a classic interview system design question:**

```
HLD:
User → POST /shorten → ShortenerService → generate shortCode → store mapping
User → GET /{code} → RedirectService → lookup code → 301 redirect

Core Design Decisions:
1. Short code generation:
   - Option A: Base62 encode auto-increment DB ID (simple, predictable → security risk)
   - Option B: MD5/SHA hash of URL (collision risk)
   - Option C: Random base62 (best: unpredictable, no collision if long enough)

2. Storage: Redis for hot redirects + PostgreSQL for persistence
3. Scale: 10B URLs, 1K writes/sec, 10K reads/sec
   → Read:write ratio 10:1 → cache-heavy

4. Short code length:
   6 chars × 62 options = 56 billion combinations (sufficient for years)
```

```java
@Service
public class UrlShortenerService {

    private final UrlRepository urlRepo;
    private final StringRedisTemplate redis;

    public String shorten(String longUrl, String userId) {
        // Idempotent: same URL from same user gets same code
        Optional<String> existing = urlRepo.findCodeByUrlAndUser(longUrl, userId);
        if (existing.isPresent()) return buildShortUrl(existing.get());

        String code = generateCode();
        while (urlRepo.existsByCode(code)) {
            code = generateCode();  // Rare collision retry
        }

        urlRepo.save(new ShortUrl(code, longUrl, userId, Instant.now()));
        redis.opsForValue().set("url:" + code, longUrl, Duration.ofDays(30));
        return buildShortUrl(code);
    }

    public String redirect(String code) {
        // Cache hit: O(1) Redis lookup
        String longUrl = redis.opsForValue().get("url:" + code);
        if (longUrl != null) return longUrl;

        // Cache miss: DB lookup + repopulate cache
        return urlRepo.findByCode(code)
            .map(url -> {
                redis.opsForValue().set("url:" + code, url.getLongUrl(), Duration.ofDays(30));
                return url.getLongUrl();
            })
            .orElseThrow(() -> new UrlNotFoundException(code));
    }

    private String generateCode() {
        return RandomStringUtils.randomAlphanumeric(6);
    }
}
```

---

## 10.6 Scalability Patterns

### Database Scaling

```
Vertical: Bigger server (limited, expensive)
Horizontal Read: Add read replicas (scales reads, not writes)
Horizontal Write: Sharding

Sharding strategies:
  Range-based: accounts A-M → Shard 1, N-Z → Shard 2
    → Simple but uneven distribution (hotspots)

  Hash-based: hash(accountId) % N → shard number
    → Even distribution, but resharding is painful

  Directory-based: lookup table maps entity → shard
    → Flexible, but lookup table becomes bottleneck

For banking: AVOID sharding if possible
  Use: Connection pooling, read replicas, caching, efficient queries
  Last resort: Logical sharding at application level
```

### API Design for Scale

```java
// Cursor-based pagination (better than offset for large datasets)
@GetMapping("/payments")
public CursorPage<PaymentResponse> listPayments(
        @RequestParam(required = false) String cursor,
        @RequestParam(defaultValue = "20") int limit) {

    UUID lastId = cursor != null ? decodeCursor(cursor) : null;
    List<Payment> payments = paymentRepo.findAfterCursor(lastId, limit + 1);

    boolean hasMore = payments.size() > limit;
    List<Payment> page = hasMore ? payments.subList(0, limit) : payments;

    String nextCursor = hasMore ? encodeCursor(page.get(page.size() - 1).getId()) : null;
    return new CursorPage<>(page.stream().map(PaymentResponse::from).toList(), nextCursor);
}

// Repository using cursor
@Query("""
    SELECT p FROM Payment p
    WHERE (:cursor IS NULL OR p.id > :cursor)
    ORDER BY p.id ASC
    LIMIT :limit
    """)
List<Payment> findAfterCursor(UUID cursor, int limit);
```

---

## Section Summary: System Design Interview Topics

**Essential designs to practice:**

1. **Payment processing system** (banks will ask this)
2. **Notification platform** (commonly asked)
3. **URL shortener** (classic LLD + HLD)
4. **Rate limiter** (real implementation at every company)
5. **Distributed cache** (Redis patterns)
6. **API gateway** (routing, auth, rate limiting)
7. **Event-driven microservices** (Kafka-based system)
8. **Read-heavy system** (caching layers, read replicas)
9. **Write-heavy system** (buffering, batching, async writes)
10. **Search system** (Elasticsearch integration)

**Framework to evaluate trade-offs:**
- Latency vs consistency
- Throughput vs durability
- Simplicity vs scalability
- Cost vs performance

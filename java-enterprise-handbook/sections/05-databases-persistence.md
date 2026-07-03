# Section 5: Databases & Persistence

> **Enterprise Reality:** Database performance and correctness separate junior from senior engineers. At banks and FAANG, every senior interview includes transaction isolation, deadlocks, N+1 queries, and connection pool sizing. If you can't explain `SERIALIZABLE` vs `READ COMMITTED` and when to use each, you're not ready for the room.

---

## 5.1 Transaction Isolation Levels — Deep Dive

### The Four Problems Transactions Solve

```
1. Dirty Read:     Read uncommitted data from another transaction
2. Non-Repeatable Read: Row read twice within same transaction returns different data
3. Phantom Read:   Query returns different set of rows when repeated (rows added/deleted)
4. Lost Update:    Two transactions both read-modify-write, one overwrites the other
```

### Isolation Levels vs Problems

```
                     Dirty  Non-Repeatable  Phantom   Lost
                     Read   Read            Read      Update
──────────────────────────────────────────────────────────────
READ UNCOMMITTED     ✓ Possible ✓ Possible  ✓ Possible ✓ Possible
READ COMMITTED       ✗ Prevented ✓ Possible ✓ Possible ✓ Possible
REPEATABLE READ      ✗ ✗ Prevented         ✓ Possible ✗ Prevented
SERIALIZABLE         ✗ ✗                   ✗ Prevented ✗ Prevented

✓ = problem can occur   ✗ = prevented by this level
```

### Real Enterprise Usage

```java
// READ_COMMITTED — DEFAULT for most operations
// Performance: Good | Use: CRUD, reads, most writes
@Transactional(isolation = Isolation.READ_COMMITTED)
public UserProfile updateProfile(String userId, UpdateRequest request) { ... }

// REPEATABLE_READ — Balances, running totals
// Performance: Moderate | Use: Balance checks, inventory
@Transactional(isolation = Isolation.REPEATABLE_READ)
public void checkAndReserveInventory(String productId, int quantity) {
    Product product = repo.findById(productId);  // Row locked for this transaction
    // product.quantity won't change even if another transaction updates it
    if (product.getQuantity() >= quantity) {
        product.setQuantity(product.getQuantity() - quantity);
        repo.save(product);
    }
}

// SERIALIZABLE — Financial transfers, double-spend prevention
// Performance: Slowest | Use: Money movement, compliance-critical
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transferFunds(String fromId, String toId, BigDecimal amount) {
    // No concurrent transaction can see partial state
    Account from = accountRepo.findById(fromId);
    Account to = accountRepo.findById(toId);
    // Debit and credit atomically, serialized with all other transfers
}
```

---

## 5.2 Database Locking

### Optimistic vs Pessimistic Locking

```
Optimistic Locking:
- No locks held during read
- At write time: check version hasn't changed
- If version conflict → retry
- Use when: Low contention, long-lived operations, distributed reads
- In JPA: @Version annotation

Pessimistic Locking:
- Acquire lock immediately at read time (SELECT FOR UPDATE)
- Hold lock until transaction commits
- Blocking — other transactions wait
- Use when: High contention, MUST succeed, short operations
```

```java
// Optimistic locking with @Version
@Entity
public class Account {
    @Id private UUID id;
    private BigDecimal balance;

    @Version  // JPA adds WHERE version = :expectedVersion on UPDATE
    private Long version;
}

// If two threads both read account at version=5 and both try to update:
// Thread 1: UPDATE accounts SET balance=900, version=6 WHERE id=? AND version=5 → succeeds
// Thread 2: UPDATE accounts SET balance=850, version=6 WHERE id=? AND version=5 → 0 rows → OptimisticLockException

// Handle optimistic lock conflicts:
@Retryable(value = OptimisticLockingFailureException.class, maxAttempts = 3)
@Transactional
public void transfer(String fromId, String toId, BigDecimal amount) {
    // Spring-Retry will retry this method on version conflict
}

// Pessimistic locking with JPQL
@Repository
public interface AccountRepository extends JpaRepository<Account, UUID> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)  // SELECT ... FOR UPDATE
    @Query("SELECT a FROM Account a WHERE a.id = :id")
    Optional<Account> findByIdForUpdate(@Param("id") UUID id);

    @Lock(LockModeType.PESSIMISTIC_READ)   // SELECT ... FOR SHARE
    @Query("SELECT a FROM Account a WHERE a.accountNumber = :num")
    Optional<Account> findByAccountNumberForRead(@Param("num") String num);
}
```

### Deadlock Prevention

```
Deadlock scenario:
Thread 1: Lock Account A → waiting for Account B
Thread 2: Lock Account B → waiting for Account A
→ Deadlock!

Prevention strategy: ALWAYS acquire locks in the same order
```

```java
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transfer(String fromId, String toId, BigDecimal amount) {
    // Sort IDs to ensure consistent lock acquisition order
    // Prevents deadlock between concurrent transfers
    List<String> sortedIds = List.of(fromId, toId).stream()
        .sorted()
        .toList();

    // Acquire locks in deterministic order
    Account first = accountRepo.findByIdForUpdate(UUID.fromString(sortedIds.get(0)));
    Account second = accountRepo.findByIdForUpdate(UUID.fromString(sortedIds.get(1)));

    Account from = fromId.equals(sortedIds.get(0)) ? first : second;
    Account to = toId.equals(sortedIds.get(0)) ? first : second;

    from.debit(amount);
    to.credit(amount);
}
```

---

## 5.3 Connection Pooling — HikariCP

HikariCP is the Spring Boot default and fastest Java connection pool. Sizing it correctly is critical:

```java
@Configuration
public class DataSourceConfig {

    @Bean
    @ConfigurationProperties("spring.datasource.hikari")
    public DataSource dataSource() {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl(dbUrl);
        ds.setUsername(dbUser);
        ds.setPassword(dbPassword);

        // Pool sizing formula: connections = (core_count * 2) + effective_spindle_count
        // For 4-core server with SSD: ~9 connections per pod
        ds.setMaximumPoolSize(10);
        ds.setMinimumIdle(5);

        // Timeouts (critical for production)
        ds.setConnectionTimeout(30000);    // 30s wait for available connection
        ds.setIdleTimeout(600000);         // 10min: remove idle connections
        ds.setMaxLifetime(1800000);        // 30min: force connection refresh
        ds.setKeepaliveTime(60000);        // Ping every 60s to prevent firewall timeout

        // Validation
        ds.setConnectionTestQuery("SELECT 1");

        // Metrics
        ds.setMetricRegistry(meterRegistry);

        return ds;
    }
}

# application.yml equivalent
spring:
  datasource:
    hikari:
      maximum-pool-size: 10
      minimum-idle: 5
      connection-timeout: 30000
      idle-timeout: 600000
      max-lifetime: 1800000
      keepalive-time: 60000
      pool-name: PaymentServicePool
```

### Connection Pool Exhaustion — Diagnosing in Production

```
Symptoms: Requests hang or return 500 with "Unable to acquire JDBC Connection"
Causes:
1. Pool too small for load
2. Long-running transactions holding connections
3. Missing connection.close() (resource leak)
4. Database is slow (connections busy waiting for DB response)

Diagnosis:
- Check HikariCP metrics: hikaricp.connections.active vs hikaricp.connections.max
- Thread dump: many threads in "waiting for connection" state
- Trace slow queries: look for queries > 100ms that hold connections

Fix:
1. Identify slow queries → optimize or add index
2. Ensure @Transactional transactions are short-lived
3. Increase pool size (but beware DB connection limit)
4. Use connection leak detection: spring.datasource.hikari.leak-detection-threshold=2000
```

---

## 5.4 ORM Internals — Hibernate Deep Dive

### The N+1 Problem — Most Common JPA Bug

```java
// N+1 problem:
List<Order> orders = orderRepo.findAll();  // 1 query: SELECT * FROM orders
for (Order order : orders) {
    order.getCustomer().getName();  // N queries: SELECT * FROM customers WHERE id=?
}
// For 1000 orders = 1001 database queries!

// Solution 1: JOIN FETCH in JPQL
@Query("SELECT o FROM Order o JOIN FETCH o.customer WHERE o.status = :status")
List<Order> findByStatusWithCustomer(@Param("status") OrderStatus status);

// Solution 2: @EntityGraph
@EntityGraph(attributePaths = {"customer", "items", "items.product"})
List<Order> findByStatus(OrderStatus status);

// Solution 3: @BatchSize for collections
@OneToMany(mappedBy = "order")
@BatchSize(size = 100)  // Load 100 at a time instead of 1
private List<OrderItem> items;

// Solution 4: DTO projection (best for read-only views)
@Query("""
    SELECT new com.example.dto.OrderSummaryDto(
        o.id, o.createdAt, c.name, SUM(i.price * i.quantity))
    FROM Order o
    JOIN o.customer c
    JOIN o.items i
    WHERE o.status = :status
    GROUP BY o.id, o.createdAt, c.name
    """)
List<OrderSummaryDto> findOrderSummaries(@Param("status") OrderStatus status);
```

### Hibernate Session and Persistence Context

```
Persistence Context (first-level cache) = Map<EntityKey, Entity> per Session

When you call repo.findById(id):
1. Check persistence context (first-level cache)
2. If found → return cached version (no DB query!)
3. If not found → query DB, store in cache, return

This is why:
Entity a = repo.findById(1);  // DB query
Entity b = repo.findById(1);  // Returns SAME object, no DB query
a == b  // true — same object reference!

Implications:
- Within same @Transactional method, reading same entity twice = one DB hit
- dirty checking: Hibernate tracks entity state changes automatically
  → if you change a field of a managed entity, Hibernate will UPDATE on commit
  → no need to explicitly call save() for changes within transaction!
```

### Hibernate Caching — Second Level Cache

```java
// L2 Cache: Shared across sessions, reduces DB hits
@Entity
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)  // Cacheable entity
public class Currency {
    @Id private String code;
    private String name;
    private int decimalPlaces;
    // Reference data — rarely changes, read millions of times
}

@Repository
public interface CurrencyRepository extends JpaRepository<Currency, String> {
    @Cacheable("currencies")  // Spring Cache abstraction over L2
    Optional<Currency> findByCode(String code);
}

# application.yml
spring:
  jpa:
    properties:
      hibernate:
        cache:
          use_second_level_cache: true
          use_query_cache: true
          region.factory_class: org.hibernate.cache.jcache.JCacheRegionFactory
        javax.cache.missing_cache_strategy: create
```

---

## 5.5 SQL Optimization

### Index Strategy

```sql
-- B-tree index (default) — range queries, =, >, <, BETWEEN, LIKE 'prefix%'
CREATE INDEX idx_payments_account_created ON payments(account_id, created_at DESC);

-- Covering index — all query columns in index (no table lookup)
CREATE INDEX idx_payments_status_covering
  ON payments(status, created_at)
  INCLUDE (amount, currency);  -- PostgreSQL syntax

-- Partial index — index only subset of rows
CREATE INDEX idx_active_subscriptions
  ON subscriptions(user_id, renewed_at)
  WHERE status = 'ACTIVE';  -- Only active records, much smaller index

-- When to index:
-- ✓ Frequently filtered columns (WHERE clause)
-- ✓ JOIN columns (foreign keys)
-- ✓ ORDER BY columns (eliminates sort)
-- ✗ Low-cardinality columns (boolean, status with 2-3 values)
-- ✗ Columns rarely queried
-- ✗ Very small tables (full scan is faster)
-- ✗ Columns updated very frequently (index maintenance cost)
```

### EXPLAIN ANALYZE — Reading Query Plans

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) 
SELECT p.id, p.amount, a.name
FROM payments p
JOIN accounts a ON p.account_id = a.id
WHERE p.status = 'PENDING'
  AND p.created_at > NOW() - INTERVAL '7 days'
ORDER BY p.created_at DESC
LIMIT 100;

-- Key things to look for:
-- Seq Scan → Full table scan (add index?)
-- Index Scan → Using index (good)
-- Index Only Scan → Covering index hit (best)
-- Hash Join → For large result sets (normal)
-- Nested Loop → For small result sets (normal)
-- Rows: actual vs estimated → large difference = stale statistics (ANALYZE table)
-- Buffers hit/read → cache hits vs disk reads
```

### Common Query Anti-Patterns

```sql
-- 1. Function on indexed column (prevents index use)
-- BAD:
WHERE YEAR(created_at) = 2024
-- GOOD:
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'

-- 2. Leading wildcard (prevents B-tree use)
-- BAD:
WHERE name LIKE '%Smith%'
-- GOOD: Use full-text search (PostgreSQL tsvector, Elasticsearch)

-- 3. OR conditions on different columns (can't use composite index)
-- BAD:
WHERE account_id = '123' OR transaction_id = '456'
-- GOOD: UNION (can use separate indexes)
SELECT * FROM payments WHERE account_id = '123'
UNION
SELECT * FROM payments WHERE transaction_id = '456'

-- 4. SELECT * (over-fetches data, prevents covering index)
-- BAD:
SELECT * FROM payments WHERE account_id = ?
-- GOOD:
SELECT id, amount, status, created_at FROM payments WHERE account_id = ?

-- 5. COUNT(*) on large tables without index
-- Use approximate counts: pg_stat_user_tables.n_live_tup
```

---

## 5.6 Database Migrations — Flyway & Liquibase

### Flyway — Convention-Based Migration

```
db/migration/
├── V1__create_payments_table.sql
├── V2__add_idempotency_key.sql
├── V3__create_accounts_table.sql
└── V4__add_transfer_table.sql

Naming: V{version}__{description}.sql
V = versioned, R = repeatable, U = undo
```

```sql
-- V1__create_payments_table.sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id VARCHAR(50) NOT NULL,
    amount NUMERIC(19, 4) NOT NULL,
    currency CHAR(3) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    idempotency_key VARCHAR(100) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    version BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX idx_payments_account_id ON payments(account_id);
CREATE INDEX idx_payments_status_created ON payments(status, created_at DESC);

-- V2__add_payment_metadata.sql
ALTER TABLE payments
    ADD COLUMN description VARCHAR(500),
    ADD COLUMN metadata JSONB;

CREATE INDEX idx_payments_metadata ON payments USING gin(metadata);
```

```java
// Spring Boot auto-applies migrations on startup
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: false    # True for existing DBs
    validate-on-migrate: true     # Fail if migration checksums change
    out-of-order: false           # Fail if migration applied out of order
```

### Liquibase — XML/YAML-Based (More Enterprise Features)

```yaml
# db/changelog/db.changelog-master.yaml
databaseChangeLog:
  - include:
      file: db/changelog/changes/001-create-payments.yaml
  - include:
      file: db/changelog/changes/002-add-indexes.yaml

# db/changelog/changes/001-create-payments.yaml
databaseChangeLog:
  - changeSet:
      id: 001
      author: engineering-team
      changes:
        - createTable:
            tableName: payments
            columns:
              - column:
                  name: id
                  type: UUID
                  constraints:
                    primaryKey: true
              - column:
                  name: amount
                  type: DECIMAL(19,4)
                  constraints:
                    nullable: false
      rollback:
        - dropTable:
            tableName: payments
```

### Migration Strategy in Production

```
NEVER:
- hibernate.ddl-auto = create/update (wipes/corrupts production data)
- Apply migrations directly on production DB without testing on staging
- Modify existing migrations (Flyway validates checksums)
- Deploy code and migration simultaneously (downtime risk)

ALWAYS:
- Test migrations on staging with production data copy
- Use backwards-compatible migrations
- Add-only approach: add column with default, populate, then add NOT NULL constraint
- Feature flags for new columns while migrating
- Blue/green deployment: migrate DB first, then deploy new code

Safe migration sequence for addding NOT NULL column:
  Step 1: Add column as nullable (deploy, old code ignores it)
  Step 2: Backfill existing rows (batch update)
  Step 3: Add NOT NULL constraint (deploy new code using it)
```

---

## 5.7 Read Replicas & CQRS at DB Level

```java
// Routing reads to replica, writes to primary
@Configuration
public class DataSourceRoutingConfig {

    @Bean
    public DataSource routingDataSource(
            @Qualifier("primaryDataSource") DataSource primary,
            @Qualifier("replicaDataSource") DataSource replica) {

        AbstractRoutingDataSource routing = new AbstractRoutingDataSource() {
            @Override
            protected Object determineCurrentLookupKey() {
                // Use replica for read-only transactions
                return TransactionSynchronizationManager.isCurrentTransactionReadOnly()
                    ? "REPLICA" : "PRIMARY";
            }
        };

        routing.setTargetDataSources(Map.of("PRIMARY", primary, "REPLICA", replica));
        routing.setDefaultTargetDataSource(primary);
        return routing;
    }
}

// Mark read-only services
@Service
public class ReportingService {

    @Transactional(readOnly = true)  // → routes to replica
    public List<PaymentSummary> getMonthlyReport(YearMonth month) { ... }
}
```

---

## Section Summary: Database Interview Must-Know

**Questions asked at every bank interview:**

1. "Explain transaction isolation levels. When would you use SERIALIZABLE?"
2. "What is the N+1 problem and how do you solve it?"
3. "How would you handle concurrent balance updates in a banking system?"
4. "Explain optimistic vs pessimistic locking and when to use each"
5. "How does HikariCP work? How do you size the pool?"
6. "How do you run database migrations safely in production?"
7. "How would you optimize a query returning results too slowly?"
8. "What is dirty checking in Hibernate?"
9. "How do you prevent deadlocks in database transactions?"
10. "Explain the difference between first-level and second-level cache in Hibernate"

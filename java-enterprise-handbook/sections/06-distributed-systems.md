# Section 6: Distributed Systems

> **The Differentiator:** Distributed systems knowledge separates engineers who can "code features" from engineers who design systems that "work at scale." At Goldman Sachs and Stripe, you're expected to discuss CAP theorem, Kafka ordering guarantees, and saga patterns in a 45-minute conversation.

---

## 6.1 Kafka Deep Dive

### Node.js → Kafka Mental Model

```
Node.js EventEmitter:       Kafka:
─────────────────────────────────────────────────
In-process pub/sub          Distributed pub/sub
Lost if process dies        Durable (configurable retention)
No replay                   Fully replayable
No ordering guarantee       Ordered within partition
No backpressure             Configurable consumer lag
```

### Kafka Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Kafka Cluster                                │
│                                                                       │
│  Topic: "payment.created"                                            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Partition 0: [msg0] [msg3] [msg6] → offset grows           │   │
│  │  Partition 1: [msg1] [msg4] [msg7]                           │   │
│  │  Partition 2: [msg2] [msg5] [msg8]                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  Producer → chooses partition (by key or round-robin)               │
│  Consumer Group "notification-svc": each partition → one consumer  │
│  Consumer Group "audit-svc": independent read from same topic       │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Kafka Guarantees

```
At-most-once:   Message may be lost, never duplicated
                → Producer: acks=0, Consumer: commit before processing

At-least-once:  Message never lost, may be duplicated
                → Producer: acks=1 or all, Consumer: process then commit
                → DEFAULT in most enterprise setups (requires idempotent consumer)

Exactly-once:   Never lost, never duplicated
                → Kafka Transactions + Idempotent Producer
                → Most complex, significant performance cost
                → Use for: financial ledger, inventory deduction

Ordering:
- Within a partition: STRICTLY ORDERED
- Across partitions: NO ORDER GUARANTEE
→ All events for the same entity (same accountId) must go to same partition
→ Use entity ID as partition key
```

### Spring Kafka — Production Configuration

```java
// Producer Configuration
@Configuration
public class KafkaProducerConfig {

    @Bean
    public ProducerFactory<String, PaymentEvent> producerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        config.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);

        // Reliability settings
        config.put(ProducerConfig.ACKS_CONFIG, "all");           // Leader + all replicas ack
        config.put(ProducerConfig.RETRIES_CONFIG, 10);
        config.put(ProducerConfig.RETRY_BACKOFF_MS_CONFIG, 1000);
        config.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true); // Exactly-once producer

        // Performance settings
        config.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "lz4");
        config.put(ProducerConfig.LINGER_MS_CONFIG, 5);          // Batch for 5ms
        config.put(ProducerConfig.BATCH_SIZE_CONFIG, 32 * 1024); // 32KB batch

        return new DefaultKafkaProducerFactory<>(config);
    }
}

// Consumer Configuration
@Configuration
public class KafkaConsumerConfig {

    @Bean
    public ConsumerFactory<String, PaymentEvent> consumerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        config.put(ConsumerConfig.GROUP_ID_CONFIG, "notification-service");
        config.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        config.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);

        // At-least-once: manual commit after processing
        config.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);
        config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");

        // Performance
        config.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500);         // Process 500 at once
        config.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, 300000);  // 5min to process batch

        return new DefaultKafkaConsumerFactory<>(config);
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, PaymentEvent>
            containerFactory(ConsumerFactory<String, PaymentEvent> factory) {

        ConcurrentKafkaListenerContainerFactory<String, PaymentEvent> container =
            new ConcurrentKafkaListenerContainerFactory<>();
        container.setConsumerFactory(factory);
        container.setConcurrency(3);  // 3 threads = 3 partitions consumed in parallel

        // Manual offset management
        container.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL);

        // Error handling with DLQ
        container.setCommonErrorHandler(new DefaultErrorHandler(
            new DeadLetterPublishingRecoverer(kafkaTemplate),
            new FixedBackOff(1000L, 3)  // 3 retries, 1s apart
        ));

        return container;
    }
}

// Consumer Implementation
@Component
@Slf4j
public class PaymentEventConsumer {

    @KafkaListener(
        topics = "payment.created",
        groupId = "notification-service",
        containerFactory = "containerFactory"
    )
    public void handlePaymentCreated(
            @Payload PaymentEvent event,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment acknowledgment) {

        log.info("Processing payment event: id={} partition={} offset={}",
            event.getPaymentId(), partition, offset);

        try {
            // IDEMPOTENT PROCESSING — check if already processed
            if (processedEventRepo.existsById(event.getEventId())) {
                log.info("Duplicate event, skipping: {}", event.getEventId());
                acknowledgment.acknowledge();  // Still ack — already processed
                return;
            }

            notificationService.sendPaymentNotification(event);
            processedEventRepo.save(event.getEventId());
            acknowledgment.acknowledge();  // Commit offset after successful processing

        } catch (RetryableException e) {
            log.warn("Retryable error for event {}: {}", event.getEventId(), e.getMessage());
            throw e;  // DLQ handler will retry 3 times then send to DLQ
        } catch (NonRetryableException e) {
            log.error("Non-retryable error for event {}, sending to DLQ", event.getEventId());
            acknowledgment.acknowledge();  // Don't block queue — handle separately
            deadLetterService.record(event, e);
        }
    }
}
```

### Dead Letter Queue (DLQ) Pattern

```java
// DLQ processor — handles failed messages
@Component
public class DlqProcessor {

    @KafkaListener(topics = "payment.created.DLT")  // DLT = Dead Letter Topic
    public void processDlq(PaymentEvent event,
                           @Header("kafka_dlt-original-topic") String originalTopic,
                           @Header("kafka_dlt-exception-message") String error) {
        log.error("DLQ message from topic={} error={} eventId={}",
            originalTopic, error, event.getEventId());

        // Options:
        // 1. Alert on-call engineer
        alerting.critical("Kafka DLQ message requires attention: " + event.getEventId());

        // 2. Save for manual review
        dlqRepository.save(new DlqRecord(event, error));

        // 3. Attempt compensating action
        compensationService.handleFailedPaymentEvent(event);
    }
}
```

---

## 6.2 Event Sourcing

### What It Is

```
Traditional: Store current state only
  accounts table: { id, balance=900, status=ACTIVE, updated_at }

Event Sourcing: Store all events, derive state
  events table: { id=1, type=ACCOUNT_OPENED, amount=1000, ts }
                { id=2, type=CREDIT, amount=500, ts }
                { id=3, type=DEBIT, amount=600, ts }
  Current state = replay all events → balance = 1000 + 500 - 600 = 900

Benefits:
- Complete audit trail (required by banking regulators)
- Time travel (reconstruct state at any point)
- Event replay for new features
- Natural Kafka integration

Challenges:
- Query complexity (need projections/snapshots)
- Storage growth
- Schema evolution of events
- Eventual consistency in read models
```

```java
// Event store
public interface EventStore {
    void append(String aggregateId, List<DomainEvent> events, long expectedVersion);
    List<DomainEvent> loadEvents(String aggregateId);
    List<DomainEvent> loadEvents(String aggregateId, long fromVersion);
}

// Account aggregate — reconstituted from events
public class AccountAggregate {
    private UUID id;
    private BigDecimal balance;
    private AccountStatus status;
    private long version = 0;

    private final List<DomainEvent> uncommittedEvents = new ArrayList<>();

    // Reconstitute from event history
    public static AccountAggregate from(List<DomainEvent> events) {
        AccountAggregate account = new AccountAggregate();
        events.forEach(account::apply);
        return account;
    }

    // Business method — validates and creates event
    public void debit(BigDecimal amount) {
        if (status != AccountStatus.ACTIVE) {
            throw new IllegalStateException("Account is not active");
        }
        if (balance.compareTo(amount) < 0) {
            throw new InsufficientFundsException(amount, balance);
        }
        apply(new MoneyDebited(id, amount, Instant.now()));  // Apply + record
    }

    // Event application — pure state mutation, no side effects
    private void apply(DomainEvent event) {
        if (event instanceof AccountOpened e) {
            this.id = e.accountId();
            this.balance = e.initialBalance();
            this.status = AccountStatus.ACTIVE;
        } else if (event instanceof MoneyDebited e) {
            this.balance = this.balance.subtract(e.amount());
        } else if (event instanceof MoneyCredited e) {
            this.balance = this.balance.add(e.amount());
        }
        this.version++;
        uncommittedEvents.add(event);
    }
}
```

---

## 6.3 CQRS — Command Query Responsibility Segregation

```
Traditional MVC: Same model for reads and writes
  Service → reads from DB → writes to same DB

CQRS:
  Commands (writes) → Command Model → Write DB (normalized, consistent)
  Queries (reads) → Query Model → Read DB (denormalized, fast, eventual)

Event flow:
  POST /payments → PaymentService → PaymentCreated event → Kafka
                                                                ↓
  GET /payments → ReadProjection ← updates from event consumer
```

```java
// Command side
@Service
@Transactional
public class PaymentCommandService {

    public PaymentId createPayment(CreatePaymentCommand command) {
        Payment payment = new Payment(command);
        paymentWriteRepo.save(payment);
        eventBus.publish(new PaymentCreatedEvent(payment));
        return payment.getId();
    }
}

// Query side — separate optimized read model
@Service
@Transactional(readOnly = true)
public class PaymentQueryService {

    public PaymentDetailsView getPaymentDetails(UUID paymentId) {
        // Denormalized view — already joined with account, customer info
        return paymentReadRepo.findDetailView(paymentId)
            .orElseThrow(() -> new PaymentNotFoundException(paymentId));
    }

    public Page<PaymentListItem> listPayments(PaymentFilter filter, Pageable pageable) {
        // Optimized for listing — no joins needed
        return paymentReadRepo.findByFilter(filter, pageable);
    }
}

// Event handler that updates read model
@Component
public class PaymentReadModelUpdater {

    @EventListener  // Or @KafkaListener for cross-service
    public void on(PaymentCreatedEvent event) {
        // Build denormalized read model
        PaymentReadModel readModel = buildReadModel(event);
        paymentReadRepo.save(readModel);
    }
}
```

---

## 6.4 Distributed Transactions — Saga Pattern

### The Problem with Distributed Transactions

```
Multi-service operation:
1. Debit account (AccountService DB)
2. Record payment (PaymentService DB)
3. Send notification (NotificationService)

Traditional 2PC (Two-Phase Commit):
- Coordinator locks all resources, then commits
- Blocking, slow, doesn't work across microservices
- Not suitable for modern distributed systems

Solution: Saga Pattern
- Sequence of local transactions
- Each step publishes event triggering next step
- Compensating transactions for rollback
```

### Choreography-Based Saga

```
AccountService                PaymentService            NotificationService
     |                              |                          |
  Debit Account                     |                          |
  → Publish: AccountDebited         |                          |
                      ↓             |                          |
              Listens to AccountDebited                        |
              → Create Payment                                 |
              → Publish: PaymentCreated                        |
                                          ↓                    |
                               Listens to PaymentCreated       |
                               → Send Notification             |
                               → Publish: NotificationSent     |

Rollback (if PaymentService fails):
  → Publish: PaymentFailed
      ↓
  AccountService listens: PaymentFailed
  → Credit Account back (compensating transaction)
```

### Orchestration-Based Saga

```java
@Component
public class PaymentSagaOrchestrator {

    public void executePaymentSaga(PaymentSagaContext context) {
        SagaExecutionCoordinator
            .step("debit-account")
                .execute(() -> accountService.debit(context.getFromAccount(), context.getAmount()))
                .compensate(() -> accountService.credit(context.getFromAccount(), context.getAmount()))
            .step("create-payment-record")
                .execute(() -> paymentService.create(context))
                .compensate(() -> paymentService.cancel(context.getPaymentId()))
            .step("notify-customer")
                .execute(() -> notificationService.notifyPayment(context))
                .compensate(() -> {}) // Notifications: idempotent, ignore failures
            .run()
            .onSuccess(result -> log.info("Payment saga completed: {}", context.getPaymentId()))
            .onFailure((step, error) -> {
                log.error("Payment saga failed at step: {}", step);
                // Compensation is automatic
            });
    }
}
```

---

## 6.5 CAP Theorem — Practical Application

```
CAP Theorem: A distributed system can guarantee at most 2 of 3:
  C = Consistency   (all nodes see same data at same time)
  A = Availability  (every request gets a response)
  P = Partition tolerance (system works despite network splits)

Since P (network partitions) always happen in real distributed systems,
the real choice is: C vs A during a network partition.

CP Systems (consistency over availability):
  → HBase, ZooKeeper, MongoDB (in certain modes)
  → Use: Banking ledgers, inventory counts, leader election
  → During partition: refuse requests rather than risk inconsistency

AP Systems (availability over consistency):
  → Cassandra, DynamoDB, CouchDB
  → Use: Shopping carts, social feeds, cache
  → During partition: serve possibly stale data, reconcile later

Kafka sits in between:
  → Leader election (CP-like) for partition leadership
  → Producer acks control the C/A tradeoff
```

### PACELC — More Practical Model

```
When no partition (E — Else):
  Choose between Latency (L) vs Consistency (C)

PA/EL: DynamoDB, Cassandra — Available during partition, Low latency normally
PC/EC: HBase, ZooKeeper — Consistent during partition, Consistent normally
PC/EL: MongoDB — Consistent during partition, Low latency normally (dirty reads)
```

---

## 6.6 Backpressure

```
Problem: Producer sends events faster than consumer can process
  Kafka producer → 10,000 msg/sec
  DB consumer → 1,000 msg/sec
  → Queue fills up → OOM → crash

Solution strategies:

1. Buffer with bounded queue
   BlockingQueue<Task> queue = new ArrayBlockingQueue<>(1000);
   // Producer blocks when queue full → natural backpressure

2. Rate limiting consumer
   Semaphore semaphore = new Semaphore(maxConcurrent);
   semaphore.acquire();
   processAsync(event).whenComplete((r, e) -> semaphore.release());

3. Reactive backpressure (Project Reactor)
   Flux.fromIterable(items)
       .onBackpressureBuffer(1000)        // Buffer up to 1000
       .onBackpressureDrop(dropped ->     // Drop oldest when full
           log.warn("Dropping event: {}", dropped.getId()))
       .flatMap(item -> process(item), 50) // 50 concurrent max
       .subscribe();

4. Kafka: increase partitions, scale consumers
   KafkaConsumer: max.poll.records = 100  // Process in batches
```

---

## 6.7 Message Ordering Guarantees

```
Challenge: Events for Account A must be processed in order
           (open → deposit → withdrawal must not be reordered)

Kafka Ordering Rules:
- Within partition: Strict ordering guaranteed
- Across partitions: No ordering

Strategy: Use entity ID as Kafka partition key
  kafkaTemplate.send("account.events", account.getId(), event);
  // All events for account "ACC-123" → same partition → ordered

Multi-partition concerns:
  If a consumer group has 3 instances and Account A's events
  land on partition 2, only Consumer Instance 2 processes them.
  No reordering possible.

Ordering violation trap:
  Don't use UUID.randomUUID() as partition key — random distribution
  means related events land on different partitions!
```

---

## Section Summary: Distributed Systems Interview Topics

**Must-master topics for FAANG and banks:**

1. **Kafka architecture** — producers, consumers, partitions, offsets, consumer groups
2. **Delivery guarantees** — at-most-once, at-least-once, exactly-once
3. **DLQ pattern** — what it is, when to use, how to process
4. **Saga pattern** — choreography vs orchestration, compensation transactions
5. **CAP theorem** — with practical database examples
6. **Event sourcing** — pros, cons, when appropriate
7. **CQRS** — command vs query separation, eventual consistency
8. **Partition key strategy** — ordering guarantees, hot partition problems
9. **Consumer lag** — what it means, how to monitor, how to recover
10. **Idempotent consumers** — deduplication strategies

**Commonly asked design question:**  
"Design a payment system that guarantees exactly-once payment processing across microservices"  
Expected answer: Kafka transactions + idempotent consumers + saga pattern + outbox pattern

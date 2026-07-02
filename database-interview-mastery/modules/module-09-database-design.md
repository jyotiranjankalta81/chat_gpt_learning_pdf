# MODULE 9 — Database Design

> Schema-design rounds ask you to design real systems in 30–45 minutes. This module gives you
> the method plus complete reference schemas for the ten designs that actually get asked:
> users, orders, payments, products, inventory, hotel booking, flight booking, social media,
> chat, travel booking.

Chapters:
9.1 The Design Method (how to run the round)
9.2 Users & Identity
9.3 E-Commerce: Products, Inventory, Orders, Payments
9.4 Booking Systems: Hotel, Flight, Travel (the concurrency designs)
9.5 Social Media (feeds, follows, likes)
9.6 Chat & Messaging

---

## Chapter 9.1 — The Design Method

### 1. Why Interviewers Ask This
Schema design reveals more senior signal per minute than any other question: modeling judgment,
integrity instincts, concurrency awareness, and scale honesty — all at once.

### 2. Core Concept — The 7-Step Script
1. **Clarify entities + access patterns first** ("what are the top 5 queries and the write
   rates?") — never start drawing tables silently.
2. **Model the write side in ~3NF**: entities, relationships (1:1, 1:N, M:N via junction),
   surrogate `bigint` PKs, natural keys as unique constraints.
3. **Encode invariants in DDL**: NOT NULL, CHECK, UNIQUE (incl. partial), FK with explicit
   ON DELETE, EXCLUDE for overlaps. Every constraint is a class of bugs deleted.
4. **Snapshot history** where facts must not drift (prices on orders, addresses on shipments).
5. **Design state machines explicitly**: status enums + allowed transitions (+ audit/event
   table for money).
6. **Index for the access patterns** (Module 4.7 method), including pagination keys.
7. **Name the scale plan**: what partitions, what caches, what denormalizes, what shards — and
   what breaks then (Modules 5/7).

Cross-cutting patterns you'll reuse in every design below: **idempotency keys** on any
client-retriable write; **soft delete** (`deleted_at`) where audit matters; **ledger (append-
only) over mutable balance** for money; **counter caches** for hot aggregates; **outbox** for
DB+event atomicity.

### 3–4. Internal Working & Visualization
The artifact interviewers want on the whiteboard:

```
[entities] ──1:N──▶ [child tables]      per table:
   │                                     - PK (bigint identity)
   M:N via junction table                - natural keys → UNIQUE
   │                                     - FKs + ON DELETE policy
[state machines]: status + transitions   - status CHECK / enum
[money]: append-only ledger, never UPDATE amounts
[hot reads]: counter caches / denormalized read models (rebuildable)
```

### 5–12. (Method-level notes)
- **Interview questions**: "Why bigint surrogate PK?", "Where would you denormalize?",
  "How does this schema break at 100x?" — always coming; pre-plan answers per design.
- **Mistakes**: diving into DDL before access patterns; FLOAT for money (integer cents/numeric);
  EAV "flexible" schemas when jsonb suffices; storing mutable snapshots by joining live tables.
- **Best practice**: narrate trade-offs while drawing; you're graded on reasoning, not recall.
- **Follow-ups**: every design below ends with its own scale escalation.

---

## Chapter 9.2 — Users & Identity

### 1. Why Interviewers Ask This
Every system has users; the design has hidden depth: credentials vs profile separation, multiple
auth providers, sessions, soft deletion vs GDPR erasure, email uniqueness semantics.

### 2. Core Concept
Split by lifecycle and sensitivity: `users` (identity core) / `user_auth_providers` (N ways to
log in) / `user_profiles` (mutable, fat) / `sessions` (ephemeral, Redis-able). Never store
plaintext passwords (bcrypt/argon2 hash only); email uniqueness must be case-insensitive and
survive soft deletion.

### 3. SQL — Reference Schema
```sql
CREATE TABLE users (
  id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  public_id     uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,   -- external identifier
  email         citext NOT NULL,
  email_verified_at timestamptz,
  password_hash text,                          -- NULL when social-login only
  status        text NOT NULL DEFAULT 'active'
                CHECK (status IN ('active','suspended','deleted')),
  created_at    timestamptz NOT NULL DEFAULT now(),
  deleted_at    timestamptz
);
-- one LIVE account per email; freed on delete, kept for audit
CREATE UNIQUE INDEX users_email_live ON users (email) WHERE deleted_at IS NULL;

CREATE TABLE user_auth_providers (
  user_id     bigint NOT NULL REFERENCES users(id),
  provider    text  NOT NULL CHECK (provider IN ('google','github','apple')),
  provider_uid text NOT NULL,
  PRIMARY KEY (user_id, provider),
  UNIQUE (provider, provider_uid)              -- an external identity maps to ONE user
);

CREATE TABLE user_profiles (
  user_id     bigint PRIMARY KEY REFERENCES users(id),
  display_name text NOT NULL,
  avatar_url  text,
  bio         text,
  prefs       jsonb NOT NULL DEFAULT '{}'      -- genuinely flexible fragment
);

CREATE TABLE sessions (
  token_hash  bytea PRIMARY KEY,               -- store hash, never the token
  user_id     bigint NOT NULL REFERENCES users(id),
  created_at  timestamptz NOT NULL DEFAULT now(),
  expires_at  timestamptz NOT NULL,
  ip          inet, user_agent text
);
CREATE INDEX ON sessions (user_id);
CREATE INDEX ON sessions (expires_at);          -- reaper
```

### 4. Visualization
```
users 1──1 user_profiles          login flows:
  │ 1──N user_auth_providers      email+pw → users.password_hash
  │ 1──N sessions                 google  → auth_providers(provider,uid) → user
soft delete: deleted_at set, email freed via partial unique, PII scrubbed async (GDPR)
```

### 5–12. Interview Notes
- **Production example**: GDPR erasure = keep the `users` row (FK integrity for orders!) but
  null/scramble PII and set deleted; orders keep pointing at a tombstoned user.
- **Questions**: "same email re-signup after deletion?" (partial unique); "merge two accounts?"
  (auth_providers repoint + data migration job — hard, say it's hard); "sessions in PG or
  Redis?" (Redis for scale/TTL, PG acceptable early; hybrid: refresh tokens in PG, access in
  Redis).
- **Mistakes**: unique on raw `email` (case), profile columns bloating the identity row,
  deleting user rows (orphaned FKs everywhere).
- **Scale**: profiles cacheable; sessions → Redis; users table itself rarely the bottleneck —
  auth QPS is (cache the session check).

---

## Chapter 9.3 — E-Commerce: Products, Inventory, Orders, Payments

### 1. Why Interviewers Ask This
The most-asked design; it packs catalog modeling (variants), concurrency (inventory), state
machines (orders), and financial integrity (payments/ledger) into one prompt.

### 2. Core Concept
- **Products** = product (marketing shell) + **SKU/variant** (the sellable, stockable unit) +
  flexible attributes (jsonb) + categories (M:N or tree).
- **Inventory** belongs to SKU × warehouse; overselling prevented by *atomic guarded
  decrements*, not read-check-write. Reservation pattern for checkout holds.
- **Orders** snapshot everything (name, unit price, tax) at purchase; status is a state
  machine; totals stored (not derived at read time) and verifiable.
- **Payments** are append-only **attempts/transactions**; never UPDATE an amount; refunds are
  new rows; idempotency keys on every external call; a `ledger` if you must track balances.

### 3. SQL — Reference Schema
```sql
CREATE TABLE products (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name text NOT NULL, brand_id bigint REFERENCES brands(id),
  description text, attrs jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','live','retired')),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE skus (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  product_id bigint NOT NULL REFERENCES products(id),
  sku_code text NOT NULL UNIQUE,
  variant jsonb NOT NULL DEFAULT '{}',          -- {"size":"L","color":"red"}
  price_cents int NOT NULL CHECK (price_cents >= 0),
  currency char(3) NOT NULL DEFAULT 'USD'
);
CREATE INDEX ON skus (product_id);

CREATE TABLE inventory (
  sku_id bigint NOT NULL REFERENCES skus(id),
  warehouse_id bigint NOT NULL REFERENCES warehouses(id),
  on_hand  int NOT NULL DEFAULT 0 CHECK (on_hand >= 0),
  reserved int NOT NULL DEFAULT 0 CHECK (reserved >= 0 AND reserved <= on_hand),
  PRIMARY KEY (sku_id, warehouse_id)
);

CREATE TABLE orders (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_number text NOT NULL UNIQUE,            -- human/external id
  user_id bigint NOT NULL REFERENCES users(id),
  status text NOT NULL DEFAULT 'pending' CHECK (status IN
    ('pending','paid','fulfilled','shipped','delivered','cancelled','refunded')),
  subtotal_cents int NOT NULL, tax_cents int NOT NULL, total_cents int NOT NULL,
  shipping_address jsonb NOT NULL,              -- snapshot!
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz
);
CREATE INDEX ON orders (user_id, created_at DESC);
CREATE INDEX ON orders (created_at) WHERE status = 'pending';  -- ops: stuck orders

CREATE TABLE order_items (
  order_id bigint NOT NULL REFERENCES orders(id),
  sku_id bigint NOT NULL REFERENCES skus(id),
  product_name text NOT NULL,                   -- snapshot
  unit_price_cents int NOT NULL,                -- snapshot
  quantity int NOT NULL CHECK (quantity > 0),
  PRIMARY KEY (order_id, sku_id)
);

CREATE TABLE payments (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  order_id bigint NOT NULL REFERENCES orders(id),
  idempotency_key text NOT NULL UNIQUE,
  kind text NOT NULL CHECK (kind IN ('charge','refund')),
  amount_cents int NOT NULL CHECK (amount_cents > 0),
  status text NOT NULL DEFAULT 'pending'
         CHECK (status IN ('pending','succeeded','failed')),
  provider text NOT NULL, provider_ref text,    -- e.g. Stripe charge id
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON payments (order_id);
```

Checkout core (concurrency-safe):
```sql
BEGIN;
-- reserve stock atomically; rowcount 0 = out of stock
UPDATE inventory SET reserved = reserved + :qty
WHERE sku_id = :sku AND warehouse_id = :wh
  AND on_hand - reserved >= :qty;
INSERT INTO orders (...) VALUES (...);
INSERT INTO order_items (...) VALUES (...);
INSERT INTO outbox (topic, payload) VALUES ('order.created', ...);  -- events, atomically
COMMIT;
-- then: charge card OUTSIDE the txn (idempotency_key!), then finalize:
--   success: on_hand -= qty, reserved -= qty, order → 'paid'
--   failure/timeout: reserved -= qty, order → 'cancelled' (reaper for expired holds)
```

### 4. Visualization
```
products 1─N skus 1─N inventory(×warehouse)
users 1─N orders 1─N order_items ─▶ skus (id ref + SNAPSHOT columns)
orders 1─N payments (append-only attempts; refunds = new rows)
checkout: reserve(guarded UPDATE) → charge(external, idempotent) → commit/release
          └────────── reservation expiry reaper for abandoned checkouts ─────────┘
```

### 5–12. Interview Notes
- **Traps they'll pull**: "price changed after purchase — what shows on the old order?"
  (snapshots); "two buyers, one item left" (guarded UPDATE; show the SQL); "payment webhook
  arrives twice" (idempotency key + status transition guards); "totals don't match items"
  (store + verify with a CHECK or reconciliation job).
- **Ledger follow-up** (Stripe-flavored): double-entry — every movement is two rows
  (debit/credit) in an append-only `ledger_entries`; balances = SUM or maintained snapshot with
  reconciliation. Never UPDATE money rows.
- **Mistakes**: float money; deriving order totals by joining live SKU prices; one `inventory`
  count with no reservation concept; deleting order rows ever.
- **Scale plan**: products/skus cached + search in Elastic (CDC); orders partitioned by month
  (old ones cold); inventory hot rows — per-warehouse rows already shard the contention, hot
  SKUs may need queue-serialized decrements; payments append-only = easy to partition.

---

## Chapter 9.4 — Booking Systems: Hotel, Flight, Travel

### 1. Why Interviewers Ask This
Booking = the concurrency masterclass: prevent double-booking under contention, hold-then-
confirm flows, and inventory that is *time-shaped* (nights, seats, legs). Hotel booking is the
single most popular senior schema question.

### 2. Core Concept
Three equivalent strategies for "no double-booking" — know all three:
1. **Exclusion constraint on a range** (Postgres superpower): room × daterange must not
   overlap. Database-enforced, race-proof.
2. **Inventory-count model**: a row per (room_type, date) with `available` counter, decremented
   with a guarded UPDATE — books *types* not specific rooms (how real hotels/airlines sell),
   scales better, allows overbooking policy (`available` can start > physical).
3. **Unit-per-slot rows**: a row per (seat, flight) with a unique claim — flights' seat maps.

Holds: bookings start as `pending` with `expires_at`; payment confirms; reaper releases.
Travel booking (multi-item trip) = saga across hotel+flight+car with compensations — the
distributed-transaction discussion.

### 3. SQL — Reference Schemas
Hotel (both strategies):
```sql
-- Strategy 1: specific-room assignment, overlap-proof
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE room_bookings (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  room_id bigint NOT NULL REFERENCES rooms(id),
  guest_id bigint NOT NULL REFERENCES users(id),
  stay daterange NOT NULL,                          -- [check_in, check_out)
  status text NOT NULL DEFAULT 'pending'
       CHECK (status IN ('pending','confirmed','cancelled')),
  expires_at timestamptz,                            -- pending hold TTL
  EXCLUDE USING gist (room_id WITH =, stay WITH &&) WHERE (status <> 'cancelled')
);
-- concurrent overlapping inserts: exactly one wins (23P01), no app locking needed ✔

-- Strategy 2: sell room-types by night (scales; standard industry model)
CREATE TABLE room_type_inventory (
  hotel_id bigint NOT NULL, room_type_id bigint NOT NULL,
  night date NOT NULL,
  total int NOT NULL, available int NOT NULL CHECK (available >= 0),
  PRIMARY KEY (hotel_id, room_type_id, night)
);
-- book nights [d1, d2): all-or-nothing guarded decrement
UPDATE room_type_inventory
SET available = available - 1
WHERE hotel_id=:h AND room_type_id=:rt AND night >= :d1 AND night < :d2
  AND available > 0;
-- rowcount must equal (d2 - d1) nights; else ROLLBACK (partial nights unavailable)
```

Flight:
```sql
CREATE TABLE flights (
  id bigint PRIMARY KEY, flight_no text NOT NULL,
  departs_at timestamptz NOT NULL, origin char(3) NOT NULL, dest char(3) NOT NULL,
  UNIQUE (flight_no, departs_at)
);
CREATE TABLE flight_seats (
  flight_id bigint NOT NULL REFERENCES flights(id),
  seat_no text NOT NULL,
  booking_id bigint REFERENCES bookings(id),      -- NULL = free
  PRIMARY KEY (flight_id, seat_no)
);
-- claim a seat atomically:
UPDATE flight_seats SET booking_id = :b
WHERE flight_id=:f AND seat_no=:s AND booking_id IS NULL;   -- rowcount 0 = taken

CREATE TABLE bookings (               -- PNR-level record
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  pnr text NOT NULL UNIQUE,
  user_id bigint NOT NULL REFERENCES users(id),
  status text NOT NULL DEFAULT 'pending'
       CHECK (status IN ('pending','ticketed','cancelled')),
  expires_at timestamptz,
  total_cents int NOT NULL
);
CREATE TABLE booking_segments (       -- multi-leg itineraries
  booking_id bigint REFERENCES bookings(id),
  flight_id bigint REFERENCES flights(id),
  fare_class char(1) NOT NULL, price_cents int NOT NULL,   -- snapshot
  PRIMARY KEY (booking_id, flight_id)
);
```

Travel booking (trip saga):
```sql
CREATE TABLE trips (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id bigint NOT NULL,
  status text NOT NULL DEFAULT 'building' CHECK (status IN
    ('building','booking','confirmed','partially_failed','cancelled'))
);
CREATE TABLE trip_items (
  trip_id bigint REFERENCES trips(id),
  kind text NOT NULL CHECK (kind IN ('flight','hotel','car')),
  provider_ref text,                       -- external booking id
  status text NOT NULL DEFAULT 'pending' CHECK (status IN
    ('pending','reserved','confirmed','failed','compensated')),
  payload jsonb NOT NULL,
  PRIMARY KEY (trip_id, kind, provider_ref)
);
-- saga: reserve each item (idempotent) → confirm all → on any failure,
-- compensate (cancel reserved items) and mark partially_failed
```

### 4. Visualization
```
Hotel:  room_type_inventory[night]: |Jul1:3|Jul2:3|Jul3:0|Jul4:2|
        book Jul1-Jul3 → decrement Jul1,Jul2 rows atomically; Jul3 sold out? whole txn rolls back
Hold:   pending(expires 10min) ──pay──▶ confirmed
                         └─expired──▶ reaper releases (available++ / row freed)
Flight seat claim: UPDATE ... WHERE booking_id IS NULL  → exactly one winner per seat
Trip saga: [flight ✔ reserved][hotel ✔][car ✖ failed] → compensate flight+hotel → notify
```

### 5–12. Interview Notes
- **Guaranteed follow-ups**: "two users book the last room simultaneously — walk the exact
  mechanism" (constraint violation or rowcount=0 — no sleep-and-retry hand-waving);
  "user's payment takes 3 minutes — do you hold the room?" (pending + expires_at, reaper —
  never a held DB lock); "search available rooms for a date range" (inventory model:
  `GROUP BY room_type HAVING count(*) FILTER (WHERE available>0) = :nights` over the range —
  writable and indexable); "overbooking?" (inventory model supports it as policy: total >
  physical; exclusion model doesn't).
- **Mistakes**: `SELECT ... FOR UPDATE` on a *search* result set (locks the world); checking
  availability then inserting without a constraint (race); storing check_in/check_out without
  half-open semantics (adjacent bookings "overlap"); forgetting cancelled bookings must not
  block (the WHERE on the exclusion constraint).
- **Scale plan**: inventory model partitions by hotel_id naturally and shards the hot-row
  problem per (type, night); search moves to a read model (cache/Elastic) rebuilt from
  inventory; flights: seat maps per flight are small — the hot spot is fare/inventory buckets,
  same guarded-counter pattern; saga state must be crash-recoverable (the tables above are the
  saga log).

---

## Chapter 9.5 — Social Media (Feeds, Follows, Likes)

### 1. Why Interviewers Ask This
The read-amplification design: tiny writes, enormous fan-out reads, celebrity skew. Tests
denormalization judgment and the push/pull feed decision.

### 2. Core Concept
Write model (normalized, Postgres): users, posts, follows (junction), likes (junction),
comments. Read model (denormalized): **feeds**. The core decision:
- **Fan-out on write (push)**: on post, insert into every follower's feed list (Redis/Cassandra).
  Feed read = one key fetch (fast). Celebrity posts = millions of writes.
- **Fan-out on read (pull)**: feed read = merge recent posts of all followees. Cheap writes,
  expensive reads for users following thousands.
- **Hybrid (the answer)**: push for normal authors; celebrities are pulled at read time and
  merged. Likes/comment *counts* are counter caches (sharded when hot).

### 3. SQL — Reference Schema
```sql
CREATE TABLE posts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  author_id bigint NOT NULL REFERENCES users(id),
  body text NOT NULL,
  media jsonb,
  like_count int NOT NULL DEFAULT 0,          -- counter cache (rebuildable)
  comment_count int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);
CREATE INDEX ON posts (author_id, created_at DESC) WHERE deleted_at IS NULL;

CREATE TABLE follows (
  follower_id bigint NOT NULL REFERENCES users(id),
  followee_id bigint NOT NULL REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (follower_id, followee_id),
  CHECK (follower_id <> followee_id)
);
CREATE INDEX ON follows (followee_id);         -- "who follows X" (fan-out source)

CREATE TABLE likes (
  user_id bigint NOT NULL REFERENCES users(id),
  post_id bigint NOT NULL REFERENCES posts(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, post_id)               -- like-once enforced by PK
);
CREATE INDEX ON likes (post_id);

-- Pull-model feed query (works to ~thousands of followees):
SELECT p.* FROM posts p
JOIN follows f ON f.followee_id = p.author_id
WHERE f.follower_id = :me AND p.deleted_at IS NULL
  AND (p.created_at, p.id) < (:cursor_ts, :cursor_id)
ORDER BY p.created_at DESC, p.id DESC LIMIT 20;
```
Feed read model (push side, conceptually in Redis/Cassandra):
```text
Redis:      LPUSH feed:{follower} post_id      (LTRIM feed:{follower} 0 799)
Cassandra:  feed_by_user ((user_id), created_at DESC, post_id)
read:       feed page = LRANGE / partition scan → hydrate posts by id (batched!)
```

### 4. Visualization
```
post by normal user (2k followers):        post by celebrity (80M followers):
write ─▶ posts ─▶ fan-out worker           write ─▶ posts (marked celebrity)
          └─▶ 2k feed-list inserts ✔                 └─▶ NO fan-out
read: feed:{me} → ids → MGET posts ✔       read: merge(feed:{me}, recent celebrity posts) ✔
like: PK(user,post) dedups; count = sharded counter, reconciled from likes table
```

### 5–12. Interview Notes
- **Follow-ups**: "unfollow — what happens to already-fanned-out posts?" (lazy filter at read,
  or async cleanup); "delete a viral post" (source-of-truth delete + read-time filter + async
  feed scrub + cache invalidation); "like count exact?" (no — counter cache + reconciliation;
  the *likes* table is exact); "feed consistency?" (eventual, seconds — say the product accepts
  it).
- **Mistakes**: COUNT(*) likes at render time; fan-out synchronously in the request; unbounded
  feed lists (trim!); follows table without the reverse index.
- **Scale plan**: posts partitioned by time; follows/likes shard by user; feed lists in
  Redis/Cassandra keyed by user (Module 8.2's exact pattern); counters sharded (Module 5.6);
  the celebrity threshold (~10k–100k followers) is a tunable — quote it.

---

## Chapter 9.6 — Chat & Messaging

### 1. Why Interviewers Ask This
Ordering, delivery states, unread counts, and huge append-only volume — plus the classic
"Postgres first, Cassandra when" migration narrative (Discord).

### 2. Core Concept
Entities: conversations (direct or group), members (junction with per-member state), messages
(append-only, keyed by conversation + time-ordered id). Critical decisions:
- **Message ID = time-ordered** (snowflake/UUIDv7): sort key, pagination cursor, and dedup all
  in one.
- **Per-member state on the junction** (`last_read_message_id`, muted, role) — unread count =
  messages after last_read (bounded query), or maintained counters for O(1).
- **Direct conversations deduped** by a canonical pair key.
- Delivery/read receipts: per-member watermark (scales), not per-message-per-user rows
  (explodes — only for small groups if product demands per-message ticks).

### 3. SQL — Reference Schema
```sql
CREATE TABLE conversations (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  kind text NOT NULL CHECK (kind IN ('direct','group')),
  title text,                                   -- groups only
  -- dedup direct convos: canonical "smaller_id:larger_id"
  direct_key text UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE conversation_members (
  conversation_id bigint NOT NULL REFERENCES conversations(id),
  user_id bigint NOT NULL REFERENCES users(id),
  role text NOT NULL DEFAULT 'member' CHECK (role IN ('member','admin')),
  last_read_message_id bigint NOT NULL DEFAULT 0,   -- read watermark
  muted_until timestamptz,
  PRIMARY KEY (conversation_id, user_id)
);
CREATE INDEX ON conversation_members (user_id);      -- "my conversations"

CREATE TABLE messages (
  id bigint PRIMARY KEY,                        -- snowflake: time-ordered, globally unique
  conversation_id bigint NOT NULL REFERENCES conversations(id),
  sender_id bigint NOT NULL REFERENCES users(id),
  body text,
  attachments jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz                         -- soft delete ("message removed")
);
CREATE INDEX ON messages (conversation_id, id DESC);  -- the one hot index

-- history page (keyset):
SELECT * FROM messages
WHERE conversation_id = :c AND id < :cursor
ORDER BY id DESC LIMIT 50;

-- unread count per conversation (bounded by watermark):
SELECT count(*) FROM messages m
JOIN conversation_members cm
  ON cm.conversation_id = m.conversation_id AND cm.user_id = :me
WHERE m.conversation_id = :c AND m.id > cm.last_read_message_id;

-- conversation list with previews: denormalize last_message onto conversations
-- (updated on send) — avoids N top-1 subqueries on the inbox screen
```

### 4. Visualization
```
conversations 1─N messages (append-only, id = time-ordered)
      │ 1─N conversation_members (watermarks: last_read_message_id)
inbox: my memberships → conversations (denormalized last_message preview) → unread badges
history: (conversation_id, id DESC) keyset pages ── infinite scroll
read:  advance watermark (1 UPDATE) — not N receipt rows
Cassandra migration (Discord path): messages_by_channel ((channel_id, bucket), id DESC)
```

### 5–12. Interview Notes
- **Follow-ups**: "message ordering across devices?" (server-assigned ids are the order;
  client timestamps are display-only); "exactly-once send?" (client-generated message id +
  PK dedup = idempotent retry); "typing indicators/presence?" (Redis TTL keys, never the DB);
  "group of 100k members' unread counts?" (watermarks make it per-member O(1) state + lazy
  count; push badge counts via async).
- **Mistakes**: per-message-per-recipient delivery rows for large groups; OFFSET pagination on
  history; storing presence in Postgres; global autoincrement exposing message volume
  (fine internally, mask externally if it matters).
- **Scale plan**: messages = the biggest table you'll ever own — partition by month early
  (or conversation-bucket), archive cold partitions to object storage; when write volume
  outgrows one primary, this table is the textbook Cassandra/Scylla migration (channel-bucketed
  partitions — Module 8.6); everything else (users, members) stays relational far longer.

---

# Module 9 — Practice Problems

## Easy (5)
1. Add "wishlist" to the e-commerce schema: tables, keys, constraints, and the query "is this
   SKU in my wishlist" — in DDL.
2. Enforce: a user can review a product only once, and only after a delivered order containing
   it. (Unique constraint + the INSERT ... WHERE EXISTS shape.)
3. Why does `order_items` copy `unit_price_cents` when `skus.price_cents` exists? Name the
   principle and one bug the copy prevents.
4. Design the `coupons` + `coupon_redemptions` tables with per-user and global usage limits
   enforced in DDL as far as possible.
5. Write the inbox query: my 20 most recent conversations with unread counts, using the
   watermark design.

## Medium (5)
6. Extend hotel booking with rate plans (refundable/non-refundable, seasonal pricing): where do
   prices live, what gets snapshotted onto the booking, and how does availability interact with
   plan?
7. Add multi-warehouse fulfillment to e-commerce: allocation strategy tables, partial
   shipments, and the state machine from 'paid' to 'delivered' with split packages.
8. Design likes for 1M likes/minute peak: exact likes table + sharded counters + reconciliation
   + read path. Show the DDL and the flush job.
9. Flight search "NYC→LON, any airline, next Friday, 2 seats in economy": what schema/read
   model serves this in <100ms, given the booking tables? (Availability projection per
   (route, date, class) maintained by CDC.)
10. Convert the direct-message model to support "edit history + delete for me / delete for
    everyone": schema changes and the read query.

## Hard (5)
11. Full trip-booking saga: design the saga-state tables, idempotent reserve/confirm/compensate
    steps for flight+hotel+car with per-provider idempotency keys, crash recovery (resume from
    saga log), and the user-visible states. Walk a failure at each step.
12. Your hotel inventory model must now support: overbooking by policy (105%), day-of walk-ins,
    room-type upgrades at check-in, and channel managers (Expedia) with allotments. Extend the
    schema and identify each new race condition and its guard.
13. Design GDPR erasure across the whole e-commerce schema: what's deleted, scrambled, retained
    (legal), the FK strategy for tombstoned users, the async pipeline, and proof-of-erasure
    audit.
14. The messages table hits 10B rows on Postgres. Produce the full migration plan to
    Cassandra: target schema (bucketing math for 99p channel activity), dual-write phase,
    backfill strategy, read-cutover per channel cohort, verification, and rollback. Include
    what you do about the relational features you lose (FKs, transactions on member state).
15. Unify Modules 7+9: shard the social-media write model (users, posts, follows) across 8
    Postgres shards. Choose the shard key, place each table, redesign the follows fan-out
    (cross-shard!), and specify the feed pipeline end-to-end with failure semantics.

---

*Next: [Module 10 — Interview SQL](module-10-interview-sql.md)*

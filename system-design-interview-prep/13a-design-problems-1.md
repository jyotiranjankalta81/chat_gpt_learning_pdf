# Module 13 — Classic System Design Problems (Part 1)

Each design follows the full checklist: functional & non-functional requirements,
capacity estimation, API, data model, high-level design, detailed design (the deep
dive), scaling, failure handling, caching, security, and trade-offs. Closely
related prompts (URL Shortener/TinyURL, WhatsApp/Chat, Uber/Ola, Airbnb/Hotel
Booking) are treated together with their differences called out — exactly how you
should handle them in a real interview.

---

## 13.1 URL Shortener / TinyURL

*(One design — "TinyURL" is the brand name of the same problem.)*

**Functional:** shorten long URL → short code; redirect; optional custom alias,
expiration, click analytics. **Non-functional:** redirect p99 < 50 ms, 99.99%
available (redirects must survive write-path death), read:write ≈ 100:1, codes
non-guessable-ish, links live for years.

**Capacity:** 100M new URLs/month ≈ 40 writes/s (peak ~400); reads 100× ⇒ ~4k/s
(peak 40k). Storage: 100M/mo × 500 B ≈ 50 GB/yr — *tiny*; this problem is about
latency + ID generation, not storage. 7 chars of base62 = 62⁷ ≈ 3.5 × 10¹² — enough
for 1,000+ years.

**API:**

```
POST /api/urls   {long_url, custom_alias?, expires_at?}  → {short_url}
GET  /{code}     → 301/302 redirect
GET  /api/urls/{code}/stats → {clicks, referrers, countries}
```

301 (permanent, browsers cache — fewer hits, no analytics) vs 302 (every click
hits you — analytics possible). Say the trade-off; pick 302 if analytics matter.

**Data model:** `urls(code PK, long_url, owner_id, created_at, expires_at, is_custom)`
— a key-value access pattern ⇒ DynamoDB/Cassandra or sharded MySQL all work;
partition by `code`.

**High-level design:**

```
 write: client → API → ID generator → DB → (warm cache)
 read:  client → CDN/edge? → LB → redirect svc → Redis (hot codes, ~99% hit)
                                        └─ miss → DB → fill cache → 302
 clicks → Kafka → analytics pipeline (never on the redirect critical path)
```

**Deep dive — code generation (the expected one):**

- *Counter + base62*: monotonic counter → base62 encode. Simple, no collisions; but sequential codes are enumerable (privacy) and the counter is a coordination point. Fix coordination with **ranged allocation**: each app instance leases a block (e.g., 1M IDs) from a coordination store (ZooKeeper/DB row with atomic increment); hands out locally, lease a new block when exhausted. Fix enumerability with a bijective scramble of the counter.
- *Random/hash*: generate random 7-char code, INSERT with unique constraint, retry on collision (rare while sparse). Stateless, non-guessable; retries rise as space fills.
- *Pre-generated pool*: offline job fills a table of unused codes; writers pop atomically. Fast writes, extra moving part.

**Scaling:** redirect service is stateless → horizontal; cache absorbs the Zipf
head (hot 10% of codes ≈ 90+% of traffic); DB shards by code when needed; CDN/edge
workers can even serve redirects for the hottest codes. **Failure:** cache down →
DB with concurrency cap (Module 3.7); write path down → *redirects still work*
(separate the planes — the availability win to narrate). **Caching:** cache-aside,
TTL hours–days, negative caching for missing codes (bot/scan protection).
**Security:** rate-limit creation, block-list malicious targets (Safe Browsing
check async), private/expiring links, don't leak sequential IDs. **Trade-offs to
volunteer:** 301 vs 302; counter (coordinated, enumerable) vs random (collision
retries); SQL (simple, familiar) vs KV store (scale, TTL support built-in).

---

## 13.2 Instagram Feed / Facebook News Feed / Twitter(X) Timeline

*(One core design — the feed/fan-out problem — with per-product deltas.)*

**Functional:** post content; follow users; home feed of followees' posts, ranked
(FB/IG) or ~chronological (classic Twitter); like/comment counts; media.
**Non-functional:** feed load p99 < 200 ms, post visible to followers in seconds,
read:write extremely skewed (Twitter-scale: ~300k feed reads/s vs ~6k tweets/s),
eventual consistency fine everywhere except your own actions (read-your-writes).

**Capacity (Twitter-flavored):** 500M tweets/day ≈ 6k/s avg; feed reads ~300k/s;
average 200 followers ⇒ naive fan-out ≈ 1.2M timeline-insertions/s at peak — this
number *is* the design problem. Media via object storage + CDN (Module 6).

**API:**

```
POST /posts {text, media_ids}            GET /feed?cursor=&limit=20
POST /users/{id}/follow                  GET /users/{id}/posts?cursor=
POST /posts/{id}/like
```

Cursor pagination (Module 10.6) — feeds are the canonical case.

**Data model:** `posts(post_id SNOWFLAKE, author_id, text, media, created_at)`
sharded by author (or post_id); `follows(follower_id, followee_id)` sharded by
follower (need "who do I follow" fast) with a reverse index sharded by followee
("who follows me" — needed for fan-out); `timelines` in **Redis: list/zset per
user, capped ~800 entries, storing post IDs only**. Snowflake IDs give time-ordered
IDs without coordination.

**High-level design & the core trade-off:**

```
 FAN-OUT ON WRITE (push)                 FAN-OUT ON READ (pull)
 post → Kafka → fanout workers           feed request → get followees →
   → LPUSH post_id into each               fetch each followee's recent posts
     follower's Redis timeline             → merge by time → rank → return
 read = one Redis fetch (fast!)          write = one insert (cheap!)
 write cost = O(followers)  ☠ celebrities  read cost = O(followees) per load ☠
```

**The hybrid (the expected answer):** push for normal users; **don't fan out
celebrities** (>~100k followers). Feed read = fetch your precomputed timeline +
fetch recent posts from the handful of celebrities you follow + merge at read
time. Post-visibility SLO met via Kafka-buffered async fan-out (a post reaching
5M timelines takes seconds–minutes for the tail — acceptable; your own post appears
instantly to *you* via read-your-writes injection).

**Detailed design — read path:** timeline (IDs) from Redis → hydrate posts
(multi-get from post cache → DB on miss) → hydrate authors (cache) → counts
(approximate counters, Module 3.6) → **ranking** (FB/IG delta: score candidates
with an ML model — candidate generation: your timeline + collaborative/interest
sources; feature fetch; scoring service; re-rank with diversity/integrity rules;
this is a service pipeline between "fetch" and "return"). Likes: sharded counters,
write-back batched to DB, reconciled offline.

**Scaling:** everything shards cleanly (timelines by user, posts by ID, fan-out
workers by partition); Redis timeline tier is the big memory bill (~800 IDs × 8 B ×
500M users ≈ 3 TB — fine across a cluster; evict cold users' timelines and rebuild
on demand via pull — regenerable state!). **Failure:** fan-out lag ⇒ stale feeds
(monitor consumer lag, alert on p99 delivery time); Redis loss ⇒ rebuild timelines
lazily via pull path (design explicitly for regeneration); dedupe fan-out with
idempotent LPUSH-if-absent (at-least-once Kafka). **Caching:** post cache, user
cache, timeline *is* a cache, CDN for media, L1 for celebrity posts (hot keys,
Module 3.6). **Security:** private accounts filtered at fan-out *and* read
(defense in depth), block/mute filters at read, rate-limit posting/likes (bots).
**Trade-offs:** push vs pull vs hybrid (recite the celebrity math); chronological
(simple, transparent) vs ranked (engagement, ML infra cost); capped timelines
(bounded memory) vs deep history (pull fallback beyond the cap).

---

## 13.3 WhatsApp / Chat Application

*(One design: 1:1 + group messaging; WhatsApp adds E2E encryption + mobile focus.)*

**Functional:** 1:1 and group messages; delivery + read receipts; online/last-seen
presence; media; message history sync across devices; typing indicators.
**Non-functional:** delivery p99 < 500 ms online; **no message loss ever**
(durability trumps latency); ordering per conversation; billions of devices, mostly
idle connections; E2E encryption (WhatsApp).

**Capacity (WhatsApp-scale):** 2B users, ~100B messages/day ≈ 1.2M msg/s average
(peak 3–5×). Concurrent connections ~500M ⇒ at 1M conns/server (Erlang-style tuned
hosts) ≈ 500–1000 connection servers. Message storage: 100B × ~100 B ≈ 10 TB/day
raw (WhatsApp historically deletes after delivery; a Slack-like keeps forever —
say which model you're building).

**API / protocol:** WebSocket (or raw TCP) with a binary frame protocol:
`send(conv_id, client_msg_id, payload)`, server ACK, `deliver`, `receipt(delivered/read)`,
`presence`, `typing`; HTTPS for login, media upload (presigned, Module 6.1),
history sync.

**Data model:** `messages(conv_id, msg_id, sender, payload, ts)` — sharded/keyed
by **conversation** (Cassandra/HBase-style wide rows: partition = conv_id (+ time
bucket for huge groups), clustering by msg_id ⇒ "recent messages of a chat" is one
partition read); `conversations(conv_id, members…)`; `inbox/undelivered(user_id →
pending msg refs)` per recipient; `sessions(user_id → connection server)` in
Redis. Per-conversation **sequence numbers** give ordering + gap detection for
client sync.

**High-level design:**

```
 sender ═ws═► conn-srv A ──► chat service: assign seq, PERSIST message,
                             write per-recipient inbox (durable)   ── ACK sender
                │ lookup recipient session (Redis registry)
                ├─ online:  route (pub/sub or direct) → conn-srv C ═ws═► recipient
                │           recipient ACK → delete from inbox → receipt to sender
                └─ offline: stays in inbox → push notification (APNs/FCM)
                            → delivered on reconnect (client sends last_seq, server
                              replays the gap)
```

**Deep dive — the guarantees:** durability before ACK (message persisted + inbox
written, *then* sender sees ✓); delivery = at-least-once + client dedupe by
`client_msg_id` (idempotency, Module 7.5); ordering per conversation via the
sequence assigned by the conversation's owning partition (single-writer per conv —
no distributed coordination needed). **Groups:** sender uploads once; server fans
out to member inboxes (small groups) — for huge groups/channels, pull-on-open
instead (same push/pull trade-off as feeds). **Presence:** heartbeats → presence
service with debounced pub/sub to subscribed friends (don't broadcast every blip);
last-seen written lazily. **E2E encryption (WhatsApp/Signal, one paragraph):**
Signal protocol — X3DH key agreement + double ratchet per conversation; server
stores/forwards ciphertext only; group = sender keys; consequence: server-side
search/moderation impossible, multi-device needs per-device sessions.

**Scaling:** connection tier stateless-ish (sacrificial sockets, Module 1.8/2.6) —
scale by count; chat/storage shards by conv_id; hot conversations (huge groups) get
bucketed partitions. **Failure:** conn server dies → clients reconnect with
backoff+jitter → resume via last_seq replay (zero loss because inbox is durable);
datacenter loss → regional inboxes replicated (user-home-region model).
**Caching:** session registry, recent messages per hot conv, profile/keys cache.
**Security:** E2E, TLS to edge, contact discovery privacy, spam/abuse rate limits,
registration lock. **Trade-offs:** delete-after-delivery (WhatsApp: tiny storage,
privacy) vs permanent history + search (Slack: storage + index cost);
push-to-inbox vs pull-for-channels; presence freshness vs fan-out cost.

---

## 13.4 YouTube / Netflix (Video Platforms)

*(Shared core: upload→transcode→CDN→adaptive streaming. Delta: YouTube = UGC at
massive upload scale + virality; Netflix = small curated catalog, predictable,
own CDN.)*

**Functional:** upload (YT), transcode to multi-quality, stream with adaptive
bitrate, search/browse, recommendations, resume position, view counts (YT).
**Non-functional:** startup < 1–2 s, no rebuffering (the #1 UX metric), 99.99%
playback availability, durable originals; YT: 500+ hours uploaded/minute; Netflix:
~15–30% of national downstream internet at peak.

**Capacity sketch (YT):** 500 h/min uploaded = 30k min of video/min; each minute ≈
several hundred MB across renditions ⇒ exabyte-class storage, growing PB/day ⇒
erasure coding + tiering are mandatory (Module 6). Streaming egress dominated by
CDN (~99% offload target).

**API:** `POST /videos` → presigned multipart upload → `{video_id}`;
`GET /videos/{id}/manifest.m3u8` (HLS/DASH manifest); segment GETs go to CDN;
`POST /videos/{id}/progress` (resume); search/browse APIs.

**Data model:** `videos(id, owner, title, status: uploading→processing→live,
renditions[])` in a DB; originals + segments in object storage; view counts in
sharded counters; watch history in a wide-column store (Netflix: Cassandra —
write-heavy, per-user partition).

**High-level design (the pipeline):**

```
 upload (presigned multipart) → object storage → event → TRANSCODING PIPELINE:
   split video into chunks → parallel transcode (ladder: 240p…4K × codecs H.264/VP9/AV1)
   → package into 2–10 s segments (HLS/DASH) + manifests → object storage → CDN prewarm
 playback: client → manifest → player picks bitrate per measured bandwidth,
   fetches segments from CDN edge; ABR adapts up/down per segment  ◄── the key idea
```

**Deep dive — adaptive bitrate:** video = independently decodable segments in
multiple qualities; the *client* measures throughput/buffer and chooses the next
segment's rendition — no server session state, plain CDN-cacheable HTTP GETs (this
answer explains both scale and smooth playback). **Transcoding at scale:**
chunk-level parallelism (a 2 h movie transcodes in minutes across 1,000 workers),
priority queues (new-upload vs backfill), idempotent chunk jobs + reassembly
(Module 10.7). **View counting (YT):** raw events → Kafka → streaming aggregation →
approximate live counter + exact batch reconciliation (never count on the read
path). **Netflix deltas:** small catalog ⇒ **pre-position** the entire catalog on
**Open Connect** appliances inside ISPs during off-peak (predictive caching from
viewing forecasts — cache hit ~100%, backbone traffic ~zero at peak); per-title
encoding optimization; recommendation-heavy homepage (precomputed per user,
nightly + online adjustments). **YouTube deltas:** virality ⇒ hot-video handling
(CDN request collapsing, multi-tier cache), upload spam/copyright (ContentID
fingerprint matching in the pipeline), long-tail catalog ⇒ real cache-miss path
matters.

**Scaling:** every stage horizontal (uploaders, transcoders, CDN, metadata shards);
metadata reads cached heavily. **Failure:** transcode job death → idempotent retry
per chunk; CDN region loss → reroute to next PoP (client retry logic + multi-CDN
for Netflix); origin protected by shield tier. **Caching:** CDN is 99% of the
design; manifest cache; metadata cache; home-page precomputation. **Security:**
DRM (Widevine/FairPlay) for premium, signed segment URLs (leech protection),
upload scanning. **Trade-offs:** own CDN (Netflix: control, cost at scale) vs
commercial multi-CDN (YT is Google's edge anyway); more renditions (quality per
user) vs storage/compute; live streaming adds latency-vs-buffer trade (shorter
segments, LL-HLS).

---

## 13.5 Google Drive / Dropbox (File Sync & Storage)

**Functional:** upload/download; **sync across devices** (the hard part); share
with permissions; version history; offline edits reconciled. **Non-functional:**
never lose a byte (11-nines durability), sync latency seconds, efficient for
large files and small edits (don't re-upload 2 GB for a 1 KB change), millions of
concurrent syncing clients.

**Capacity:** 500M users × 10 GB avg = 5 EB logical; dedup + compression cut real
bytes substantially (Dropbox reported large dedup wins). Metadata: billions of
files × ~KB = tens of TB — a serious sharded DB of its own.

**API:** presigned block upload/download; `GET /delta?cursor=` (change feed per
account — the sync primitive); `POST /files/{id}/share`; long-poll/WebSocket
notification channel ("something changed, call /delta").

**Data model — the block design (the expected deep dive):**

```
 files:    (file_id, ns_id, path, current_version)
 versions: (file_id, version, block_list[hash1, hash2, ...], size, mtime)
 blocks:   content-addressed: hash(SHA-256) → object storage key   (4 MB chunks)
 sharing:  namespaces (ns) with ACLs; shared folder = mount of another ns
```

- **Chunking**: files split into ~4 MB blocks, addressed by content hash.
- **Delta sync**: client hashes local blocks; uploads *only new hashes*; a small edit = 1 block, not the file. (Bonus point: content-defined chunking keeps edits from shifting all subsequent block boundaries.)
- **Dedup**: identical blocks (across users!) stored once — hash-addressed storage gives it for free (mention the privacy caveat of cross-user dedup).
- **Version history**: a version = a block list; old versions share unchanged blocks (cheap snapshots, Merkle-flavored).

**Sync flow:**

```
 device edits file → chunk + hash → ask server which blocks are new → upload those
 → commit new version (block list) to metadata svc (transactional, detects conflict:
   base_version mismatch) → change feed entry → other devices notified (long-poll)
   → they pull /delta → download missing blocks → reassemble
 conflict (offline concurrent edits): DON'T merge silently — keep both:
   "report (Bob's conflicted copy)"  ◄── classic, honest answer
```

**Scaling:** metadata DB sharded by namespace/user; block storage is object
storage (or Dropbox's Magic Pocket); notification tier = millions of idle
long-poll/WS connections (Module 2.6). **Failure:** upload resume via
already-have-hashes (idempotent by content address!); metadata/block consistency
via commit-after-blocks + orphan GC (Module 6.4); client crash mid-sync → journal
+ re-diff. **Caching:** hot metadata, block presence checks via Bloom-filter-ish
caches, CDN for popular shared files. **Security:** encryption at rest per-block,
TLS, ACL checks on every namespace op (IDOR!), share links with scoped tokens,
virus scan pipeline on shared content. **Trade-offs:** block size (small = better
dedup/delta, more metadata; big = fewer round trips); server-side merge (Google
Docs — needs OT/CRDT, format-aware) vs conflicted copies (Dropbox — format-
agnostic, honest); strong metadata consistency + eventual block propagation.

---

## 13.6 Uber / Ola (Ride-Hailing)

*(Same design; Ola = same problem in denser, cash-heavier markets.)*

**Functional:** rider requests ride; match nearby driver; live location tracking;
ETA + dynamic pricing; trip lifecycle (request→match→pickup→ride→payment→rating).
**Non-functional:** match < 5–10 s; location update pipeline handles millions of
drivers @ 1 update/4 s; high availability during a trip (an ongoing trip must
survive service failures); payment consistency.

**Capacity:** 5M active drivers × 0.25 updates/s ≈ 1.25M location writes/s —
**the location firehose is the design center**; matching QPS is small by
comparison (peaks ~thousands/s). Location data is ephemeral (latest matters) ⇒
in-memory store, trip history to durable storage async.

**API:** driver: `PUT /location {lat,lng,heading}` (over an open WS/gRPC stream);
rider: `POST /rides {pickup, dest}` → offer states; `GET /rides/{id}` (live
tracking via WS push); pricing internal.

**Deep dive — geo-indexing (the expected one):** you can't query "drivers within
2 km" from a lat/lng table at this rate. Discretize the world into cells —
**H3 (Uber's hexagons)**, S2 (Google), or geohash:

```
 location update: cell = h3(lat,lng, res≈9)
   Redis: SADD cell:{cell} driver_id  (+ per-driver latest point, TTL ~30 s
          — silence self-cleans)      sharded by cell across the cluster
 match query: cells = k-ring(pickup_cell, 1..2) → union members → filter
   (available, right vehicle) → rank by ROAD-network ETA (routing svc), not
   straight-line → offer to best driver (accept window) → cascade on decline
```

Hexagons: uniform neighbor distances (better ring queries than squares); resolution
trades precision vs cell population; **hot cells** (airport, stadium) = classic hot
key → finer resolution locally + replicated reads (Module 3.6).

**Trip lifecycle & consistency:** trip = a **state machine**
(REQUESTED→MATCHED→ARRIVING→IN_RIDE→COMPLETED→PAID) persisted in a durable DB
(sharded by trip/city); transitions idempotent + versioned; matching offers use
short locks/leases on the driver (one offer at a time) — but final assignment is a
transactional state transition (double-assignment must be impossible: unique
active-trip-per-driver constraint as the arbiter, Module 11.7's "DB as final
lock"). Payment via saga: auth at match/start, capture at completion (Module 7.6).
**Pricing/ETA:** surge = streaming supply/demand aggregation per cell (Flink over
the location/request firehose); ETA = routing service over road graph with live
traffic (precomputed contraction hierarchies + live edge weights).

**Scaling:** shard *everything by city/region* (natural isolation — an outage in
one city stays there; also data residency); location tier by cell; matching
stateless per region. **Failure:** location store loss = self-healing within
seconds (next updates repopulate — say this!); ongoing trips unaffected (trip
state durable elsewhere); driver app offline mid-trip → GPS buffered locally,
reconciled. **Caching:** driver profiles, rider payment profiles, route/ETA
memoization per cell-pair. **Security:** driver identity verification, location
data privacy (retention limits, access audit), fraud (GPS spoof detection —
plausibility checks), payment tokenization. **Trade-offs:** hex grid resolution;
push offers to one driver (fairness, latency) vs broadcast (race, but faster in
sparse areas — Ola/other markets differ); exact nearest (expensive) vs
cell-approximate + ETA re-rank (standard).

---

## 13.7 Airbnb / Hotel Booking / Flight Booking

*(One family: search → availability → reserve without double-booking → pay.
Deltas: Airbnb = 1 unit per listing + two-sided marketplace; hotels = N identical
rooms per type; flights = seats + fare classes + GDS legacy + extreme search
fan-out.)*

**Functional:** search (location/dates/filters); listing/room/flight details;
availability calendar; **book without double-booking**; pay; cancel; host/inventory
management. **Non-functional:** search p99 < 500 ms over millions of listings;
**zero double-bookings** (strong consistency exactly here); booking flow 99.99%;
search freshness eventual (seconds) is fine.

**Capacity (Airbnb-ish):** 10M listings; searches 10k/s peak; bookings ~100/s —
*search is the scale problem, booking is the consistency problem.* Say that
sentence; it structures everything.

**API:**

```
GET  /search?loc&checkin&checkout&guests&filters&cursor
GET  /listings/{id}?checkin&checkout        (availability + priced total)
POST /bookings {listing_id, dates, idempotency_key} → PENDING_PAYMENT
POST /bookings/{id}/confirm (payment)       DELETE /bookings/{id} (cancel policy)
```

**Data model:** `listings` (attributes, geo) in Postgres, sharded by region as
needed; **availability calendar**: `calendar(listing_id, date, status, price)` —
one row per listing-day (2-year window × 10M listings = 7B rows; fine sharded by
listing_id); `bookings(id, listing_id, dates, status state machine, idem_key
UNIQUE)`; search index in Elasticsearch fed by CDC (CQRS, Module 4.7); hotels:
`room_inventory(hotel_id, room_type, date, total, reserved)` — *counts*, not
units; flights: `seat_inventory(flight, fare_class, remaining)` + seat map.

**High-level design:**

```
 search:  query → ES (geo + dates + filters, pre-joined availability summary)
          → candidates → pricing svc (dynamic) → rank → results  [eventually consistent]
 booking: → booking svc → TRANSACTIONAL availability check+reserve (source of truth,
          strongly consistent) → payment saga → confirm          [strictly consistent]
```

**Deep dive — preventing double booking (the guaranteed question):** the calendar
DB is the arbiter, not the search index and not a cache:

```sql
BEGIN;
SELECT * FROM calendar WHERE listing_id=? AND date BETWEEN ?  FOR UPDATE;  -- lock range
-- all nights 'available'? else abort with friendly error
UPDATE calendar SET status='held', hold_expires=now()+'10 min' ...;
INSERT INTO bookings(..., status='PENDING_PAYMENT');
COMMIT;
```

Two-phase UX: **hold with TTL** during payment (expired holds swept back to
available), confirm on payment success (saga: capture → CONFIRMED; failure →
release, Module 7.6). Idempotency key on booking creation (double-click, retry
safety). Hotels: `UPDATE room_inventory SET reserved=reserved+1 WHERE ... AND
reserved < total` — atomic conditional decrement of a *count* (no per-unit rows;
overselling policies are deliberate business config, not bugs). Flights: same
conditional decrement per fare class; legacy twist — availability often lives in
external **GDS** systems ⇒ cached availability + revalidate-at-booking + graceful
"fare changed" UX (a great real-world wrinkle to mention).

**Scaling:** search via ES shards + caching of hot geo-date queries; calendar
sharded by listing (all rows of one booking in one shard ⇒ local transaction —
shard key chosen *for* the consistency need, Module 4.3). **Failure:** payment
timeout → hold expiry sweeps (janitor); ES lag → final availability check at
booking catches phantoms ("sorry, just taken" — quantify: lag seconds × booking
rate = rare); region loss → bookings DB is the recovery priority (RPO≈0 semi-sync).
**Caching:** search results (short TTL), listing details, pricing memoization —
**never cache the final availability check**. **Security:** payment via
PSP/tokenization, IDOR on bookings, scraping rate limits, fraud screening on
bookings. **Trade-offs:** pessimistic lock/hold (simple, brief lock) vs optimistic
(version check at confirm — better under low contention); denormalized
availability-in-ES (fast search, staleness) vs query-time join (fresh, slow);
hold TTL length (conversion vs inventory lockup).

---

## 13.8 Payment Gateway / Payment System

**Functional:** merchant charges a card (auth/capture/refund/void); support cards
+ wallets + bank rails; webhooks to merchants; ledger + reconciliation with
processors. **Non-functional:** **never double-charge, never lose money** (exact
consistency); p99 auth < 2 s (human at checkout); 99.99%+; PCI-DSS compliance;
full auditability.

**Capacity:** Stripe-order-of-magnitude: ~10k payments/s peak. Small QPS, extreme
correctness — the *inverse* of feed systems; say so.

**API (Stripe-shaped):**

```
POST /v1/payment_intents {amount, currency, ...}   Idempotency-Key: <uuid>  ← REQUIRED
POST /v1/payment_intents/{id}/confirm    POST /refunds {payment_intent, amount}
GET  /v1/payment_intents/{id}            webhooks: payment_succeeded/failed (signed)
```

**Data model — the two pillars:**

1. **Payment state machine**: `payments(id, merchant, amount, status:
   CREATED→AUTHORIZED→CAPTURED→SETTLED / FAILED / REFUNDED, psp_ref, idem_key
   UNIQUE)` — every transition idempotent, versioned, audit-logged.
2. **Double-entry ledger**: `ledger_entries(txn_id, account, debit, credit, ...)`
   — **append-only, immutable**; every money movement = balanced entries (merchant
   receivable ↔ processor clearing ↔ fees). Balances = derived (materialized,
   reconciled). Corrections = new reversing entries, never UPDATEs. This is what
   "bank-grade" means in interviews.

**High-level design:**

```
 merchant → API (idempotency layer, Module 7.5: key+response stored in-txn)
   → payment svc (state machine, ledger) → card vault (tokenized PAN, PCI island)
   → PSP/network adapter (Visa/MC/banks) — timeout+breaker+ONE retry w/ same
     idempotency ref → async webhooks (outbox→Kafka→signed delivery w/ retries)
   → reconciliation: daily processor settlement files diffed against ledger
```

**Deep dive — the double-charge question:** client retry → same Idempotency-Key →
stored response returned (no re-execution). Crash *after* PSP call, *before*
recording? On recovery the state machine is "in flight" → **query the PSP by our
reference** (or void-and-retry) — never blind-retry a charge; unknown-outcome
states get a reconciliation queue. External calls carry *our* idempotent reference
so the PSP dedupes too. Auth-then-capture is itself the saga's reversible pivot
(Module 7.6). **Reconciliation** (the senior differentiator): settlement files vs
ledger, automated matching, exception queue for humans — every real payment
company runs this; mentioning it signals authenticity.

**Scaling:** shard by merchant (hot merchants isolated); reads from replicas;
ledger appends partition cleanly. QPS is modest — scale is in event/webhook fan-out
and reporting (CQRS read models). **Failure:** PSP down → queue+retry auths?
No — fail fast to user, offer retry (money UX beats silent queues); PSP *slow* →
timeout+breaker+fallback processor (multi-PSP routing — also a cost optimization);
datacenter loss → RPO 0 (semi-sync/quorum) because "lost payment record with
captured money" is the nightmare scenario. **Caching:** none on the money path
(only merchant config/keys). **Security:** PCI scope minimized via
tokenization/vault (Module 9.6), mTLS internal, HSM for keys, signed webhooks,
velocity/fraud scoring inline (ML risk score gate before auth), full audit trail.
**Trade-offs:** sync auth + async everything-else; exactly-once *effect* via
idempotency (over impossible exactly-once delivery); double-entry overhead vs
auditability (no real trade — always double-entry, say why).

---

## 13.9 E-commerce Platform & Inventory Management

*(Amazon-style storefront; inventory is its own deep dive and the requested
"Inventory Management" system.)*

**Functional:** browse/search catalog; product pages; cart; checkout (order,
payment, inventory); order tracking; reviews. Inventory: track stock per SKU per
warehouse; reserve at checkout; replenish; oversell policy. **Non-functional:**
catalog reads massive (100k+ QPS peak) and cacheable; **inventory decrement
strongly consistent**; order flow 99.99%; flash-sale spikes 100×; search freshness
seconds.

**Capacity:** 50M products; 100k QPS browse peak; 1k orders/s peak (flash sale:
one SKU, 10k attempts/s — the hot-row problem). Read:write ≈ 1000:1 on catalog.

**API:** `GET /products/{id}`, `GET /search?q&filters`, `POST /cart/items`,
`POST /checkout {cart_id, idempotency_key}`, `GET /orders/{id}`; internal:
`POST /inventory/reserve {order_id, sku, qty, warehouse?}`.

**Data model:** catalog in Postgres + ES (CDC) + heavy caching; `cart` in Redis
(TTL, session-ish) backed to DB for logged-in persistence; `orders(id, status
state machine, items snapshot price/title — Module 4.5)`;
`inventory(sku, warehouse, on_hand, reserved)` — available = on_hand − reserved;
`reservations(order_id, sku, qty, expires_at, status)`.

**High-level design:**

```
 browse: CDN → catalog svc → Redis (L1+L2, Module 3) → DB      [eventual, cached]
 search: ES read model (CDC-fed)                                [eventual]
 checkout: order svc → SAGA: reserve inventory → charge payment → confirm order
           → outbox events → fulfillment / email / analytics    [strictly consistent core]
```

**Deep dive — inventory correctness + the flash sale:**

```sql
-- reservation (atomic conditional update; the arbiter):
UPDATE inventory SET reserved = reserved + :q
 WHERE sku=:s AND warehouse=:w AND on_hand - reserved >= :q;   -- 0 rows = out of stock
```

Reserve with TTL at checkout-start (cart hoarding prevention), convert to
deduction on payment success, sweep expired reservations (janitor) — the same
hold pattern as bookings. **Flash sale hot row:** 10k TPS on one SKU row melts row
locks ⇒ (a) **queue the attempts** (Kafka per-SKU partition = single-writer
serialization, natural fairness, absorbs the spike — users get position/async
confirm), or (b) shard the counter into N sub-buckets summed at read (Module 3.6)
with rebalancing, or (c) pre-allocate stock tokens to app servers. State (a) as
default — it converts a consistency problem into an ordering problem you already
solved. Overselling: policy toggle (backorder allowed?) not an accident;
warehouse-level allocation at fulfillment re-optimizes later. **Multi-warehouse:**
reserve against aggregate or region-preferred warehouse; reconcile with WMS
(physical counts drift — cycle-count adjustments are normal; another authenticity
point).

**Scaling:** catalog/search/cart all shard trivially; orders shard by order_id/
customer; inventory shards by SKU (hot SKUs get the queue treatment). **Failure:**
payment fails → saga compensation releases reservation; ES lag → "in stock" badge
stale but checkout re-verifies (same phantom pattern as bookings); cache stampede
on product drop → single-flight + prewarm (Module 3.5). **Caching:** product pages
(CDN + Redis, invalidated via CDC), search results short-TTL, cart in Redis,
**never** the reservation check. **Security:** idempotent checkout, payment
tokenization, bot defense on drops (queue + rate limit + CAPTCHA), price-integrity
(server-side price, never trust client), IDOR on orders. **Trade-offs:** reserve
at add-to-cart (better UX, inventory lockup) vs at checkout (standard); sync
inventory check on product page (fresh, load) vs cached-with-recheck (standard);
monolith checkout (simpler txn) vs saga (scale/team autonomy).

---

*(Part 2 continues with: Chat/Notification/Autocomplete/Crawler/Distributed
Cache/Rate Limiter/API Gateway/Logging/Analytics — plus the Netflix/Google Drive
deltas already covered above where shared.)*

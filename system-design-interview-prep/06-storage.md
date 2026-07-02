# Module 6 — Storage

Every design with files, media, backups, or big data needs a storage tier, and
interviewers expect you to pick the right *class* of storage (object vs block vs
file) with numbers: durability, latency, cost per GB, and access patterns.

---

## 6.1 Object Storage (S3, GCS, Azure Blob)

### Why Interviewers Ask This

"Where do the images/videos/backups go?" — the answer is object storage in ~100% of
modern designs, and the follow-ups (consistency, multipart upload, presigned URLs,
tiering) test real experience.

### Core Concept

A flat namespace of **immutable objects** (bytes + metadata) addressed by key over
an **HTTP API** (GET/PUT/DELETE) — no directories (prefixes only simulate them), no
in-place edits (replace whole objects; versioning keeps history), no POSIX.
Effectively infinite capacity, pay per GB + per request.

### Internal Working

- **Durability (11 nines)** via **erasure coding**: an object is split into k data + m parity shards spread across disks/AZs (e.g., 6+3 survives any 3 losses at 1.5× overhead vs 3× for replication). Background scrubbing verifies checksums and re-shards.
- Metadata service maps key → shard locations (itself a massive distributed DB — S3's metadata layer is one of the largest database systems on earth).
- **Consistency**: S3 is strongly consistent since 2020 (read-after-write for all ops) — stop citing the old eventual-consistency caveat.
- **Multipart upload**: big files uploaded as parallel parts (5 MB–5 GB each), then committed — resumable, parallel, the standard for anything > ~100 MB.
- **Presigned URLs**: time-limited signed URLs so clients upload/download *directly* to object storage, bypassing your servers — the pattern for every upload flow in interviews (your API issues the URL, the bytes never touch your fleet).
- **Storage classes / lifecycle**: hot (Standard) → infrequent (IA) → archive (Glacier: minutes–hours retrieval) with lifecycle rules auto-transitioning by age; cost drops ~10–20× hot→archive.
- **Event notifications**: object-created events → SQS/Lambda (triggers thumbnailing, virus scan, indexing pipelines).

```
 client ──(1) POST /upload-url──► API (auth, validate) ──► returns presigned URL
 client ──(2) PUT parts directly─────────────────────────► S3 (multipart)
 S3 ──(3) ObjectCreated event──► queue ──► workers (thumbnail, transcode, scan)
 CDN ◄── serves the public reads (origin = bucket)
```

### Real Production Example

Netflix stores masters + encodes in S3, distributes via Open Connect. Dropbox
famously *left* S3 for its own exabyte-scale "Magic Pocket" (custom erasure-coded
storage) when scale economics justified building — the canonical build-vs-buy story.
Every photo app (Instagram, Airbnb listings) = object storage + CDN + presigned
uploads.

### Trade-offs / Common Mistakes

- Not a filesystem: no rename (copy+delete), no append, latency in tens of ms, LIST is expensive — don't design chatty small-file access patterns on it.
- Mistake: proxying file bytes through your API servers (bandwidth + memory burn) instead of presigned direct transfer.
- Mistake: millions of tiny objects (per-request overhead dominates — batch/pack them); hot-prefix throttling under extreme request rates (spread key prefixes).
- Storing DB-like mutable state in objects (race conditions; use a database).

### Interview Questions

1. Design the upload path for 10 GB video files from mobile clients. (presigned multipart, resume, event-driven processing)
2. How does erasure coding get 11 nines cheaper than 3× replication?
3. Photos older than 1 year are viewed 100× less — cut the storage bill. (lifecycle tiering + CDN for the hot set)

---

## 6.2 Block Storage (EBS, Persistent Disk, SAN)

### Core Concept & Internals

Raw **fixed-size blocks** presented as a virtual disk to ONE server (attach →
format with a filesystem → mount). This is what your **databases** run on:
lowest latency (sub-ms), high IOPS (provisioned: e.g., EBS io2 up to 256k IOPS),
random read/write in place. Cloud block stores replicate blocks within an AZ and
support **snapshots** (incremental, stored in object storage) for backup/cloning.

Trade-offs: expensive per GB vs object storage, capacity bounded, single-attach
(mostly), AZ-bound (snapshot/restore to move) — and network-attached block storage
adds a subtle failure mode: the disk can "hang" when the storage network degrades
(EBS incidents), which looks like a frozen database.

**Interview line**: *databases and boot volumes → block; shared media/backups →
object; shared POSIX across many hosts → file.*

### Interview Questions

1. Why does Postgres run on block storage, not S3? (random in-place I/O, fsync latency, POSIX)
2. What are snapshots and how do they enable fast DB clones for staging?

---

## 6.3 File Storage (NFS, EFS, Filestore)

### Core Concept & Internals

A **shared POSIX filesystem over the network**: hierarchy, permissions, appends,
partial writes, many concurrent clients (NFS/SMB protocols; managed: EFS —
elastic, multi-AZ, pay-per-use). The fit: legacy apps expecting a filesystem,
shared content (CMS/WordPress uploads), ML training data mounted across a GPU
fleet, home directories.

Costs: network round trip per metadata op (small-file workloads crawl), locking
semantics across clients are subtle, throughput below local NVMe. Interview
posture: file storage is the *compatibility* choice; for new designs prefer object
storage unless you specifically need POSIX-shared semantics.

---

## 6.4 "Blob Storage" and Handling Large Binary Data in Databases

"Blob storage" in practice = object storage (Azure literally names it Blob
Storage). The recurring interview point: **don't store big binaries in the
database**. The pattern is always:

```
 DB row:    { id, owner, size, content_type, checksum, s3_key, status }
 Object:    s3://bucket/ab/cd/abcd1234...   (bytes)
 Why: DB stays small/fast (backups, replication, cache), storage is cheap,
 CDN can serve bytes, and the DB transactionally owns METADATA + lifecycle.
```

Keep the two consistent: write metadata row (status=pending) → upload → mark
committed; a janitor reconciles orphans (objects without rows, rows without
objects). Small exception: tiny blobs (< a few KB, e.g., avatars) sometimes inline
fine — know the threshold argument, not a dogma.

---

## 6.5 Distributed File Systems (GFS/HDFS lineage, Colossus, Ceph)

### Why Interviewers Ask This

"How would you store petabytes with commodity machines" is the design behind GFS —
and its ideas (chunking, metadata/data separation, replication pipelines) power
everything from HDFS to your object store, so it doubles as an internals question.

### Core Concept & Internal Working (GFS/HDFS model)

- Files split into large **chunks/blocks** (64–256 MB — large to amortize metadata and favor streaming reads).
- A **metadata service** (GFS master / HDFS NameNode) holds the namespace + chunk→server mapping *in memory*; **data servers** (chunkservers/DataNodes) store chunks on local disks, checksummed.
- **Data path bypasses the master**: client asks master "where is chunk 7?" then streams directly from/to chunkservers — the master is a control plane, never a data bottleneck.
- **Replication** (3×, rack-aware) or erasure coding; heartbeats detect dead servers; master re-replicates lost chunks automatically.
- Designed assumptions: huge sequential reads/appends, failure is constant, throughput >> latency. The NameNode SPOF/memory ceiling drove HDFS federation + HA standbys, and Google's successor **Colossus** distributed the metadata itself (metadata stored in Bigtable — which runs on Colossus; bootstrap via a small Paxos core).
- **Ceph**: no central mapping at all — placement computed by the **CRUSH** hash algorithm (any client can compute where data lives), giving object/block/file interfaces on one substrate.

```
            ┌── metadata (namespace, chunk map, leases) ──┐
 client ───►│ MASTER / NameNode │  control plane only
            └───────┬───────────┘
     "chunk 7 @ CS2,CS5,CS9"
 client ◄══ data streams directly ══► [CS2] [CS5] [CS9] ... commodity chunkservers
                                      3× rack-aware replicas, checksums, heartbeats
```

### Real Production Example

GFS → MapReduce → the entire big-data era; HDFS under Hadoop/Spark at Yahoo, Meta,
LinkedIn (though cloud object storage has largely replaced new HDFS deployments);
Colossus under nearly all Google storage (Bigtable, Spanner, YouTube); Ceph under
many private clouds.

### Interview Questions

1. Why 64 MB+ chunks? (metadata volume, seek amortization, streaming)
2. Why does the data path bypass the master, and what still limits the master? (namespace size in RAM, ops/sec — hence federation/Colossus)
3. Replication vs erasure coding trade-off here? (3× fast recovery/reads, 1.5× EC cheaper but reconstruction costs CPU/IO)

---

## 6.6 Storage Trade-offs (the decision table)

```
               latency      throughput   shared?      mutability     cost/GB   use for
 local NVMe    ~100 µs      GB/s         no           full           low*      caches, temp, LSM engines
 block (EBS)   <1 ms        provisioned  1 host       full           $$$       databases, boot volumes
 file (EFS)    ~ms          good         many hosts   full POSIX     $$$$      legacy/shared POSIX, ML data
 object (S3)   10–100 ms    huge (∥)     everyone     replace-only   $         media, backups, data lake
 archive       min–hours    batch        everyone     replace-only   ¢         compliance, cold backups
 *local NVMe is ephemeral on cloud instances — data dies with the host
```

Cross-cutting decision drivers to narrate in interviews:

- **Access pattern first**: random small writes → block; streaming large reads → object; shared POSIX → file.
- **Durability model**: replication (fast, 3× cost) vs erasure coding (1.5×, CPU/rebuild cost) vs snapshot+backup (point-in-time, not HA).
- **Cost architecture**: hot/warm/cold tiering with lifecycle automation is expected in any large-media design; egress fees often dominate — put a CDN in front.
- **Consistency**: object stores give per-object atomicity only — no cross-object transactions; databases own coordination.

### Mock scenario answers you should be able to produce instantly

- Video platform: object (masters + renditions) + CDN + archive tier for cold originals; metadata in DB.
- OLTP database: block storage with provisioned IOPS + snapshots + WAL archiving to object storage.
- ML training corpus: object as source of truth, file/parallel FS or local NVMe cache at the GPUs.
- Log/analytics lake: object storage + columnar files (Parquet) + lifecycle to archive.

---

## Module 6 Cheat Sheet

```
OBJECT   HTTP objects, immutable, flat keys. 11-nines via erasure coding + scrubbing.
         S3 now strongly consistent. Multipart uploads; PRESIGNED URLs (never proxy
         bytes); lifecycle tiering hot→IA→archive; events → processing pipelines.
BLOCK    raw disk for ONE host; sub-ms, provisioned IOPS; databases live here.
         Snapshots (incremental, to object storage). AZ-bound; net-attached can hang.
FILE     shared POSIX over network (NFS/EFS). Compatibility + shared-mount niches.
         Metadata round trips kill small-file workloads.
BLOB+DB  bytes in object storage, metadata row in DB (key, checksum, status);
         reconcile orphans. Never blob columns for media.
DFS      GFS/HDFS: big chunks, in-RAM metadata master (control plane only),
         direct client↔chunkserver data path, 3× rack-aware replicas, heartbeat
         re-replication. Colossus: distributed metadata. Ceph: CRUSH computed placement.
TRADE    latency: NVMe≪block≪file≪object≪archive. cost: reverse. random-write →
         block; streaming/shared/scale → object; POSIX-shared → file. CDN for egress.
```

## Top Interview Questions (Module 6)

1. Upload pipeline for 10 GB videos (presigned multipart + events). 2. Erasure
coding vs replication math. 3. Why DBs need block not object storage. 4. GFS
architecture and why data bypasses the master. 5. Storage-bill reduction via
lifecycle tiering. 6. Blob-in-DB vs object storage + metadata. 7. What breaks with
millions of tiny objects. 8. Snapshot-based backup/clone strategy. 9. Dropbox's
build-vs-buy S3 story. 10. Pick storage for four given workloads (table above).

## Common Mistakes Recap

Proxying file bytes through app servers • blobs in the database • treating S3 as a
filesystem (renames, appends, chatty small I/O) • ignoring lifecycle/tiering in
cost questions • citing S3 eventual consistency (outdated) • no orphan
reconciliation between DB metadata and objects • forgetting egress/CDN in media
designs.

## Mock Interview Exercise

*"Design storage for a Google Photos clone: 500M users, 1B photo uploads/day (avg
3 MB), originals kept forever, thumbnails served hot, p99 view < 200 ms
worldwide."* Expected: presigned multipart uploads → object storage (originals,
EC-coded, lifecycle: 30d hot → IA → archive) + thumbnail derivation pipeline via
events → hot thumbnail tier + CDN; metadata (album/photo rows, checksums, s3 keys)
in sharded DB; dedupe by content hash; capacity math: ~3 PB/day ingest → tiering is
the whole cost story; failure: orphan janitor, checksum scrubbing, multi-region
replication for DR.

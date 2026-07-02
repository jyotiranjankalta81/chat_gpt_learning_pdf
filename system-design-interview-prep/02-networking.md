# Module 2 — Networking

Interview-relevant networking only: the protocols and middleboxes that appear on
every system design whiteboard, with enough internals to survive a deep dive.

---

## 2.1 TCP, UDP, and QUIC

### Why Interviewers Ask This

Transport choice determines latency behavior, connection cost, and what your load
balancers and proxies must do. It comes up directly ("why QUIC?") and indirectly
("why is your p99 bad on mobile?").

### Core Concept

- **TCP**: connection-oriented, reliable, ordered byte stream. Handshake, retransmission, flow control, congestion control. The default for everything.
- **UDP**: connectionless datagrams. No delivery/order guarantees, minimal overhead. Used where the application supplies its own semantics: DNS, video/game real-time traffic, QUIC.
- **QUIC**: a reliable, multiplexed, encrypted transport built *on UDP* in user space. Fixes TCP's head-of-line blocking and slow handshakes; the transport under HTTP/3.

### Internal Working

**TCP connection setup:**

```
Client                    Server
  │ ── SYN (seq=x) ──────► │
  │ ◄─ SYN-ACK (y, x+1) ── │      1 RTT before data
  │ ── ACK (y+1) + data ─► │
```

Then TLS 1.3 adds 1 more RTT (TLS 1.2 added 2). So a fresh HTTPS-over-TCP request
costs 2–3 RTTs before the first byte. On a 100 ms RTT mobile link, that's 200–300 ms
of pure setup — this is why connection reuse and QUIC matter.

Reliability: sequence numbers + cumulative/selective ACKs + retransmission timers.
**Flow control**: receiver advertises a window. **Congestion control**: sender probes
network capacity — slow start (exponential growth of cwnd), congestion avoidance
(linear), loss → back off. Modern algorithms: CUBIC (loss-based, default), BBR
(model-based, Google — keeps queues short, better on lossy/long-fat links).

**TCP head-of-line (HOL) blocking**: one lost packet stalls delivery of *all*
subsequent bytes in the stream, even if they belong to logically independent
requests. This is the flaw HTTP/2 multiplexing inherits and QUIC fixes.

**QUIC**: streams are independent (loss in stream A doesn't stall stream B), TLS 1.3
is fused into the handshake (1 RTT, or **0-RTT** for resumed sessions), and
connections are identified by a connection ID, not the 4-tuple — so a phone hopping
from Wi-Fi to LTE keeps its connection alive (**connection migration**).

### Visual Architecture

```
 HTTPS over TCP+TLS1.3:            HTTP/3 over QUIC:
 ── SYN ─────────►                 ── QUIC Initial (+TLS CH) ─►
 ◄─ SYN-ACK ─────                  ◄─ handshake + TLS done ────
 ── ACK ─────────►                 ── encrypted request ──────►   1 RTT
 ── TLS ClientHello ─►             (0-RTT possible on resume)
 ◄─ TLS ServerHello ──
 ── request ─────►    2 RTT
```

### Real Production Example

Google serves most Chrome/YouTube traffic over QUIC; Meta and Cloudflare report
double-digit p95 latency wins on mobile from HTTP/3, mostly from handshake savings
and loss isolation. Uber uses QUIC in its mobile apps for exactly the
lossy-network/connection-migration reasons.

### Advantages / Trade-offs

- TCP: universal, kernel-optimized, middlebox-friendly. But HOL blocking, slow setup, connection breaks on IP change.
- UDP: minimal latency, multicast-capable. But you own reliability/congestion if you need them.
- QUIC: fast setup, no transport HOL blocking, migration, always encrypted. But higher CPU (user-space, per-packet crypto), some networks throttle/block UDP (need TCP fallback), harder to inspect/debug on the wire.

### Common Mistakes

- "UDP is unreliable so it's bad" — real-time media *prefers* dropping a late packet over retransmitting it.
- Thinking QUIC is just "HTTP over UDP" without naming the actual wins (handshake RTTs, stream independence, migration).
- Ignoring 0-RTT replay risk: 0-RTT data can be replayed by an attacker, so it must carry only idempotent requests.

### Scaling / Failure / Monitoring

- Long-lived TCP at scale: tune keepalives, beware NAT idle timeouts (~5 min) killing "idle" connections; LBs must handle millions of concurrent connections (epoll, SO_REUSEPORT).
- Monitor: retransmission rate, RTT distributions, connection setup failures, cwnd behavior for bulk transfer paths. `ss -ti`, packet captures, eBPF tooling.
- Failure: SYN floods (mitigate with SYN cookies), ephemeral port exhaustion on high-connection-rate proxies (fix with keepalive/pooling), bufferbloat inflating latency.

### Interview Questions

1. Walk through what happens on the wire for a first-ever HTTPS request. How many RTTs, and how do you cut them?
2. Why does packet loss hurt HTTP/2 more than HTTP/3?
3. When would you build on UDP directly?

### Follow-ups

- "Why can QUIC survive a client IP change but TCP can't?" (connection ID vs 4-tuple)
- "CUBIC vs BBR — when does it matter?" (long-fat/lossy links; video delivery)

### Best Practices

- Reuse connections aggressively (keepalive, pooling); handshakes are the tax.
- Enable HTTP/3 with TCP fallback at the edge; keep 0-RTT for idempotent GETs only.

### Hands-on Exercise

Your mobile p95 API latency is 900 ms while Wi-Fi p95 is 250 ms. RTT on mobile is
120 ms. Itemize where the time likely goes and what protocol changes recover it.

---

## 2.2 HTTP/1.1 → HTTP/2 → HTTP/3, and HTTPS

### Why Interviewers Ask This

Every external API in your design speaks HTTP. Version differences explain real
performance behavior (multiplexing, HOL blocking) and real operational choices
(gRPC needs HTTP/2; browsers cap HTTP/1.1 connections).

### Core Concept & Internal Working

**HTTP/1.1** (text): one request at a time per connection (pipelining exists but is
dead due to HOL + broken proxies). Browsers open ~6 parallel connections per host as
a workaround; the era of domain sharding, spriting, and bundling was all HTTP/1.1
mitigation.

**HTTP/2** (binary, 2015): a single TCP connection carries many concurrent **streams**
(multiplexing). Frames (HEADERS, DATA) are interleaved. **HPACK** header compression
(huge win — cookies/headers repeat on every request). Stream prioritization. Server
push (deprecated in practice). Remaining flaw: all streams share one TCP stream, so
one lost TCP packet stalls *every* stream (transport-level HOL).

**HTTP/3** (2022): same HTTP semantics mapped onto QUIC streams — loss on one stream
doesn't stall others; QPACK replaces HPACK (designed for out-of-order delivery);
handshake savings from QUIC.

**HTTPS** = HTTP over TLS. TLS 1.3 handshake: client sends supported ciphers + key
share; server replies with its cert + key share; both derive session keys (1 RTT).
Certificates chain to a trusted CA; SNI tells the server which cert to present when
many domains share an IP. Session resumption / 0-RTT skip round trips on
reconnection. Everything is encrypted: confidentiality + integrity + server
authentication.

### Visual Architecture

```
 HTTP/1.1: conn1: [req1───resp1][req2───resp2]      serialized per connection
           conn2: [req3───resp3]                     (browser opens ~6)

 HTTP/2:   one TCP conn: [h1][d3][h2][d1][d2][d3]    interleaved frames, streams 1..N
           ✗ lost TCP packet → ALL streams stall

 HTTP/3:   one QUIC conn: stream1 ▓▓▓  stream2 ▓▓▓   independent recovery per stream
           ✓ lost packet stalls only its own stream
```

### Real Production Example

Cloudflare/Fastly/Akamai edges negotiate h3 with browsers and often speak HTTP/2 or
1.1 to origins. gRPC (Google, Netflix, Uber internal RPC) mandates HTTP/2 for
multiplexed streaming. Meta measured meaningful engagement wins moving mobile
traffic to HTTP/3.

### Common Mistakes

- "HTTP/2 solves head-of-line blocking" — it solves *application-layer* HOL, and moves it to the transport layer. Naming this distinction is a strong senior signal.
- Recommending domain sharding on HTTP/2 (it's an anti-pattern there — kills one-connection benefits).
- Forgetting that a single HTTP/2 connection between two proxies can be a throughput bottleneck (per-connection flow control windows) — internal L7 proxies often open multiple.

### Monitoring & Failure

- Track protocol mix, handshake failures, TLS version/cipher distribution, cert expiry (a classic self-inflicted outage — automate renewal, alert 30/14/7 days out).
- HTTP/2 stream resets and GOAWAYs signal server overload or LB connection recycling.

### Interview Questions

1. Why did HTTP/2 need to be binary and framed?
2. Your site is slow for users with 2% packet loss — compare behavior on h1/h2/h3.
3. What problems does TLS 1.3 solve over 1.2? (1 RTT, forward secrecy by default, dead ciphers removed)

### Best Practices

- Terminate TLS at the edge/LB; use modern certs with automated rotation (ACME).
- h3 at the edge, h2 for internal gRPC, keep connections warm.

### Hands-on Exercise

A dashboard page fires 40 XHRs to one API host. Explain concretely what changes in
connection count, header bytes, and stall behavior as you move h1.1 → h2 → h3.

---

## 2.3 DNS

### Why Interviewers Ask This

DNS is the first hop of *every* request, a global eventually-consistent database
everyone already runs, and the crudest-but-most-universal traffic steering and
failover tool.

### Core Concept & Internal Working

Hierarchical, cached name resolution:

```
Browser cache → OS cache → Recursive resolver (ISP/8.8.8.8/1.1.1.1)
    │ (on miss)
    ▼
Root servers (.)  ──►  TLD servers (.com)  ──►  Authoritative NS (example.com)
                                                   │
                                          A/AAAA 93.184.216.34  (TTL 300)
```

Record types you must know: **A/AAAA** (IP), **CNAME** (alias), **NS**, **MX**,
**TXT** (verification, SPF), **SRV**, **ALIAS/ANAME** (apex CNAME workaround).
**TTL** controls cache duration = your failover speed vs query volume trade-off.

DNS-based traffic management (Route 53, NS1): weighted routing (canary),
latency-based routing (nearest region), geo routing (data residency), health-checked
failover records. **Anycast** (same IP announced from many locations via BGP) is how
root servers and CDNs make DNS itself fast and DDoS-resistant.

### Real Production Example

The 2016 Dyn DDoS took down Twitter/GitHub/Spotify — not their servers, their DNS
provider. Lesson repeated in interviews: DNS is a dependency with its own
availability, use multiple providers for critical domains. Netflix and AWS use
Route 53 health checks + low TTLs for region failover.

### Common Mistakes

- Believing TTL=60 guarantees 60-second failover — resolvers and OSes disrespect TTLs; some clients (JVMs with default settings!) cache forever. Plan failover assuming a long tail of stale clients.
- Using DNS as a load balancer and expecting even distribution — resolver caching skews it badly.
- Forgetting negative caching (NXDOMAIN cached) — a typo'd record hurts for a while.

### Monitoring, Failure, Scaling

- Monitor resolution latency and failure rate from multiple vantage points; alert on serving NXDOMAIN/SERVFAIL spikes.
- Failures: expired domains, DNSSEC misconfiguration, provider outage, cache poisoning (mitigated by DNSSEC, 0x20 randomization).

### Interview Questions

1. Trace a cold `api.example.com` resolution end to end.
2. Design DNS-based multi-region failover — what limits how fast it works?
3. Why anycast for DNS?

### Best Practices

- TTL 30–300 s for records you may need to move; longer for stable ones.
- Dual DNS providers for tier-0 domains; automate record changes; never hand-edit.

### Hands-on Exercise

Design DNS for a service in 3 regions with latency routing and automatic failout of
an unhealthy region, and state the worst-case user impact window during a region
failure.

---

## 2.4 CDN

### Why Interviewers Ask This

Any read-heavy or global design should put a CDN in front. Interviewers probe: what
do you cache, how do you invalidate, and what happens on the miss path.

### Core Concept & Internal Working

A CDN is a globally distributed cache + smart network edge. Users are routed to the
nearest **PoP** (via anycast or DNS). Edge cache hit → served in ~10–30 ms. Miss →
fetch from a **shield/parent** tier (regional cache) → origin.

```
user ──► edge PoP (300+ worldwide) ──miss──► shield PoP ──miss──► origin
              │ cache-control, TTL,               │  collapses many edge
              ▼ stale-while-revalidate            ▼  misses into 1 origin fetch
           HIT ~90–99% for static           origin sees ~1% of traffic
```

Key mechanics: cache keys (URL + selected headers — keep it minimal or hit rate
dies), `Cache-Control`/`s-maxage`, invalidation (purge APIs are seconds-fast but
global purges are expensive; prefer **versioned URLs**: `app.v42.js` — immutable,
cache forever), **request collapsing** (one origin fetch for N concurrent misses —
stampede protection), **stale-while-revalidate** and **serve-stale-on-error**
(origin down ≠ site down). Modern CDNs also run edge compute (Cloudflare Workers,
Lambda@Edge) and terminate TLS/h3 near the user. Dynamic (uncacheable) traffic
still benefits: TLS terminated at the edge + warm, optimized edge→origin
connections cut 1–2 RTTs.

### Real Production Example

Netflix built its own CDN (**Open Connect**): appliances installed inside ISPs,
pre-loaded with the catalog during off-peak hours — video never crosses the public
internet backbone at peak. This is the canonical "we outgrew commercial CDNs"
story. Meanwhile, image-heavy products (Instagram, Airbnb) serve virtually all
media via CDN with versioned URLs and long TTLs.

### Common Mistakes

- "CDN is only for static files" — API GETs with short TTLs and edge logic are routinely cached.
- Purge-based invalidation as the primary strategy instead of versioned/immutable URLs.
- Caching personalized responses (cookie in the cache key explosion, or worse, leaking user A's data to user B — a real class of incident).

### Monitoring, Failure, Scaling

- Watch cache hit ratio (per content class), origin offload %, origin error rate, PoP-level latency.
- Failure: cache poisoning via unkeyed headers; a global CDN config push taking sites down (Fastly 2021, Cloudflare incidents — even CDNs need canaried config).

### Interview Questions

1. How do you invalidate CDN content the instant a product price changes? (short TTL or purge for price API; versioned assets elsewhere; or don't cache price — cache the shell)
2. What's request collapsing and why does it matter for a viral video?
3. Design the miss path so origin survives a global cache flush.

### Best Practices

- Immutable, versioned asset URLs + `Cache-Control: max-age=31536000, immutable`.
- Shield tier on; serve-stale-on-error on; keep cache keys minimal and explicit.

### Hands-on Exercise

A news site gets 2M RPS at breaking-news peak; article pages change occasionally,
the homepage every 30 s. Design TTLs, invalidation, and the origin protection story.

---

## 2.5 Load Balancer, Reverse Proxy, API Gateway (and NAT)

### Why Interviewers Ask This

These three boxes appear in every diagram and candidates routinely blur them. Being
precise about L4 vs L7, and about what belongs in a gateway vs a service, is an
easy senior signal.

### Core Concept

- **Load balancer**: distributes traffic across replicas. **L4** (transport: forwards TCP/UDP by IP:port, blazing fast, no content awareness — AWS NLB, IPVS, Maglev) vs **L7** (application: parses HTTP, routes by path/host/header, retries, TLS termination — Envoy, NGINX, ALB, HAProxy).
- **Reverse proxy**: a server-side intermediary that terminates client connections and forwards to backends — TLS termination, caching, compression, buffering slow clients. An L7 LB *is* a reverse proxy with balancing.
- **API gateway**: a reverse proxy specialized for API management — authentication/JWT validation, rate limiting, quotas, routing to microservices, request transformation, canary splitting, analytics (Kong, Apigee, AWS API Gateway, Zuul, Envoy-based gateways).
- **NAT**: rewrites private IPs to public at the network boundary. Interview relevance: NAT gateways are how private subnets reach the internet (egress), they keep connection state (idle timeouts kill long-lived connections), and they're why peer-to-peer/WebRTC needs STUN/TURN hole-punching.

### Internal Working

Balancing algorithms: round robin, weighted RR, **least connections** (best general
default for uneven request costs), **consistent hashing** (cache affinity, sticky
WebSockets), **power of two choices** (pick 2 random, take less loaded — near-optimal
with O(1) state, used in Envoy/HAProxy). Health checks: active (probe /healthz) +
passive (eject on error rate — outlier detection). High availability of the LB
itself: pairs with VRRP/keepalived, or L4 via ECMP/anycast + consistent hashing
(Google Maglev, Meta Katran — connection-stable despite router hashing).

```
                internet
                   │
              ┌────▼─────┐   L4: IP:port, millions of conns, no HTTP parsing
              │  L4 LB   │   (NLB / Maglev / Katran)
              └────┬─────┘
              ┌────▼─────┐   L7: TLS, routing, retries, rate limit, authn
              │ L7 GW/LB │   (Envoy / NGINX / API Gateway)
              └─┬───┬───┬┘
         /users │   │   │ /orders
            ┌───▼┐ ┌▼──┐ ┌▼───┐
            │svc1│ │svc│ │svc3│    least-conn / P2C across replicas
            └────┘ └───┘ └────┘
```

### Real Production Example

Netflix Zuul (now Envoy-based gateways elsewhere) fronts all API traffic: auth,
routing, canary, region failover, and — crucially — load shedding by priority during
incidents. Google's Maglev L4 balancer uses consistent hashing so any Maglev can
handle any packet, making the LB tier itself horizontally scalable and hitless
under LB failure.

### Common Mistakes

- Putting business logic in the gateway (it becomes a shared monolith with a platform team bottleneck) — keep it to cross-cutting concerns.
- Ignoring the LB as SPOF ("draw one box" — say how the LB tier itself is redundant).
- Retrying non-idempotent requests at the proxy (duplicate payments!) — retries only on idempotent methods or with idempotency keys.
- Sticky sessions as a crutch for stateful apps instead of externalizing state.

### Monitoring, Failure, Scaling

- Golden signals at the LB: RPS, error rate by upstream, latency percentiles, active connections, healthy-host count. The LB is the best vantage point in the system.
- Failure: health-check flapping (add hysteresis), slow drains during deploys, connection pile-ups when upstreams slow down (cap queue + shed early).

### Interview Questions

1. L4 vs L7 — when is each the right choice? (L4: raw TCP/UDP, extreme scale, WebSocket passthrough; L7: routing, retries, TLS, canary)
2. How do you make the load balancer tier itself highly available?
3. What belongs in an API gateway vs in each service?

### Best Practices

- Two tiers: L4 at the edge for scale/DDoS, L7 behind it for smarts.
- Least-connections or P2C over round robin; outlier ejection on; drain before deploy.
- Idempotency-aware retries with budgets (e.g., ≤ 1 retry, only 5xx/connect-fail, exponential backoff + jitter).

### Hands-on Exercise

Design the traffic path for a 500k-RPS public API across 3 regions: DNS policy, L4
edge, L7 gateway features (auth, rate limit, canary), and what fails over at each
layer.

---

## 2.6 WebSocket

### Why Interviewers Ask This

Any real-time design (chat, presence, live scores, collaborative editing, trading)
needs a server-push story, and WebSocket is the default answer — with a stateful
connection tier whose scaling story interviewers love to probe.

### Core Concept & Internal Working

WebSocket = a persistent, full-duplex, message-framed channel over a single TCP
connection, established by an HTTP/1.1 **Upgrade** handshake:

```
GET /chat HTTP/1.1
Upgrade: websocket          ──►   HTTP/1.1 101 Switching Protocols
Connection: Upgrade                Sec-WebSocket-Accept: <hash>
Sec-WebSocket-Key: <nonce>        ...then raw framed messages both ways, forever
```

After 101, it's no longer HTTP — proxies/LBs must support upgrade passthrough and
long-lived idle connections (tune idle timeouts; NAT/LB defaults of 60 s will
sever "quiet" sockets — send ping/pong heartbeats ~every 30 s).

Alternatives to know and compare: **SSE** (server→client only, plain HTTP, auto-
reconnect built in — great for feeds/notifications, simpler than WS), **long
polling** (fallback, high overhead), **gRPC streaming** (service-to-service),
**WebTransport/HTTP3** (emerging).

Scaling model (the part interviews grade): the connection tier is stateful.
- Capacity: a tuned server holds 100k–1M+ mostly-idle connections (memory-bound: ~
  tens of KB per conn).
- Routing: a **registry** (Redis) maps userId → server, or you use consistent
  hashing at the LB; cross-server delivery goes through a **pub/sub backplane**
  (Redis pub/sub, Kafka, or a mesh of server-to-server streams).
- Deploys/failover: drain connections gracefully; clients reconnect with backoff +
  jitter (else you thundering-herd yourself) and resume via cursor/sequence number
  against the durable message store.

```
 userA ═ws═► conn-srv-3 ─┐        ┌─► conn-srv-9 ═ws═► userB
                          ▼        │
                    pub/sub bus ───┘     registry: userB → srv-9 (Redis)
                          │
                          ▼
                    message store (durable, source of truth)
```

### Real Production Example

Slack's real-time messaging runs on a WebSocket edge fleet with regional presence
and a pub/sub fabric; Discord holds millions of concurrent connections per cluster
on an Elixir/Rust gateway tier, with client resume protocols (session + sequence
numbers) so a gateway restart doesn't lose messages — messages are durable in the
store, sockets are sacrificial.

### Common Mistakes

- Treating the socket as the source of truth: delivery must be backed by a durable store + resume cursor, or restarts lose messages.
- Forgetting heartbeats and LB idle-timeout tuning (mystery disconnects every 60 s).
- No reconnect jitter → a deploy causes a reconnect storm that DDoSes your own auth service.
- Choosing WS when SSE suffices (one-directional feed) — extra ops complexity for nothing.

### Monitoring & Failure

- Metrics: concurrent connections per server, connect/disconnect rates, heartbeat failures, message delivery latency, backlog per client.
- Failure: one server death drops 100k+ connections at once — the reconnect surge is the real event to engineer for (jitter, token bucket at LB, warm capacity).

### Interview Questions

1. WebSocket vs SSE vs long polling — pick per use case.
2. How does a message reach a user connected to a different server?
3. Deploy the connection fleet with zero message loss — walk me through it.

### Best Practices

- Heartbeats + jittered reconnect + resume cursors; durable store as truth.
- Isolate the connection tier from business logic (dumb pipes, smart services).

### Hands-on Exercise

Size and design the WebSocket tier for 5M concurrent users, average 1 msg/s per
1,000 users, with < 1 s delivery p99 and zero loss across deploys.

---

## 2.7 gRPC

### Why Interviewers Ask This

It's the default for internal service-to-service RPC at scale, and comparing REST vs
gRPC — with actual reasons — is a standard question.

### Core Concept & Internal Working

gRPC = RPC framework over **HTTP/2** using **Protocol Buffers** as the IDL and wire
format.

- **Contract-first**: `.proto` files define services/messages; codegen produces typed clients/servers in every language — the contract *is* the documentation.
- **Protobuf encoding**: binary tag-length-value; field numbers (not names) on the wire → compact (often 3–10× smaller than JSON) and fast to parse; unknown fields are ignored → forward/backward compatibility rules (never reuse/renumber fields, only add).
- **Four call types**: unary, server-streaming, client-streaming, bidirectional streaming (multiplexed as HTTP/2 streams on one connection).
- Built-ins interviewers expect you to name: **deadlines propagated across the call chain** (each hop knows remaining budget — the killer feature vs ad-hoc REST timeouts), cancellation propagation, per-call metadata (auth), client-side load balancing (pick-first/round-robin/lookaside), interceptors (auth, retries, telemetry), and status codes designed for retry semantics (UNAVAILABLE retryable, INVALID_ARGUMENT not).

```
 .proto ──codegen──► client stub (Go)          server (Java)
 order = svc.GetOrder(id, deadline=80ms)  ═══HTTP/2═══►  handler
        ◄── binary protobuf frames, one TCP conn, N concurrent streams ──
```

Limitations to volunteer: browsers can't speak native gRPC (need gRPC-Web or a
REST/JSON transcoding gateway); binary payloads aren't grep-able (need reflection/
tooling); L7 infrastructure must be HTTP/2-aware, and long-lived HTTP/2 connections
need **client-side or lookaside LB** (a naive L4 LB pins all requests of a client to
one backend — the classic "gRPC doesn't balance" incident).

### Real Production Example

Google internally (Stubby → gRPC) runs ~10^10 RPCs/sec on this model. Netflix,
Uber, Square, and Dropbox use gRPC for inter-service traffic; Uber pairs it with a
service mesh so Envoy sidecars handle the HTTP/2-aware balancing. Public APIs
usually stay REST/JSON (browser + ecosystem reach) — "gRPC inside, REST outside" is
the standard answer.

### Common Mistakes

- "gRPC is faster because binary" — the deeper wins are multiplexing, deadline propagation, streaming, and typed contracts.
- Breaking proto compatibility (renumbering fields, changing types).
- Load balancing gRPC with a connection-level L4 LB and wondering why one pod is hot.
- No deadlines: a missing deadline turns one slow service into fleet-wide thread exhaustion.

### Monitoring & Failure

- Per-method RPS, latency, and status-code metrics come nearly free via interceptors; deadline-exceeded and UNAVAILABLE rates are your early-warning signals.
- Debug with grpcurl, server reflection, and channel-state logs.

### Interview Questions

1. REST vs gRPC — decision criteria? (audience: browser/public vs internal; streaming needs; contract rigor; ecosystem)
2. How do deadlines propagate and why does that matter? (each hop subtracts elapsed time; prevents useless downstream work + resource exhaustion)
3. How do you evolve a proto without breaking old clients?

### Best Practices

- Deadlines on every call; retries only on idempotent methods with backoff and retry budgets; interceptors for auth/tracing/metrics; reserve removed field numbers.

### Hands-on Exercise

Define the `.proto` for an inventory service (get, batch-get, watch-stream), choose
deadlines per method, and describe the LB setup in Kubernetes (headless service +
client-side LB, or Envoy sidecar).

---

## Module 2 Cheat Sheet

```
TCP        3-way handshake (1 RTT) + TLS1.3 (1 RTT). Reliable ordered stream.
           HOL blocking. CUBIC/BBR congestion control. Keepalive vs NAT timeouts.
UDP        No guarantees, no handshake. DNS, media, games, QUIC substrate.
QUIC       TLS fused (1/0-RTT), independent streams (no transport HOL),
           connection ID → migration. UDP-based, user space. 0-RTT = idempotent only.
HTTP/1.1   1 req at a time/conn → 6 conns, bundling era.
HTTP/2     Binary frames, multiplexed streams, HPACK. TCP HOL remains.
HTTP/3     h2 semantics over QUIC. Loss isolation per stream. QPACK.
HTTPS/TLS  1.3 = 1 RTT, forward secrecy. Certs→CA chain, SNI, automate rotation.
DNS        Hierarchy + caches. TTL = failover speed. Route: weighted/latency/geo/
           failover. Anycast. Clients disrespect TTLs. Dual providers for tier-0.
CDN        Edge→shield→origin. Versioned immutable URLs > purges. Request
           collapsing, stale-while-revalidate, serve-stale-on-error. Minimal cache keys.
LB         L4 (fast, opaque) vs L7 (routing/retries/TLS). Least-conn/P2C/consistent
           hash. Health checks + outlier ejection. LB tier itself: ECMP/anycast/VRRP.
REV PROXY  TLS term, caching, buffering. Gateway = proxy + auth/rate limit/quotas/
           routing. Keep business logic OUT.
NAT        Private→public rewrite; idle timeouts kill quiet conns; P2P needs STUN/TURN.
WEBSOCKET  HTTP Upgrade→101→full duplex. Stateful tier: registry + pub/sub backplane,
           heartbeats, jittered reconnect, resume cursor, durable store = truth.
           SSE for one-way feeds.
gRPC       proto contract + HTTP/2 + streaming + propagated deadlines. Client-side/
           lookaside LB. gRPC inside, REST outside. Never renumber fields.
```

## Top Interview Questions (Module 2)

1. First-ever HTTPS request: every RTT on the wire. 2. h1 vs h2 vs h3 under packet
loss. 3. Design multi-region DNS failover and its limits. 4. CDN invalidation
strategy for a price change. 5. L4 vs L7 and making the LB tier HA. 6. Gateway
responsibilities vs service responsibilities. 7. Scale WebSockets to 5M concurrent.
8. REST vs gRPC decision. 9. Why gRPC misbehaves behind L4 LBs. 10. What breaks
long-lived connections in production (NAT/LB idle timeouts) and the fix.

## Common Mistakes Recap

Blurring LB/proxy/gateway • "h2 fixed HOL" • purge-first CDN strategy • caching
personalized content • no heartbeats/jitter on WebSockets • business logic in the
gateway • retrying non-idempotent requests • gRPC behind connection-level LB •
treating DNS TTLs as guarantees.

## Mock Interview Exercise

*"Design the global edge for a real-time sports app: 20M concurrent score
subscribers, REST API for everything else, worldwide, p99 API < 150 ms."*
Expected shape: anycast/DNS → CDN (cache API GETs w/ short TTL + collapse) → L4 →
L7 gateway (auth, rate limit) → services; scores via WebSocket/SSE fan-out tier fed
by pub/sub; per-layer failure story; protocol choices justified (h3 edge, gRPC
internal).

# MODULE 10 — Production Debugging (Real-World Scenarios)

> This module is the payoff: interviews at Meta, Google, Uber, and Cloudflare increasingly run "incident interviews" — a live scenario you must debug out loud. The winning shape is always: **clarify blast radius → localize the layer → confirm with a measurement → fix + prevent.** Never guess-then-restart.

**The universal toolbox** (memorize the mapping):

| Question | Tool |
|---|---|
| Is DNS resolving, and fast? | `dig`, `dig +trace`, `resolvectl` |
| Can I reach the port? | `nc -vz host port`, `curl -v telnet://` |
| Where does latency live per hop of one request? | `curl -w` timing breakdown |
| What are the sockets doing (cwnd, rtt, retrans, queues)? | `ss -tnpi`, `netstat -s`, `nstat` |
| What's on the wire? | `tcpdump` → Wireshark (expert info) |
| Which path hop hurts? | `mtr` (continuous traceroute + loss per hop) |
| Kernel drop counters? | `nstat -az`, `ethtool -S`, `/proc/net/*` |
| TLS specifics? | `openssl s_client`, `curl -v` |
| Per-process network usage? | `iftop`, `nethogs`, eBPF (`tcpretrans`, `tcplife`) |

The killer diagnostic one-liner to memorize:
`curl -w 'dns %{time_namelookup} tcp %{time_connect} tls %{time_appconnect} ttfb %{time_starttransfer} total %{time_total}\n' -o /dev/null -s https://api.example.com/health`
— it decomposes a request into DNS / TCP / TLS / server-think / transfer in one shot.

---

## Scenario 10.1 — High Latency

### 1. Why Interviewers Ask This
"p99 doubled last night" is the most common real page and the most common interview scenario. It tests systematic decomposition — the anti-pattern they're screening out is "restart it and see."

### 2. Core Concept
Latency = DNS + connect (RTT) + TLS + **queueing** + server processing + transfer (bytes/bandwidth, windows) + retransmission events. Localize which term grew. Golden split: is it *network* (connect/rtt/retrans grew) or *server* (TTFB grew with flat connect times)? p50 vs p99 tells you *everyone* vs *the tail* (queueing, GC, retries, cold paths).

### 3. Internal Working
Tail-latency machinery: queues (accept queue, threadpool, LB surge queue, NIC ring) convert utilization >~70–80% into exploding wait times (queueing theory: wait ~ ρ/(1−ρ)); RTO events add fixed +200ms/+1s steps (Module 2.6 signature); coordinated omission hides it in bad dashboards; fan-out amplifies (p99 of 1 call = p50 of 100-call fan-out — cite this).

### 4. Packet Flow Explanation
```
Decompose with curl -w against the same endpoint through each hop:
edge:   dns .002 tcp .050 tls .102 ttfb .690 total .700  <- TTFB is 85%!
origin direct:                        ttfb .050          <- origin fine
=> latency added between edge and origin: LB queue? cross-region hop?
   mis-routed PoP? retransmits on backbone path (check ss -i retrans)?
If instead tcp/tls grew: path RTT changed (route change! mtr both ways)
If dns grew: resolver issue (10.4).
```

### 5. ASCII Diagram
```
 [client]--dns--[resolver]   each segment is a suspect; measure, don't guess
    |___tcp+tls___[edge/CDN]___pool/queue___[LB]___queue___[svc]___[db]
 p50 up + p99 up  => systemic: route change, overload, missing cache
 p50 flat, p99 up => tail: queueing, GC, retries, one bad backend,
                     RTO events (spike at exactly +200ms = the tell)
 one region only  => path/PoP/steering | one client type => protocol/mobile
```

### 6. Real Production Example
Classic postmortem shapes: (a) BGP route change sent traffic Frankfurt→Virginia→Frankfurt (RTT 8ms→180ms — caught by mtr both directions being asymmetric); (b) conn-pool exhaustion added 300ms of *wait-for-connection* invisible in server metrics (client-side pool wait metric was the missing observability); (c) one backend with a failing NIC (retransmits) dragging p99 while p50 was fine — per-backend latency histograms found it.

### 7. Advantages (of the systematic method)
Each measurement halves the search space (binary search over the path); artifacts (curl timings, mtr, ss output) make incident review and vendor escalation (ISP/cloud) actionable.

### 8. Trade-offs
Live packet captures are heavy at 10Gbps (sample; filter narrowly); measuring from one vantage lies (client vs server view differ — measure both ends); percentile aggregation across hosts can hide a single bad host (max + per-host views needed).

### 9. Common Mistakes
- Staring at averages (p99 lives elsewhere); trusting server-side latency (excludes queueing before accept + network);
- restarting first (destroys evidence — capture `ss -tnpi` snapshot, one tcpdump before);
- assuming "network" without a single retransmit counter checked (`nstat | grep -i retrans`).

### 10. Performance Impact
Numbers to anchor answers: intra-DC RTT 0.1–1ms; cross-region 20–150ms; RTO ≥200ms; TLS cold +1 RTT; queue at 90% utilization ≈ 9× service time wait. If p99 = p50+200ms exactly → RTO. If everything +X ms uniformly → path/RTT change.

### 11. Common Interview Questions
1. "API p99 went from 80ms to 800ms at 2am, p50 unchanged. Go." 2. "Latency high only from mobile clients?" (RTT+loss+TLS cold; edge/h3 story.) 3. "How do you separate network vs application latency with one command?" (curl -w.)

### 12. Follow-up Questions
"What's coordinated omission?" → load generators that wait for slow responses under-sample the bad periods → lies in the histogram. "Why does fan-out murder tail latency, and fixes?" → P(all N fast) = (1−p)^N; hedged requests, timeouts+fallbacks, reduce N.

### 13. Debugging Scenarios (drill)
- p99 stepped +200ms exactly after a network change → loss introduced (duplex mismatch/oversubscribed link) → `nstat TcpExtTCPTimeouts` climbing → mtr shows the hop → fix link; verify counter flattens.
- Latency only for responses >64KB → window/buffer clamp (`ss -i` shows tiny cwnd/rwnd; check SO_RCVBUF misconfig).
- Everything slow only during backup window → bandwidth contention: `iftop` shows the flow; QoS/schedule fix.

### 14. Best Practices
Pre-deploy the observability you'll need at 3am: RED per endpoint + histograms (not averages), client-measured latency, per-backend/per-PoP splits, retransmit-rate dashboards, pool wait-time metrics; keep a warm runbook with the curl -w one-liner.

### 15. Practice Questions
1. p50 3ms / p95 9ms / p99 210ms / p99.9 1.2s. Read the histogram like a story. (Healthy core; RTO events at p99 — 200ms floor; p99.9 = 1s initial-RTO on fresh connections or retry-after-timeout — check handshake SYN retransmits.)
2. Design the dashboard that would have caught the pool-exhaustion example before users did. (Pool wait time, pool utilization, conn churn, queue depth — client side.)

---

## Scenario 10.2 — Packet Loss

### 1. Why Interviewers Ask This
Loss is invisible in app logs but devastating (Mathis: throughput ∝ 1/√loss), and finding *where* along a path packets die is a real skill — the interview tests tool fluency (mtr, counters, captures).

### 2. Core Concept
Loss sources: congestion (queue overflow — the usual), faulty hardware (NIC/cable/optic — corruption→CRC drops), host-level drops (ring buffer, socket buffer, conntrack full — technically "loss" to the app), policers/rate limiters, and MTU blackholes masquerading as loss (only big packets die — Module 1.5). Random-looking loss ≠ random cause: correlate with size, direction, path, time.

### 3. Internal Working
Where drops hide, outside→in: switch/router queue drops (interface counters), policer drops (invisible to you — ask provider), NIC ring overflow (`ethtool -S: rx_no_buffer/rx_missed`), kernel (`nstat`: backlog drops, conntrack `nf_conntrack: table full` in dmesg), socket buffers (`netstat -su` UDP "receive buffer errors"; TCP flow-controls instead). TCP masks loss as latency/throughput collapse; UDP apps see silence.

### 4. Packet Flow Explanation
```
Localize with mtr (loss column PER HOP, run BOTH directions — paths
are asymmetric!):
mtr -rwzbc 100 target:
 hop3 (isp-core)  loss 0%     <- transit hops showing loss to THEIR
 hop5 (peer-edge) loss 30%*      control plane may be ICMP dedprio
 hop9 (target)    loss 2%     <- ONLY end-to-end loss is real loss
*rule: loss that starts mid-path but vanishes at the destination =
 ICMP rate-limiting artifact, NOT real. Loss persisting to the last
 hop = real. This rule alone wins the interview segment.
```

### 5. ASCII Diagram
```
 app "slow"/timeouts
   |-> ss -tnpi: retrans:X/Y rising?  nstat: TcpRetransSegs/TCPTimeouts
   |-> which flows? all (link) vs one path (routing) vs big pkts (MTU!)
   |-> mtr both directions -> hop where REAL loss starts
   |-> that hop yours? ethtool -S (CRC=cable/optic, missed=ring),
   |    switch iface counters (output drops = congestion microburst)
   |-> not yours? escalate with evidence (mtr+timestamps+flow tuples)
```

### 6. Real Production Example
Recurring true stories: a flapping optic corrupting frames (CRC errors climbing on one switchport — fixed by reseating/replacing); cloud-instance "loss" that was conntrack table exhaustion during a connection storm (dmesg told the truth); microburst drops on a ToR uplink invisible in 1-min-average graphs (needed high-resolution counters) — incast, Module 2.4.

### 7. Advantages (of counter-driven diagnosis)
Counters don't lie and cost nothing (vs captures); every layer exports them; deltas over 10s (`nstat` resets, `watch -d`) turn a vague "it's lossy" into "rx_missed_errors +1200/s on eth0."

### 8. Trade-offs
Provider hops are opaque (policers don't appear anywhere you can see); ICMP-based tools (mtr/ping) measure ICMP treatment, not necessarily your TCP's QoS class (use `mtr --tcp -P 443` for realism); loss is often transient — you need always-on retransmit-rate monitoring to catch it in the act.

### 9. Common Mistakes
- Reading mid-path mtr loss as real (the #1 misread).
- Testing with ping only (small packets pass; MTU blackhole missed — test with `-s 1472 -M do`).
- Ignoring the host itself (everyone blames "the network"; check ethtool/nstat first — it's frequently your own box).
- One-direction testing (reverse path may be the broken one).

### 10. Performance Impact
Mathis math again (worth repeating in the interview): 100ms RTT, MSS 1448 → 0.1% loss caps ~14 Mbps; 1% → ~4.6 Mbps; datacenter target <0.01%. UDP media: >1–2% = visible artifacts without FEC. One number: even "just 0.5%" loss is a catastrophe for long-RTT TCP.

### 11. Common Interview Questions
1. "Users report slowness; you suspect loss. Prove it and localize it." 2. "mtr shows 40% loss at hop 4 but 0% at destination — verdict?" (Artifact.) 3. "Loss only on large transfers — hypotheses?" (MTU blackhole, microbursts filling queues, policer with small burst size.)

### 12. Follow-up Questions
"Distinguish congestion loss vs corruption loss?" → corruption: CRC/frame errors on counters, random timing, fixed % regardless of load; congestion: correlates with traffic peaks, queue drops on the bottleneck interface, tail-drop patterns. "How would ECN change this picture?" → marks instead of drops → congestion visible without loss.

### 13. Debugging Scenarios (drill)
- Kafka replication lag alerts at market open only → microburst congestion on rack uplink (interface output-drops spike) → move brokers/upgrade uplink/pace producers.
- 2% loss to exactly one /24 → routing: one ECMP path member bad — flow-hash dependence proves it (loss only for some 5-tuples! vary source ports to demonstrate) → drain the bad path.
- VPN users lose big uploads only → MTU blackhole not loss → clamp MSS (1.5/1.6).

### 14. Best Practices
Continuously monitor: retransmit rate, per-interface error/drop counters, conntrack occupancy; alert on deltas; keep mtr/tcpdump snippets in runbooks; for critical paths run scheduled synthetic probes (both directions, TCP-mode, full-MTU sized).

### 15. Practice Questions
1. Write the 5-command sequence you'd run on a host suspected of dropping inbound packets, and what each rules in/out. (`ethtool -S` NIC; `nstat -az | grep -iE 'drop|retrans'` kernel; `ss -tnpi` per-flow; `dmesg | grep -i conntrack`; `mtr --tcp` path.)
2. 10 Gbps link, 0.05% loss, RTT 40ms: estimate single-flow CUBIC throughput and the fix if you need line rate. (Mathis ≈ 1448B/(0.04×√0.0005) ≈ ~130 Mbps → parallel flows or BBR or fix the loss.)

---

## Scenario 10.3 — Connection Timeout

### 1. Why Interviewers Ask This
"Connection timed out" is the vaguest error users report and has the widest cause tree (DNS, routing, firewall, backlog, dead host, wrong port). Interviewers grade the *decision tree*, not the answer.

### 2. Core Concept
Split the timeout class first — it names the failing phase:
- **Connect timeout** (SYN sent, nothing back): packet not arriving (route/firewall-drop/dead host) or SYN-ACK lost/dropped (return path! asymmetric routing) or listener's SYN queue overflowing.
- **Read/request timeout** (connected, response never came): app slow/hung, mid-path idle teardown (NAT/LB), half-open zombie.
- **Connection refused** (RST) is *different and better*: host reachable, port closed — firewall REJECT or nothing listening. Timeout = silence (DROP); refused = active no. Saying this distinction early is a strong signal.

### 3. Internal Working
Client SYN retransmission schedule (1s, 2s, 4s… ~6 tries ≈ 2 min default) explains "takes forever then fails." Server side: SYN queue (syncookies rescue) vs **accept queue** overflow (app not accepting — GC pause, threads busy; kernel may drop the final ACK silently → client thinks it's connected, server doesn't — the nastiest variant: client sends request into the void → read timeout). Conntrack/NAT table full drops new flows silently. Security groups default-DROP → timeouts, not refusals.

### 4. Packet Flow Explanation
```
Decision tree, executed with tools:
1. dig name                 -> DNS ok? (else 10.4)
2. nc -vz host 443 (+ from ANOTHER vantage: your laptop vs pod vs region)
   refused -> port closed/REJECT: check listener (ss -ltnp on server)
   timeout -> 3. tcpdump ON SERVER: do SYNs arrive?
      no  -> path/firewall/SG/route: mtr, check SGs/NACLs/route tables
      yes, no SYN-ACK -> listener? backlog? (nstat ListenOverflows,
                          ss -ltn shows Recv-Q vs backlog limit)
      SYN-ACK sent, no final ACK seen -> return path broken (asymmetric
                          routing / client-side firewall)
```

### 5. ASCII Diagram
```
 timeout(silence)  vs  refused(RST)  vs  connects-then-hangs
   DROP rule            REJECT/no listener    app hang / NAT idle-death /
   dead host/route      (better: reachable!)  accept-queue ghost / MTU(!)
 "works from A, times out from B" => path-specific: SG/NACL scoping,
 routing, conntrack on B's NAT — diff the two paths, not the server.
```

### 6. Real Production Example
Perennial cloud incident: new service unreachable = security-group rule scoped to the wrong CIDR/port (timeout, since cloud SGs drop silently). The subtler classic: intermittent timeouts under load = accept-queue overflow during GC pauses (`ListenOverflows` climbing) — server "looks idle" in CPU graphs (Module 1.4's example, now as full incident). Third: everything fine until connection-count peak → conntrack limit on a NAT gateway.

### 7. Advantages (of the phase-split method)
Instantly prunes 80% of the cause tree; produces the right escalation artifact (tcpdump showing SYNs-arrive-no-answer vs SYNs-never-arrive assigns ownership: server team vs network team — incident politics resolved by packets).

### 8. Trade-offs
Needs access to both ends (production capture permissions — argue for pre-approved break-glass tooling); intermittent cases require patience (leave a rolling `tcpdump -W` ring buffer); cloud abstractions (SG/NACL/LB) hide hops you can't capture on.

### 9. Common Mistakes
- Not distinguishing timeout/refused/hang (three different fault classes).
- Testing only from one vantage point; forgetting the *return* path.
- Checking "is the process up" but not "is it accepting" (backlog ≠ liveness).
- Blaming the network before `ss -ltnp` + ListenOverflows on the server (60 seconds of work).

### 10. Performance Impact
Timeout config cascade matters: client connect-timeout (set it! default OS-level ~2min is user-hostile — 1–3s + retry is sane for internal calls), retries multiply load (10.9), and long timeouts hold threads/fds hostage (one hung dependency × 200 threads = your outage too). Timeouts are a resource-protection mechanism, not just UX.

### 11. Common Interview Questions
1. "curl hangs then times out — full decision tree, out loud." 2. "Timeout vs connection refused — what does each tell you?" 3. "Works from region A, times out from B — how do you diff the paths?"

### 12. Follow-up Questions
"Why can a client think it's connected while the server has no such connection?" → accept-queue-full ACK-drop ghost state (or NAT died later); "How do syncookies change SYN-flood behavior?" → no SYN-queue state → floods can't cause connect timeouts via queue exhaustion (options cost aside).

### 13. Debugging Scenarios (drill)
- Deploys cause 30s of client timeouts → old pods killed before deregistration (LB still routes to them: silence) → fix drain ordering (readiness-fail → wait → SIGTERM).
- Timeouts to a dependency exactly every ~350s of idle → NAT/NLB idle reap (Module 2.9) → keep-alives.
- 1-in-1000 connects hang cluster-internally → conntrack race / SNAT port collision on the node — kernel counters + known k8s issue; fix NodeLocal/port-range.

### 14. Best Practices
Explicit connect/read timeouts everywhere (never OS defaults); connect-timeout short + retry with backoff+jitter; monitor ListenOverflows/conntrack fill as standing alerts; pre-approved capture tooling; runbook the decision tree verbatim.

### 15. Practice Questions
1. Users in one office can't reach the app (timeout); everyone else fine. List your first four checks in order with the tool for each. (Their egress IP vs SG/allowlist — diff vantage curl; their DNS answer — dig from their resolver; their path — mtr; their proxy/MTU — full-size ping.)
2. Explain how you'd prove to the network team that SYNs are being dropped before your server, in one tcpdump command + one client command. (Server: `tcpdump 'tcp[tcpflags]&tcp-syn!=0 and port 443'`; client: `nc -vz`; SYNs absent server-side while client retransmits = path drop, with timestamps.)

---

## Scenario 10.4 — DNS Failures

### 1. Why Interviewers Ask This
"It's always DNS" is folklore because DNS failures are *weird*: partial (some users), sticky (caches), and disguised (as connect errors or 5s stalls). Interviewers test whether you can recognize DNS wearing a costume.

### 2. Core Concept
DNS failure modes: total (authoritative down/zone broken — rare, catastrophic), partial (one resolver population, one region's anycast site), slow (resolver overload → 5s client timeouts felt as "app slow"), wrong-answer (stale cache, split-horizon leaking, hijack), and self-inflicted (expired domain! bad record push, negative-cache traps). Disguises: 5s latency plateaus, "connection refused to a wrong IP," errors only on *new* connections (pooled ones keep working — a fleet "half-broken").

### 3. Internal Working
Client resolution stack failure behavior: glibc tries resolvers in `resolv.conf` serially with ~5s timeout each (hence the magic 5s/10s stalls); `options timeout:1 attempts:2 rotate` fixes; NXDOMAIN vs SERVFAIL vs timeout are *different diagnoses* (name doesn't exist vs resolver's upstream problem vs unreachable). Negative caching makes NXDOMAIN sticky (SOA MINIMUM). K8s adds CoreDNS + ndots + conntrack races (Module 5.2).

### 4. Packet Flow Explanation
```
Triage ladder (each step isolates one layer):
1. dig api.example.com            <- via configured resolver: broken?
2. dig @1.1.1.1 api.example.com   <- public resolver: same answer?
   differs => your resolver/cache problem (flush? forwarder dead?)
3. dig @ns1.provider.com +norec   <- authoritative directly: truth?
   SERVFAIL/timeout here => provider/zone incident (status page, failover)
4. dig +trace                     <- full delegation walk: where does it die?
   (registrar/NS misconfig, DNSSEC validation failure shows here)
compare NXDOMAIN (record truly absent? typo? negative-cached?) vs
SERVFAIL (resolver upstream/DNSSEC broken) vs empty NOERROR (record
type mismatch — asked A, only CNAME→AAAA exists?).
```

### 5. ASCII Diagram
```
 symptom translation table:
 5s exact stalls          -> resolver timeout (first NS dead)
 errors on new conns only -> DNS broken, pools coasting on old IPs
 one region broken        -> anycast site / regional resolver outage
 works by IP not by name  -> 100% DNS (bypass test — always do this)
 after a "successful" change, some users on old IP -> TTL decay (5.4)
 everything down + can't reach your own tooling -> your zone/registrar
                            (Facebook 2021 pattern; keep out-of-band!)
```

### 6. Real Production Example
Facebook 2021 (BGP withdrew authoritative DNS → global outage including internal tools); Dyn 2016 (authoritative DDoS → half the internet's names dark for hours → multi-provider doctrine); Microsoft Teams/Azure and countless others via *expired domains/certs*; everyday enterprise version: someone pushes a bad record, negative caches make the fix "not work" for MINIMUM seconds.

### 7. Advantages (of the triage ladder)
Four `dig` commands assign blame precisely (my cache / my resolver / provider / registrar) — DNS incidents are escalation-heavy and evidence shortens them; the by-IP bypass test converts "is it DNS?" from debate to fact in 10 seconds.

### 8. Trade-offs
Caches mean your test ≠ user's reality (their resolver, their TTL clock — use external probe networks); fixes are TTL-gated (you can't push, only wait or dual-serve — Module 5.4); anycast resolver issues are geographically invisible from your desk.

### 9. Common Mistakes
- Testing once from your laptop and declaring victory (your cache lies).
- Confusing NXDOMAIN with SERVFAIL (opposite escalation paths).
- Forgetting pooled connections mask DNS death (fleet looks "randomly" broken as pools churn).
- Renewals: domains and DNSSEC keys expire like certs — unmonitored.

### 10. Performance Impact
Resolver latency sits on *every cold connection* (Module 5.1 numbers); resolver failure = +5s per attempt per host = instant p99 apocalypse even at 99% resolver success; app-side: missing local caching turns DNS into a top-QPS dependency.

### 11. Common Interview Questions
1. "Half your fleet can't reach the payment API; the other half is fine. DNS suspicion — prove and fix." 2. "NXDOMAIN vs SERVFAIL vs timeout — what does each mean?" 3. "Your DNS change 'didn't take' — walk the cache forensics." (5.4 replay.)

### 12. Follow-up Questions
"How do you make an app resilient to resolver outages?" → local caching daemon + serve-stale, multiple resolvers with rotate + short timeouts, connection reuse (fewer resolutions), optionally last-known-good IP fallback for critical deps. "What breaks when you hardcode IPs as the 'fix'?" → failover/steering dies silently later — time-bomb; if you must, pair with monitoring.

### 13. Debugging Scenarios (drill)
- App latency histogram grows a spike at exactly +5.0s → first nameserver in resolv.conf unreachable → fix resolver list + `timeout:1`.
- K8s: external calls slow, internal fine → ndots:5 walking search domains (5 queries per lookup) → FQDN trailing dot / ndots:1 / NodeLocal.
- Some ISPs' users get NXDOMAIN for your new subdomain for ~an hour → negative caching (queried pre-creation) + their resolver's floor — wait or rename; prevention: create records before announcing.

### 14. Best Practices
Monitor resolution externally (multiple geographies/resolvers) + domain/DNSSEC expiry; local DNS caching on every host/node; resolv.conf tuned (timeout 1–2s, attempts 2, rotate); runbook the 4-step dig ladder; out-of-band access that doesn't depend on your own domain.

### 15. Practice Questions
1. Write the four dig commands of the triage ladder for `api.shop.com` and state what each outcome pair implies.
2. Your standby region's DNS failover fired at 03:00 but synthetic checks show 20% of traffic still hitting the dead region at 03:30. Enumerate causes and which you can act on. (TTL decay + clamping resolvers + pooled conns + client OS caches; act on: kill old-region conns (RST/withdraw), lower future TTLs, client re-resolve-on-error policy.)

---

## Scenario 10.5 — Slow APIs

### 1. Why Interviewers Ask This
"The API is slow" arrives with zero information; converting it into a localized, measured cause is the daily job of a senior engineer — interviews simulate exactly this vagueness on purpose.

### 2. Core Concept
Slow API = high latency (10.1) *scoped to an application boundary* — so the network method plus the app-side suspects: N+1 queries, missing index, cold caches, pool exhaustion (DB/HTTP), GC, lock contention, payload bloat, serial fan-out, retry amplification, noisy neighbor. First move is always scoping: which endpoints, which percentile, which callers, since when, what changed?

### 3. Internal Working
The request's time budget across layers, and who owns each: client network (curl -w segments) → LB queue (surge queue depth metric) → server queue (threadpool/event loop lag) → handler CPU → downstream calls (DB/cache/RPC — tracing spans) → serialization+transfer (payload size × client bandwidth; compression). Distributed tracing (OpenTelemetry) is *the* tool: one slow trace names the guilty span — interviewers expect you to reach for traces before tcpdump here.

### 4. Packet Flow Explanation
```
scoping questions -> instrumentation path:
"all endpoints or one?"  one -> that handler's downstream (trace it)
                         all -> shared layer: LB, runtime (GC!), infra
"all callers or one?"    one -> caller's network/payloads/retries
"p50 or tail?"           tail -> queueing/GC/one-bad-backend
"since when?"            deploy? traffic shape? data growth (index!)?
then ONE slow trace: gateway 5ms | svc 8ms | db 1400ms <- verdict
  (vs symmetric slowness everywhere -> resource saturation: check
   USE: utilization/saturation/errors on cpu, pool, disk, net)
```

### 5. ASCII Diagram
```
 [client]-net->[LB q]->[srv q]->[handler]->[db/cache/rpc]->[serialize]->
 owner:  netops   infra    app      app        app+dba        app
 tools:  curl -w  LB metr  runtime  profiler   traces/slowlog  payload size
 classic causes by signature:
  grows with data size -> missing index/N+1 | after deploy -> code/config
  cyclic -> cron/GC/neighbor | tail-only -> queue/pool | cold-only -> cache
```

### 6. Real Production Example
The recurring big three in postmortems: (1) ORM N+1 — endpoint slowed linearly with list size (fixed by eager loading; found via one trace with 200 identical DB spans); (2) connection-pool ceiling — DB pool 20 conns at 500 RPS → 300ms queue wait invisible in DB metrics (client pool metrics!); (3) retry amplification during a downstream brownout turning 1× load into 3× (10.9 preview).

### 7. Advantages (of trace-first debugging)
One exemplar trace beats an hour of dashboard archaeology; span attribution ends cross-team blame instantly; traces catch *composition* problems (serial calls that should be parallel) that no single component's metrics reveal.

### 8. Trade-offs
Sampling can miss the tail (tail-based sampling exists — mention it); tracing adds overhead/infra; spans lie at boundaries they don't instrument (queue wait *before* the span starts — the pool example — so pair traces with queue/pool gauges).

### 9. Common Mistakes
- Jumping into code/profilers before scoping (which/who/when).
- Server-side-only view (misses client network, LB queue, DNS).
- Optimizing p50 when the complaint is p99; ignoring payload size (a 4MB JSON response is a network problem *created by* the app).
- Not asking "what changed?" (deploys, feature flags, data milestones, traffic mix).

### 10. Performance Impact
Order-of-magnitude anchors for verdicts: local cache ~µs; Redis ~0.5ms; indexed DB query ~1–5ms; unindexed scan ~100ms–10s; intra-DC RPC ~1ms; cross-region ~50–150ms; JSON serialization of 1MB ~5–20ms; GC pause 1–500ms. A senior instantly sniffs "1.4s DB span = missing index or lock wait, not network."

### 11. Common Interview Questions
1. "Users say checkout is slow. You have 10 minutes. Narrate." 2. "How do you find N+1 problems in production?" (Trace span counts, DB query logs grouped by shape.) 3. "API is slow only for one big customer — why?" (Their data size → unindexed path; their payloads; their region; per-tenant noisy-neighbor.)

### 12. Follow-up Questions
"Traces show nothing slow but users disagree" → time is *between* spans: queues (pool wait, event-loop lag) or client-side (network, rendering) — instrument the gaps + RUM. "How do you keep APIs fast permanently?" → latency budgets per SLO with per-dependency allocation, perf regression tests in CI, payload budgets, tail-latency alerting.

### 13. Debugging Scenarios (drill)
- Every ~2 min all endpoints stall 800ms → GC (runtime pause metrics correlate) → heap/allocation tuning.
- Slow only first request per pod after deploys → cold JIT/caches/connection pools → warmup before readiness.
- One endpoint's p99 degrades each week → data growth crossing an index/plan boundary → EXPLAIN before/after, add index; the "slow query log + calendar" diagnosis.

### 14. Best Practices
Instrument before incidents: tracing with tail sampling, RED per endpoint, USE per resource, pool/queue gauges, per-dependency latency SLO budgets; keep an exemplar-trace link in every latency alert; payload-size budgets enforced in code review.

### 15. Practice Questions
1. Trace shows: gateway 4ms → svc A 6ms → [svc B 90ms → db 2ms ×30 sequential] → total 2.8s. Name the two distinct anti-patterns and the fixes. (N+1 across services + sequential fan-out → batch endpoint + parallelize; also question why B needs 30 lookups at all — denormalize/cache.)
2. Define the latency budget for a 500ms-SLO endpoint calling auth, db, cache, and a 3rd-party API. Where do you put the slack and the timeout on the 3rd party? (3rd-party gets a hard 150–200ms timeout + fallback; never let the piece you don't control own your SLO.)

---

## Scenario 10.6 — Network Bottlenecks

### 1. Why Interviewers Ask This
Throughput problems ("replication can't keep up," "the link is full") test a different muscle than latency: capacity math (BDP, line rates, pps budgets) and locating the *narrowest* resource among link, NIC, CPU, and protocol window.

### 2. Core Concept
Throughput ceiling = min(link bandwidth on the narrowest hop, window/RTT (TCP), pps × packet-size (CPU/NIC packet budget), application production rate, per-flow limits like policers/ECMP-hash-fate). Diagnose by computing what each ceiling *should* be, measuring actuals (`iperf3` for path capability vs app throughput), and finding which constraint binds.

### 3. Internal Working
The three distinct budgets people conflate: **bandwidth** (bits/s on the wire), **packet rate** (pps — per-packet CPU: interrupts, lookups; 1500B frames at 10G = 830k pps; small-RPC workloads exhaust pps long before bandwidth), and **window** (in-flight bytes ≤ min(cwnd, rwnd) → single-flow max = window/RTT regardless of link — Module 2 math). Plus host limits: single-core softirq saturation (irq affinity/RSS), NIC offloads off, memory bandwidth.

### 4. Packet Flow Explanation
```
"replication between DCs stuck at 300 Mbps on a 10G link":
1. iperf3 single stream        -> 310 Mbps   (matches app: path/proto limit)
   iperf3 -P 8 (parallel)      -> 2.4 Gbps   => per-FLOW ceiling, not link
2. compute: RTT 60ms, 310Mbps => window ≈ 2.3MB — suspiciously ≈ default
   tcp_rmem max / app SO_RCVBUF clamp / not-scaled window!
3. ss -tnpi: cwnd huge, rwnd 2.3MB pinned  => receiver buffer clamp
4. fix tcp_rmem / remove setsockopt; retest 8 Gbps; alternatively
   loss-limited case: retrans>0 -> Mathis math -> BBR/parallel/fix loss.
if parallel ALSO capped: policer? single ECMP path member? link truly full
   (interface counters at both ends: utilization + drops).
```

### 5. ASCII Diagram
```
 ceilings, compute EACH:                     typical tells:
 link:    narrowest hop line rate            iface util ~100%, queue drops
 window:  min(cwnd,rwnd)/RTT                 throughput ∝ 1/RTT, one flow
 loss:    MSS/(RTT·√p)                       retrans counters, sawtooth
 pps:     core softirq 100%                  small pkts, %si pegged, drops
 app:     producer can't fill pipe           send-q empty! (Module 1.2)
 golden discriminator: ss -tnpi send-q: full => network-bound;
                                empty => application-bound.
```

### 6. Real Production Example
Cross-region database restores capped by default 4MB tcp_rmem (window/RTT on 70ms ≈ 460 Mbps) — fixed fleet-wide by raising buffer maxima (the most-repeated infra tuning story in existence); NFV/proxy boxes falling over at low bandwidth but high pps (small packets — needed RSS tuning + more cores); "the 10G link is full" that was actually one elephant flow hashed onto one LAG member (per-flow hashing — 4×10G LAG ≠ 40G for a single flow: a favorite interview nugget).

### 7. Advantages (of ceiling-math-first)
Prevents the classic wild goose chase (tuning the app when the window is clamped, buying bandwidth when pps-bound); each ceiling has a one-line formula — you can *predict* the fix's outcome before applying it (and impress the room).

### 8. Trade-offs
iperf tests consume real capacity (schedule/off-peak, or use pacing); parallel-flow fixes shift fairness (N flows grab N shares); big buffers fix throughput but add bufferbloat latency for competing traffic (know both sides); jumbo frames need end-to-end coordination (1.5).

### 9. Common Mistakes
- Conflating the three budgets ("we have 10G!" while single-flow window-bound).
- Testing with parallel iperf only (hides per-flow limits your app will hit).
- Ignoring the reverse direction (ACK path congestion throttles forward throughput — ACK compression/loss).
- Forgetting per-flow ECMP/LAG hashing (one flow can't use multiple members).

### 10. Performance Impact
Anchor numbers: 1500B@10G=830kpps, @1G=83kpps; default Linux tcp_rmem max often 4–6MB → ~64MB needed for 10G×50ms; interrupt-per-packet without coalescing/GRO melts a core around ~1Mpps; a single policer at 100Mbps with tiny burst wrecks TCP far below 100Mbps (burst-size matters, not just rate).

### 11. Common Interview Questions
1. "Single TCP flow between DCs won't exceed N Mbps — enumerate the possible ceilings and how you'd test each." 2. "When is a system pps-bound vs bandwidth-bound?" 3. "Why doesn't LACP/ECMP help a single large flow?"

### 12. Follow-up Questions
"How does BBR change the loss-limited case?" → models BW×RTT instead of backing off on loss → near-capacity on lossy long paths. "MPTCP or parallelism at app layer?" → practical answer: app-level parallel streams (like gridFTP/S3 multipart) is the deployed solution.

### 13. Debugging Scenarios (drill)
- Backup saturates link nightly and pages you for app latency → competing elephant flow + bufferbloat → QoS/pacing (`tc`), schedule, or separate paths.
- 100k RPS of 200-byte messages maxing a box at 30% bandwidth → pps/softirq bound → RSS across cores, batch APIs (sendmmsg), bigger messages/coalescing.
- Throughput fine except to one AZ → asymmetric path or one bad ECMP member (10.2 crossover) → hash-varied probes.

### 14. Best Practices
Capacity dashboards in all three currencies (bps, pps, conns) per link/NIC; autotuning buffers verified (no legacy setsockopt clamps); BBR+fq for WAN egress; per-flow expectations documented (window math) so alarms fire on the right metric; iperf3 runbooked per-region pairs.

### 15. Practice Questions
1. You must move 2TB Frankfurt→Tokyo (RTT 240ms, 10G both ends, 0.01% loss) nightly in <2h. Required ~2.3 Gbps: single CUBIC flow? (Mathis ≈ 1448/(0.24×0.0001^0.5)... ≈ ~480 Mbps — no) Design the transfer. (8–16 parallel streams or BBR + big windows ≈ achievable; multipart + checksums + pacing.)
2. A service does 1M msg/s of 300B over one TCP conn between two hosts and the sender's core is pegged. List three fixes across different layers. (Batching/coalescing at app; GSO/writev/sendmmsg syscall layer; RSS/multiple conns to spread cores.)

---

## Scenario 10.7 — TLS Failures

### 1. Why Interviewers Ask This
TLS failures are common (expiry! chains! version skew!), user-visible, and have crisp diagnostic tooling — perfect interview material to test precision. Bonus: they probe whether you can read handshake errors instead of fearing them.

### 2. Core Concept
Failure classes, each with a distinct signature: **expiry/validity** (clock says no), **chain** (missing intermediate — works in browsers, fails in code: 9.2), **name mismatch** (SAN ≠ hostname; SNI routing to wrong vhost cert), **version/cipher mismatch** (legacy client vs modern server or vice versa), **trust store** (container missing CA bundle; corporate MITM roots), **protocol interference** (middlebox tampering, `bad record mac`), **resumption/0-RTT edge cases**, and **client cert (mTLS) failures**.

### 3. Internal Working
Read the alert taxonomy like error codes: `certificate_expired`, `unknown_ca` (their store lacks your chain — or your chain is incomplete), `handshake_failure` (no common cipher/version/curve), `certificate_unknown`, `bad_record_mac` (corruption/tampering — MTU/middlebox!), `unrecognized_name` (SNI vhost miss). Client vs server alerts tell you which side rejected. Clock skew (IoT/VMs after resume) fails validity checks with perfectly good certs — always check `date` first on weird devices.

### 4. Packet Flow Explanation
```
triage with openssl s_client (the TLS swiss knife):
openssl s_client -connect api.x.com:443 -servername api.x.com
  -> Verify return code: 0 (ok)?  10 (expired)?  20/21 (unable to get
     issuer = CHAIN)?  18 (self-signed)?
  -> shows: chain as SERVED (count the intermediates!), negotiated
     version/cipher, ALPN, SAN list (-showcerts to dump)
variants: -tls1_2 (force version — does legacy work?), -cert/-key (mTLS),
          omit -servername (what default vhost cert do SNI-less get?)
compare: curl -v (client-realistic) | Java/Python clients use THEIR OWN
trust stores — browser-works-curl-works-Java-fails = trust store drift.
```

### 5. ASCII Diagram
```
 who fails? ALL clients        -> cert itself: expired/revoked/wrong SAN
            new deploys only   -> chain/config on new nodes; ticket keys
            one language/runtime -> its trust store / TLS version support
            one network        -> MITM proxy, middlebox, MTU(big cert
                                  chain doesn't fit -> hang not error!)
            intermittent       -> mixed fleet (one node bad cert/config),
                                  resumption edge, LB pool asymmetry
 handshake HANGS (vs fails) => usually not TLS: MTU blackhole eating
 the certificate flight (1.5!) — the sneakiest one; test with -tls1_3
 (smaller flights) and ping -M do.
```

### 6. Real Production Example
Expiry outages (Microsoft Teams 2020 among many) — always automation gaps; the "one pod has last year's cert" mixed-fleet intermittent (config drift — hash your served certs in monitoring); enterprise-MITM breakage (corporate proxies with own roots failing pinned/modern-TLS apps); Let's Encrypt root expiry (Sept 2021, DST Root X3) breaking *old clients only* — a masterclass in trust-store-skew incidents worth citing.

### 7. Advantages (of alert-literate debugging)
TLS fails *loudly and specifically* if you read the alert + verify-code — minutes to diagnosis; `s_client` needs no privileged access; served-chain vs required-chain comparison is deterministic (no flakiness).

### 8. Trade-offs
Client error reporting varies wildly (browsers hide detail; JVM stack traces mislead); you often can't see the *client's* trust store (IoT/old Android matrices — test labs needed); captures of TLS 1.3 show little without keys (use endpoints' debug modes/qlog for h3).

### 9. Common Mistakes
- Testing only from a browser (auto-fetches intermediates via AIA — masks chain bugs).
- Forgetting SNI in tests (`-servername`! curl by IP hits default vhost).
- Not checking *both* validity ends (notBefore fails on clock-ahead devices).
- Blaming TLS for MTU hangs; renewing the cert but not reloading the process (served ≠ on-disk — check!).

### 10. Performance Impact
Failure-adjacent perf issues interviewers accept as bonus: chain > ~14KB = +1 RTT cold (9.2); OCSP without stapling = client-side stall on some networks; resumption misconfig across an LB fleet (no shared ticket keys) = full handshakes fleet-wide = CPU + latency regression that looks like "TLS got slow."

### 11. Common Interview Questions
1. "Mobile apps fine, server-to-server calls failing TLS since yesterday — go." (Chain or trust-store; s_client verify code; served chain diff.) 2. "How do you monitor certs properly?" (External probe of *served* chain + expiry on every endpoint incl. internal, not just a spreadsheet of issued certs.) 3. "TLS handshake times out rather than erroring — what's special?" (MTU/middlebox — the hang-vs-fail distinction.)

### 12. Follow-up Questions
"Rotate a cert with zero downtime across 200 nodes?" → dual-serve capable config, staged reload, verify served-cert hash converges, keep old key until fleet confirms. "What breaks when you switch RSA→ECDSA?" → ancient clients without ECDSA support — dual-cert configs serve both, selected by handshake.

### 13. Debugging Scenarios (drill)
- 03:00 page: "SSL certificate problem: certificate has expired" from internal cron jobs only → an *internal* CA-signed endpoint missed by the ACME automation inventory → fix + add to external monitoring.
- After LB scale-out, ~10% of handshakes fail → new nodes missing intermediate in bundle → served-chain hash alert.
- One customer's on-prem agent fails with `unknown_ca` since their proxy upgrade → MITM proxy re-signing with their root → document supported egress modes / proxy allowlist.

### 14. Best Practices
Monitor the *served* endpoint (chain completeness + expiry <21d + verify-code 0) externally on every TLS port including internal; automate renewal + reload + convergence check; pin nothing without a rotation plan; keep a client-matrix test (old Android/Java/OpenSSL) for public endpoints; clock sync (NTP) everywhere.

### 15. Practice Questions
1. Write the exact s_client invocations to prove: (a) chain completeness, (b) SNI vhost correctness, (c) TLS1.2-only client compatibility, (d) mTLS client-cert acceptance.
2. Design cert monitoring for: 3 public LBs, 40 internal mTLS services, 5 customer-pinned endpoints. What alerts exist and what does each catch? (External served-chain probes; mesh cert TTL/rotation lag metrics; pinned-cert change freeze + coordinated rotation calendar.)

---

## Scenario 10.8 — CDN Cache Misses

### 1. Why Interviewers Ask This
"Hit ratio dropped 30 points" burns money and origins fast; diagnosing it exercises the whole Module 7 header/key model under time pressure — a favorite at CDN-heavy shops (Cloudflare, Netflix, e-commerce).

### 2. Core Concept
A "cache-miss incident" is always one of: **key fragmentation** (URL/query/Vary/cookie variants exploding the keyspace), **cacheability regression** (new headers: Set-Cookie, no-store, private, Authorization; TTL dropped), **eviction pressure** (catalog grew / PoP cache contention — LRU evicting before TTL), **invalidation abuse** (purge-everything in a deploy pipeline), or **traffic-shape change** (long-tail shift, cache-busting query params from a new client/campaign, bot scrapes of unique URLs).

### 3. Internal Working
Response header forensics: `X-Cache`/`CF-Cache-Status` (HIT/MISS/EXPIRED/BYPASS/DYNAMIC — each is a different diagnosis: BYPASS=config says don't; DYNAMIC=deemed uncacheable; EXPIRED=TTL; MISS=not present: new key or evicted), `Age` (time in cache — Age resets across the fleet reveal purges/restarts), `Cache-Control` as *served* (did the app change it?). Distinguish hit-ratio by requests vs by bytes vs by *origin-load* — a bot spraying unique URLs tanks request-ratio while humans still get hits.

### 4. Packet Flow Explanation
```
triage sequence:
1. when did it drop + what shipped? (deploy diff: headers/routes/params)
2. sample misses from CDN logs: GROUP BY normalized-URL, query-string
   shape, Vary inputs, cookie presence
   -> same URL repeatedly MISS? (cacheability/eviction/purge)
   -> unique-URL flood? (cache-busting params, bot, campaign links
      utm_*=random -> normalize/strip at edge)
3. curl -sD- the top miss URL twice through the CDN:
   2nd response HIT? -> eviction/fragmentation at scale, not config
   still MISS/BYPASS/DYNAMIC? -> read served Cache-Control/Set-Cookie
   -> the app regression (middleware adding a session cookie is the
      classic: analytics/AB-test framework added Set-Cookie to HTML)
```

### 5. ASCII Diagram
```
 status decoder:  BYPASS  -> CDN config rule says skip (page rules)
                  DYNAMIC -> response judged uncacheable (headers!)
                  MISS    -> new key (fragmentation? purge? eviction?)
                  EXPIRED -> TTL passed (was TTL shortened?)
                  HIT+Age reset everywhere -> mass purge happened
 fragmentation suspects: ?utm_*/fbclid | Vary: Cookie/User-Agent |
 device-split URLs | locale in path×query mixed | http/https/host variants
 money math: hit 95%->65% = origin traffic x7. state this.
```

### 6. Real Production Example
The archetypes: marketing launches links with random `utm_`/click-ID params → every visitor a unique cache key (fix: strip/normalize params in cache key — most CDNs one-liner); a framework upgrade silently adding `Set-Cookie` to every response → global DYNAMIC (CDNs won't cache Set-Cookie responses by default — 7.4); a deploy pipeline running purge-all on each of 30 daily deploys → permanent cold cache; catalog 10× growth quietly exceeding PoP working-set → TTL-irrelevant LRU misses (fix: tiered/shield + longer TTL + smaller variants).

### 7. Advantages (of log-forensics method)
CDN logs contain the full verdict trail (status + key inputs) — no origin instrumentation needed; two curls reproduce or exonerate config in seconds; grouping misses by shape names the culprit class immediately.

### 8. Trade-offs
CDN sampling/log latency during incidents; per-PoP variance (one cold/misbehaving PoP vs global issue — always split metrics by PoP); provider config abstractions (page rules, "smart" defaults) can override your headers — trust the *observed* status, not the intended config.

### 9. Common Mistakes
- Watching request-hit-ratio only (bytes and origin-QPS tell different stories; bots distort).
- Forgetting purge audit trails (someone's script); not checking *which* header the CDN honored (`s-maxage` beats `max-age`; page rule beats both).
- "Fixing" by forcing cache on responses that were uncacheable *for a reason* (Set-Cookie sessions → cross-user leaks: the incident worse than the outage — 7.4's warning).

### 10. Performance Impact
Origin exposure math to present: at 50k RPS edge, hit 95%→65% = origin 2.5k→17.5k RPS (×7) — is origin autoscaled for that? Latency: users move from ~20ms edge to ~200ms origin path = visible p50 shift. Cost: origin egress + compute. Frame misses as an *availability risk*, not just perf.

### 11. Common Interview Questions
1. "Hit ratio fell off a cliff at 14:00. First three checks?" (Deploy diff; CDN status-code mix shift — BYPASS/DYNAMIC vs MISS; miss-URL shape sampling.) 2. "Explain each cache status and what it implicates." 3. "How do you protect origin while you debug?" (Raise TTLs/serve-stale/enable coalescing first — stop the bleeding, then diagnose.)

### 12. Follow-up Questions
"Design cache keys for an international, A/B-tested, logged-in-optional site without fragmenting." → normalize params allowlist, cookie-free HTML for anon + edge-injected personalization (7.2), locale by path only, Vary minimal. "How do you canary CDN config?" → staged rollout by percentage/PoP with hit-ratio + origin-QPS guardrails (CDN config is deploy #1 outage class — 7.2).

### 13. Debugging Scenarios (drill)
- Hit ratio fine, origin load doubled anyway → revalidation storm: TTL shortened so EXPIRED→304 churn (check conditional-request rate); lengthen TTL + SWR.
- One country's users all MISS → their PoP cold after maintenance or steering moved them to a fresh PoP (Age=0 there; warms in minutes — but explains user complaints).
- HTML misses only for logged-out mobile users → device-detection middleware setting a cookie + Vary — the intersection nobody tested.

### 14. Best Practices
Guardrail alerts: hit ratio (requests + bytes), origin QPS, BYPASS/DYNAMIC share, purge audit log; cache-key config as code + review; header contract tests in CI (assert Cache-Control per route class); pre-launch checklist for campaigns (param normalization); serve-stale + coalescing always-on as origin armor.

### 15. Practice Questions
1. From these five sampled miss log lines (unique fbclid params, Set-Cookie present, Vary: User-Agent, status DYNAMIC, Age: 0 after 30 TTL) — name each root cause and its one-line fix.
2. Write the CI test that would have caught "framework upgrade adds Set-Cookie to static routes" before production. (Integration test asserting absence of Set-Cookie + presence of expected Cache-Control on route classes.)

---

## Scenario 10.9 — Retry Storms

### 1. Why Interviewers Ask This
The retry storm is *the* canonical metastable failure: a small blip becomes a self-sustaining outage because everyone's "resilience" code attacks in unison. It's the deepest test of distributed-systems maturity in the debugging genre — Google/AWS interviews love it.

### 2. Core Concept
Mechanism: dependency slows → callers time out → retry (×2–3 load) → dependency saturates further → more timeouts → more retries. **Multiplicative across layers**: 3 retries at edge × 3 at service × 3 at client library = 27× amplification of a single user action. The system enters a **metastable state**: even after the original cause heals, retry load alone keeps it pinned down (recovery requires load *shedding*, not just waiting — this insight is the interview's core).

### 3. Internal Working
The defense stack (know all six):
1. **Backoff + full jitter** (`sleep = rand(0, min(cap, base×2^n))` — AWS's paper: full jitter beats equal/decorrelated for contention).
2. **Retry budgets** (retries ≤10–20% of requests, cluster-wide — Envoy implements; hard cap on amplification).
3. **Circuit breakers** (stop calling a failing dependency; half-open probes for recovery).
4. **Only-retry-retryable** (5xx/timeout/connect — never 4xx; idempotency required for non-GET).
5. **Single-layer retries** (retry at ONE tier — usually the edge; inner layers propagate failure fast: deadline propagation, Module 8.5).
6. **Load shedding + queue caps at the callee** (reject early [503+Retry-After] instead of queueing into death; adaptive concurrency limits).

### 4. Packet Flow Explanation
```
anatomy of the incident:
t0   db p99 500ms->2s (a vacuum, a deploy, whatever — trigger is trivial)
t1   svc timeout=1s fires -> retries x3 => db QPS x3 -> db at 100%
t2   gateway timeouts fire -> its retries x3 => x9 -> conn pools exhaust
t3   users refresh (human retry layer!) => x27; healthy endpoints starve
     (shared pools/threads) — blast radius now total
t4   db recovers... but arrival rate = 27x normal => still saturated
     METASTABLE: the outage now sustains itself           <- say this
recovery: shed load at the edge (reject 70%+), drain queues, restore
gradually (ramp %), THEN fix retry configs so it can't recur.
```

### 5. ASCII Diagram
```
 load
  27x|            ____________________ <- retry-sustained plateau
     |           /                      (trigger long gone)
   9x|          /
   3x|      ___/
   1x|_____/        ^trigger   ^trigger healed... nothing improves
     +------------------------------------ time
 telltale metrics: QPS up while SUCCESS rate down; queue depth pinned;
 retry% of traffic >20%; recovery only after load shedding — not after fix
 defenses: jitter | budgets | breakers | one-layer | deadlines | shedding
```

### 6. Real Production Example
AWS DynamoDB Sept 2015: a network blip → storage-node metadata retries → metadata service overwhelmed → region-wide cascading failure; the postmortem introduced wider adoption of retry budgets and is *the* citable case. Same shape recurs in many public postmortems (Slack Jan 2021: provisioning + retry amplification). Every mature stack now ships budgets (Envoy/gRPC retry throttling, finagle budgets) because of this class.

### 7. Advantages (of budget/breaker discipline)
Bounds worst-case amplification mathematically (budget = hard ceiling); breakers convert "hammering a corpse" into fast-fail + graceful degradation; single-layer policy makes system behavior *analyzable* (you can compute peak load).

### 8. Trade-offs
Budgets/breakers add config surface + failure modes of their own (breaker flapping, premature opens on noisy metrics); aggressive shedding trades availability-for-some vs degraded-for-all (product decision — say who decides); jitter increases individual-request tail latency slightly (the price of herd immunity).

### 9. Common Mistakes
- Retries with no jitter (synchronized waves — thundering herd on recovery), no cap, no budget; retrying non-idempotent writes (duplicate payments!) without idempotency keys.
- Retrying at every layer "for safety" (multiplicative — audit the whole call chain, including client SDKs and *user-facing* auto-refresh).
- Timeouts longer at inner layers than outer (outer gives up + retries while inner still works: wasted work + amplification — deadlines must *shrink* inward).
- Treating recovery as "wait for dependency to heal" (metastability means it won't — must shed).

### 10. Performance Impact
Quantify in interviews: 3 layers × 3 attempts = 27× theoretical, but pools/queues saturate earlier so observed is "everything pegged"; retry-share of traffic is the leading indicator (alert >10%); with full-jitter backoff + 20% budget, the same trigger yields ≤1.2× load — a 20× difference from config alone. That sentence wins the round.

### 11. Common Interview Questions
1. "Walk me through how a 30-second database slowdown became a 4-hour outage." (The anatomy above.) 2. "Design the retry policy for a 4-tier architecture." (One retry layer, budgets, jittered backoff, deadline propagation, idempotency keys, breakers per dependency.) 3. "Why doesn't the system recover when the root cause is fixed?" (Metastable state; shed to escape.)

### 12. Follow-up Questions
"Why *full* jitter specifically?" → spreads retries uniformly over the window — minimizes collision probability vs exponential-only (all clients synchronized at 1s,2s,4s marks). "Circuit breaker thresholds?" → error-rate + minimum-volume windows, half-open probe rate, per-endpoint not global (avoid one bad route opening the breaker for all). "How do you *test* this?" → chaos: inject dependency latency in staging, assert amplification ≤ budget; load-shed drills.

### 13. Debugging Scenarios (drill)
- During incident: is it a storm? → compare QPS vs unique-user actions (ratio ≫ normal), retry-flagged request share, arrival rate at each tier (amplification staircase across tiers is the fingerprint).
- Post-recovery flapping: dependency heals, breakers half-open, herd of probes re-kills it → jittered probe budget, slow ramp.
- "Retries are 40% of DB load in steady state" (no incident!) → too-tight timeouts on a p99-heavy call: retries as chronic waste — fix timeout to fit the real distribution or fix the p99.

### 14. Best Practices
Org-wide retry standard: single designated retry layer, full-jitter exponential with cap, budget ≤20%, retry only idempotent+retryable, deadlines propagate and shrink inward, breakers + load shedding + Retry-After honored; retry-share dashboards + alerts; chaos-test the policy quarterly; idempotency keys on all mutating APIs.

### 15. Practice Questions
1. Given: edge (3 attempts, 2s timeout) → svc (3 attempts, 1s) → db-client (2 attempts, 500ms). A db query takes 900ms. Trace exactly what happens for one user request and count db queries issued. (db-client: attempt1 times out at 500ms, attempt2 times out; svc attempt fails at 1s → svc retries ×3 → 6 db queries; edge times out at 2s mid-flight and retries ×3 → up to 18 queries, all for one user click — then redesign it.)
2. Write the load-shedding policy for the recovery phase: what % do you reject, keyed on what, and how do you ramp? (Reject to bring arrival ≤80% of measured capacity; prioritize by request class (health checks/payments first, browse later) or fair per-user; ramp +10–20% per healthy interval with abort-on-regression.)

---

# MODULE 10 — One-Page Cheat Sheet

```
METHOD        blast radius (who/where/when/what-changed) -> localize layer
              -> MEASURE to confirm -> fix -> prevent. Never guess-restart.
ONE-LINER     curl -w 'dns %{time_namelookup} tcp %{time_connect} tls
              %{time_appconnect} ttfb %{time_starttransfer}' — decomposes
              any request into DNS/TCP/TLS/server/transfer
LATENCY       p50 vs p99 first. +200ms exactly = RTO. TTFB grew = server;
              connect grew = path; fan-out multiplies tails; queues explode
              past ~80% util
LOSS          mtr BOTH directions; mid-path loss vanishing at dest = ICMP
              artifact; persisting to last hop = real. host first:
              ethtool -S / nstat / conntrack. Mathis: tput~MSS/(RTT√p)
TIMEOUT       silence(DROP) vs refused(RST) vs connect-then-hang(app/NAT/
              MTU). tcpdump on server: SYNs arrive? SYN-ACK returns?
              ListenOverflows = accept-queue. Deploy drains ordering.
DNS           dig -> dig @public -> dig @authoritative -> dig +trace
              NXDOMAIN vs SERVFAIL vs timeout = different escalations
              5s stalls = resolver timeout; new-conns-only = pools coasting
SLOW API      scope (which/who/tail/when) -> ONE trace names the span
              anchors: redis .5ms, indexed 1-5ms, scan 100ms+, xregion 50-150ms
              time between spans = queues/pools (client-side metrics!)
BOTTLENECK    ceilings: link bps | window/RTT | Mathis | pps(core) | app
              send-q full=network-bound, empty=app-bound. per-flow ECMP!
TLS           s_client verify codes: 10 expired / 20 chain / handshake_
              failure=cipher-version | browser-ok-code-fails=chain/store
              hang not fail = MTU. monitor SERVED chain externally.
CDN MISS      status decode: BYPASS(config) DYNAMIC(headers) MISS(key/evict)
              EXPIRED(ttl). miss-shape sampling: utm params, Set-Cookie,
              Vary. protect origin FIRST (TTL up, serve-stale, coalesce)
RETRY STORM   amplification = attempts^layers; metastable: heal != recover,
              must SHED. defenses: full jitter, budget<=20%, breakers,
              ONE retry layer, deadlines shrink inward, idempotency keys
```

# MODULE 10 — Top Interview Questions
1. "p99 doubled overnight, p50 flat" — run the method out loud end-to-end.
2. "Prove the loss is real and not yours" — mtr literacy + host counters.
3. The connect-timeout decision tree with the exact commands at each branch.
4. "It's always DNS" — the four-dig triage ladder and the 5s-stall signature.
5. One slow trace: read it, name the anti-patterns, fix them.
6. "Single flow won't exceed X Mbps" — enumerate and test the five ceilings.
7. Cert outage taxonomy: expired vs chain vs trust-store vs SNI vs MTU-hang.
8. Hit ratio cliff: status decoding + miss-shape forensics + origin armor.
9. Reconstruct a retry-storm postmortem; then design the org-wide policy that makes it impossible.
10. "What observability do you build BEFORE the incident?" (The meta-question — RED+USE+traces+drop counters+retry share+served-TLS probes.)

# MODULE 10 — Common Mistakes
- Guess-then-restart (destroys evidence); averages instead of percentiles.
- One vantage point; one direction; ICMP-only tests; no what-changed question.
- Blaming the network before checking your own host's counters.
- Timeout configs from defaults; retries at every layer with no jitter/budget.
- Fixing hit ratio by force-caching uncacheable (cross-user leaks).
- Declaring victory when the trigger heals while the system stays metastable.

# MODULE 10 — Mock Interview (20 min, incident-style)
**Scenario:** "It's Black Friday, 10:04. Checkout error rate 8% and climbing. Latency p99 4s (normal 300ms). CPU on checkout service 45%. DB looks fine per DBA. Traffic is 2.1× last year's peak. Go."

*Strong answer arc:*
1. **Stabilize first**: is it getting worse? Enable/verify load shedding + retry budgets at the edge before diagnosis (protect the fleet); confirm rollback candidates (any 10:00 deploys? — change correlation first).
2. **Scope**: errors = which type (timeouts vs 5xx vs refused)? which endpoints/regions/clients? p99 4s with CPU 45% = queueing somewhere that isn't CPU: connection pools, threadpools, downstream.
3. **Measure**: traces on slow checkouts → span gap between service and payment-provider calls; `ss -tnpi` on checkout pods → send-q/pool wait; discover: payment provider p99 2.5s (their brownout) + our timeout 3s × 3 retries = thread exhaustion → queueing → the 8%.
4. **Mitigate**: cut payment timeout to fit budget (800ms) + fallback (queue order, async confirm), single retry with jitter, breaker on provider, shed non-checkout traffic if needed; watch retry-share and queue depth drain.
5. **Verify + prevent**: error rate recovery curve; postmortem items: deadline budgets per dependency, provider SLA + multi-provider failover, chaos test for dependency brownouts, "retry share" standing alert.
*The examiner is grading: stabilize-before-diagnose, queueing-not-CPU insight, dependency-timeout arithmetic, and the metastability awareness throughout.*

---

# COURSE WRAP — The Meta-Cheat-Sheet (all 10 modules in one breath)

```
M1  layers = fault localization | MTU/MSS math | PMTUD blackholes
M2  handshake/close state machines | min(cwnd,rwnd)/RTT | RTO=200ms tail
    killer | TIME_WAIT port math | keepalive vs middlebox timeouts
M3  UDP = you own reliability | sliding window+SACK+FEC toolbox | NAT/
    amplification realities | when latency beats completeness
M4  HoL story: 1.1(app) -> h2(TCP) -> h3(none) | RTT budget: TCP+TLS+slow
    start | SNI/ALPN | 0-RTT=idempotent-only
M5  recursive vs authoritative | TTL decay (never a switch) | negative
    caching | DNS-steering vs anycast | k8s ndots/conntrack traps
M6  L4(conns) vs L7(requests) | gRPC-through-NLB trap | health checks
    that can't mass-eject | failover ladder + capacity headroom
M7  edge/shield/coalescing | invalidation: version > TTL+SWR > tag purge
    | header contract (no-cache!=no-store, s-maxage) | browsers unpurgeable
M8  poll -> long-poll -> SSE -> WS -> gRPC decision matrix | heartbeats/
    jitter/resume/drain for anything long-lived | deadlines propagate
M9  TLS1.3 1-RTT + PFS | chain validation | JWT: stateless => revocation
    via short TTL+refresh | PKCE flow | CORS protects users | SameSite+
    tokens for CSRF | output encoding+CSP for XSS | XSS > CSRF
M10 method: scope -> localize -> measure -> fix -> prevent | curl -w |
    mtr both ways | dig ladder | trace-first | five ceilings | retry
    budgets + jitter + shedding vs metastability
```

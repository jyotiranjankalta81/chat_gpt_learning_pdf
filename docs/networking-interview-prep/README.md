# Computer Networking for Senior SWE Interviews

Interview-focused networking course for backend engineers with 5+ years of
experience, covering only what is repeatedly asked in Software Engineer,
Backend, Distributed Systems, and System Design interviews at Google, Meta,
Amazon, Microsoft, Uber, Netflix, Cloudflare, Stripe, LinkedIn, and Cisco.

## Contents

| Module | Topic | PDF |
|---|---|---|
| 1 | Networking Basics (OSI, TCP/IP, encapsulation, MTU/MSS) | `../Networking-01-Networking-Basics.pdf` |
| 2 | TCP (handshake, congestion, retransmission, TIME_WAIT...) | `../Networking-02-TCP.pdf` |
| 3 | UDP (when it wins, reliability over UDP, production uses) | `../Networking-03-UDP.pdf` |
| 4 | HTTP/1.1, HTTP/2, HTTP/3, HTTPS, QUIC | `../Networking-04-HTTP-1-1-2-3-HTTPS-QUIC.pdf` |
| 5 | DNS (resolution, resolvers, caching, TTL, CDN steering) | `../Networking-05-DNS.pdf` |
| 6 | Load Balancing (L4/L7, proxies, gateways, health, failover) | `../Networking-06-Load-Balancing.pdf` |
| 7 | CDN (architecture, edge, invalidation, headers, geo) | `../Networking-07-CDN.pdf` |
| 8 | WebSockets, SSE, Polling, gRPC, HTTP streaming | `../Networking-08-WebSockets-SSE-Polling-gRPC.pdf` |
| 9 | Security (TLS, PKI, JWT, OAuth 2.0, CORS, CSRF, XSS) | `../Networking-09-Security-TLS-PKI-JWT-OAuth-CORS-CSRF-XSS.pdf` |
| 10 | Production Debugging (9 real incident scenarios) | `../Networking-10-Production-Debugging.pdf` |

Cumulative **Master PDF** with all modules: `../Networking_Interview_Master.pdf`

## Structure of every topic

1. Why Interviewers Ask This · 2. Core Concept · 3. Internal Working ·
4. Packet Flow Explanation · 5. ASCII Diagram · 6. Real Production Example ·
7. Advantages · 8. Trade-offs · 9. Common Mistakes · 10. Performance Impact ·
11. Common Interview Questions · 12. Follow-up Questions ·
13. Debugging Scenarios · 14. Best Practices · 15. Practice Questions

Every module ends with a one-page cheat sheet, top interview questions,
common mistakes, and a mock interview.

## Rebuilding the PDFs

```bash
pip install weasyprint markdown pygments
python3 build_pdfs.py
```

Markdown sources live in `src/`; PDFs are written to `docs/`.

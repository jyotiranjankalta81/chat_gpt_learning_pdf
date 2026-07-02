# Module 9 — Security

Interviews don't expect a security specialist, but they expect the security
*section* of every design: how users authenticate, how services authorize, where
tokens live, how abuse is limited, and where secrets and encryption fit. Miss it
and you lose easy points; nail it in 3–4 minutes and you look senior.

---

## 9.1 Authentication vs Authorization

### Core Concept

- **Authentication (authn)**: who are you? (credentials → identity)
- **Authorization (authz)**: what may you do? (identity + policy → allow/deny)

Say them separately, always. Authn happens once at the edge (gateway/identity
provider); authz happens on **every request, at the service that owns the
resource** — the gateway can pre-check coarse scopes, but object-level checks
("is this *your* order?") belong to the owning service. The most common real-world
vulnerability class is **broken object-level authorization** (IDOR — changing
`/orders/123` to `/orders/124`), not exotic crypto.

Authz models to name: **RBAC** (roles → permissions; simple, coarse), **ABAC**
(attributes/policies: "owner OR same-team AND business-hours"), **ReBAC**
(relationship graphs — Google Zanzibar powers Drive/YouTube sharing; check
`user —viewer→ doc` edges at massive scale).

Password storage (one-liner expected): salted adaptive hashes — bcrypt/scrypt/
Argon2, never MD5/SHA-fast; plus MFA and breached-password checks.

### Interview Questions

1. Where do authn and authz each happen in a microservice architecture?
2. RBAC vs ABAC vs Zanzibar-style — pick for a Google-Docs-like sharing model.

---

## 9.2 Session Management vs JWT (Stateful vs Stateless Auth)

### Why Interviewers Ask This

"Where does login state live" is asked in nearly every design with users, and the
JWT-vs-session trade-off is a precision test: most candidates know JWT, few can
articulate revocation.

### Core Concept & Internal Working

**Server-side sessions**: login → random session ID in an HttpOnly, Secure,
SameSite cookie → session data in Redis (`session:{id}` with TTL). Every request
does a Redis lookup. **Instant revocation** (delete the key), easy "log out
everywhere", data can change server-side. Cost: a shared session store every
request touches (scale it, replicate it).

**JWT (JSON Web Token)**: signed, self-contained claims.

```
 header.payload.signature   (base64url each)
 { "alg":"RS256" } . { "sub":"u123", "roles":["seller"],
                       "iat":1719900000, "exp":1719903600, "iss","aud" } . SIG

 Verification = check signature (public key) + exp/iss/aud — NO datastore call.
 ⇒ any service validates locally; perfect for microservices & API gateways.
 ⚠ Signed, NOT encrypted — anyone can read the payload (don't put secrets in it).
```

**The revocation problem** (the senior discriminator): a JWT is valid until `exp`
no matter what — logout, password change, or ban can't recall it. Standard
resolution: **short-lived access token (5–15 min) + long-lived refresh token stored
server-side**. Revocation = kill the refresh token; exposure window = access-token
TTL. Refresh tokens should be **rotated on every use** with reuse detection
(a replayed old refresh token ⇒ theft ⇒ revoke the whole family). For
higher-stakes needs, add a denylist of revoked JWT IDs (`jti`) in Redis — at which
point you've partially rebuilt sessions, which is exactly the trade-off to
articulate.

Key hygiene: RS256/EdDSA (asymmetric) so services verify with a public key (via
JWKS endpoint) and only the identity provider signs; rotate keys with `kid`
headers; never accept `alg:none`; validate audience.

### Real Production Example

Big platforms hybridize: an edge session/gateway exchange (cookie → short internal
JWT) so browsers get revocable sessions while internal services get stateless
verification. Auth0/Okta/Cognito all implement access+refresh rotation exactly as
above.

### Common Mistakes

- JWTs in `localStorage` (XSS-stealable) — prefer HttpOnly cookies (with CSRF protection) for browsers.
- 24-hour access tokens "for convenience" — that's your breach window.
- "JWT is encrypted" (it isn't); skipping `aud`/`iss` checks (token from service A replayed at service B).

### Interview Questions

1. Sessions vs JWT for: a bank web app, a public API, service-to-service calls.
2. User's token is stolen — walk through containment with your design.
3. Design "log out of all devices" for both models.

---

## 9.3 OAuth 2.0 & OpenID Connect

### Why Interviewers Ask This

"Login with Google" and third-party API access are ubiquitous, and OAuth is the
most commonly *mis*-explained protocol in interviews. Getting the roles and the
authorization-code flow right is a strong signal.

### Core Concept

**OAuth 2.0 is delegated *authorization***: a user (resource owner) grants a
third-party app (client) limited access (scopes) to their resources at an API
(resource server), issued by an authorization server — *without sharing their
password*. **OIDC is a thin identity layer on top** that adds an **ID token**
(a JWT about *who the user is*) and a userinfo endpoint — OIDC is what "Login with
Google" actually is. Access token = for calling APIs; ID token = for knowing the
user. Confusing these is the classic mistake.

### Internal Working — Authorization Code flow + PKCE (the one to know)

```
 1. app → browser redirect → auth server /authorize?client_id&scope&redirect_uri
                                        &state=xyz&code_challenge=H(v)   (PKCE)
 2. user authenticates & consents at the auth server (password never seen by app)
 3. auth server → redirect back → app?code=AUTH_CODE&state=xyz
 4. app backend → POST /token {code, client_secret, code_verifier=v}
 5. ← { access_token, refresh_token, id_token(OIDC) }
 6. app → API with Authorization: Bearer access_token; API validates + checks scopes
```

Why the code indirection: tokens never transit the browser URL (history, logs,
referrers); the code is single-use, short-lived, and only exchangeable by the
authenticated client. **PKCE** (proof key) binds steps 1 and 4 so an intercepted
code is useless — mandatory for mobile/SPA (no client secret), recommended for all.
`state` blocks CSRF; exact `redirect_uri` allowlisting blocks token redirection.
Deprecated/avoid: implicit flow (tokens in URL fragment), password grant. Machine-
to-machine: **client credentials** flow (no user). Scopes are coarse permissions
(`repo:read`) — the resource server still does fine-grained authz.

### Real Production Example

"Sign in with Google/GitHub/Apple" (OIDC), every third-party integration
(Slack apps, GitHub Apps), and internal SSO (Okta) — one identity provider,
authorization-code flow everywhere, tokens scoped per audience.

### Interview Questions

1. Explain the authorization-code flow and *why* the code exists at all.
2. OAuth vs OIDC — which token proves identity, which grants API access?
3. Why is PKCE mandatory for mobile apps?

---

## 9.4 API Keys & Service-to-Service Auth

### Core Concept

- **API keys**: long-lived opaque strings identifying a *calling application* (not a user). Right for server-to-server B2B APIs (Stripe: `sk_live_...`). Handling: show once at creation, store **hashed** (they're credentials), prefix for identification (`sk_live_` — enables secret scanning), scope + per-key rate limits, easy rotation with overlapping validity, and instant revocation. Weakness: bearer credential — anyone holding it is you; no user context, no expiry unless you add it.
- Stronger service-to-service options to name: **mTLS** (both sides present certs — the service mesh does this transparently; identity = certificate), **signed requests** (AWS SigV4: request signed with a secret, replay-resistant, key never on the wire), and short-lived platform identities (cloud IAM roles, SPIFFE/SVID) instead of static keys.
- Zero-trust framing: don't trust the network ("we're inside the VPC" is not authn); every hop authenticates and authorizes.

### Interview Questions

1. Design the API-key system for a public developer API (issue, store, rotate, revoke, rate-limit).
2. API key vs OAuth client-credentials vs mTLS — when each?

---

## 9.5 Rate Limiting

### Why Interviewers Ask This

It's both a security control (brute force, scraping, abuse) and a reliability
control (protect capacity, fairness) — and "design a rate limiter" is a full
interview question (Module 13.24). Expect algorithm + distributed-state discussion.

### Core Concept & Internal Working

Algorithms, with the trade-offs interviewers want:

- **Fixed window**: counter per `key:window` (`user:123:12:05` → INCR, EXPIRE). Cheap; boundary burst flaw (100 at 12:04:59 + 100 at 12:05:01 = 200 in 2 s).
- **Sliding window log**: timestamps in a sorted set; exact but O(rate) memory.
- **Sliding window counter**: weighted blend of current+previous window — near-exact, cheap; the pragmatic default (Cloudflare uses this).
- **Token bucket**: capacity B, refill r/sec; a request takes a token. Allows *bursts up to B* while enforcing average r — usually the right semantics for APIs (AWS/Stripe model). Two numbers to state: rate and burst.
- **Leaky bucket**: queue drained at constant rate — smooths output (traffic shaping), adds queueing delay.

Distributed enforcement: counters in **Redis** (atomic Lua: INCR+check+EXPIRE) —
adds ~1 ms/request and makes Redis a critical dependency (decide **fail-open**
(availability) vs **fail-closed** (protection) — say the choice). Common
production compromise: **local token buckets per gateway node with async sync** —
approximate global limit (N nodes × local slice), zero added latency; or
Envoy/gateway-integrated global rate limit service.

Design details that score points: return **429 + Retry-After** and
`X-RateLimit-Remaining` headers; layer limits (per-IP at edge for DDoS, per-user,
per-API-key, per-endpoint cost-weighted, global per-service concurrency); shadow
mode before enforcement; separate the *decision* (policy) from the *counting*
(infra).

```
 request → gateway → Lua @ Redis: tokens = min(B, tokens + r·Δt); tokens ≥ 1 ?
            allow (tokens-1) ──► service          deny ──► 429 + Retry-After
```

### Real Production Example

Stripe's published rate limiter suite: request-rate limiter (token bucket) +
concurrency limiter + fleet-usage load shedders, all in Redis with fail-open.
GitHub/Cloudflare document sliding-window counters at the edge.

### Interview Questions

1. Token bucket vs sliding window — semantics and when each fits.
2. Make the limit *global* across 50 gateway nodes — options and their accuracy/latency trade-offs.
3. Redis is down — does your limiter fail open or closed, and why?

---

## 9.6 Encryption & TLS

### Core Concept

Three states of data, three answers:

- **In transit — TLS everywhere** (external *and* internal: mTLS via mesh). TLS 1.3: asymmetric crypto (certificates, key exchange with forward secrecy) bootstraps a symmetric session key (AES-GCM/ChaCha20) — asymmetric authenticates, symmetric encrypts bulk (fast). Certificates chain to CAs; automate issuance/renewal (ACME/Let's Encrypt) — expired certs are a top self-inflicted outage.
- **At rest — envelope encryption**: each object/record encrypted with a **DEK** (data encryption key); DEKs encrypted by a **KEK** living in a **KMS/HSM**; ciphertext DEK stored alongside data. Rotation = re-encrypt small DEKs, not petabytes; access control + audit at the KMS; "crypto-shredding" (destroy key = destroy data) for deletion/GDPR.
- **In use / application-layer**: field-level encryption for the crown jewels (PANs, SSNs) so even DB admins/dumps can't read them; tokenization for card data (swap PAN for a token; only the vault maps back — shrinks PCI scope massively).

Non-negotiables: never roll your own crypto; hash passwords (Argon2/bcrypt),
encrypt data — different tools; TLS termination point is a *decision* (edge for
performance + re-encrypt internally, or end-to-end for zero-trust).

### Interview Questions

1. Explain envelope encryption and why KMS doesn't encrypt your data directly. (throughput + blast radius + rotation economics)
2. Where does TLS terminate in your design and what runs in cleartext afterwards?
3. How does tokenization reduce PCI scope?

---

## 9.7 Secrets Management

### Core Concept

Secrets (DB passwords, API keys, signing keys) must be: **out of code/images/env
files** (the #1 breach vector is a leaked repo/laptop), centrally stored
(Vault/AWS Secrets Manager/GCP Secret Manager), **access-controlled per workload
identity** (the pod's platform identity — IAM role/K8s service account — fetches
only its own secrets; solves "secret zero"), **audited**, **rotated** (best:
short-lived *dynamic* credentials — Vault mints per-service DB users with TTLs, so
leaks expire by themselves), and **revocable in an emergency** (documented
break-glass + rotation runbook; assume any long-lived static secret is eventually
leaked). Delivery: injected at deploy/runtime (sidecar/CSI/env-at-start), cached
with TTL, never logged (log scrubbing — secrets in logs is a routine incident).

### Interview Questions

1. How does a fresh pod get its DB password with no secret baked anywhere? (platform identity → KMS/Vault auth → scoped secret; "secret zero" via the platform)
2. A contractor's laptop leaked `.env` — walk the response and the design that makes it a non-event (short-lived dynamic creds).

---

## Module 9 Cheat Sheet

```
AUTHN/AUTHZ  who vs what-may. Authn at edge/IdP once; authz per request at owning
             service (object-level! IDOR). RBAC→ABAC→ReBAC(Zanzibar).
SESSIONS     random ID in HttpOnly+Secure+SameSite cookie → Redis; instant revoke;
             store is a scaled dependency.
JWT          header.claims.signature; local verify (JWKS, RS256, kid, aud/iss, exp);
             readable not encrypted; REVOCATION: short access (5–15m) + rotated
             refresh (server-side, reuse detection); jti denylist if needed.
OAUTH2/OIDC  delegated authorization; OIDC adds ID token (identity). Auth-code flow
             + PKCE + state + exact redirect URIs. access≠id token. client-creds
             for M2M. No implicit/password grants.
API KEYS     app identity; hash at rest, prefix, scope, rotate, revoke. Stronger:
             mTLS (mesh), SigV4-style signing, short-lived platform identities.
             Zero trust: VPC ≠ authn.
RATE LIMIT   fixed window(burst flaw) < sliding counter(default) < token bucket
             (rate+burst, API standard) / leaky (shaping). Redis+Lua global vs
             local-approximate. 429+Retry-After. Layered: IP/user/key/endpoint.
             Declare fail-open vs fail-closed.
ENCRYPTION   transit: TLS1.3+mTLS, ACME automation. rest: envelope (DEK+KMS KEK),
             rotation, crypto-shred. fields: tokenize PANs (PCI scope).
             Argon2/bcrypt for passwords.
SECRETS      central vault, workload identity, dynamic short-lived creds, audit,
             rotation runbook, never in code/logs.
```

## Top Interview Questions (Module 9)

1. Sessions vs JWT + revocation design. 2. Auth-code+PKCE flow and why the code
exists. 3. Stolen-token containment. 4. Global rate limiter across 50 nodes.
5. Token bucket vs sliding window. 6. Envelope encryption + KMS rationale.
7. Service-to-service auth options (mTLS/signing/IAM). 8. Secret zero problem.
9. Zanzibar-style sharing authz. 10. Where TLS terminates and why.

## Common Mistakes Recap

JWT with no revocation story • tokens in localStorage • "JWT is encrypted" •
skipping aud/iss • implicit flow • plaintext/`.env` secrets • API keys stored
unhashed • rate limiter with no fail-open/closed decision • authz only at the
gateway (IDOR) • trusting the internal network • manual cert renewal.

## Mock Interview Exercise

*"Add the full security story to a marketplace API: browser + mobile apps,
third-party developer API, internal microservices, card payments."* Expected:
OIDC login (auth-code+PKCE) → edge session cookie → short internal JWTs; refresh
rotation + logout-everywhere; developer API keys (hashed, scoped, per-key token-
bucket limits) or client-credentials OAuth; mesh mTLS internally; object-level
authz in owning services; tokenized cards via PSP (PCI scope), envelope encryption
at rest; Vault + workload identity + dynamic DB creds; layered rate limits +
fail-open call; audit logging.

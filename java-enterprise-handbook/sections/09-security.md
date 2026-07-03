# Section 9: Security

> **Banking-Grade Security:** At HSBC, Goldman Sachs, and JP Morgan, security is not a checkbox — it's an engineering discipline. You're expected to know OAuth2 flows, JWT vulnerabilities, OWASP Top 10 mitigations, and how to implement them correctly in Spring Security.

---

## 9.1 OAuth2 & OpenID Connect — Deep Dive

### OAuth2 Flows — When to Use Each

```
Authorization Code Flow (+ PKCE):
  → Use for: Web apps, mobile apps (user-facing)
  → Browser redirects to auth server → code → exchange for token
  → Never exposes tokens in URL

Client Credentials Flow:
  → Use for: Service-to-service (M2M) communication
  → No user involved → service gets token directly
  → How payment-service calls account-service in enterprise

Implicit Flow:
  → DEPRECATED — never use (tokens in URL, no PKCS)

Resource Owner Password:
  → DEPRECATED — never use (service gets user credentials directly)

Device Code Flow:
  → Use for: CLI tools, IoT devices
```

### Spring Security OAuth2 Resource Server

```java
// Resource Server — validates JWT tokens from auth server
@Configuration
@EnableWebSecurity
public class ResourceServerConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt
                    .decoder(jwtDecoder())
                    .jwtAuthenticationConverter(jwtAuthConverter()))
                .authenticationEntryPoint(customEntryPoint()))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health/**").permitAll()
                .requestMatchers(HttpMethod.GET, "/api/v1/payments/**")
                    .hasAuthority("SCOPE_payments:read")
                .requestMatchers(HttpMethod.POST, "/api/v1/payments")
                    .hasAuthority("SCOPE_payments:write")
                .requestMatchers("/api/v1/admin/**")
                    .hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .build();
    }

    @Bean
    public JwtDecoder jwtDecoder() {
        // Verify JWT signature using auth server's public key (JWKS endpoint)
        return NimbusJwtDecoder.withJwkSetUri("https://auth.bank.com/.well-known/jwks.json")
            .jwsAlgorithm(SignatureAlgorithm.RS256)
            .build();
    }

    @Bean
    public JwtAuthenticationConverter jwtAuthConverter() {
        JwtGrantedAuthoritiesConverter scopeConverter = new JwtGrantedAuthoritiesConverter();
        scopeConverter.setAuthorityPrefix("SCOPE_");
        scopeConverter.setAuthoritiesClaimName("scp");  // Custom claim name

        JwtAuthenticationConverter converter = new JwtAuthenticationConverter();
        converter.setJwtGrantedAuthoritiesConverter(jwt -> {
            Collection<GrantedAuthority> scopes = scopeConverter.convert(jwt);
            // Add roles from custom claim
            List<GrantedAuthority> roles = jwt.getClaimAsStringList("roles").stream()
                .map(role -> new SimpleGrantedAuthority("ROLE_" + role))
                .collect(Collectors.toList());
            return Stream.concat(scopes.stream(), roles.stream()).toList();
        });
        converter.setPrincipalClaimName("sub");
        return converter;
    }
}
```

### Client Credentials (Service-to-Service)

```java
// OAuth2 client config for calling protected microservices
@Configuration
public class OAuth2ClientConfig {

    @Bean
    public WebClient accountServiceClient(
            ReactiveClientRegistrationRepository clientRegistrations,
            ServerOAuth2AuthorizedClientRepository authorizedClients) {

        ServerOAuth2AuthorizedClientExchangeFilterFunction oauth =
            new ServerOAuth2AuthorizedClientExchangeFilterFunction(
                clientRegistrations, authorizedClients);
        oauth.setDefaultClientRegistrationId("account-service");

        return WebClient.builder()
            .baseUrl("https://account-service.internal")
            .filter(oauth)  // Automatically adds Bearer token
            .build();
    }
}

# application.yml
spring:
  security:
    oauth2:
      client:
        registration:
          account-service:
            provider: internal-auth
            client-id: payment-service
            client-secret: ${OAUTH2_CLIENT_SECRET}
            authorization-grant-type: client_credentials
            scope: accounts:read
        provider:
          internal-auth:
            token-uri: https://auth.bank.com/oauth2/token
```

---

## 9.2 JWT — Security Deep Dive

### JWT Structure

```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.   ← Header: algorithm, type
eyJzdWIiOiJ1c2VyLTEyMyIsInJvbGVzIjpbIlVTRVIiXSwic2NwIjpbInBheW1lbnRzOnJlYWQiXSwiZXhwIjoxNzA5MTM5MjAwLCJpYXQiOjE3MDkxMzU2MDAsImp0aSI6ImFiYy0xMjMifQ==.  ← Payload: claims
RSASHA256signature  ← Signature: verifies integrity

Payload decoded:
{
  "sub": "user-123",           // Subject (user ID)
  "roles": ["USER"],           // Custom roles
  "scp": ["payments:read"],    // Scopes
  "exp": 1709139200,           // Expiration
  "iat": 1709135600,           // Issued at
  "jti": "abc-123",            // JWT ID (for revocation)
  "iss": "https://auth.bank.com", // Issuer
  "aud": "payment-service"     // Audience
}
```

### JWT Security Best Practices

```java
// JWT validation — ALL these checks MUST happen
@Component
public class JwtValidator {

    public Claims validateAndExtract(String token) {
        try {
            return Jwts.parserBuilder()
                .setSigningKey(publicKey)          // Verify signature
                .requireIssuer("https://auth.bank.com")  // Verify issuer
                .requireAudience("payment-service")       // Verify intended audience
                .setAllowedClockSkewSeconds(30)          // Allow 30s clock drift
                .build()
                .parseClaimsJws(token)
                .getBody();
        } catch (ExpiredJwtException e) {
            throw new UnauthorizedException("Token expired");
        } catch (JwtException e) {
            // Don't reveal WHY validation failed — security
            log.warn("JWT validation failed: {}", e.getClass().getSimpleName());
            throw new UnauthorizedException("Invalid token");
        }
    }
}

// Common JWT vulnerabilities to prevent:

// 1. alg:none attack — NEVER accept "none" algorithm
// Spring's NimbusJwtDecoder with RS256 prevents this automatically

// 2. Algorithm confusion (RS256 → HS256) — use separate public/private key configs
// Always explicitly specify allowed algorithm

// 3. Token not expiring — always set exp, typical: 15min access, 7d refresh

// 4. Sensitive data in payload — JWT is base64 encoded, NOT encrypted
// NEVER put: passwords, SSN, PII in JWT payload

// 5. Missing audience check — prevents tokens for service A being used at service B

// Token revocation (stateless JWT cannot be revoked — workarounds):
// Option 1: Short expiry (15 min) + refresh token rotation
// Option 2: Token blacklist in Redis (compromise: stateful)
// Option 3: JTI (JWT ID) tracking — check Redis on each request
```

---

## 9.3 OWASP Top 10 — Java Mitigations

### A1: Injection (SQL, LDAP, OS Command)

```java
// SQL Injection — NEVER use string concatenation
// WRONG:
String sql = "SELECT * FROM users WHERE name = '" + userInput + "'";
// If userInput = "'; DROP TABLE users; --" → catastrophic

// CORRECT: Parameterized queries
@Query("SELECT u FROM User u WHERE u.name = :name")
Optional<User> findByName(@Param("name") String name);

// JdbcTemplate parameterized
jdbcTemplate.query(
    "SELECT * FROM users WHERE email = ?",
    new Object[]{email},  // Properly escaped by driver
    rowMapper
);

// NEVER construct JPQL/HQL dynamically with user input
// Use Specification API (JPA Criteria) for dynamic queries:
public Specification<Payment> withFilters(PaymentFilter filter) {
    return (root, query, cb) -> {
        List<Predicate> predicates = new ArrayList<>();
        if (filter.getStatus() != null) {
            predicates.add(cb.equal(root.get("status"), filter.getStatus()));
        }
        if (filter.getFromDate() != null) {
            predicates.add(cb.greaterThanOrEqualTo(root.get("createdAt"), filter.getFromDate()));
        }
        return cb.and(predicates.toArray(new Predicate[0]));
    };
}
```

### A2: Broken Authentication

```java
// Secure password storage
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder(12);  // Cost 12 → ~300ms per hash (brute-force resistant)
}

// Account lockout after failed attempts
@Service
public class AuthenticationService {
    private final LoadingCache<String, AtomicInteger> loginAttempts =
        CacheBuilder.newBuilder()
            .expireAfterWrite(15, TimeUnit.MINUTES)
            .build(CacheLoader.from(k -> new AtomicInteger(0)));

    public LoginResult login(String email, String password) {
        int attempts = loginAttempts.getUnchecked(email).get();
        if (attempts >= 5) {
            throw new AccountLockedException("Account locked. Try again in 15 minutes.");
        }

        User user = userRepo.findByEmail(email)
            .orElseThrow(() -> {
                loginAttempts.getUnchecked(email).incrementAndGet();
                return new BadCredentialsException("Invalid credentials");
            });

        if (!passwordEncoder.matches(password, user.getPasswordHash())) {
            loginAttempts.getUnchecked(email).incrementAndGet();
            throw new BadCredentialsException("Invalid credentials");
        }

        loginAttempts.invalidate(email);  // Reset on success
        return generateTokens(user);
    }
}
```

### A3: Sensitive Data Exposure

```java
// Mask sensitive data in logs
@Slf4j
public class PaymentService {
    public void processCard(CardPaymentRequest request) {
        log.info("Processing card payment: last4={} amount={}",
            request.getCardNumber().substring(request.getCardNumber().length() - 4),
            request.getAmount());
        // NEVER: log.info("Card: {}", request.getCardNumber());
    }
}

// Sensitive field masking in Jackson (JSON responses)
public class CardDetails {
    @JsonProperty
    private String cardholderName;

    @JsonSerialize(using = MaskedCardSerializer.class)
    private String cardNumber;  // Serializes as "****-****-****-1234"

    @JsonIgnore
    private String cvv;  // Never include in any response
}

// HTTPS enforcement
http.requiresChannel()
    .requestMatchers(r -> r.getHeader("X-Forwarded-Proto") != null)
    .requiresSecure();

// HSTS header
http.headers(headers -> headers
    .httpStrictTransportSecurity(hsts -> hsts
        .includeSubDomains(true)
        .maxAgeInSeconds(31536000)));
```

### A4: XML External Entity (XXE)

```java
// Safe XML parsing — disable external entities
DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
factory.setExpandEntityReferences(false);
DocumentBuilder builder = factory.newDocumentBuilder();
// Now safe to parse untrusted XML
```

### A5: Broken Access Control

```java
// ALWAYS verify ownership — never trust client-provided IDs
@Service
public class AccountService {

    @PreAuthorize("@accountSecurity.isOwnerOrAdmin(#accountId, authentication)")
    public Account getAccount(String accountId) { ... }

    // Custom security expression
    @Component("accountSecurity")
    public class AccountSecurityExpressions {
        public boolean isOwnerOrAdmin(String accountId, Authentication auth) {
            if (auth.getAuthorities().stream()
                    .anyMatch(a -> a.getAuthority().equals("ROLE_ADMIN"))) {
                return true;
            }
            Account account = accountRepo.findById(accountId).orElse(null);
            return account != null && account.getOwnerId().equals(auth.getName());
        }
    }
}
```

---

## 9.4 Secrets Management

```java
// Spring Vault integration
@Configuration
public class VaultConfig extends AbstractVaultConfiguration {

    @Override
    public VaultEndpoint vaultEndpoint() {
        return VaultEndpoint.from(URI.create("https://vault.internal.bank.com"));
    }

    @Override
    public ClientAuthentication clientAuthentication() {
        // Kubernetes auth — uses service account token
        return new KubernetesAuthentication(
            KubernetesAuthenticationOptions.builder()
                .role("payment-service")
                .build(),
            restOperations());
    }
}

# application.yml — Vault secrets injected as Spring properties
spring:
  cloud:
    vault:
      enabled: true
      uri: https://vault.internal.bank.com
      authentication: kubernetes
      kubernetes:
        role: payment-service
      kv:
        enabled: true
        backend: secret
        default-context: payment-service
        application-name: payment-service
# Secrets at vault path: secret/payment-service/
# Accessible as: ${database.password}, ${jwt.secret}
```

---

## 9.5 Secure Coding Checklist

```java
// Input validation — always at API boundary
@Valid @RequestBody CreatePaymentRequest request

// Output encoding — prevent XSS
// Jackson's default JSON encoding prevents XSS in JSON APIs
// For HTML output: use Thymeleaf (auto-escapes) or explicitly encode

// Error messages — don't reveal internals
@ExceptionHandler(Exception.class)
public ResponseEntity<ErrorResponse> handleGeneral(Exception e) {
    log.error("Unhandled exception", e);  // Log full stack trace internally
    return ResponseEntity.status(500)
        .body(new ErrorResponse("INTERNAL_ERROR", "An error occurred"));
    // NEVER return e.getMessage() for unexpected exceptions
}

// Rate limiting on sensitive endpoints
@RateLimiter(name = "login-endpoint")
@PostMapping("/auth/login")
public ResponseEntity<TokenResponse> login(@RequestBody LoginRequest request) { ... }

// CSRF protection — enable for non-stateless APIs
// (stateless JWT APIs can disable CSRF since there's no session cookie)

// Dependency scanning
// Run: mvn dependency-check:check
// In CI: fail on CVSS score > 7

// Security headers
http.headers(headers -> headers
    .contentSecurityPolicy(csp -> csp
        .policyDirectives("default-src 'self'; script-src 'self'"))
    .frameOptions(fo -> fo.deny())
    .xssProtection(xss -> xss.block(true)));
```

---

## Section Summary: Security Interview Questions

**Banking/fintech companies always ask:**

1. "How does OAuth2 client credentials flow work? Walk me through service-to-service auth."
2. "What are the JWT vulnerabilities you need to protect against?"
3. "How do you prevent SQL injection in a Spring Data JPA application?"
4. "How do you store sensitive configuration (DB passwords, API keys) in production?"
5. "What is the difference between authentication and authorization?"
6. "How would you implement row-level security? (user can only see their own data)"
7. "What OWASP vulnerabilities have you encountered and mitigated?"
8. "How do you handle token revocation with stateless JWTs?"
9. "What is PKCE and why is it needed for Authorization Code flow?"
10. "How do you audit sensitive operations in a banking system?"

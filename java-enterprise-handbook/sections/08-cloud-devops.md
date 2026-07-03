# Section 8: Cloud & DevOps Integration

> **You Already Know This:** Your AWS, Docker, Kubernetes, Terraform, and Kafka background is a serious advantage. This section focuses specifically on how Java/Spring services integrate with these tools — the patterns and idioms that differ from Node.js deployments.

---

## 8.1 Spring Boot on AWS

### Spring Cloud AWS

```java
// Spring Cloud AWS — native AWS service integration
// Replaces manual SDK usage with Spring-idiomatic code

// application.yml
spring:
  cloud:
    aws:
      region:
        static: eu-west-1
      credentials:
        instance-profile: true  # Use EC2/ECS instance role (IAM role)

// AWS Secrets Manager — replace hardcoded secrets
spring:
  config:
    import: aws-secretsmanager:/myapp/prod/secrets
# Secrets from AWS Secrets Manager available as Spring properties
# database.password=${DB_PASSWORD}  → fetched from secrets manager
```

### SQS Consumer (AWS Queue)

```java
@Component
public class SqsPaymentConsumer {

    @SqsListener("payment-processing-queue")
    public void receivePayment(@Payload PaymentMessage message,
                                @Header("ApproximateReceiveCount") int receiveCount) {
        if (receiveCount > 3) {
            log.error("Message exceeded retry limit, sending to DLQ: {}", message.getId());
            return;  // SQS will send to DLQ after maxReceiveCount
        }

        try {
            paymentService.process(message);
        } catch (RetryableException e) {
            throw e;  // Trigger SQS retry
        }
    }
}

// SQS Producer
@Service
public class SqsProducer {

    private final SqsTemplate sqsTemplate;

    public void sendPayment(PaymentMessage message) {
        sqsTemplate.send(to -> to
            .queue("payment-processing-queue")
            .payload(message)
            .header("paymentType", message.getType())
            .delaySeconds(5));
    }
}
```

### S3 Integration

```java
@Service
public class DocumentStorageService {

    private final S3Client s3Client;

    public String uploadDocument(String key, InputStream content, String contentType) {
        PutObjectRequest request = PutObjectRequest.builder()
            .bucket(bucketName)
            .key(key)
            .contentType(contentType)
            .serverSideEncryption(ServerSideEncryption.AWS_KMS)  // Encrypt at rest
            .build();

        s3Client.putObject(request, RequestBody.fromInputStream(content, contentLength));
        return "s3://" + bucketName + "/" + key;
    }

    // Pre-signed URL — temporary access (no proxy required)
    public String generateDownloadUrl(String key, Duration expiry) {
        S3Presigner presigner = S3Presigner.create();
        GetObjectPresignRequest presignRequest = GetObjectPresignRequest.builder()
            .signatureDuration(expiry)
            .getObjectRequest(r -> r.bucket(bucketName).key(key))
            .build();
        return presigner.presignGetObject(presignRequest).url().toString();
    }
}
```

---

## 8.2 Docker — Java-Specific Patterns

### Production Dockerfile (Multi-stage)

```dockerfile
# Stage 1: Build
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /app
COPY pom.xml .
COPY .mvn/ .mvn/
COPY mvnw .
# Download deps separately — cache this layer
RUN ./mvnw dependency:go-offline -B

COPY src/ src/
RUN ./mvnw package -DskipTests -B

# Unpack JAR for better layer caching (Spring Boot layered JARs)
RUN java -Djarmode=layertools -jar target/*.jar extract

# Stage 2: Runtime — minimal image
FROM eclipse-temurin:21-jre-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app

# Copy Spring Boot layers (changes least frequently → better caching)
COPY --from=builder /app/dependencies/ ./
COPY --from=builder /app/spring-boot-loader/ ./
COPY --from=builder /app/snapshot-dependencies/ ./
COPY --from=builder /app/application/ ./

# Security: run as non-root
USER appuser

EXPOSE 8080

# JVM memory configured via env — not hardcoded
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 \
               -XX:+ExitOnOutOfMemoryError \
               -Djava.security.egd=file:/dev/./urandom"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS org.springframework.boot.loader.JarLauncher"]
```

### Spring Boot Layered JARs

```
Traditional JAR: all-in-one, any code change = large Docker layer invalidated
Layered JAR: separated layers, incremental pushes

spring-boot:repackage with layers:
├── dependencies        (rarely changes — library updates)
├── spring-boot-loader  (almost never changes)
├── snapshot-dependencies (dev dependencies)
└── application         (your code — changes every commit)

Only the application layer (~100KB) needs to be pushed on most builds
vs full JAR (~50MB) without layers
```

---

## 8.3 Kubernetes — Java Service Deployment

### Kubernetes Manifest for Spring Boot

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  labels:
    app: payment-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/path: "/actuator/prometheus"
        prometheus.io/port: "8080"
    spec:
      containers:
        - name: payment-service
          image: myregistry/payment-service:1.2.3
          ports:
            - containerPort: 8080
          env:
            - name: SPRING_PROFILES_ACTIVE
              value: "prod"
            - name: DB_URL
              valueFrom:
                secretKeyRef:
                  name: payment-secrets
                  key: database-url
            - name: JAVA_OPTS
              value: "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0"
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          # Liveness: restart pod if JVM is stuck
          livenessProbe:
            httpGet:
              path: /actuator/health/liveness
              port: 8080
            initialDelaySeconds: 60   # Account for JVM startup
            periodSeconds: 10
            failureThreshold: 3
          # Readiness: route traffic only when app is warm
          readinessProbe:
            httpGet:
              path: /actuator/health/readiness
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 5
            failureThreshold: 3
          # Graceful shutdown
          lifecycle:
            preStop:
              exec:
                command: ["sh", "-c", "sleep 10"]  # Let load balancer deregister first
      terminationGracePeriodSeconds: 60  # Allow in-flight requests to complete
```

### Graceful Shutdown in Spring Boot

```java
// application.yml
server:
  shutdown: graceful  # Wait for in-flight requests to complete

spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s  # Max wait time

// On SIGTERM:
// 1. Spring marks app as "not ready" (readiness probe fails → k8s stops routing)
// 2. Wait 10s (preStop sleep) for load balancer to deregister
// 3. Process in-flight requests (up to 30s)
// 4. Close DB connections, Kafka producers, etc.
// 5. JVM exits
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payment-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payment-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: External
      external:
        metric:
          name: kafka_consumer_lag  # Scale on Kafka consumer lag
        target:
          type: AverageValue
          averageValue: "1000"  # Scale up when lag > 1000 per pod
```

---

## 8.4 CI/CD Pipeline for Java Services

### GitHub Actions — Java/Maven Pipeline

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  JAVA_VERSION: '21'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK ${{ env.JAVA_VERSION }}
        uses: actions/setup-java@v4
        with:
          java-version: ${{ env.JAVA_VERSION }}
          distribution: 'temurin'
          cache: 'maven'

      - name: Run tests with coverage
        run: ./mvnw verify -B --no-transfer-progress
        env:
          SPRING_DATASOURCE_URL: jdbc:postgresql://localhost:5432/testdb

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4

      - name: Run OWASP dependency check
        run: ./mvnw org.owasp:dependency-check-maven:check -B

  build-and-push:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK ${{ env.JAVA_VERSION }}
        uses: actions/setup-java@v4
        with:
          java-version: ${{ env.JAVA_VERSION }}
          distribution: 'temurin'
          cache: 'maven'

      - name: Build with Maven
        run: ./mvnw package -DskipTests -B

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/payment-service \
            payment-service=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            -n staging
          kubectl rollout status deployment/payment-service -n staging --timeout=5m
```

---

## 8.5 Terraform for Java Infrastructure

```hcl
# terraform/modules/java-service/main.tf
# ECS Fargate task for Java microservice

resource "aws_ecs_task_definition" "payment_service" {
  family                   = "payment-service"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024  # 1 vCPU
  memory                   = 2048  # 2GB RAM

  container_definitions = jsonencode([{
    name  = "payment-service"
    image = "${var.ecr_repo}:${var.image_tag}"

    environment = [
      { name = "SPRING_PROFILES_ACTIVE", value = var.environment },
      { name = "JAVA_OPTS", value = "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+ExitOnOutOfMemoryError" }
    ]

    secrets = [
      { name = "DB_PASSWORD", valueFrom = aws_secretsmanager_secret.db_password.arn },
      { name = "JWT_SECRET", valueFrom = aws_secretsmanager_secret.jwt_secret.arn }
    ]

    portMappings = [{ containerPort = 8080 }]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group  = "/ecs/payment-service"
        awslogs-region = var.aws_region
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8080/actuator/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60  # Account for JVM startup
    }
  }])
}
```

---

## 8.6 Helm Chart for Java Microservice

```yaml
# helm/payment-service/values.yaml
replicaCount: 3

image:
  repository: myregistry/payment-service
  tag: "1.2.3"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8080

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 512Mi

jvmOptions: "-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+ExitOnOutOfMemoryError"

springProfile: prod

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 5

# Production: use AWS Secrets Manager / Vault
secrets:
  dbUrl: ""       # Override in values-prod.yaml
  dbPassword: ""
```

---

## 8.7 GraalVM Native Image

```xml
<!-- pom.xml — Spring Boot Native -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-aot</artifactId>
</dependency>

<plugin>
    <groupId>org.graalvm.buildtools</groupId>
    <artifactId>native-maven-plugin</artifactId>
    <version>0.10.3</version>
</plugin>
```

```bash
# Build native image (takes 5-15 minutes)
./mvnw native:compile -Pnative

# Result: native executable, ~50MB, no JVM needed
./target/payment-service

# Startup time: 50-200ms vs 3-8s for JVM
# Memory: 50-80MB vs 200-500MB for JVM

# Tradeoffs:
# + Instant startup (perfect for Lambda/serverless)
# + Much lower memory
# - No JIT optimization (peak throughput slightly lower)
# - Reflection requires explicit configuration (hint files)
# - Longer build time
# - Some libraries not yet native-compatible
```

---

## Section Summary: Cloud/DevOps Key Points

**What companies actually care about:**

1. **Container best practices** — multi-stage builds, non-root user, proper JVM flags for containers
2. **k8s probes** — liveness vs readiness, correct `initialDelaySeconds` for JVM
3. **Graceful shutdown** — why it matters, how to configure
4. **Resource limits** — JVM heap vs container memory, why `MaxRAMPercentage` > hardcoded Xmx
5. **Secret management** — never hardcode, use AWS Secrets Manager, Vault, k8s secrets
6. **HPA scaling** — CPU-based and custom metrics (Kafka lag)
7. **Layered JARs** — why and how for better Docker layer caching

**Your Node.js advantage:** You already understand containers, k8s, and Terraform deeply. The Java-specific knowledge to add: JVM flag tuning for containers, Spring Boot actuator endpoints, and layered JAR builds.

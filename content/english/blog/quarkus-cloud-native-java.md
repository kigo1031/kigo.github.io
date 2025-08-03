---
title: "Getting Started with Cloud Native Java Development using Quarkus"
meta_title: "Quarkus Cloud Native Java"
description: "Introduction to Quarkus, the Kubernetes-era Java framework, and comparison with Spring Boot"
date: 2025-08-03T13:00:00+09:00
image: "/images/service-1.png"
categories: ["Backend"]
tags: ["Java", "Quarkus", "Cloud Native", "Kubernetes", "GraalVM"]
draft: false
---

Recently, there's been a lot of discussion about the limitations of Java applications in cloud-native environments. Particularly, **high memory usage** and **slow startup times** have made Java somewhat disadvantageous in containerized environments. **Quarkus** emerged to solve these exact problems.

## What is Quarkus?

Quarkus is a **Kubernetes Native Java framework** developed by Red Hat. True to its slogan "Supersonic Subatomic Java," it boasts much faster startup times and lower memory usage compared to traditional Java applications.

### Key Features

- **Fast startup time**: Millisecond-level startup times
- **Low memory usage**: 1/10th of traditional usage
- **GraalVM Native Image support**: Native compilation capable
- **Developer-friendly**: Live Coding for immediate reflection

## Spring Boot vs Quarkus

### Memory Usage Comparison

```bash
# Spring Boot Application
Memory: ~200MB

# Quarkus JVM Mode
Memory: ~50MB

# Quarkus Native Mode
Memory: ~20MB
```

### Startup Time Comparison

```bash
# Spring Boot
Started in 3.2 seconds

# Quarkus JVM Mode
Started in 1.1 seconds

# Quarkus Native Mode
Started in 0.016 seconds
```

## Getting Started with Quarkus Project

### 1. Project Creation

```bash
mvn io.quarkus.platform:quarkus-maven-plugin:3.2.4.Final:create \
    -DprojectGroupId=com.kigo.example \
    -DprojectArtifactId=quarkus-demo \
    -DclassName="com.kigo.example.GreetingResource" \
    -Dpath="/hello"
```

### 2. Basic REST API Implementation

```java
@Path("/hello")
public class GreetingResource {

    @GET
    @Produces(MediaType.TEXT_PLAIN)
    public String hello() {
        return "Hello from Quarkus!";
    }
}
```

### 3. Database Integration (Hibernate ORM with Panache)

```java
@Entity
@Table(name = "users")
public class User extends PanacheEntity {
    public String name;
    public String email;

    public static List<User> findByName(String name) {
        return find("name", name).list();
    }
}
```

## Benefits of Quarkus in Production

### 1. Container Environment Optimization

In Kubernetes, faster startup times enable quicker response to traffic spikes during Pod scaling.

```yaml
# Requesting fewer resources in Kubernetes Deployment
resources:
  requests:
    memory: "32Mi"
    cpu: "100m"
  limits:
    memory: "64Mi"
    cpu: "200m"
```

### 2. Improved Development Productivity

Live Coding feature reflects code changes immediately without application restart.

```bash
# Run in development mode
mvn quarkus:dev
```

### 3. GraalVM Native Image

When compiled to native image, it can run without JVM.

```bash
# Build native image
mvn clean package -Pnative

# Check executable size and startup time
ls -lh target/*-runner
time ./target/quarkus-demo-1.0.0-SNAPSHOT-runner
```

## Quarkus Migration for Spring Boot Developers

### Dependency Injection

```java
// Spring Boot
@Autowired
private UserService userService;

// Quarkus (CDI)
@Inject
UserService userService;
```

### Configuration

```java
// Spring Boot
@Value("${app.name}")
private String appName;

// Quarkus
@ConfigProperty(name = "app.name")
String appName;
```

### REST Controller

```java
// Spring Boot
@RestController
@RequestMapping("/api")
public class UserController {
    @GetMapping("/users")
    public List<User> getUsers() { ... }
}

// Quarkus
@Path("/api/users")
public class UserResource {
    @GET
    public List<User> getUsers() { ... }
}
```

## When to Choose Quarkus?

### Quarkus is Suitable for:

- **Microservices Architecture**
- **Container-based Deployment**
- **Serverless Environments** (AWS Lambda, etc.)
- **Resource-constrained Environments**

### Spring Boot is Still Great for:

- **Deep Dependency on Spring Ecosystem**
- **Large Monolithic Applications**
- **Need for Rich Community Support**

## Performance Test Results

Results measured from actual projects:

```
# Based on identical REST API
┌──────────────┬─────────────┬──────────────┬─────────────┐
│              │ Spring Boot │ Quarkus JVM  │ Quarkus Native │
├──────────────┼─────────────┼──────────────┼─────────────┤
│ Startup Time │ 3.2s        │ 1.1s         │ 0.016s      │
│ Memory Usage │ 200MB       │ 50MB         │ 20MB        │
│ Throughput   │ 1,200 RPS   │ 1,180 RPS    │ 1,100 RPS   │
└──────────────┴─────────────┴──────────────┴─────────────┘
```

## Conclusion

Quarkus is a Java framework suited for the cloud-native era. Rather than being a complete replacement for Spring Boot, it can be **a better choice in specific situations**.

Particularly, consider adopting Quarkus in the following scenarios:

1. When **container resource cost optimization** is important
2. Microservices requiring **fast scale-out**
3. **Java usage in serverless environments**

I'll continue to share practical application cases as I use Quarkus in more projects!

---

**References:**
- [Quarkus Official Documentation](https://quarkus.io/)
- [Quarkus vs Spring Boot Benchmark](https://quarkus.io/blog/quarkus-vs-spring-boot/)
- [GraalVM Native Image](https://www.graalvm.org/latest/reference-manual/native-image/)

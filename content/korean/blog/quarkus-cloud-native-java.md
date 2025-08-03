---
title: "Quarkus로 시작하는 Cloud Native Java 개발"
meta_title: "Quarkus Cloud Native Java"
description: "Kubernetes 시대의 Java 프레임워크 Quarkus 소개와 Spring Boot와의 비교"
date: 2025-08-03T13:00:00+09:00
image: "/images/service-1.png"
categories: ["웹개발"]
author: "Kigo"
tags: ["Java", "Quarkus", "Cloud Native", "Kubernetes", "GraalVM"]
draft: false
---

최근 클라우드 네이티브 환경에서 Java 애플리케이션의 한계점들이 많이 언급되고 있습니다. 특히 **높은 메모리 사용량**과 **느린 시작 시간** 때문에 컨테이너 환경에서는 다소 불리한 면이 있었죠. 이런 문제를 해결하기 위해 등장한 것이 바로 **Quarkus**입니다.

## Quarkus란?

Quarkus는 Red Hat에서 개발한 **Kubernetes Native Java 프레임워크**입니다. "Supersonic Subatomic Java"라는 슬로건답게 기존 Java 애플리케이션보다 훨씬 빠른 시작 시간과 낮은 메모리 사용량을 자랑합니다.

### 주요 특징

- **빠른 시작 시간**: 밀리초 단위의 시작 시간
- **낮은 메모리 사용량**: 기존 대비 1/10 수준
- **GraalVM Native Image 지원**: 네이티브 컴파일 가능
- **개발자 친화적**: Live Coding으로 즉시 반영

## Spring Boot vs Quarkus

### 메모리 사용량 비교

```bash
# Spring Boot 애플리케이션
Memory: ~200MB

# Quarkus JVM 모드
Memory: ~50MB

# Quarkus Native 모드
Memory: ~20MB
```

### 시작 시간 비교

```bash
# Spring Boot
Started in 3.2 seconds

# Quarkus JVM 모드
Started in 1.1 seconds

# Quarkus Native 모드
Started in 0.016 seconds
```

## Quarkus 프로젝트 시작하기

### 1. 프로젝트 생성

```bash
mvn io.quarkus.platform:quarkus-maven-plugin:3.2.4.Final:create \
    -DprojectGroupId=com.kigo.example \
    -DprojectArtifactId=quarkus-demo \
    -DclassName="com.kigo.example.GreetingResource" \
    -Dpath="/hello"
```

### 2. 기본 REST API 구현

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

### 3. 데이터베이스 연동 (Hibernate ORM with Panache)

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

## 실무에서 느낀 Quarkus의 장점

### 1. 컨테이너 환경 최적화

Kubernetes에서 Pod 스케일링 시 빠른 시작 시간 덕분에 트래픽 급증에 더 빠르게 대응할 수 있습니다.

```yaml
# Kubernetes Deployment에서 더 적은 리소스 요청
resources:
  requests:
    memory: "32Mi"
    cpu: "100m"
  limits:
    memory: "64Mi"
    cpu: "200m"
```

### 2. 개발 생산성 향상

Live Coding 기능으로 코드 변경 시 애플리케이션 재시작 없이 즉시 반영됩니다.

```bash
# 개발 모드로 실행
mvn quarkus:dev
```

### 3. GraalVM Native Image

네이티브 이미지로 컴파일하면 JVM 없이도 실행 가능합니다.

```bash
# Native 이미지 빌드
mvn clean package -Pnative

# 실행 파일 크기와 시작 시간 확인
ls -lh target/*-runner
time ./target/quarkus-demo-1.0.0-SNAPSHOT-runner
```

## Spring Boot 개발자를 위한 Quarkus 마이그레이션

### 의존성 주입

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

## 언제 Quarkus를 선택해야 할까?

### Quarkus가 적합한 경우

- **마이크로서비스 아키텍처**
- **컨테이너 기반 배포**
- **서버리스 환경** (AWS Lambda, etc.)
- **리소스 제약이 있는 환경**

### Spring Boot가 여전히 좋은 경우

- **기존 Spring 생태계에 깊이 의존**
- **대규모 모놀리식 애플리케이션**
- **풍부한 커뮤니티 지원이 필요한 경우**

## 성능 테스트 결과

실제 프로젝트에서 측정한 결과입니다:

```
# 동일한 REST API 기준
┌──────────────┬─────────────┬──────────────┬─────────────┐
│              │ Spring Boot │ Quarkus JVM  │ Quarkus Native │
├──────────────┼─────────────┼──────────────┼─────────────┤
│ 시작 시간     │ 3.2초       │ 1.1초        │ 0.016초     │
│ 메모리 사용량 │ 200MB       │ 50MB         │ 20MB        │
│ 처리량(RPS)   │ 1,200       │ 1,180        │ 1,100       │
└──────────────┴─────────────┴──────────────┴─────────────┘
```

## 마치며

Quarkus는 클라우드 네이티브 시대에 맞는 Java 프레임워크입니다. Spring Boot의 완전한 대체재라기보다는, **특정 상황에서 더 나은 선택지**가 될 수 있습니다.

특히 다음과 같은 상황에서는 Quarkus 도입을 적극 고려해볼 만합니다:

1. **컨테이너 리소스 비용 최적화**가 중요한 경우
2. **빠른 스케일 아웃**이 필요한 마이크로서비스
3. **서버리스 환경**에서의 Java 사용

앞으로 더 많은 프로젝트에서 Quarkus를 활용해보면서, 실무 적용 사례들을 계속 공유하겠습니다!

---

**참고 자료:**
- [Quarkus 공식 문서](https://quarkus.io/)
- [Quarkus vs Spring Boot 벤치마크](https://quarkus.io/blog/quarkus-vs-spring-boot/)
- [GraalVM Native Image](https://www.graalvm.org/latest/reference-manual/native-image/)

---
title: "Quarkus JPA 완전 정복 - 엔티티부터 트랜잭션까지"
meta_title: "Quarkus JPA 사용법 완전 정복 - 백엔드 개발자를 위한 학습 가이드"
description: "Quarkus에서 JPA를 활용한 데이터베이스 연동부터 고급 기능까지, 백엔드 개발자가 알아야 할 모든 것을 다룹니다."
date: 2025-08-03T10:00:00+09:00
image: "/images/service-3.png"
categories: ["웹개발"]
tags: ["Quarkus", "JPA", "Database", "Java", "Backend", "Hibernate", "PostgreSQL"]
draft: false
author: "Kigo"
---

Spring Boot에서 JPA를 사용하다 Quarkus로 넘어오면서 가장 궁금했던 것이 "데이터베이스 연동은 어떻게 하지?"였습니다. 다행히 Quarkus도 JPA를 완벽 지원하며, 오히려 더 간단하고 성능이 좋은 경우가 많습니다.

## 프로젝트 설정

### 의존성 추가

`pom.xml`에 필요한 의존성을 추가합니다:

```xml
<dependencies>
    <!-- Quarkus JPA 확장 -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-hibernate-orm-panache</artifactId>
    </dependency>

    <!-- PostgreSQL 드라이버 -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-jdbc-postgresql</artifactId>
    </dependency>

    <!-- 개발 시 유용한 DevServices -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-devservices-postgresql</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### 데이터베이스 설정

`application.properties`에서 데이터베이스를 설정합니다:

```properties
# 데이터베이스 연결 설정
quarkus.datasource.db-kind=postgresql
quarkus.datasource.username=postgres
quarkus.datasource.password=password
quarkus.datasource.jdbc.url=jdbc:postgresql://localhost:5432/quarkus_jpa

# Hibernate 설정
quarkus.hibernate-orm.database.generation=drop-and-create
quarkus.hibernate-orm.log.sql=true
quarkus.hibernate-orm.log.bind-parameters=true

# 개발 환경에서만 사용 (운영에서는 validate 또는 none)
%dev.quarkus.hibernate-orm.database.generation=drop-and-create
%prod.quarkus.hibernate-orm.database.generation=validate
```

## 엔티티 정의

Quarkus에서는 표준 JPA 어노테이션을 그대로 사용할 수 있습니다:

```java
@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String name;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Post> posts = new ArrayList<>();

    // 기본 생성자 (JPA 필수)
    public User() {}

    public User(String email, String name) {
        this.email = email;
        this.name = name;
        this.createdAt = LocalDateTime.now();
    }

    // getter/setter 생략
}
```

```java
@Entity
@Table(name = "posts")
public class Post {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String content;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    public Post() {}

    public Post(String title, String content, User user) {
        this.title = title;
        this.content = content;
        this.user = user;
        this.createdAt = LocalDateTime.now();
    }

    // getter/setter 생략
}
```

## Repository 패턴 vs Panache 패턴

Quarkus는 두 가지 방식을 지원합니다:

### 1. 전통적인 Repository 패턴

```java
@ApplicationScoped
public class UserRepository {

    @Inject
    EntityManager em;

    @Transactional
    public User save(User user) {
        if (user.getId() == null) {
            em.persist(user);
            return user;
        } else {
            return em.merge(user);
        }
    }

    public Optional<User> findById(Long id) {
        return Optional.ofNullable(em.find(User.class, id));
    }

    public Optional<User> findByEmail(String email) {
        try {
            User user = em.createQuery(
                "SELECT u FROM User u WHERE u.email = :email", User.class)
                .setParameter("email", email)
                .getSingleResult();
            return Optional.of(user);
        } catch (NoResultException e) {
            return Optional.empty();
        }
    }

    public List<User> findAll() {
        return em.createQuery("SELECT u FROM User u", User.class)
                .getResultList();
    }

    @Transactional
    public void delete(User user) {
        em.remove(em.merge(user));
    }
}
```

### 2. Panache 패턴 (권장)

Panache를 사용하면 훨씬 간단해집니다:

```java
@Entity
@Table(name = "users")
public class User extends PanacheEntity {

    @Column(nullable = false, unique = true)
    public String email;

    @Column(nullable = false)
    public String name;

    @Column(name = "created_at")
    public LocalDateTime createdAt;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    public List<Post> posts = new ArrayList<>();

    public User() {}

    public User(String email, String name) {
        this.email = email;
        this.name = name;
        this.createdAt = LocalDateTime.now();
    }

    // 커스텀 쿼리 메서드
    public static Optional<User> findByEmail(String email) {
        return find("email", email).firstResultOptional();
    }

    public static List<User> findByNameContaining(String name) {
        return find("name like ?1", "%" + name + "%").list();
    }
}
```

Repository 클래스를 별도로 만들고 싶다면:

```java
@ApplicationScoped
public class UserRepository implements PanacheRepository<User> {

    public Optional<User> findByEmail(String email) {
        return find("email", email).firstResultOptional();
    }

    public List<User> findActiveUsers() {
        return find("active = true").list();
    }

    public long countByDomain(String domain) {
        return count("email like ?1", "%@" + domain);
    }
}
```

## 서비스 계층 구현

```java
@ApplicationScoped
public class UserService {

    @Inject
    UserRepository userRepository;

    @Transactional
    public User createUser(String email, String name) {
        // 이메일 중복 체크
        if (userRepository.findByEmail(email).isPresent()) {
            throw new IllegalArgumentException("이미 존재하는 이메일입니다.");
        }

        User user = new User(email, name);
        userRepository.persist(user);
        return user;
    }

    public Optional<User> getUserById(Long id) {
        return userRepository.findByIdOptional(id);
    }

    public List<User> getAllUsers() {
        return userRepository.listAll();
    }

    @Transactional
    public User updateUser(Long id, String name) {
        User user = userRepository.findById(id);
        if (user == null) {
            throw new EntityNotFoundException("사용자를 찾을 수 없습니다.");
        }

        user.name = name;
        return user; // Panache는 자동으로 변경사항을 감지
    }

    @Transactional
    public void deleteUser(Long id) {
        if (!userRepository.deleteById(id)) {
            throw new EntityNotFoundException("사용자를 찾을 수 없습니다.");
        }
    }
}
```

## REST API 구현

```java
@Path("/api/users")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class UserResource {

    @Inject
    UserService userService;

    @GET
    public List<User> getAllUsers() {
        return userService.getAllUsers();
    }

    @GET
    @Path("/{id}")
    public Response getUserById(@PathParam("id") Long id) {
        return userService.getUserById(id)
                .map(user -> Response.ok(user).build())
                .orElse(Response.status(Response.Status.NOT_FOUND).build());
    }

    @POST
    public Response createUser(CreateUserRequest request) {
        try {
            User user = userService.createUser(request.email, request.name);
            return Response.status(Response.Status.CREATED).entity(user).build();
        } catch (IllegalArgumentException e) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", e.getMessage()))
                    .build();
        }
    }

    @PUT
    @Path("/{id}")
    public Response updateUser(@PathParam("id") Long id, UpdateUserRequest request) {
        try {
            User user = userService.updateUser(id, request.name);
            return Response.ok(user).build();
        } catch (EntityNotFoundException e) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", e.getMessage()))
                    .build();
        }
    }

    @DELETE
    @Path("/{id}")
    public Response deleteUser(@PathParam("id") Long id) {
        try {
            userService.deleteUser(id);
            return Response.noContent().build();
        } catch (EntityNotFoundException e) {
            return Response.status(Response.Status.NOT_FOUND)
                    .entity(Map.of("error", e.getMessage()))
                    .build();
        }
    }

    public static class CreateUserRequest {
        public String email;
        public String name;
    }

    public static class UpdateUserRequest {
        public String name;
    }
}
```

## 고급 기능

### 1. 커스텀 쿼리

```java
@ApplicationScoped
public class PostRepository implements PanacheRepository<Post> {

    // JPQL 사용
    public List<Post> findByTitleContaining(String keyword) {
        return find("title like ?1", "%" + keyword + "%").list();
    }

    // 네이티브 쿼리 사용
    @Query(value = "SELECT * FROM posts WHERE created_at >= ?1", nativeQuery = true)
    public List<Post> findRecentPosts(LocalDateTime since) {
        return getEntityManager()
                .createNativeQuery("SELECT * FROM posts WHERE created_at >= ?1", Post.class)
                .setParameter(1, since)
                .getResultList();
    }

    // 복잡한 조건 쿼리
    public List<Post> findPostsByUserAndPeriod(String userEmail,
                                              LocalDateTime startDate,
                                              LocalDateTime endDate) {
        return find("user.email = ?1 and createdAt between ?2 and ?3",
                   userEmail, startDate, endDate).list();
    }
}
```

### 2. 트랜잭션 관리

```java
@ApplicationScoped
public class PostService {

    @Inject
    PostRepository postRepository;

    @Inject
    UserRepository userRepository;

    // 기본 트랜잭션
    @Transactional
    public Post createPost(Long userId, String title, String content) {
        User user = userRepository.findById(userId);
        if (user == null) {
            throw new EntityNotFoundException("사용자를 찾을 수 없습니다.");
        }

        Post post = new Post(title, content, user);
        postRepository.persist(post);
        return post;
    }

    // 읽기 전용 트랜잭션
    @Transactional(Transactional.TxType.SUPPORTS)
    public List<Post> getPostsByUser(Long userId) {
        return postRepository.find("user.id", userId).list();
    }

    // 새 트랜잭션 생성
    @Transactional(Transactional.TxType.REQUIRES_NEW)
    public void logActivity(String activity) {
        // 로그는 별도 트랜잭션에서 처리
        // 메인 트랜잭션이 롤백되어도 로그는 유지됨
    }

    // 롤백 조건 지정
    @Transactional(rollbackOn = {BusinessException.class})
    public void complexBusinessLogic() {
        // BusinessException 발생 시에만 롤백
    }
}
```

### 3. 페이징과 정렬

```java
@GET
public Response getUsers(@QueryParam("page") @DefaultValue("0") int page,
                        @QueryParam("size") @DefaultValue("10") int size,
                        @QueryParam("sort") @DefaultValue("id") String sort) {

    PanacheQuery<User> query = User.findAll(Sort.by(sort));
    List<User> users = query.page(page, size).list();

    long totalCount = query.count();
    int totalPages = (int) Math.ceil((double) totalCount / size);

    Map<String, Object> response = Map.of(
        "users", users,
        "currentPage", page,
        "totalPages", totalPages,
        "totalCount", totalCount
    );

    return Response.ok(response).build();
}
```

## 개발 환경 팁

### DevServices 활용

개발 환경에서는 DevServices를 사용하면 별도의 데이터베이스 설치 없이 개발할 수 있습니다:

```properties
# 개발 환경에서는 DevServices가 자동으로 PostgreSQL 컨테이너 실행
%dev.quarkus.devservices.enabled=true
%test.quarkus.devservices.enabled=true

# 특정 데이터베이스 버전 지정
quarkus.datasource.devservices.image-name=postgres:14
```

### 데이터 초기화

```java
@ApplicationScoped
public class DataInitializer {

    @Inject
    UserService userService;

    @Inject
    PostService postService;

    void onStart(@Observes StartupEvent ev) {
        // 개발 환경에서만 실행
        if (Profile.of("dev").equals(Profile.getCurrent())) {
            initializeData();
        }
    }

    @Transactional
    void initializeData() {
        // 테스트 데이터 생성
        User user1 = userService.createUser("john@example.com", "John Doe");
        User user2 = userService.createUser("jane@example.com", "Jane Smith");

        postService.createPost(user1.id, "First Post", "This is my first post");
        postService.createPost(user2.id, "Another Post", "Hello world!");
    }
}
```

## Spring Boot와의 주요 차이점

1. **Panache 패턴**: Repository 인터페이스 구현이 불필요
2. **빠른 시작**: 네이티브 이미지에서 빠른 부팅 시간
3. **DevServices**: 개발 환경 자동 구성
4. **설정 방식**: `application.properties` 중심
5. **의존성 주입**: CDI 기반으로 `@Inject` 사용

## 마무리

Quarkus JPA는 Spring Boot JPA와 매우 유사하면서도 더 간단하고 성능이 좋습니다. 특히 Panache 패턴을 사용하면 보일러플레이트 코드를 크게 줄일 수 있어서 개발 생산성이 향상됩니다.

클라우드 네이티브 환경에서 빠른 시작 시간과 적은 메모리 사용량이 중요하다면 Quarkus JPA를 적극 추천합니다. 기존 JPA 지식이 있다면 러닝 커브도 거의 없어서 쉽게 적응할 수 있을 것입니다.

다음 포스트에서는 Quarkus에서 Redis 캐싱과 메시징 시스템 연동에 대해 다뤄보겠습니다.

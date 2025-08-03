---
title: "Complete Quarkus JPA Guide - From Entity to Transaction"
meta_title: "Complete Quarkus JPA Usage Guide - Learning Guide for Backend Developers"
description: "Everything backend developers need to know about using JPA in Quarkus, from database integration to advanced features."
date: 2025-08-03T10:00:00+09:00
image: "/images/service-3.png"
categories: ["backend"]
tags: ["Quarkus", "JPA", "Database", "Java", "Backend", "Hibernate", "PostgreSQL"]
draft: false
author: "Kigo"
---

When transitioning from Spring Boot to Quarkus, one of the first questions that comes to mind is "How do I handle database integration?" Fortunately, Quarkus provides excellent JPA support, often with better performance and simpler configuration.

## Project Setup

### Adding Dependencies

Add the necessary dependencies to your `pom.xml`:

```xml
<dependencies>
    <!-- Quarkus JPA Extension -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-hibernate-orm-panache</artifactId>
    </dependency>

    <!-- PostgreSQL Driver -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-jdbc-postgresql</artifactId>
    </dependency>

    <!-- DevServices for Development -->
    <dependency>
        <groupId>io.quarkus</groupId>
        <artifactId>quarkus-devservices-postgresql</artifactId>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### Database Configuration

Configure your database in `application.properties`:

```properties
# Database Connection Settings
quarkus.datasource.db-kind=postgresql
quarkus.datasource.username=postgres
quarkus.datasource.password=password
quarkus.datasource.jdbc.url=jdbc:postgresql://localhost:5432/quarkus_jpa

# Hibernate Settings
quarkus.hibernate-orm.database.generation=drop-and-create
quarkus.hibernate-orm.log.sql=true
quarkus.hibernate-orm.log.bind-parameters=true

# Environment-specific settings
%dev.quarkus.hibernate-orm.database.generation=drop-and-create
%prod.quarkus.hibernate-orm.database.generation=validate
```

## Entity Definition

Quarkus uses standard JPA annotations:

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

    // Default constructor (required by JPA)
    public User() {}

    public User(String email, String name) {
        this.email = email;
        this.name = name;
        this.createdAt = LocalDateTime.now();
    }

    // getters/setters omitted
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

    // getters/setters omitted
}
```

## Repository Pattern vs Panache Pattern

Quarkus supports both approaches:

### 1. Traditional Repository Pattern

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

### 2. Panache Pattern (Recommended)

Using Panache makes everything much simpler:

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

    // Custom query methods
    public static Optional<User> findByEmail(String email) {
        return find("email", email).firstResultOptional();
    }

    public static List<User> findByNameContaining(String name) {
        return find("name like ?1", "%" + name + "%").list();
    }
}
```

If you prefer separate repository classes:

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

## Service Layer Implementation

```java
@ApplicationScoped
public class UserService {

    @Inject
    UserRepository userRepository;

    @Transactional
    public User createUser(String email, String name) {
        // Check for duplicate email
        if (userRepository.findByEmail(email).isPresent()) {
            throw new IllegalArgumentException("Email already exists");
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
            throw new EntityNotFoundException("User not found");
        }

        user.name = name;
        return user; // Panache automatically detects changes
    }

    @Transactional
    public void deleteUser(Long id) {
        if (!userRepository.deleteById(id)) {
            throw new EntityNotFoundException("User not found");
        }
    }
}
```

## REST API Implementation

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

## Advanced Features

### 1. Custom Queries

```java
@ApplicationScoped
public class PostRepository implements PanacheRepository<Post> {

    // Using JPQL
    public List<Post> findByTitleContaining(String keyword) {
        return find("title like ?1", "%" + keyword + "%").list();
    }

    // Using native queries
    public List<Post> findRecentPosts(LocalDateTime since) {
        return getEntityManager()
                .createNativeQuery("SELECT * FROM posts WHERE created_at >= ?1", Post.class)
                .setParameter(1, since)
                .getResultList();
    }

    // Complex conditional queries
    public List<Post> findPostsByUserAndPeriod(String userEmail,
                                              LocalDateTime startDate,
                                              LocalDateTime endDate) {
        return find("user.email = ?1 and createdAt between ?2 and ?3",
                   userEmail, startDate, endDate).list();
    }
}
```

### 2. Transaction Management

```java
@ApplicationScoped
public class PostService {

    @Inject
    PostRepository postRepository;

    @Inject
    UserRepository userRepository;

    // Basic transaction
    @Transactional
    public Post createPost(Long userId, String title, String content) {
        User user = userRepository.findById(userId);
        if (user == null) {
            throw new EntityNotFoundException("User not found");
        }

        Post post = new Post(title, content, user);
        postRepository.persist(post);
        return post;
    }

    // Read-only transaction
    @Transactional(Transactional.TxType.SUPPORTS)
    public List<Post> getPostsByUser(Long userId) {
        return postRepository.find("user.id", userId).list();
    }

    // New transaction
    @Transactional(Transactional.TxType.REQUIRES_NEW)
    public void logActivity(String activity) {
        // Logs are processed in separate transaction
        // Logs persist even if main transaction rolls back
    }

    // Specify rollback conditions
    @Transactional(rollbackOn = {BusinessException.class})
    public void complexBusinessLogic() {
        // Only rolls back on BusinessException
    }
}
```

### 3. Pagination and Sorting

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

## Development Environment Tips

### Using DevServices

In development, DevServices automatically sets up databases:

```properties
# DevServices automatically runs PostgreSQL container in dev/test
%dev.quarkus.devservices.enabled=true
%test.quarkus.devservices.enabled=true

# Specify database version
quarkus.datasource.devservices.image-name=postgres:14
```

### Data Initialization

```java
@ApplicationScoped
public class DataInitializer {

    @Inject
    UserService userService;

    @Inject
    PostService postService;

    void onStart(@Observes StartupEvent ev) {
        // Only run in development
        if (Profile.of("dev").equals(Profile.getCurrent())) {
            initializeData();
        }
    }

    @Transactional
    void initializeData() {
        // Create test data
        User user1 = userService.createUser("john@example.com", "John Doe");
        User user2 = userService.createUser("jane@example.com", "Jane Smith");

        postService.createPost(user1.id, "First Post", "This is my first post");
        postService.createPost(user2.id, "Another Post", "Hello world!");
    }
}
```

## Key Differences from Spring Boot

1. **Panache Pattern**: No need to implement repository interfaces
2. **Fast Startup**: Quick boot times in native images
3. **DevServices**: Automatic development environment setup
4. **Configuration**: `application.properties` focused
5. **Dependency Injection**: CDI-based using `@Inject`

## Conclusion

Quarkus JPA is remarkably similar to Spring Boot JPA while being simpler and more performant. The Panache pattern significantly reduces boilerplate code, improving development productivity.

If fast startup times and low memory usage are important for your cloud-native environment, I highly recommend Quarkus JPA. With existing JPA knowledge, the learning curve is minimal and adaptation is straightforward.

In the next post, we'll explore Redis caching and messaging system integration in Quarkus.

---
title: "Spring Boot Production Best Practices"
meta_title: ""
description: "Learn essential configurations and coding conventions for stable Spring Boot applications in production environments."
date: 2022-04-04T05:00:00Z
image: "/images/service-1.png"
categories: ["Backend", "Java"]
author: "Kigo"
tags: ["Spring Boot", "Java", "Backend", "Best Practices"]
draft: false
---

To create stable Spring Boot applications in production, you need more than just basic functionality. Let's explore essential practices for building robust, secure, and maintainable applications.

## Application Configuration

### Profile-based Configuration

```yaml
# application.yml
spring:
  profiles:
    active: ${SPRING_PROFILES_ACTIVE:dev}

---
# Development profile
spring:
  config:
    activate:
      on-profile: dev
  datasource:
    url: jdbc:h2:mem:testdb
    driver-class-name: org.h2.Driver
  jpa:
    show-sql: true
    hibernate:
      ddl-auto: create-drop

---
# Production profile
spring:
  config:
    activate:
      on-profile: prod
  datasource:
    url: ${DATABASE_URL}
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
  jpa:
    show-sql: false
    hibernate:
      ddl-auto: validate
```

### Externalized Configuration

```java
@ConfigurationProperties(prefix = "app")
@Component
public class AppProperties {

    private String name;
    private String version;
    private Security security = new Security();
    private Database database = new Database();

    // Getters and setters

    public static class Security {
        private String jwtSecret;
        private long jwtExpirationMs = 86400000; // 24 hours

        // Getters and setters
    }

    public static class Database {
        private int maxConnections = 20;
        private int connectionTimeout = 30000;

        // Getters and setters
    }
}
```

## Security Implementation

### JWT Authentication

```java
@Component
public class JwtTokenProvider {

    private final String jwtSecret;
    private final int jwtExpirationMs;

    public JwtTokenProvider(AppProperties appProperties) {
        this.jwtSecret = appProperties.getSecurity().getJwtSecret();
        this.jwtExpirationMs = appProperties.getSecurity().getJwtExpirationMs();
    }

    public String generateToken(Authentication authentication) {
        UserPrincipal userPrincipal = (UserPrincipal) authentication.getPrincipal();
        Date expiryDate = new Date(System.currentTimeMillis() + jwtExpirationMs);

        return Jwts.builder()
                .setSubject(Long.toString(userPrincipal.getId()))
                .setIssuedAt(new Date())
                .setExpiration(expiryDate)
                .signWith(SignatureAlgorithm.HS512, jwtSecret)
                .compact();
    }

    public boolean validateToken(String authToken) {
        try {
            Jwts.parser().setSigningKey(jwtSecret).parseClaimsJws(authToken);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            log.error("Invalid JWT token: {}", e.getMessage());
        }
        return false;
    }
}
```

### Security Configuration

```java
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig {

    @Autowired
    private JwtAuthenticationEntryPoint unauthorizedHandler;

    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter() {
        return new JwtAuthenticationFilter();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.cors()
            .and()
            .csrf().disable()
            .exceptionHandling()
                .authenticationEntryPoint(unauthorizedHandler)
            .and()
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            .and()
            .authorizeRequests()
                .antMatchers("/api/auth/**").permitAll()
                .antMatchers("/api/public/**").permitAll()
                .antMatchers(HttpMethod.GET, "/api/posts/**").permitAll()
                .anyRequest().authenticated();

        http.addFilterBefore(jwtAuthenticationFilter(),
                            UsernamePasswordAuthenticationFilter.class);
    }
}
```

## Error Handling

### Global Exception Handler

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(ValidationException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ApiResponse handleValidationException(ValidationException ex) {
        log.warn("Validation error: {}", ex.getMessage());
        return ApiResponse.error("Validation failed", ex.getMessage());
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ApiResponse handleResourceNotFoundException(ResourceNotFoundException ex) {
        log.warn("Resource not found: {}", ex.getMessage());
        return ApiResponse.error("Resource not found", ex.getMessage());
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ApiResponse handleDataIntegrityViolation(DataIntegrityViolationException ex) {
        log.error("Data integrity violation: {}", ex.getMessage());
        return ApiResponse.error("Data conflict", "The requested operation conflicts with existing data");
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ApiResponse handleGenericException(Exception ex) {
        log.error("Unexpected error occurred", ex);
        return ApiResponse.error("Internal server error", "An unexpected error occurred");
    }
}
```

## Database Optimization

### Connection Pool Configuration

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5
      idle-timeout: 300000
      max-lifetime: 1200000
      connection-timeout: 20000
      validation-timeout: 5000
      leak-detection-threshold: 60000
```

### JPA Performance Tuning

```java
@Entity
@Table(name = "users", indexes = {
    @Index(name = "idx_user_email", columnList = "email"),
    @Index(name = "idx_user_status", columnList = "status")
})
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @OneToMany(mappedBy = "user", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @BatchSize(size = 20)
    private List<Post> posts = new ArrayList<>();

    // Constructors, getters, setters
}

@Repository
public class UserRepository extends JpaRepository<User, Long> {

    @Query("SELECT u FROM User u LEFT JOIN FETCH u.posts WHERE u.id = :id")
    Optional<User> findByIdWithPosts(@Param("id") Long id);

    @Query(value = "SELECT * FROM users WHERE status = :status ORDER BY created_at DESC LIMIT :limit",
           nativeQuery = true)
    List<User> findActiveUsersWithLimit(@Param("status") String status, @Param("limit") int limit);
}
```

## Monitoring and Observability

### Actuator Configuration

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: when-authorized
  metrics:
    export:
      prometheus:
        enabled: true
```

### Custom Health Indicator

```java
@Component
public class DatabaseHealthIndicator implements HealthIndicator {

    private final DataSource dataSource;

    public DatabaseHealthIndicator(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public Health health() {
        try (Connection connection = dataSource.getConnection()) {
            if (connection.isValid(1)) {
                return Health.up()
                    .withDetail("database", "Available")
                    .withDetail("validationQuery", "SELECT 1")
                    .build();
            }
        } catch (SQLException e) {
            return Health.down()
                .withDetail("database", "Unavailable")
                .withException(e)
                .build();
        }
        return Health.down().withDetail("database", "Connection validation failed").build();
    }
}
```

### Application Metrics

```java
@Service
@Slf4j
public class UserService {

    private final UserRepository userRepository;
    private final MeterRegistry meterRegistry;
    private final Counter userCreationCounter;
    private final Timer userFetchTimer;

    public UserService(UserRepository userRepository, MeterRegistry meterRegistry) {
        this.userRepository = userRepository;
        this.meterRegistry = meterRegistry;
        this.userCreationCounter = Counter.builder("user.creation.count")
            .description("Number of users created")
            .register(meterRegistry);
        this.userFetchTimer = Timer.builder("user.fetch.time")
            .description("Time taken to fetch users")
            .register(meterRegistry);
    }

    public User createUser(CreateUserRequest request) {
        return userFetchTimer.recordCallable(() -> {
            User user = new User(request.getEmail(), request.getName());
            User savedUser = userRepository.save(user);
            userCreationCounter.increment();
            log.info("User created with ID: {}", savedUser.getId());
            return savedUser;
        });
    }
}
```

## Testing Best Practices

### Integration Tests

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@TestPropertySource(properties = {
    "spring.datasource.url=jdbc:h2:mem:testdb",
    "spring.jpa.hibernate.ddl-auto=create-drop"
})
class UserControllerIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private UserRepository userRepository;

    @Test
    void createUser_Test() {
        CreateUserRequest request = new CreateUserRequest("test@example.com", "Test User");

        ResponseEntity<User> response = restTemplate.postForEntity("/api/users", request, User.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody().getEmail()).isEqualTo("test@example.com");
        assertThat(userRepository.count()).isEqualTo(1);
    }
}
```

### Unit Tests with Mocking

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private MeterRegistry meterRegistry;

    @InjectMocks
    private UserService userService;

    @Test
    void createUser_Success_Test() {
        // Given
        CreateUserRequest request = new CreateUserRequest("test@example.com", "Test User");
        User savedUser = new User("test@example.com", "Test User");
        savedUser.setId(1L);

        when(userRepository.save(any(User.class))).thenReturn(savedUser);

        // When
        User result = userService.createUser(request);

        // Then
        assertThat(result.getId()).isEqualTo(1L);
        assertThat(result.getEmail()).isEqualTo("test@example.com");
        verify(userRepository).save(any(User.class));
    }
}
```

## Performance Optimization

### Caching Strategy

```java
@Service
@EnableCaching
public class UserService {

    @Cacheable(value = "users", key = "#id")
    public User findById(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("User not found"));
    }

    @CacheEvict(value = "users", key = "#user.id")
    public User updateUser(User user) {
        return userRepository.save(user);
    }

    @CacheEvict(value = "users", allEntries = true)
    public void clearUserCache() {
        // Cache will be cleared
    }
}
```

### Asynchronous Processing

```java
@Service
@Slf4j
public class EmailService {

    @Async("taskExecutor")
    public CompletableFuture<Void> sendWelcomeEmail(String email, String name) {
        try {
            // Email sending simulation
            Thread.sleep(2000);
            log.info("Welcome email sent to: {}", email);
            return CompletableFuture.completedFuture(null);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return CompletableFuture.failedFuture(e);
        }
    }
}

@Configuration
@EnableAsync
public class AsyncConfig {

    @Bean(name = "taskExecutor")
    public TaskExecutor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.initialize();
        return executor;
    }
}
```

Through these practices, you can ensure that Spring Boot applications are safe and maintainable in production. Implement them gradually while adjusting to specific requirements.

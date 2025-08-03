---
title: "Spring Boot 프로덕션 베스트 프랙티스"
meta_title: ""
description: "프로덕션 환경에서 안정적인 Spring Boot 애플리케이션을 위한 필수 설정과 코딩 관례들을 알아봅니다."
date: 2022-04-04T05:00:00Z
image: "/images/service-1.png"
categories: ["백엔드", "Java"]
author: "Kigo"
tags: ["Spring Boot", "Java", "백엔드", "베스트 프랙티스"]
draft: false
---

프로덕션에서 안정적인 Spring Boot 애플리케이션을 만들기 위해서는 기본 기능 구현 이상의 것들이 필요합니다. 견고하고 안전하며 유지보수가 가능한 애플리케이션을 만들기 위한 필수 관례들을 알아보겠습니다.

## 애플리케이션 설정

### 프로파일 기반 설정

```yaml
# application.yml
spring:
  profiles:
    active: ${SPRING_PROFILES_ACTIVE:dev}

---
# 개발 프로파일
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
# 프로덕션 프로파일
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

### 외부화된 설정

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
        private long jwtExpirationMs = 86400000; // 24시간

        // Getters and setters
    }

    public static class Database {
        private int maxConnections = 20;
        private int connectionTimeout = 30000;

        // Getters and setters
    }
}
```

## 보안 구현

### JWT 인증

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
            log.error("유효하지 않은 JWT 토큰: {}", e.getMessage());
        }
        return false;
    }
}
```

### 보안 설정

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

## 에러 핸들링

### 글로벌 예외 처리기

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(ValidationException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ApiResponse handleValidationException(ValidationException ex) {
        log.warn("검증 오류: {}", ex.getMessage());
        return ApiResponse.error("검증 실패", ex.getMessage());
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ApiResponse handleResourceNotFoundException(ResourceNotFoundException ex) {
        log.warn("리소스를 찾을 수 없음: {}", ex.getMessage());
        return ApiResponse.error("리소스를 찾을 수 없음", ex.getMessage());
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ApiResponse handleDataIntegrityViolation(DataIntegrityViolationException ex) {
        log.error("데이터 무결성 위반: {}", ex.getMessage());
        return ApiResponse.error("데이터 충돌", "요청한 작업이 기존 데이터와 충돌합니다");
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ApiResponse handleGenericException(Exception ex) {
        log.error("예상치 못한 오류 발생", ex);
        return ApiResponse.error("내부 서버 오류", "예상치 못한 오류가 발생했습니다");
    }
}
```

## 데이터베이스 최적화

### 커넥션 풀 설정

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

### JPA 성능 튜닝

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

    // 생성자, getters, setters
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

## 모니터링과 관찰 가능성

### Actuator 설정

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

### 커스텀 헬스 인디케이터

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
                    .withDetail("database", "사용 가능")
                    .withDetail("validationQuery", "SELECT 1")
                    .build();
            }
        } catch (SQLException e) {
            return Health.down()
                .withDetail("database", "사용 불가")
                .withException(e)
                .build();
        }
        return Health.down().withDetail("database", "연결 검증 실패").build();
    }
}
```

### 애플리케이션 메트릭

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
            .description("생성된 사용자 수")
            .register(meterRegistry);
        this.userFetchTimer = Timer.builder("user.fetch.time")
            .description("사용자 조회 소요 시간")
            .register(meterRegistry);
    }

    public User createUser(CreateUserRequest request) {
        return userFetchTimer.recordCallable(() -> {
            User user = new User(request.getEmail(), request.getName());
            User savedUser = userRepository.save(user);
            userCreationCounter.increment();
            log.info("사용자 생성 완료 ID: {}", savedUser.getId());
            return savedUser;
        });
    }
}
```

## 테스트 베스트 프랙티스

### 통합 테스트

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
    void 사용자_생성_테스트() {
        CreateUserRequest request = new CreateUserRequest("test@example.com", "테스트 사용자");

        ResponseEntity<User> response = restTemplate.postForEntity("/api/users", request, User.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody().getEmail()).isEqualTo("test@example.com");
        assertThat(userRepository.count()).isEqualTo(1);
    }
}
```

### 목킹을 활용한 단위 테스트

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
    void 사용자_생성_성공_테스트() {
        // Given
        CreateUserRequest request = new CreateUserRequest("test@example.com", "테스트 사용자");
        User savedUser = new User("test@example.com", "테스트 사용자");
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

## 성능 최적화

### 캐싱 전략

```java
@Service
@EnableCaching
public class UserService {

    @Cacheable(value = "users", key = "#id")
    public User findById(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("사용자를 찾을 수 없습니다"));
    }

    @CacheEvict(value = "users", key = "#user.id")
    public User updateUser(User user) {
        return userRepository.save(user);
    }

    @CacheEvict(value = "users", allEntries = true)
    public void clearUserCache() {
        // 캐시가 클리어됩니다
    }
}
```

### 비동기 처리

```java
@Service
@Slf4j
public class EmailService {

    @Async("taskExecutor")
    public CompletableFuture<Void> sendWelcomeEmail(String email, String name) {
        try {
            // 이메일 발송 시뮬레이션
            Thread.sleep(2000);
            log.info("환영 이메일 발송 완료: {}", email);
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

이러한 관례들을 통해 Spring Boot 애플리케이션이 프로덕션에서 안전하고 유지보수 가능하도록 보장할 수 있습니다. 점진적으로 구현하면서 특정 요구사항에 맞게 조정하시기 바랍니다.

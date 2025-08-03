---
title: "Spring Boot를 활용한 마이크로서비스 아키텍처"
meta_title: ""
description: "Spring Boot와 Spring Cloud를 사용하여 확장 가능한 마이크로서비스 아키텍처를 구축하는 방법을 알아봅니다."
date: 2022-04-06T05:00:00Z
image: "/images/service-3.png"
categories: ["백엔드", "아키텍처"]
author: "Kigo"
tags: ["Spring Boot", "마이크로서비스", "Spring Cloud", "아키텍처"]
draft: false
---

모놀리식 애플리케이션의 한계를 넘어 확장 가능하고 유연한 시스템을 구축하기 위해 마이크로서비스 아키텍처가 주목받고 있습니다. Spring Boot와 Spring Cloud 생태계를 활용하여 실제 운영 환경에서 사용할 수 있는 마이크로서비스를 구축하는 방법을 알아보겠습니다.

## 마이크로서비스 아키텍처 개요

### 서비스 분해 전략

```yaml
# 도메인별 서비스 분리 예시
services:
  user-service:
    responsibility: "사용자 관리, 인증"
    database: "user_db"
    port: 8081

  product-service:
    responsibility: "상품 관리, 카탈로그"
    database: "product_db"
    port: 8082

  order-service:
    responsibility: "주문 처리, 결제"
    database: "order_db"
    port: 8083

  notification-service:
    responsibility: "알림, 이메일 발송"
    database: "notification_db"
    port: 8084
```

## 서비스 디스커버리

### Eureka 서버 설정

```java
@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
```

```yaml
# application.yml (Eureka Server)
server:
  port: 8761

eureka:
  instance:
    hostname: localhost
  client:
    register-with-eureka: false
    fetch-registry: false
    service-url:
      defaultZone: http://${eureka.instance.hostname}:${server.port}/eureka/
  server:
    enable-self-preservation: false
```

### 서비스 등록 (클라이언트)

```java
@SpringBootApplication
@EnableEurekaClient
@EnableJpaAuditing
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
```

```yaml
# application.yml (User Service)
server:
  port: 8081

spring:
  application:
    name: user-service
  datasource:
    url: jdbc:postgresql://localhost:5432/user_db
    username: ${DB_USERNAME:user}
    password: ${DB_PASSWORD:password}

eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/
  instance:
    prefer-ip-address: true
    lease-renewal-interval-in-seconds: 30
    lease-expiration-duration-in-seconds: 90
```

## API 게이트웨이

### Spring Cloud Gateway 설정

```java
@SpringBootApplication
public class ApiGatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(ApiGatewayApplication.class, args);
    }

    @Bean
    public RouteLocator customRouteLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            .route("user-service", r -> r.path("/api/users/**")
                .filters(f -> f
                    .stripPrefix(1)
                    .addRequestHeader("X-Gateway-Name", "api-gateway")
                    .circuitBreaker(c -> c.setName("user-service-cb")))
                .uri("lb://user-service"))
            .route("product-service", r -> r.path("/api/products/**")
                .filters(f -> f
                    .stripPrefix(1)
                    .retry(3))
                .uri("lb://product-service"))
            .route("order-service", r -> r.path("/api/orders/**")
                .filters(f -> f
                    .stripPrefix(1)
                    .requestRateLimiter(c -> c
                        .setRateLimiter(redisRateLimiter())
                        .setKeyResolver(userKeyResolver())))
                .uri("lb://order-service"))
            .build();
    }

    @Bean
    public RedisRateLimiter redisRateLimiter() {
        return new RedisRateLimiter(10, 20, 1);
    }

    @Bean
    public KeyResolver userKeyResolver() {
        return exchange -> exchange.getRequest()
            .getHeaders()
            .getFirst("X-User-Id") != null ?
            Mono.just(exchange.getRequest().getHeaders().getFirst("X-User-Id")) :
            Mono.just("anonymous");
    }
}
```

### 글로벌 필터

```java
@Component
@Slf4j
public class LoggingGlobalFilter implements GlobalFilter, Ordered {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getPath().pathWithinApplication().value();
        String method = request.getMethod().name();
        String correlationId = UUID.randomUUID().toString();

        log.info("요청 시작 - Method: {}, Path: {}, CorrelationId: {}",
                method, path, correlationId);

        // 요청에 상관관계 ID 추가
        ServerHttpRequest mutatedRequest = request.mutate()
            .header("X-Correlation-ID", correlationId)
            .build();

        ServerWebExchange mutatedExchange = exchange.mutate()
            .request(mutatedRequest)
            .build();

        long startTime = System.currentTimeMillis();

        return chain.filter(mutatedExchange)
            .doOnSuccess(aVoid -> {
                long duration = System.currentTimeMillis() - startTime;
                log.info("요청 완료 - Path: {}, Duration: {}ms, CorrelationId: {}",
                        path, duration, correlationId);
            })
            .doOnError(throwable -> {
                long duration = System.currentTimeMillis() - startTime;
                log.error("요청 실패 - Path: {}, Duration: {}ms, CorrelationId: {}, Error: {}",
                         path, duration, correlationId, throwable.getMessage());
            });
    }

    @Override
    public int getOrder() {
        return -1; // 가장 먼저 실행
    }
}
```

## 서비스 간 통신

### OpenFeign을 이용한 동기 통신

```java
@FeignClient(name = "user-service", fallback = UserServiceFallback.class)
public interface UserServiceClient {

    @GetMapping("/users/{userId}")
    UserDto getUser(@PathVariable("userId") Long userId);

    @PostMapping("/users")
    UserDto createUser(@RequestBody CreateUserRequest request);

    @GetMapping("/users/{userId}/profile")
    UserProfileDto getUserProfile(@PathVariable("userId") Long userId);
}

@Component
@Slf4j
public class UserServiceFallback implements UserServiceClient {

    @Override
    public UserDto getUser(Long userId) {
        log.warn("사용자 서비스 호출 실패, 폴백 실행 - userId: {}", userId);
        return UserDto.builder()
            .id(userId)
            .name("Unknown User")
            .email("unknown@example.com")
            .build();
    }

    @Override
    public UserDto createUser(CreateUserRequest request) {
        log.error("사용자 생성 서비스 호출 실패");
        throw new ServiceUnavailableException("사용자 서비스를 사용할 수 없습니다");
    }

    @Override
    public UserProfileDto getUserProfile(Long userId) {
        log.warn("사용자 프로필 서비스 호출 실패, 기본값 반환");
        return UserProfileDto.builder()
            .userId(userId)
            .displayName("Unknown")
            .build();
    }
}
```

### 비동기 메시지 통신 (RabbitMQ)

```java
@Configuration
@EnableRabbit
public class RabbitConfig {

    public static final String ORDER_EXCHANGE = "order.exchange";
    public static final String ORDER_CREATED_QUEUE = "order.created.queue";
    public static final String ORDER_CREATED_ROUTING_KEY = "order.created";

    @Bean
    public TopicExchange orderExchange() {
        return new TopicExchange(ORDER_EXCHANGE);
    }

    @Bean
    public Queue orderCreatedQueue() {
        return QueueBuilder.durable(ORDER_CREATED_QUEUE)
            .withArgument("x-dead-letter-exchange", "dlx.exchange")
            .withArgument("x-dead-letter-routing-key", "dlx.order.created")
            .build();
    }

    @Bean
    public Binding orderCreatedBinding() {
        return BindingBuilder
            .bind(orderCreatedQueue())
            .to(orderExchange())
            .with(ORDER_CREATED_ROUTING_KEY);
    }

    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);
        template.setMessageConverter(new Jackson2JsonMessageConverter());
        return template;
    }
}

// 메시지 발행 (Order Service)
@Service
@Slf4j
public class OrderEventPublisher {

    private final RabbitTemplate rabbitTemplate;

    public void publishOrderCreated(OrderCreatedEvent event) {
        try {
            rabbitTemplate.convertAndSend(
                RabbitConfig.ORDER_EXCHANGE,
                RabbitConfig.ORDER_CREATED_ROUTING_KEY,
                event
            );
            log.info("주문 생성 이벤트 발행 완료 - orderId: {}", event.getOrderId());
        } catch (Exception e) {
            log.error("주문 생성 이벤트 발행 실패 - orderId: {}", event.getOrderId(), e);
            throw new EventPublishException("이벤트 발행에 실패했습니다", e);
        }
    }
}

// 메시지 구독 (Notification Service)
@RabbitListener(queues = RabbitConfig.ORDER_CREATED_QUEUE)
@Component
@Slf4j
public class OrderEventListener {

    private final NotificationService notificationService;
    private final UserServiceClient userServiceClient;

    @RabbitHandler
    public void handleOrderCreated(OrderCreatedEvent event) {
        try {
            log.info("주문 생성 이벤트 수신 - orderId: {}", event.getOrderId());

            UserDto user = userServiceClient.getUser(event.getUserId());

            NotificationRequest notification = NotificationRequest.builder()
                .userId(event.getUserId())
                .email(user.getEmail())
                .type(NotificationType.ORDER_CONFIRMATION)
                .title("주문이 접수되었습니다")
                .content(String.format("주문번호 %s가 성공적으로 접수되었습니다.", event.getOrderId()))
                .build();

            notificationService.sendNotification(notification);

        } catch (Exception e) {
            log.error("주문 생성 이벤트 처리 실패 - orderId: {}", event.getOrderId(), e);
            throw new MessageProcessingException("메시지 처리에 실패했습니다", e);
        }
    }
}
```

## 서킷 브레이커 패턴

### Resilience4j 설정

```java
@Configuration
public class ResilienceConfig {

    @Bean
    public CircuitBreaker userServiceCircuitBreaker() {
        return CircuitBreaker.of("user-service", CircuitBreakerConfig.custom()
            .failureRateThreshold(50)
            .waitDurationInOpenState(Duration.ofSeconds(30))
            .slidingWindowSize(10)
            .minimumNumberOfCalls(5)
            .slowCallRateThreshold(50)
            .slowCallDurationThreshold(Duration.ofSeconds(2))
            .build());
    }

    @Bean
    public Retry userServiceRetry() {
        return Retry.of("user-service", RetryConfig.custom()
            .maxAttempts(3)
            .waitDuration(Duration.ofSeconds(1))
            .retryExceptions(ConnectException.class, SocketTimeoutException.class)
            .build());
    }

    @Bean
    public TimeLimiter userServiceTimeLimiter() {
        return TimeLimiter.of("user-service", TimeLimiterConfig.custom()
            .timeoutDuration(Duration.ofSeconds(3))
            .build());
    }
}

@Service
public class OrderService {

    private final UserServiceClient userServiceClient;
    private final CircuitBreaker circuitBreaker;
    private final Retry retry;

    public Order createOrder(CreateOrderRequest request) {
        // 사용자 정보 조회 with Circuit Breaker + Retry
        UserDto user = Decorators.ofSupplier(() -> userServiceClient.getUser(request.getUserId()))
            .withCircuitBreaker(circuitBreaker)
            .withRetry(retry)
            .withFallback(Arrays.asList(Exception.class),
                ex -> createDefaultUser(request.getUserId()))
            .get();

        // 주문 생성 로직
        Order order = Order.builder()
            .userId(user.getId())
            .productId(request.getProductId())
            .quantity(request.getQuantity())
            .status(OrderStatus.CREATED)
            .build();

        return orderRepository.save(order);
    }

    private UserDto createDefaultUser(Long userId) {
        return UserDto.builder()
            .id(userId)
            .name("Guest User")
            .email("guest@example.com")
            .build();
    }
}
```

## 분산 설정 관리

### Spring Cloud Config

```java
// Config Server
@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }
}
```

```yaml
# Config Server - application.yml
server:
  port: 8888

spring:
  cloud:
    config:
      server:
        git:
          uri: https://github.com/your-org/config-repo
          clone-on-start: true
          default-label: main
        encrypt:
          enabled: false
```

```yaml
# Config Repository - user-service.yml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/user_db
    username: ${DB_USERNAME}
    password: '{cipher}AQA3mHJz5RQ...' # 암호화된 비밀번호

# user-service-prod.yml
spring:
  datasource:
    url: jdbc:postgresql://prod-db:5432/user_db
    hikari:
      maximum-pool-size: 20
      minimum-idle: 5

logging:
  level:
    com.kigo.userservice: INFO
```

## 분산 추적

### Sleuth + Zipkin 설정

```yaml
# 각 서비스의 application.yml
spring:
  sleuth:
    sampler:
      probability: 1.0 # 개발 환경에서는 100% 샘플링
    zipkin:
      base-url: http://localhost:9411
      enabled: true
  application:
    name: user-service
```

```java
@RestController
@Slf4j
public class UserController {

    private final UserService userService;
    private final Tracer tracer;

    @GetMapping("/users/{id}")
    public ResponseEntity<UserDto> getUser(@PathVariable Long id) {
        Span customSpan = tracer.nextSpan()
            .name("get-user-operation")
            .tag("user.id", String.valueOf(id))
            .start();

        try (Tracer.SpanInScope ws = tracer.withSpanInScope(customSpan)) {
            log.info("사용자 조회 요청 - userId: {}", id);
            UserDto user = userService.findById(id);
            customSpan.tag("user.found", "true");
            return ResponseEntity.ok(user);
        } catch (Exception e) {
            customSpan.tag("error", e.getMessage());
            throw e;
        } finally {
            customSpan.end();
        }
    }
}
```

## 모니터링과 헬스 체크

### Actuator 설정

```yaml
# 각 서비스의 공통 설정
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus,refresh
  endpoint:
    health:
      show-details: always
  health:
    circuitbreakers:
      enabled: true
  metrics:
    export:
      prometheus:
        enabled: true
    distribution:
      percentiles-histogram:
        http.server.requests: true
```

```java
@Component
public class CustomHealthIndicator implements HealthIndicator {

    private final UserRepository userRepository;

    @Override
    public Health health() {
        try {
            long userCount = userRepository.count();
            if (userCount >= 0) {
                return Health.up()
                    .withDetail("database", "사용 가능")
                    .withDetail("userCount", userCount)
                    .build();
            }
        } catch (Exception e) {
            return Health.down()
                .withDetail("database", "사용 불가")
                .withException(e)
                .build();
        }
        return Health.down().build();
    }
}
```

## 통합 테스트

```java
@SpringBootTest
@TestPropertySource(properties = {
    "spring.cloud.config.enabled=false",
    "eureka.client.enabled=false"
})
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class UserServiceIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:13")
            .withDatabaseName("test_db")
            .withUsername("test")
            .withPassword("test");

    @MockBean
    private ProductServiceClient productServiceClient;

    @Autowired
    private TestRestTemplate restTemplate;

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Test
    void 사용자_생성_및_조회_통합_테스트() {
        // Given
        CreateUserRequest request = new CreateUserRequest("test@example.com", "Test User");

        // When - 사용자 생성
        ResponseEntity<UserDto> createResponse = restTemplate.postForEntity(
            "/api/users", request, UserDto.class);

        // Then
        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        UserDto createdUser = createResponse.getBody();
        assertThat(createdUser.getEmail()).isEqualTo("test@example.com");

        // When - 사용자 조회
        ResponseEntity<UserDto> getResponse = restTemplate.getForEntity(
            "/api/users/" + createdUser.getId(), UserDto.class);

        // Then
        assertThat(getResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(getResponse.getBody().getId()).isEqualTo(createdUser.getId());
    }
}
```

이러한 패턴과 설정을 통해 확장 가능하고 견고한 마이크로서비스 아키텍처를 구축할 수 있습니다. 각 서비스는 독립적으로 개발, 배포, 확장이 가능하며, 장애 격리와 복원력을 갖춘 시스템을 만들 수 있습니다.

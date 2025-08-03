---
title: "Microservices Architecture with Spring Boot"
meta_title: ""
description: "Learn how to build scalable microservices architecture using Spring Boot and Spring Cloud framework."
date: 2022-04-06T05:00:00Z
image: "/images/service-3.png"
categories: ["Backend", "Architecture"]
author: "Kigo"
tags: ["Spring Boot", "Microservices", "Spring Cloud", "Architecture"]
draft: false
---

To overcome the limitations of monolithic applications and build scalable and flexible systems, microservices architecture is gaining attention. Let's explore how to build microservices that can be used in actual production environments using the Spring Boot and Spring Cloud ecosystem.

## Microservices Architecture Overview

### Service Decomposition Strategy

```yaml
# Example of domain-based service separation
services:
  user-service:
    responsibility: "User management, authentication"
    database: "user_db"
    port: 8081

  product-service:
    responsibility: "Product management, catalog"
    database: "product_db"
    port: 8082

  order-service:
    responsibility: "Order processing, payment"
    database: "order_db"
    port: 8083

  notification-service:
    responsibility: "Notifications, email sending"
    database: "notification_db"
    port: 8084
```

## Service Discovery

### Eureka Server Setup

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

### Service Registration (Client)

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

## API Gateway

### Spring Cloud Gateway Configuration

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

### Global Filter

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

        log.info("Request started - Method: {}, Path: {}, CorrelationId: {}",
                method, path, correlationId);

        // Add correlation ID to request
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
                log.info("Request completed - Path: {}, Duration: {}ms, CorrelationId: {}",
                        path, duration, correlationId);
            })
            .doOnError(throwable -> {
                long duration = System.currentTimeMillis() - startTime;
                log.error("Request failed - Path: {}, Duration: {}ms, CorrelationId: {}, Error: {}",
                         path, duration, correlationId, throwable.getMessage());
            });
    }

    @Override
    public int getOrder() {
        return -1; // Execute first
    }
}
```

## Inter-Service Communication

### Synchronous Communication with OpenFeign

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
        log.warn("User service call failed, executing fallback - userId: {}", userId);
        return UserDto.builder()
            .id(userId)
            .name("Unknown User")
            .email("unknown@example.com")
            .build();
    }

    @Override
    public UserDto createUser(CreateUserRequest request) {
        log.error("User creation service call failed");
        throw new ServiceUnavailableException("User service is unavailable");
    }

    @Override
    public UserProfileDto getUserProfile(Long userId) {
        log.warn("User profile service call failed, returning default values");
        return UserProfileDto.builder()
            .userId(userId)
            .displayName("Unknown")
            .build();
    }
}
```

### Asynchronous Message Communication (RabbitMQ)

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

// Message Publishing (Order Service)
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
            log.info("Order created event published - orderId: {}", event.getOrderId());
        } catch (Exception e) {
            log.error("Order created event publishing failed - orderId: {}", event.getOrderId(), e);
            throw new EventPublishException("Failed to publish event", e);
        }
    }
}

// Message Subscription (Notification Service)
@RabbitListener(queues = RabbitConfig.ORDER_CREATED_QUEUE)
@Component
@Slf4j
public class OrderEventListener {

    private final NotificationService notificationService;
    private final UserServiceClient userServiceClient;

    @RabbitHandler
    public void handleOrderCreated(OrderCreatedEvent event) {
        try {
            log.info("Order created event received - orderId: {}", event.getOrderId());

            UserDto user = userServiceClient.getUser(event.getUserId());

            NotificationRequest notification = NotificationRequest.builder()
                .userId(event.getUserId())
                .email(user.getEmail())
                .type(NotificationType.ORDER_CONFIRMATION)
                .title("Your order has been received")
                .content(String.format("Order number %s has been successfully received.", event.getOrderId()))
                .build();

            notificationService.sendNotification(notification);

        } catch (Exception e) {
            log.error("Order created event processing failed - orderId: {}", event.getOrderId(), e);
            throw new MessageProcessingException("Failed to process message", e);
        }
    }
}
```

## Circuit Breaker Pattern

### Resilience4j Configuration

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
        // User information lookup with Circuit Breaker + Retry
        UserDto user = Decorators.ofSupplier(() -> userServiceClient.getUser(request.getUserId()))
            .withCircuitBreaker(circuitBreaker)
            .withRetry(retry)
            .withFallback(Arrays.asList(Exception.class),
                ex -> createDefaultUser(request.getUserId()))
            .get();

        // Order creation logic
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

## Distributed Configuration Management

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

## Distributed Tracing

### Sleuth + Zipkin Configuration

```yaml
# application.yml for each service
spring:
  sleuth:
    sampler:
      probability: 1.0 # 100% sampling in development
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
            log.info("User lookup request - userId: {}", id);
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

## Monitoring and Health Checks

### Actuator Configuration

```yaml
# Common configuration for each service
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
                    .withDetail("database", "Available")
                    .withDetail("userCount", userCount)
                    .build();
            }
        } catch (Exception e) {
            return Health.down()
                .withDetail("database", "Unavailable")
                .withException(e)
                .build();
        }
        return Health.down().build();
    }
}
```

## Integration Testing

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
    void user_creation_and_lookup_integration_test() {
        // Given
        CreateUserRequest request = new CreateUserRequest("test@example.com", "Test User");

        // When - Create user
        ResponseEntity<UserDto> createResponse = restTemplate.postForEntity(
            "/api/users", request, UserDto.class);

        // Then
        assertThat(createResponse.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        UserDto createdUser = createResponse.getBody();
        assertThat(createdUser.getEmail()).isEqualTo("test@example.com");

        // When - Get user
        ResponseEntity<UserDto> getResponse = restTemplate.getForEntity(
            "/api/users/" + createdUser.getId(), UserDto.class);

        // Then
        assertThat(getResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(getResponse.getBody().getId()).isEqualTo(createdUser.getId());
    }
}
```

Through these patterns and configurations, you can build scalable and robust microservices architecture. Each service can be developed, deployed, and scaled independently, creating systems with fault isolation and resilience.

---
title: "Microservices Architecture with Spring Boot"
meta_title: ""
description: "Learn how to design and implement microservices architecture using Spring Boot, Spring Cloud, and modern patterns."
date: 2022-04-06T05:00:00Z
image: "/images/service-3.png"
categories: ["Architecture", "Backend"]
author: "Kigo"
tags: ["Microservices", "Spring Boot", "Spring Cloud", "Architecture", "Distributed Systems"]
draft: false
---

Microservices architecture has become the preferred approach for building scalable, maintainable applications. Let's explore how to implement microservices using Spring Boot and Spring Cloud.

## What are Microservices?

Microservices are small, independent services that communicate over well-defined APIs. Each service owns its data and business logic, making the system more resilient and scalable.

### Benefits
- **Scalability**: Scale individual services based on demand
- **Technology Diversity**: Use different technologies for different services
- **Team Independence**: Teams can work independently on services
- **Fault Isolation**: Failure in one service doesn't bring down the entire system

### Challenges
- **Complexity**: Distributed systems are inherently complex
- **Network Latency**: Inter-service communication overhead
- **Data Consistency**: Managing transactions across services
- **Monitoring**: Observing distributed system behavior

## Spring Cloud Overview

Spring Cloud provides tools for common patterns in distributed systems:

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-dependencies</artifactId>
            <version>2023.0.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <!-- Service Discovery -->
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
    </dependency>

    <!-- Circuit Breaker -->
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-circuitbreaker-resilience4j</artifactId>
    </dependency>

    <!-- API Gateway -->
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-gateway</artifactId>
    </dependency>

    <!-- Configuration -->
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-config</artifactId>
    </dependency>
</dependencies>
```

## Service Discovery with Eureka

### Eureka Server

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
# eureka-server application.yml
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
```

### Eureka Client (Service)

```java
@SpringBootApplication
@EnableEurekaClient
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
```

```yaml
# user-service application.yml
server:
  port: 8081

spring:
  application:
    name: user-service

eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/
  instance:
    prefer-ip-address: true
```

## API Gateway

Central entry point for all client requests:

```java
@SpringBootApplication
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}
```

```yaml
# gateway application.yml
server:
  port: 8080

spring:
  application:
    name: api-gateway
  cloud:
    gateway:
      discovery:
        locator:
          enabled: true
          lower-case-service-id: true
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
          filters:
            - StripPrefix=1
        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/api/orders/**
          filters:
            - StripPrefix=1

eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/
```

## Inter-Service Communication

### Synchronous Communication with OpenFeign

```java
@FeignClient(name = "user-service")
public interface UserServiceClient {

    @GetMapping("/users/{userId}")
    UserDto getUser(@PathVariable Long userId);

    @PostMapping("/users")
    UserDto createUser(@RequestBody CreateUserRequest request);
}

@Service
public class OrderService {

    private final UserServiceClient userServiceClient;
    private final OrderRepository orderRepository;

    public OrderService(UserServiceClient userServiceClient, OrderRepository orderRepository) {
        this.userServiceClient = userServiceClient;
        this.orderRepository = orderRepository;
    }

    public Order createOrder(CreateOrderRequest request) {
        // Validate user exists
        UserDto user = userServiceClient.getUser(request.getUserId());

        Order order = new Order(request.getUserId(), request.getItems());
        return orderRepository.save(order);
    }
}
```

### Asynchronous Communication with RabbitMQ

```java
@Configuration
@EnableRabbit
public class RabbitConfig {

    @Bean
    public TopicExchange orderExchange() {
        return new TopicExchange("order.exchange");
    }

    @Bean
    public Queue orderCreatedQueue() {
        return QueueBuilder.durable("order.created.queue").build();
    }

    @Bean
    public Binding orderCreatedBinding() {
        return BindingBuilder
                .bind(orderCreatedQueue())
                .to(orderExchange())
                .with("order.created");
    }
}

// Publisher (Order Service)
@Service
public class OrderEventPublisher {

    private final RabbitTemplate rabbitTemplate;

    public void publishOrderCreated(Order order) {
        OrderCreatedEvent event = new OrderCreatedEvent(
            order.getId(),
            order.getUserId(),
            order.getTotalAmount()
        );

        rabbitTemplate.convertAndSend(
            "order.exchange",
            "order.created",
            event
        );
    }
}

// Consumer (Inventory Service)
@Component
public class OrderEventListener {

    private final InventoryService inventoryService;

    @RabbitListener(queues = "order.created.queue")
    public void handleOrderCreated(OrderCreatedEvent event) {
        inventoryService.reserveItems(event.getOrderId(), event.getItems());
    }
}
```

## Circuit Breaker Pattern

Prevent cascading failures using Resilience4j:

```java
@Service
public class OrderService {

    private final UserServiceClient userServiceClient;

    @CircuitBreaker(name = "user-service", fallbackMethod = "fallbackGetUser")
    @Retry(name = "user-service")
    @TimeLimiter(name = "user-service")
    public CompletableFuture<UserDto> getUser(Long userId) {
        return CompletableFuture.supplyAsync(() -> userServiceClient.getUser(userId));
    }

    public CompletableFuture<UserDto> fallbackGetUser(Long userId, Exception ex) {
        return CompletableFuture.completedFuture(
            new UserDto(userId, "Unknown User", "unknown@example.com")
        );
    }
}
```

```yaml
# Circuit breaker configuration
resilience4j:
  circuitbreaker:
    instances:
      user-service:
        register-health-indicator: true
        sliding-window-size: 10
        minimum-number-of-calls: 5
        permitted-number-of-calls-in-half-open-state: 3
        automatic-transition-from-open-to-half-open-enabled: true
        wait-duration-in-open-state: 5s
        failure-rate-threshold: 50
        event-consumer-buffer-size: 10
  retry:
    instances:
      user-service:
        max-attempts: 3
        wait-duration: 500ms
  timelimiter:
    instances:
      user-service:
        timeout-duration: 2s
```

## Distributed Configuration

### Config Server

```java
@SpringBootApplication
@EnableConfigServer
public class ConfigServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(ConfigServerApplication.class, args);
    }
}
```

```yaml
# config-server application.yml
server:
  port: 8888

spring:
  cloud:
    config:
      server:
        git:
          uri: https://github.com/your-org/config-repo
          search-paths: config
```

### Config Client

```yaml
# bootstrap.yml
spring:
  application:
    name: user-service
  cloud:
    config:
      uri: http://localhost:8888
      fail-fast: true
```

## Distributed Tracing

### Sleuth and Zipkin

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-sleuth</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-sleuth-zipkin</artifactId>
</dependency>
```

```yaml
spring:
  sleuth:
    sampler:
      probability: 1.0
  zipkin:
    base-url: http://localhost:9411
```

## Data Management Patterns

### Database per Service

```java
// User Service - User Database
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String email;
    private String name;
    // No foreign keys to other services
}

// Order Service - Order Database
@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private Long userId; // Reference by ID only
    private BigDecimal totalAmount;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> items;
}
```

### Saga Pattern for Distributed Transactions

```java
@Component
public class OrderSaga {

    private final PaymentService paymentService;
    private final InventoryService inventoryService;
    private final OrderService orderService;

    @SagaOrchestrationStart
    public void processOrder(CreateOrderCommand command) {
        // Step 1: Reserve inventory
        reserveInventory(command.getOrderId(), command.getItems());
    }

    @SagaOrchestrationParticipant
    public void reserveInventory(Long orderId, List<OrderItem> items) {
        try {
            inventoryService.reserve(orderId, items);
            // Success - proceed to payment
            processPayment(orderId);
        } catch (Exception e) {
            // Compensation - cancel order
            cancelOrder(orderId);
        }
    }

    @SagaOrchestrationParticipant
    public void processPayment(Long orderId) {
        try {
            paymentService.charge(orderId);
            // Success - confirm order
            confirmOrder(orderId);
        } catch (Exception e) {
            // Compensation - release inventory and cancel order
            releaseInventory(orderId);
            cancelOrder(orderId);
        }
    }
}
```

## Monitoring and Observability

### Metrics with Micrometer

```java
@RestController
public class UserController {

    private final UserService userService;
    private final MeterRegistry meterRegistry;
    private final Counter userCreationCounter;

    public UserController(UserService userService, MeterRegistry meterRegistry) {
        this.userService = userService;
        this.meterRegistry = meterRegistry;
        this.userCreationCounter = Counter.builder("users.created")
            .description("Number of users created")
            .register(meterRegistry);
    }

    @PostMapping("/users")
    @Timed(name = "user.creation.time", description = "Time spent creating user")
    public ResponseEntity<User> createUser(@RequestBody CreateUserRequest request) {
        User user = userService.createUser(request);
        userCreationCounter.increment();
        return ResponseEntity.ok(user);
    }
}
```

### Health Checks

```java
@Component
public class DatabaseHealthIndicator implements HealthIndicator {

    private final DataSource dataSource;

    @Override
    public Health health() {
        try (Connection connection = dataSource.getConnection()) {
            if (connection.isValid(1)) {
                return Health.up().withDetail("database", "Available").build();
            }
        } catch (SQLException e) {
            return Health.down(e).build();
        }
        return Health.down().withDetail("database", "Connection failed").build();
    }
}
```

## Security in Microservices

### JWT Token Validation

```java
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider tokenProvider;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                  HttpServletResponse response,
                                  FilterChain filterChain) throws ServletException, IOException {

        String token = extractToken(request);

        if (token != null && tokenProvider.validateToken(token)) {
            Authentication auth = tokenProvider.getAuthentication(token);
            SecurityContextHolder.getContext().setAuthentication(auth);
        }

        filterChain.doFilter(request, response);
    }

    private String extractToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (bearerToken != null && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
```

## Deployment Strategies

### Docker Compose for Development

```yaml
version: '3.8'
services:
  eureka-server:
    build: ./eureka-server
    ports:
      - "8761:8761"

  config-server:
    build: ./config-server
    ports:
      - "8888:8888"
    depends_on:
      - eureka-server

  user-service:
    build: ./user-service
    ports:
      - "8081:8081"
    depends_on:
      - eureka-server
      - config-server
    environment:
      - EUREKA_CLIENT_SERVICE_URL_DEFAULTZONE=http://eureka-server:8761/eureka
      - SPRING_CLOUD_CONFIG_URI=http://config-server:8888

  order-service:
    build: ./order-service
    ports:
      - "8082:8082"
    depends_on:
      - eureka-server
      - config-server
      - user-service
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: user-service:latest
        ports:
        - containerPort: 8081
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "kubernetes"
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 8081
    targetPort: 8081
  type: ClusterIP
```

## Best Practices

1. **Start with Modular Monolith**: Don't begin with microservices
2. **Domain-Driven Design**: Align services with business capabilities
3. **API Versioning**: Version your APIs to maintain backward compatibility
4. **Circuit Breakers**: Implement fault tolerance patterns
5. **Centralized Logging**: Use ELK stack or similar for log aggregation
6. **Monitoring**: Implement comprehensive monitoring and alerting
7. **Security**: Secure service-to-service communication
8. **Testing**: Include contract testing between services

Microservices architecture offers significant benefits but comes with complexity. Start simple, evolve gradually, and focus on observability and resilience from the beginning.

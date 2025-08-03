---
title: "REST API Design Best Practices"
meta_title: ""
description: "Learn essential REST API design principles and best practices for building maintainable and scalable web services."
date: 2022-04-07T05:00:00Z
image: "/images/service-1.png"
categories: ["Backend", "API Design"]
author: "Kigo"
tags: ["REST API", "API Design", "Web Services", "Backend", "HTTP"]
draft: false
---

Well-designed REST APIs are crucial for building maintainable and scalable applications. Let's explore the essential principles and best practices for creating robust APIs.

## REST Principles

### 1. Resource-Based URLs

Use nouns to represent resources, not verbs:

```
✅ Good
GET /api/users
GET /api/users/123
POST /api/users
PUT /api/users/123
DELETE /api/users/123

❌ Bad
GET /api/getUsers
GET /api/getUserById/123
POST /api/createUser
PUT /api/updateUser/123
DELETE /api/deleteUser/123
```

### 2. HTTP Methods

Use appropriate HTTP methods for different operations:

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    // GET - Retrieve resources
    @GetMapping
    public ResponseEntity<Page<UserDto>> getUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {
        // Implementation
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserDto> getUser(@PathVariable Long id) {
        // Implementation
    }

    // POST - Create new resource
    @PostMapping
    public ResponseEntity<UserDto> createUser(@RequestBody @Valid CreateUserRequest request) {
        // Implementation
    }

    // PUT - Update entire resource
    @PutMapping("/{id}")
    public ResponseEntity<UserDto> updateUser(
            @PathVariable Long id,
            @RequestBody @Valid UpdateUserRequest request) {
        // Implementation
    }

    // PATCH - Partial update
    @PatchMapping("/{id}")
    public ResponseEntity<UserDto> patchUser(
            @PathVariable Long id,
            @RequestBody Map<String, Object> updates) {
        // Implementation
    }

    // DELETE - Remove resource
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        // Implementation
    }
}
```

## URL Design Patterns

### Hierarchical Resources

```
/api/users/{userId}/orders
/api/users/{userId}/orders/{orderId}
/api/orders/{orderId}/items
/api/orders/{orderId}/items/{itemId}
```

### Query Parameters for Filtering and Pagination

```java
@GetMapping("/api/products")
public ResponseEntity<PagedResponse<ProductDto>> getProducts(
        @RequestParam(required = false) String category,
        @RequestParam(required = false) BigDecimal minPrice,
        @RequestParam(required = false) BigDecimal maxPrice,
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size,
        @RequestParam(defaultValue = "id") String sortBy,
        @RequestParam(defaultValue = "asc") String sortDir) {

    ProductFilter filter = ProductFilter.builder()
        .category(category)
        .minPrice(minPrice)
        .maxPrice(maxPrice)
        .build();

    Pageable pageable = PageRequest.of(page, size,
        Sort.Direction.fromString(sortDir), sortBy);

    Page<Product> products = productService.findProducts(filter, pageable);

    return ResponseEntity.ok(PagedResponse.of(products));
}
```

## Response Design

### Standard Response Structure

```java
public class ApiResponse<T> {
    private boolean success;
    private String message;
    private T data;
    private String timestamp;
    private List<String> errors;

    public static <T> ApiResponse<T> success(T data) {
        return ApiResponse.<T>builder()
            .success(true)
            .data(data)
            .timestamp(Instant.now().toString())
            .build();
    }

    public static <T> ApiResponse<T> error(String message, List<String> errors) {
        return ApiResponse.<T>builder()
            .success(false)
            .message(message)
            .errors(errors)
            .timestamp(Instant.now().toString())
            .build();
    }
}

// Paginated response
public class PagedResponse<T> {
    private List<T> content;
    private int page;
    private int size;
    private long totalElements;
    private int totalPages;
    private boolean first;
    private boolean last;

    public static <T> PagedResponse<T> of(Page<T> page) {
        return PagedResponse.<T>builder()
            .content(page.getContent())
            .page(page.getNumber())
            .size(page.getSize())
            .totalElements(page.getTotalElements())
            .totalPages(page.getTotalPages())
            .first(page.isFirst())
            .last(page.isLast())
            .build();
    }
}
```

### HTTP Status Codes

```java
@RestController
public class UserController {

    @PostMapping("/users")
    public ResponseEntity<UserDto> createUser(@RequestBody @Valid CreateUserRequest request) {
        UserDto user = userService.createUser(request);
        URI location = ServletUriComponentsBuilder
            .fromCurrentRequest()
            .path("/{id}")
            .buildAndExpand(user.getId())
            .toUri();

        return ResponseEntity
            .created(location)  // 201 Created
            .body(user);
    }

    @GetMapping("/users/{id}")
    public ResponseEntity<UserDto> getUser(@PathVariable Long id) {
        Optional<UserDto> user = userService.findById(id);
        return user
            .map(u -> ResponseEntity.ok(u))  // 200 OK
            .orElse(ResponseEntity.notFound().build());  // 404 Not Found
    }

    @PutMapping("/users/{id}")
    public ResponseEntity<UserDto> updateUser(@PathVariable Long id,
                                            @RequestBody @Valid UpdateUserRequest request) {
        try {
            UserDto user = userService.updateUser(id, request);
            return ResponseEntity.ok(user);  // 200 OK
        } catch (UserNotFoundException e) {
            return ResponseEntity.notFound().build();  // 404 Not Found
        }
    }

    @DeleteMapping("/users/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        try {
            userService.deleteUser(id);
            return ResponseEntity.noContent().build();  // 204 No Content
        } catch (UserNotFoundException e) {
            return ResponseEntity.notFound().build();  // 404 Not Found
        }
    }
}
```

## Error Handling

### Global Exception Handler

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ApiResponse<Void> handleValidationExceptions(MethodArgumentNotValidException ex) {
        List<String> errors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .collect(Collectors.toList());

        return ApiResponse.error("Validation failed", errors);
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ApiResponse<Void> handleResourceNotFoundException(ResourceNotFoundException ex) {
        return ApiResponse.error(ex.getMessage(), List.of());
    }

    @ExceptionHandler(ConflictException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ApiResponse<Void> handleConflictException(ConflictException ex) {
        return ApiResponse.error(ex.getMessage(), List.of());
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ApiResponse<Void> handleGenericException(Exception ex) {
        log.error("Unexpected error occurred", ex);
        return ApiResponse.error("Internal server error", List.of());
    }
}

// Custom exceptions
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}

public class ConflictException extends RuntimeException {
    public ConflictException(String message) {
        super(message);
    }
}
```

## Input Validation

### Request DTOs with Validation

```java
public class CreateUserRequest {

    @NotBlank(message = "Email is required")
    @Email(message = "Email must be valid")
    private String email;

    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 50, message = "Name must be between 2 and 50 characters")
    private String name;

    @Past(message = "Date of birth must be in the past")
    private LocalDate dateOfBirth;

    @Valid
    @NotNull(message = "Address is required")
    private AddressDto address;

    // getters, setters
}

public class AddressDto {

    @NotBlank(message = "Street is required")
    private String street;

    @NotBlank(message = "City is required")
    private String city;

    @Pattern(regexp = "\\d{5}", message = "Postal code must be 5 digits")
    private String postalCode;

    // getters, setters
}

// Custom validator
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = UniqueEmailValidator.class)
public @interface UniqueEmail {
    String message() default "Email already exists";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

@Component
public class UniqueEmailValidator implements ConstraintValidator<UniqueEmail, String> {

    @Autowired
    private UserRepository userRepository;

    @Override
    public boolean isValid(String email, ConstraintValidatorContext context) {
        return email != null && !userRepository.existsByEmail(email);
    }
}
```

## Content Negotiation

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping(produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
    public ResponseEntity<List<UserDto>> getUsers() {
        // Returns JSON or XML based on Accept header
        List<UserDto> users = userService.findAll();
        return ResponseEntity.ok(users);
    }

    @PostMapping(
        consumes = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE},
        produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE}
    )
    public ResponseEntity<UserDto> createUser(@RequestBody CreateUserRequest request) {
        UserDto user = userService.createUser(request);
        return ResponseEntity.ok(user);
    }
}
```

## Security Best Practices

### Authentication and Authorization

```java
@Configuration
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(authz -> authz
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers(HttpMethod.GET, "/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()));

        return http.build();
    }
}

@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping
    @PreAuthorize("hasRole('USER') or hasRole('ADMIN')")
    public ResponseEntity<List<UserDto>> getUsers() {
        // Implementation
    }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UserDto> createUser(@RequestBody CreateUserRequest request) {
        // Implementation
    }

    @GetMapping("/me")
    public ResponseEntity<UserDto> getCurrentUser(Authentication authentication) {
        String username = authentication.getName();
        UserDto user = userService.findByUsername(username);
        return ResponseEntity.ok(user);
    }
}
```

### Rate Limiting

```java
@Configuration
public class RateLimitConfig {

    @Bean
    public RedisTemplate<String, String> redisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<String, String> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);
        template.setDefaultSerializer(new StringRedisSerializer());
        return template;
    }
}

@Component
public class RateLimitInterceptor implements HandlerInterceptor {

    private final RedisTemplate<String, String> redisTemplate;

    @Override
    public boolean preHandle(HttpServletRequest request,
                           HttpServletResponse response,
                           Object handler) throws Exception {

        String clientId = getClientId(request);
        String key = "rate_limit:" + clientId;

        String requests = redisTemplate.opsForValue().get(key);

        if (requests == null) {
            redisTemplate.opsForValue().set(key, "1", Duration.ofMinutes(1));
        } else if (Integer.parseInt(requests) < 100) {
            redisTemplate.opsForValue().increment(key);
        } else {
            response.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            response.getWriter().write("Rate limit exceeded");
            return false;
        }

        return true;
    }

    private String getClientId(HttpServletRequest request) {
        // Extract client ID from JWT token or IP address
        return request.getRemoteAddr();
    }
}
```

## API Documentation

### OpenAPI/Swagger

```java
@Configuration
public class OpenAPIConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("User Management API")
                .version("1.0")
                .description("API for managing users")
                .contact(new Contact()
                    .name("API Team")
                    .email("api-team@example.com")))
            .servers(List.of(
                new Server().url("http://localhost:8080").description("Development server"),
                new Server().url("https://api.example.com").description("Production server")
            ))
            .components(new Components()
                .addSecuritySchemes("bearerAuth",
                    new SecurityScheme()
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")));
    }
}

@RestController
@RequestMapping("/api/users")
@Tag(name = "User Management", description = "Operations for managing users")
public class UserController {

    @Operation(
        summary = "Get all users",
        description = "Retrieve a paginated list of all users",
        responses = {
            @ApiResponse(responseCode = "200", description = "Successfully retrieved users"),
            @ApiResponse(responseCode = "401", description = "Unauthorized"),
            @ApiResponse(responseCode = "403", description = "Forbidden")
        }
    )
    @GetMapping
    public ResponseEntity<PagedResponse<UserDto>> getUsers(
            @Parameter(description = "Page number (0-based)") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "10") int size) {
        // Implementation
    }

    @Operation(summary = "Create a new user")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "201", description = "User created successfully"),
        @ApiResponse(responseCode = "400", description = "Invalid input"),
        @ApiResponse(responseCode = "409", description = "User already exists")
    })
    @PostMapping
    @SecurityRequirement(name = "bearerAuth")
    public ResponseEntity<UserDto> createUser(
            @Parameter(description = "User creation request") @RequestBody @Valid CreateUserRequest request) {
        // Implementation
    }
}
```

## Versioning Strategies

### URL Versioning

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserV1Controller {
    // Version 1 implementation
}

@RestController
@RequestMapping("/api/v2/users")
public class UserV2Controller {
    // Version 2 implementation
}
```

### Header Versioning

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping(headers = "API-Version=1")
    public ResponseEntity<List<UserV1Dto>> getUsersV1() {
        // Version 1 implementation
    }

    @GetMapping(headers = "API-Version=2")
    public ResponseEntity<List<UserV2Dto>> getUsersV2() {
        // Version 2 implementation
    }
}
```

## Testing APIs

### Integration Tests

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class UserControllerIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private UserRepository userRepository;

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:14")
            .withDatabaseName("testdb")
            .withUsername("test")
            .withPassword("test");

    @Test
    void shouldCreateUser() {
        CreateUserRequest request = new CreateUserRequest("test@example.com", "Test User");

        ResponseEntity<UserDto> response = restTemplate.postForEntity(
            "/api/users", request, UserDto.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody().getEmail()).isEqualTo("test@example.com");
        assertThat(userRepository.count()).isEqualTo(1);
    }

    @Test
    void shouldReturnValidationErrorForInvalidEmail() {
        CreateUserRequest request = new CreateUserRequest("invalid-email", "Test User");

        ResponseEntity<ApiResponse> response = restTemplate.postForEntity(
            "/api/users", request, ApiResponse.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody().isSuccess()).isFalse();
    }
}
```

### Contract Testing with WireMock

```java
@SpringBootTest
class UserServiceTest {

    @RegisterExtension
    static WireMockExtension wireMock = WireMockExtension.newInstance()
        .options(wireMockConfig().port(8089))
        .build();

    @Autowired
    private UserService userService;

    @Test
    void shouldCallExternalAPISuccessfully() {
        // Given
        wireMock.stubFor(get(urlEqualTo("/api/external/users/1"))
            .willReturn(aResponse()
                .withStatus(200)
                .withHeader("Content-Type", "application/json")
                .withBody("{\"id\":1,\"name\":\"External User\"}")));

        // When
        ExternalUser user = userService.fetchExternalUser(1L);

        // Then
        assertThat(user.getName()).isEqualTo("External User");
        wireMock.verify(getRequestedFor(urlEqualTo("/api/external/users/1")));
    }
}
```

## Performance Optimization

### Caching

```java
@Service
@CacheConfig(cacheNames = "users")
public class UserService {

    @Cacheable(key = "#id")
    public UserDto findById(Long id) {
        return userRepository.findById(id)
            .map(this::toDto)
            .orElseThrow(() -> new UserNotFoundException("User not found"));
    }

    @CacheEvict(key = "#userDto.id")
    public UserDto updateUser(UserDto userDto) {
        // Update logic
        return userDto;
    }

    @CacheEvict(allEntries = true)
    public void clearCache() {
        // Cache will be cleared
    }
}
```

### Pagination and Filtering

```java
@Service
public class ProductService {

    public Page<ProductDto> findProducts(ProductFilter filter, Pageable pageable) {
        Specification<Product> spec = Specification.where(null);

        if (filter.getCategory() != null) {
            spec = spec.and((root, query, cb) ->
                cb.equal(root.get("category"), filter.getCategory()));
        }

        if (filter.getMinPrice() != null) {
            spec = spec.and((root, query, cb) ->
                cb.greaterThanOrEqualTo(root.get("price"), filter.getMinPrice()));
        }

        if (filter.getMaxPrice() != null) {
            spec = spec.and((root, query, cb) ->
                cb.lessThanOrEqualTo(root.get("price"), filter.getMaxPrice()));
        }

        return productRepository.findAll(spec, pageable)
            .map(this::toDto);
    }
}
```

Well-designed REST APIs are the foundation of maintainable microservices and web applications. Focus on consistency, clear documentation, and following HTTP standards to create APIs that developers love to use.

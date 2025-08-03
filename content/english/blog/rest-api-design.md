---
title: "REST API Design Best Practices"
meta_title: ""
description: "Learn core principles and practical guides for designing scalable and maintainable REST APIs."
date: 2022-04-07T05:00:00Z
image: "/images/service-1.png"
categories: ["Backend", "API"]
author: "Kigo"
tags: ["REST API", "API Design", "Backend", "Web Development"]
draft: false
---

Well-designed REST APIs improve developer experience and ensure system scalability. Let's explore REST API design principles and best practices that can be applied in real projects, along with Spring Boot examples.

## REST API Design Principles

### 1. Resource-Centered URL Design

```java
// ❌ Bad example - using verbs
@RestController
@RequestMapping("/api")
public class BadUserController {

    @PostMapping("/createUser")
    public User createUser(@RequestBody CreateUserRequest request) { ... }

    @PostMapping("/deleteUser/{id}")
    public void deleteUser(@PathVariable Long id) { ... }

    @GetMapping("/getUsersByStatus/{status}")
    public List<User> getUsersByStatus(@PathVariable String status) { ... }
}

// ✅ Good example - using nouns, HTTP methods express actions
@RestController
@RequestMapping("/api/users")
@Validated
@Slf4j
public class UserController {

    private final UserService userService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody CreateUserRequest request) {
        User user = userService.createUser(request);
        UserResponse response = UserResponse.from(user);

        URI location = ServletUriComponentsBuilder
            .fromCurrentRequest()
            .path("/{id}")
            .buildAndExpand(user.getId())
            .toUri();

        return ResponseEntity.created(location).body(response);
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
        User user = userService.findById(id);
        return ResponseEntity.ok(UserResponse.from(user));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<UserResponse>> getUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "createdAt") String sortBy,
            @RequestParam(defaultValue = "desc") String sortDir) {

        UserSearchCriteria criteria = UserSearchCriteria.builder()
            .status(status)
            .page(page)
            .size(size)
            .sortBy(sortBy)
            .sortDirection(sortDir)
            .build();

        Page<User> users = userService.findUsers(criteria);
        PagedResponse<UserResponse> response = PagedResponse.of(
            users.map(UserResponse::from)
        );

        return ResponseEntity.ok(response);
    }

    @PutMapping("/{id}")
    public ResponseEntity<UserResponse> updateUser(
            @PathVariable Long id,
            @Valid @RequestBody UpdateUserRequest request) {
        User user = userService.updateUser(id, request);
        return ResponseEntity.ok(UserResponse.from(user));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        userService.deleteUser(id);
        return ResponseEntity.noContent().build();
    }
}
```

### 2. Nested Resource Design

```java
@RestController
@RequestMapping("/api/users/{userId}/posts")
public class UserPostController {

    private final PostService postService;

    @GetMapping
    public ResponseEntity<PagedResponse<PostResponse>> getUserPosts(
            @PathVariable Long userId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size) {

        Page<Post> posts = postService.findByUserId(userId,
            PageRequest.of(page, size, Sort.by("createdAt").descending()));

        PagedResponse<PostResponse> response = PagedResponse.of(
            posts.map(PostResponse::from)
        );

        return ResponseEntity.ok(response);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<PostResponse> createPost(
            @PathVariable Long userId,
            @Valid @RequestBody CreatePostRequest request) {

        Post post = postService.createPost(userId, request);
        PostResponse response = PostResponse.from(post);

        URI location = ServletUriComponentsBuilder
            .fromCurrentRequest()
            .path("/{postId}")
            .buildAndExpand(post.getId())
            .toUri();

        return ResponseEntity.created(location).body(response);
    }
}
```

## Request/Response DTO Design

### Request DTOs

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CreateUserRequest {

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    @Size(max = 100, message = "Email cannot exceed 100 characters")
    private String email;

    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 50, message = "Name must be between 2 and 50 characters")
    private String name;

    @Size(max = 500, message = "Bio cannot exceed 500 characters")
    private String bio;

    @Valid
    private CreateAddressRequest address;

    @JsonFormat(pattern = "yyyy-MM-dd")
    @Past(message = "Birth date must be in the past")
    private LocalDate birthDate;
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateUserRequest {

    @Size(min = 2, max = 50, message = "Name must be between 2 and 50 characters")
    private String name;

    @Size(max = 500, message = "Bio cannot exceed 500 characters")
    private String bio;

    @Valid
    private UpdateAddressRequest address;
}
```

### Response DTOs

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserResponse {

    private Long id;
    private String email;
    private String name;
    private String bio;
    private AddressResponse address;

    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate birthDate;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime createdAt;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime updatedAt;

    // Related resource links
    private Map<String, String> links;

    public static UserResponse from(User user) {
        UserResponseBuilder builder = UserResponse.builder()
            .id(user.getId())
            .email(user.getEmail())
            .name(user.getName())
            .bio(user.getBio())
            .birthDate(user.getBirthDate())
            .createdAt(user.getCreatedAt())
            .updatedAt(user.getUpdatedAt());

        if (user.getAddress() != null) {
            builder.address(AddressResponse.from(user.getAddress()));
        }

        // Add HATEOAS links
        Map<String, String> links = new HashMap<>();
        links.put("self", "/api/users/" + user.getId());
        links.put("posts", "/api/users/" + user.getId() + "/posts");
        links.put("profile", "/api/users/" + user.getId() + "/profile");
        builder.links(links);

        return builder.build();
    }
}
```

### Paginated Response

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PagedResponse<T> {

    private List<T> content;
    private PageInfo page;
    private Map<String, String> links;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PageInfo {
        private int number;
        private int size;
        private long totalElements;
        private int totalPages;
        private boolean first;
        private boolean last;
        private boolean hasNext;
        private boolean hasPrevious;
    }

    public static <T> PagedResponse<T> of(Page<T> page) {
        PageInfo pageInfo = PageInfo.builder()
            .number(page.getNumber())
            .size(page.getSize())
            .totalElements(page.getTotalElements())
            .totalPages(page.getTotalPages())
            .first(page.isFirst())
            .last(page.isLast())
            .hasNext(page.hasNext())
            .hasPrevious(page.hasPrevious())
            .build();

        // Generate pagination links
        Map<String, String> links = createPaginationLinks(page);

        return PagedResponse.<T>builder()
            .content(page.getContent())
            .page(pageInfo)
            .links(links)
            .build();
    }

    private static Map<String, String> createPaginationLinks(Page<?> page) {
        Map<String, String> links = new HashMap<>();
        String baseUrl = ServletUriComponentsBuilder.fromCurrentRequest()
            .replaceQueryParam("page", "{page}")
            .toUriString();

        links.put("self", baseUrl.replace("{page}", String.valueOf(page.getNumber())));

        if (page.hasNext()) {
            links.put("next", baseUrl.replace("{page}", String.valueOf(page.getNumber() + 1)));
        }

        if (page.hasPrevious()) {
            links.put("prev", baseUrl.replace("{page}", String.valueOf(page.getNumber() - 1)));
        }

        links.put("first", baseUrl.replace("{page}", "0"));
        links.put("last", baseUrl.replace("{page}", String.valueOf(page.getTotalPages() - 1)));

        return links;
    }
}
```

## Error Handling

### Standard Error Response

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ErrorResponse {

    private String error;
    private String message;
    private int status;
    private String path;
    private LocalDateTime timestamp;
    private List<FieldError> fieldErrors;
    private String correlationId;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class FieldError {
        private String field;
        private Object rejectedValue;
        private String message;
    }
}

@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidationException(
            MethodArgumentNotValidException ex,
            HttpServletRequest request) {

        List<ErrorResponse.FieldError> fieldErrors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(error -> ErrorResponse.FieldError.builder()
                .field(error.getField())
                .rejectedValue(error.getRejectedValue())
                .message(error.getDefaultMessage())
                .build())
            .collect(Collectors.toList());

        String correlationId = request.getHeader("X-Correlation-ID");

        return ErrorResponse.builder()
            .error("VALIDATION_FAILED")
            .message("Input validation failed")
            .status(HttpStatus.BAD_REQUEST.value())
            .path(request.getRequestURI())
            .timestamp(LocalDateTime.now())
            .fieldErrors(fieldErrors)
            .correlationId(correlationId)
            .build();
    }

    @ExceptionHandler(EntityNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleEntityNotFoundException(
            EntityNotFoundException ex,
            HttpServletRequest request) {

        return ErrorResponse.builder()
            .error("RESOURCE_NOT_FOUND")
            .message(ex.getMessage())
            .status(HttpStatus.NOT_FOUND.value())
            .path(request.getRequestURI())
            .timestamp(LocalDateTime.now())
            .correlationId(request.getHeader("X-Correlation-ID"))
            .build();
    }

    @ExceptionHandler(DataIntegrityViolationException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ErrorResponse handleDataIntegrityViolation(
            DataIntegrityViolationException ex,
            HttpServletRequest request) {

        String message = "Data integrity constraint violation";
        if (ex.getMessage().contains("email")) {
            message = "Email already exists";
        }

        return ErrorResponse.builder()
            .error("DATA_INTEGRITY_VIOLATION")
            .message(message)
            .status(HttpStatus.CONFLICT.value())
            .path(request.getRequestURI())
            .timestamp(LocalDateTime.now())
            .correlationId(request.getHeader("X-Correlation-ID"))
            .build();
    }
}
```

## API Versioning

### URL-based Versioning

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserV1Controller {

    @GetMapping("/{id}")
    public ResponseEntity<UserV1Response> getUser(@PathVariable Long id) {
        // v1 implementation
    }
}

@RestController
@RequestMapping("/api/v2/users")
public class UserV2Controller {

    @GetMapping("/{id}")
    public ResponseEntity<UserV2Response> getUser(@PathVariable Long id) {
        // v2 implementation - new fields added
    }
}
```

### Header-based Versioning

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping(value = "/{id}", headers = "API-Version=v1")
    public ResponseEntity<UserV1Response> getUserV1(@PathVariable Long id) {
        // v1 implementation
    }

    @GetMapping(value = "/{id}", headers = "API-Version=v2")
    public ResponseEntity<UserV2Response> getUserV2(@PathVariable Long id) {
        // v2 implementation
    }
}
```

## API Documentation

### OpenAPI 3.0 Configuration

```java
@Configuration
@OpenAPIDefinition(
    info = @Info(
        title = "User Management API",
        version = "v1.0.0",
        description = "REST API providing user registration, lookup, update, and delete functionality",
        contact = @Contact(
            name = "Kigo",
            email = "support@kigo.dev",
            url = "https://kigo.dev"
        ),
        license = @License(
            name = "MIT License",
            url = "https://opensource.org/licenses/MIT"
        )
    ),
    servers = {
        @Server(url = "https://api.kigo.dev", description = "Production server"),
        @Server(url = "https://staging-api.kigo.dev", description = "Staging server"),
        @Server(url = "http://localhost:8080", description = "Local development server")
    }
)
public class OpenApiConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .components(new Components()
                .addSecuritySchemes("bearer-jwt",
                    new SecurityScheme()
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")
                        .description("Enter JWT token")))
            .addSecurityItem(new SecurityRequirement().addList("bearer-jwt"));
    }
}

@RestController
@RequestMapping("/api/users")
@Tag(name = "User Management", description = "APIs for user CRUD operations")
public class UserController {

    @Operation(
        summary = "Create user",
        description = "Creates a new user.",
        responses = {
            @ApiResponse(
                responseCode = "201",
                description = "User created successfully",
                content = @Content(
                    mediaType = "application/json",
                    schema = @Schema(implementation = UserResponse.class)
                )
            ),
            @ApiResponse(
                responseCode = "400",
                description = "Bad request",
                content = @Content(
                    mediaType = "application/json",
                    schema = @Schema(implementation = ErrorResponse.class)
                )
            )
        }
    )
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody
            @Parameter(description = "User creation request information", required = true)
            CreateUserRequest request) {
        // Implementation
    }

    @Operation(
        summary = "Get user list",
        description = "Retrieves user list with pagination and filtering applied."
    )
    @GetMapping
    public ResponseEntity<PagedResponse<UserResponse>> getUsers(
            @Parameter(description = "Page number (starts from 0)", example = "0")
            @RequestParam(defaultValue = "0") int page,

            @Parameter(description = "Page size", example = "20")
            @RequestParam(defaultValue = "20") int size,

            @Parameter(description = "User status filter", example = "ACTIVE")
            @RequestParam(required = false) String status) {
        // Implementation
    }
}
```

## Performance Optimization

### Caching Strategy

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/{id}")
    @Cacheable(value = "users", key = "#id")
    public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
        User user = userService.findById(id);
        return ResponseEntity
            .ok()
            .cacheControl(CacheControl.maxAge(5, TimeUnit.MINUTES))
            .eTag(String.valueOf(user.getVersion()))
            .body(UserResponse.from(user));
    }

    @PutMapping("/{id}")
    @CacheEvict(value = "users", key = "#id")
    public ResponseEntity<UserResponse> updateUser(
            @PathVariable Long id,
            @RequestHeader(value = "If-Match", required = false) String ifMatch,
            @Valid @RequestBody UpdateUserRequest request) {

        // Optimistic locking check
        if (ifMatch != null) {
            User currentUser = userService.findById(id);
            if (!ifMatch.equals(String.valueOf(currentUser.getVersion()))) {
                return ResponseEntity.status(HttpStatus.PRECONDITION_FAILED).build();
            }
        }

        User user = userService.updateUser(id, request);
        return ResponseEntity
            .ok()
            .eTag(String.valueOf(user.getVersion()))
            .body(UserResponse.from(user));
    }
}
```

### Compression Configuration

```yaml
# application.yml
server:
  compression:
    enabled: true
    mime-types:
      - application/json
      - application/xml
      - text/html
      - text/xml
      - text/plain
    min-response-size: 1024
```

## Security Configuration

### CORS Configuration

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOriginPatterns("https://*.kigo.dev", "http://localhost:*")
            .allowedMethods("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")
            .allowedHeaders("*")
            .allowCredentials(true)
            .maxAge(3600);
    }
}
```

Through these best practices, you can build developer-friendly and scalable REST APIs. Apply consistent design principles and proper documentation to improve API quality and usability.

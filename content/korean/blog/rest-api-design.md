---
title: "REST API 설계 베스트 프랙티스"
meta_title: ""
description: "확장 가능하고 유지보수가 용이한 REST API를 설계하기 위한 핵심 원칙과 실무 가이드를 알아봅니다."
date: 2022-04-07T05:00:00Z
image: "/images/service-1.png"
categories: ["백엔드", "API"]
author: "Kigo"
tags: ["REST API", "API 설계", "백엔드", "웹 개발"]
draft: false
---

잘 설계된 REST API는 개발자 경험을 향상시키고 시스템의 확장성을 보장합니다. 실제 프로젝트에서 적용할 수 있는 REST API 설계 원칙과 베스트 프랙티스를 Spring Boot 예제와 함께 알아보겠습니다.

## REST API 설계 원칙

### 1. 리소스 중심 URL 설계

```java
// ❌ 잘못된 예시 - 동사 사용
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

// ✅ 올바른 예시 - 명사 사용, HTTP 메서드로 동작 표현
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

### 2. 중첩 리소스 설계

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

## 요청/응답 DTO 설계

### 요청 DTO

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CreateUserRequest {

    @NotBlank(message = "이메일은 필수입니다")
    @Email(message = "올바른 이메일 형식이 아닙니다")
    @Size(max = 100, message = "이메일은 100자를 초과할 수 없습니다")
    private String email;

    @NotBlank(message = "이름은 필수입니다")
    @Size(min = 2, max = 50, message = "이름은 2자 이상 50자 이하여야 합니다")
    private String name;

    @Size(max = 500, message = "소개는 500자를 초과할 수 없습니다")
    private String bio;

    @Valid
    private CreateAddressRequest address;

    @JsonFormat(pattern = "yyyy-MM-dd")
    @Past(message = "생년월일은 과거 날짜여야 합니다")
    private LocalDate birthDate;
}

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateUserRequest {

    @Size(min = 2, max = 50, message = "이름은 2자 이상 50자 이하여야 합니다")
    private String name;

    @Size(max = 500, message = "소개는 500자를 초과할 수 없습니다")
    private String bio;

    @Valid
    private UpdateAddressRequest address;
}
```

### 응답 DTO

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

    // 관련 리소스 링크
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

        // HATEOAS 링크 추가
        Map<String, String> links = new HashMap<>();
        links.put("self", "/api/users/" + user.getId());
        links.put("posts", "/api/users/" + user.getId() + "/posts");
        links.put("profile", "/api/users/" + user.getId() + "/profile");
        builder.links(links);

        return builder.build();
    }
}
```

### 페이징 응답

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

        // 페이징 링크 생성
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

## 에러 핸들링

### 표준 에러 응답

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
            .message("입력값 검증에 실패했습니다")
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

        String message = "데이터 무결성 제약조건 위반";
        if (ex.getMessage().contains("email")) {
            message = "이미 존재하는 이메일입니다";
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

## API 버전 관리

### URL 기반 버전 관리

```java
@RestController
@RequestMapping("/api/v1/users")
public class UserV1Controller {

    @GetMapping("/{id}")
    public ResponseEntity<UserV1Response> getUser(@PathVariable Long id) {
        // v1 구현
    }
}

@RestController
@RequestMapping("/api/v2/users")
public class UserV2Controller {

    @GetMapping("/{id}")
    public ResponseEntity<UserV2Response> getUser(@PathVariable Long id) {
        // v2 구현 - 새로운 필드 추가
    }
}
```

### 헤더 기반 버전 관리

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping(value = "/{id}", headers = "API-Version=v1")
    public ResponseEntity<UserV1Response> getUserV1(@PathVariable Long id) {
        // v1 구현
    }

    @GetMapping(value = "/{id}", headers = "API-Version=v2")
    public ResponseEntity<UserV2Response> getUserV2(@PathVariable Long id) {
        // v2 구현
    }
}
```

## API 문서화

### OpenAPI 3.0 설정

```java
@Configuration
@OpenAPIDefinition(
    info = @Info(
        title = "사용자 관리 API",
        version = "v1.0.0",
        description = "사용자 등록, 조회, 수정, 삭제 기능을 제공하는 REST API",
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
        @Server(url = "https://api.kigo.dev", description = "운영 서버"),
        @Server(url = "https://staging-api.kigo.dev", description = "스테이징 서버"),
        @Server(url = "http://localhost:8080", description = "로컬 개발 서버")
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
                        .description("JWT 토큰을 입력하세요")))
            .addSecurityItem(new SecurityRequirement().addList("bearer-jwt"));
    }
}

@RestController
@RequestMapping("/api/users")
@Tag(name = "사용자 관리", description = "사용자 CRUD 작업을 위한 API")
public class UserController {

    @Operation(
        summary = "사용자 생성",
        description = "새로운 사용자를 생성합니다.",
        responses = {
            @ApiResponse(
                responseCode = "201",
                description = "사용자 생성 성공",
                content = @Content(
                    mediaType = "application/json",
                    schema = @Schema(implementation = UserResponse.class)
                )
            ),
            @ApiResponse(
                responseCode = "400",
                description = "잘못된 요청",
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
            @Parameter(description = "사용자 생성 요청 정보", required = true)
            CreateUserRequest request) {
        // 구현
    }

    @Operation(
        summary = "사용자 목록 조회",
        description = "페이징과 필터링이 적용된 사용자 목록을 조회합니다."
    )
    @GetMapping
    public ResponseEntity<PagedResponse<UserResponse>> getUsers(
            @Parameter(description = "페이지 번호 (0부터 시작)", example = "0")
            @RequestParam(defaultValue = "0") int page,

            @Parameter(description = "페이지 크기", example = "20")
            @RequestParam(defaultValue = "20") int size,

            @Parameter(description = "사용자 상태 필터", example = "ACTIVE")
            @RequestParam(required = false) String status) {
        // 구현
    }
}
```

## 성능 최적화

### 캐싱 전략

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

        // 낙관적 잠금 확인
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

### 압축 설정

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

## 보안 설정

### CORS 설정

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

이러한 베스트 프랙티스를 통해 개발자 친화적이고 확장 가능한 REST API를 구축할 수 있습니다. 일관된 설계 원칙을 적용하고 적절한 문서화를 통해 API의 품질과 사용성을 향상시키시기 바랍니다.

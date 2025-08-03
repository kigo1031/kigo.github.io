---
title: "Database Design Patterns for Java Applications"
meta_title: ""
description: "Essential database design patterns and optimization techniques for Java backend applications."
date: 2022-04-05T05:00:00Z
image: "/images/service-2.png"
categories: ["Backend", "Database"]
author: "Kigo"
tags: ["Database", "JPA", "SQL", "Java", "Design Patterns"]
draft: false
---

Effective database design is crucial for building scalable Java applications. Let's explore essential patterns and techniques that every backend developer should know.

## Entity Relationship Patterns

### One-to-Many Relationships

```java
@Entity
@Table(name = "categories")
public class Category {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String name;

    @OneToMany(mappedBy = "category", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Product> products = new ArrayList<>();

    // Helper methods
    public void addProduct(Product product) {
        products.add(product);
        product.setCategory(this);
    }

    public void removeProduct(Product product) {
        products.remove(product);
        product.setCategory(null);
    }
}

@Entity
@Table(name = "products")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(precision = 10, scale = 2)
    private BigDecimal price;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id", nullable = false)
    private Category category;

    // Constructor, getters, setters
}
```

### Many-to-Many Relationships

```java
@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @ManyToMany(cascade = {CascadeType.PERSIST, CascadeType.MERGE})
    @JoinTable(
        name = "user_roles",
        joinColumns = @JoinColumn(name = "user_id"),
        inverseJoinColumns = @JoinColumn(name = "role_id")
    )
    private Set<Role> roles = new HashSet<>();

    public void addRole(Role role) {
        roles.add(role);
        role.getUsers().add(this);
    }

    public void removeRole(Role role) {
        roles.remove(role);
        role.getUsers().remove(this);
    }
}

@Entity
@Table(name = "roles")
public class Role {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, unique = true)
    private RoleName name;

    @ManyToMany(mappedBy = "roles")
    private Set<User> users = new HashSet<>();
}
```

## Repository Patterns

### Generic Repository

```java
public interface BaseRepository<T, ID> {
    Optional<T> findById(ID id);
    List<T> findAll();
    T save(T entity);
    void deleteById(ID id);
    boolean existsById(ID id);
}

@NoRepositoryBean
public interface CustomRepository<T, ID> extends BaseRepository<T, ID> {
    List<T> findAllWithPagination(int page, int size);
    long countAll();
    List<T> findByFieldContaining(String fieldName, String value);
}

public interface UserRepository extends JpaRepository<User, Long>, CustomRepository<User, Long> {
    Optional<User> findByEmail(String email);
    List<User> findByRoles_Name(RoleName roleName);

    @Query("SELECT u FROM User u WHERE u.createdAt >= :date")
    List<User> findUsersCreatedAfter(@Param("date") LocalDateTime date);

    @Query(value = "SELECT * FROM users WHERE status = 'ACTIVE' ORDER BY last_login_at DESC LIMIT :limit",
           nativeQuery = true)
    List<User> findRecentActiveUsers(@Param("limit") int limit);
}
```

### Custom Repository Implementation

```java
@Repository
public class UserRepositoryImpl implements CustomRepository<User, Long> {

    @PersistenceContext
    private EntityManager entityManager;

    @Override
    public List<User> findAllWithPagination(int page, int size) {
        return entityManager.createQuery("SELECT u FROM User u ORDER BY u.createdAt DESC", User.class)
                .setFirstResult(page * size)
                .setMaxResults(size)
                .getResultList();
    }

    @Override
    public List<User> findByFieldContaining(String fieldName, String value) {
        CriteriaBuilder cb = entityManager.getCriteriaBuilder();
        CriteriaQuery<User> query = cb.createQuery(User.class);
        Root<User> root = query.from(User.class);

        query.select(root)
             .where(cb.like(cb.lower(root.get(fieldName)), "%" + value.toLowerCase() + "%"));

        return entityManager.createQuery(query).getResultList();
    }
}
```

## Query Optimization Patterns

### N+1 Problem Solutions

```java
// Problem: N+1 queries
public List<UserDTO> getAllUsersWithRoles() {
    List<User> users = userRepository.findAll(); // 1 query
    return users.stream()
            .map(user -> new UserDTO(
                user.getId(),
                user.getEmail(),
                user.getRoles() // N queries (one for each user)
            ))
            .collect(Collectors.toList());
}

// Solution 1: Join Fetch
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    @Query("SELECT DISTINCT u FROM User u LEFT JOIN FETCH u.roles")
    List<User> findAllWithRoles();
}

// Solution 2: Entity Graph
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    @EntityGraph(attributePaths = {"roles"})
    List<User> findAll();
}

// Solution 3: Projection
public interface UserProjection {
    Long getId();
    String getEmail();
    Set<RoleProjection> getRoles();

    interface RoleProjection {
        Long getId();
        String getName();
    }
}

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    List<UserProjection> findAllProjectedBy();
}
```

### Batch Processing

```java
@Service
@Transactional
public class UserService {

    private final UserRepository userRepository;

    @PersistenceContext
    private EntityManager entityManager;

    public void batchCreateUsers(List<CreateUserRequest> requests) {
        int batchSize = 20;

        for (int i = 0; i < requests.size(); i++) {
            User user = new User(requests.get(i).getEmail(), requests.get(i).getName());
            entityManager.persist(user);

            if (i % batchSize == 0 && i > 0) {
                entityManager.flush();
                entityManager.clear();
            }
        }
        entityManager.flush();
        entityManager.clear();
    }

    @Modifying
    @Query("UPDATE User u SET u.status = :status WHERE u.id IN :ids")
    int batchUpdateUserStatus(@Param("ids") List<Long> ids, @Param("status") UserStatus status);
}
```

## Transaction Management Patterns

### Declarative Transactions

```java
@Service
@Transactional(readOnly = true)
public class OrderService {

    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        // This method runs in a read-write transaction
        Order order = new Order(request.getUserId(), request.getItems());
        return orderRepository.save(order);
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logOrderEvent(Long orderId, String event) {
        // This runs in a separate transaction
        OrderLog log = new OrderLog(orderId, event);
        orderLogRepository.save(log);
    }

    @Transactional(
        isolation = Isolation.SERIALIZABLE,
        timeout = 30,
        rollbackFor = {BusinessException.class}
    )
    public void processPayment(PaymentRequest request) {
        // High isolation level for payment processing
        paymentProcessor.process(request);
    }

    // Read-only method (inherited from class level)
    public List<Order> findOrdersByUser(Long userId) {
        return orderRepository.findByUserId(userId);
    }
}
```

### Programmatic Transactions

```java
@Service
public class ComplexTransactionService {

    private final PlatformTransactionManager transactionManager;

    public void complexBusinessOperation() {
        TransactionTemplate transactionTemplate = new TransactionTemplate(transactionManager);

        transactionTemplate.execute(status -> {
            try {
                // Business logic
                performOperation1();
                performOperation2();

                // Conditional rollback
                if (someCondition()) {
                    status.setRollbackOnly();
                    return null;
                }

                performOperation3();
                return null;
            } catch (Exception e) {
                status.setRollbackOnly();
                throw new RuntimeException("Transaction failed", e);
            }
        });
    }
}
```

## Caching Strategies

### Entity-Level Caching

```java
@Entity
@Table(name = "products")
@Cacheable
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class Product {
    // Entity definition
}

// Application configuration
@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public CacheManager cacheManager() {
        ConcurrentMapCacheManager cacheManager = new ConcurrentMapCacheManager();
        cacheManager.setCacheNames(Arrays.asList("products", "categories", "users"));
        return cacheManager;
    }
}
```

### Query Result Caching

```java
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {

    @QueryHints({
        @QueryHint(name = "org.hibernate.cacheable", value = "true"),
        @QueryHint(name = "org.hibernate.cacheRegion", value = "product-queries")
    })
    @Query("SELECT p FROM Product p WHERE p.category.id = :categoryId")
    List<Product> findByCategoryId(@Param("categoryId") Long categoryId);
}
```

### Service-Level Caching

```java
@Service
public class ProductService {

    @Cacheable(value = "products", key = "#id")
    public Product findById(Long id) {
        return productRepository.findById(id)
            .orElseThrow(() -> new ProductNotFoundException("Product not found"));
    }

    @Cacheable(value = "product-lists", key = "#categoryId + '_' + #page + '_' + #size")
    public Page<Product> findByCategory(Long categoryId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return productRepository.findByCategoryId(categoryId, pageable);
    }

    @CacheEvict(value = "products", key = "#product.id")
    public Product updateProduct(Product product) {
        return productRepository.save(product);
    }

    @CacheEvict(value = {"products", "product-lists"}, allEntries = true)
    public void clearProductCaches() {
        // Clears all product-related caches
    }
}
```

## Database Migration Patterns

### Flyway Migrations

```sql
-- V1__Create_user_table.sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

```sql
-- V2__Add_user_status.sql
ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE';
CREATE INDEX idx_users_status ON users(status);
```

```java
// Migration configuration
@Configuration
public class FlywayConfig {

    @Bean
    public Flyway flyway(@Qualifier("dataSource") DataSource dataSource) {
        return Flyway.configure()
                .dataSource(dataSource)
                .locations("classpath:db/migration")
                .baselineOnMigrate(true)
                .validateOnMigrate(true)
                .load();
    }
}
```

## Performance Monitoring

### Database Connection Monitoring

```java
@Component
public class DatabaseMetrics {

    private final DataSource dataSource;
    private final MeterRegistry meterRegistry;

    public DatabaseMetrics(DataSource dataSource, MeterRegistry meterRegistry) {
        this.dataSource = dataSource;
        this.meterRegistry = meterRegistry;

        // Register connection pool metrics
        if (dataSource instanceof HikariDataSource) {
            HikariDataSource hikariDataSource = (HikariDataSource) dataSource;
            Gauge.builder("database.connections.active")
                .description("Active database connections")
                .register(meterRegistry, hikariDataSource, ds -> ds.getHikariPoolMXBean().getActiveConnections());

            Gauge.builder("database.connections.idle")
                .description("Idle database connections")
                .register(meterRegistry, hikariDataSource, ds -> ds.getHikariPoolMXBean().getIdleConnections());
        }
    }
}
```

### Query Performance Monitoring

```java
@Component
@Slf4j
public class QueryPerformanceInterceptor implements Interceptor {

    private final MeterRegistry meterRegistry;

    @Override
    public boolean onLoad(Object entity, Serializable id, Object[] state, String[] propertyNames, Type[] types) {
        Timer.Sample sample = Timer.start(meterRegistry);
        sample.stop(Timer.builder("hibernate.query.execution")
            .tag("operation", "load")
            .tag("entity", entity.getClass().getSimpleName())
            .register(meterRegistry));
        return false;
    }
}
```

These patterns provide a solid foundation for building robust, scalable database-driven Java applications. Choose the appropriate patterns based on your specific requirements and performance needs.

Nemo vel ad consectetur namut rutrum ex, venenatis sollicitudin urna. Aliquam erat volutpat. Integer eu ipsum sem. Ut bibendum lacus vestibulum maximus suscipit. Quisque vitae nibh iaculis neque blandit euismod.

Lorem ipsum dolor sit amet consectetur adipisicing elit. Nemo vel ad consectetur ut aperiam. Itaque eligendi natus aperiam? Excepturi repellendus consequatur quibusdam optio expedita praesentium est adipisci dolorem ut eius!

## Creative Design

Nam ut rutrum ex, venenatis sollicitudin urna. Aliquam erat volutpat. Integer eu ipsum sem. Ut bibendum lacus vestibulum maximus suscipit. Quisque vitae nibh iaculis neque blandit euismod.

> Lorem ipsum dolor sit amet consectetur adipisicing elit. Nemo vel ad consectetur ut aperiam. Itaque eligendi natus aperiam? Excepturi repellendus consequatur quibusdam optio expedita praesentium est adipisci dolorem ut eius!

Lorem ipsum dolor sit amet consectetur adipisicing elit. Nemo vel ad consectetur ut aperiam. Itaque eligendi natus aperiam? Excepturi repellendus consequatur quibusdam optio expedita praesentium est adipisci dolorem ut eius!

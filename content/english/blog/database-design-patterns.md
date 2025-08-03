---
title: "Database Design Patterns for Java Applications"
meta_title: ""
description: "Learn about efficient database design patterns and optimization techniques using JPA and Spring Data for Java applications."
date: 2022-04-05T05:00:00Z
image: "/images/service-2.png"
categories: ["Backend", "Database"]
author: "Kigo"
tags: ["JPA", "Spring Data", "Database", "Design Patterns"]
draft: false
---

Solid database design is essential for efficient Java application development. Let's explore database design patterns that satisfy both performance and maintainability using JPA and Spring Data.

## Entity Design Principles

### Basic Entity Structure

```java
@Entity
@Table(name = "users")
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 100)
    private String email;

    @Column(nullable = false, length = 50)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private UserStatus status;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @Version
    private Long version;
}
```

### Inheritance Mapping Strategy

```java
// Joined Table Strategy (JOINED)
@Entity
@Table(name = "accounts")
@Inheritance(strategy = InheritanceType.JOINED)
@DiscriminatorColumn(name = "account_type")
public abstract class Account {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String accountNumber;

    @Column(nullable = false, precision = 15, scale = 2)
    private BigDecimal balance;

    // Common fields
}

@Entity
@Table(name = "savings_accounts")
@DiscriminatorValue("SAVINGS")
public class SavingsAccount extends Account {

    @Column(nullable = false, precision = 5, scale = 4)
    private BigDecimal interestRate;

    private Integer minBalance;
}

@Entity
@Table(name = "checking_accounts")
@DiscriminatorValue("CHECKING")
public class CheckingAccount extends Account {

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal overdraftLimit;

    private Integer freeTransactions;
}
```

## Association Mapping Patterns

### One-to-Many Association Optimization

```java
@Entity
@Table(name = "categories")
public class Category {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    // Bidirectional association - LAZY loading for performance
    @OneToMany(mappedBy = "category", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @BatchSize(size = 20) // Solving N+1 problem
    private List<Product> products = new ArrayList<>();

    // Convenience methods for associations
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

    @Column(nullable = false, length = 200)
    private String name;

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal price;

    // Many-to-One association
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id", nullable = false)
    private Category category;
}
```

### Many-to-Many Association with Additional Attributes

```java
@Entity
@Table(name = "students")
public class Student {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @OneToMany(mappedBy = "student", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Enrollment> enrollments = new ArrayList<>();

    public void enrollInCourse(Course course, LocalDateTime enrollmentDate) {
        Enrollment enrollment = new Enrollment(this, course, enrollmentDate);
        enrollments.add(enrollment);
        course.getEnrollments().add(enrollment);
    }
}

@Entity
@Table(name = "courses")
public class Course {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 200)
    private String title;

    @OneToMany(mappedBy = "course", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Enrollment> enrollments = new ArrayList<>();
}

@Entity
@Table(name = "enrollments")
public class Enrollment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "student_id")
    private Student student;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "course_id")
    private Course course;

    @Column(nullable = false)
    private LocalDateTime enrollmentDate;

    private BigDecimal grade;

    public Enrollment(Student student, Course course, LocalDateTime enrollmentDate) {
        this.student = student;
        this.course = course;
        this.enrollmentDate = enrollmentDate;
    }
}
```

## Repository Pattern

### Custom Repository Implementation

```java
public interface UserRepositoryCustom {
    List<User> findUsersWithComplexCriteria(UserSearchCriteria criteria);
    Page<User> findActiveUsersWithPosts(Pageable pageable);
}

@Repository
public class UserRepositoryImpl implements UserRepositoryCustom {

    @PersistenceContext
    private EntityManager entityManager;

    @Override
    public List<User> findUsersWithComplexCriteria(UserSearchCriteria criteria) {
        CriteriaBuilder cb = entityManager.getCriteriaBuilder();
        CriteriaQuery<User> query = cb.createQuery(User.class);
        Root<User> root = query.from(User.class);

        List<Predicate> predicates = new ArrayList<>();

        if (criteria.getName() != null) {
            predicates.add(cb.like(cb.lower(root.get("name")),
                "%" + criteria.getName().toLowerCase() + "%"));
        }

        if (criteria.getStatus() != null) {
            predicates.add(cb.equal(root.get("status"), criteria.getStatus()));
        }

        if (criteria.getCreatedAfter() != null) {
            predicates.add(cb.greaterThanOrEqualTo(root.get("createdAt"),
                criteria.getCreatedAfter()));
        }

        query.where(predicates.toArray(new Predicate[0]));
        query.orderBy(cb.desc(root.get("createdAt")));

        return entityManager.createQuery(query)
            .setMaxResults(100)
            .getResultList();
    }

    @Override
    public Page<User> findActiveUsersWithPosts(Pageable pageable) {
        String jpql = """
            SELECT DISTINCT u FROM User u
            LEFT JOIN FETCH u.posts p
            WHERE u.status = :status
            ORDER BY u.createdAt DESC
            """;

        TypedQuery<User> query = entityManager.createQuery(jpql, User.class)
            .setParameter("status", UserStatus.ACTIVE)
            .setFirstResult((int) pageable.getOffset())
            .setMaxResults(pageable.getPageSize());

        List<User> users = query.getResultList();

        // Count total results
        Long total = entityManager.createQuery(
            "SELECT COUNT(DISTINCT u) FROM User u WHERE u.status = :status", Long.class)
            .setParameter("status", UserStatus.ACTIVE)
            .getSingleResult();

        return new PageImpl<>(users, pageable, total);
    }
}

public interface UserRepository extends JpaRepository<User, Long>, UserRepositoryCustom {

    @Query("SELECT u FROM User u WHERE u.email = :email")
    Optional<User> findByEmail(@Param("email") String email);

    @Query(value = """
        SELECT u.* FROM users u
        WHERE u.status = :status
        AND u.created_at >= :since
        ORDER BY u.created_at DESC
        """, nativeQuery = true)
    List<User> findRecentActiveUsers(@Param("status") String status,
                                   @Param("since") LocalDateTime since);

    @Modifying
    @Query("UPDATE User u SET u.status = :status WHERE u.id IN :ids")
    int updateUserStatus(@Param("ids") List<Long> ids, @Param("status") UserStatus status);
}
```

## Performance Optimization Patterns

### Pagination and Sorting

```java
@Service
@Transactional(readOnly = true)
public class ProductService {

    private final ProductRepository productRepository;

    public Page<ProductDto> getProducts(ProductSearchRequest request) {
        Pageable pageable = PageRequest.of(
            request.getPage(),
            request.getSize(),
            Sort.by(Sort.Direction.DESC, "createdAt")
        );

        Page<Product> products = productRepository.findByCategoryAndPriceRange(
            request.getCategoryId(),
            request.getMinPrice(),
            request.getMaxPrice(),
            pageable
        );

        return products.map(this::convertToDto);
    }

    private ProductDto convertToDto(Product product) {
        return ProductDto.builder()
            .id(product.getId())
            .name(product.getName())
            .price(product.getPrice())
            .categoryName(product.getCategory().getName())
            .build();
    }
}
```

### Batch Processing Optimization

```java
@Service
public class BatchUserService {

    @PersistenceContext
    private EntityManager entityManager;

    @Transactional
    public void batchUpdateUserStatus(List<Long> userIds, UserStatus newStatus) {
        final int batchSize = 100;

        for (int i = 0; i < userIds.size(); i += batchSize) {
            List<Long> batch = userIds.subList(i,
                Math.min(i + batchSize, userIds.size()));

            entityManager.createQuery(
                "UPDATE User u SET u.status = :status WHERE u.id IN :ids")
                .setParameter("status", newStatus)
                .setParameter("ids", batch)
                .executeUpdate();

            entityManager.flush();
            entityManager.clear();
        }
    }

    @Transactional
    public void batchInsertUsers(List<CreateUserRequest> requests) {
        final int batchSize = 50;

        for (int i = 0; i < requests.size(); i++) {
            User user = User.builder()
                .email(requests.get(i).getEmail())
                .name(requests.get(i).getName())
                .status(UserStatus.ACTIVE)
                .build();

            entityManager.persist(user);

            if (i % batchSize == 0 && i > 0) {
                entityManager.flush();
                entityManager.clear();
            }
        }
    }
}
```

### Caching Strategy

```java
@Entity
@Cacheable
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class Category {
    // Entity definition
}

@Service
public class CategoryService {

    @Cacheable(value = "categories", key = "#id")
    public Category findById(Long id) {
        return categoryRepository.findById(id)
            .orElseThrow(() -> new EntityNotFoundException("Category not found"));
    }

    @Cacheable(value = "categories", key = "'all'")
    public List<Category> findAll() {
        return categoryRepository.findAll();
    }

    @CacheEvict(value = "categories", allEntries = true)
    public Category save(Category category) {
        return categoryRepository.save(category);
    }
}
```

## Transaction Management

### Declarative Transactions

```java
@Service
@Transactional(readOnly = true)
public class OrderService {

    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;
    private final InventoryService inventoryService;

    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        // Check product inventory
        Product product = productRepository.findById(request.getProductId())
            .orElseThrow(() -> new EntityNotFoundException("Product not found"));

        if (!inventoryService.hasStock(product.getId(), request.getQuantity())) {
            throw new InsufficientStockException("Insufficient stock");
        }

        // Create order
        Order order = Order.builder()
            .product(product)
            .quantity(request.getQuantity())
            .totalPrice(product.getPrice().multiply(BigDecimal.valueOf(request.getQuantity())))
            .status(OrderStatus.PENDING)
            .build();

        Order savedOrder = orderRepository.save(order);

        // Decrease inventory
        inventoryService.decreaseStock(product.getId(), request.getQuantity());

        return savedOrder;
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void processPayment(Long orderId, PaymentInfo paymentInfo) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new EntityNotFoundException("Order not found"));

        try {
            // Payment processing logic
            paymentService.processPayment(paymentInfo);
            order.setStatus(OrderStatus.PAID);
        } catch (PaymentException e) {
            order.setStatus(OrderStatus.PAYMENT_FAILED);
            throw e;
        } finally {
            orderRepository.save(order);
        }
    }
}
```

## Auditing Features

```java
@EntityListeners(AuditingEntityListener.class)
@MappedSuperclass
public abstract class BaseEntity {

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @CreatedBy
    @Column(name = "created_by", updatable = false)
    private String createdBy;

    @LastModifiedBy
    @Column(name = "updated_by")
    private String updatedBy;
}

@Configuration
@EnableJpaAuditing
public class JpaAuditingConfig {

    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> {
            Authentication auth = SecurityContextHolder.getContext().getAuthentication();
            if (auth != null && auth.isAuthenticated() && !auth.getPrincipal().equals("anonymousUser")) {
                return Optional.of(auth.getName());
            }
            return Optional.of("system");
        };
    }
}
```

Through these patterns, you can build a robust and high-performance database layer. Each pattern should be selectively applied according to specific situations to achieve optimal results.

---
title: "Java 애플리케이션을 위한 데이터베이스 설계 패턴"
meta_title: ""
description: "JPA와 Spring Data를 활용한 효율적인 데이터베이스 설계 패턴과 최적화 기법들을 알아봅니다."
date: 2022-04-05T05:00:00Z
image: "/images/service-2.png"
categories: ["백엔드", "데이터베이스"]
author: "Kigo"
tags: ["JPA", "Spring Data", "데이터베이스", "설계 패턴"]
draft: false
---

효율적인 Java 애플리케이션 개발을 위해서는 견고한 데이터베이스 설계가 필수입니다. JPA와 Spring Data를 활용하여 성능과 유지보수성을 모두 만족하는 데이터베이스 설계 패턴들을 알아보겠습니다.

## 엔티티 설계 원칙

### 기본 엔티티 구조

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

### 상속 매핑 전략

```java
// 조인 테이블 전략 (JOINED)
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

    // 공통 필드들
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

## 연관관계 매핑 패턴

### 일대다 연관관계 최적화

```java
@Entity
@Table(name = "categories")
public class Category {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    // 양방향 연관관계 - 성능을 위해 LAZY 로딩
    @OneToMany(mappedBy = "category", fetch = FetchType.LAZY, cascade = CascadeType.ALL)
    @BatchSize(size = 20) // N+1 문제 해결
    private List<Product> products = new ArrayList<>();

    // 연관관계 편의 메서드
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

    // 다대일 연관관계
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "category_id", nullable = false)
    private Category category;
}
```

### 다대다 연관관계 with 추가 속성

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

## Repository 패턴

### 커스텀 Repository 구현

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

        // 전체 개수 조회
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

## 성능 최적화 패턴

### 페이징과 정렬

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

### 배치 처리 최적화

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

### 캐싱 전략

```java
@Entity
@Cacheable
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class Category {
    // 엔티티 정의
}

@Service
public class CategoryService {

    @Cacheable(value = "categories", key = "#id")
    public Category findById(Long id) {
        return categoryRepository.findById(id)
            .orElseThrow(() -> new EntityNotFoundException("카테고리를 찾을 수 없습니다"));
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

## 트랜잭션 관리

### 선언적 트랜잭션

```java
@Service
@Transactional(readOnly = true)
public class OrderService {

    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;
    private final InventoryService inventoryService;

    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        // 상품 재고 확인
        Product product = productRepository.findById(request.getProductId())
            .orElseThrow(() -> new EntityNotFoundException("상품을 찾을 수 없습니다"));

        if (!inventoryService.hasStock(product.getId(), request.getQuantity())) {
            throw new InsufficientStockException("재고가 부족합니다");
        }

        // 주문 생성
        Order order = Order.builder()
            .product(product)
            .quantity(request.getQuantity())
            .totalPrice(product.getPrice().multiply(BigDecimal.valueOf(request.getQuantity())))
            .status(OrderStatus.PENDING)
            .build();

        Order savedOrder = orderRepository.save(order);

        // 재고 차감
        inventoryService.decreaseStock(product.getId(), request.getQuantity());

        return savedOrder;
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void processPayment(Long orderId, PaymentInfo paymentInfo) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new EntityNotFoundException("주문을 찾을 수 없습니다"));

        try {
            // 결제 처리 로직
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

### 프로그래밍적 트랜잭션

```java
@Service
public class DataMigrationService {

    private final PlatformTransactionManager transactionManager;

    public void migrateUserData(List<UserData> userData) {
        TransactionTemplate transactionTemplate = new TransactionTemplate(transactionManager);
        transactionTemplate.setIsolationLevel(TransactionDefinition.ISOLATION_READ_COMMITTED);

        for (UserData data : userData) {
            try {
                transactionTemplate.execute(status -> {
                    User user = new User(data.getEmail(), data.getName());
                    userRepository.save(user);

                    // 프로필 데이터 마이그레이션
                    Profile profile = new Profile(user, data.getProfileData());
                    profileRepository.save(profile);

                    return null;
                });
                log.info("사용자 마이그레이션 완료: {}", data.getEmail());
            } catch (Exception e) {
                log.error("사용자 마이그레이션 실패: {}", data.getEmail(), e);
                // 개별 실패는 전체 마이그레이션을 중단하지 않음
            }
        }
    }
}
```

## 감사(Auditing) 기능

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

이러한 패턴들을 통해 견고하고 성능이 우수한 데이터베이스 계층을 구축할 수 있습니다. 각 패턴은 특정 상황에 맞게 선택적으로 적용하여 최적의 결과를 얻으시기 바랍니다.

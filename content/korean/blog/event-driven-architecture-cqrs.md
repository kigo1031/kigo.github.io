---
title: "이벤트 기반 아키텍처와 CQRS: 확장 가능한 시스템 설계"
meta_title: "이벤트 기반 아키텍처 CQRS 패턴"
description: "이벤트 소싱, CQRS, 이벤트 스트리밍을 활용한 확장 가능하고 탄력적인 백엔드 시스템 구축 방법을 알아봅니다."
date: 2025-08-08T12:00:00Z
image: "/images/service-1.png"
categories: ["백엔드", "아키텍처", "DevOps"]
author: "Kigo"
tags: ["이벤트기반아키텍처", "CQRS", "이벤트소싱", "Apache Kafka", "마이크로서비스"]
draft: false
---

2025년 백엔드 개발에서 이벤트 기반 아키텍처(EDA)와 CQRS(Command Query Responsibility Segregation)는 대규모 분산 시스템의 핵심 패턴이 되었습니다. 실시간 데이터 처리와 높은 확장성을 요구하는 현대 애플리케이션에 필수적인 패턴들을 실전 코드와 함께 살펴보겠습니다.

## 이벤트 기반 아키텍처 핵심 개념

### 1. 이벤트 스토어 구현
```typescript
// 이벤트 정의
interface Event {
  id: string
  streamId: string
  eventType: string
  eventVersion: number
  data: any
  metadata: any
  timestamp: Date
}

interface EventStore {
  append(streamId: string, events: Event[]): Promise<void>
  read(streamId: string, fromVersion?: number): Promise<Event[]>
  subscribe(eventType: string, handler: EventHandler): void
}

// PostgreSQL 기반 이벤트 스토어
class PostgreSQLEventStore implements EventStore {
  constructor(private db: Pool) {}

  async append(streamId: string, events: Event[]): Promise<void> {
    const client = await this.db.connect()

    try {
      await client.query('BEGIN')

      for (const event of events) {
        await client.query(`
          INSERT INTO events (
            id, stream_id, event_type, event_version,
            data, metadata, timestamp
          ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [
          event.id,
          event.streamId,
          event.eventType,
          event.eventVersion,
          JSON.stringify(event.data),
          JSON.stringify(event.metadata),
          event.timestamp
        ])
      }

      await client.query('COMMIT')
    } catch (error) {
      await client.query('ROLLBACK')
      throw error
    } finally {
      client.release()
    }
  }

  async read(streamId: string, fromVersion = 0): Promise<Event[]> {
    const result = await this.db.query(`
      SELECT * FROM events
      WHERE stream_id = $1 AND event_version >= $2
      ORDER BY event_version ASC
    `, [streamId, fromVersion])

    return result.rows.map(row => ({
      id: row.id,
      streamId: row.stream_id,
      eventType: row.event_type,
      eventVersion: row.event_version,
      data: JSON.parse(row.data),
      metadata: JSON.parse(row.metadata),
      timestamp: row.timestamp
    }))
  }

  subscribe(eventType: string, handler: EventHandler): void {
    // PostgreSQL LISTEN/NOTIFY 활용
    this.db.connect().then(client => {
      client.query(`LISTEN ${eventType}`)
      client.on('notification', (msg) => {
        const event = JSON.parse(msg.payload)
        handler(event)
      })
    })
  }
}
```

### 2. 애그리게이트와 이벤트 소싱
```typescript
// 도메인 이벤트 정의
abstract class DomainEvent {
  abstract eventType: string
  constructor(
    public aggregateId: string,
    public timestamp: Date = new Date()
  ) {}
}

class UserRegisteredEvent extends DomainEvent {
  eventType = 'UserRegistered'

  constructor(
    aggregateId: string,
    public email: string,
    public name: string
  ) {
    super(aggregateId)
  }
}

class UserEmailChangedEvent extends DomainEvent {
  eventType = 'UserEmailChanged'

  constructor(
    aggregateId: string,
    public newEmail: string,
    public oldEmail: string
  ) {
    super(aggregateId)
  }
}

// 애그리게이트 루트
abstract class AggregateRoot {
  protected uncommittedEvents: DomainEvent[] = []
  protected version = 0

  protected addEvent(event: DomainEvent): void {
    this.uncommittedEvents.push(event)
    this.apply(event)
  }

  abstract apply(event: DomainEvent): void

  getUncommittedEvents(): DomainEvent[] {
    return [...this.uncommittedEvents]
  }

  markEventsAsCommitted(): void {
    this.uncommittedEvents = []
  }

  loadFromHistory(events: DomainEvent[]): void {
    events.forEach(event => {
      this.apply(event)
      this.version++
    })
  }
}

// 사용자 애그리게이트
class User extends AggregateRoot {
  private id: string
  private email: string
  private name: string
  private isActive: boolean

  static create(id: string, email: string, name: string): User {
    const user = new User()
    user.addEvent(new UserRegisteredEvent(id, email, name))
    return user
  }

  changeEmail(newEmail: string): void {
    if (this.email === newEmail) return

    this.addEvent(new UserEmailChangedEvent(
      this.id,
      newEmail,
      this.email
    ))
  }

  apply(event: DomainEvent): void {
    switch (event.eventType) {
      case 'UserRegistered':
        const registered = event as UserRegisteredEvent
        this.id = registered.aggregateId
        this.email = registered.email
        this.name = registered.name
        this.isActive = true
        break

      case 'UserEmailChanged':
        const emailChanged = event as UserEmailChangedEvent
        this.email = emailChanged.newEmail
        break
    }
  }

  getId(): string { return this.id }
  getEmail(): string { return this.email }
  getName(): string { return this.name }
}
```

## CQRS 패턴 구현

### 1. 커맨드와 쿼리 분리
```typescript
// 커맨드 정의
interface Command {
  id: string
  userId: string
  timestamp: Date
}

class RegisterUserCommand implements Command {
  constructor(
    public id: string,
    public userId: string,
    public email: string,
    public name: string,
    public timestamp: Date = new Date()
  ) {}
}

class ChangeUserEmailCommand implements Command {
  constructor(
    public id: string,
    public userId: string,
    public newEmail: string,
    public timestamp: Date = new Date()
  ) {}
}

// 커맨드 핸들러
interface CommandHandler<T extends Command> {
  handle(command: T): Promise<void>
}

class RegisterUserCommandHandler implements CommandHandler<RegisterUserCommand> {
  constructor(
    private userRepository: UserRepository,
    private eventStore: EventStore
  ) {}

  async handle(command: RegisterUserCommand): Promise<void> {
    // 비즈니스 규칙 검증
    const existingUser = await this.userRepository.findByEmail(command.email)
    if (existingUser) {
      throw new Error('User with this email already exists')
    }

    // 애그리게이트 생성
    const user = User.create(command.userId, command.email, command.name)

    // 이벤트 저장
    const events = user.getUncommittedEvents().map(event => ({
      id: generateId(),
      streamId: user.getId(),
      eventType: event.eventType,
      eventVersion: 1,
      data: event,
      metadata: { commandId: command.id },
      timestamp: event.timestamp
    }))

    await this.eventStore.append(user.getId(), events)
    user.markEventsAsCommitted()
  }
}

// 쿼리 모델
interface UserReadModel {
  id: string
  email: string
  name: string
  registeredAt: Date
  lastUpdated: Date
}

interface UserQueryRepository {
  findById(id: string): Promise<UserReadModel | null>
  findByEmail(email: string): Promise<UserReadModel | null>
  findAll(page: number, size: number): Promise<UserReadModel[]>
}

// 읽기 모델 프로젝션
class UserProjection {
  constructor(
    private queryRepository: UserQueryRepository,
    private eventStore: EventStore
  ) {
    this.subscribeToEvents()
  }

  private subscribeToEvents(): void {
    this.eventStore.subscribe('UserRegistered', this.handleUserRegistered.bind(this))
    this.eventStore.subscribe('UserEmailChanged', this.handleUserEmailChanged.bind(this))
  }

  private async handleUserRegistered(event: UserRegisteredEvent): Promise<void> {
    const readModel: UserReadModel = {
      id: event.aggregateId,
      email: event.email,
      name: event.name,
      registeredAt: event.timestamp,
      lastUpdated: event.timestamp
    }

    await this.queryRepository.save(readModel)
  }

  private async handleUserEmailChanged(event: UserEmailChangedEvent): Promise<void> {
    const user = await this.queryRepository.findById(event.aggregateId)
    if (user) {
      user.email = event.newEmail
      user.lastUpdated = event.timestamp
      await this.queryRepository.save(user)
    }
  }
}
```

### 2. 이벤트 버스와 메시지 브로커
```typescript
// Apache Kafka 이벤트 버스
import { Kafka, Producer, Consumer } from 'kafkajs'

class KafkaEventBus {
  private kafka: Kafka
  private producer: Producer
  private consumers: Map<string, Consumer> = new Map()

  constructor(brokers: string[]) {
    this.kafka = new Kafka({
      clientId: 'event-bus',
      brokers
    })
    this.producer = this.kafka.producer()
  }

  async initialize(): Promise<void> {
    await this.producer.connect()
  }

  async publish(topic: string, events: DomainEvent[]): Promise<void> {
    const messages = events.map(event => ({
      key: event.aggregateId,
      value: JSON.stringify(event),
      headers: {
        eventType: event.eventType,
        timestamp: event.timestamp.toISOString()
      }
    }))

    await this.producer.send({
      topic,
      messages
    })
  }

  async subscribe(
    topic: string,
    groupId: string,
    handler: (event: DomainEvent) => Promise<void>
  ): Promise<void> {
    const consumer = this.kafka.consumer({ groupId })
    await consumer.connect()
    await consumer.subscribe({ topic })

    await consumer.run({
      eachMessage: async ({ message }) => {
        try {
          const event = JSON.parse(message.value?.toString() || '{}')
          await handler(event)
        } catch (error) {
          console.error('Event processing failed:', error)
          // 데드 레터 큐로 전송 또는 재시도 로직
        }
      }
    })

    this.consumers.set(`${topic}-${groupId}`, consumer)
  }

  async shutdown(): Promise<void> {
    await this.producer.disconnect()

    for (const consumer of this.consumers.values()) {
      await consumer.disconnect()
    }
  }
}
```

## 실시간 이벤트 처리

### 1. 이벤트 스트림 처리
```typescript
// 이벤트 스트림 프로세서
class EventStreamProcessor {
  private isRunning = false
  private checkpointInterval = 5000 // 5초
  private lastCheckpoint = 0

  constructor(
    private eventStore: EventStore,
    private projections: EventProjection[]
  ) {}

  async start(): Promise<void> {
    this.isRunning = true
    this.lastCheckpoint = await this.loadCheckpoint()

    console.log(`Starting event stream processor from checkpoint: ${this.lastCheckpoint}`)

    while (this.isRunning) {
      try {
        const events = await this.fetchEvents(this.lastCheckpoint, 100)

        if (events.length > 0) {
          await this.processEvents(events)
          this.lastCheckpoint = events[events.length - 1].eventVersion
          await this.saveCheckpoint(this.lastCheckpoint)
        } else {
          await this.sleep(1000) // 1초 대기
        }
      } catch (error) {
        console.error('Event processing error:', error)
        await this.sleep(5000) // 에러 시 5초 대기
      }
    }
  }

  stop(): void {
    this.isRunning = false
  }

  private async processEvents(events: Event[]): Promise<void> {
    for (const event of events) {
      for (const projection of this.projections) {
        if (projection.canHandle(event.eventType)) {
          await projection.handle(event)
        }
      }
    }
  }

  private async fetchEvents(fromVersion: number, limit: number): Promise<Event[]> {
    // 글로벌 이벤트 스트림에서 이벤트 조회
    return this.eventStore.readGlobalStream(fromVersion, limit)
  }

  private async loadCheckpoint(): Promise<number> {
    // 체크포인트 저장소에서 마지막 처리된 이벤트 버전 로드
    return 0 // 구현 필요
  }

  private async saveCheckpoint(version: number): Promise<void> {
    // 체크포인트 저장
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}
```

### 2. 복합 이벤트 처리 (CEP)
```typescript
// 복합 이벤트 정의
interface EventPattern {
  name: string
  events: string[]
  timeWindow: number // milliseconds
  condition: (events: DomainEvent[]) => boolean
}

class ComplexEventProcessor {
  private eventBuffer: Map<string, DomainEvent[]> = new Map()
  private patterns: EventPattern[] = []

  addPattern(pattern: EventPattern): void {
    this.patterns.push(pattern)
  }

  processEvent(event: DomainEvent): void {
    // 이벤트를 버퍼에 추가
    const key = `${event.aggregateId}-${event.eventType}`
    const events = this.eventBuffer.get(key) || []
    events.push(event)
    this.eventBuffer.set(key, events)

    // 패턴 매칭 확인
    this.checkPatterns(event.aggregateId)

    // 오래된 이벤트 정리
    this.cleanupOldEvents()
  }

  private checkPatterns(aggregateId: string): void {
    for (const pattern of this.patterns) {
      const relevantEvents = this.getEventsForPattern(aggregateId, pattern)

      if (relevantEvents.length >= pattern.events.length) {
        const sortedEvents = relevantEvents.sort((a, b) =>
          a.timestamp.getTime() - b.timestamp.getTime()
        )

        // 시간 윈도우 확인
        const firstEvent = sortedEvents[0]
        const lastEvent = sortedEvents[sortedEvents.length - 1]
        const timeDiff = lastEvent.timestamp.getTime() - firstEvent.timestamp.getTime()

        if (timeDiff <= pattern.timeWindow && pattern.condition(sortedEvents)) {
          this.triggerPattern(pattern, sortedEvents)
        }
      }
    }
  }

  private getEventsForPattern(aggregateId: string, pattern: EventPattern): DomainEvent[] {
    const events: DomainEvent[] = []

    for (const eventType of pattern.events) {
      const key = `${aggregateId}-${eventType}`
      const bufferEvents = this.eventBuffer.get(key) || []
      events.push(...bufferEvents)
    }

    return events
  }

  private triggerPattern(pattern: EventPattern, events: DomainEvent[]): void {
    console.log(`Pattern triggered: ${pattern.name}`, events)
    // 복합 이벤트 발생 처리
  }

  private cleanupOldEvents(): void {
    const now = Date.now()
    const maxAge = 60000 // 1분

    for (const [key, events] of this.eventBuffer.entries()) {
      const validEvents = events.filter(event =>
        now - event.timestamp.getTime() < maxAge
      )

      if (validEvents.length === 0) {
        this.eventBuffer.delete(key)
      } else {
        this.eventBuffer.set(key, validEvents)
      }
    }
  }
}

// 사용 예시
const cep = new ComplexEventProcessor()

cep.addPattern({
  name: 'SuspiciousUserActivity',
  events: ['UserLoginFailed', 'UserLoginFailed', 'UserLoginFailed'],
  timeWindow: 300000, // 5분
  condition: (events) => events.length >= 3
})
```

## 오류 처리 및 복원력

### 1. 보상 트랜잭션 (Saga 패턴)
```typescript
// Saga 상태
enum SagaStatus {
  Started = 'started',
  Completed = 'completed',
  Failed = 'failed',
  Compensating = 'compensating',
  Compensated = 'compensated'
}

interface SagaStep {
  name: string
  execute: () => Promise<void>
  compensate: () => Promise<void>
}

class Saga {
  private steps: SagaStep[] = []
  private executedSteps: SagaStep[] = []
  private status = SagaStatus.Started

  addStep(step: SagaStep): void {
    this.steps.push(step)
  }

  async execute(): Promise<void> {
    try {
      for (const step of this.steps) {
        await step.execute()
        this.executedSteps.push(step)
      }
      this.status = SagaStatus.Completed
    } catch (error) {
      this.status = SagaStatus.Failed
      await this.compensate()
      throw error
    }
  }

  private async compensate(): Promise<void> {
    this.status = SagaStatus.Compensating

    // 실행된 단계들을 역순으로 보상
    for (const step of this.executedSteps.reverse()) {
      try {
        await step.compensate()
      } catch (error) {
        console.error(`Compensation failed for step: ${step.name}`, error)
      }
    }

    this.status = SagaStatus.Compensated
  }
}
```

### 2. 이벤트 재처리 및 멱등성
```typescript
class IdempotentEventHandler {
  private processedEvents = new Set<string>()

  async handle(event: DomainEvent, handler: () => Promise<void>): Promise<void> {
    const eventId = this.generateEventId(event)

    if (this.processedEvents.has(eventId)) {
      console.log(`Event already processed: ${eventId}`)
      return
    }

    try {
      await handler()
      this.processedEvents.add(eventId)
    } catch (error) {
      console.error(`Event processing failed: ${eventId}`, error)
      throw error
    }
  }

  private generateEventId(event: DomainEvent): string {
    return `${event.aggregateId}-${event.eventType}-${event.timestamp.getTime()}`
  }
}
```

## 마무리

이벤트 기반 아키텍처와 CQRS의 핵심 이점:

- **확장성**: 읽기와 쓰기 분리로 독립적 확장
- **탄력성**: 장애 격리와 복구 능력
- **유연성**: 새로운 기능 추가 용이
- **감사 가능성**: 모든 변경 이력 추적
- **실시간 처리**: 이벤트 스트림 기반 반응형 시스템

2025년 대규모 분산 시스템에서는 이러한 패턴들이 필수적이며, 특히 실시간 데이터 처리와 높은 가용성이 요구되는 서비스에서 그 가치가 더욱 두드러집니다.

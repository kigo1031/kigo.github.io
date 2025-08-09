---
title: "Event-Driven Architecture and CQRS: Scalable System Design"
meta_title: "Event-Driven Architecture CQRS Patterns"
description: "Learn how to build scalable and resilient backend systems using event sourcing, CQRS, and event streaming with practical implementation examples."
date: 2025-08-08T12:00:00Z
image: "/images/service-1.png"
categories: ["Backend", "Architecture", "DevOps"]
author: "Kigo"
tags: ["Event-Driven Architecture", "CQRS", "Event Sourcing", "Apache Kafka", "Microservices"]
draft: false
---

Event-driven architecture (EDA) and CQRS (Command Query Responsibility Segregation) have become core patterns for large-scale distributed systems in 2025 backend development. Let's explore these essential patterns for modern applications requiring real-time data processing and high scalability with practical code examples.

## Core Concepts of Event-Driven Architecture

### 1. Event Store Implementation
```typescript
// Event definition
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

// PostgreSQL-based event store
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
    // Using PostgreSQL LISTEN/NOTIFY
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

### 2. Aggregates and Event Sourcing
```typescript
// Domain event definition
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

// Aggregate root
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

// User aggregate
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

## CQRS Pattern Implementation

### 1. Command and Query Separation
```typescript
// Command definition
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

// Command handler
interface CommandHandler<T extends Command> {
  handle(command: T): Promise<void>
}

class RegisterUserCommandHandler implements CommandHandler<RegisterUserCommand> {
  constructor(
    private userRepository: UserRepository,
    private eventStore: EventStore
  ) {}

  async handle(command: RegisterUserCommand): Promise<void> {
    // Business rule validation
    const existingUser = await this.userRepository.findByEmail(command.email)
    if (existingUser) {
      throw new Error('User with this email already exists')
    }

    // Create aggregate
    const user = User.create(command.userId, command.email, command.name)

    // Store events
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

// Query model
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

// Read model projection
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

### 2. Event Bus and Message Broker
```typescript
// Apache Kafka event bus
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
          // Send to dead letter queue or retry logic
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

## Real-time Event Processing

### 1. Event Stream Processing
```typescript
// Event stream processor
class EventStreamProcessor {
  private isRunning = false
  private checkpointInterval = 5000 // 5 seconds
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
          await this.sleep(1000) // Wait 1 second
        }
      } catch (error) {
        console.error('Event processing error:', error)
        await this.sleep(5000) // Wait 5 seconds on error
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
    // Fetch events from global event stream
    return this.eventStore.readGlobalStream(fromVersion, limit)
  }

  private async loadCheckpoint(): Promise<number> {
    // Load last processed event version from checkpoint store
    return 0 // Implementation needed
  }

  private async saveCheckpoint(version: number): Promise<void> {
    // Save checkpoint
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}
```

### 2. Complex Event Processing (CEP)
```typescript
// Complex event definition
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
    // Add event to buffer
    const key = `${event.aggregateId}-${event.eventType}`
    const events = this.eventBuffer.get(key) || []
    events.push(event)
    this.eventBuffer.set(key, events)

    // Check pattern matching
    this.checkPatterns(event.aggregateId)

    // Clean up old events
    this.cleanupOldEvents()
  }

  private checkPatterns(aggregateId: string): void {
    for (const pattern of this.patterns) {
      const relevantEvents = this.getEventsForPattern(aggregateId, pattern)

      if (relevantEvents.length >= pattern.events.length) {
        const sortedEvents = relevantEvents.sort((a, b) =>
          a.timestamp.getTime() - b.timestamp.getTime()
        )

        // Check time window
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
    // Handle complex event occurrence
  }

  private cleanupOldEvents(): void {
    const now = Date.now()
    const maxAge = 60000 // 1 minute

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

// Usage example
const cep = new ComplexEventProcessor()

cep.addPattern({
  name: 'SuspiciousUserActivity',
  events: ['UserLoginFailed', 'UserLoginFailed', 'UserLoginFailed'],
  timeWindow: 300000, // 5 minutes
  condition: (events) => events.length >= 3
})
```

## Error Handling and Resilience

### 1. Compensating Transactions (Saga Pattern)
```typescript
// Saga status
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

    // Compensate executed steps in reverse order
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

### 2. Event Reprocessing and Idempotency
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

## Conclusion

Key benefits of event-driven architecture and CQRS:

- **Scalability**: Independent scaling through read/write separation
- **Resilience**: Fault isolation and recovery capabilities
- **Flexibility**: Easy addition of new features
- **Auditability**: Complete change history tracking
- **Real-time Processing**: Event stream-based reactive systems

These patterns are essential for large-scale distributed systems in 2025, especially for services requiring real-time data processing and high availability.

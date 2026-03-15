---
type: architecture
tags:
  - rabbitmq
  - messaging
  - async
  - inter-service
  - integration
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[architecture/system-overview]]'
  - '[[patterns/feature-toggles-unleash]]'
  - '[[modules/ttt-service]]'
  - '[[modules/vacation-service]]'
  - '[[modules/email-service]]'
  - '[[modules/calendar-service]]'
  - '[[modules/accounting-backend]]'
branch: release/2.1
---
# RabbitMQ Inter-Service Messaging

All 4 TTT services communicate asynchronously via RabbitMQ using Spring AMQP. Each service has an `integration/mq/` module with constants and listeners.

## Exchanges (8)

| Exchange | Type | Publisher | Purpose |
|---|---|---|---|
| `ttt.fanout` | Fanout | TTT, Vacation | Broadcast CRUD events to all services |
| `ttt.email.topic` | Topic | TTT, Vacation | Async email sending (when `email-async` toggle enabled) |
| `ttt.backend.employee.topic` | Topic | TTT | Employee changes (CS sync, manual edits) |
| `ttt.backend.officePeriod.topic` | Topic | TTT | Office period advance/revert |
| `ttt.backend.officePeriod.reopened.topic` | Topic | TTT | Period reopened events |
| `ttt.backend.employeePeriod.topic` | Topic | TTT | Employee-specific period changes |
| `ttt.calendar.topic` | Topic | Calendar | Production calendar changes |
| `ttt.calendar.deleted.topic` | Topic | Calendar | Calendar day overrides deleted |

## Service Roles

**TTT Backend** (producer + consumer):
- Publishes: employee changes, period changes, email requests, CRUD events
- Consumes: `ttt.fanout` (own queue), employee month norm context calculated
- Listeners: CrudMessageListener, EmployeeChangedListener, PeriodChangedListener, PeriodReopenedListener, SendEmailListener, SystemListener, EmployeeMonthNormContextCalculatedListener

**Vacation** (primary consumer):
- Publishes: email requests, CRUD events
- Consumes: ttt.fanout, all 5 TTT-backend topics, both calendar topics — **8 subscriptions**
- Key reactions: calendar change → recalculate day-offs; period change → recalculate vacation days; employee change → update employee records

**Email** (consumer only):
- Consumes: `ttt.fanout`, `ttt.email.topic`
- Listeners: CrudMessageListener, SendEmailListener

**Frontend** (consumer only):
- Consumes: `ttt.fanout`
- Listener: CrudMessageListener (cache invalidation)

## Configuration

All services use identical retry config:
- **Max attempts**: 3
- **Backoff**: Exponential — 2s initial, 2x multiplier, 100s max
- **Ack mode**: AUTO
- **Requeue on rejection**: false (messages go to DLQ or are dropped)
- **Serialization**: Jackson2JsonMessageConverter

## Key Message Flows

1. **Period advance** (accounting): TTT publishes to officePeriod.topic → Vacation recalculates vacation days + payments
2. **Calendar update**: Calendar publishes to calendar.topic → Vacation recalculates day-off balances
3. **Async email**: TTT/Vacation publish to email.topic → Email service dequeues and sends
4. **Employee sync**: TTT publishes employee changes to employee.topic → Vacation updates employee records
5. **CRUD broadcast**: Any service publishes to ttt.fanout → All other services receive (cache invalidation)

## Test Implications

- RabbitMQ is required for integration tests (TestContainers used in both TTT and Vacation test suites)
- Period change tests must verify Vacation service receives and processes the MQ message
- Email tests should verify message reaches email service queue
- **No DLQ configuration found** — failed messages after 3 retries are silently dropped

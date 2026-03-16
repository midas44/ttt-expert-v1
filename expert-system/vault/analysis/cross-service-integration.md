---
type: analysis
tags:
  - cross-service
  - rabbitmq
  - websocket
  - cs-sync
  - integration
  - event-driven
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[architecture/rabbitmq-messaging]]'
  - '[[architecture/websocket-events]]'
  - '[[modules/companystaff-integration]]'
  - '[[modules/calendar-service-deep-dive]]'
  - '[[modules/vacation-service-deep-dive]]'
  - '[[modules/accounting-service-deep-dive]]'
  - '[[modules/dayoff-service-deep-dive]]'
  - '[[modules/email-notification-deep-dive]]'
---
# Cross-Service Integration Architecture

## Overview

TTT uses **event-driven architecture** via RabbitMQ for cross-service communication. The 4 services (TTT Backend, Vacation, Calendar, Email) communicate through 8 exchanges and 9 queues. All services also share a **CompanyStaff (CS) synchronization** pattern for employee/office data. WebSocket (STOMP) is used for real-time UI updates within the TTT Backend only.

## 1. RabbitMQ Event Architecture

### Exchange/Queue Topology

| Exchange | Type | Publishers | Consumers |
|----------|------|-----------|-----------|
| `ttt.fanout` | Fanout | System clock | TTT (`ttt.fanout.ttt-queue`), Email (`ttt.fanout.email-queue`), Calendar (`ttt.fanout.calendar-queue`) |
| `ttt.calendar.topic` | Topic | Calendar Service | Vacation (`ttt.calendar.topic.vacation-queue`) |
| `ttt.calendar.deleted.topic` | Topic | Calendar Service | Vacation (`ttt.calendar.deleted.topic.vacation-queue`) |
| `ttt.backend.officePeriod.topic` | Topic | TTT Backend | Vacation (`ttt.backend.officePeriod.topic.vacation-queue`) |
| `ttt.backend.officePeriod.reopened.topic` | Topic | TTT Backend | Vacation (`ttt.backend.officePeriod.reopened.topic.vacation-queue`) |
| `ttt.backend.employee.topic` | Topic | TTT Backend, Vacation | Vacation (`ttt.backend.employee.topic.vacation-queue`), TTT (`ttt.backend.employee.topic.ttt-queue`) |
| `ttt.backend.employeePeriod.topic` | Topic | TTT Backend | Vacation (`ttt.backend.employeePeriod.topic.vacation-queue`) |
| `ttt.email.topic` | Topic | TTT Backend, Vacation | Email (`ttt.email.topic.send-email`) |

### Event Types and Routing

| Event | Routing Key | Publisher | Consumer Handler | Business Logic |
|-------|-------------|----------|-----------------|----------------|
| `CalendarChangedEvent` | `calendar-changed` | Calendar → `ttt.calendar.topic` | Vacation: `CalendarChangedEventHandler` | CalendarUpdateProcessor: detect day-off conflicts, recalculate vacations, trigger month norm recalc |
| `CalendarDeletedEvent` | `calendar-deleted` | Calendar → `ttt.calendar.deleted.topic` | Vacation: `CalendarDeletedEventHandler` | Delete NEW/APPROVED day-offs, recalculate parent vacations, send notifications |
| `PeriodChangedEvent` | `period-changed` | TTT → `ttt.backend.officePeriod.topic` | Vacation: `PeriodChangedEventHandler` | APPROVE type only: recalculate available days, reject out-of-date day-offs, mark vacation for payment cron |
| `PeriodReopenedEvent` | `period-reopened` | TTT → `ttt.backend.officePeriod.reopened.topic` | Vacation: `PeriodReopenedEventHandler` | APPROVE type only: reverse available days recalculation |
| `EmployeeChangedEvent` | `employee-changed` | TTT → `ttt.backend.employee.topic` | Vacation: `EmployeeChangedEventHandler` | Evict employee cache by login |
| `EmployeeReportedToProjectEvent` | `employee-reported-to-project` | TTT → `ttt.backend.employee.topic` | Vacation: `EmployeeMessageListener` | Project membership tracking |
| `EmployeeDeletedReportFromProjectEvent` | `employee-deleted-report-from-project` | TTT → `ttt.backend.employee.topic` | Vacation: `EmployeeMessageListener` | Project membership tracking |
| `EmployeePeriodChangedEvent` | `employee-period-changed` | TTT → `ttt.backend.employeePeriod.topic` | Vacation: `EmployeePeriodChangedListener` | Employee-specific period updates |
| `EmployeeMonthNormContextCalculatedEvent` | `employee-month-norm-context-calculated` | Vacation → `ttt.backend.employee.topic` | TTT: `EmployeeMonthNormContextCalculatedEventHandler` | Save month norm + reported effort via StatisticReportSyncService |
| `SendEmailEvent` | `send-email` | TTT & Vacation → `ttt.email.topic` | Email: `SendEmailEventHandler` | Convert SendEmailMQ → EmailBO, save for batch sending |
| `SystemClockChangedEvent` | (broadcast) | System → `ttt.fanout` | All 3: `CrudMessageListener` | Clock synchronization (timemachine env) |

### Message Routing Pattern

All services use the **AbstractMessageListener** pattern:

```java
// Message arrives with TYPE header → lookup event class → lookup handler → deserialize + handle
public void onEvent(final Message message) {
    String type = message.getMessageProperties().getHeader("TYPE");
    Class<? extends MqEvent> eventClass = getEventByType(type);
    MqEventHandler handler = handlersMap.get(eventClass);
    MqEvent mqEvent = objectMapper.readValue(message.getBody(), eventClass);
    handler.handle(mqEvent);
}
```

All publishers use `@Async @EventListener` with `RabbitTemplate.convertAndSend()`. All handlers use `@Timed(value = "rabbit_handler")` for Micrometer metrics.

### Error Handling

- **Missing handler**: `IllegalStateException` thrown → message rejected
- **Deserialization failure**: `IllegalStateException` thrown → message rejected  
- **No DLQ configured**: Failed messages are lost — no Dead Letter Queue
- **No retry mechanism**: One-shot processing, no redelivery configuration observed

### Design Issues

1. **No DLQ** — failed messages are silently lost after exception
2. **No idempotency** — handlers don't check for duplicate event processing
3. **@Async on publishers** — event publication can fail silently after source transaction commits

## 2. Calendar-Vacation Interaction

The most complex cross-service interaction. Calendar changes trigger cascading updates to vacations, day-offs, and working day norms.

### Calendar Changed → Vacation Recalculation

```
Calendar: admin adds/modifies/removes calendar day
  → CalendarChangedApplicationEvent (Spring event)
  → CalendarChangedApplicationEventListener (@Async @EventListener)
  → RabbitMQ: ttt.calendar.topic / routing key: calendar-changed
  → Vacation: CalendarChangedListener
  → CalendarChangedEventHandler
      ├── CalendarUpdateProcessor.process()
      │   ├── For each changed day:
      │   │   ├── If day.diff == 1 (new working day): insert VacationStatusUpdate(NEW_FOR_DAYS_CHECK)
      │   │   ├── If day is half-working-day (duration==7) or non-working (diff==-1, duration==0):
      │   │   │   ├── Find employees with day-offs on this date
      │   │   │   ├── Publish CalendarUpdateHasDayOffConflictEvent per employee
      │   │   │   │   (reschedules day-off to previous working day)
      │   │   │   └── Exclude conflict employees from recalculation
      │   │   └── VacationCalendarUpdateService.recalculateVacations()
      │   │       ├── Find all vacations spanning changed date
      │   │       └── Recalculate each vacation (working days count changes)
      │   └── Special case: day-off moved between different vacations
      │       → used_vacation_days stays constant
      └── sendUpdateMonthNormEventForEmployeesFromAffectedOffices()
          → For each affected date, for each office:
            → MonthNormContextCalculator.prepareMonthNormCalculationContextForEmployees()
            → Publish EmployeeMonthNormContextCalculatedApplicationEvent
            → RabbitMQ: ttt.backend.employee.topic → TTT Backend
            → StatisticReportSyncService.saveMonthNormAndReportedEffortForEmployees()
```

**Key constant**: `HALF_WORKING_DAY = 7` (hours, presumably)

### Calendar Deleted → Day-Off Cascade

```
Calendar: admin deletes a calendar day entry (e.g., removes holiday)
  → CalendarDeletedApplicationEvent
  → RabbitMQ: ttt.calendar.deleted.topic / routing key: calendar-deleted
  → Vacation: CalendarDeletedEventHandler
      ├── EmployeeDayOffCalendarUpdateService.deleteDayOffs()
      │   ├── Find day-off requests with status NEW or APPROVED for deleted date + office
      │   ├── Find day-off entities for deleted date + office
      │   ├── Update request statuses (mark deleted)
      │   ├── Delete day-off entities from DB
      │   ├── For each deleted day-off:
      │   │   └── Recalculate parent vacation (simulate +1 working day change)
      │   └── Publish EmployeeDayOffDeletedFromCalendarEvent
      │       → EmployeeDayOffDeletedFromCalendarSendNotificationEventHandler
      │       → notificationHelper.notifyCalendarDeletedToEmployee()
      └── sendUpdateMonthNormEventForEmployeesFromAffectedOffices()
          → Same month norm recalc cascade as CalendarChanged
```

### Period Changed → Vacation Impact

```
TTT Backend: accountant advances office period
  → OfficePeriodChangedApplicationEvent
  → RabbitMQ: ttt.backend.officePeriod.topic / routing key: period-changed
  → Vacation: PeriodChangedEventHandler
      (only for APPROVE period type)
      ├── AvailableDaysRecalculationService.recalculate(officeId, date)
      ├── EmployeeDayOffService.rejectedBySystem(officeId, date)
      │   → Reject all employee day-offs past the new period boundary
      └── VacationStatusUpdatesRepository.insert(officeId, prevMonth, NEW_FOR_PAID)
          → Marks vacations for payment processing by cron job
```

### Period Reopened → Reverse Recalculation

```
TTT Backend: accountant reverts/reopens a period
  → OfficePeriodReopenedApplicationEvent
  → RabbitMQ: ttt.backend.officePeriod.reopened.topic
  → Vacation: PeriodReopenedEventHandler
      (only for APPROVE period type)
      └── AvailableDaysRecalculationService.recalculationReverse(officeId, date)
          → Rolls back vacation day changes made during period advance
```

## 3. CompanyStaff (CS) Synchronization

### Architecture

```
Scheduled Cron Job (per service)
  → CSSyncLauncher.sync(fullSync)
      → Feature toggle check: CS_SYNC-{env}
      → CSSyncServiceV2.sync()
          → CSEntitySyncLauncher.sync(synchronizer, pageSize=50, fullSync)
              ├── Build CSPageRequest (with updatedAfter for incremental)
              ├── Fetch entities from CompanyStaff API (page by page)
              ├── Submit each entity to thread pool (10s timeout per entity)
              ├── Track failures in CsSyncFailedEmployeeRepository
              ├── On success: delete from failed repo
              └── Post-process if any succeeded
```

### Sync Scope per Service

| Service | Employee Sync | Contractor Sync | Office Sync | Post-Processors |
|---------|:---:|:---:|:---:|---|
| TTT Backend | ✓ | ✓ | ✓ | 7: DeptMgrRole, ProjMgrRole, Cache, Token, OfficeDirectorRole, AccountantRole, OfficeHRRole |
| Vacation | ✓ | ✗ | ✓ | 2: EmployeeNameDuplicates, EmployeeCache |
| Calendar | ✗ | ✗ | ✓ | None (startup full sync only for office-calendar mapping) |

### TTT Backend Post-Processors

1. **DepartmentManagerRolePostProcessor**: Assign/remove `ROLE_DEPARTMENT_MANAGER` based on CS department head status
2. **ProjectManagerRolePostProcessor**: Assign/remove `ROLE_PROJECT_MANAGER` — **BUG: removes `ROLE_DEPARTMENT_MANAGER` instead of `ROLE_PROJECT_MANAGER` on demotion** (line 39)
3. **EmployeeCachePostProcessor**: Invalidate office and employee caches
4. **TokenPostProcessor**: Generate API tokens for new employees without tokens
5. **OfficeDirectorRolePostProcessor**: Assign `ROLE_OFFICE_DIRECTOR` to office directors
6. **AccountantRolePostProcessor**: Assign `ROLE_ACCOUNTANT` to office accountants
7. **OfficeHRRolePostProcessor**: Assign `ROLE_OFFICE_HR` to HR personnel

### Vacation Service Employee Lifecycle Events

The vacation service detects employment state changes during CS sync and publishes events:

```java
// Detection logic in CSEmployeeSynchronizer:
isHired: (employee null or !working) AND csEmployee.working AND csEmployee.active → EmployeeHiredEvent
isFired: employee.working AND !csEmployee.working → EmployeeFiredEvent
isMaternityStarted: !employee.maternity AND csEmployee.maternity → EmployeeMaternityBeginEvent
isMaternityEnded: employee.maternity AND !csEmployee.maternity → EmployeeMaternityEndEvent
officeChanged: employee.officeId != csEmployee.officeId → EmployeeOfficeChangedEvent
always: → EmployeeChangedEvent (cache invalidation)
```

### Calendar Service Startup Sync

Calendar service performs **full sync on application startup** (`@EventListener ContextRefreshedEvent`):
- Warms up calendar calculations
- Ensures office-calendar mappings exist after data migration
- Assigns `Calendar.RUSSIAN_CALENDAR_ID` to offices in `SalaryOfficeIds.DEFAULT_CALENDAR_OFFICE_IDS`

### Design Issues

1. **[CRITICAL] ProjectManagerRolePostProcessor bug**: Line 39 removes `ROLE_DEPARTMENT_MANAGER` instead of `ROLE_PROJECT_MANAGER` when demoting
2. **Three separate CSEntitySyncLauncher implementations**: Identical logic copy-pasted across 3 services — no shared library
3. **Feature toggle gate**: CS_SYNC-{env} — if disabled, sync silently does nothing, no warning
4. **10-second entity timeout**: Entities that take >10s are retried next sync — can cause perpetual retry loops for complex entities
5. **Vacation service OfficePostProcessor**: Interface declared but no concrete implementation found

## 4. WebSocket (STOMP) Event Architecture

### Configuration

- Endpoints: `/ws` (WebSocket) and `/sockjs` (SockJS fallback)
- Topic prefix: `/topic`
- Auth: JWT or API token validated at STOMP CONNECT via `WsChannelInterceptorAdapter`

### STOMP Topics

| Topic Pattern | Event Types | Triggered By |
|---------------|------------|-------------|
| `/topic/projects/{projectId}/tasks` | TASK_RENAME, TASK_REFRESH_START, TASK_REFRESH_FINISH | Planner: task rename, section refresh |
| `/topic/employees/{login}/reports` | ADD, PATCH, DELETE, TASK_RENAME | Report CRUD operations, task rename cascade |
| `/topic/employees/{login}/assignments` | ADD, PATCH, DELETE, GENERATE, TASK_RENAME | Assignment CRUD, batch generation, task rename cascade |
| `/topic/employees/{login}/locks` | LOCK, UNLOCK | Cell lock/unlock in timesheet |
| `/topic/employees/{login}/selections` | SELECT | Cell selection in timesheet |

### Event Model

```java
class Event<T> {
    EventType type;      // 12 types: GENERATE, TASK_RENAME, TASK_REFRESH_START/FINISH, TRACKER_SYNC_START/FINISH, LOCK, UNLOCK, SELECT, ADD, PATCH, DELETE
    String emitterLogin; // Who triggered the event
    long timestamp;      // When
    T value;             // Payload (varies by event type)
}
```

### Event Services

- **TaskReportEventService**: Extends `AbstractEventService<TaskReportEvent>`, destination: `/topic/employees/{executorLogin}/reports`
- **TaskAssignmentEventService**: Extends `AbstractEventService<TaskAssignmentEvent>`, destination: `/topic/employees/{assigneeLogin}/assignments`
- **WsLockEventListener**: Direct listener, destination: `/topic/employees/{employeeLogin}/locks`
- **WsSelectionEventListener**: Direct listener, destination: `/topic/employees/{employeeLogin}/selections`
- **WsTaskEventListener**: Handles task rename/refresh, sends to `/topic/projects/{projectId}/tasks` + cascades to affected employee topics

### Design Issues

1. **No WebSocket reconnection awareness**: Server doesn't track client connection state
2. **Topic per employee login**: Could leak data if STOMP subscription isn't validated against authenticated user

## 5. Integration Design Issues Summary

| # | Category | Severity | Description |
|---|----------|----------|-------------|
| 1 | CS Sync | CRITICAL | ProjectManagerRolePostProcessor removes wrong role on demotion |
| 2 | RabbitMQ | MAJOR | No DLQ — failed messages are silently lost |
| 3 | RabbitMQ | MAJOR | No idempotency — duplicate events can cause double processing |
| 4 | RabbitMQ | MAJOR | @Async publishers can fail silently after source transaction commits |
| 5 | CS Sync | MAJOR | Three identical CSEntitySyncLauncher copies — no shared library |
| 6 | Calendar-Vacation | MINOR | HALF_WORKING_DAY hardcoded to 7 hours |
| 7 | CS Sync | MINOR | Vacation service OfficePostProcessor interface with no implementation |
| 8 | CS Sync | MINOR | 10-second entity timeout can cause perpetual retry for slow entities |
| 9 | WebSocket | MINOR | No STOMP subscription authorization — topic access not validated |
| 10 | CS Sync | MINOR | Feature toggle silently disables sync with no warning |

## Related Notes

- [[architecture/rabbitmq-messaging]] — Exchange/queue overview (Phase A)
- [[architecture/websocket-events]] — WebSocket topic overview (Phase A)
- [[modules/companystaff-integration]] — CS sync bugs (Phase A)
- [[modules/calendar-service-deep-dive]] — Calendar event publishing detail
- [[modules/email-notification-deep-dive]] — Email event consumption detail
- [[modules/vacation-service-deep-dive]] — Vacation state transitions
- [[modules/accounting-service-deep-dive]] — Period management (publishes PeriodChanged/Reopened)
- [[modules/dayoff-service-deep-dive]] — Day-off conflict resolution
- [[analysis/frontend-backend-validation-gaps]] — Validation gap analysis

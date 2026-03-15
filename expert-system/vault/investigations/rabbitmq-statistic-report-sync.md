---
type: investigation
tags:
  - rabbitmq
  - statistics
  - sync
  - async
  - messaging
  - statistic-report
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[architecture/rabbitmq-messaging]]'
  - '[[modules/statistics-service-implementation]]'
  - '[[modules/vacation-service-implementation]]'
branch: release/2.1
---

# RabbitMQ Statistic Report Sync Flow

Complete mapping of PATH 3 (MQ-triggered) for `statistic_report` table updates — from vacation/sick-leave change to database write.

## Trigger Chain

Vacation or sick-leave CRUD → Spring ApplicationEvent → event listeners → StatisticReportUpdateAfterVacationEventHelper → calculate norm context → publish local event → MQ publisher → RabbitMQ → TTT consumer → handler → sync service → DB write.

## Step-by-Step Flow

### 1. Event Listeners (Vacation Service)
Seven listeners trigger the flow:
- **Vacation**: Created, Updated, Deleted, StatusChanged event listeners
- **Sick Leave**: Created, Changed, Deleted event listeners

All call `statisticReportUpdateAfterVacationEventHelper.sendUpdateMonthNormEvent(bo)`.

### 2. Context Preparation
**StatisticReportUpdateAfterVacationEventHelper** extracts start/end months from the absence, then **MonthNormContextCalculatorImpl** prepares context:
- Fetches employee details
- Fetches all time-offs for affected month(s)
- Fetches employee office assignment
- Returns `List<EmployeeMonthNormContextPayload>` (one per affected month)

### 3. Local Event → MQ Publish
Publishes `EmployeeMonthNormContextCalculatedApplicationEvent` (local Spring event) → caught by **EmployeeMonthNormContextCalculatedApplicationEventListener** → publishes to RabbitMQ:
- **Exchange**: `ttt.backend.employee.topic` (Topic)
- **Routing Key**: `employee-month-norm-context-calculated`
- **Header**: `TYPE = "EMPLOYEE_MONTH_NORM_CONTEXT_CALCULATED"`

### 4. MQ Message Body
```
EmployeeMonthNormContextCalculatedEventPayloadMQ {
  contexts: [{
    employeeLogin: String,
    yearMonth: YearMonth,
    employeeTimeOffs: EmployeeTimeOffModel,
    employeeOffice: EmployeeOfficeModel
  }],
  eventType: VACATION_CHANGES | SICK_LEAVE_CHANGES | INITIAL_SYNC
}
```

### 5. TTT Backend Consumer
**EmployeeMonthNormContextCalculatedListener** on queue `ttt.backend.employee.topic.ttt-queue` → routes to **EmployeeMonthNormContextCalculatedEventHandler** via MqEventHandlerRegistry.

### 6. Sync Persistence
**StatisticReportSyncServiceImpl.saveMonthNormAndReportedEffortForEmployees()**:
1. Groups contexts by YearMonth
2. If INITIAL_SYNC: deletes stale employee records
3. For each employee/month: get-or-create StatisticReport, fetch reported effort, calculate personal + budget norms
4. Batch save via `StatisticReportRepository.saveAll()`

## Three Event Types
| Type | Trigger | Scope |
|---|---|---|
| VACATION_CHANGES | Vacation CRUD | Single employee, affected months |
| SICK_LEAVE_CHANGES | Sick leave CRUD | Single employee, affected months |
| INITIAL_SYNC | CS sync / period change | Batch of employees, with cleanup |

## Database (timemachine)
- **statistic_report**: 9,662 rows, 469 unique employees, date range 2025-01-01 to 2026-12-01
- Key: (employee_login, report_date)
- Fields: reported_effort, month_norm, budget_norm, comment

## Error Handling
- **No DLQ configured** per rabbitmq-messaging note — but the handler DOES throw `IllegalStateException` on deserialization/handler failure (Spring AMQP retry: 3 attempts, 2s exponential backoff, then drop)
- DB failures → transaction rollback via Spring `@Transactional`
- **Race condition**: No pessimistic locking between MQ events and task report events updating same statistic_report row

## Design Issues
1. **Race condition** between MQ and task report event paths updating same row
2. **Pre-computed time-off data** sent in MQ message rather than fetched at consumption time — potential staleness if messages queue
3. **No idempotency key** — duplicate MQ messages would recalculate redundantly
4. **Multi-month spans**: vacation spanning months sends separate events per month (not atomic)
5. **Future dates**: statistic_report has entries up to 2026-12-01, suggesting pre-computation for planning

## Related
- [[architecture/rabbitmq-messaging]]
- [[modules/statistics-service-implementation]]
- [[modules/vacation-service-implementation]]
- [[modules/sick-leave-service-implementation]]
- [[exploration/api-findings/cron-job-live-verification]]

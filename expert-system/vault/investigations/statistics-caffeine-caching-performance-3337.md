---
type: investigation
tags:
  - statistics
  - performance
  - caching
  - materialized-view
  - rabbitmq
  - sprint-15
  - ticket-3337
created: '2026-03-16'
updated: '2026-03-16'
status: active
related:
  - '[[modules/statistics-service-deep-dive]]'
  - '[[patterns/vacation-day-calculation]]'
  - '[[external/tickets/sprint-14-15-overview]]'
---
# Statistics Performance Enhancement — Caffeine Caching / Materialized View (#3337)

## Summary

Major architectural rework of the Statistic Employee Report page. Replaced on-the-fly calculation with a **materialized view pattern** using pre-computed data in the `statistic_report` database table. Added `reported_effort` and `month_norm` columns, event-driven cache invalidation via RabbitMQ, and daily scheduled sync. Frontend migrated from batched per-employee GET calls to bulk POST requests.

## Ticket Details

**Ticket:** #3337 — `[Optimization] Performance enhancement for Statistic Employee Report page`
**State:** opened (all 8 MRs merged, labeled "Production Ready")
**Sprint:** 15
**Author:** Quyen Nguyen (backend), Ilya Shumchenko (frontend)
**Assignee:** Olga Maksimova (QA)

## Architecture — Before vs After

### Before
```
Frontend → GET /v1/statistic?employeeLogin=X&startDate=...&endDate=...
  → StatisticReportService recalculates on each request:
    → VacationClient.getMonthNorm() (cross-service call)
    → TaskReportSummaryService.getReportedEffort() (DB aggregation)
  → Repeated per employee (batched in groups of 5-10)
```

### After (Materialized View)
```
Frontend → POST /v1/statistic {employeesLogins: [...], startDate, endDate}
  → StatisticReportService reads pre-computed data from statistic_report table
  → No cross-service calls at query time

Cache populated by:
  1. RabbitMQ events from Vacation service (vacation/sick-leave changes)
  2. TaskReportEventListener (task report add/patch/delete)
  3. Daily cron job at 4:00 AM (current + previous month)
  4. Manual trigger via test endpoint (non-prod)
```

## Database Changes

### Migration V2_1_26
```sql
ALTER TABLE statistic_report ADD COLUMN reported_effort DECIMAL(10,3);
ALTER TABLE statistic_report ADD COLUMN month_norm BIGINT;
```

### EqualsAndHashCode
Changed from `id` to natural key `{employeeLogin, reportDate}`.

## 8 Merged MRs

### !5013 (83 files, merged 2025-12-16 → development-ttt) — Core Architecture
- New `StatisticReportSyncService` with 4 methods:
  - `saveMonthNormAndReportedEffortForEmployees()` — initial sync + absence events
  - `updateMonthlyReportedEffortForEmployees()` — bulk task report rejection
  - `updateMonthlyReportedEffortForEmployee()` — individual task report CRUD
  - `getEmployeesWithTheirMonthNormAndReportedEffortForPeriodicalSync()` — scheduled sync
- New `StatisticReportScheduler` — cron `0 0 4 * * ?` (4:00 AM daily) with ShedLock
- New `StatisticReportSyncLauncher` — syncs previous and current month
- RabbitMQ topic exchange `TTT_BACKEND_EMPLOYEE_TOPIC`, routing key `employee-month-norm-context-calculated`
- `TaskReportEventListener` triggers effort recalculation on add/patch/delete
- `rejectByOfficeId()` return type → `Map<Long, Set<YearMonth>>` for targeted recalculation
- `calculatePersonalNorm()` extracted to `InternalReportingNormService`
- `Serializable` added to `EmployeeDayOffModel`, `EmployeeOfficeModel`, `EmployeeTimeOffItemModel`, `EmployeeTimeOffModel`
- New BOs: `EmployeeMonthNormContextBO`, `EmployeeMonthlyEffortBO`, `TaskReportSummaryContextBO`
- New test endpoint: `POST /v1/test/statistic-reports` (non-prod only)

### !5101 (9 files, merged 2025-12-26) — Role-Based Access
- `EmployeeRepository.findAllByOfficesOrManagers()` — JPQL query filtering by officeIds/managerId/techLeadId/hrId
- `StatisticReportRepository.findAllByEmployeeLoginInAndReportDate()` — batch lookup
- Method renamed: `getAllStatisticReportsByCurrentUserRoleOrByEmployeeLogin()`
- Role filtering:
  - **ADMIN, CHIEF_ACCOUNTANT** → see all employees
  - **OFFICE_DIRECTOR, ACCOUNTANT** → employees in their profit centers
  - **DEPARTMENT_MANAGER** → direct reports
  - **TECH_LEAD** → their employees
  - **OFFICE_HR** → their employees

### !5150 (2 files, merged 2026-01-26) — GET→POST Endpoints
- `StatisticController`: `@GetMapping → @PostMapping`, `@ModelAttribute → @RequestBody`
- `StatisticReportController /sick-leaves`: GET → POST
- Enables sending `employeesLogins` array in request body (bulk)

### !5152 (3 files, merged 2026-01-26) — CI/CD Pipeline
- Pre-release jobs restricted to `pre-release/v*` branches only
- New `TestPreReleaseController` at `GET /v1/test/pre-release` for CI/CD verification

### !5155 (7 files, merged 2026-01-26) — Frontend Bulk Migration
- **Deleted** `getAbsencesStatisticsForEmployees.ts` (86 lines of batched per-employee calls)
- **Created** `processStatisticsData.ts` — flattens and indexes responses by login
- Rewrote sagas: two parallel bulk POST requests instead of batched GETs:
  - `POST /v1/statistic {employeesLogins, startDate, endDate}` (vacations)
  - `POST /v1/statistic/sick-leaves {employeesLogins, startDate, endDate}` (sick leaves)
- Improved saga cancellation with `task.isRunning()` and `Map<string, Task>`
- `sickLeaves` PropTypes: `string → object`

### !5194 (2 files, merged 2026-02-02) — Frontend Empty Response Fix
- Empty/null response → dispatch `fetchReportsFailureAction()` to clear loading state
- Reducer clears `state.reports = []` on failure (was leaving stale data)

### !5200 (4 files, merged 2026-02-03) — Sick Leave Event Handlers
- `SickLeaveCreatedEventListener`, `SickLeaveChangedEventListener`, `SickLeaveDeletedEventListener` now call `statisticReportUpdateAfterVacationEventHelper.sendUpdateMonthNormEvent(sickLeave)`
- Handles sick leaves spanning two months (separate events for each)

### !5203 (11 files, merged 2026-02-04) — Event Type Discrimination (Critical Bug Fix)
- **New enum `StatisticReportUpdateEventType`**: `INITIAL_SYNC`, `VACATION_CHANGES`, `SICK_LEAVE_CHANGES`
- **Root cause fixed:** `deleteReportsWithEmploymentChanged()` was called for ALL events, deleting unrelated employees' statistic reports
- **Fix:** `deleteReportsWithEmploymentChanged()` now only executes when `eventType == INITIAL_SYNC`
- Event type added to MQ payload for discrimination

## Bugs Found During QA

### Bug #1 — Infinite Load on Out-of-Employment Period
Searching for employee and switching to month outside their employment period → infinite loading spinner (no data, no error state). **Fixed in !5194** (failure action clears loading).

### Bug #2 — Month Norm Not Updated After Sick Leave
`statistic_report.month_norm` didn't update after sick leave creation — only updated by daily cron sync. **Fixed in !5200** (sick leave event handlers trigger recalculation).

### Bug #3 — Unrelated Employee Reports Deleted
Vacation/sick leave events triggered `deleteReportsWithEmploymentChanged()` which deleted statistic reports of employees NOT affected by the event. **Fixed in !5203** (event type discrimination).

## Cache Invalidation Triggers

| Trigger | Update Type | Scope |
|---------|-------------|-------|
| Vacation create/update/delete | month_norm via RabbitMQ event | Affected employee + months |
| Sick leave create/change/delete | month_norm via RabbitMQ event | Affected employee + months (up to 2) |
| Task report add/patch/delete | reported_effort via direct call | Employee + report month |
| Office period change / bulk reject | reported_effort for affected employees | All employees in office + affected months |
| Daily cron (4:00 AM) | Full sync: month_norm + reported_effort | All employees, current + previous month |
| Manual test endpoint (non-prod) | Full sync | Configurable |

## Key API Changes

| Before | After |
|--------|-------|
| `GET /v1/statistic?employeeLogin=X&...` | `POST /v1/statistic {employeesLogins: [...], ...}` |
| `GET /v1/statistic/sick-leaves?...` | `POST /v1/statistic/sick-leaves {...}` |
| Per-employee calls (5-10 per batch) | Single bulk request per type |
| Real-time cross-service calculation | Pre-computed from cached table |

## Related
- [[modules/statistics-service-deep-dive]] — statistics module details
- [[patterns/vacation-day-calculation]] — norm deviation calculations
- [[external/tickets/sprint-14-15-overview]] — sprint context
- [[investigations/statistics-effective-bounds-norm]] — norm boundary investigation

---
type: module
tags:
  - backend
  - statistics
  - norm-calculation
  - caching
  - scheduled-jobs
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[ttt-report-service]]'
  - '[[frontend-statistics-module]]'
  - '[[ttt-service]]'
branch: release/2.1
---
# Statistics Service Implementation

Two subsystems: Live Statistics (real-time queries) and Statistic Report (pre-computed cache table).

## Database: `ttt_backend.statistic_report`

Per-employee monthly aggregate. Unique on (report_date, employee_login).
Fields: id, employee_login, report_date (1st of month), comment, reported_effort (decimal hours), month_norm (minutes), budget_norm (minutes), created_time, last_updated_time, updated_by.

## Norm Calculation

### Individual (Personal) Norm
1. Clamp date range to employee work period (effectiveBounds)
2. Fetch time-offs from vacation service: vacations + sick leaves + day-offs + maternity
3. Merge overlapping off-periods
4. totalNorm = calendar service working hours for office in period
5. personalNorm = max(0, totalNorm - offHours) → converted to minutes
6. Cached via Caffeine (TTL 5min, max 1000 entries)

### Budget Norm
Same as personal norm **except**: administrative vacations filtered out before building off-periods. Employee on unpaid leave still counted in budget.

## Three Update Paths

| Path | Trigger | Scope | Detail |
|------|---------|-------|--------|
| Nightly sync | Cron 4:00 AM, ShedLock | Current + previous month | Full recalc for all employees; deletes removed employees |
| Task report event | @TransactionalEventListener, @Async | Single employee/month | Updates reported_effort only; creates record if missing |
| MQ (RabbitMQ) | Vacation/sick leave change | Batch of employees | INITIAL_SYNC deletes extras; VACATION_CHANGES/SICK_LEAVE_CHANGES upsert only |

## Over-Report Detection

**Legacy**: `/v1/task-reports/employees-over-reported` — N+1 heavy, calculates on the fly.
**New**: `/v1/statistic/report/employees` — reads from statistic_report table.

Excess formula: `(reported - budgetNorm) / budgetNorm * 100`

ExcessStatus: HIGH (>0%), LOW (<0%), NEUTRAL (==), NA (budgetNorm=0).
Notification threshold from application_settings: ±10%.

## Access Control
| Role | Access |
|------|--------|
| ADMIN, CHIEF_ACCOUNTANT | All employees |
| OFFICE_DIRECTOR, ACCOUNTANT | Their office employees |
| DEPARTMENT_MANAGER, TECH_LEAD | Subordinates |
| OFFICE_HR | Assigned HR employees |
| EMPLOYEE only | Cannot access |

Live statistics path uses Resilience4j bulkhead to limit concurrent DB queries.

## Caching
- Caffeine in-memory: reportingNorm cache (5min TTL, 1000 entries) for calendar service calls
- statistic_report table itself is persistent cache for monthly aggregates

## Design Issues
1. **Race condition**: No pessimistic locking between MQ events and task report events
2. **budgetNorm null fallback**: Falls back to monthNorm when null
3. **Excess uses budgetNorm not personalNorm**: Administrative vacation counted against employee
4. **2-month sync only**: Scheduler syncs current + previous month; no historical back-fill
5. **Hardcoded CEO login**: `CEO_LOGIN = "ilnitsky"` in BaseStatistic
6. **Legacy over-report endpoint**: N+1 pattern, superseded by cache table

Links: [[ttt-report-service]], [[frontend-statistics-module]], [[ttt-service]]

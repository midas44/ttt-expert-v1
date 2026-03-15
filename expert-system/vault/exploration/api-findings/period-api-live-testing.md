---
type: exploration
tags:
  - period
  - API
  - testing
  - bugs
  - accounting
created: '2026-03-13'
updated: '2026-03-13'
status: active
branch: release/2.1
related:
  - '[[accounting-backend]]'
  - '[[rabbitmq-messaging]]'
  - '[[vacation-service]]'
---
# Period API Live Testing (Timemachine)

## Summary

Comprehensive API testing of report period and approve period management endpoints on timemachine environment. Tested all CRUD operations, edge cases, and validated business rules.

## Endpoints Tested

**GET (Read):**
- `GET /v1/offices/{id}/periods/report` — office-specific report period
- `GET /v1/offices/{id}/periods/approve` — office-specific approve period
- `GET /v1/offices/periods/report/min|max` — cross-office min/max report period
- `GET /v1/offices/periods/approve/min|max` — cross-office min/max approve period
- `GET /v1/periods/report/employees/{login}` — employee-level report period
- `GET /v1/periods/report/employees` — extended period employee list

**PATCH (Write):**
- `PATCH /v1/offices/{id}/periods/report` — advance/revert report period
- `PATCH /v1/offices/{id}/periods/approve` — advance/revert approve period

## Business Rules

### Report Period
- Must be first day of month (validated)
- Cannot precede approve period (strict `<` — equal is allowed)
- No upper bound limit or jump-size restriction
- Creates DB row if missing for that office

### Approve Period
- Should be first day of month but **NOT validated** (BUG — see below)
- Cannot exceed report period (strict `>`)
- Cannot go back more than 2 months from today
- Maximum 1-month jump in either direction
- Blocked by active extended periods in the office
- Publishes `PeriodChangedEvent` (advance) or `PeriodReopenedEvent` (revert) via [[rabbitmq-messaging|RabbitMQ]]
- Triggers vacation day recalculation on [[vacation-service]]

### Non-salary offices
- Filtered out by `office.salary = TRUE`
- GET returns computed default (today - 1 month), PATCH returns 404

### Caching
- `@Cacheable` on getPeriod(), evicted per PATCH via `SimpleKey(officeId, periodType)`

## Bugs Found

1. **Missing first-day-of-month validation on approve period** (HIGH) — `patchApprovePeriod()` at `OfficePeriodServiceImpl.java:104` lacks the `getDayOfMonth() != 1` check that `patchReportPeriod()` has at line 91. Any day of month accepted.

2. **NPE on null start** (HIGH) — PATCH with `{}` or `{"start":null}` → 500 NullPointerException at `start.getDayOfMonth()`. DTO has `@NotNull` but no `@Valid` on `@RequestBody`.

3. **Stack trace leakage** (MEDIUM) — Invalid date format returns full Java stack trace (98+ frames) in response body.

4. **Permission inconsistency** (MEDIUM) — GET report min/max requires JWT only (403 with API token), while GET approve min/max accepts both JWT and API token.

## Environment State

- 28 salary offices: all at Report=2026-03-01, Approve=2026-02-01
- 1 non-salary office (id=9): stale 2020-03-01 periods
- All mutations reverted after testing

## Key Files

- Controller: `ttt/rest/.../controller/v1/office/OfficePeriodController.java`
- Service: `ttt/service/service-impl/.../office/period/OfficePeriodServiceImpl.java`
- Extended periods: `ttt/rest/.../controller/v1/office/EmployeeExtendedPeriodController.java`
- MQ events: `PeriodChangedEvent.java`, `PeriodReopenedEvent.java`

## Related

- [[accounting-backend]] — period management is accounting feature
- [[database-schema]] — office_period table
- [[rabbitmq-messaging]] — PeriodChanged/PeriodReopened events
- [[vacation-service]] — recalculation triggered by period changes
- [[confirmation-flow-live-testing]] — approve period gates confirmation

---
type: exploration
tags:
  - api
  - accounting
  - testing
  - bugs
  - vacation-payment
  - periods
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[accounting-backend]]'
  - '[[vacation-service]]'
  - '[[ttt-service]]'
  - '[[security-patterns]]'
  - '[[api-surface]]'
branch: release/2.1
env: timemachine
---

# Accounting API Testing

Tested 25+ accounting-related endpoints on timemachine env via Swagger MCP and API token auth.

## Period Management

All 27 offices have identical periods: REPORT=2026-03-01, APPROVE=2026-02-01.

**BUG: Invalid office IDs return 200 with default data** — `officeId=99999`, `0`, `-1` all return a valid period response instead of 404. Silent fallback masks invalid input.

Individual employee periods work correctly. Invalid logins properly return 400 with `EmployeeLoginExistsValidator`.

Employee work periods (`GET /v1/employees/{login}/work-periods`) return empty arrays — the `employee_work_period` table is newly created but unpopulated.

## Vacation Payment

**Payment date calculation** (`GET /v1/paymentdates`) works but has edge cases:
- Reversed dates (start > end) accepted without validation
- Missing params return 400 with **full Java stack trace** (information disclosure)

**Available paid days** (`GET /v1/vacationdays/available`) works correctly, properly adjusts when `vacationId` provided (adds back referenced vacation's days).

**BUG: status=ALL causes 500 NPE** — `GET /v2/vacations?status=ALL` throws `NullPointerException` at `VacationRepositoryCustomImpl.buildCommonCondition:433`. The ALL enum is passed as null to repository, which doesn't handle null status.

## Vacation Days Corrections

**Data quality findings** from `GET /v1/vacationdays` (returns all 1609 employees, no pagination):
- 10 employees with negative balances (worst: -79 days, totalAccruedDays: -569.5)
- 75 employees with >50 days balance
- 23 employees with norm=0 and high balances (likely leadership/special accounts)
- Norm distribution: 0 (23), 15 (9), 19 (8), 21 (21), 24 (1537)

Days grouped by years can show negative values for corrections (e.g., `{year:2025, days:-60}`).

## Accounting Report — 403 Despite Valid Permissions

`GET /v1/reports/accounting` returns 403 even though permissions endpoint shows `ACCOUNTING: [VIEW, NOTIFY]`. The user has ROLE_ADMIN + ROLE_ACCOUNTANT. **Likely token-vs-session auth discrepancy** — same pattern as sick leave API testing.

## Cross-Cutting Issues

1. **Information disclosure**: Multiple endpoints return full Java stack traces in error responses (class names, method names, package structure)
2. **Pagination inconsistency**: v1 uses `size`/`totalElements`, v2 uses `pageSize`/`totalCount`. Vacation days list has NO pagination (1609 records in one response)
3. **Error response inconsistency**: TTT returns structured errors with `errorCode`; vacation sometimes includes `trace`, sometimes doesn't. Non-existent vacation IDs return 400 (not 404), non-existent offices return 200 with default data
4. **Auth/permission gap**: API token user has all roles but accounting report, notifications list, and period min/max return 403 — service-layer permission checks behave differently for token vs session auth

## Bugs Summary

| # | Severity | Description | Endpoint |
|---|----------|-------------|----------|
| 1 | MEDIUM | Invalid officeId returns 200 with default period | GET /v1/offices/{id}/periods/* |
| 2 | HIGH | status=ALL causes 500 NPE | GET /v2/vacations?status=ALL |
| 3 | MEDIUM | Reversed date range accepted without validation | GET /v1/paymentdates |
| 4 | MEDIUM | Full stack traces in error responses | Multiple endpoints |
| 5 | LOW | No pagination on vacation days list (1609 records) | GET /v1/vacationdays |

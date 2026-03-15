---
type: exploration
tags:
  - period-management
  - API
  - testing
  - office-period
  - accounting
  - bugs
created: '2026-03-13'
updated: '2026-03-13'
status: superseded
related:
  - '[[accounting-backend]]'
  - '[[office-period-model]]'
  - '[[security-patterns]]'
branch: release/2.1
superseded_by: '[[period-api-live-testing]]'
---

> **Superseded by [[period-api-live-testing]]** — this note's findings (permission inconsistency, NPE on null start, stack trace leakage) are all included in the comprehensive follow-up. Unique detail preserved: JWT header is `TTT_JWT_TOKEN` (not `Authorization: Bearer`), per `Headers.java`.


# Period Management API Testing — Timemachine

## Authentication Discovery

JWT header is `TTT_JWT_TOKEN` (not `Authorization: Bearer`), per `Headers.java`. Two auth mechanisms:
- **API_SECRET_TOKEN**: Grants `OFFICES_VIEW`, `REPORTS_VIEW` etc. Does NOT grant `AUTHENTICATED_USER`
- **TTT_JWT_TOKEN** (JWT): Grants `AUTHENTICATED_USER` authority

## Permission Inconsistency Bug

In `OfficePeriodController.java`:
| Endpoint | Permission | API Token? |
|---|---|---|
| GET report/approve period | `AUTHENTICATED_USER \|\| OFFICES_VIEW` | Yes |
| GET approve min/max | `AUTHENTICATED_USER \|\| OFFICES_VIEW` | Yes |
| GET report min/max | `AUTHENTICATED_USER` only | **No (403)** |
| PATCH report/approve | `AUTHENTICATED_USER` only | **No (403)** |

Report min/max lack `OFFICES_VIEW` fallback that approve min/max have — inconsistency.

## PATCH Tests — All Constraints Verified

| Constraint | Error Code | Verified |
|---|---|---|
| Approve past report period | `period.approve.start.max` | Yes |
| Report before approve | `period.report.before.approve` | Yes |
| Non-first-day-of-month | `period.not.first.day.of.month` | Yes |
| Approve >1 month backward | `period.approve.start.min` | Yes |
| Approve >1 month forward | `period.approve.change.more.than.one.month` | Yes |

Boundary tests: approve == report succeeds (`isBefore`/`isAfter` are strict).

## Business Logic Constraints (from source)

**Report period**: Must be 1st of month. Must not be before approve start. No upper bound. No jump-size limit.

**Approve period**: Must not be before today-2months. Must not be after report start. Max 1-month jump. Fails if extended report period exists in office.

## Bugs Found

1. **Permission inconsistency** (MEDIUM): GET report min/max missing `OFFICES_VIEW` fallback
2. **NPE on null start** (HIGH): PATCH with `{}` causes 500 NullPointerException at `start.getDayOfMonth()`. `@NotNull` in Swagger spec but not enforced at controller/DTO level
3. **Stack trace leakage** (MEDIUM): Invalid date format returns full Java stack trace in response body

## Environment State

Tested on Сатурн (office 2) as Perekrest. All 28 offices: REPORT=2026-03-01, APPROVE=2026-02-01. All changes reverted after testing.

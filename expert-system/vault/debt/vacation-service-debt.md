---
type: debt
tags:
  - technical-debt
  - bugs
  - security
  - vacation
  - code-quality
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[vacation-service-implementation]]'
  - '[[exploration/data-findings/vacation-schema-deep-dive]]'
branch: release/2.1
---
# Vacation Service Technical Debt

Code quality issues discovered during backend analysis of vacation service module.

## Bugs

1. **Object identity comparison** in `SickLeaveServiceImpl.getEditorType`: `if (employee == currentEmployee)` uses `==` instead of `.equals()`. Works by accident — always falls through to correct default.

2. **Wrong previous status in payExpiredApproved:** `VacationStatusChangedEvent` published with `previousStatus = PAID` instead of `APPROVED`.

3. **Crossing check uses wrong employee** in `VacationServiceImpl.updateVacation`: Uses `currentEmployeeId` instead of `entity.getEmployeeId()` — checks current user's vacations instead of vacation owner's.

4. **No guard for PAID+PRELIMINARY deletion:** `deleteVacation()` blocks PAID+EXACT but allows PAID+PRELIMINARY. Since all data is now EXACT, low risk but guard is incomplete.

## Design Issues

5. **CHECKSTYLE.OFF everywhere:** Suppressed: ParameterNumber, ClassFanOutComplexity, ClassDataAbstractionCoupling, CyclomaticComplexity. Many constructors take 10+ parameters.

6. **150+ lines of commented-out code** in `VacationAvailablePaidDaysCalculatorImpl` (dead `_OLD` methods).

7. **Binary search for max days** — O(N × log(maxDays)) calls per page load. Expensive.

8. **Inconsistent REPORTING_NORM:** Hardcoded `8` in `AvailableDaysRecalculationServiceImpl` vs. `@Value("${calendar.reporting-norm}")` in `EmployeeDayOffServiceImpl`.

## Security

9. **API token in application.yml:** `api-token: f20102cb-ff71-4aa6-b7f1-c2463134b84d` checked into repo.

10. **DB password in application.yml:** `password: 123456` — dev default committed to repo.

## Schema Debt
11. **`office_annual_leave.advance_vacation`** always NULL — dead column (flag lives on `office` table).
12. **Timeline has no FK constraints** on vacation/day_off columns.
13. **`employee_vacation` "unique" index** is not actually unique.
14. **Notification typo:** `TOMMOROW` in scheduled_vacation_notification.

Links: [[vacation-service-implementation]], [[exploration/data-findings/vacation-schema-deep-dive]], [[modules/vacation-service]]

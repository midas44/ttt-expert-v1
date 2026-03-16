---
type: investigation
tags:
  - vacation
  - validation
  - bug-fix
  - sprint-15
  - '#3369'
  - MR-5116
created: '2026-03-16'
updated: '2026-03-16'
status: active
related:
  - '[[vacation-form-validation-rules]]'
  - '[[vacation-service-deep-dive]]'
  - '[[investigations/vacation-sprint-15-technical-details]]'
branch: release/2.1
---
# Vacation Past-Date Validation — #3369 Fix Analysis

## Summary
Backend allowed creating/updating vacations with start dates in the past. Fixed in MR !5116 (merged 2026-01-14, branch `feature/3369-snavrockiy`). The MR was titled after a different issue (#3360), causing GitLab not to auto-link it to #3369.

## Root Cause
`VacationCreateValidator.isStartEndDatesCorrect()` had no past-date check — only checked date ordering (end >= start).

## Fix Implementation

**File:** `vacation/rest/src/main/java/com/noveogroup/ttt/vacation/rest/validation/VacationCreateValidator.java`

New validation constant:
```java
private static final String VACATION_START_DATE_IN_PAST = "validation.vacation.start.date.in.past";
```

Added check in `isStartEndDatesCorrect()` (lines 207-234):
```java
if (request.getStartDate().isBefore(today)) {
    context.buildConstraintViolationWithTemplate(VACATION_START_DATE_IN_PAST)
        .addPropertyNode(START_DATE_FIELD)
        .addConstraintViolation();
    result = false;
}
```

### Key Behavioral Details
- **Boundary**: `isBefore(today)` — today's date is **accepted**, only strictly past dates are rejected
- **Non-short-circuiting**: Both past-date and dates-order checks execute independently — both errors can be returned simultaneously
- **Error attached to `startDate` property node** only
- **Dates-order error** attached to both `startDate` and `endDate` nodes
- **Short-circuit after**: If `isStartEndDatesCorrect()` fails, subsequent validations (duration, next-year availability) are skipped via `&&`

### Update Path
`VacationUpdateValidator.isStartEndDatesCorrect()` **delegates directly** to the create validator's method:
```java
return validator.isStartEndDatesCorrect(request, context);
```
Same past-date check applies to both create and update operations.

## Missing Frontend Translation
The error key `validation.vacation.start.date.in.past` has **NO frontend translation string** in the current codebase. The existing translations only cover:
- `exception.validation.vacation.duration` → "You don't have enough available vacation days"
- `exception.validation.vacation.too.early` → "Vacation request can be created after 6 months..."

The `start.date.in.past`, `dates.order`, and `next.year.not.available` keys are returned as **raw key strings** to the frontend.

## BDD Test Scenarios (vacation.feature)

### Scenario 1 — Create with past start date (line 563)
- Current date: 2025-01-15
- Vacation: 2025-01-10 to 2025-01-20 (start 5 days in past)
- Expected: `validation.vacation.start.date.in.past`
- Runs for both AV=false and AV=true

### Scenario 2 — Create with past start + incorrect date order (line 584)
- Current date: 2025-01-15
- Vacation: 2025-01-10 to 2025-01-05 (past + end before start)
- Expected: BOTH `validation.vacation.start.date.in.past` AND `validation.vacation.dates.order`

### Scenario 3 — Update with past start date (line 607)
- Creates vacation 2026-03-01 to 2026-03-02, then advances clock to 2026-01-15
- Updates startDate to 2026-01-10
- Expected: `validation.vacation.start.date.in.past`
- Runs for both AV=false and AV=true

## Also Fixed in Same MR (!5116) — #3360

`EmployeeDaysServiceImpl.calculateDaysNotAfter()` replaced `calculateDaysBeforeAndAfter(employeesIds, year, year - 2)` (3-year window) with unbounded sum:
```sql
SELECT SUM(ev.available_vacation_days) FROM employee_vacation ev
WHERE ev.employee IN :ids AND ev.year <= :year
```
This fixes "Expected balance of days by year-end" showing incorrect values for employees with > 2 years of accruals.

## All Validation Constants in VacationCreateValidator

| Constant | Key | Purpose |
|----------|-----|---------|
| INCORRECT_VACATION_DURATION | validation.vacation.duration | Not enough days |
| VACATION_LIMIT_EXCEEDED | exception.validation.vacation.too.early | Before 6 months |
| INCORRECT_VACATION_DATES_ORDER | validation.vacation.dates.order | End < start |
| VACATION_START_DATE_IN_PAST | validation.vacation.start.date.in.past | Past start date |
| NEXT_YEAR_VACATION_NOT_AVAILABLE | validation.vacation.next.year.not.available | Next year before Feb 1 |

## Connections
- [[vacation-form-validation-rules]] — comprehensive validation rules reference
- [[vacation-service-deep-dive]] — vacation service architecture
- [[vacation-business-rules-reference]] — business rules
- [[investigations/vacation-sprint-15-technical-details]] — Sprint 15 context

---
type: investigation
tags:
  - maternity
  - vacation
  - lifecycle
  - events
  - edge-cases
  - production-bug
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[vacation-service]]'
  - '[[patterns/vacation-day-calculation]]'
  - '[[investigations/vacation-sprint-15-technical-details]]'
branch: release/2.1
---
# Maternity Leave Lifecycle — Complete Implementation

## Summary

Maternity leave is tracked via a boolean `maternity` flag on the employee entity, managed through CS synchronization events. The lifecycle is fully event-driven with two key events: `EmployeeMaternityBeginEvent` and `EmployeeMaternityEndEvent`. Vacation days are proportionally adjusted at both transitions.

## State Tracking

**ttt_vacation.employee**: `maternity` boolean (non-nullable)
**ttt_backend.employee**: `maternityStartDate`, `maternityEndDate` (LocalDate fields)

Detection in `CSEmployeeSynchronizer.java` (lines 294-300):
```java
private boolean isMaternityStarted(EmployeeEntity employee, CSEmployee csEmployee) {
    return employee != null && !employee.isMaternity() && csEmployee.isMaternity();
}
private boolean isMaternityEnded(EmployeeEntity employee, CSEmployee csEmployee) {
    return employee != null && employee.isMaternity() && !csEmployee.isMaternity();
}
```

## Maternity Begin — EmployeeMaternityBeginEventListener

File: `EmployeeMaternityBeginEventListener.java`
Triggers: `@Async`, `@TransactionalEventListener`

### Actions:

**1. Reject all NEW vacation requests** (lines 71-80):
```java
final List<VacationEntity> newRequests = vacationCRUDService.findNewRequests(employeeId);
for (final VacationEntity vacation : newRequests) {
    vacationUpdateService.rejectVacationBySystem(vacation.getId());
}
```
- Only `NEW` status vacations are rejected
- `APPROVED` vacations are kept (important edge case)
- Uses write lock per vacation entity

**2. Reduce current year days** (lines 82-90):
```java
BigDecimal subtractDays = BigDecimal.valueOf(
    (double) annualLeaveDays * (double) remainingDays / (double) totalYearDays
).setScale(0, RoundingMode.HALF_UP);
employeeDaysService.updateDays(employeeId, currentYear, currentDays.subtract(subtractDays));
```
- Formula: `subtract = annualDays × (daysFromTodayToYearEnd / totalDaysInYear)`
- HALF_UP rounding to integer

**3. Zero next year days** (lines 94-95):
```java
employeeDaysService.updateDays(employeeId, nextYear, BigDecimal.ZERO);
```

**4. Timeline event**: `MATERNITY_BEGIN`, negative `accrued_days`

## Maternity End — EmployeeMaternityEndEventListener

File: `EmployeeMaternityEndEventListener.java`
Triggers: `@Async`, `@TransactionalEventListener`

### Actions:

**1. Restore current year days** (lines 54-60):
```java
BigDecimal newDays = BigDecimal.valueOf(
    vacationDaysHelpService.calculate(employee.getOfficeId(), event.getTime().toLocalDate())
);
employeeDaysService.updateDays(employeeId, currentYear, currentDays.add(newDays));
```
- `calculate()` computes proportional accrual from maternity end date to year end

**2. Restore next year to full allocation** (lines 61-63):
```java
BigDecimal nextYearDays = BigDecimal.valueOf(
    officeAnnualLeaveService.getDays(employee.getOfficeId(), currentYear + 1)
);
employeeDaysService.updateDays(employeeId, currentYear + 1, nextYearDays);
```

**3. Timeline event**: `MATERNITY_END`, positive `accrued_days`

## Special Calculation During Maternity

**VacationAvailabilityChecker.java** (lines 54-114):
```java
if (employee.isMaternity()) {
    return hasEnoughDaysForMaternityEmployee(employee, vacation.getDays());
}
```
- During maternity: available days = SUM of `available_vacation_days` across ALL years
- Normal: per-year calculation with strategy pattern (advance vs accrued)
- Maternity employees CAN still request vacations if total available > 0

## Production Bug — V2.1.25 Migration

File: `V2_1_25_202512190841__fix_maternity_2025_zero_vacation_days_2026.sql`
3 employees had 2026 days = 24 instead of 0 after MATERNITY_BEGIN in late 2025.
Manually corrected: mgrishkevich, edobrovlyanskaya, afanaseva → 2026 days = 0.

**Root cause**: Race condition or timing issue between CS sync detecting maternity and the event handler zeroing next year days. The next-year zeroing happened before the annual accrual job, which then re-set 2026 to 24.

## Live Data Evidence (timemachine env)

**14 employees currently on maternity** (maternity=true)

**Timeline events** (selected):
| Employee | Event | Accrued Days | Date | Notes |
|----------|-------|-------------|------|-------|
| dshipacheva | BEGIN | -22 | 2023-01-27 | Nearly 3 years on maternity |
| dshipacheva | END | 0 | 2025-12-27 | Year-end: 0 days restored, 2026=24 |
| apliskina | BEGIN | -2 | 2024-11-30 | Late year, only 2 days lost |
| apliskina | END | +4 | 2025-10-28 | ~2 months remaining → 4 days |
| mzakharova | BEGIN | -10 | 2023-08-08 | |
| mzakharova | END | +22 | 2025-01-30 | ~11 months remaining → 22 days |
| ykozlovskaya | BEGIN | -8 | 2022-08-30 | |
| ykozlovskaya | END | +8 | 2025-09-01 | ~4 months remaining → 8 days |

**Employee vacation days during maternity** (current on-maternity employees):
| Employee | 2025 Days | 2026 Days |
|----------|-----------|-----------|
| afanaseva | 7 | 0 |
| edobrovlyanskaya | 16 | 0 |
| mgrishkevich | -1 | 0 |
| iromanenko | 13 | 0 |
| zmustafina | -1 | — |

Note: mgrishkevich and zmustafina have **negative** vacation days (-1), suggesting they used more vacation than was available before maternity began.

## Edge Cases for Testing

1. **APPROVED vacations not rejected** — only NEW are auto-rejected
2. **Year-end maternity end** — dshipacheva: 0 current-year days restored, full next year
3. **Negative vacation days** — mgrishkevich: -1 days, maternity can start with negative balance
4. **Multi-year maternity** — dshipacheva: 2023→2025, nearly 3 years
5. **Short maternity** — dprotopopova: maternity begin + end same day (2024-09-25)
6. **Annual accrual race condition** — V2.1.25 production bug: next year not zeroed
7. **Office change during maternity** — what happens to day calculation?
8. **Vacation request during maternity** — total across all years check

## References

- [[vacation-service]]
- [[patterns/vacation-day-calculation]]
- [[investigations/vacation-approval-workflow-e2e]]
- [[investigations/vacation-sprint-15-technical-details]]

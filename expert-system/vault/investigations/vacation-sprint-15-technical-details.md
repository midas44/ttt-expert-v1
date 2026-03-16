---
type: investigation
tags: [vacation, sprint-15, advance-vacation, maternity, next-year-blocking, accrual, deep-dive]
created: 2026-03-15
updated: 2026-03-15
status: active
related:
  - "[[modules/vacation-service-implementation]]"
  - "[[external/tickets/sprint-14-15-overview]]"
  - "[[exploration/data-findings/cross-service-office-sync-divergence]]"
branch: release/2.1
---

# Vacation Service — Sprint 15 Technical Details

## 1. Advance Vacation (AV) Logic

### Source of Truth
`advanceVacation` boolean on `OfficeEntity`, synced from CompanyStaff via `CSSalaryOfficeSynchronizer`:
```java
office.setAdvanceVacation(vacationData.get().getAdvanceVacation());
office.setNormDeviationType(convertCSNormDeviationType(vacationData.get().getOverworkUnderwork()));
```

### Routing in VacationRecalculationServiceImpl
```java
final OfficeBO office = officeService.getById(employee.getOfficeId());
if (!office.isAdvanceVacation()) {
    recalculateWithoutAdvance(employeeId, vacationId, context);
} else {
    recalculateWithAdvance(employeeId, vacationId, isNegativeBalanceAllowed, context);
}
```

### Key Differences: AV=false vs AV=true
| Aspect | AV=false (Regular) | AV=true (Advance) |
|--------|-------------------|-------------------|
| Calculation strategy | RegularCalculationStrategy | AdvanceCalculationStrategy |
| Negative balance | Shows 0 (clamped) | Allowed (negative days displayed) |
| Accrual | Proportional: months × (norm/12) | Full year available immediately |
| Norm deviation | Not applicable | Overtime adds days, undertime deducts |

### Test Coverage Status
TC-VAC-069–074 cover both AV modes. Gaps: #3347 AV=true next-year corner cases, #3361 multi-year balance bugs not explicitly tested.

## 2. Next-Year Vacation Blocking

### Implementation (`VacationCreateValidator.java`)
```java
public boolean isNextVacationAvailable(AbstractVacationRequestDTO request, ConstraintValidatorContext context) {
    final LocalDate now = TimeUtils.today();
    final LocalDate nextYearFrom = LocalDate.of(now.getYear(), 
        vacationProperties.getNextYearAvailableFromMonth(), FIRST_DAY);
    if (request.getStartDate().getYear() > now.getYear() && now.isBefore(nextYearFrom)) {
        context.buildConstraintViolationWithTemplate(NEXT_YEAR_VACATION_NOT_AVAILABLE)
            .addPropertyNode(START_DATE_FIELD)
            .addConstraintViolation();
        return false;
    }
    return true;
}
```

### Configuration
`nextYearAvailableFromMonth` property (default: 2 = February). Can't book next year until Feb 1st of current year.

### Error
`NEXT_YEAR_VACATION_NOT_AVAILABLE` on `startDate` field.

### Test Coverage Status
TC-VAC-011 and TC-VAC-012 cover this. Note: ticket #3322 mentions Dec-01 but code uses configurable month (default Feb 1).

## 3. Double Accrual Prevention (RegularCalculationStrategy)

### Formula
```java
double calculateAvailableDays(employee, year, paymentMonth, currentYearDays, pastYearDays, futureDays, editedVacationDays) {
    int normDays = officeAnnualLeaveRepository.findDays(employee.getOfficeId(), year);
    double accruedDays = paymentMonth * ((double) normDays / MONTH_COUNT);
    return accruedDays + currentYearDays + pastYearDays - normDays + futureDays + editedVacationDays;
}
```

### Why `-normDays`
At hire, system initializes full-year norm (e.g., 28 days) into `currentYearDays`. The proportional accrual (`accruedDays`) would double-count this. The `- normDays` term compensates.

### Salary Office Transfer Risk
If employee transfers between offices with different `normDays` (e.g., 24→28), the formula uses new office's norm for both `accruedDays` calculation AND compensation. This could produce incorrect results if the transfer happened mid-year and historical days weren't adjusted.

### Test Coverage Status
TC-VAC-069–070 test AV=false calculation. #2789 (double accrual for SO-transfer) is only indirectly covered via norm deviation logic — no explicit SO-transfer test case.

## 4. Maternity Leave Handling

### Event: `EmployeeMaternityBeginEvent`

### Actions (`EmployeeMaternityBeginEventListener.onMaternityBegin()`):
1. **Reject all NEW vacations**: `vacationRepository.findNewRequests(employeeId, today)` → set status REJECTED
2. **Reduce current year days proportionally**:
   ```java
   int newYearAvailableDays = (int)(fullYearAvailableDays * currentYearDaysToReduce / fullYearDays);
   BigDecimal reduction = BigDecimal.valueOf(newYearAvailableDays * restDays / fullYearDays)
       .setScale(0, RoundingMode.HALF_UP);
   employeeDaysService.updateDays(employeeId, year, employeeCurrentDays.subtract(reduction));
   ```
3. **Zero next-year days**: `employeeDaysService.updateDays(employeeId, year + 1, BigDecimal.ZERO)`

### Edge Cases
- Late-year maternity: almost no reduction (most days already earned)
- Already-approved vacations: NOT rejected (only NEW status)
- Maternity end event: not investigated — unclear if days are restored

### Test Coverage Status
TC-VAC-081 covers maternity as special case for day calculation. #3370 (maternity edit block) partially covered.

## 5. VacationStatusUpdateJob

### Schedule
- Status update: every 10 minutes (`fixedDelay = 600000`)
- Calendar update check: every 5 minutes (`fixedDelay = 300000`)

### Logic
```java
@Scheduled(fixedDelay = 600000)
public void updateVacations() {
    List<VacationEntity> vacations = vacationRepository.findApprovableBefore(today);
    for (VacationEntity vacation : vacations) {
        vacation.setStatus(VacationStatusType.PAID);
    }
    vacationRepository.saveAll(vacations);
}
```

Transitions APPROVED vacations to PAID when end date has passed. This is the "orphan window" — between vacation end and next job run (up to 10 minutes), vacation stays APPROVED.

### Test Coverage Status
TC-VAC-101 covers the orphan window. TC-VAC-086 covers calendar change recalculation.

## Identified Test Gaps

| Gap | Ticket | Priority |
|-----|--------|----------|
| AV=true next-year corner cases | #3347 | Medium |
| AV=true multi-year balance bugs | #3361 | Medium |
| SO-transfer double accrual explicit test | #2789 | High |
| Maternity end event (day restoration) | — | Low |
| Calendar update job + vacation interaction | #3380 | Medium |
| nextYearAvailableFromMonth configuration variants | #3322 | Low |

## Connections
- [[modules/vacation-service-implementation]] — main service architecture
- [[external/tickets/sprint-14-15-overview]] — ticket context
- [[exploration/data-findings/cross-service-office-sync-divergence]] — office sync bug affecting vacation calculations

---
type: module
tags:
  - accounting
  - payment
  - period-management
  - vacation-days
  - deep-dive
  - sprint-15
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[vacation-service-deep-dive]]'
  - '[[ttt-report-service-deep-dive]]'
  - '[[dayoff-service-deep-dive]]'
branch: release/2.1
---
# Accounting Service Deep Dive

Deep code-level investigation of accounting operations across TTT services: vacation payment, period management, vacation day corrections, norm-based recalculation, and scheduled tasks.

## 1. Dual Period System

TTT uses two period types per salary office (per `PeriodType` enum):

- **REPORT period**: When employees can submit/edit time reports. Controlled by accountants.
- **APPROVE period**: When managers can approve reports. Always <= report period start.

```
APPROVE_PERIOD_START <= REPORT_PERIOD_START
```

Default when no period configured: previous month 1st day (design issue — could cause problems for newly created offices).

### Period Controller Endpoints (OfficePeriodController — `/v1/offices`)

| Endpoint | Method | Authority | Purpose |
|----------|--------|-----------|---------|
| `/{officeId}/periods/report` | GET | AUTHENTICATED_USER or OFFICES_VIEW | Get report period |
| `/{officeId}/periods/report` | PATCH | AUTHENTICATED_USER | Change report period |
| `/{officeId}/periods/approve` | GET | AUTHENTICATED_USER or OFFICES_VIEW | Get approve period |
| `/{officeId}/periods/approve` | PATCH | AUTHENTICATED_USER | Change approve period |
| `/periods/report/min` | GET | AUTHENTICATED_USER | Earliest report across offices |
| `/periods/report/max` | GET | AUTHENTICATED_USER | Latest report across offices |
| `/periods/approve/min` | GET | AUTHENTICATED_USER or OFFICES_VIEW | Earliest approve across offices |
| `/periods/approve/max` | GET | AUTHENTICATED_USER or OFFICES_VIEW | Latest approve across offices |

**Design issue**: Controller uses AUTHENTICATED_USER for PATCH — overly permissive. Real access control via `OfficePeriodValidator.validateWriteAccess()` checks office EDIT permission.

### Report Period Validation (`OfficePeriodServiceImpl.patchReportPeriod`)

```java
// Must be 1st of month
if (start.getDayOfMonth() != 1) {
    throw new ValidationException(CODE_NOT_FIRST_DAY_OF_MONTH);
}
// Must be >= approve period
if (start.isBefore(approvePeriod.getStart())) {
    throw new ValidationException(CODE_ERROR_REPORT_BEFORE_APPROVE);
}
```

Error codes:
- `exception.validation.period.not.first.day.of.month`
- `exception.validation.period.report.before.approve`

### Approve Period Validation (`OfficePeriodServiceImpl.patchApprovePeriod`)

```java
// Min: 2 months before today
final LocalDate previousMonthFirstDay = TimeUtils.today().minusMonths(2).withDayOfMonth(1);
if (start.isBefore(previousMonthFirstDay)) → CODE_ERROR_APPROVE_START_MIN

// Max: must not exceed report period
if (start.isAfter(reportPeriod.getStart())) → CODE_ERROR_APPROVE_START_MAX

// Change limit: max 1 month backward or forward from current
if (start.isBefore(currentPeriodStart.minusMonths(1))) → CODE_ERROR_APPROVE_CHANGE_MORE_THAN_ONE_MONTH
if (start.isAfter(currentPeriodStart.plusMonths(1))) → CODE_ERROR_APPROVE_CHANGE_MORE_THAN_ONE_MONTH

// Block if any employee has extended period
if (internalEmployeeExtendedPeriodService.hasAny(officeId)) → approve.notAllowed.extendedPeriod
```

Error codes:
- `exception.validation.period.approve.start.min`
- `exception.validation.period.approve.start.max`
- `exception.validation.period.approve.change.more.than.one.month`
- `approve.notAllowed.extendedPeriod` (via MessageUtil)

**Design issue**: Approve period blocked if ANY employee has extended period — entire office blocked by single extension.

### Period Change Events and RabbitMQ

`InternalOfficePeriodService.setPeriodStart()` distinguishes:
- **Period changed** (forward or new): publishes `OfficePeriodChangedApplicationEvent`
- **Period reopened** (approve period moved backward): publishes `OfficePeriodReopenedApplicationEvent`

Feature toggle `TTT_VACATION_ASYNC`:
- **Disabled**: synchronous call `vacationClient.recalculateAvailableDays(officeId, start)` when approve period changes
- **Enabled**: publishes Spring events → RabbitMQ listeners

RabbitMQ listeners (both @Async):
- `PeriodChangedApplicationEventListener` → exchange `TTT_BACKEND_OFFICE_PERIOD_TOPIC`
- `PeriodReopenedApplicationEventListener` → exchange `TTT_BACKEND_OFFICE_PERIOD_REOPENED_TOPIC`

Period caching via `OfficePeriodCacheConfiguration.CACHE_OFFICE_PERIOD` with explicit eviction on change.

## 2. Vacation Payment Flow

### PayVacationServiceImpl.payVacation()

Payment is the final lifecycle step: APPROVED → PAID.

```java
public VacationBO payVacation(Long vacationId, Integer regularDays, Integer administrativeDays) {
    // 1. Acquire write lock
    VacationEntity entity = vacationRepository.findByIdAndAcquireWriteLock(vacationId);
    
    // 2. Validate (5 checks — all throw same error code!)
    checkForPayment(entity, VacationStatusType.PAID, regularDays + administrativeDays);
    
    // 3. Create payment record
    VacationPaymentEntity payment = createVacationPayment(regularDays, administrativeDays);
    
    // 4. Update status
    entity.setStatus(VacationStatusType.PAID);
    entity.setVacationPaymentId(payment.getId());
    
    // 5. Update vacation days (redistribute if paid less)
    updateVacationDays(entity, payment);
    
    // 6. Save + recalculate + publish event
    vacationRepository.save(entity);
    vacationRecalculationService.recalculate(entity.getEmployeeId(), null, false);
    eventPublisher.publishEvent(new VacationStatusChangedEvent(vacationBO, previousStatus));
}
```

### Payment Validation (checkForPayment)

5 sequential checks, ALL throwing `exception.vacation.status.notAllowed` or `exception.vacation.pay.days.not.equal`:

```java
1. entity.getDays() != totalDays → exception.vacation.pay.days.not.equal
2. entity.getStatus() != APPROVED → exception.vacation.status.notAllowed
3. entity.getPeriodType() != EXACT → exception.vacation.period.type.notAllowed
4. nextStatus != PAID → exception.vacation.status.notAllowed
5. !hasAnyRole(ACCOUNTANT, CHIEF_ACCOUNTANT) → exception.vacation.status.notAllowed
6. !statusManager.isNextStateAvailable() → exception.vacation.status.notAllowed
```

**Design issue**: Same error code `exception.vacation.status.notAllowed` for 4 different failures — impossible to distinguish cause from error response.

**Design issue**: Check #4 (`nextStatus != PAID`) is always true since `nextStatus` is hardcoded to PAID at line 108 — dead code.

### Day Redistribution on Payment (`returnDaysToEmployeeIfPaidLess`)

If vacation is REGULAR and fewer days are paid than requested:

```java
BigDecimal daysToReturn = vacation.getDays() - payment.getRegularDaysPayed();
// If daysToReturn > 0: redistribute back
// Uses VacationDaysCalculator for year-based distribution
// Adjusts nextYear first, then thisYear if nextYear insufficient
VacationDaysBO newDays = new VacationDaysBO(thisYearReminder, max(0, nextYearReminder));
vacationDaysUpdater.update(from, to, vacation);
```

ADMINISTRATIVE vacations skip redistribution entirely — just return current days.

### Auto-Payment of Expired Approved Vacations

`payExpiredApproved()` — called by cron job:

```java
LocalDate twoMonthsBeforeSecondDay = today.minusMonths(2).withDayOfMonth(2);
List<VacationEntity> requestsToPay = vacationRepository.findOverduePayments(
    Collections.singleton(0L), false, twoMonthsBeforeSecondDay);
```

**Design issue**: `Collections.singleton(0L)` — magic value, purpose unclear (likely "no office filter").
**Design issue**: Hardcoded 2-month threshold, not configurable.

Auto-payment assigns all days to REGULAR or ADMINISTRATIVE based on `paymentType`, sets status to PAID.

## 3. Vacation Days Correction (Manual Adjustment)

### EmployeeDaysServiceImpl.manualAdjustment()

Accountant-initiated correction of employee's vacation day balance.

```java
public EmployeeVacationDaysBO manualAdjustment(Long employeeId, BigDecimal daysChangedByAccounting, String comment) {
    // 1. Permission check: current user must be accountant + have EDIT on employee's office
    if (!statusManager.isAccountant(getCurrent()) || !accountantOffices.contains(employee.getOfficeId())) {
        throw new VacationSecurityException();
    }
    
    // 2. Branch on positive/negative
    if (daysChangedByAccounting >= 0) {
        manualAdjustForPositiveDaysChanged(...);
    } else {
        // AV=false offices cannot go negative
        if (!isAdvanceVacationAllowed) throw new InvalidVacationDaysCorrectionException();
        manualAdjustForNegativeDaysChanged(...);
    }
    
    // 3. Always creates DAYS_ADJUSTMENT timeline event
    createDayAdjustmentEvent(employeeId, dayDelta, comment);
}
```

Error: `exception.invalid.vacation.days.correction` — when AV=false and negative correction attempted.

### Positive Adjustment Logic

If `daysChangedByAccounting > availableDays`:
- Single year update: `daysChangedByAccounting - pastPeriodsAvailableDays`

If `daysChangedByAccounting <= availableDays`:
- Iterates year-by-year (oldest first), subtracting surplus from each year's balance

**Design issue**: Uses `double` arithmetic (`daysToSubract`, `day.getDays().doubleValue()`) for financial calculations — floating point precision risk.

### Negative Adjustment Logic

1. Zeroes out all previous years' days
2. Sets current year to `daysChangedByAccounting`
3. Creates timeline event with delta

### VacationDaysController Endpoints (`/v1/vacationdays`)

| Endpoint | Method | Authority | Purpose |
|----------|--------|-----------|---------|
| `/` | GET | VACATION_DAYS_VIEW | All employees' vacation days |
| `/{login}` | GET | VACATION_DAYS_VIEW | Single employee's days |
| `/{login}` | PUT | VACATION_DAYS_EDIT | Manual adjustment (correction) |
| `/recalculate` | POST | VACATION_DAYS_EDIT | Recalculate for office |
| `/{login}/years` | GET | VACATION_DAYS_EDIT | Days grouped by year |
| `/available` | GET | VACATION_DAYS_VIEW | Calculate available paid days |

## 4. Vacation Days Distribution Algorithm

### VacationDaysDistributor

3 strategies based on AV (advance vacation) setting and direction:

**Non-AV office (AV=false)**:
- Increase: add days to newest year first (reverse chronological), consume vacation days first
- Decrease: subtract from oldest year first (chronological), shift to vacation days

**AV office (AV=true)**:
- Same as non-AV for increase and non-negative decrease
- Negative balance allowed: current year can go negative, but not next year (`paymentDate.getYear()` boundary)

All strategies validate remainder == 0 → `IllegalStateException("Calculation error")` if not.

**Design issue**: TODO comment in code: "possibly it is not correct" — acknowledged code smell in negative balance path.

## 5. Norm-Based Recalculation

### AvailableDaysRecalculationServiceImpl

Automatically adjusts vacation days based on actual vs. expected working hours.

**Triggers**: Period change, manual recalculate endpoint

**Conditions** (all must be true):
1. Office `NormDeviationType != NONE`
2. Office `isAdvanceVacation() == true`
3. Employee started before recalculation month

**Calculation**:
```java
double difference = reported - personalNorm;
// Skip if difference == 0
// Skip if difference > 0 AND type == UNDERTIME (only penalize underwork)
BigDecimal daysDelta = normalizeEffort(difference); // difference / 8 (REPORTING_NORM), scale 3, HALF_UP
```

**Design issue**: `difference == 0` uses `double` comparison — floating point equality check is unreliable.

**Subtraction** (negative delta):
- Iterates year-by-year from oldest
- Current year can go negative (others cannot)
- Saves `ConfirmationPeriodDays` records for reverse capability

**Addition** (positive delta):
- Adds to the recalculation year directly
- Also saves reverse records

### Recalculation Reverse (`recalculationReverse`)

Used when approve period is reopened (moved backward):
1. Restores days from saved `ConfirmationPeriodDays`
2. Deletes the saved records
3. Publishes `MonthlyRecalculationReverseEvent` if delta != 0

**Design issue**: `subtractAvailableVacationDaysAndSaveDaysForReverse` potentially saves to `confirmationPeriodDaysRepository` twice in some branches — risk of double accounting.

## 6. Employee Extended Report Period

### EmployeeExtendedPeriodServiceImpl

Allows individual employees to report in the approve period (between approve and report period starts).

```java
getEmployeeReportPeriod(employeeId):
    // If approve != report AND employee has extension:
    //   return approve period start (more permissive)
    // Otherwise: return report period start
```

**Operations**:
- `putEmployee(login)`: Grant extension + send notification
- `removeEmployee(login)`: Revoke extension + send notification
- `cleanUp()`: Remove expired extensions (deadline-based)

**Permission**: Office EDIT required (via `OfficePeriodValidator.validateWriteAccess`)

### ExtendedPeriodScheduler (Cron Job)

Scheduled via `${ttt.period.report.extended.clean-up.cron}`, ShedLock-protected. Calls `cleanUp()` to remove expired extensions and notify affected employees.

## 7. Annual Accruals (Cron Job)

### AnnualAccrualsTask

Scheduled via `${annual-accruals.cron}`, ShedLock-protected. Publishes `EmployeeNewYearEvent` for each active employee. The event handlers (not in this scope) create new year's vacation day accrual entries.

## 8. Task Report Accounting

### TaskReportAccountingServiceImpl

Accounting view of task reports — showing approved/unapproved hours per employee.

**Permission model** (AccountingPermissionProvider):
- VIEW: ADMIN, VIEW_ALL, ACCOUNTANT, CHIEF_ACCOUNTANT
- NOTIFY: ADMIN, CHIEF_ACCOUNTANT, ACCOUNTANT (no VIEW_ALL — design issue)

**Office scoping**:
- ADMIN/VIEW_ALL/CHIEF_ACCOUNTANT: see all offices (or filter to one)
- ACCOUNTANT: restricted to assigned offices only → `TttSecurityException` if requesting non-assigned office

**Features**:
- Keyboard layout auto-correction via `SuggestionMappingUtil.correctLayout` (RU↔EN)
- Employee search with SQL LIKE wrapping
- Filter by: office, department type, being dismissed, date range
- `notifyManagers()`: sends notification to managers with unapproved reports

## 9. DaysLimitationService (Probation Period)

Enforces vacation restrictions for new employees within first 3 months:

```java
List<Limit> limits = List.of(new Limit(3, BigDecimal.valueOf(0)));
// 3 months from first working day, limit = 0 vacation days
```

**Design issue**: Hardcoded 3-month/0-day limit — not configurable per office or employee type.

Calculates regular vacation days within the limit period using `FirstWorkingDayCalculator.calculateVeryFirstDay()`.

## 10. Design Issues Summary

| # | Issue | Location | Severity | Test Impact |
|---|-------|----------|----------|-------------|
| 1 | Same error code for 5 payment failures | PayVacationServiceImpl.checkForPayment | Medium | Cannot verify specific failure reason |
| 2 | Dead code: nextStatus != PAID always true | PayVacationServiceImpl.checkForPayment | Low | N/A |
| 3 | Hardcoded 2-month auto-pay threshold | PayVacationServiceImpl.payExpiredApproved | Low | Test boundary at exactly 2 months |
| 4 | Magic singleton(0L) parameter | PayVacationServiceImpl.payExpiredApproved | Low | Unclear filter behavior |
| 5 | double arithmetic for day calculations | EmployeeDaysServiceImpl.manualAdjustForPositiveDaysChanged | Medium | Floating point edge cases |
| 6 | double comparison (== 0) for differences | AvailableDaysRecalculationServiceImpl.recalculateDays | Medium | May skip recalculation for tiny differences |
| 7 | Double save to confirmationPeriodDaysRepository | AvailableDaysRecalculationServiceImpl.subtractAvailableVacationDaysAndSaveDaysForReverse | High | May cause double counting on reverse |
| 8 | TODO "possibly incorrect" comment | VacationDaysDistributor | Medium | Negative balance distribution may be wrong |
| 9 | Approve change blocked by any extension | OfficePeriodServiceImpl.patchApprovePeriod | Medium | Single employee blocks entire office |
| 10 | VIEW_ALL cannot NOTIFY | AccountingPermissionProvider | Low | Permission gap |
| 11 | Hardcoded 3-month probation limit | DaysLimitationService | Low | Not configurable |
| 12 | Default period = prev month 1st | InternalOfficePeriodService.findPeriodStart | Low | New office edge case |
| 13 | Controller-level AUTHENTICATED_USER for writes | OfficePeriodController | Low | Service-level guards provide real security |

## Related Notes

- [[vacation-service-deep-dive]] — vacation CRUD, status transitions, permissions
- [[ttt-report-service-deep-dive]] — task report CRUD, confirmation flow
- [[dayoff-service-deep-dive]] — day-off lifecycle, calendar conflict
- [[sick-leave-service-deep-dive]] — sick leave dual status model
- [[vacation-day-calculation]] — calculation details
- [[office-period-model]] — period architecture overview
- [[EXT-cron-jobs]] — scheduled task inventory

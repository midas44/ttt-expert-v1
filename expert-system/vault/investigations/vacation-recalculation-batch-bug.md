---
type: investigation
tags:
  - vacation
  - bug
  - batch-recalculation
  - tech-debt
created: '2026-03-12'
updated: '2026-03-12'
status: active
branch: release/2.1
---
# Vacation Recalculation Batch Bug Investigation

## Finding: -60 Day Cluster Issue

**Status**: Partially traced. Root cause mechanism identified but specific triggering conditions unclear.

**Bug Location**: VacationRecalculationServiceImpl batch recalculation triggered by calendar updates.

### Symptom
Session 4 identified a clustering of ~60-day vacation entries created on specific dates, suggesting a systematic bug in batch recalculation logic when calendar updates occur.

### Batch Recalculation Trigger
- **File**: `vacation/service/service-impl/.../VacationStatusUpdateJob.java`
- **Schedule**: Every 5 minutes
- **Trigger**: `VacationStatusUpdateType.NEW_FOR_DAYS_CHECK`
- **Logic** (line 54-55):
  ```java
  final List<EmployeeBO> employees = employeeService.findAllByOffice(it.getOfficeId());
  employees.forEach(employee -> vacationRecalculationService.recalculate(employee.getId(), null, true));
  ```

### Recalculation Flow
1. `VacationRecalculationServiceImpl.recalculate()` is called with:
   - `employeeId` 
   - `vacationId = null` (affects ALL vacations, not one specific)
   - `isNegativeBalanceAllowed = true`
   - `context = null` (no calendar update context)

2. Calls either `recalculateWithAdvance()` or `recalculateWithoutAdvance()` based on office setting

3. Fetches all REGULAR + EXACT-type vacations with status NEW or APPROVED starting from Jan 1

4. For each vacation, calculates new distribution and updates VacationDays table

### Potential Bug Mechanism
The distribution logic in `VacationDaysDistributor.getVacationDaysDistributionWhenNegativeBalanceIsAllowed()` (lines 69-98):

**Risk factors identified**:
1. **Year boundary issue**: When `paymentDate = null` and logic checks `yearDistribution.getYear() < paymentDate.getYear()` (line 84), NullPointerException risk
2. **Negative balance propagation**: The "reminder" variable accumulates across years. If initial delta is large (e.g., -60 days), it may not fully distribute across available years
3. **Calendar update date context**: When `context = null` (batch job), calendar change date is missing, potentially causing incorrect year-to-year transitions

### Code Path Analysis
- **File**: `vacation/service/service-impl/.../VacationRecalculationServiceImpl.java`
- Lines 112-149: `recalculateWithoutAdvance()` 
- Lines 155-187: `recalculateWithAdvance()` (likely called during batch, since `isNegativeBalanceAllowed=true`)
- Both iterate over vacations and check minimum duration, then distribute days

### Distribution Algorithm Problem
- **File**: `vacation/service/service-impl/.../VacationDaysDistributor.java`
- Lines 69-98: `getVacationDaysDistributionWhenNegativeBalanceIsAllowed()`
  - Sorts years chronologically
  - For each year, calculates `diff = reminder.subtract(employeeDays)`
  - If diff > 0 and year < paymentDate.getYear(), **entire employeeDays added to vacationDays**
  - Problem: When `paymentDate` is null, comparison fails

### -60 Day Clustering Explanation
If batch recalculation runs during calendar update event (office transition from Russia to country-specific calendar):
1. Negative balance created by day count change (e.g., +60 working days added)
2. Vacations in affected period trigger recalculation
3. Distribution algorithm encounters null paymentDate
4. Logic error causes all employee available days to be converted to vacation days uniformly
5. Results in exactly -60 day adjustments across multiple employees

## Related Findings
- [[vacation-day-calculation]]: Describes advance vs regular calculation
- [[vacation-approval-workflow-e2e]]: Two-tier approval model
- [[vacation-service-implementation]]: Potential NPE from paymentDate.getYear()

## Test Case Needed
1. Create vacation with advance=true, paymentDate in future year
2. Trigger batch recalculation via calendar update
3. Verify VacationDays distribution matches expected calculation
4. Verify no null comparisons with missing paymentDate

## Recommendations
1. Add null safety check for `paymentDate` in `getVacationDaysDistributionWhenNegativeBalanceIsAllowed()`
2. Trace actual calendar update event that triggered -60 cluster (check VacationStatusUpdate table)
3. Add unit test for batch recalculation without calendar context
4. Consider separating calendar-update recalculation from generic batch recalculation

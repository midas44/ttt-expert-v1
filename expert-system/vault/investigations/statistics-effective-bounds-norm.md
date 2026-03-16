---
type: investigation
tags:
  - statistics
  - effective-bounds
  - individual-norm
  - budget-norm
  - sprint-15
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[statistics-service-deep-dive]]'
  - '[[cross-service-office-sync-divergence]]'
  - '[[vacation-sprint-15-technical-details]]'
branch: release/2.1
---
# Statistics — Effective Bounds on Individual Norm

## Summary
Sprint 15 tickets #3353, #3356, and #3381 implemented "effective bounds" that clamp individual norm calculation to an employee's actual work period (first working day → last working day). This affects the Statistics employee reports, the My Tasks counter, and the statistic_report table sync. Budget norm (#3381) adds back administrative vacation hours so it represents "expected work excluding non-admin leave."

## Core Method: `effectiveBounds()`

**File:** `ttt/service/service-impl/.../task/report/TaskReportSummaryServiceImpl.java` (lines 96-106)

```java
private Pair<LocalDate, LocalDate> effectiveBounds(final long employeeId,
                                                    final LocalDate rangeStart,
                                                    final LocalDate rangeEnd) {
    return employeeWorkPeriodRepository.findPeriodForRange(employeeId, rangeStart, rangeEnd)
        .map(period -> Pair.of(
            TimeUtils.max(rangeStart, period.getPeriodStart()),
            period.getPeriodEnd() == null
                ? rangeEnd
                : TimeUtils.min(rangeEnd, period.getPeriodEnd())))
        .orElse(Pair.of(rangeStart, rangeEnd));
}
```

**Boundary logic:**
- `TimeUtils.max(a, b)` returns the later date; `TimeUtils.min(a, b)` returns the earlier
- If `periodEnd == null` (employee still active), range end is unchanged
- If no work period found at all → original range returned as-is (fallback for un-synced employees)

## Work Period Data Source

**Table:** `ttt_backend.employee_work_period` (migration V1_59)
**Fields:** `id`, `employee` (FK), `period_start` (NOT NULL), `period_end` (nullable)

**Populated by:** `CSEmployeeSynchronizer.updateWorkPeriods()` — full replacement sync from CompanyStaff:
- Deletes ALL existing periods for the employee
- Inserts fresh periods from CS `csPeriods.getWork()` list
- Skips periods where `firstDate` is null

## Period Lookup: `findPeriodForRange`

Two-step lookup (only one period ever returned):
1. `findPeriodContainingDate(employeeId, rangeStart)` — `period_start <= rangeStart AND (period_end IS NULL OR period_end >= rangeStart)`, ordered `period_start DESC`
2. Fallback: `findPeriodOverlapping(employeeId, rangeStart, rangeEnd)` — `period_start <= rangeEnd AND (period_end IS NULL OR period_end >= rangeStart)`, ordered `period_start DESC`

**Re-hired employees:** Only ONE period returned per query. `DESC` ordering picks the most recent matching period. Periods are never merged.

## Three Sync Paths (All Apply effectiveBounds)

| Entry Point | Trigger | Method Chain |
|---|---|---|
| Vacation event (RabbitMQ) | `EmployeeMonthNormContextCalculated` | `StatisticReportSyncServiceImpl.saveMonthNormAndReportedEffortForEmployees()` → `calculatePersonalNorm()` / `calculateBudgetNorm()` |
| Task report change | `TaskReportAddEvent` | `StatisticReportSyncServiceImpl.updateMonthlyReportedEffortForEmployee()` → creates report with norms if not exists |
| Periodic cron | `StatisticReportScheduler` (04:00 daily, Asia/Novosibirsk, ShedLock) | `StatisticReportSyncLauncherImpl.sync()` → syncs previous month + current month |

## Personal Norm vs Budget Norm

In `InternalReportingNormService`:
- **personalNorm** = `totalNorm - offHours(ALL vacations + sick leaves + maternity)` — what the employee "owes"
- **budgetNorm** = `totalNorm - offHours(non-administrative vacations + sick leaves + maternity)` — excludes admin vacation from deduction

`filterNonAdministrativeVacations()` filters out `VacationPaymentTypeModel.ADMINISTRATIVE` for budget norm.

**Excess calculation:** `(reported - budgetNorm) / budgetNorm * 100` — uses budgetNorm as denominator. If budgetNorm == 0 → excess is `null`, status = `NA`.

## Zero-Norm Short-Circuit

When `effectiveStart.isAfter(effectiveEnd)` (employee not working during the period), returns `0L` or `Pair.of(0L, 0L)` immediately without calling calendar service.

## normForDate Edge Cases

`periodSummary()` method (lines 296-359) handles:
1. **Employee hired after report date** (e.g., date=11th, first day=15th): `startForDate=15 > endForDate=11` → normForDate=0
2. **Employee dismissed before report date** (e.g., last day=10th, date=15th): `endForDate = min(15, 10) = 10`, norm covers only up to dismissal

## UI Display Rules

### Statistics Employee Reports Table (`/statistics/employee-reports`)
- Norm column shows **budgetNorm** (not personalNorm)
- When admin vacation exists: `{personalNorm} ({budgetNorm})` — two numbers
- When no admin vacation: single number (budgetNorm = personalNorm)
- Excess percentage uses budgetNorm as denominator

### My Tasks Counter (`/report` — "Worked in [Month]")
- **4-number format** when personalNorm ≠ generalNorm: `worked / normForDate / personalNorm / generalNorm`
- **3-number format** when personalNorm = generalNorm: `worked / normForDate / generalNorm`
- personalNorm shown only when it differs from generalNorm
- normForDate hidden for closed/past periods

## Database Schema

**Table:** `public.statistic_report`

| Column | Type | Notes |
|--------|------|-------|
| id | bigint | PK |
| employee_login | text | Employee identifier |
| report_date | date | First day of month (e.g., 2026-02-01) |
| month_norm | bigint | Personal norm in HOURS (effective bounds applied) |
| budget_norm | bigint | Budget norm in HOURS |
| reported_effort | numeric | Reported hours (decimal) |
| comment | text | UI cell comment |
| created_time | timestamptz | |
| last_updated_time | timestamptz | |
| updated_by | text | |

**Units:** Norms stored as HOURS (Long). Reported effort as decimal HOURS. Task reports internally use MINUTES, converted via `EffortUtils.minutesToUnit()`.

## API Response: `StatisticReportNodeDTO`

| Field | Type | Description |
|---|---|---|
| norm | Long | Personal month norm (hours) |
| budgetNorm | Long | Budget norm (hours) |
| normForDate | Long | Norm up to selected date (hours) |
| reported | BigDecimal | Reported hours |
| excess | Double | `(reported - budgetNorm) / budgetNorm * 100` |
| reportedStatus | ExcessStatus | LOW/NEUTRAL/HIGH/NA |

## Integration Test Coverage

**File:** `StatisticReportEffectiveBoundsIntegrationTest.java` — 5 tests covering:
1. Work periods REST endpoint
2. Full month employee → 160h via vacation event
3. Hired mid-month (Feb 15) → 80h via task report update
4. Dismissed mid-month (Feb 10) → 56h via periodic cron
5. API returns correct pre-stored norms
6. All three sync sources produce consistent norms

## Test Gaps Identified

1. **Re-hired employees** (multiple work periods) — only one period picked, behavior untested
2. **Gap between periods** — month in gap between two work periods
3. **Exact month boundary** — periodStart == monthStart or periodEnd == monthEnd
4. **Budget norm + effective bounds** — admin vacation during partial month
5. **normForDate edge cases** — hired after requested date → 0
6. **Maternity + effective bounds** interaction
7. **Time-offs overlapping period boundaries** — vacation spanning hire date
8. **No work period at all** — fallback to unclamped range
9. **Zero-norm excess display** — budgetNorm=0 → excess=null, status=NA
10. **Concurrent sync from multiple sources** — race conditions

## Related Tickets
- **#3353** — Exclude periods before first/after last working day from individual norm (Sprint 15)
- **#3356** — Use updated individual norm for partial-month employees in statistics (Sprint 15)
- **#3381** — Budget norm = individual norm + admin vacation hours (Hotfix Sprint 14)
- **#3400** — CSV export of individual calendar norm (Sprint 15, operational task)

## Related Notes
- [[statistics-service-deep-dive]]
- [[cross-service-office-sync-divergence]]
- [[vacation-sprint-15-technical-details]]

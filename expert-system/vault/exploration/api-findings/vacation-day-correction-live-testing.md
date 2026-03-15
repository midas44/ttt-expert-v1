---
type: exploration
tags:
  - vacation
  - correction
  - live-testing
  - timemachine
  - accounting
  - bug
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[modules/accounting-backend]]'
  - '[[exploration/ui-flows/accounting-pages]]'
  - '[[external/requirements/REQ-vacation-day-corrections]]'
  - '[[patterns/vacation-day-calculation]]'
---

# Vacation Day Correction — Live Testing

Tested on timemachine with two employees: `abpopov` (AV=true, Neptun) and `abaymaganov` (AV=false, Venera).

## Baseline Data

| Employee | availableDays | pastPeriods | nextYear | normForYear | AV |
|----------|--------------|-------------|----------|-------------|-----|
| abpopov | 26.625 | 5.625 | 21 | 21 | true |
| abaymaganov | 88 | 64 | 24 | 24 | false |

## Test Results

### AV=true (abpopov) — All corrections accepted
- **+1 day**: PUT 27.625 → accepted, DB shows DAYS_ADJUSTMENT event with `days_accrued=1.000`
- **Negative (-2)**: PUT -2 → **accepted** (correct for AV=true)
- **Restore**: PUT 26.625 → accepted

### AV=false (abaymaganov) — Negative blocked
- **Negative (-5)**: PUT → **400 InvalidVacationDaysCorrectionException** (correct enforcement)
- **+1 day**: PUT 89 → accepted
- **Restore**: PUT 88 → accepted

### Bulk Recalculate
`POST /v1/vacationdays/recalculate?officeId=11&date=2026-03-13` → 200 OK. Created 1 DAYS_ADJUSTMENT event for `amatiushin` (+1.313 days for Feb 2026).

## BUG: pastPeriodsAvailableDays Drift (MEDIUM severity)

After net-zero correction cycles (+1, -1), `pastPeriodsAvailableDays` drifts downward:
- **abpopov**: 5.625 → 0 after four corrections netting to zero
- **abaymaganov**: 64 → 63 after two corrections netting to zero

**Root cause**: Corrections are applied asymmetrically — increases don't add to sub-components, but decreases subtract from `pastPeriodsAvailableDays` first (oldest-first consumption). This one-directional logic causes irreversible drift.

**Bulk recalculate does NOT fix this** — pastPeriodsAvailableDays remained at 0 after recalculation.

**Impact**: Incorrect breakdown of past-period vs current-year balances. If different payment rules apply to past-period days, financial calculations may be affected. Total `availableDays` remains correct.

## Other Findings

1. **`/available` requires undocumented `newDays` param**: `GET /v1/vacationdays/available` requires `employeeLogin`, `startDate`, `endDate`, `paymentDate`, `newDays` (int). Not just a balance check — calculates availability for a hypothetical vacation.

2. **Audit trail**: All DAYS_ADJUSTMENT events correctly logged with delta (`days_accrued`), comment, and timestamp. Deltas are stored, not absolute values.

3. **Sub-component calculation is one-directional**: Increase goes to total only (sub-components unchanged), decrease subtracts from pastPeriods first, then nextYear.

## Connections
- [[modules/accounting-backend]] — correction endpoints
- [[external/requirements/REQ-vacation-day-corrections]] — requirements
- [[patterns/vacation-day-calculation]] — calculation formulas
- [[exploration/ui-flows/accounting-pages]] — UI exploration

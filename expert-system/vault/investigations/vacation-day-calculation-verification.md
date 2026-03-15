---
type: investigation
tags:
  - vacation
  - calculation
  - verification
  - FIFO
  - norm-deviation
  - API
  - database
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[patterns/vacation-day-calculation]]'
  - '[[investigations/bug-verification-s5]]'
  - '[[modules/vacation-service-implementation]]'
branch: release/2.1
---
# Vacation Day Calculation Verification

End-to-end verification: code formulas vs database state vs API responses on timemachine environment.

## Verified Employees

### arybin — AV=true (Нептун, norm=21, norm_deviation=BOTH)
**API response** (`/v1/vacationdays/arybin`): `availableDays: 20.193, normForYear: 21, pastPeriodsAvailableDays: 0, nextYearAvailableDays: 21`

**DB pool state** (`employee_vacation`): 2023=0, 2024=0, 2025=0, 2026=20.193, 2027=21

**FIFO distribution verified** (`vacation_days_distribution`):
- vac 46532 (2024-04-29): **split** 4.595 from 2023 + 2.405 from 2024 ← FIFO exhausting 2023
- vac 48743 (2025-01-02): **split** 1.785 from 2024 + 0.215 from 2025 ← FIFO exhausting 2024
- vac 50997 (2026-01-02): **split** 1.130 from 2025 + 0.870 from 2026 ← FIFO exhausting 2025

**Pool consumption by year**: 2023: 9.595, 2024: 23.190, 2025: 19.345, 2026: 0.870

**Norm deviation math** (2026): `available = 21 + normDev - consumed = 21 + 0.063 - 0.870 = 20.193` ✓

**Days summary**: totalAccruedDays=125.193, totalUsedDays=105, totalAdministrativeDays=7

### akonoplyov — AV=false (Венера, norm=24, no norm_deviation)
**API response** (`/v1/vacationdays/akonoplyov/years`): 2025=1, 2026=24, 2027=24

**DB pool state**: 2023=0, 2024=0, 2025=1, 2026=24, 2027=24

**FIFO verified**: vac 50067 (2025-07-25): **split** 2 from 2024 + 9 from 2025 ← exhausting 2024 pool

**Pool consumption**: 2023: 26 (>24 — carryover from prior years consumed), 2024: 24, 2025: 23

**Days summary**: totalAccruedDays=136.0, totalUsedDays=111, totalAdministrativeDays=0

## Key Findings

### 1. API ↔ DB Consistency: VERIFIED ✓
`/v1/vacationdays/{login}/years` returns exactly `employee_vacation.available_vacation_days` values. The API is a thin layer over the DB.

### 2. FIFO Distribution: IMPLEMENTED ✓ (at storage level)
`vacation_days_distribution` tracks fractional day consumption from oldest year first. Cross-year splits are common (3 found for arybin alone).

### 3. Norm Deviation Adjustments: VERIFIED ✓
AV=true offices with `norm_deviation_type=BOTH` have fractional `available_vacation_days` that differ from base norm (21). Formula: `available = norm + deviation - consumed_from_pool`.

### 4. Regular vs Advance Strategy Differences
| Aspect | AV=true (Нептун) | AV=false (Венера) |
|--------|-----------------|-------------------|
| Norm | 21 days/year | 24 days/year |
| Norm deviation | Active (BOTH) | None |
| Available days | Fractional (20.193) | Integer (24, 1) |
| Past years | All 0 (FIFO exhausted) | Mostly 0, some carryover |
| Future year | Always full norm (21) | Always full norm (24) |

### 5. FIFO Validation Gap: CONFIRMED
While FIFO **distribution** works correctly at storage level, the FIFO **validation** at creation time is missing (see [[investigations/bug-verification-s5]]). Distribution is handled by recalculation service; validation should prevent invalid states but doesn't.

### 6. Binary Search for Main Page Display
The `availableDays` field from `/v1/vacationdays/{login}` is the pre-computed value from `employee_vacation`. The binary search (`calculateForMainPage`) is only invoked for the "how many more days can you take" calculation, not for the balance display.

## Connections
- [[patterns/vacation-day-calculation]] — formula reference
- [[investigations/bug-verification-s5]] — FIFO validation gap
- [[modules/vacation-service-implementation]] — backend code
- [[exploration/data-findings/vacation-schema-deep-dive]] — schema reference

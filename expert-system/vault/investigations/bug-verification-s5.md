---
type: investigation
tags:
  - bugs
  - verification
  - vacation
  - concurrency
  - FIFO
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[debt/vacation-service-debt]]'
  - '[[modules/vacation-service-implementation]]'
  - '[[patterns/vacation-day-calculation]]'
branch: release/2.1
---
# Bug Verification — Session 5

## Bug #2: No Locking on Vacation Recalculation — CONFIRMED
**Location**: `VacationRecalculationServiceImpl`
**Issue**: Missing `@SchedulerLock` annotation on recalculation method. Concurrent recalculation runs could corrupt vacation day balances.
**Evidence**: Code-level — annotation absent while other scheduled tasks use `shedlock`.
**Severity**: High — data corruption risk in concurrent scenarios.

## Bug #4: FIFO Day Consumption Not Implemented — CONFIRMED
**Location**: `VacationAvailabilityChecker` → `AdvanceCalculationStrategy` (lines 44-81)
**Issue**: Requirements specify FIFO ordering (older vacation days consumed first, per #3067, #3347). Implementation only validates total available days — no FIFO validation or reallocation logic exists.

### Code Trace
1. `VacationAvailabilityChecker` delegates to `AdvanceCalculationStrategy` for advance vacation offices
2. `AdvanceCalculationStrategy.checkFutureVacationAvailability()` checks: `totalAvailableDays >= vacation.getDays()` (line 80)
3. `VacationAvailablePaidDaysCalculatorImpl` (lines 121-130) converts to administrative if insufficient days but does NOT revalidate FIFO ordering

### Missing Logic
- No check that older days are consumed before newer ones
- No detection of office transfers with different entitlement rates
- No recalculation of entitlements on transfer
- No FIFO constraint revalidation after entitlement changes

**Severity**: High — business rule violation. Advance vacation offices may consume future-year days before prior-year days.

## Updated Bug Tracker (S2 → S5)
| Bug | Description | Status | Session |
|-----|------------|--------|---------|
| #1 | Negative vacation days (-60 cluster) | NOT CONFIRMED at data level, code investigation ongoing | S4 |
| #2 | No locking on recalculation | **CONFIRMED** | S5 |
| #3 | Negative day cluster exists | CONFIRMED (-60 day cluster) | S4 |
| #4 | FIFO not implemented | **CONFIRMED** | S5 |

## Connections
- [[debt/vacation-service-debt]] — original bug discovery
- [[modules/vacation-service-implementation]] — code context
- [[patterns/vacation-day-calculation]] — calculation strategies
- [[investigations/vacation-approval-workflow-e2e]] — data verification

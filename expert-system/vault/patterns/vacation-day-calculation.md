---
type: pattern
tags:
  - vacation
  - calculation
  - strategy-pattern
  - business-logic
  - formula
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[vacation-service-implementation]]'
  - '[[REQ-vacations-master]]'
  - '[[REQ-advance-vacation]]'
branch: release/2.1
---
# Vacation Day Calculation Strategies

Two strategies based on `office.advanceVacation`, implemented via strategy pattern.

## RegularCalculationStrategy (AV=false, Russia)
```
availableDays = accruedDays + currentYearDays + pastYearDays - normDays + futureDays + editedVacationDays
accruedDays = paymentMonth × (normDays / 12)
```
The `- normDays` compensates for full annual norm credited at year start. Effectively monthly accrual model. If result < 0, display 0.

## AdvanceCalculationStrategy (AV=true, Cyprus/Germany)
```
availableDays = currentYearDays + pastYearDays + futureDays + editedVacationDays
```
No monthly accrual — full year balance available immediately. Can go negative.

## Maternity Special Case
`maternity=true` → available = sum of ALL year balances (no year restriction).

## Binary Search for Main Page Display
`VacationAvailablePaidDaysCalculatorImpl.calculateForMainPage` uses binary search to find max vacation duration. O(N × log(maxDays)) calls to `calculate` — computationally expensive.

## Norm Deviation Recalculation (AV=true offices)
Monthly: `daysDelta = (reported - personalNorm) / 8` (hardcoded REPORTING_NORM=8). Overtime adds, undertime deducts from earliest year. If all years exhausted, current year goes negative.

## FIFO Day Consumption
Days consumed from earliest year first. On cancel/reject/edit: days returned to pool, redistributed among NEW/APPROVED using FIFO. Recalculation returns ALL regular days to balance then re-distributes — if insufficient, auto-converts later requests to ADMINISTRATIVE.

Links: [[vacation-service-implementation]], [[REQ-vacations-master]], [[REQ-accrued-vacation-days]], [[REQ-advance-vacation]], [[analysis/absence-data-model]]

---
type: investigation
tags:
  - vacation
  - av-true
  - multi-year
  - balance
  - frontend-bug
  - sprint-15
  - ticket-3361
created: '2026-03-16'
updated: '2026-03-16'
status: active
related:
  - '[[patterns/vacation-day-calculation]]'
  - '[[analysis/vacation-business-rules-reference]]'
  - '[[modules/vacation-service-implementation]]'
  - '[[external/tickets/sprint-14-15-overview]]'
---
# Vacation AV=True Multi-Year Balance Distribution Bug (#3361)

## Summary

Frontend bug in AV=true offices: "vacation days left" display used `currentYear` field instead of `availablePaidDays`, leading to incorrect available-days display when vacations span multiple years and days are redistributed.

## Bug Description

**Ticket:** #3361 — `[Bug] [Vacations] AV=True. Incorrect multi-year balance days distribution in cases of transition from the current year to the next`

**State:** opened (both MRs merged, fix deployed but ticket not closed)
**Sprint:** 15, labeled "Production Ready"
**Assignee:** Olga Maksimova (QA), fixes by Ilya Shumchenko (dev)

### Case 1 — Available Days Display
When AV=true employee creates vacation with payment month in next year, `currentYear` balance shows 0 even though days are available. Root cause: frontend displayed `currentYear` (static per-year balance) instead of `availablePaidDays` (dynamically computed after redistribution).

**Example:** User `tdemetriou` (Neptun SO, AV=true). Creating next-year vacation incorrectly blocked current-year vacation creation.

### Case 2 — Multi-Year Redistribution
When editing vacation spanning Dec→Jan (e.g., `22.12.25–11.01.26`, 13 days), the redistribution algorithm should move days between vacations across year boundaries. Algorithm didn't work — 10 balance days from 2025 used in `09.02.26–22.02.26` should shift to the Dec-Jan vacation.

## Fix Details — 2 MRs (Frontend Only)

### MR !5169 (merged 2026-01-28) — Display Field Switch
**2 files changed:**

1. `VacationEventsModal.js` line 120:
```javascript
// BEFORE (bug):
<div>{userVacationDays.currentYear}</div>
// AFTER (fix):
<div>{userVacationDays.availablePaidDays}</div>
```

2. `UserVacationsPage.js` line 102:
```javascript
// BEFORE (bug):
{vacationDays.currentYear || 0}
// AFTER (fix):
{vacationDays.availablePaidDays || 0}
```

### MR !5211 (merged 2026-02-04) — Redux Reducer Fix
**1 file changed:** `myVacation/reducer.ts` line 175:
```typescript
// BEFORE (bug): safeToFixed corrupts structured daysLimitation object
daysLimitation: safeToFixed(daysObject.daysLimitation),
// AFTER (fix): preserve raw API value
daysLimitation: daysObject.daysLimitation,
```

`safeToFixed()` formats numbers to fixed decimal places, but `daysLimitation` is a structured object/null — formatting corrupted it.

## API Endpoint

`GET /v1/vacationdays/available` — the key endpoint for "available vacation days" display.
**Params:** `employeeLogin`, `newDays`, `paymentDate`, `usePaymentDateFilter`
**Returns:** `availablePaidDays` (correct redistributed value), `daysNotEnough[]`

**BDD test scenario from dev (snavrockiy):**
- Office "TTT HQ" with AV=true, 21 days/year norm
- Employee creates vacation 2026-01-25 to 2026-02-21 (21 days)
- Days distribution: `2025: 21` (all from current year)
- Balance becomes: `2025: 0, 2026: 21`
- `GET /v1/vacationdays/available` with `usePaymentDateFilter=true` → `availablePaidDays: 21.0`

## Sub-Bugs Found During QA (by omaksimova)

### Sub-bug #3 — Future Vacations Don't Affect Display
Available vacation days count doesn't reflect future vacations. Creating vacation in November 2026 doesn't change the display for the current period.

### Sub-bug #4 — Missing Ineligibility Tooltip
Tooltip explaining vacation ineligibility not displayed for new employees during 3-month waiting period. Affects **both** AV=true and AV=false offices. Env: qa-2, stage.

### Sub-bug #4.1 — Rehired Employee Waiting Period
Employees rehired the day after termination get incorrect 3-month waiting period calculation. User `vmatveev`, env qa-2. Clarification from imalakhovskaia: 3-month period applies from first day of employment for all users.

## Test Scope

1. **Display accuracy:** `availablePaidDays` vs `currentYear` — verify correct value shown after creating multi-year vacations
2. **Redistribution:** Create vacation spanning year boundary → verify days shift correctly from other vacations
3. **daysLimitation:** Verify structured object preserved in Redux state (not formatted as number)
4. **API contract:** `/v1/vacationdays/available` returns correct `availablePaidDays` for AV=true offices
5. **Waiting period tooltip:** Verify tooltip appears for new/rehired employees (AV=true and AV=false)
6. **Future vacation impact:** Verify creating future vacations updates available-days display

## Related
- [[patterns/vacation-day-calculation]] — FIFO and AV formulas
- [[analysis/vacation-business-rules-reference]] — business rules
- [[modules/vacation-service-implementation]] — backend service
- [[external/requirements/REQ-advance-vacation]] — AV=true spec
- [[external/tickets/sprint-14-15-overview]] — sprint context

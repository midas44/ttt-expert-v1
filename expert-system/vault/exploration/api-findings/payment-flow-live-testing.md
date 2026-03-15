---
type: exploration
tags:
  - api-testing
  - payment
  - vacation
  - accounting
  - bugs
  - timemachine
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/accounting-backend]]'
  - '[[exploration/ui-flows/accounting-pages]]'
  - '[[exploration/data-findings/vacation-schema-deep-dive]]'
branch: release/2.1
---
# Payment Flow Live Testing

## Endpoints Tested (timemachine env)

### Payment Dates: GET /v1/paymentdates
- Params: `vacationStartDate`, `vacationEndDate` (yyyy-MM-dd)
- Returns: Set of 1st-of-month dates between (vacStart - 2mo, bounded by report period) and (vacEnd + 6mo)
- Auth: API_SECRET_TOKEN ✓

### Available Paid Days: GET /v1/vacationdays/available
- Params: `employeeLogin`, `paymentDate`, `newDays`, optional `vacationId`, `usePaymentDateFilter`
- Returns: `availablePaidDays` + `daysNotEnough` (list of future vacations at risk)
- `newDays=0` triggers binary search "main page" mode → returns safe maximum
- Auth: API_SECRET_TOKEN ✓

### Pay Vacation: PUT /v1/vacations/pay/{vacationId}
- Body: `{"regularDaysPayed": N, "administrativeDaysPayed": N}`
- Validation: days sum must match vacation total, status must be APPROVED, period must be EXACT
- Field validation: regularDaysPayed/administrativeDaysPayed Range(0-366), NotNull
- Creates `vacation_payment` record, sets status → PAID, publishes VacationStatusChangedEvent
- Auth: API_SECRET_TOKEN ✓

### Days By Years: GET /v1/vacationdays/{login}/years
- Returns: `[{year, days}]` per-year breakdown
- Auth: API_SECRET_TOKEN ✓

### Days Summary: GET /v1/timelines/days-summary/{login}
- Returns: `totalAccruedDays`, `totalUsedDays`, `totalAdministrativeDays`
- Auth: API_SECRET_TOKEN ✓

## Bugs Found

### BUG-1 (HIGH): VacationStatusUpdateJob 2-hour processing window
The cron job (`0 */10 * * * *`) queries `findRecentNew(now.minusHours(2))` — entries older than 2 hours are **permanently orphaned**. Found 6 stuck `NEW_FOR_PAID` entries for Saturn office (created 2026-03-13 18:22-18:27, now >19h old). These will never be processed. The status_updates table lacks any cleanup/retry mechanism.

### BUG-2 (MEDIUM): No payment type alignment validation
ADMINISTRATIVE vacation (id 51421) successfully paid with `regularDaysPayed=1, administrativeDaysPayed=0`. The `checkForPayment` validates only total days match (`regular + admin == vacation.getDays()`), NOT that the day type distribution matches `paymentType`. Allows incorrect accounting classification.

### BUG-3 (MEDIUM): Payment dates accepts start > end
`GET /v1/paymentdates?vacationStartDate=2026-04-01&vacationEndDate=2026-03-01` returns valid results (same as normal range). No validation that start ≤ end.

### BUG-4 (MEDIUM): DB/API data representation inconsistency
ADMINISTRATIVE vacations store days in DB `regular_days` column (e.g., `regular_days=1, administrative_days=0`), but the API returns them swapped: `regularDays=0, administrativeDays=1`. The DTO conversion transposes based on `payment_type`. This means DB queries for reporting would give wrong day-type breakdowns.

### BUG-5 (LOW): Available days accepts negative newDays
`newDays=-5` returns `availablePaidDays=16.0` without error. Should reject non-positive values.

### BUG-6 (LOW): Stack trace leakage on invalid payment date format
Invalid date `2026-13-01` returns full Spring exception class and conversion details in response body.

## Behavioral Findings

### Vacation day balance unchanged on payment
Pre/post payment comparison for anazarov (vacation 51180, 3 days):
- Before: 2025=6, 2026=24, 2027=24
- After: 2025=6, 2026=24, 2027=24 (identical)
Days are deducted at **approval** time, not payment time. Payment is purely an accounting status transition (APPROVED → PAID).

### Timeline audit gaps for payment events
VACATION_PAID timeline events have `days_used=0, administrative_days_used=0` — the event doesn't record how many days were paid or the regular/admin split. Also `previous_status=NULL`. Audit trail for payment actions is incomplete.

### Validation coverage summary
| Scenario | Result | Error Code |
|----------|--------|-----------|
| Days mismatch (2 of 3) | 400 | exception.vacation.pay.days.not.equal |
| Already PAID | 400 | exception.vacation.status.notAllowed |
| Nonexistent vacation ID | 400 | Vacation id not found |
| Negative days (-1) | 400 | must be between 0 and 366 |
| Null/empty body | 400 | regularDaysPayed/administrativeDaysPayed must not be null |
| Correct payment (3/0) | 200 | Status → PAID ✓ |
| ADMIN payment (0/1) | 200 | Status → PAID ✓ |
| ADMIN with wrong type (1/0) | 200 | ⚠ Allowed (BUG-2) |

### Automatic payment (payExpiredApproved)
- Cron-triggered, finds APPROVED vacations >2 months old
- Auto-distributes: REGULAR → all regularDays, ADMINISTRATIVE → all adminDays
- Uses ShedLock for distributed locking

## Test Data
- Paid vacation 51180 (anazarov, REGULAR, 3 days) → payment_id 844030
- Paid vacation 51431 (tpotapova, ADMINISTRATIVE, 1 day)
- Paid vacation 51421 (ekotov, ADMINISTRATIVE, 1 day — with wrong type split)

## Connections
- [[modules/accounting-backend]] — backend implementation
- [[exploration/ui-flows/accounting-pages]] — UI exploration
- [[exploration/data-findings/vacation-schema-deep-dive]] — DB schema
- [[modules/vacation-service-implementation]] — vacation state machine
- [[exploration/api-findings/vacation-crud-api-testing]] — earlier API testing

---
type: module
tags:
  - accounting
  - backend
  - periods
  - payment
  - vacation-days
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[analysis/office-period-model]]'
  - '[[modules/vacation-service-implementation]]'
  - '[[exploration/ui-flows/accounting-pages]]'
branch: release/2.1
---
# Accounting Backend

## Overview
Accounting operations span two services: TTT (period management, report accounting) and Vacation (payment, day corrections). Available to ACCOUNTANT, CHIEF_ACCOUNTANT, and ADMIN roles.

## Period Management (OfficePeriodController)
Two period types per salary office: **Report Period** (reporting hours starting from) and **Approve Period** (confirming hours starting from).

### Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/offices/periods/report/min` | Earliest report period across offices |
| GET | `/v1/offices/periods/report/max` | Latest report period |
| GET | `/v1/offices/periods/approve/min` | Earliest approve period |
| GET | `/v1/offices/periods/approve/max` | Latest approve period |
| GET | `/v1/offices/{officeId}/periods/report` | Office report period |
| PATCH | `/v1/offices/{officeId}/periods/report` | Advance/revert report period |
| GET | `/v1/offices/{officeId}/periods/approve` | Office approve period |
| PATCH | `/v1/offices/{officeId}/periods/approve` | Advance/revert approve period |

### Business Rules
**Report Period Constraints:**
- Must start on 1st of month
- Cannot move before approve period start date

**Approve Period Constraints:**
- Cannot move earlier than 2 months ago on the 2nd day (e.g., today 2026-03-13 → min 2026-01-02)
- Cannot advance past the report period start date
- Can only move by **exactly one month** at a time
- If any employee has extended report period → cannot modify (`CODE_ERROR_APPROVE_CHANGE_MORE_THAN_ONE_MONTH`)

## Vacation Payment (PayVacationService)

### Payment Workflow (payVacation)
1. **Acquire write lock** — prevents concurrent modifications
2. **Create payment record** — `VacationPaymentEntity` with `regularDaysPayed` + `administrativeDaysPayed`
3. **Validate** — status must be APPROVED, period EXACT, role must be ACCOUNTANT/CHIEF_ACCOUNTANT
4. **Update vacation status** to PAID
5. **Return unpaid days** — if paid fewer days than vacation duration, return remainder to balance
6. **Recalculate** — update employee vacation day totals
7. **Publish event** — `VacationStatusChangedEvent`

### Validation Rules (checkForPayment)
- `regularDays + administrativeDays` must equal `vacation.getDays()`
- Status must be APPROVED
- Period type must be EXACT (not APPROXIMATE)
- User must have ACCOUNTANT or CHIEF_ACCOUNTANT role

### Automatic Payment (payExpiredApproved — scheduled)
- Triggered by cron job
- Finds APPROVED vacations older than 2 months (`today.minusMonths(2).withDayOfMonth(2)`)
- Auto-distributes days as regular/administrative based on vacation paymentType

### Day Return Logic
When partial payment (e.g., paid 20 of 25 days):
- Subtracts paid days from **next year balance first**
- If next year goes negative, adds overage to **this year**
- Creates corrected `VacationDaysBO` with new split

## Vacation Day Corrections (EmployeeDaysService)
| Endpoint | Purpose |
|----------|---------|
| `PUT /v1/vacationdays/{login}` | Manual adjustment with comment (audit trail) |
| `POST /v1/vacationdays/recalculate` | Bulk recalculate for salary office |
| `GET /v1/vacationdays/available` | Calculate available paid days |

## Accounting Report Search & Notifications (TaskReportAccountingService)
- **search()**: Find reports requiring accounting review (permission: `ACCOUNTING.VIEW`)
- **notifyManagers()**: Send email notifications to managers (permission: `ACCOUNTING.NOTIFY`)
- Templates: `APPROVE_REQUEST` (general) and `APPROVE_REQUEST_FOR_EMPLOYEE` (per-employee)
- CC's the triggering accountant

## Role Access Matrix
| Operation | Required Role |
|-----------|--------------|
| View accounting reports | ACCOUNTING.VIEW permission |
| Send notifications | ACCOUNTING.NOTIFY permission |
| Advance/revert periods | ADMIN or ACCOUNTANT |
| Pay vacation | ACCOUNTANT or CHIEF_ACCOUNTANT |
| Adjust vacation days | ACCOUNTANT or ADMIN |

## Connections
- [[analysis/office-period-model]] — period dual model
- [[modules/vacation-service-implementation]] — vacation state machine
- [[modules/email-service]] — notification templates
- [[exploration/ui-flows/accounting-pages]] — UI exploration
- [[patterns/vacation-day-calculation]] — day calculation formulas

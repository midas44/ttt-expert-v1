---
type: analysis
tags:
  - absences
  - vacation
  - sick-leave
  - dayoff
  - data-model
  - priority-1
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[database-schema]]'
  - '[[vacation-service]]'
  - '[[db-data-overview-tm]]'
branch: release/2.1
---
# Absence Data Model Analysis

Three types of absences with related but distinct data models.

## 1. Vacations
**Tables**: vacation, vacation_approval, vacation_days_distribution, vacation_payment, vacation_status_updates, vacation_notify_also

**Lifecycle**: NEW → APPROVED → PAID (happy path)
- Also: NEW → REJECTED, NEW/APPROVED → DELETED

**Approval Model**: Multi-approver via `vacation_approval` table
- Approval statuses: ASKED → APPROVED/REJECTED (per approver)
- 10,250 ASKED + 6,333 APPROVED + 4 REJECTED on timemachine

**Day Distribution**: `vacation_days_distribution` tracks how vacation days are allocated across years (vacation_id + year → days). Supports cross-year vacations.

**Payment Types**: REGULAR (paid), ADMINISTRATIVE (unpaid / за свой счёт)
- Vacation can have both `regular_days` and `administrative_days` — mixed-type possible

**Payment**: Separate `vacation_payment` table (linked via `vacation_payment_id` FK)

## 2. Sick Leaves
**Tables**: sick_leave, sick_leave_file, sick_leave_notify_also

**Lifecycle**: OPEN → CLOSED (happy path)
- Also: OPEN → REJECTED, OPEN → DELETED

**Dual Status**: Separate `accounting_status` (NEW → PAID/REJECTED) for payment tracking

**No approval workflow** — sick leaves don't have an approval table. Accountant handles via `accounting_status`.

**Files**: Can attach files via `sick_leave_file` table (supporting documents)

## 3. Days Off
**Tables**: employee_dayoff (confirmed), employee_dayoff_request (with approval), employee_dayoff_approval

**Two-table pattern**: Request goes through approval; confirmed day-off stored separately
- Request statuses: NEW → APPROVED/REJECTED/DELETED/DELETED_FROM_CALENDAR
- Approval statuses: ASKED → APPROVED/REJECTED (same as vacation)

**DELETED_FROM_CALENDAR** — unique status suggesting calendar sync for day-offs

**Fields**: `original_date` + `personal_date` — day-off may be moved from one date to another; `duration` in days; `reason` text

## Shared Patterns
- All absence types track employee FK and creation_date
- Vacation and day-off share multi-approver approval pattern (ASKED/APPROVED/REJECTED)
- Sick leaves use simpler accountant-driven status model
- `*_notify_also` tables exist for vacation and sick leave — additional notification recipients

## Related
- [[vacation-service]]
- [[database-schema]]
- [[db-data-overview-tm]]
- [[vacation-workflows]]

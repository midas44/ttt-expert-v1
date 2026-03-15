---
type: exploration
tags:
  - database
  - vacation
  - schema
  - deep-dive
  - timemachine
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[analysis/absence-data-model]]'
  - '[[architecture/database-schema]]'
  - '[[vacation-service-implementation]]'
branch: release/2.1
---
# Vacation Schema Deep-Dive (ttt_vacation)

Timemachine env. 32 tables, 0 views. Core findings from schema analysis.

## Key Tables and Counts
- **vacation** (14,195): Core request table. Statuses: PAID 94%, DELETED 3%, APPROVED 1.5%, NEW 0.6%, REJECTED 0.4%. Types: REGULAR 88%, ADMINISTRATIVE 12%. `period_type` 100% EXACT (vestigial — PRELIMINARY eliminated).
- **vacation_payment** (10,317): No auto-increment sequence (externally-assigned IDs). Links to vacation via `vacation.vacation_payment_id`. Only PAID vacations link here.
- **employee_vacation** (3,716): Per-year balance. Range: -60 to 208 days. Negative allowed by `office.advance_vacation`. Index named "unique" but is NOT a unique constraint.
- **office_annual_leave** (37): Uses `since_year` versioning. Most offices 24 days. `advance_vacation` column always NULL — flag lives on `office` table instead (dead column).
- **timeline** (53,519): Append-only audit log, 34 event types. No FK constraints on vacation/day_off columns. Descriptions in Russian. Covers full lifecycle of vacations, day-offs, employees, maternity.
- **vacation_approval** (16,587): Multi-approver. ASKED 62%, APPROVED 38%, REJECTED 0.02%.
- **vacation_days_distribution** (5,281): Cross-year day allocation for boundary-spanning vacations.
- **employee_dayoff** (5,334): Credit/debit ledger — duration=8 (credit: worked holiday), duration=0 (debit: taking day off).
- **employee_dayoff_request** (3,238): APPROVED 90%, DELETED 7%, DELETED_FROM_CALENDAR 2.5%.
- **sick_leave** (348): Dual status system — `status` (OPEN/CLOSED/DELETED/REJECTED) and `accounting_status` (NEW/PAID/REJECTED). Independent workflows.
- **vacation_status_updates** (943): Batch payment processing log per office. 100% COMPLETED.
- **confirmation_period_days_distribution** (3): Nearly empty, fractional day adjustments. Appears to be new/rarely-used.

## Architectural Observations
1. **Dual naming legacy:** Table = `vacation`, sequence = `vacation_request_id_seq`. Was renamed.
2. **Soft text enums:** All status/type fields are `text` with no CHECK constraints. Validation application-level only.
3. **Multi-approval pattern:** Shared by vacations and day-offs: primary approver on main table + `_approval` table (ASKED/APPROVED/REJECTED) + `_notify_also` (required flag).
4. **Payment flow:** APPROVED → vacation_status_updates batch → PAID + vacation_payment record.
5. **Day-off notification typo:** `TOMMOROW` in scheduled_vacation_notification types.

Links: [[analysis/absence-data-model]], [[vacation-service-implementation]], [[architecture/database-schema]], [[modules/vacation-service]]

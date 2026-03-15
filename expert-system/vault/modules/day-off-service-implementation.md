---
type: module
tags:
  - backend
  - day-off
  - implementation
  - service
  - absences
  - priority-1
  - calendar
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[vacation-service-implementation]]'
  - '[[absence-data-model]]'
  - '[[frontend-day-off-module]]'
branch: release/2.1
---
# Day-Off Service Implementation

Backend service for compensatory day-off lifecycle. Implements "substitute day" workflow: employee works a public holiday → earns right to take a compensatory day off.

## Two-Table Pattern

**employee_dayoff_request** — mutable workflow state machine:
- Fields: id, employee, approver, original_date (immutable), last_approved_date (=public holiday date), personal_date (employee's chosen day), duration, status, reason, creation_date
- Statuses: NEW → APPROVED/REJECTED/DELETED/DELETED_FROM_CALENDAR. CANCELED exists in entity enum but never used (dead code).

**employee_dayoff** — settled credit/debit ledger:
- Fields: id, employee, original_date, personal_date, duration, reason, creation_date
- No status, no approver — pure accounting entries
- duration=0: taking day off (debit). duration=8/7: worked holiday (credit).

**employee_dayoff_approval** — optional FYI-style approvers (not blocking):
- ASKED → APPROVED/REJECTED per optional approver

## Field Naming Confusion
- `original_date`: immutable calendar source date
- `last_approved_date`: misleadingly named — actually the public holiday date (REST API correctly calls it `publicDate`)
- `personal_date`: employee's chosen compensatory day (editable before approval)

## Lifecycle

| Action | Method | Guard | Side effects |
|--------|--------|-------|-------------|
| Create | POST /v1/employee-dayOff | Authenticated | CPO self-approves; defaults originalDate=publicDate; upsert pattern |
| Approve | PUT /approve/{id} | Approver, NEW/REJECTED status | Writes 2 ledger entries + recalculates vacation days + updates month norms |
| Reject | PUT /reject/{id} | Approver, NEW/APPROVED (if personalDate ≥ report period start) | Status change only, no ledger update |
| Delete | DELETE /{id} | Owner, personalDate ≥ period start OR not APPROVED | Soft status=DELETED, no ledger update |
| Edit | PATCH /{id} | Owner only | Only personalDate changeable; resets optional approvals to ASKED |
| Change approver | PUT /change-approver/{id}/{approver} | Current approver | Old→optional, new approver removed from optional |
| System rejection | rejectedBySystem(officeId, date) | Calendar change | Bulk-rejects NEW requests for removed holiday |
| Calendar deletion | deleteDayOffs(date) | Calendar removes holiday | DELETED_FROM_CALENDAR + physically deletes ledger rows + vacation recalc |
| Office change | AutoDeleteHelper.update | Employee changes office | DELETED_FROM_CALENDAR + physically deletes all ledger entries for year |

## Approve — Ledger Mechanics
Two entries written on approval (upsert):
1. **lastApprovedDate slot** (credit reversal): duration from existing ledger or calendar or reportingNorm fallback
2. **personalDate slot** (debit confirmation): duration + reason from request

Then fires event → RecalculateVacationDaysHandler creates two CalendarDaysChanged models (diff=+1 for lastApprovedDate, diff=-1 for personalDate) → adjusts vacation balance. Also UpdateMonthNormHandler recalculates norms for both months.

## Permission Model (dynamic calculation)
| Actor | Conditions | Permissions |
|-------|-----------|------------|
| Approver | NEW/REJECTED | APPROVE |
| Approver | NEW/APPROVED, personalDate ≥ report period start | REJECT |
| Approver | Always | EDIT_APPROVER |
| Owner | personalDate ≥ period start OR status ≠ APPROVED | DELETE |
| Owner | Always | EDIT |
Read-only employees and non-ROLE_EMPLOYEE: no permissions. CPO: self-approve on creation.

## Calendar Conflict Handling
CalendarUpdateProcessorImpl.processDay: when calendar change introduces half-day (7h) or removes working day (0h), checks for conflicting employee_dayoff ledger entries → moves day-off to previous working day.

## Search Types
MY (own + calendar + ledger merge), ALL (admin), APPROVER, OPTIONAL_APPROVER, MY_DEPARTMENT, RELATED, DELEGATED_TO_ME. The MY view merges 3 data sources with date-matching heuristics.

## Warning System
`ExpiredNonApprovedEmployeeDayOffCommand` — warns PM/DM/ADMIN about unresolved NEW requests where personalDate or lastApprovedDate is past today.

## Notifications
Status change, approver changed, system rejection, calendar deletion, office change auto-delete, calendar conflict moves. **Hardcoded production URL**: `https://ttt.noveogroup.com/vacation/my/daysoff`.

## Bugs and Debt

**BUG: Transaction isolation** — `changeDayOffDaysAfterApprove` (ledger write) and `changeDayOffStatus` (status update) not atomic. Ledger can update without status change or vice versa.

**BUG: CANCELED dead code** — present in entity enum, absent from BO enum, never assigned.

**BUG: Duplicate setStatus call** — toEmployeeDayOffRequestBO lines 454-455 calls setStatus twice.

**DEBT: Misleading field name** — `last_approved_date` is actually the public holiday date.

**DEBT: rejectedBySystem vs deleteDayOffs inconsistency** — two code paths for same conceptual event (calendar invalidation) produce different terminal statuses.

**DEBT: Random.nextLong() for synthetic IDs** in findSoonDayOffs — display concern leaking into service.

**DEBT: Upsert on creation** — onDuplicateKeyUpdate can silently overwrite records.

**DEBT: Hardcoded production URL** in notification helper.

**DEBT: @SuppressWarnings** on 4 Checkstyle rules — acknowledged complexity.

Links: [[vacation-service-implementation]], [[frontend-day-off-module]], [[absence-data-model]], [[vacation-schema-deep-dive]]

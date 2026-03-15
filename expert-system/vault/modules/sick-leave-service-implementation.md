---
type: module
tags:
  - backend
  - sick-leave
  - implementation
  - service
  - absences
  - priority-1
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[vacation-service-implementation]]'
  - '[[absence-data-model]]'
  - '[[frontend-sick-leave-module]]'
branch: release/2.1
---
# Sick Leave Service Implementation

Backend service for sick leave lifecycle management.

## Entity: `SickLeave` (ttt_vacation.sick_leave)

Fields: id (BIGSERIAL), employee (FK), start_date, end_date, total_days (calendar), work_days (working), status (text enum), accountant (FK nullable), number (certificate, max 40), accounting_status (text enum, default NEW), accountant_comment.

Associated tables: `sick_leave_notify_also` (extra notification recipients), `sick_leave_file` (M:N to file table, max 5 per sick leave), `office_sick_leave_notification_receiver` (per-office accountant receivers).

## Dual Status System

**Main status** (`SickLeaveStatusType`):
- Stored: OPEN, CLOSED, REJECTED, DELETED
- Computed (query-time CASE WHEN, never persisted): SCHEDULED (OPEN + future start), OVERDUE (OPEN + past end)
- Read/write asymmetry: API returns SCHEDULED/OVERDUE but PATCH only accepts OPEN/CLOSED

**Accounting status** (`SickLeaveAccountingStatusType`): NEW → PROCESSING → PAID or REJECTED

**Coupling**: PAID → auto-close (status=CLOSED), REJECTED → status=REJECTED, PROCESSING → status=OPEN (reopens)

## Lifecycle

| Action | Method | Guard | Side effects |
|--------|--------|-------|-------------|
| Create | POST /v1/sick-leaves | Any authenticated user (!!) | Calendar calc, notify, crossing check |
| Edit | PATCH /v1/sick-leaves/{id} | PM only for own reports; admin/accountant for PAID | Two-step file update |
| Close | PATCH status=CLOSED | Number required | Sets CLOSED |
| Reopen | PATCH status=OPEN | Standard perms | Direct status overwrite |
| Delete | DELETE /v1/sick-leaves/{id} | Cannot delete PAID | Soft-delete, files/notify orphaned |
| Accounting | PATCH accounting_status | Admin/chief/office accountant only | Sets accountant FK |

## Validation Rules
- startDate ≤ endDate (bean validation)
- No overlapping active sick leaves (excludes DELETED/REJECTED)
- Vacation crossing: 409 if force=false, allowed if force=true
- Number required to close (max 40 chars)
- Max 5 files (5MB each via FileController)

## File Handling
Two-step: upload via POST /v1/files/upload → include UUID in create/patch. Diff-and-sync on update. FilesAddedEvent only on patch (not create). Soft-delete does NOT clean up file associations.

## Notifications (5 event types, async after commit)
- Created: NOTIFY_SICKLEAVE_OPEN / _BY_SUPERVISOR
- Changed: chain-of-responsibility dispatches CLOSED/DATES_CHANGED/NUMBER_CHANGED/REJECTED templates per editor type
- Deleted: NOTIFY_SICKLEAVE_DELETE / _BY_SUPERVISOR
- Files added: NOTIFY_SICKLEAVE_FILES_ADDED
- Vacation overlap: NOTIFY_EMPLOYEE_SICKLEAVE_OVERLAPS_VACATION

Recipients: employee's manager + optional approvers + notifyAlso + per-office notification receivers.

## Overdue Warning System
`OverdueSickLeaveCommand` — per-request check (not cron), evaluates OPEN + end_date < today, surfaces as `OVERDUE_SICK_LEAVE` warning.

## Permission Model
- View: TECH_LEAD, PROJECT_MANAGER, DEPARTMENT_MANAGER
- Accounting view: ACCOUNTANT, DM, CHIEF_ACCOUNTANT, VIEW_ALL, ADMIN
- Mutation: PM can only modify own reports' sick leaves; admin/accountant for PAID ones

## Bugs and Debt

**BUG: Reference equality in getEditorType()** — `employee == currentEmployee` uses `==` on two separately-fetched BO instances → always false. Notification editor type falls through to default.

**BUG: No creation permission check** — any authenticated user can create sick leave for any employee by supplying their login.

**DEBT: Orphaned records on soft-delete** — file and notify_also associations not cleaned up.

**DEBT: office_sick_leave_notification_receiver migration churn** — employee FK → email TEXT → employee FK. N+1 query pattern in getOfficeReceivers().

**DEBT: @SuppressWarnings** on ClassFanOutComplexity, ClassDataAbstractionCoupling, ParameterNumber — acknowledged but unaddressed.

**DEBT: SCHEDULED/OVERDUE asymmetry** — returned in API reads but not accepted in PATCH writes. Undocumented.

Links: [[vacation-service-implementation]], [[frontend-sick-leave-module]], [[absence-data-model]], [[vacation-schema-deep-dive]]

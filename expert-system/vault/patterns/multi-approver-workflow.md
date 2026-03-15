---
type: pattern
tags:
  - approval
  - workflow
  - multi-approver
  - vacation
  - day-off
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[vacation-service-implementation]]'
  - '[[exploration/data-findings/vacation-schema-deep-dive]]'
branch: release/2.1
---
# Multi-Approver Workflow Pattern

Shared pattern used by both vacation requests and day-off requests.

## Structure
- **Primary approver:** Set on main entity (`vacation.approver`, `employee_dayoff_request.approver`). Determines who can approve/reject.
- **Optional approvers:** Stored in `_approval` table with status: ASKED → APPROVED or REJECTED.
- **Notify-also:** Stored in `_notify_also` table with `required` flag. If required=true, acts as additional mandatory approver.

## Vacation Approval Flow
1. Creation: approver auto-assigned (CPO → self with manager optional; regular → manager; no manager → self)
2. Optional approvers can be added by: vacation owner, designated approver, or employee's manager
3. Primary approver approves → status moves to APPROVED
4. When ALL optional approvers approve → `VACATION_ALL_APPROVED` event fires
5. `changeApprover()`: old approver becomes optional with ASKED status; new becomes primary

## Day-Off Approval Flow
Same pattern. `changeDayOffDaysAfterApprove()` creates the actual day swap records.

## Database Evidence
- vacation_approval: 16,587 rows — 62% ASKED, 38% APPROVED, 0.02% REJECTED (4 total)
- employee_dayoff_approval: 5,447 rows — 62% ASKED, 38% APPROVED, 0.02% REJECTED (1 total)
- Very few rejections suggest culture of informal pre-approval

## State Reset
When vacation is edited (dates changed), all optional approvals are reset to ASKED.

Links: [[vacation-service-implementation]], [[exploration/data-findings/vacation-schema-deep-dive]], [[modules/vacation-service]], [[analysis/absence-data-model]]

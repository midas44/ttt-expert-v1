---
type: exploration
tags:
  - sick-leave
  - accounting
  - ui-testing
  - playwright
  - workflow
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/sick-leave-service-implementation]]'
  - '[[modules/frontend-sick-leave-module]]'
  - '[[external/requirements/REQ-sick-leave]]'
branch: release/2.1
---

# Sick Leave Accounting Workflow — UI Exploration

Tested on timemachine as `perekrest` (ROLE_ACCOUNTANT + ROLE_CHIEF_ACCOUNTANT). Session 11.

## Accounting Page (/accounting/sick-leaves)

### Table Columns (10)
Employee, Sick leave dates, Days (calendar), Work days, Sick note (number), Accountant, Salary office (filter: 27 offices), State (filter: 7 values), Status (filter: 4 values, **inline dropdown**), Actions

### Dual Status System (Confirmed)

**State** (derived from DB `status` + dates):
- Planned: OPEN + future start
- Started: OPEN + in progress
- Overdue: OPEN + past end
- Ended: CLOSED
- Deleted: DELETED
- Rejected: REJECTED

**Status** (accounting, stored as `accounting_status`):
- New, Pending, Paid, Rejected
- **No PENDING records in current data** — only NEW, PAID, REJECTED exist

### Accounting Status Transitions
**Any-to-any** — no enforced state machine. Both New→Paid and Paid→New are possible via inline dropdown.

### Action Buttons (Conditional)
| Button | Icon | Available When |
|--------|------|---------------|
| View sick note | Clipboard | Non-deleted, has attachments |
| Edit sick note | Pencil | Non-deleted |
| Leave a comment | Speech bubble | Always |
| (none) | — | Deleted: comment only |

### Edit Dialog
Fields: Employee (read-only), Start date, End date, Calendar days (auto-calc), Sick note number. **No accounting status** — managed only via inline dropdown.

## Employee View (/sick-leave/my)
- Columns: Sick leave dates, Calendar days, Number, Accountant, State, Actions
- **No "Status" column** — employees cannot see accounting status
- Has "Add a sick note" button

## Manager View (/vacation/sick-leaves-of-employees/my-department)
- Tabs: My department, My projects
- Columns: Employee, Sick leave dates, Calendar days, State (filter), Status (filter), Actions
- Status shown as **plain text** (not dropdown) — managers see but cannot change
- Overdue records show green checkmark action

## Bugs/UX Issues
1. **No bulk operations** — no checkboxes, each record processed individually
2. **Unrestricted status transitions** — Paid→New possible (no guardrails)
3. **"Rejected Rejected" label** — State filter shows duplicated text
4. **215 unprocessed records** — CLOSED/NEW (62% backlog, never processed by accounting)
5. **NoveoAI widget overlap** — floating banner obscures Status/Actions columns

## Data Distribution
| State | Status | Count |
|-------|--------|-------|
| CLOSED | NEW | 215 |
| CLOSED | PAID | 96 |
| DELETED | NEW | 16 |
| REJECTED | REJECTED | 13 |
| OPEN | NEW | 8 |

## Related
- [[modules/sick-leave-service-implementation]] — backend
- [[modules/frontend-sick-leave-module]] — frontend
- [[external/requirements/REQ-sick-leave]] — Confluence requirements

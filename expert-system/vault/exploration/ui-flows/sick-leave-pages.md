---
type: exploration
tags:
  - ui-flow
  - sick-leave
  - playwright
  - timemachine
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[frontend-sick-leave-module]]'
  - '[[sick-leave-service-implementation]]'
  - '[[app-navigation]]'
branch: release/2.1
---
# Sick Leave UI Exploration (Timemachine)

Explored as Dmitry Dergachev (manager + accounting roles). Build 2.1.26-SNAPSHOT.290209.

## Page 1: /sick-leave/my — Employee View

**Title**: "My sick leaves". Single table, no tabs. "Add a sick note" button (blue, primary).

**Table columns**: Sick leave dates (sortable) | Calendar days (sortable) | Number (sortable) | Accountant (link to CS) | State (sortable) | Actions (2 icons per row)

**Actions per row**:
- Attachment icon (`data-testid="sickleave-action-attachments"`) → inline panel showing uploaded files
- Detail icon (`data-testid="sickleave-action-detail"`) → "More about the sick note" modal

**Detail modal fields**: Employee, Accountant, State, Status, Period, Calendar days, Number, Notify also.

**Create modal ("Adding sick note")**: Start date*, End date* (pickers), Calendar days (auto-calculated live), Number (optional, "needed to end sick leave"), File upload (JPG/JPEG/PNG/PDF, max 5 files, 5MB each), Notify also (multiselect, note: "manager, tech lead, accounting, PMs notified automatically"), info: "Sick pay paid after ending". Cancel / Save.

## Page 2: /vacation/sick-leaves-of-employees — Manager View

**Title**: "Sick leaves of employees". Redirects to `/my-department` default tab. "Add a sick note" button present.

**Two tabs**: My department | My projects

**Table columns**: Employee (CS link) | Sick leave dates (sortable, default desc) | Calendar days | State (filterable) | Status (filterable) | Actions (1 icon per row)

**Sample data**: Mix of Ended/Paid, Ended/New (unpaid), Rejected/Rejected. Pagination on My projects tab (~20/page).

## Page 3: /accounting/sick-leaves — Accounting View

**Title**: "Sick leave records". Accessible with accounting role. Shows "No data" with default filters (scoped to accountant's salary office).

**Table columns (richer)**: Employee | Sick leave dates | Days | **Work days** | **Sick note** (number) | Accountant | **Salary office** (filterable) | State (filterable) | Status (filterable) | Actions

**State filter values**: All, Started, Ended, Planned, Overdue, Rejected, Deleted.

No "Add a sick note" button — read-only view.

## Cross-Cutting Observations

**State vs Status distinction in UI**:
- **State** = lifecycle: Started / Ended / Planned / Overdue / Rejected / Deleted
- **Status** = payment: New / Paid / Rejected

Maps to backend: State ≈ main status (OPEN→Started/Planned/Overdue, CLOSED→Ended), Status ≈ accounting_status.

**No inline status editing** — state transitions driven by system processes and accountant actions, not direct UI buttons in these views. Accounting status change likely happens through a different mechanism (inline dropdown found in frontend code analysis but not observed in this exploration — may require correct salary office data).

**Number field**: Optional on creation, required to close (end) the sick leave.

Links: [[frontend-sick-leave-module]], [[sick-leave-service-implementation]], [[app-navigation]]

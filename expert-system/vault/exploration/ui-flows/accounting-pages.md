---
type: exploration
tags:
  - accounting
  - ui
  - playwright
  - salary
  - periods
  - payment
  - correction
  - sick-leave
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/accounting-backend]]'
  - '[[analysis/office-period-model]]'
  - '[[modules/sick-leave-service-implementation]]'
branch: release/2.1
---
# Accounting UI Exploration

## Access
User: `perekrest` (ROLE_CHIEF_ACCOUNTANT + ROLE_ACCOUNTANT). Accounting dropdown in nav with 5 sub-pages.

## 1. Salary Page (`/admin/salary`)
Report approval tracking for accountants.

**Controls**: Search by employee/salary office, period start/end date pickers, date range dropdown, "Show only leaving employees" checkbox, "Notify all managers" button.

**Table**: Employee (link to /report/{login}), Approved hours, Not approved hours, Managers who haven't confirmed, per-row email notification button. 15 rows/page.

**Key**: Accountant can notify individual managers (envelope icon) or all managers at once.

## 2. Changing Periods (`/admin/offices`)
Two tabs: **Salary offices** (default) and **Individual period changing**.

### Salary Offices Tab
Table: Salary office name (sortable), Reporting hours starting from, Confirming hours starting from, Edit action.
- 27 salary offices listed (Altair through Venera variants)
- All showing: Reporting = March 2026, Confirming = February 2026
- **Edit dialog**: Two month pickers for Report and Approve periods, Cancel/Edit buttons

### Individual Period Tab
Employee combobox + "Change the report period" button. Table: Employee, Reporting hours starting from, Salary office, Actions. Currently empty ("No data").

## 3. Vacation Payment (`/vacation/payment`)
Alert banner: "You have unpaid vacation requests. Please confirm their payment."

**Controls**: Payments month picker, quick month tabs (Jan-May 2026), "Pay all checked requests" bulk button.

**Table**: Employee (CS profile link), Vacation dates, Duration (days), Vacation type (Regular/Administrative, filterable), Salary office (filterable), Status (Not paid), Actions, Checkbox for bulk selection.

**Key observations**:
- Administrative vacations have no status/actions/checkbox — cannot be marked as paid
- Regular vacations show "Not paid" with checkbox for bulk payment
- 4 pages of data

## 4. Vacation Day Correction (`/vacation/days-correction`)
**Controls**: Search by employee/department manager, "Show dismissed employees" checkbox, department type filter.

**Table**: Employee (CS link), Manager (CS link), **Vacation days (inline editable!)**, Pending approval days, Department type (Production/Administration), Events feed button.

**Events Feed Dialog**: Shows employee name, annual vacation days left, work dates, events table (Date, Event, Paid/Unpaid days allowance/used), total row.

**Key**: Accountant can directly edit vacation day balance by clicking the cell — becomes editable text field. Events feed provides audit trail.

## 5. Sick Leave Records (`/accounting/sick-leaves`)
**Table**: Employee (CS link), Sick leave dates (sortable, desc), Days, Work days, Sick note number, Accountant, Salary office (filterable), State (filterable: Planned/Overdue/Deleted/Ended), **Status dropdown (New→Pending→Paid/Rejected)**, Actions (edit/download/delete).

**Key observations**:
- Status workflow: New → Pending → Paid (or Rejected)
- Overdue state highlighted in red
- Deleted sick leaves have no status changes allowed
- Actions vary by state (2-3 buttons: edit, download attachment, delete)
- 18 pages of data

## Connections
- [[modules/accounting-backend]] — backend implementation
- [[modules/sick-leave-service-implementation]] — sick leave accounting status
- [[analysis/office-period-model]] — period model
- [[patterns/vacation-day-calculation]] — day calculation
- [[modules/vacation-service-implementation]] — payment workflow

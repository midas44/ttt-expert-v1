---
type: exploration
tags:
  - ui
  - vacation
  - playwright
  - timemachine
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-vacations-master]]'
  - '[[vacation-service-implementation]]'
  - '[[multi-approver-workflow]]'
  - '[[app-navigation]]'
---
# Vacation UI Pages

Explored on timemachine via Playwright. Manager perspective (dergachev).

## My Vacations and Days Off (`/vacation/my`)

Redirects to `/vacation/my/my-vacation/OPENED`.

### Vacations Tab
- **Info panel**: Available days count, expected year-end balance, regulation link, events feed button
- **Filter tabs**: Open | Closed | All
- **Table columns**: Vacation dates, Regular days, Administrative days, Vacation type (filterable), Approved by, Status (filterable), Payment month, Actions
- **Actions**: Edit (pencil) + more options (three-dot)
- **Total row** sums regular + administrative days

### Days Off Tab (`/vacation/my/daysoff`)
- Year selector (date picker)
- "Weekend regulation" link (Confluence)
- **Table columns**: Date of event (with day-of-week), Duration, Reason, Approved by, Status, Actions
- **Localization bug**: Day-off reasons display in Russian even in EN mode (e.g., "Новый год")
- Duration: "0" = full day-off, "7" = pre-holiday shortened day
- Future dates have reschedule button

### Vacation Creation Dialog (Modal)
- **Fields**:
  - Vacation period: Two date pickers (DD.MM.YYYY), shows "Number of days: 0"
  - Payment month: Date picker (month selector)
  - Unpaid vacation: Checkbox
  - Approved by: Auto-populated (links to CS profile)
  - Agreed by: Empty field
  - Also notify: Multi-select employee dropdown
  - Comment: Textarea
- **Links**: "See Vacation regulation" (Confluence)
- **Buttons**: Cancel | Save

## Employees Requests (`/vacation/request`)

Redirects to `/vacation/request/vacation-request/APPROVER`.

- **Two main tabs**: Vacation requests | Days off rescheduling
- **Sub-tabs**: Approval | Agreement | My department | My projects | Redirected
- **Table columns**: Employee, Vacation dates, Vacation type, Manager, Approved by, Agreed by, Payment month, Status, Actions

## Employees Vacation Days (`/vacation/vacation-days`)
- Search by first/last name
- "Show dismissed employees" checkbox
- **Columns**: Employee (sortable, CS link), Vacation days, Pending approval
- Shows managed employees only (9 visible for this manager)

## My Sick Leaves (`/sick-leave/my`)
- "Add a sick note" button
- **Columns**: Sick leave dates, Calendar days, Number, Accountant, State, Actions
- States: "Ended"

## Sick Leaves of Employees (`/vacation/sick-leaves-of-employees`)
- Two tabs: My department | My projects
- "Add a sick note" button
- **Columns**: Employee, Sick leave dates, Calendar days, State (filterable), Status (filterable), Actions
- States: "Ended", "Rejected". Statuses: "Paid", "Rejected"

## Availability Chart (`/vacation/chart`)
- Gantt-style timeline, one row per employee
- Search by employee/project/manager/salary office
- View toggle: Days | Months
- Color coding: Blue = vacations, Green = longer absences
- Weekends/holidays highlighted yellow

## Key Findings
1. **Localization gap**: Day-off reasons are untranslated in EN mode
2. **Auto-populated approver**: Vacation form pre-fills approved-by from employee's manager
3. **Multi-approver UI**: "Agreed by" field separate from "Approved by"
4. **Payment month selector**: Accountant-facing field visible on creation
5. **Status-based filtering**: Both vacation type and status have filter dropdowns

See also: [[REQ-vacations-master]], [[vacation-service-implementation]], [[multi-approver-workflow]], [[app-navigation]]

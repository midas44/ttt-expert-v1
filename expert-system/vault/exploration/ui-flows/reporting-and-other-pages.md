---
type: exploration
tags:
  - ui
  - reporting
  - planner
  - statistics
  - playwright
  - timemachine
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[app-navigation]]'
  - '[[ttt-service]]'
  - '[[REQ-planner]]'
  - '[[REQ-statistics]]'
---
# Reporting, Planner, Statistics, and Other Pages

Explored on timemachine via Playwright. Manager perspective (dergachev).

## My Tasks / Time Reporting (`/report`)

Default page after login. Weekly time entry grid.

- **Task input bar**: "My project / my task, ticket number or URL 1,5h" + "Add a task" button
- **Monthly progress**: "Worked in March: 0/16/120/144" (current/days/hours/norm)
- **Week navigator**: Current week button, left/right arrows, date range (DD.MM.YYYY - DD.MM.YYYY)
- **Group by project**: checkbox toggle
- **Table**: Active tasks column, day columns (Mo-Su), "For the period", "Total"
- **Project rows**: collapsible with expand/collapse arrows
- **Pin icons**: next to task names (persist tasks in list)
- **Alert banners**: overdue day-off, over-reported hours, non-working days reminder
- **Footer**: vacation fund calculation rules link to Confluence

## Planner (`/planner`)

Redirects to `/planner/TABS_ASSIGNMENTS_TASK`.

- **Two tabs**: Tasks (default) | Projects
- **"Open for editing" button** (toggles edit mode)
- **Table columns**: No., Info, Tracker (filterable), Task/Ticket (sortable/filterable), Day column (with date navigation), Remaining work, Comment
- **Task rows grouped by project** (collapsible headers)
- **Tracker links**: external tracker URLs (e.g., ClickUp)
- **Sync indicator**: green checkmark

## Confirmation (`/approve`)

Redirects to `/approve/employees`.

- **Two tabs**: By employees | By projects
- **Filters**: Employee dropdown, "Show projects where I am a" (PM/SPM/etc.), "Show tasks of other projects", "With approved hours"
- Requires employee selection to show content

## General Statistics (`/statistics/general`)

- **Search bar**: by project/employee/task/customer with type buttons
- **6 tabs**: My tasks | My projects | Employees on my projects | Department projects | Department employees | Tasks by employees
- **Date range**: two pickers, preset dropdown
- **View options**: Tree/Flat list, Hours/Days format
- **Actions**: Refresh data, Export (CSV, with dropdown)
- **Table**: expandable rows with period/total columns

## Admin Panel

### Projects (`/admin/projects`)
Not explored in detail this session.

### Employees (`/admin/employees`)
Not explored in detail this session.

## Notifications (`/notifications`)
Not explored in detail this session.

See also: [[app-navigation]], [[ttt-service]], [[REQ-planner]], [[REQ-statistics]], [[REQ-confirmation]]

---
type: exploration
tags:
  - admin
  - ui
  - pm-tool
  - projects
  - employees
  - settings
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[exploration/ui-flows/app-navigation]]'
  - '[[external/tickets/pm-tool-integration]]'
  - '[[architecture/roles-permissions]]'
  - '[[architecture/security-patterns]]'
branch: release/2.1
---
# Admin Panel Pages

Comprehensive exploration of 7 admin pages on timemachine (user: perekrest).

## Navigation Structure
Admin panel dropdown: Projects, Employees, TTT parameters, Production calendars, API, Export. Plus /admin/account.

## Projects Page (/admin/projects)

Two tabs: "All projects" (11 pages) and "My projects"

**All Projects table**: Name, Customer, Supervisor, Manager, Type, Status, Actions
- **Types**: COMMERCIAL, INTERNAL, ADMINISTRATION, PRODUCTION
- **3 action buttons per row**: Task templates, Edit tracker data, More about project
- **Project detail dialog** links to `https://pm.noveogroup.com/projects/<ID>/profile/general`
- Employee names link to CompanyStaff profiles
- **NO create/edit project buttons** — all project metadata is read-only in TTT

**PM Tool Integration Confirmed**: Project names link to PM Tool. TTT only manages tracker data and task templates per project.

## Employees Page (/admin/employees)

Two tabs: Employees (20 pages) and Subcontractor (2 pages)
- **Entirely read-only** — no create/edit/delete
- Employee data synced from CompanyStaff
- Search by name, "Show dismissed" checkbox

## TTT Parameters (/admin/settings)

18 key-value parameters, editable by admin:
- Task autocomplete ranges (30/90/180 days)
- Notification emails and thresholds (over: 10%, under: -10%)
- Extended period duration (60 min)
- CSV export settings, presales URL
- Budget notification last handled timestamp

## Production Calendars (/admin/calendar)

Two tabs: "Setting up calendars" and "Calendars for SO"
- Year picker, Calendar dropdown (Russia shown), Add calendar, Create event buttons
- Lists non-standard days: holidays (0h), pre-holiday (7h)
- 18 calendar events for Russia 2026

## API Page (/admin/api)

12 API keys, each with: Name, Creator, UUID value, Allowed API methods
- 22 permission types: PROJECTS_ALL, VACATIONS_EDIT, TASKS_EDIT, etc.
- Notable keys: Autotest, Companystaff-vacations, Google-apps, InvoicingProd

## Export Page (/admin/export)

Single-purpose: "Highest number of hours by customer"
- Date range picker → Download CSV

## User Account (/admin/account)

Three tabs: General (API token, task carry-over), Trackers (per-user tracker config), Export (CSV format settings)

---
type: exploration
tags:
  - statistics
  - ui-exploration
  - phase-b-prep
  - permission-gating
  - tabs
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[modules/statistics-service-implementation]]'
  - '[[modules/frontend-statistics-module]]'
  - '[[exploration/api-findings/statistics-api-testing]]'
  - '[[analysis/role-permission-matrix]]'
branch: release/2.1
---
# Statistics UI Deep Exploration (Session 29)

Live UI exploration across multiple user roles on timemachine, combined with API endpoint testing. Phase B preparation for Statistics module (0 Qase cases, #1 generation priority).

## Tab Visibility Matrix (Live Verified)

| Permission | Tab (EN) | EMPLOYEE | Multi-Role (7+) |
|---|---|---|---|
| VIEW_MY_TASKS | My tasks | ✓ | ✓ |
| VIEW_MY_PROJECTS | My projects | ✗ | ✓ |
| VIEW_MY_PROJECTS | Employees on my projects | ✗ | ✓ |
| VIEW_MY_DEPARTMENT | Department projects | ✗ | ✓ |
| VIEW_MY_DEPARTMENT | Department employees | ✗ | ✓ |
| VIEW_MY_OFFICE | Office projects | ✗ | ✓ |
| VIEW_MY_OFFICE | Office employees | ✗ | ✓ |
| VIEW_PROJECT | @ Tasks by employees | ✗ | ✓ |
| VIEW_CUSTOMER | Customer projects | ✗ | ✗ (not observed) |
| VIEW_CUSTOMER | Customer employees | ✗ | ✗ (not observed) |

EMPLOYEE-only (alsmirnov): 1 tab. Multi-role (pvaynmaster/perekrest, 7 roles): 8 tabs. Customer tabs (2) never appeared — need VIEW_CUSTOMER permission. **Maximum observed: 8 of code-defined 13 tabs.**

## Search Filter Types

- EMPLOYEE: 3 filters (project, employee, task)
- Multi-role: 4 filters (+ customer) — customer filter requires VIEW_CUSTOMER

## Controls & Features

- **Date range**: Two datepickers with calendar icons (default: Jan 1 – Dec 31 current year)
- **Period preset**: Dropdown "Please select a date range"
- **List view**: Tree / Flat radio buttons (Flat default)
- **Time format**: Hours / Days radio buttons (Hours default)
- **Reset all filters**: Button (disabled when no filters active)
- **Refresh data**: Blue button
- **Export dropdown**: Copy the table | Download CSV | Copy link for Google tables

## Table Structure

**Columns**: Employee/project/task (sortable ↑↓), For the period, Total, Start date, End date
- Tree mode: expandable rows (employee → project → task hierarchy)
- Flat mode: all rows flat
- CompanyStaff profile link icon per employee
- Report page link icon per employee

## Employee Reports Sub-Page (/statistics/employee-reports)

- **Access**: Role-gated — 403 for EMPLOYEE-only users
- **Layout**: Full employee table with per-month hours, over-report color indicators
- **Features**: Absence icons (vacation/sick leave) inline, manager filter column, expandable project breakdown, comment field (saves on blur)

## API Endpoint Behavior (Timemachine, Session 29)

### /v1/statistic/permissions
22 permissions returned (flat list, id==name): EMPLOYEES_VIEW, OFFICES_VIEW, STATISTICS_VIEW, SUGGESTIONS_VIEW, PROJECTS_ALL, TASKS_EDIT, ASSIGNMENTS_VIEW/ALL, REPORTS_VIEW/EDIT/APPROVE, VACATIONS_VIEW/CREATE/EDIT/DELETE/APPROVE/PAY, VACATION_DAYS_VIEW/EDIT, CALENDAR_VIEW/EDIT, FILES_VIEW.

### /v1/reports/summary
Dual week/month breakdown. Response: `{week: {reported, personalNorm, norm, personalNormForDate, normForDate}, month: {...}}`. Units: HOURS. normForDate is progressive (0 at start of month, increases daily).

### /v1/reports/total
108 employees (March), supports type=EMPLOYEE|PROJECT|TASK, periodType=MONTH|WEEK. Units: MINUTES. Polymorphic response: employee type returns employee object, project type returns project object. Three statuses: WAITING_APPROVAL, APPROVED, NOTHING_APPROVE.

### /v1/reports/employees-over-reported
91 employees for Feb 2026 (closed period). Response: {total, data[]}. Items include bilingual names but no login field. Units: HOURS.

### Error Handling (500 Bug Pattern)
Systemic: all @RequestParam-required params return 500 (MissingServletRequestParameterException) when missing. Affects summary, over-reported, effort endpoints. DTO-bound @Valid params properly return 400.

## Bugs Found This Session

| ID | Severity | Description |
|---|---|---|
| BUG-STAT-UI-1 | LOW | Typo: "You do'nt have access" (misplaced apostrophe in "don't") |
| BUG-STAT-UI-2 | MEDIUM | Vacation statistic endpoint 403 → absence data fails silently, shows error banner |
| BUG-STAT-UI-3 | LOW | Language persistence: perekrest displayed RU despite EN script enforcement |

## Screenshots (artefacts/)

- `statistics-general-alsmirnov.png` — EMPLOYEE view (1 tab)
- `statistics-pvaynmaster.png` — Multi-role view (8 tabs, EN)
- `statistics-perekrest.png` — Multi-role view (8 tabs, RU)
- `statistics-employee-reports-pvaynmaster.png` — Employee Reports page
- `statistics-alsmirnov-clean.png` — EMPLOYEE view clean (RU)

## Related

- [[modules/statistics-service-implementation]] — backend
- [[modules/frontend-statistics-module]] — frontend (13 code-defined tabs)
- [[exploration/api-findings/statistics-api-testing]] — Session 11 API testing
- [[analysis/role-permission-matrix]] — permission mapping

---
type: exploration
tags:
  - confirmation
  - approval
  - ui-flow
  - live-testing
  - timemachine
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/ttt-report-confirmation-flow]]'
  - '[[modules/frontend-approve-module]]'
---

# Confirmation Flow Live Testing

Tested on timemachine as Galina Perekrest (7 roles: ACCOUNTANT, ADMIN, CHIEF_ACCOUNTANT, DEPARTMENT_MANAGER, EMPLOYEE, OFFICE_HR, PROJECT_MANAGER).

## UI Structure

### Two Tabs
- **By employees** (`/approve/employees/{index}`): Employee dropdown → shows one employee's tasks for a week
- **By projects** (`/approve/projects/{index}`): Project dropdown → shows all employees grouped under project

### Filters
- **Employee/Project dropdown** — searchable combobox
- **"Show projects where I am a"** — role filter (PM, Senior PM, etc.)
- **"Of other projects"** checkbox (By employees tab only) — shows tasks from projects where approver is not PM
- **"With approved hours"** checkbox — toggles visibility of already-approved tasks; when unchecked shows only REPORTED

### Week Navigation
- 6 week tabs shown, ranging from approve period start to current week
- Orange dot indicator on tabs with pending (REPORTED) items
- Approve period (office 2 = Сатурн): 2026-02-01 → weeks start from 26.01-01.02
- Report period: 2026-03-01

### Table Structure
- Columns: Active tasks, Mon-Sun (date headers), For the period, Total
- Day cells show hours (decimal, e.g., "0.5", "6.5", "7.5")
- Green background = REPORTED (pending approval), white = APPROVED
- Total row: reported/norm format (e.g., "8/8" = 8 reported out of 8 norm)
- Red text for days where norm is 0 (weekends) or reported < norm

## Approve/Reject Mechanics

### Per-Task Buttons
- Each task row has approve (✓) and reject (✗) icon buttons
- **Approve**: Single click → batch approves ALL reports for that task across all days in the week
- **Reject**: Click → opens tooltip with textarea (rejection comment) + Cancel/Reject buttons
- Rejection requires a comment before confirming
- Verified in DB: approve sets state=APPROVED, approver=current user ID (e.g., 9 for Perekrest)

### Header-Level Buttons
- Approve-all and reject-all buttons in the Active tasks column header
- Bulk "Approve" button (green, top-right corner) — approves all REPORTED tasks for the selected employee/project in the current week

### API Calls (from network trace)
- **Approve**: `PATCH /api/ttt/v1/reports` (batch) → 200, then refetches reports for the specific task
- **Data loading**: Complex chain of 15+ API calls per employee per tab switch
- **Period check**: `GET /v1/offices/{officeId}/periods/approve` fetched repeatedly (performance issue)

## Console Errors Found

1. **"employee is undefined"** — JS error after approve click (`TypeError: Cannot read properties of undefined`). Despite this, the approve action completes successfully. Non-blocking but indicates a race condition in the frontend state management.
2. **CompanyStaff photo fetch fails** — `cas-demo.noveogroup.com` returns ERR_BLOCKED_BY_ORB for thumbnail requests
3. **Feedback script load failure** — `feedback-preprod.noveogroup.com` script blocked

## Performance Issues

### Excessive Authentication Polling
Over 50 `GET /v1/authentication/check` calls during a single page interaction session. This is unnecessary polling — should use session validation on demand.

### N+1 API Pattern
For "By projects" view with N employees, the frontend makes:
- N calls to `/vacation/v1/vacations` (per employee)
- N calls to `/vacation/v1/sick-leaves` (per employee)
- N calls to `/vacation/v1/employee-dayOff` (per employee, per year × 2)
- N calls to `/v1/statistic/report/employees` (per employee)
= ~5N separate API requests for auxiliary data. For 8 employees = 40 requests.

### Repeated Approve Period Fetch
`/v1/offices/{officeId}/periods/approve` is called 6-8 times per page load instead of once.

## Data Verification (DB)

Reports for Alexander Ilnitsky (id=672) in week 02.03-08.03:
- March 2-4: All APPROVED, approver=9 (Perekrest), actual_efforts in minutes (30=0.5h, 390=6.5h, 60=1h, 450=7.5h)
- March 5: 2 reports still REPORTED (no approver) — matches UI green cells
- Confirms: approve acts per-task across all days, not per-cell

## Office Period Configuration

All 28 offices (except "Не указано" stuck at 2020-03-01) have consistent periods:
- REPORT start: 2026-03-01 (employees report from March)
- APPROVE start: 2026-02-01 (managers approve from February)
- "Не указано" (id=9): both periods at 2020-03-01 (frozen — no active employees)

## Connections
- [[modules/ttt-report-confirmation-flow]] — backend flow documentation
- [[modules/frontend-approve-module]] — frontend module analysis
- [[exploration/api-findings/report-crud-api-testing]] — API testing
- [[architecture/security-patterns]] — auth and permissions
- [[patterns/error-handling-agreement]] — error handling patterns

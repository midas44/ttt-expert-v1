---
type: module
tags:
  - frontend
  - confirmation
  - approval
  - redux
  - manager
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/ttt-report-service]]'
  - '[[modules/frontend-report-module]]'
  - '[[modules/frontend-planner-module]]'
branch: release/2.1
---
# Frontend Approve Module (Confirmation)

## Overview
84 files, 10,141 lines. Manager approval workflow for employee/project reports. Dual-tab interface (employees/projects) with weekday effort breakdown.

## Component Tree
```
ApprovePage
├─ Tabs (employees | projects)
│  ├─ Tab: Employees
│  │  └─ ReportsByEmployeesContainer
│  │     ├─ EmployeeFilter / RolesFilterContainer
│  │     ├─ EmployeeWeekdayEffort (cells: Mon-Sun)
│  │     ├─ TotalEmployeePeriodEffort (aggregated row)
│  │     ├─ ShowOtherProjectsInEmployeeContainer
│  │     └─ ShowApprovedTasksInEmployeesContainer
│  └─ Tab: Projects
│     └─ ReportsByProjectsContainer
│        ├─ ProjectFilter / RolesFilterContainer
│        ├─ ProjectWeekdayEffort (cells: Mon-Sun)
│        ├─ TotalProjectPeriodEffort
│        ├─ ShowOtherProjectsInProjectsContainer
│        └─ ShowApprovedTasksInProjectsContainer
├─ ApproveEffortOverLimitNotification
└─ TaskRename
```

## State Management (2 Redux Slices)
- **filters** (persisted): `approve_all_button_state`, `employee_current_tab`, `selected_employee/project`, `show_other_projects`, `show_approved_tasks`, date range, `reject_tooltip`, `role_types`, `approve_period`
- **data**: `employees[]`, `projects[]`, `employee_week_periods`, `project_week_periods`, `employee_approve_reports` (by login), `project_approve_reports` (by projectId), `report_params: {over, under}`

## Effort Calculation Pipeline (3 levels)
1. **mapTaskItemsWithEffort(taskItem)**: Per-task — extract isoWeekday → map to Mon-Sun fields, check APPROVE permission → approved effort, convert minutes→hours
2. **calculateTasksTotalEfforts(tasks)**: Cross-task — reduce all tasks summing each weekday column
3. **calculateAllEfforts(tasks)**: Main entry — chains above, returns reported + approved breakdown

## Status Enum
REPORTED → APPROVED | REJECTED (same as backend 3-state machine)

## Selectors (7 domain files)
`selectCommon`, `selectEmployeeReports`, `selectEmployees`, `selectFilters`, `selectProjectReports`, `selectProjects`, `selectReports`

## Sagas (5 files)
- `approveAllSagas.ts` — bulk approval
- `approveSagas.ts` — individual approve/reject
- `employeeTabSagas.ts` — employee tab operations
- `filtersSagas.ts` — filter state persistence
- `reportsTabSagas.ts` — project tab operations

## 18 Smart Containers
Key: `ReportsByEmployeesContainer`, `ReportsByProjectsContainer`, `EmployeeWeekdayEffort`, `WeekdayEffortContainer`, `TotalEmployeePeriodEffort`, `TotalProjectPeriodEffort`, `RolesFilterContainer`

## Tech Debt
- Complex permission model (`TTaskReportPermission` at multiple levels)
- Dual effort tracking (reported + approved columns) → parallel calculations
- Filter persistence to localStorage (state sync issues)
- Reports stored as unflattened arrays (no normalization)
- Effort calculation redundancy across helpers/selectors/API transforms
- Type flexibility: `TEmployeeApproveReports` accepts multiple data formats → hard to reason about
- Global reject tooltip state in Redux (doesn't scale)
- Heavy role-based conditional rendering (consider feature flags)

## Connections
- Backend: [[modules/ttt-report-service]] (approve/reject flow, period management)
- Shares notification controllers: [[modules/frontend-report-module]], [[modules/frontend-planner-module]]
- Approval workflow: [[investigations/vacation-approval-workflow-e2e]]

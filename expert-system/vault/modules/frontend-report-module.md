---
type: module
tags:
  - frontend
  - reports
  - my-tasks
  - redux
  - react-query
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/ttt-report-service]]'
  - '[[modules/frontend-app]]'
  - '[[modules/frontend-planner-module]]'
branch: release/2.1
---
# Frontend Report Module (MyTasks)

## Overview
53 files, 6,873 lines. Container/presentational pattern with Redux Ducks + React Query.

## Component Tree
```
ReportPage (connect)
├─ OverReportNotificationController
├─ AbsencesNotificationController
├─ RejectedReports
├─ AutoRejectedReports
├─ TitleContainer (employee name)
├─ TaskAddContainer (quick task search/add)
├─ EffortForPeriodContainer (week + month norms)
│  ├─ WeekSwitcherContainer (date navigation)
│  └─ ProjectsGroupedSwitcher (ungrouped/grouped toggle)
└─ TaskReportsContainer (main data table)
   ├─ TaskReports (ungrouped)
   └─ TaskReportsGrouped (by project)
```

## State Management (3 Redux Slices)
- **dataReducer**: `EMPLOYEE_REPORTS` (Record<login, {tasks, isLoading}>), `EMPLOYEE_REPORTS_SUMMARY`, `EMPLOYEE_REPORT_PERIOD`, `REJECTED_REPORTS`, `EMPLOYEE_PROJECT_REPORT_TOTALS`
- **filtersReducer**: `DATE_START/END/SELECTED` (Moment.js), `EMPLOYEE_LOGIN`, `COMMENT_TOOLTIP`
- **uiFiltersReducer**: `CLOSED_ROWS`, `IS_GROUPED`

## API Endpoints
- `GET /v1/task-auto-reject-warnings`
- `GET /v1/reports/summary {date, login}`
- `GET /v1/reports/effort {taskId, executorLogin?}`
- `GET /v1/periods/report/employees/{login}`
- `PATCH /v1/reports/{id} {effort, reportComment, state, stateComment}`
- `PATCH /v1/reports {items: UpdateTaskReportParamsRequest[]}`
- `POST /v1/reports {taskId, reportDate, effort, reportComment, state}`
- `POST/DELETE /v1/tasks/{id}/employees/{login}/pin`

## Key Business Logic
- **Effort calculation**: `calcEmployeeEffort()` — reduces tasks → sum reports effort → divide by 60 (minutes→hours)
- **Week/month period boundary logic** in selectors (complex date math with Moment.js)
- **Pin/unpin tasks** for quick access

## Tech Debt
- Moment.js dates (not date-fns)
- No data normalization (array-based storage)
- Cross-module notification coupling (OverReport, Absences controllers)
- Effort calculations duplicated across helpers, selectors, and API transformations
- Mixed JS/TS files

## Connections
- Shares notification controllers with [[modules/frontend-planner-module]] and [[modules/frontend-approve-module]]
- Backend: [[modules/ttt-report-service]] for submission/confirmation workflows
- API surface: [[architecture/api-surface]] TTT endpoints

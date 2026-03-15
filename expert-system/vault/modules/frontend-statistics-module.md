---
type: module
tags:
  - frontend
  - statistics
  - react
  - redux
  - rtk
  - react-query
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[statistics-service-implementation]]'
  - '[[frontend-app]]'
  - '[[ttt-report-service]]'
branch: release/2.1
---
# Frontend Statistics Module

Two parallel sub-systems within modules/statistics/:

## Sub-system A — Classic Statistics (`/statistics/general`)

Legacy hierarchical tree-table. connect() HOC + class-based reducers. JavaScript only.

### Component Tree
```
StatisticsPage
  ├── StatisticsFiltersPanel
  │     ├── SearchMultiFilterContainer (entity search)
  │     ├── TabsWithFiltersContainer (13 role-gated tabs via rc-tabs)
  │     ├── SelectDateContainer (date range + period presets)
  │     ├── ListTypeRadioGroupContainer (hours/days toggle)
  │     └── EffortTypeRadioGroupContainer
  ├── TableControls (export dropdown, refresh)
  ├── StatisticsTableContainer (rc-table tree-table with lazy child expansion)
  ├── TaskDetails (slide-in panel)
  └── TaskRename (inline dialog)
```

### Permission-Gated Tabs (13)
VIEW_MY_TASKS → MY_TASKS, VIEW_MY_PROJECTS → MY_PROJECTS + EMPLOYEES_IN_MY_PROJECTS, VIEW_MY_DEPARTMENT → DEPARTMENT tabs, VIEW_MY_OFFICE → OFFICE tabs, VIEW_MANAGER_OFFICE → OFFICE tabs, VIEW_PROJECT → PROJECT tabs, VIEW_CUSTOMER → CUSTOMER tabs, etc.

### State: `state.statistics` (persisted via redux-persist)
- permissions (role array), filters (dates, search values, current tab), uiFilters (sort, effort type, expanded keys), data (parent/child nodes, task details)

## Sub-system B — Employee Reports (`/statistics/employee-reports`)

Newer flat tabular view. RTK createAction/createReducer + React-Query for comments. TypeScript.

### Component Tree
```
EmployeeReportsContainer
  └── EmployeeReportsPage
        ├── Filters (employee search, month picker, over-limit toggle)
        └── ReportsTable
              ├── ManagerFilter (filterable column header)
              ├── EmployeeRow (expand + staff link + AbsencesIcon + nav link)
              ├── ProjectRow (on expand)
              ├── ManagerRow (staff link)
              └── CommentField (inline textarea, save on blur)
```

### State: `state.employeeReports` (not persisted)
- reports, isLoadingReports, params (startDate, endDate, employee, exceedingLimit, sort, order, managersLogin), projectBreakdown per employee

## Absence Icons (AbsencesIcon)
Displayed inline on employee rows. Two icons: IconSick (sick leaves), IconVacation (vacations). Tooltip shows breakdown: total hours + individual periods with dates, status, payment type. Hours/days unit from effortDisplayType setting.

## Norm Display
renderNormHours: shows `{personalNorm}` and if different, appends `({budgetNorm})` in parentheses.

## Over-Report Indicators
- reportedNotificationStatus → color class (LOW=underReported, NEUTRAL=normal, HIGH/NA=overReported)
- reportedStatus → directional arrows (HIGH/NA=up, LOW=down)
- exceedingLimit toggle pre-filters server-side

## API Endpoints (6 classic + 6 employee reports)
Classic: GET /v1/statistic/permissions, /employees, /employees/tasks, /tasks, /projects, /departments, export links. Employee Reports: GET /v1/statistic/report/employees, /report/projects, GET+POST /v1/statistic/report (comments).

Both call vacation service POST /v1/statistic and POST /v1/statistic/report/sick-leaves for absence data.

## Technical Debt (12 items)
1. **Split patterns**: Legacy connect+reducers vs RTK+React-Query in same module
2. **Partial TypeScript**: Employee Reports in TS, classic in JS
3. **Broken tab auto-selection**: statisticsPermissionsTabName mostly commented out → currentTab=null
4. **Hardcoded CompanyStaff URL**: `https://companystaff.noveogroup.com/profile/`
5. **processStatisticsData overwrites**: Only keeps last absence record per employee (childNodeList has individuals)
6. **getExpandedRowKeysForData bug**: Checks length===0 then iterates empty array (no-op)
7. **handleRemovingProcessingParent bug**: splice() receives item not index from find()
8. **Dual vacation/sick-leave API calls**: Both sub-systems fetch independently, no deduplication
9. **CommentField saves on blur only**: No auto-save, data lost on tab close
10. **projectBreakdown in local state**: Re-fetched on every navigation
11. **Stale filter persistence**: redux-persist preserves filters across sessions → confusion
12. **React element in Redux action**: FiltersError renders JSX inside saga put() — non-serializable

Links: [[statistics-service-implementation]], [[frontend-app]], [[ttt-report-service]]

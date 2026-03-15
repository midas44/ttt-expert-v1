---
type: module
tags:
  - frontend
  - sick-leave
  - react
  - redux
  - absences
  - priority-1
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[sick-leave-service-implementation]]'
  - '[[frontend-vacation-module]]'
  - '[[frontend-app]]'
branch: release/2.1
---
# Frontend Sick Leave Module

Split across two modules: `modules/sickLeave/` (employee + accounting, ~3,908 lines) and `modules/vacation/containers/sickLeavesOfEmployees/` (manager view).

## Routes

| Route | Page | Permission |
|-------|------|-----------|
| /sick-leave/my | MySickLeavePageContainer | SICK_LEAVE:VIEW (but **TODO: no router-level permission check**) |
| /vacation/sick-leaves-of-employees | SickLeavesOfEmployees | VACATIONS:SICK_LEAVE_VIEW |
| /accounting/sick-leaves | SickLeaveAccountingPage | VACATIONS:SICK_LEAVE_ACCOUNTING_VIEW |

## State Management

Redux + Redux-Saga (Ducks). Two state slices:
- `state.sickLeave`: currentSickList, showModal (key-value map), mySickLeavesTableData, tablePagination, sickLeaveAccounting (nested: data, tablePagination, tableFilter, currentSickList, showCrossNotification)
- `state.sickLeavesOfEmployees`: tableData (DM/TL), myProjectsTableData (PM), employeesField, tabCounters

## Modal System (12 types)
Centrally managed by SickLeaveModalManager. Multiple modals can stack (z-index tiers).
- Employee: CREATE_SICK_LIST (create/edit), SICK_LIST_DETAILS, DELETE_SICK_LIST, CLOSE_SICK_LIST, VACATION_CROSSING
- Accountant: EDIT_SICK_LEAVES_ACCOUNTING, ADD_COMMENT_SICK_LEAVES_ACCOUNTING (orphaned — replaced by inline tooltip)
- Manager: CREATE/EDIT/DETAILS/DELETE/CLOSE_EMPLOYEES_SICK_LIST

## Key UI Flows

**Create (employee)**: Date interval + document number (max 40) + file uploader (max 5, 5MB) + notify-also multiselect → saga uploads files first (parallel, cleanup on failure) → POST /v1/sick-leaves → check vacation crossing client-side

**Edit (employee)**: Same modal, isEdit flag. Two-step PATCH: first dates/number, then file diff + second PATCH for filesIds. Hidden when CLOSED+PAID or REJECTED.

**Close**: Requires document number entry → PATCH status=CLOSED + number

**Accounting status**: Inline dropdown in accounting table (SickLeaveAccountingStatusCell) — direct PATCH without modal. NEW → PROCESSING → PAID/REJECTED.

**Accountant comment**: Inline Tooltip overlay with textarea, not a modal.

**Manager create/edit**: Employee async-search + date interval + number. No file upload capability. force=true hardcoded (bypasses BE overlap). Client-side overlap check via pre-fetch (100 record cap).

## API Endpoints
GET /v1/sick-leaves (list with filters: employeeLogin, statuses, accountingStatuses, officeIds, view, etc.)
GET /v1/sick-leaves/{id} | POST /v1/sick-leaves | PATCH /v1/sick-leaves/{id} | DELETE /v1/sick-leaves/{id}
POST /v1/files/upload | GET /v1/files/{id}/download | DELETE /v1/files/{id}

## Technical Debt (10 items)
1. **Typo in action constant**: `'@sickLeave/REFRESHs_MY_SICK_LEAVES'` (extra 's')
2. **showCrossNotification state inconsistency**: defined at top-level but written inside handleAccounting wrapper
3. **ADD_COMMENT modal orphaned**: registered but never dispatched (inline Tooltip used instead)
4. **Missing router-level permission check**: `/sick-leave/my` has no role guard (TODO comment)
5. **MySickLeaveTableContainer re-fetches vacations on every render**: useEffect missing dependency array
6. **Manager saga 100-record overlap cap**: pre-fetch limited, force=true bypasses BE validation
7. **Mixed Redux patterns**: connect() HOC + hooks coexist
8. **Sort direction encoding**: +/- prefix mixed into sort field string
9. **Manager view has no file upload**: capability gap vs employee view
10. **Import path anomaly**: SickLeaveAccountingPageContainer imports from `@sickLeave/components/Index/Index` (path doesn't match actual structure)

Links: [[sick-leave-service-implementation]], [[frontend-vacation-module]], [[frontend-app]]

---
type: module
tags:
  - frontend
  - day-off
  - weekend
  - react
  - redux
  - absences
  - priority-1
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[day-off-service-implementation]]'
  - '[[frontend-vacation-module]]'
  - '[[frontend-app]]'
branch: release/2.1
---
# Frontend Day-Off Module

Day-off functionality embedded within the vacation module. No standalone module — uses "weekend" terminology throughout (Russian labour law concept of transferred working weekends).

## Routing (embedded in vacation routes)

No dedicated /vacation/daysoff route. Day-offs are tabs within:
- `/vacation/my` → "Days off" tab (WeekendTab.tsx) — employee view
- `/vacation/request` → "Postponements of weekends" tab — manager approval view

## Component Tree

**Employee view** (tab within UserVacationsPage):
```
WeekendTab → TableSimple (year-filtered)
  → useWeekendTableHeaders (date display logic by status)
  → WeekendsTableButtons (cancel postponement + edit)
  → TransferDaysoffModal (date picker for personal_date)
```

**Manager view** (tab within RequestVacation):
```
RequestTypeWeekendTabsContainer (5 sub-tabs: APPROVER, OPTIONAL_APPROVER, MY_DEPARTMENT, MY_PROJECTS, DELEGATED)
  → WeekendTable (TableAsync with approve/reject/redirect actions)
  → WeekendTableActions (role-dependent buttons)
  → WeekendDetailsModalContainer (approve/reject/redirect + optional approvers management)
  → WeekendRedirectFormContainer (change approver)
```

## Redux State (requestDaysoff/)
- currentTypeTab, modalLoading, weekendRedirectModal
- approverWeekendCount / optionalApproverWeekendCount (badge counts)
- tableData (entities, sort, order, page, total, size=20)
- tableFilters (statuses), pagination (sort, order, page, status, type)

**Quirk**: Initial currentTypeTab reads `window.location.pathname` at module load time (side-effect in reducer initializer).

## API Layer (daysOffApi.ts + myVacation/api.ts)
- GET /v1/employee-dayOff (list with filters: type, year, statuses, approverLogin, etc.)
- PUT /v1/employee-dayOff/approve/{id} | /reject/{id} | /cancel/{id}
- DELETE /v1/employee-dayOff/{id} (cancel postponement)
- PUT /v1/employee-dayOff/change-approver/{id}/{approver}
- POST /v1/employee-dayOff (create transfer request)
- PATCH /v1/employee-dayOff/{id} (update personalDate)
- GET/POST/DELETE/PATCH /v1/employee-dayOff-approvers (optional approvers CRUD)

## Key UI Flows

**Transfer day-off (employee)**: No standalone creation form — always from existing calendar working-weekend entry. Click edit → TransferDaysoffModal → datepicker with minDate=originalDate (or yesterday if past), maxDate=end of next year. POST creates new request, PATCH updates personalDate on existing.

**Cancel postponement (employee)**: X button on NEW status rows → DELETE /v1/employee-dayOff/{id}

**Approve/Reject (manager)**: Inline action buttons or via WeekendDetailsModal. Optional approvers vote via PATCH with APPROVED/REJECTED status. ApproveBar shows vote counts.

**originalDate vs personalDate display**: NEW status shows "lastApprovedDate → personalDate" (transfer arrow). Other statuses show only lastApprovedDate.

**Filtering**: WeekendTab hides rows where checking date is normal working day with duration=8 (full working-weekend entries without compensatory day-off).

## Availability Chart Integration
DayOffTooltip renders day-off blocks with date range. EventSquareWithTooltip maps DAY_OFF and WEEKEND event types to distinct CSS classes.

## Technical Debt (8 items)
1. **BUG: Hardcoded date '2024-03-10'** in WeekendTableActions isOnlyOneAction — test/stub value never replaced
2. **BUG: updateEmployeeDayoffRequest drops personalDate** — destructuring ignores it silently
3. **Typo: weekendOoptionalReject** (double 'o') in actions + sagas
4. **Side-effect in reducer**: getCurrentTab() reads window.location.pathname at import time
5. **Mixed .js/.ts/.tsx**: core containers remain JS, newer files TypeScript
6. **cancelDayoffRequest vs deleteDayoffRequest confusion**: PUT /cancel/{id} exists but UI uses DELETE for "cancel postponement"
7. **No standalone creation form**: day-offs always derived from calendar events
8. **WeekendTab filtering hides working-weekend entries**: may confuse users expecting full calendar view

Links: [[day-off-service-implementation]], [[frontend-vacation-module]], [[frontend-app]], [[absence-data-model]]

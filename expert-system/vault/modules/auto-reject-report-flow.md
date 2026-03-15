---
type: module
tags:
  - auto-reject
  - confirmation
  - reports
  - approval
  - notifications
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[ttt-report-confirmation-flow]]'
  - '[[frontend-approve-module]]'
  - '[[frontend-report-module]]'
  - '[[email-notification-triggers]]'
branch: release/2.1
---

# Auto-Reject Report Flow

## Overview

When the approval period closes for an office, all unconfirmed (REPORTED state) task reports within the closed period are automatically rejected. This is a backend-driven process triggered by accountant action, with UI notifications shown on the employee's My Tasks page.

## Important: UI Location Clarification

- **Auto-reject warnings display on the My Tasks page** (`/report`), NOT the Confirmation page (`/approve`)
- The Confirmation page only has `ApproveEffortOverLimitNotification` (effort threshold warnings)
- The `AutoRejectedReportsContainer` renders at the top of `ReportPage` (report/index.js line 44), between `RejectedReports` and `TitleContainer`

## Trigger Mechanism

1. Accountant closes approval period: `PATCH /{officeId}/periods/approve` (moves the approve period start forward)
2. Backend calls `TaskReportServiceImpl.rejectByOfficeId()` → `InternalTaskReportService.rejectNonApprovedTasks()`
3. All task reports with `state=REPORTED` in the previous month (before new approve period start) are batch-updated to `state=REJECTED`
4. A `Reject` record is created with `description='auto.reject.state'` — this distinguishes auto-rejections from manual ones (which have NULL description)
5. Notification emails sent to affected employees listing the affected months

## Warning Type Enum

`TaskReportWarningType` has 3 values:
- `DATE_EFFORT_OVER_LIMIT` — single-day effort exceeded
- `EMPLOYEE_REPORT_DATE_EFFORT_OVER_LIMIT` — employee-level daily effort exceeded
- `REJECTED_REPORT_ON_CONFIRMATION_PERIOD_CLOSE` — auto-reject warning (used by both warning controller and auto-reject controller)

## API Endpoints

| Endpoint | Controller | Used By | Auth |
|----------|-----------|---------|------|
| `GET /v1/task-auto-reject-warnings` | TaskReportAutoRejectController | My Tasks page | AUTHENTICATED_USER only |
| `GET /v1/task-report-warnings` | TaskReportWarningController | Confirmation page (effort warnings) | AUTHENTICATED_USER only |

## Frontend Component Chain

```
ReportPage (report/index.js)
  └─ AutoRejectedReportsContainer (containers/AutoRejectedReportsContainer)
       ├─ useGetAutoRejectWarnings() hook (ducks/api.ts)
       │   ├─ GET /v1/task-auto-reject-warnings
       │   ├─ Filters out hidden notifications from localStorage
       │   └─ Returns AutoRejectedReportsType[]
       └─ AutoRejectedReports (components/AutoRejectedReports)
            └─ Notification (error type) per warning
                ├─ Message: "Unconfirmed hours for task <taskName> were automatically rejected upon month closure"
                ├─ "Go to the report page" link → navigates to rejection week
                └─ Close button → hides via localStorage
```

## Backend Service Flow

```
PATCH /periods/approve (AccountantAction)
  → TaskReportServiceImpl.rejectByOfficeId(OfficePeriodBO)
    → InternalTaskReportService.rejectNonApprovedTasks()
      1. repository.findEmployeeWithUnconfirmedTasks(officeId, prevStart, currStart)
      2. Create Reject record (description='auto.reject.state')
      3. repository.findAllByOfficeIdAndReportMonth(...)
      4. Set all matching reports: state=REJECTED, reject=savedReject
      5. repository.saveAll(taskReports)
    → Send email notifications per affected employee
```

## Data Verification

No auto-rejected reports exist on any testing environment (timemachine, qa-1, stage). All reject records in `ttt_backend.reject` table have NULL description (= manual rejections only). The auto-reject feature has never been triggered on these environments.

## Design Observations

1. **BO leak**: `TaskReportAutoRejectController` returns `List<TaskReportRejectWarningBO>` directly — no DTO conversion (unlike other controllers). Internal model exposed to frontend.
2. **Time window**: Only queries previous month relative to current approve period. Older auto-rejections become invisible to the warning endpoint.
3. **LocalStorage dismissal**: Hidden notification IDs stored in `hiddenAutoRejectWarnings` localStorage key. Clearing browser data resurfaces dismissed warnings.
4. **No confirmation page integration**: Auto-reject warnings are employee-facing (My Tasks). Managers on the Confirmation page get no indication that reports were auto-rejected in the closed period.

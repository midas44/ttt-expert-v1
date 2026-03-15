---
type: module
tags:
  - confirmation
  - approval
  - reports
  - workflow
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/ttt-report-service]]'
  - '[[modules/frontend-approve-module]]'
  - '[[architecture/security-patterns]]'
branch: release/2.1
---
# Report Confirmation Flow

The confirmation (approval) workflow for time reports. Governs how reported hours move through REPORTED → APPROVED/REJECTED states.

## Core Flow
1. **Employee reports** → POST /v1/reports (state=REPORTED, effort in minutes)
2. **Manager reviews** → GET /v1/reports/total (type=PROJECT or EMPLOYEE, grouped by week)
3. **Manager approves/rejects** → PATCH /v1/reports/{id} (state=APPROVED/REJECTED)
4. **Rejected reports** → Employee re-reports (PATCH state=REPORTED)
5. **Accountant verifies** → GET /v1/reports/accounting (paginated, by office+date range)
6. **Accountant sends reminders** → POST /v1/reports/accounting/notifications
7. **Period close** → PATCH /{officeId}/periods/approve (advances boundary)

## Period Model
- **Report period**: defines when employees can submit reports (per office, start date)
- **Approve period**: defines from when managers can approve (per office, start date)
- Both stored per office, controlled by accountant via PATCH endpoints
- Extended report period: individual employees can be given extra time (PUT /periods/report/employees/{login})

### Period Controller Permissions
| Action | Permission | API Token |
|--------|-----------|-----------|
| GET report/approve period | OFFICES_VIEW | Yes |
| GET min/max periods | AUTHENTICATED_USER | No |
| PATCH report period (close/reopen) | AUTHENTICATED_USER | No |
| PATCH approve period (close) | AUTHENTICATED_USER | No |

Key insight: period management (closing) is AUTHENTICATED_USER only — accountant action via JWT only.

## Warning System
Three types of warnings, all AUTHENTICATED_USER only (not accessible via API token):

1. **TaskReportWarningController** (/v1/task-report-warnings): shows reports exceeding limits
   - Warning types: DATE_EFFORT_OVER_LIMIT, EMPLOYEE_REPORT_DATE_EFFORT_OVER_LIMIT, REJECTED_REPORT_ON_CONFIRMATION_PERIOD_CLOSE
2. **TaskReportAutoRejectController** (/v1/task-auto-reject-warnings): lists reports auto-rejected on period close
   - Returns BO directly (code quality issue — no DTO conversion)
3. **EmployeeWarningController** (/v1/employees/current/warnings): current employee's warnings
4. **ProjectWarningController** (/v1/projects/{id}/warnings): project-level warnings

## Auto-Reject Behavior
When approve period closes (PATCH /periods/approve):
- Reports still in REPORTED state within closed period are auto-rejected
- Warnings are generated for affected employees
- Notification emails sent via scheduled job: `send-reject-notifications`

## Permission Matrix (TaskReportController)
| Endpoint | REPORTS_VIEW | REPORTS_EDIT | REPORTS_APPROVE | AUTHENTICATED_USER |
|----------|-------------|-------------|----------------|-------------------|
| GET /reports | ✓ | | | ✓ |
| POST /reports | | ✓ | | ✓ |
| PUT /reports (batch) | | ✓ | | ✓ |
| PATCH /{id} | | ✓ | ✓ | ✓ |
| PATCH /reports (batch) | | ✓ | ✓ | ✓ |
| DELETE /reports | | ✓ | ✓ | ✓ |
| GET /accounting | | | | ✓ only |
| POST /accounting/notifications | | | | ✓ only |
| GET /total | ✓ | | | ✓ |
| GET /summary | ✓ | | | ✓ |
| GET /over-reported | ✓ | | | ✓ |
| GET /effort | **none** | | | |
| GET /employee-projects | **none** | | | |

## Design Issues
- Self-approval: no executor≠approver check
- Direct create-as-approved: bypasses workflow entirely
- /effort and /employee-projects missing @PreAuthorize
- Auto-reject returns BO instead of DTO (leaks internal model)

## Related
- [[exploration/api-findings/report-crud-api-testing]] — API testing results
- [[modules/ttt-report-service]] — backend service
- [[modules/frontend-approve-module]] — frontend approve UI
- [[architecture/security-patterns]] — auth architecture

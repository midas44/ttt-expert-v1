---
type: analysis
tags:
  - reports
  - confirmation
  - periods
  - statistics
  - business-rules
  - phase-b-ready
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[analysis/vacation-business-rules-reference]]'
  - '[[analysis/role-permission-matrix]]'
  - '[[modules/ttt-report-confirmation-flow]]'
  - '[[modules/ttt-report-service]]'
branch: release/2.1
---
# Reports & Confirmation Business Rules Reference

Structured compilation of all report submission, confirmation, period management, and statistics business rules from 15+ vault notes, code analysis, API testing, and live UI exploration. Organized for Phase B test case generation.

## 1. Report Submission

### Data Model
- Entity: `task_report` in `ttt_backend` schema
- Key: unique (task_id, executor_login, report_date)
- Effort stored in **minutes** (bigint), displayed as hours (÷60)
- State enum: REPORTED, APPROVED, REJECTED (3-state machine)

### Create Rules
| Rule | Detail |
|------|--------|
| Effort minimum | ≥1 minute (validated) |
| Effort maximum | **No upper bound** — 1500 min (25h) accepted (BUG-REPORT-1) |
| Duplicate check | Same task+date+executor → 409 Conflict with `existentObject` |
| Closed period | reportDate before office report period start → 400 |
| Future date | **Accepted** — no forward-date restriction (BUG-REPORT-5) |
| Project state | Cannot report on FINISHED/CANCELED projects |
| Cross-employee | API token owner can report for any employee (BUG-REPORT-4) |
| Direct approve | POST with state=APPROVED accepted — bypasses workflow (BUG-REPORT-3) |
| Cell locking | LockService prevents concurrent cell edits (HTTP 423). Batch PUT skips locking. |
| Effort=0 | Setting effort to 0 **deletes** the report |

### Update Rules
- PATCH changes effort, comment, state
- Effort change always resets state to REPORTED (clears approver)
- Re-reporting from REJECTED: PATCH state=REPORTED → deletes `reject` record, clears approver

### Delete Rules
- DELETE by ids array → 204 No Content
- Requires REPORTS_EDIT or REPORTS_APPROVE permission

### Batch Operations
- PUT /v1/reports: batch create/replace (array of items)
- PATCH /v1/reports: batch patch (array of items, supports bulk approve/reject)

## 2. Confirmation (Approval) Flow

### State Machine
```
REPORTED ──→ APPROVED (manager approves)
    │
    └──→ REJECTED (manager rejects with optional comment)
              │
              └──→ REPORTED (employee re-reports / changes effort)
```

### Approve Rules
| Rule | Detail |
|------|--------|
| Permission | REPORTS_APPROVE (PROJECT_MANAGER, SENIOR_MANAGER, ADMIN on project) |
| Period check | reportDate must be ≥ approve period start |
| PROJECT_MANAGER type | Projects of type PROJECT_MANAGER cannot be approved |
| Self-approval | **No executor≠approver check** — self-approval possible (BUG-REPORT-2) |
| Batch | PATCH /v1/reports with items array → bulk state change |

### Reject Rules
| Rule | Detail |
|------|--------|
| Comment | Optional stateComment on rejection |
| Reject record | Creates row in `ttt_backend.reject` table (rejector, description, created_time, executor_notified) |
| Re-report | Employee changes effort → auto-resets to REPORTED, **deletes** reject record (no history) |
| API mapping | Response shows `approverLogin` for rejected reports, but DB `approver` is NULL — derived from `reject.rejector` |
| No GET by ID | GET /v1/reports/{id} returns 500 — must use list endpoint with filters |

### Reject Notification
- `executor_notified=false` on reject record creation
- Scheduler `sendRejectNotifications` runs every 5 minutes
- Sends APPROVE_REJECT email template to executor

### UI Confirmation Page (/approve)
- **Two tabs**: By employees, By projects
- **Filters**: Employee/Project dropdown, role filter, "Of other projects" checkbox, "With approved hours" toggle
- **Week navigation**: 6 week tabs, orange dot on tabs with pending items
- **Approve**: Per-task (all days in week) or bulk header button
- **Reject**: Opens tooltip with textarea (comment required in UI, optional in API)
- **Console error**: "employee is undefined" TypeError after approve click — non-blocking race condition
- **N+1 API pattern**: ~5N requests for N employees in "By projects" view
- **Auth polling**: 50+ GET /v1/authentication/check calls per session

## 3. Auto-Reject on Period Close

### Trigger
Accountant advances approve period: PATCH /{officeId}/periods/approve

### Flow
1. `TaskReportServiceImpl.rejectByOfficeId()` → `InternalTaskReportService.rejectNonApprovedTasks()`
2. Find all REPORTED-state reports in closing month
3. Create single shared `Reject` record with `description='auto.reject.state'`
4. Bulk update matching reports: state=REJECTED, reject FK set
5. Send email notifications per affected employee

### UI Display
- **Location**: My Tasks page (`/report`), NOT Confirmation page
- `AutoRejectedReportsContainer` renders error notifications at top of ReportPage
- Message: "Unconfirmed hours for task {taskName} were automatically rejected upon month closure"
- "Go to the report page" link navigates to rejection week
- Close button hides via localStorage (`hiddenAutoRejectWarnings`)
- **No data exists** on any testing environment — feature never triggered

### Design Issues
- BO leak: controller returns `TaskReportRejectWarningBO` directly (no DTO)
- Time window: only queries previous month — older auto-rejections invisible
- No Confirmation page integration for managers

## 4. Period Management

### Dual Period Model
| Period | Controls | Typical Value |
|--------|----------|---------------|
| REPORT | When employees can submit hours | 2026-03-01 |
| APPROVE | When managers can approve hours | 2026-02-01 |

Invariant: APPROVE period ≤ REPORT period (APPROVE always 1 month behind)

### Report Period Rules
| Rule | Detail |
|------|--------|
| First of month | Must be 1st day (validated: `getDayOfMonth() != 1` check) |
| Lower bound | Cannot precede approve period (strict `<`) |
| Upper bound | **No limit** — can jump forward any amount |
| Non-salary offices | GET returns computed default, PATCH returns 404 |

### Approve Period Rules
| Rule | Detail |
|------|--------|
| First of month | **NOT validated** — any day accepted (BUG: missing check at line 104) |
| Upper bound | Cannot exceed report period (strict `>`) |
| Lower bound | Cannot go back >2 months from today |
| Jump size | Maximum 1-month jump in either direction |
| Extended periods | Blocked if any employee has active extended period in office |
| Side effects | Advance → `PeriodChangedEvent` (auto-reject + vacation recalc). Revert → `PeriodReopenedEvent` |

### Extended Report Period
- Individual employee exceptions: PUT /v1/periods/report/employees/{login}
- Auto-cleaned by `ExtendedPeriodScheduler` every 5 minutes
- Blocks approve period advancement for the office

### Bugs Found
1. **Missing first-day-of-month validation on approve period** (HIGH)
2. **NPE on null start** (HIGH) — PATCH with `{}` → 500 NullPointerException
3. **Stack trace leakage** (MEDIUM) — invalid date format returns full Java trace
4. **Permission inconsistency** (MEDIUM) — report min/max requires JWT only; approve min/max accepts both

### Caching
- `@Cacheable` on `getPeriod()`, evicted per PATCH via `SimpleKey(officeId, periodType)`

## 5. Norm Calculation

### Personal (Individual) Norm
1. Clamp date range to employee work period
2. Fetch time-offs: vacations + sick leaves + day-offs + maternity
3. Merge overlapping off-periods
4. totalNorm = calendar working hours for office
5. personalNorm = max(0, totalNorm - offHours) in minutes

### Budget Norm
Same as personal norm **except**: administrative (unpaid) vacations excluded from off-periods. Employee on unpaid leave still counted in budget.

### Display Format (#3381)
- Has admin vacation: `{individual} ({budget})`
- No admin vacation: just `{budget}`

### Thresholds
- Forgotten report: 90% of personal norm
- Daily report limit: 36h (2160 minutes)
- Over/under-reporting: configurable ±M%/L% in TTT Parameters (default: over=10%, under=30%)

## 6. Statistics

### Statistic Report Table (Pre-computed Cache)
- Table: `ttt_backend.statistic_report`
- Key: unique (employee_login, report_date)
- Fields: reported_effort (decimal hours), month_norm (minutes), budget_norm (minutes), comment

### Three Update Paths
| Path | Trigger | Scope |
|------|---------|-------|
| Nightly sync | Cron 4:00 AM | Current + previous month, all employees |
| Task report event | @Async after commit | Single employee/month |
| RabbitMQ | Vacation/sick leave change | Batch (INITIAL_SYNC, VACATION_CHANGES, SICK_LEAVE_CHANGES) |

### Deviation Formula
`excess = (reported - budgetNorm) / budgetNorm × 100%`
- ExcessStatus: HIGH (>0%), LOW (<0%), NEUTRAL (==0%), NA (budgetNorm=0)
- Display: integer except (-1,+1) range → 1 decimal. NA → "+N/A%" (sorts to top)

### Employee Reports Page Access
| Role | Scope |
|------|-------|
| ADMIN, CHIEF_ACCOUNTANT | All employees |
| OFFICE_DIRECTOR, ACCOUNTANT | Their office |
| DEPARTMENT_MANAGER, TECH_LEAD | Subordinates |
| EMPLOYEE | Cannot access |

### Over/Under-Reporting Banner (Confirmation Page)
- Non-dismissible banner visible to ADMIN, PM, SPM
- Triggers: over-reporting exists today (current month) OR existed at month end (past month) OR under-reporting at month end
- Employee names highlighted: red=over, purple=under
- Clock icon with tooltip: deviation %, month, DM, projects with PM names

### Design Issues
1. Race condition: no pessimistic locking between MQ and task report event paths
2. budgetNorm null fallback to monthNorm
3. 2-month sync only — no historical back-fill
4. Hardcoded CEO login: `CEO_LOGIN = "ilnitsky"`
5. Legacy over-report endpoint: N+1 pattern, superseded by cache table

## 7. Scheduled Jobs (Reports Domain)

| Job | Schedule | Action |
|-----|----------|--------|
| sendReportsChangedNotifications | Daily 07:50 | Notify employees when manager reported on their behalf |
| sendReportsForgottenNotifications | Mon/Fri 16:00 | Under-reported employees (<90% norm) |
| sendReportsForgottenDelayedNotifications | Daily 16:30 | Retry deferred forgotten notifications |
| sendRejectNotifications | Every 5 min | Notify executors of rejected reports |
| ExtendedPeriodScheduler.cleanUp | Every 5 min | Remove expired extended periods |
| StatisticReportScheduler | Nightly 4:00 AM | Sync statistic_report for current+previous month |

## 8. Permission Matrix (Report Endpoints)

| Endpoint | REPORTS_VIEW | REPORTS_EDIT | REPORTS_APPROVE | AUTH_USER only | No auth |
|----------|:-----------:|:-----------:|:--------------:|:------------:|:-------:|
| GET /reports | ✓ | | | ✓ | |
| POST /reports | | ✓ | | ✓ | |
| PUT /reports (batch) | | ✓ | | ✓ | |
| PATCH /{id} | | ✓ | ✓ | ✓ | |
| PATCH /reports (batch) | | ✓ | ✓ | ✓ | |
| DELETE /reports | | ✓ | ✓ | ✓ | |
| GET /accounting | | | | ✓ only | |
| POST /accounting/notifications | | | | ✓ only | |
| GET /total | ✓ | | | ✓ | |
| GET /summary | ✓ | | | ✓ | |
| GET /over-reported | ✓ | | | ✓ | |
| GET /effort | | | | | ✓ (BUG) |
| GET /employee-projects | | | | | ✓ (BUG) |

## 9. Known Bugs Summary

| ID | Severity | Description | Source |
|----|----------|-------------|--------|
| BUG-REPORT-1 | HIGH | No upper bound on effort (25h accepted) | API testing S8 |
| BUG-REPORT-2 | HIGH | Self-approval via API | API testing S8 |
| BUG-REPORT-3 | HIGH | Direct create-as-APPROVED bypasses workflow | API testing S8 |
| BUG-REPORT-4 | MEDIUM | Cross-employee reporting (any employee) | API testing S8 |
| BUG-REPORT-5 | MEDIUM | Future date accepted without restriction | API testing S8 |
| BUG-REPORT-6 | LOW | Missing @PreAuthorize on /effort and /employee-projects | API testing S8 |
| BUG-PERIOD-1 | HIGH | Missing first-day validation on approve period | Period testing S13 |
| BUG-PERIOD-2 | HIGH | NPE on null start in PATCH body | Period testing S13 |
| BUG-PERIOD-3 | MEDIUM | Stack trace leakage on invalid date format | Period testing S13 |
| BUG-PERIOD-4 | MEDIUM | Permission inconsistency (report vs approve min/max) | Period testing S13 |
| BUG-CONFIRM-1 | LOW | "employee is undefined" JS error after approve | UI testing S12 |
| BUG-CONFIRM-2 | MEDIUM | Reject email not sent (timing/date filtering issue) | E2E testing S17 |
| BUG-CONFIRM-3 | LOW | APPROVE permission appears/disappears between PATCH and GET | E2E testing S17 |
| BUG-STATS-1 | MEDIUM | Race condition between MQ and task report event paths | Code analysis S20 |

## 10. Related Vault Notes

- [[exploration/api-findings/report-crud-api-testing]] — API testing results
- [[modules/ttt-report-confirmation-flow]] — confirmation flow details
- [[exploration/ui-flows/confirmation-flow-live-testing]] — UI testing
- [[modules/auto-reject-report-flow]] — auto-reject behavior
- [[exploration/api-findings/reject-with-comment-e2e]] — reject e2e
- [[exploration/api-findings/period-api-live-testing]] — period testing
- [[modules/ttt-report-service]] — backend service
- [[modules/frontend-report-module]] — frontend report module
- [[modules/frontend-approve-module]] — frontend approve module
- [[modules/statistics-service-implementation]] — statistics service
- [[investigations/rabbitmq-statistic-report-sync]] — MQ sync flow
- [[external/requirements/REQ-confirmation]] — requirements
- [[external/requirements/REQ-statistics]] — statistics requirements
- [[analysis/role-permission-matrix]] — permission matrix
- [[analysis/office-period-model]] — period model

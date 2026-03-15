---
type: module
tags:
  - backend
  - ttt-service
  - reports
  - confirmation
  - periods
  - approval
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[architecture/api-surface]]'
  - '[[modules/ttt-service]]'
  - '[[analysis/office-period-model]]'
branch: release/2.1
---
# TTT Report Service — Submission, Confirmation, Period Management

## Report Submission

**Controller**: `TaskReportController` at `/v1/reports`. POST (create), PUT (batch upsert), PATCH (update), DELETE (batch).

**Service chain**: TaskReportController → TaskReportServiceImpl (orchestrator) → InternalTaskReportService (DB operations) → TaskReportRepository.

**State machine**: 3 states — REPORTED → APPROVED (via manager) or REJECTED. Effort change always resets to REPORTED. Setting effort to 0 deletes the report.

**Key business rules**:
- One report per (task, executor, report_date) — unique constraint
- Cannot create reports for FINISHED/CANCELED projects
- Cell-level locking via LockService (HTTP 423 if held). Batch PUT skips locking.
- Effort stored in **minutes** (bigint)
- Reporter ≠ executor allowed (managers report on behalf of employees)

## Confirmation Workflow

**Approval**: Manager PATCH with state=APPROVED. Requires `APPROVE` permission (MANAGER/SENIOR_MANAGER/ADMIN on project). Report date must be ≥ approve period start. PROJECT_MANAGER type projects cannot be approved.

**Rejection**: Manager PATCH with state=REJECTED + optional comment. Creates `Reject` entity with `executor_notified=false`. Reject notification sent within 5 minutes by scheduler.

**Auto-reject on period close**: When approve period advances, all REPORTED-state reports in the closing month get bulk REJECTED with `AUTO_REJECT_STATE` description. Single shared Reject entity for the batch.

**Re-reporting**: Effort change on rejected report → auto-reset to REPORTED, Reject entity deleted, approver cleared.

## Period Management

**Dual periods per office**: REPORT (employee submission boundary) and APPROVE (manager confirmation boundary). Report period ≥ Approve period always.

| Endpoint | Description |
|----------|-------------|
| GET/PATCH `/v1/offices/{id}/periods/report` | Office report period |
| GET/PATCH `/v1/offices/{id}/periods/approve` | Office approve period |

**Approve period constraints**: Cannot move >1 month at once, cannot go before today-2months, blocked if any employee has extended period.

**Employee extended period**: Individual exceptions via PUT `/v1/periods/report/employees/{login}`. Auto-cleaned by `ExtendedPeriodScheduler` every 5 min.

## Norm Calculation

Personal norm = calendar norm - off hours (vacations + sick leaves + maternity, clamped ≥ 0).
Budget norm = personal norm excluding administrative (unpaid) vacations.
Forgotten report threshold: 90% of personal norm.
Daily report limit: 36h (2160 minutes).

## Scheduled Tasks (5)

| Job | Schedule | Action |
|-----|----------|--------|
| sendReportsChangedNotifications | Daily 07:50 | Notify employees when manager reported on their behalf |
| sendReportsForgottenNotifications | Mon/Fri 16:00 | Under-reported employees (<90% norm) |
| sendReportsForgottenDelayedNotifications | Daily 16:30 | Retry deferred forgotten notifications |
| sendRejectNotifications | Every 5 min | Notify executors of rejected reports |
| ExtendedPeriodScheduler.cleanUp | Every 5 min | Remove expired extended periods |

## Async Event Side Effects

TaskReportEventListener (async + transactional): On add/patch/delete → update task lastReportedTime, project firstReportDate, sync statistic_report effort, manage vacation employee-project cache.

See also: [[architecture/api-surface]], [[exploration/data-findings/ttt-backend-schema-deep-dive]], [[analysis/office-period-model]], [[modules/ttt-service]]

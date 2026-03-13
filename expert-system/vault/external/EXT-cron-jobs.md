---
type: external
tags:
  - cron
  - scheduling
  - background-jobs
  - notifications
  - code-verified
created: '2026-03-12'
updated: '2026-03-13'
status: active
related:
  - '[[architecture/system-overview]]'
  - '[[modules/ttt-service]]'
  - '[[modules/vacation-service]]'
  - '[[modules/email-service]]'
  - '[[patterns/feature-toggles-unleash]]'
branch: release/2.1
---
# Cron Jobs Inventory

**Source**: Confluence 32904541 + code verification (release/2.1) | All run on Asia/Novosibirsk (GMT+7) | **21 active jobs** across 4 services.

## TTT Backend (9 active jobs)

| Scheduler | Lock Name | Cron | Purpose |
|---|---|---|---|
| `TaskReportNotificationScheduler` | `sendReportsChangedNotifications` | config | Manager-changed report notifications |
| `TaskReportNotificationScheduler` | `sendReportsForgottenNotifications` | config | Unreported hours reminder |
| `TaskReportNotificationScheduler` | `sendReportsForgottenDelayedNotifications` | config | Delayed unreported hours |
| `TaskReportNotificationScheduler` | `sendRejectNotifications` | config | Rejected hours notifications |
| `BudgetNotificationScheduler` | `sendBudgetNotifications` | config | Budget exceeded notifications |
| `CSSyncScheduler` | `doCsSynchronization` | config | CompanyStaff partial sync |
| `PmToolSyncScheduler` | `doPmToolSynchronization` | config | PM Tool project sync |
| `StatisticReportScheduler` | `sync` | config | Periodic statistic report sync |
| `ExtendedPeriodScheduler` | `cleanUp` | config | Extended period cleanup |
| `LockServiceImpl` | `cleanUpCache` | `*/10 * * * * *` | **Stale lock cleanup (every 10 sec!)** |

Note: `CSFullSyncScheduler` is **commented out** — disabled.

## Vacation Service (8 active jobs)

| Scheduler | Lock Name | Cron | Purpose |
|---|---|---|---|
| `CSSyncScheduler` | `sync` | config | CompanyStaff sync |
| `EmployeeProjectsSyncScheduler` | `sync` | config | Employee-project sync |
| `DigestScheduler` | `sendDigests` | config | Vacation digest emails |
| `AnnualProductionCalendarTask` | `runFirst` | config | Annual calendar reminder |
| `AnnualAccrualsTask` | `run` | config | New Year vacation day accrual |
| `AutomaticallyPayApprovedTask` | `CloseOutdatedTask.run` | config | Auto-pay approved vacations |
| `AvailabilityScheduleNotificationScheduler` | **NONE** | config | Availability notifications |
| `VacationStatusUpdateJob` | **NONE** | `0 */10 * * * *` + `0 */5 * * * *` | Status updates (2 schedules!) |

Note: `CSFullSyncScheduler` is **commented out**.

## Calendar Service (1 active job)

| Scheduler | Lock Name | Cron | Purpose |
|---|---|---|---|
| `CSSyncScheduler` | `doCsSynchronization` | config | CompanyStaff sync |

Note: `CSFullSyncScheduler` is **commented out**.

## Email Service (2 active jobs)

| Scheduler | Lock Name | Cron | Purpose |
|---|---|---|---|
| `EmailSendScheduler` | `sendEmails` | config | Send queued emails |
| `EmailPruneScheduler` | `pruneEmails` | config | Prune old emails |

## Issues Found (Code Verification)

1. **Missing @SchedulerLock** on `AvailabilityScheduleNotificationScheduler` — could fire duplicate notifications in clustered deployment
2. **Missing @SchedulerLock** on `VacationStatusUpdateJob` — two schedules (5min + 10min), CONFIRMED bug #2 from Session 5
3. **Misleading lock name**: `AutomaticallyPayApprovedTask` uses lock name "CloseOutdatedTask.run" — legacy naming, confusing
4. **Aggressive frequency**: `LockServiceImpl.cleanUpCache` runs every 10 seconds — performance concern
5. **CSFullSyncScheduler disabled** in all 3 services — suggests it caused problems (only partial sync active)

## Testing Endpoints

All jobs have test endpoints under `/api/{service}/v1/test/...` for manual triggering via Swagger.

## Related
- [[architecture/system-overview]]
- [[modules/ttt-service]]
- [[modules/vacation-service]]
- [[modules/email-service]]
- [[patterns/feature-toggles-unleash]] (CS_SYNC and PM_TOOL_SYNC toggles gate sync schedulers)

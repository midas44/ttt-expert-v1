---
type: exploration
tags:
  - cron
  - scheduling
  - shedlock
  - live-testing
  - verification
created: '2026-03-13'
updated: '2026-03-13'
status: active
branch: release/2.1
related:
  - '[[EXT-cron-jobs]]'
  - '[[email-notification-triggers]]'
  - '[[feature-toggles-unleash]]'
  - '[[companystaff-integration]]'
---

# Cron Job Live Verification

Verified all 21 cataloged cron jobs against ShedLock tables on timemachine and stage. Cross-referenced with codebase cron expressions (application.yml) and DB timestamps.

## Verification Method

Queried `shedlock` table in all 4 schemas (ttt_backend, ttt_vacation, ttt_calendar, ttt_email) on both timemachine and stage. ShedLock records `locked_at` timestamp for every execution — provides execution history.

## All Active Jobs Confirmed Running

**TTT Backend** (10 active, all ShedLock-verified on TM + Stage):
| Scheduler | Cron (NSK) | Last TM locked_at (UTC) | Stage Match |
|---|---|---|---|
| LockServiceImpl.cleanUpCache | */10s (hardcoded) | 16:39 | ✓ |
| sendRejectNotifications | */5min | 16:35 | ✓ |
| ExtendedPeriodScheduler.cleanUp | */5min | 16:35 | ✓ |
| BudgetNotificationScheduler | */30min | 16:30 | ✓ |
| CSSyncScheduler | */15min | 16:30 | ✓ |
| PmToolSyncScheduler | */15min | 16:30 | **NOT on Stage** |
| sendReportsForgottenDelayed | daily 16:30 NSK | 09:30 | ✓ |
| sendReportsForgotten | MON/FRI 16:00 NSK | 09:00 | ✓ |
| sendReportsChanged | daily 07:50 NSK | 00:50 | ✓ |
| StatisticReportScheduler | daily 04:00 NSK | 21:00 (prev day) | via 7-day window |

**Vacation Service** (7 active, 5 ShedLock-verified, 2 without ShedLock):
| Scheduler | Cron (NSK) | Last TM locked_at (UTC) | ShedLock |
|---|---|---|---|
| CSSyncScheduler | */15min | 16:30 | ✓ |
| DigestScheduler | daily 08:00 NSK | 01:00 | ✓ |
| EmployeeProjectsSyncScheduler | daily 03:00 NSK | 20:00 (prev day) | ✓ |
| AutomaticallyPayApprovedTask | daily 00:00 NSK | 17:00 (prev day) | ✓ (as "CloseOutdatedTask.run") |
| AnnualAccrualsTask | Jan 1 00:00 NSK | 2025-12-31 17:00 | ✓ |
| AnnualProductionCalendarTask | Nov 1 00:01 NSK | 2025-10-31 17:01 | ✓ |
| VacationStatusUpdateJob (×2) | */10min + */5min | **NO ENTRY** | ❌ Missing |
| AvailabilityScheduleNotif | daily 14:00 NSK | **NO ENTRY** | ❌ Missing |

**Calendar Service** (1 active): CSSyncScheduler */15min ✓
**Email Service** (2 active): EmailSendScheduler */20s ✓, EmailPruneScheduler daily ✓

## Key Findings

### 1. PmToolSyncScheduler Missing on Stage
Active on timemachine but NOT in stage's last-24h ShedLock. Likely disabled via [[feature-toggles-unleash|Unleash]] `PM_TOOL_SYNC` toggle on stage environment.

### 2. Legacy ShedLock Cruft (12+ stale entries)
ShedLock never cleans up rows for removed/renamed schedulers:
- `CompanyStaffScheduler.doCsSynchronization` (2023) → renamed to CSSyncScheduler
- `CSSyncLauncher.sync` (2024) → renamed
- `CSFullSyncScheduler` (2024) → disabled across all 3 services
- `VacationNotificationScheduler.sendVacationNotifications` (2025-04) → removed
- `PreliminaryExpiredRequestTask.run` (2024-11) → removed
- `EmployeeSyncTask.syncEmployees` (2023) → renamed
- `AnnualProductionCalendarTask.runLast` (2022) → removed
- `TimelineEventHandler.handle` (2022) → removed
No operational impact but adds DB clutter. Could cause confusion during debugging.

### 3. Config Cruft in application.yml
`preliminary-outdated.cron` and `close-outdated.cron` entries exist in vacation's `application.yml` (lines 95-101) but `PreliminaryExpiredRequestTask` and the original `CloseOutdatedTask` classes have been removed/renamed. Dead configuration.

### 4. INVALID Email Accumulation (85 on TM)
All "Invalid Addresses" errors for @noveogroup.com addresses — likely former employees whose mailboxes were deactivated. Subject: reports-forgotten notifications. No cleanup or address-validation mechanism before send. Emails remain in INVALID status indefinitely (until EmailPruneScheduler prunes after 30 days).

### 5. Timezone Verification
- JVM timezone: Asia/Novosibirsk (UTC+7)
- PostgreSQL timezone: UTC
- All cron expressions fire in NSK, stored as UTC in ShedLock — verified consistent across all jobs

### 6. Single-Instance Deployment Confirmed
Same `locked_by` value per service across all entries (TM: `142311e083f8`, Stage: `8abe76719968`). No clustering. Makes missing ShedLock on VacationStatusUpdateJob/AvailabilityScheduleNotificationScheduler low-risk in practice but still a code defect.

### 7. Profile-Specific Overrides
`application-preprod.yml` overrides two schedules: budget notifications (*/5min vs */30min) and CS sync (*/5min vs */15min). All other schedules use base `application.yml` values.

## Email Activity Pattern (TM, last 24h)
| Hour (UTC) | Sent Count | Likely Source |
|---|---|---|
| 00:50 | included in 01h | sendReportsChanged |
| 01:00 | (digest) | DigestScheduler |
| 04:00 | 1 | Event-driven |
| 08:00 | 14 | Event-driven |
| 11:00 | 6 | Event-driven |
| 14:00 | 7 | AvailabilitySchedule (14:00 UTC = 21:00 NSK) |
| 16:00 | 287 | Reports-forgotten batch |
| 22:00 | 1 | Calendar conflict test (session 14) |

## Related
- [[EXT-cron-jobs]] — original inventory from Confluence + code
- [[email-notification-triggers]] — email pipeline architecture
- [[feature-toggles-unleash]] — PM_TOOL_SYNC and CS_SYNC toggles
- [[companystaff-integration]] — CS sync across 3 services
- [[rabbitmq-messaging]] — notification queue processing

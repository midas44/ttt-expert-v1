---
type: module
tags:
  - pm-tool
  - sync
  - feign
  - rate-limiting
  - validation
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[ttt-service]]'
  - '[[EXT-cron-jobs]]'
  - '[[database-schema]]'
  - '[[backend-architecture]]'
branch: release/2.1
---

# PM Tool Sync Implementation

## Architecture

Feign client (`PmToolClient`) calls PM Tool REST API (`/api/v2/projects`) with token auth. Sync runs every 15 minutes via `PmToolSyncScheduler` with ShedLock. Orchestrated by `PmToolEntitySyncLauncher`.

**Rate limiting**: Guava `RateLimiter` at 50 fetches/minute (configurable via `pmTool.sync.fetch-rate-per-minute`). Page size: 100 items. Thread pool: 4 workers (`pmToolSyncPool`).

## Root Cause: Project Count Mismatch

PM Tool reports ~3132 projects but only ~501 sync to TTT. The validation cascade in `PmToolProjectSynchronizer.validateEmployeesExist()` throws `IllegalStateException` for any project where the owner, supervisor, PM, or **any watcher** is missing from the employee database.

**Why employees are missing**: Company Staff sync runs independently. If an employee referenced by PM Tool hasn't been synced yet (or was removed/deactivated in CS), all their projects fail validation.

**Sales filtering compounds the issue**: `removeSalesFromProject()` nullifies employee references marked as "sales" type. If a critical role (owner/PM) is sales-typed, the reference becomes null, potentially triggering validation failure.

## Failed Project Retry

Failed projects tracked in `pm_tool_sync_failed_entity` table. Retried in batches of 10 (configurable via `pmTool.sync.retry-batch-size`). Each retry attempt re-runs validation — if the missing employee still isn't in DB, it fails again indefinitely.

**Bug**: No max retry limit or exponential backoff on failed projects. A project with a permanently missing employee reference will retry every 15 minutes forever, generating log noise.

## Error Handling

Per-project isolation via `Future.get(10s timeout)`:
- `TimeoutException` → cancel task, mark failed
- Any other `Exception` → mark failed
- Success → remove from failed tracking

No dead-letter queue or alerting for persistently failing projects.

## Key Files

- Client: `common/common-client/pmtool-client/.../PmToolClient.java`
- Scheduler: `ttt/service/service-impl/.../PmToolSyncScheduler.java`
- Launcher: `ttt/service/service-impl/.../PmToolEntitySyncLauncher.java`
- Synchronizer: `ttt/service/service-impl/.../PmToolProjectSynchronizer.java`
- Failed repo: `ttt/db/db-impl/.../PmToolSyncFailedProjectRepositoryImpl.java`

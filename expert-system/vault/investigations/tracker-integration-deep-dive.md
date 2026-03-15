---
type: investigation
tags:
  - tracker
  - integration
  - jira
  - gitlab
  - graalvm
  - sandbox
  - worklog
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[modules/ttt-service]]'
  - '[[external/EXT-tracker-integration]]'
  - '[[modules/pm-tool-sync-implementation]]'
branch: release/2.1
---

# Tracker Integration Deep Dive

Comprehensive analysis of the tracker integration subsystem — code architecture, database patterns, API surface, and live data.

## Architecture

Eight tracker types via `EmployeeTrackerCredentialsType` enum: GITLAB, REDMINE, JIRA_TOKEN, JIRA_LOGPASS, ASANA, CLICK_UP, PRESALES, YOU_TRACK. Each implemented as a separate Maven module under `ttt/tracker-client/`.

**Core flow**: REST Controller → Service → TrackerClientFactory → concrete TrackerClient → External API

### Key Classes
- **TrackerClientFactory** — factory switch on credential type → 7 concrete clients (Asana listed but not implemented)
- **IssueTrackerService** — high-level operations: getTaskFromTracker(), credential resolution with fallback chain
- **CustomScriptService** — GraalVM JavaScript sandbox for project-specific task mapping
- **ProjectTrackerWorkLogServiceImpl** — work log sync coordination via Command pattern (SendToTrackerCommand / LoadFromTrackerCommand)
- **TrackerSyncStartEvent / TrackerSyncFinishEvent** — Spring events for sync lifecycle

### TrackerClient Interface
- `getCurrentUser()` — connectivity validation
- `getTicketInfo(ticketUrl)` — fetch external ticket data
- `supportsWorkLog()` — capability check
- `updateWorkLog(request)` — push work log
- `searchReports(request)` — search reports in tracker

### Credential Resolution
Per-employee credentials stored encrypted in `employee_tracker_credentials`. Resolution: current user → project manager → project owner (read-only fallback).

## Custom Scripting (GraalVM Sandbox)

Projects can define custom JavaScript for task mapping:
- `taskNameScript` — transform ticket info → task name
- `boundEmployeeScript` — extract employee login from ticket
- `workLogScript` — map work log data

**Security**: Scripts wrapped with `beforeScript.js` that blocks loops (while/for/do/goto), Java reflection, host access. Error codes: ILLEGAL_OPERATOR_ERROR, ILLEGAL_FUNCTION_CALL_ERROR, ILLEGAL_JAVA_CALL_ERROR.

## API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/v1/employees/current/settings/trackers` | GET | Search employee credentials |
| `/v1/employees/current/settings/trackers` | POST | Create (validates via getCurrentUser()) |
| `/v1/employees/current/settings/trackers` | PATCH | Update credentials |
| `/v1/employees/current/settings/trackers` | DELETE | Remove credentials |
| `/v1/projects/{id}/tracker-work-log/info` | GET | Sync status |
| `/v1/projects/{id}/tracker-work-log/sync` | POST | Trigger sync (TTT→tracker or tracker→TTT) |

**Error codes**: TRACKER_NOT_CONFIGURED, TRACKER_NOT_AVAILABLE, TRACKER_NOT_AUTHORIZED, TRACKER_NOT_PERMITTED, TRACKER_HTTPS_REQUIRED, TRACKER_NOT_SUPPORTED, PROXY_NOT_AVAILABLE, TRACKER_UNKNOWN, TRACKER_RESOURCE_NAME.

## Database (timemachine)

### tracker_work_log
- **222K rows**, 41K unique tasks, 157 unique employees
- Date range: 2021-04-02 to 2026-03-05
- Fields: id, task, employee, date, tracker_work_log_id (external), effort, remaining_estimate, comment
- Indexes on date, employee, task

### employee_tracker_credentials
- **19 credentials** for 14 unique employees
- Distribution: GITLAB (7), JIRA_LOGPASS (5), REDMINE (2), CLICK_UP (2), JIRA_TOKEN (2), PRESALES (1)
- **No ASANA or YOU_TRACK** credentials exist (unused tracker types)
- Fields: id, employee, tracker_url, type, auth_type, credentials (encrypted)

## Sync Scheduler

**PmToolSyncScheduler** — configurable cron (`pmTool.sync.cron`), ShedLock-protected, calls PmToolSyncService.sync(false) for incremental sync. Metrics via Micrometer `@Timed`.

## Design Issues

1. **Asana listed but not implemented** — enum value exists but Confluence marks "NOT supported"
2. **Encrypted credentials** — stored in DB, but encryption key management not visible
3. **Low adoption** — only 14 employees have configured tracker credentials out of ~400 active
4. **GraalVM sandbox bypasses** — loop prevention via string matching (not AST), potentially fragile

## Test Implications

- Tracker connectivity mocking needed (external APIs)
- Script sandbox security tests (loop prevention, Java interop blocking)
- Work log sync bidirectional: TTT→tracker and tracker→TTT
- Error handling for all 9 error codes
- Credential CRUD with connectivity validation
- Multi-tracker per employee scenarios
- Fallback chain for credential resolution

## Related
- [[modules/ttt-service]]
- [[architecture/system-overview]]
- [[external/EXT-tracker-integration]]
- [[modules/pm-tool-sync-implementation]]
- [[exploration/ui-flows/admin-projects-deep-exploration]]

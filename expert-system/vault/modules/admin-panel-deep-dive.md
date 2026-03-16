---
type: module
tags:
  - admin
  - project-management
  - employee
  - calendar
  - pmtool-sync
  - deep-dive
  - sprint-15
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[accounting-service-deep-dive]]'
  - '[[vacation-service-deep-dive]]'
  - '[[production-calendar-management]]'
branch: release/2.1
---
# Admin Panel Deep Dive

Deep code-level investigation of admin functionality: project CRUD, employee management, PM Tool sync, and production calendar CRUD.

## 1. Project Management

### ProjectController (`/v1/projects`)

| Endpoint | Method | Authority | Purpose |
|----------|--------|-----------|---------|
| `/{projectId}` | GET | PROJECTS_ALL or AUTHENTICATED_USER | Find project by ID |
| `/` | GET | PROJECTS_ALL or AUTHENTICATED_USER | Search with filters |
| `/managers` | POST | PROJECTS_ALL or AUTHENTICATED_USER | Find managers with active projects |
| `/{projectId}` | PATCH | PROJECTS_ALL or AUTHENTICATED_USER | Patch project |
| `/{projectId}` | DELETE | PROJECTS_ALL or AUTHENTICATED_USER | Delete project |
| `/models` | GET | (none) | List project models enum |
| `/types` | GET | (none) | List project types enum |
| `/statuses` | GET | (none) | List project statuses enum |

**Validators**: `@ProjectIdExists` on projectId path variable.

**AlreadyExistsException handling**: PATCH catches `AlreadyExistsException`, converts existing object to DTO and re-throws — returns the conflicting project in error response.

### ProjectServiceImpl

```java
// find() — validates PROJECTS VIEW permission
public ProjectBO find(Long id) {
    permissionService.validate(PermissionClassType.PROJECTS, PermissionClassActionType.VIEW);
    ProjectBO project = internalProjectService.find(id);
    return fillPermissions(fillReportInfo(project));
}

// fillReportInfo() — enriches with report data
projectCopy.setLastReportDate(taskReportService.findLastReportDateForProject(id));
projectCopy.setTotalEffort(taskReportService.getTotalEffortForProject(id));

// delete() — validates DELETE permission
public void delete(long projectId) {
    ProjectBO project = internalProjectService.find(projectId);
    ProjectBO projectWithPermissions = fillPermissions(project);
    projectPermissionService.validate(projectWithPermissions, ProjectPermissionType.DELETE);
    internalProjectService.delete(projectId);
}
```

**Permission model**: Class-level (PROJECTS VIEW) + object-level (ProjectPermissionService for DELETE).

**Design issue**: Controller uses AUTHENTICATED_USER for all operations including DELETE — service-level guards are the real security boundary.

### Project Search

`ProjectSearchRequestDTO` supports filters:
- `managersLogins` — filter by manager
- `seniorManagersLogins` — filter by senior manager
- `ownerLogin` — filter by owner
- `employeeLogins` — filter by role-based membership (MANAGER, SENIOR_MANAGER, OWNER, MEMBER, OBSERVER)

Keyboard layout auto-correction via `SuggestionMappingUtil.correctLayout`.

## 2. Employee Management

### EmployeeController (`/v1/employees`)

| Endpoint | Method | Authority | Purpose |
|----------|--------|-----------|---------|
| `/` | GET | EMPLOYEES_VIEW or AUTHENTICATED_USER | Search employees |
| `/current` | GET | EMPLOYEES_VIEW or AUTHENTICATED_USER | Current logged-in employee |
| `/{login}/work-periods` | GET | EMPLOYEES_VIEW or AUTHENTICATED_USER | Work periods for employee |
| `/{login}` | GET | EMPLOYEES_VIEW or AUTHENTICATED_USER | Get by login |
| `/{login}/roles` | GET | EMPLOYEES_VIEW or AUTHENTICATED_USER | Get employee roles |
| `/{login}` | PATCH | (none — no @PreAuthorize!) | Patch employee |

**Validators**: `@EmployeeLoginExists` on login path variable.

**No create/delete**: Employees are imported from CompanyStaff sync — TTT only patches existing employees.

**Design issue**: `PATCH /{login}` has no `@PreAuthorize` annotation — relying entirely on service-level security. All other endpoints have explicit annotations. This is inconsistent.

**Employee Search** (`EmployeeSearchRequestDTO`):
- Uses `searchSecured()` — applies role-based visibility filters
- `PageableUtil.correct()` normalizes pagination parameters

## 3. PM Tool Synchronization

### Architecture

```
PmToolSyncScheduler (cron)
  → PmToolSyncLauncher.sync(false)  // incremental sync
    → PmToolSyncService.sync(fullSync=false)
      → PmToolEntitySyncLauncher.sync(projectSynchronizer, PAGE_SIZE=100, fullSync)
        → Paginated fetch with rate limiter
        → Async execution pool (per entity)
        → Failed entity retry with batching
```

### PmToolSyncScheduler

```java
@Scheduled(cron = "${pmTool.sync.cron}", zone = TimeUtils.DEFAULT_ZONE_NAME)
@SchedulerLock(name = "PmToolSyncScheduler.doPmToolSynchronization")
public void doPmToolSynchronization() {
    pmToolSyncLauncher.sync(false); // incremental
}
```

### PmToolEntitySyncLauncher — Sync Engine

**Configuration**:
- `${pmTool.sync.retry-batch-size:10}` — retry batch size (default 10)
- `${pmTool.sync.fetch-rate-per-minute:50}` — rate limit (default 50 req/min)
- `TIMEOUT = 10000` ms — per-entity sync timeout
- Uses `RateLimiter` (Guava) for API call throttling

**Incremental vs Full sync**:
- Incremental: `updatedAfter = lastSucceeded.toLocalDate()` — only changed since last sync
- Full: no date filter — syncs everything

**Failed entity handling**:
1. On timeout/error: entity ID saved to `PmToolSyncFailedProjectRepository`
2. After main sync: retry failed IDs in configurable batches
3. On success: remove from failed repository
4. Status tracking in `PmToolSyncStatusRepository`

**Post-processing**: `entitySynchronizer.postProcess()` called if any entities synced.

### PmToolProjectSynchronizer

Maps PM Tool projects to TTT `Project` entities.

**Field mapping**:
- `pmToolId` → source identifier
- `name` / `accountingName` ← both set to PM Tool project name
- `customer` ← `customerName`
- `model` ← parsed via `parseProjectModel()`
- `type` ← `ProjectType.valueOf(upperCase(typeId))`
- `status` ← `ProjectStatus.valueOf(upperCase(statusId))`, except `"draft"` → `ACTIVE`
- `country` ← `countryId`
- `preSalesIds` ← presales ticket IDs joined with ","
- `pmtId` ← PM Tool tracker ID
- Owner/PM/Supervisor ← looked up by CompanyStaff ID

**Sales filtering**: `removeSalesFromProject()` — removes all sales-type references from PM, owner, supervisor, and watchers before processing. Sales employees exist in PM Tool but not in TTT.

**Validation**: `validateEmployeesExist()` — all employee CS IDs must exist in TTT. Throws `IllegalStateException` with details if missing.

**Design issue**: Throws `IllegalStateException` for missing employees — not a proper business exception, will cause HTTP 500 instead of a meaningful error.

**Observer sync**: After project save, batch-syncs watchers via `InternalProjectObserverService.batchChangeObservers()`.

**Cache eviction**: `projectService.evictFromCache()` after each project sync.

## 4. Production Calendar CRUD

### CalendarControllerV2 (`/v2/calendars`)

| Endpoint | Method | Authority | Purpose |
|----------|--------|-----------|---------|
| `/` | GET | CALENDAR_VIEW | List calendars (paginated) |
| `/` | POST | ADMIN or CHIEF_ACCOUNTANT | Create calendar |
| `/{calendarId}` | PATCH | ADMIN or CHIEF_ACCOUNTANT | Update calendar |
| `/{calendarId}` | DELETE | ADMIN or CHIEF_ACCOUNTANT | Delete calendar |

**Validators**: `@CalendarIdExists` on calendarId.

**Role check**: Uses `hasAnyRole('ADMIN', 'ROLE_CHIEF_ACCOUNTANT')` (note: inconsistent role naming — 'ADMIN' vs 'ROLE_CHIEF_ACCOUNTANT').

### CalendarServiceImpl

Simple CRUD with audit fields:
- `create(name)`: sets name, createdAt/By, updatedAt/By from current user
- `update(id, name)`: updates name and updatedAt/By
- `delete(id)`: simple deletion

**Design issue**: `update()` contains `calendar.setId(calendar.getId())` — redundant self-assignment, dead code.

### CalendarDaysController (`/v2/days`)

| Endpoint | Method | Authority | Purpose |
|----------|--------|-----------|---------|
| `/` | GET | CALENDAR_VIEW | List calendar days (default page=0, size=100) |
| `/` | POST | ADMIN or CHIEF_ACCOUNTANT | Create calendar day |
| `/{dayId}` | PATCH | ADMIN or CHIEF_ACCOUNTANT | Patch calendar day |
| `/{dayId}` | DELETE | ADMIN or CHIEF_ACCOUNTANT | Delete calendar day |
| `/by-date` | GET | CALENDAR_VIEW | Find by date and calendar ID |

**Validators**: `@CalendarDaysIdExists` on dayId.

**Date format**: ISO 8601 (YYYY-MM-DD). Controller Javadoc: "All time and timezone information will be ignored."

**Design issue**: `findByDate` returns `null` instead of 404 when not found — inconsistent REST convention.

### CalendarDaysServiceImpl — Complex Working Day Calculations

**Constants**:
```java
DAYS_IN_WEEK = 7
WORKING_DAYS_IN_WEEK = 5
START_WEEK_COMPENSATION = 8
```

**Working days calculation** (`calculateWorkingDaysInPeriod`):
1. Calculate base working days (Mon-Fri) in period
2. Apply holiday compensation (hours adjustment from calendar entries)
3. Apply weekend compensation (working weekends, non-working weekdays)

**Calendar day operations**:
- `create`: saves entry + publishes `CalendarUpdatedEvent` with diff calculation
- `patch`: only updates `reason` field (not duration/date — design issue)
- `delete`: publishes both `CalendarUpdatedEvent` and `CalendarDeletedEvent` → triggers absence conflict resolution in vacation service

**Cross-year period handling**: For date ranges spanning year boundaries, queries different calendars per year based on `OfficeCalendar` mapping.

**Event propagation**: Calendar changes cascade to vacation service → day-off deletion, vacation day recalculation.

**Design issue**: `RUSSIAN_CALENDAR_ID` hardcoded constant — legacy code smell, assumes single default calendar.

## 5. Office/Salary Office Management

Offices are synced from CompanyStaff via periodic synchronization (`CSSalaryOfficeSynchronizer` in 3 services: TTT, vacation, calendar). TTT doesn't provide office CRUD — offices are managed externally.

**OfficeController** (`/v1/offices`):
- Period management endpoints (covered in [[accounting-service-deep-dive]])
- Employee extended period endpoints
- Suggestion/search endpoints
- No create/delete — offices come from CompanyStaff

## 6. Tracker Integration

Files located but architecture is complex — uses `TrackerClient` abstraction with factory pattern:
- `TrackerClientFactory` — creates tracker clients (JIRA, GitLab)
- `IssueTrackerService` — manages tracker tasks
- `LoadFromTrackerCommand` / `SendToTrackerCommand` — command pattern for work log sync
- `EmployeeTrackerCredentialsController` — manages per-employee tracker credentials
- `ProjectTrackerWorkLogController` — tracker work log operations

**No GraalVM sandbox found** — the tracker integration uses direct HTTP clients, not a GraalVM sandbox as initially suspected.

## 7. Design Issues Summary

| # | Issue | Location | Severity | Test Impact |
|---|-------|----------|----------|-------------|
| 1 | No @PreAuthorize on PATCH employee | EmployeeController.patch | Medium | Test unauthenticated access |
| 2 | AUTHENTICATED_USER for all project ops | ProjectController | Low | Service guards provide security |
| 3 | IllegalStateException for missing employees | PmToolProjectSynchronizer | Medium | HTTP 500 instead of business error |
| 4 | findByDate returns null not 404 | CalendarDaysController | Low | Client must handle null |
| 5 | PATCH only updates reason | CalendarDaysServiceImpl.patch | Low | Cannot update duration/date via PATCH |
| 6 | Redundant self-assignment | CalendarServiceImpl.update | Low | Dead code |
| 7 | RUSSIAN_CALENDAR_ID hardcoded | CalendarDaysServiceImpl | Low | Legacy constraint |
| 8 | Inconsistent role naming in auth | CalendarControllerV2 | Low | 'ADMIN' vs 'ROLE_CHIEF_ACCOUNTANT' |
| 9 | draft → ACTIVE status mapping | PmToolProjectSynchronizer | Low | Test PM Tool draft projects |
| 10 | Sales filtering removes nulls | PmToolProjectSynchronizer | Low | Test with null watcher entries |

## Related Notes

- [[accounting-service-deep-dive]] — period management, vacation payment
- [[vacation-service-deep-dive]] — vacation CRUD and permissions
- [[dayoff-service-deep-dive]] — day-off calendar conflicts
- [[sick-leave-service-deep-dive]] — sick leave lifecycle
- [[ttt-report-service-deep-dive]] — task report CRUD
- [[pm-tool-sync-implementation]] — PM Tool sync overview
- [[production-calendar-management]] — calendar architecture
- [[EXT-cron-jobs]] — scheduled task inventory

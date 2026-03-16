---
type: module
tags:
  - pm-tool
  - integration
  - sync
  - admin
  - projects
  - sprint-15
  - deep-dive
created: 2026-03-15T00:00:00.000Z
updated: 2026-03-15T00:00:00.000Z
status: active
related:
  - '[[external/tickets/pm-tool-integration]]'
  - '[[modules/admin-panel-deep-dive]]'
  - '[[modules/ttt-service]]'
  - '[[architecture/api-surface]]'
branch: release/2.1
---

# PM Tool Integration — Deep Dive

## Architecture

### Two-Phase ID Mapping
- **Phase 1 (legacy)**: TTT creates projects → PM Tool stores TTT ID as `ttt_id` → `TTT.id = TTT.pmToolId`
- **Phase 2+ (current)**: PM Tool creates projects → TTT stores `pmToolId` (PM Tool's ttt_id) AND `pmtId` (PM Tool's internal ID)

### Project Entity Fields
```java
// Project.java
@Column(name = "pm_tool_id")
private Long pmToolId;    // PM Tool's ttt_id field

@Column(name = "pmt_id") 
private Long pmtId;       // PM Tool's primary key — used for URL links
```

### Sync Mechanism

**Scheduler**: `PmToolSyncScheduler.java` — cron `0 */15 * * * *` (every 15 minutes)

**Feature Toggle**: `PM_TOOL_SYNC-{env}` — gates sync per environment

**Rate Limiter**: Guava `RateLimiter` at 50 req/min (configurable via `pmTool.sync.fetch-rate-per-minute`)

**Sync Process** (`PmToolEntitySyncLauncher.java`):
1. Check feature toggle enabled
2. Fetch projects in pages (100/page) via Feign client `PmToolClient.getProjects()`
3. Rate limit each page fetch (`fetchRateLimiter.acquire()`)
4. Submit each project to async thread pool (`PM_TOOL_SYNC_POOL_NAME`)
5. Timeout: 10 seconds per project
6. Track failures in `pm_tool_sync_failed_entity` table
7. Retry failed projects in batches of 10 (`retry-batch-size`)
8. Record sync status in `pm_sync_status` table
9. Call `postProcess()` → cache eviction + observer batch sync

**Project Synchronizer** (`PmToolProjectSynchronizer.sync()`):
1. `removeSalesFromProject()` — filter sales employees from pmId, ownerId, projectSupervisorId
2. Collect all employee IDs (pm, owner, supervisor, watchers)
3. Bulk-load employees by CompanyStaff ID
4. Validate all employees exist (throws IllegalStateException if missing → HTTP 500)
5. Map PM Tool fields → TTT Project:
   - `pmId` → `managerId`
   - `ownerId` → `ownerId`
   - `projectSupervisorId` → `seniorManagerId`
   - `pmtId` → `pmtId`
   - `pmToolId` → `pmToolId`
   - `draft` status → `ACTIVE` (silent conversion)
6. Set watchers via `InternalProjectObserverService`
7. Evict project from cache

### Entity Reference Type Handling
`CSToolEntityReference` has `type` field: "employee", "sales", "contractor"
- `isSales()` → filtered out before sync
- `isEmployee()` → processed normally
- `isContractor()` → processed normally

### Configuration
```yaml
pmTool:
  url: https://pm-dev2.noveogroup.com
  token: [auth token]
  sync:
    cron: "0 */15 * * * *"
    retry-batch-size: 10
    fetch-rate-per-minute: 50
```

### Test Endpoint
`POST /v1/test/project/sync` — triggers manual sync (TestProjectController)

## Frontend UI Changes

### Project Table (`tableHelpers.js`)
- Project name links to PM Tool: `https://pm.noveogroup.com/projects/{pmtId}/profile/general`
- Falls back to plain text if `pmtId` is missing
- Dev/prod URL distinction via `isDevelopmentEnv` check
- **Supervisor** column: `seniorManager.russianLastName` — sortable, filterable
- **Manager** column: `manager.russianLastName` — sortable, filterable

### Action Buttons (`TableProjectsButtons.js`)
- Edit Template button (non-FINISHED projects)
- Edit Project button (pencil icon — edit existing only, requires `PermissionType.EDIT`)
- Project Info button (info icon)
- **NO "Create Project" button** — project creation via PM Tool only

### Edit Dialog (`EditProjectForm.js`) — 3 Fields Only
1. `scriptUrl` — sync script URL
2. `trackerUrl` — tracker URL path
3. `proxyUrl` — VPN proxy for tracker
All other project fields are **read-only**.

### Info Modal (`InfoProjectModal.js`) — Read-Only
Shows: name (with PM Tool link), account name, customer, country, senior manager, manager, owner, observers, status, type, model, total cost, report dates, tracker URLs.

### No Feature Flags
PM Tool integration is always enabled — no conditional rendering.

## Database Tables

### pm_sync_status
Tracks sync history — when syncs ran and their status.

### pm_tool_sync_failed_entity
Tracks failed sync attempts by entity + ID for retry.

### project table fields
- `pm_tool_id` (Long) — PM Tool's ttt_id
- `pmt_id` (Long) — PM Tool's primary key for URL links

## Design Issues

1. **Missing employee → HTTP 500**: `IllegalStateException` instead of business error when PM Tool references employee not in TTT DB (#3384)
2. **Draft→ACTIVE silent conversion**: PM Tool draft projects become ACTIVE in TTT with no notification
3. **No feature flags in UI**: Can't disable PM Tool integration per-environment in frontend
4. **My Projects link bug**: `href='#'` fallback when `pmtId` is missing — incomplete integration
5. **Rate limiter blocking**: `acquire()` blocks thread until permit available — no timeout or failure mode

## Test Coverage Assessment

### Covered in Admin Workbook (8 cases TC-ADM-006 to TC-ADM-022)
- Sync mechanics (incremental vs full, cron, ShedLock)
- Rate limiting (50 req/min exists)
- Data mapping (draft→ACTIVE, field mapping, preSalesIds)
- Error handling (missing employee → 500, timeout retry)
- Cache eviction post-sync
- UI integration (pmtId link, read-only fields)

### Gaps Identified
- Rate limit boundary testing (trigger the 50 req/min limit)
- PM Tool API unavailability/timeout scenarios
- Partial sync failure recovery (some entities fail, others succeed)
- Concurrent sync attempts (ShedLock contention)
- pmtId null/empty edge cases in URL generation
- Observer batch sync failures
- Sync status tracking verification
- Draft→ACTIVE reverse scenario

## Connections
- [[external/tickets/pm-tool-integration]] — Sprint 15 ticket context
- [[modules/admin-panel-deep-dive]] — admin UI architecture
- [[modules/ttt-service]] — backend service
- [[architecture/api-surface]] — API endpoint inventory

## Sprint 15 PM Tool Ticket Cluster — Enriched Details (S76)

### #3382 — API Pagination/Batching (2 MRs: !5189, !5192)
**Problem**: Sending too many project IDs as query parameters to PM Tool API caused `422 Unprocessable Content`.
**Fix**: Added pagination to `PmToolEntitySyncLauncher`:
- `PmToolEntitySyncLauncher` now fetches projects in pages of 100 (`PAGE_SIZE=100`)
- Uses `nextPage` from response to iterate
- Each page fetch is rate-limited via `fetchRateLimiter.acquire()`
- New `PmToolPageRequest` model handles page parameters
- Integration tests with page-1/page-2 JSON fixtures validate multi-page sync

### #3383 — Broken id Query Parameter (1 MR: !5214)
**Problem**: PM Tool API documentation says `?id=2775` is supported but returns `422 Unprocessable Content`.
**Fix**: Refactored `PmToolClient` to avoid the broken `id` parameter entirely:
- Introduced `PmToolPageRequest` model
- Added `PmToolClientQueryTest` (91 lines) verifying new query approach
- Updated synchronizer and launcher to use new request model

### #3384 — Unable to Locate Employee by ID (NO MRs)
**Problem**: PM Tool references employee ID 642 as owner/manager for multiple projects, but this ID doesn't exist in TTT's DB.
**Resolution**: Data-level issue, likely resolved by #3389's sales filtering — the employee may have been a sales type that TTT doesn't track.
**Design issue**: `validateEmployeesExist()` throws `IllegalStateException` → HTTP 500 instead of a proper business error with actionable details.

### #3387 — pmtId Full-Stack Addition (1 MR: !5236, 18 files)
**Problem**: Need PM Tool's internal project ID to generate URL links from TTT UI to PM Tool project pages.
**Changes**:
- **DB migration** `V2_1_26_20260206120000__add_pmt_id_to_project.sql` — new `pmt_id` column
- **Entity**: `Project.java` — `@Column(name = "pmt_id") private Long pmtId`
- **jOOQ**: Regenerated `ProjectRecord`, `Project` table classes
- **Converter**: `RecordToProjectConverter` maps pmtId from DB
- **REST DTO**: `ProjectListItemDTO` exposes pmtId in API response
- **BO**: `ProjectListItemBO` — business object layer
- **PM Tool model**: `PmToolProjects` reads pmtId from PM Tool API
- **Synchronizer**: `PmToolProjectSynchronizer` persists pmtId during sync
- **Frontend**: `tableHelpers.js` generates PM Tool URL: `https://pm.noveogroup.com/projects/{pmtId}/profile/general`
- **Fallback**: Plain text project name if `pmtId` is null

### #3389 — Sales Employee Type Filtering (1 MR: !5246, 9 files)
**Problem**: PM Tool API changed employee ID format from plain integer to `{"id": N, "type": "T"}`. TTT must parse and skip sales type.
**Changes**:
- **New model**: `CSToolEntityReference` (25 lines) — `id` (Long), `type` (String), methods: `isSales()`, `isEmployee()`, `isContractor()` (all case-insensitive)
- **Updated**: `PmToolProjects` — all employee fields use `CSToolEntityReference` instead of plain Long
- **Synchronizer rewrite** (222 lines diff): `removeSalesFromProject()` nullifies pmId, ownerId, projectSupervisorId if type=sales, removes sales from watchersIds list
- **Affected fields**: `pmId`, `ownerId`, `projectSupervisorId`, `salesIds`, `watchersIds`

### #3093 — Admin Projects UI Frontend Restructure (4 MRs: !5209, !5252, !5260, !5264, ~43 files)
**Major UI overhaul**:
1. **All Projects tab**:
   - "Senior Manager" → "Supervisor" column rename
   - Project name becomes clickable link to PM Tool (`https://pm.noveogroup.com/projects/{pmtId}/profile/general`)
   - Removed inline editing on Type/Status columns
   - Removed "Transfer/Return Project" action button
   - "Edit Project" → "Edit Tracker Data" rename
   - Removed "Create Project" button entirely
2. **My Projects tab**:
   - "Current Manager" → "Manager" column rename
   - Project name links to PM Tool
   - Removed inline editing on Status column
   - Removed Transfer/Create actions
3. **Project Details modal** (`InfoProjectModal.js`, 116 lines):
   - Name displayed as PM Tool link (if pmtId exists)
   - "Senior Manager" → "Supervisor" rename
   - Owner reordered near Manager
   - Hidden "Knowledge Base" and "Notifications" links
   - Sales-type watchers hidden
4. **Edit Tracker Data modal** (`EditProjectForm.js`, 90 lines):
   - Only 3 fields: `scriptUrl` (sync script), `trackerUrl` (tracker URL), `proxyUrl` (proxy)
   - Uses `LinkInputFormik` component
   - All other project fields removed from editing
   - `ProxyDescription` links to Google Docs setup guide

### #3083 — Admin Projects Backend (Parent Ticket, 5 MRs: !4741, !4776, !5122, !5130, !5270)
**Major backend infrastructure** (already covered in main note):
- **Startup sync**: `TttStartupApplicationListener` triggers full sync on app boot (!5130)
- **Default sync script**: Auto-assigns `ttt.noveogroup.com/api/ttt/resource/defaultTaskInfoScript.js` to new projects; not logged as history event (!5270)
- **Accounting name rules**: Set from PM Tool name on first sync; never updated after initial set
- **Change history**: Only tracks changes for TTT-owned fields (scriptUrl, trackerUrl, proxyUrl)
- **Failed entity tracking**: `PmToolSyncFailedProjectRepository` (!5122) — retry in batches of 10

### Test Gap Analysis (S76)
Existing admin test cases (TC-ADM-071 to TC-ADM-080) cover sync mechanics, rate limiting, and basic PM Tool integration. Missing:
1. API pagination handling for >100 projects
2. CSToolEntityReference type-specific filtering (employee vs sales vs contractor)
3. pmtId persistence and URL generation (full-stack)
4. Frontend UI restructure verification (removed buttons, renamed columns, 3-field edit)
5. Startup full sync behavior
6. Default sync script auto-assignment
7. Accounting name immutability after first sync

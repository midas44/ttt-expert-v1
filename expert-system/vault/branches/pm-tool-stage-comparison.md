---
type: analysis
tags:
  - pm-tool
  - stage-comparison
  - sync
  - sprint-15
  - refactoring
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[pm-tool-sync-implementation]]'
  - '[[planner-close-tag-permissions]]'
branch: release/2.1
---
# PM Tool: release/2.1 vs stage Comparison

34 files changed, +2209/-225 lines. Major refactoring of PM Tool sync architecture plus UI cleanup.

## 1. Sync Architecture Refactoring (Backend)

Old monolithic `PmToolSyncService` (185 lines inline sync) replaced with extensible entity-based framework:

- **`PmToolEntitySynchronizer`** — generic interface with `fetch()`, `sync()`, `getId()`, `getEntityName()`, `postProcess()`
- **`PmToolEntitySyncLauncher`** (181 lines) — orchestrator with paginated fetching, async per-entity sync via thread pool + `RateLimiter` (configurable `pmTool.sync.fetch-rate-per-minute`), 10s timeout, failed entity retry in batches
- **`PmToolProjectSynchronizer`** (292 lines) — concrete project sync implementation
- **Failed entity tracking** — new `pm_tool_sync_failed_entity` table + repository for retry

## 2. Client Model Changes

- `PmToolProjects` type changes: `countryId` long→String; `pmId`/`ownerId`/`projectSupervisorId` long→`CSToolEntityReference`; `salesIds`/`watchersIds` List<Long>→List<CSToolEntityReference>
- New `CSToolEntityReference` with `id`+`type` and helpers (`isSales()`, `isEmployee()`, `isContractor()`)
- New field mapping: `seniorManagerId` from `projectSupervisorId` (was `managerId`); `managerId` from `pmId`; new `pmtId` field

## 3. Key Business Logic Changes

- **Sales filtering**: `removeSalesFromProject()` strips sales-type references before processing
- **Employee validation**: throws `IllegalStateException` if referenced employees not in local DB
- **Per-entity transactional**: each project syncs in own `@Transactional` block (was batch)
- **Cache eviction**: `projectService.evictFromCache()` after each sync
- **Feature toggle**: `PM_TOOL_SYNC` via Unleash controls per-environment execution
- **Rate limiting**: tickets #3399 and #3401 add configurable rate limiting

## 4. Close-by-Tag Tracker Integration

`LoadFromTrackerCommand` now calls `closeByTagService.apply(section)` after worklog sync — auto-closes assignments by matching tags. New `CloseByTagService` + `CloseByTagServiceImpl` (267 lines) + integration test (760 lines).

## 5. Frontend UI Changes (#3093)

Major removal of manual project editing UI in admin panel:
- Removed 8 edit field components (manager, country, customer, model, observers, owner, status, type)
- Removed `ProjectButton`, `ProjectsCellStatus`, `ProjectsCellType`, `InfoProjectBudget`
- Simplified `EditProjectForm`, `EditProjectContainer`, `InfoProjectModal`
- Updated translations (EN/RU)

**Rationale**: Projects now managed exclusively via PM Tool sync — manual editing removed.

## 6. Version Bump

tracker-client modules: 2.1.25 → 2.1.26-SNAPSHOT

## Impact Assessment

This closes the PM Tool stage comparison gap. Changes are extensive but don't affect core time reporting or absence functionality. Key test areas:
- PM Tool sync reliability with rate limiting
- Failed entity retry behavior
- Close-by-tag after tracker sync
- Admin Projects UI now read-only for PM Tool-synced fields

See also: [[pm-tool-sync-implementation]], [[planner-close-tag-permissions]], [[feature-toggles-unleash]]

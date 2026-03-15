---
type: external
tags:
  - pm-tool
  - integration
  - sprint-15
  - projects
  - admin
  - sync
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/ttt-service]]'
  - '[[external/tickets/sprint-14-15-overview]]'
  - '[[architecture/api-surface]]'
branch: release/2.1
---
# PM Tool Integration — Sprint 15

## Overview
Major initiative moving project management (creation, editing of core fields) from TTT to an external "PM Tool" system. TTT retains only tracker-specific fields and syncs project data via API.

## Master Tickets
- **#3083** (Backend, Open): Field mapping, sync rules, permission model, deprecation of project creation API
- **#3093** (Frontend, Open): UI changes — rename columns, remove inline editing, link to PM Tool, edit dialog reduced to 3 fields
- **#3286** (Backend, Open): Sync implementation status — project sync done, `pm-id` column added, TODO: deprecate creation API, schedule sync

## Field Mapping (From PM Tool → TTT)
**Synced**: Name, Customer, Country, Supervisor (ex "Senior Manager"), Manager, Owner, Watchers, Status, Type, Model, Presales IDs
**TTT-only**: Accounting Name, Total Cost, First/Last Report Dates, Tracker Script/URL, Proxy Server, Change History
**Deprecated**: Knowledge Base URL, Project Notifications

## Accounting Name Rules
- Existing projects: keep current name
- New projects from PM Tool: copy PM Tool "Name" value
- Once set, never auto-updated by sync

## Permission Changes
- VIEW: all users with Admin>Projects access
- EDIT: Supervisor/Manager/Owner/Admin (only TTT-local fields)
- Close-by-tag: PM/Manager/Supervisor can configure planner tags

## API Integration Issues (6 tickets)

| Ticket | Issue | State |
|--------|-------|-------|
| #3382 | Batch fetch needed — many IDs as query params causes 422 | Open |
| #3383 | PM Tool `id` query parameter returns 422 despite docs | Open |
| #3384 | Employee ID 642 in PM Tool not found in TTT DB | Open |
| #3389 | PM Tool changed employee ID format to `{id, type}` — skip `sales` type | Open |
| #3391 | TTT has 3132 projects but PM Tool returns only 501 — blocking for project links | Open |
| #3397 | 500 error on project creation (deprecated on qa-1) | Closed |

## Rate Limiting (2 tickets)
- **#3399**: TTT hits PM Tool 429 Too Many Requests during sync
- **#3401**: Solution — client-side rate limiting at 60 RPM

## UI Changes (#3093)
- "All Projects" tab: Supervisor column, project name links to PM Tool, remove inline edit for Type/Status, remove "Create Project" button
- "My Projects" tab: Manager column, same link changes
- Project Details: name as link, Supervisor label, hide Knowledge Base/Notifications, hide SALES watchers
- "Edit Tracker Data" dialog: only 3 fields (tracker script, tracker URL, proxy)

## Additional Context
- **#3387**: Store `pmtId` from PM Tool for frontend links (`https://pm-preprod.noveogroup.com/projects/{pmtId}/profile/general`)
- **#2724**: Planner close-by-tag feature uses PM Tool role names (PM/Manager/Supervisor)
- **#3400**: CSV export of individual calendar norms (tangentially related)
- **PM Tool API spec**: https://docs.google.com/document/d/1DFZ6o_8-XE2vATYZ7wTt1TQ0J8uO6tMuIzsvPwCHQBI/edit

## Key People
- **Olga Maksimova**: QA lead, assignee on most tickets
- **Sergey Navrockiy**: Backend, rate limiting
- **Vladimir Ulyanov**: Backend, pmtId/planner
- **Ivan Starodumov**: Data investigation (#3391)
- **Irina Malakhovskaia**: Author of master tickets

## Impact Assessment
- **High**: Project admin UI fundamentally changes — creation moves to PM Tool
- **Medium**: Sync reliability issues (rate limits, data mismatches) risk stale data
- **Low**: Tracker-specific fields unchanged in TTT

## Connections
- [[modules/ttt-service]] — project management in backend
- [[external/tickets/sprint-14-15-overview]] — Sprint context
- [[architecture/api-surface]] — API changes
- [[modules/frontend-planner-module]] — close-by-tag feature (#2724)


## Session 26 Update — New Ticket Details

### #3382 — Batch Fetch Query String Overflow
PM Tool API returns 422 when TTT appends too many project IDs as query params. Fix: batch requests with limited IDs per call. **Interdependent with #3399** — more batched requests may worsen rate limiting.

### #3383 — PM Tool `id` Filter Returns 422
Despite PM Tool API docs claiming `id` query parameter support, it returns 422. External dependency — requires PM Tool team fix or workaround.

### #3384 — Employee ID 642 Not in TTT DB
PM Tool references employee ID 642 as owner/manager on projects (3101, 2888, 2848, 2805, 2792, 2753, 2671), but this employee doesn't exist in TTT. Data sync/mapping gap.

### #3389 — Employee ID Format Breaking Change
PM Tool changed employee references from plain integers to `{"id": N, "type": "employee|sales"}` objects. TTT must parse new format and **skip `type: "sales"` entries**. Breaking API contract change affecting multiple touchpoints.

### #3387 — `pmtId` Field End-to-End
Store PM Tool internal project ID (`pmtId`) through: PM Tool response → TTT DB → TTT API → frontend. Enables deep links: `https://pm-preprod.noveogroup.com/projects/{pmtId}/profile/general`.

### Interdependency Analysis
- **#3382 + #3383 + #3399**: Three facets of same problem — efficiently fetching specific projects without triggering 422 or 429 errors. Must be solved together.
- **#3389**: Breaking schema change may affect code beyond just project sync.
- **#3384**: Data integrity issue — requires either employee sync fix or graceful handling of missing employees.


## Session 27 Update — #3401 Rate Limiter Implementation Details

### Mechanism
Google Guava `RateLimiter` (token-bucket algorithm) applied to `PmToolEntitySyncLauncher.java`.

### Configuration
- **Property**: `pmTool.sync.fetch-rate-per-minute`
- **Default**: 50 RPM (tuned down from initial 60 RPM in second commit)
- **Conversion**: `RateLimiter.create(fetchRatePerMinute / 60.0)` → permits per second

### Behavior
- Single `fetchRateLimiter.acquire()` call before each `fetch()` in the sync loop
- **Blocking**: Thread waits until permit available — no exceptions thrown
- **Thread-safe**: Guava RateLimiter serializes requests across threads (FIFO)
- Added as constructor-injected field with `@Value` annotation

### Tests (PmToolEntitySyncLauncherTest.java)
1. **Single-thread**: 3 fetches at 60 RPM → verifies ≥2 seconds elapsed
2. **Multi-thread**: 4 fetches from 2 threads at 60 RPM → verifies ≥3 seconds elapsed

### Dependency
New: Google Guava added to `ttt/service/service-impl/pom.xml`

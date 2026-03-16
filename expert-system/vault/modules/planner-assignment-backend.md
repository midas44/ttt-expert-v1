---
type: module
tags:
  - planner
  - backend
  - assignment
  - generation
  - ordering
  - close-by-tag
  - locks
  - websocket
created: '2026-03-13'
updated: '2026-03-15'
status: active
related:
  - '[[investigations/planner-ordering-deep-dive]]'
  - '[[modules/frontend-planner-module]]'
  - '[[modules/planner-close-tag-permissions]]'
  - '[[external/requirements/REQ-planner]]'
  - '[[architecture/websocket-events]]'
branch: release/2.1
---
# Planner Assignment Backend

## Overview
The planner assignment subsystem manages task assignments per employee per date. Core operations: generate, create, patch (move/edit), close-by-tag. **No delete endpoint** — assignments are closed, not deleted.

## REST API Endpoints

### Assignment Controller (`/v1/assignments`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/assignments` | AUTHENTICATED_USER / ASSIGNMENTS_ALL | Search assignments grouped by employee |
| GET | `/v1/assignments/history` | AUTHENTICATED_USER / ASSIGNMENTS_ALL | Get assignment change history |
| POST | `/v1/assignments` | AUTHENTICATED_USER / ASSIGNMENTS_ALL | Create single assignment |
| POST | `/v1/assignments/generate` | AUTHENTICATED_USER / ASSIGNMENTS_ALL | Generate assignments from recent + reports |
| PATCH | `/v1/assignments/{assignmentId}` | AUTHENTICATED_USER / ASSIGNMENTS_ALL | Patch assignment fields, move (via nextAssignmentId) |

**Search Request Fields** (`TaskAssignmentSearchRequestDTO`):
- `startDate` (LocalDate, **required**) — period start
- `endDate` (LocalDate, **required**) — period end
- `employeeLogin` (String, optional, validated via `@EmployeeLoginExists`)
- `projectId` (Long, optional, validated via `@ProjectIdExists`)
- `closed` (Boolean, optional) — filter by closed status
- `assignmentId` (Long, optional) — filter by specific assignment
- Custom validator: `@TaskAssignmentSearchRequest` (requires at least employeeLogin or projectId)

**Search Response** (`TaskAssignmentsGroupedByEmployeeResponseDTO`):
- `employees[]` array, each containing:
  - `employee` object (login, name, office, seniorManager, contractor, readOnly, permissions, etc.)
  - `readOnly` boolean
  - `assignments[]` — mixed generated (with `id`, `position`, `nextAssignmentId`) and non-generated (id=null, from task reports without assignments)

**Generate Request** (`TaskAssignmentsGenerateRequestDTO`):
- `employeeLogin` (String, **required**, validated)
- `date` (LocalDate, **required**)
- `projectId` (Long, optional) — if provided, generates for that project only

**Create Request** (`TaskAssignmentCreateRequestDTO` extends `TaskAssignmentBaseDTO`):
- `employeeLogin` (String, **required**, validated)
- `taskId` (Long, **required**)
- `date` (LocalDate, **required**)
- + base fields: `remainingEstimate`, `comment`, `internalComment`, `uiData`, `nextAssignmentId`, `closed`
- Returns 409 (`AlreadyExistsException`) if assignment for same employee+task+date exists

**Patch Request** (`TaskAssignmentPatchRequestBaseDTO` extends `TaskAssignmentBaseDTO`):
- All base fields optional: `employeeLogin`, `remainingEstimate`, `comment` (HTML), `internalComment` (HTML), `uiData` (JSON string), `nextAssignmentId` (triggers move), `closed` (Boolean)
- Returns 423 if assignment is locked by another employee
- Returns 409 if move creates duplicate

**History Request** (`TaskAssignmentHistoryRequestDTO`):
- `employeeLogin` (String, **required**)
- `taskId` (Long, **required**)
- `startDate` / `endDate` (LocalDate, **required**)
- Paginated (page, pageSize)

### Lock Controller (`/v1/locks`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v1/locks` | AUTHENTICATED_USER / ASSIGNMENTS_VIEW / REPORTS_VIEW | Create cell locks |
| DELETE | `/v1/locks` | same | Delete current employee's locks |
| GET | `/v1/locks` | same | Search active locks |

**Lock Behavior**:
- Locks last **1 minute** — must re-invoke POST to extend
- POST replaces all previous locks for the employee — only the cells in the request are locked
- Returns 423 if lock is held by another employee
- Lockable fields: TaskAssignment (`remainingEstimate`, `comment`, `internalComment`, `uiData`) + TaskReport (`effort`, `reportComment`, `state`, `stateComment`)
- DELETE removes all locks for current authenticated employee
- WebSocket LOCK/UNLOCK events emitted on create/delete

### Close-by-Tag Controller (`/v1/projects/{projectId}/close-tags`)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/projects/{projectId}/close-tags` | AUTHENTICATED_USER / PROJECTS_ALL | List tags for project |
| POST | `/v1/projects/{projectId}/close-tags` | same + object-level perm | Create tag (idempotent get-or-create) |
| PATCH | `/v1/projects/{projectId}/close-tags/{tagId}` | same + object-level perm | Update tag string |
| DELETE | `/v1/projects/{projectId}/close-tags/{tagId}` | same + object-level perm | Delete tag |

**Object-level permissions** (via `PlannerCloseTagPermissionService`):
- Authorized: admin, project manager, senior manager, project owner — get CREATE+EDIT+DELETE together
- Denied: plain employees, read-only users — get empty set (can still LIST but not mutate)
- Tag `@NotBlank`, DB column `length = 255` (requirements say max 200 — **discrepancy**)
- Create is **idempotent**: duplicate tag returns existing record (race-condition safe via REQUIRES_NEW)
- Update to duplicate tag returns 400 ValidationException (not idempotent)
- Cross-project validation: tag must belong to specified projectId

## Key Service Classes

### InternalTaskAssignmentService (434 lines)
- **create()**: Sets `position = 0`, emits WebSocket event
- **createForCloseByTag()**: Creates assignment pre-closed via tag, `position = 0`
- **patch()**: Updates fields; if `nextAssignmentId` present, triggers `move()`
- **move()** (307-366): Drag-drop reorder — fetches all for date, sorts, removes/reinserts, rebuilds linked-list AND position
- **moveFutureAssignmentsAccordingly()** (382-432): Propagates move to future dates for same employee. Contains `System.out.println` debug code in production (line 406). Silently returns if target task doesn't exist on future date.

### TaskAssignmentServiceImpl (444 lines)
- **generate()** (168-228): Creates missing assignments, then **overwrites entire ordering** (linked-list + position) based on search results. Destroys any manual DnD reordering.
- **search()**: Returns assignments with employee mapping
- Non-generated assignments (from task reports without planner assignment) included in response with `id=null`

### TaskAssignmentSorter (42 lines)
Deterministic: assignments with `position != null` sorted by (position ASC, taskName); `position == null` sorted by taskName and **prepended to front**.

## DB Schema (task_assignment table)

| Column | Type | Notes |
|--------|------|-------|
| id | bigint PK | Sequence-generated |
| assignee | bigint FK → employee | Employee ID |
| task | bigint FK → task | Task ID |
| date | date | Assignment date |
| position | integer, nullable | Ordinal (added by migration V2_1_2_202101191720) |
| next_assignment | bigint FK → self | Linked-list pointer |
| closed | boolean | If true, won't be generated for future dates |
| remaining_estimate | varchar | Free text estimate |
| comment | text | HTML content |
| internal_comment | text | HTML, not shown to customer |
| ui_data | text | JSON string managed by frontend |
| updated_time | timestamp | Last modification |
| show_in_history | boolean | Whether visible in history tab |

**Close-by-tag table** (`planner_close_tag`):
| Column | Type | Notes |
|--------|------|-------|
| id | bigint PK | Sequence-generated |
| project_id | bigint FK → project | Not null |
| tag | varchar(255) | Not null, unique per project |

## Live Data (timemachine, March 2026)
- Active assignments on busy days: 1000-1700+
- Employee `diborisov` has 15+ assignments per day with full position/linked-list chain
- All assignments have sequential positions (0, 1, 2...) and linked-list chain
- Comments contain HTML (`<p>`, `<strong>`, etc.)
- No close-by-tag data in current env (table empty)

## Known Bugs (5 interconnected tickets)

| Ticket | Bug | Layer | State |
|--------|-----|-------|-------|
| #3258 | Master UX: fix assignment order + add-task | Both | Closed |
| #3308 | DnD order not persisted across days | Backend | Closed |
| #3314 | Order resets on "Open for Editing" | Frontend | Open |
| #3332 | Tasks duplicated after DnD reorder | Frontend | Open |
| #3375 | Member order in project planner broke (regression from #3258) | Both | Open |

## Technical Debt
1. Dual ordering (linked-list + position) must be kept in sync
2. `System.out.println` in production code (moveFutureAssignmentsAccordingly)
3. `position=0` for all new assignments creates ambiguous ordering
4. `generate()` destroys manual DnD ordering
5. No migration backfill: old assignments have NULL position → float to top
6. Move tests verify linked-list but not position values

## Connections
- [[investigations/planner-ordering-deep-dive]] — bug analysis
- [[modules/frontend-planner-module]] — frontend counterpart
- [[modules/planner-close-tag-permissions]] — permission system
- [[external/requirements/REQ-planner]] — requirements
- [[architecture/websocket-events]] — WebSocket events
- [[exploration/data-findings/ttt-backend-schema-deep-dive]] — task_assignment schema

- [[investigations/planner-close-by-tag-implementation]] — Sprint 15 close-by-tag deep investigation

## Close-by-Tag Feature — Enriched Details (S73)

See [[investigations/planner-close-by-tag-implementation]] for full deep-dive. Key additions to module knowledge:

### New API Endpoints (V2.1.27)
| Method | Path | Purpose | Permission |
|--------|------|---------|------------|
| GET | `/v1/projects/{projectId}/close-tags` | List close tags | Any authenticated |
| POST | `/v1/projects/{projectId}/close-tags` | Create tag (idempotent) | Manager/Owner/Admin |
| PATCH | `/v1/projects/{projectId}/close-tags/{tagId}` | Update tag | Manager/Owner/Admin |
| DELETE | `/v1/projects/{projectId}/close-tags/{tagId}` | Delete tag | Manager/Owner/Admin |

### New Database Table
`planner_close_tag`: id, project_id (FK CASCADE), tag (VARCHAR 255), UNIQUE(project_id, tag)

### Integration Points
- `TaskRefreshServiceImpl.refresh()` → `closeByTagService.apply()` after refresh
- `LoadFromTrackerCommand.execute()` → `closeByTagService.apply()` after tracker sync
- WebSocket events: PATCH (existing) / GENERATE+ADD (generated) to `/topic/employees/{login}/assignments`

### Frontend Changes
- "Project employees" modal → "Project settings" modal with 2 tabs
- New tab "Tasks closing" with tag CRUD UI, inline editing, new-item highlighting

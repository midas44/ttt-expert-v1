---
type: module
tags:
  - planner
  - backend
  - assignment
  - generation
  - ordering
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[investigations/planner-ordering-deep-dive]]'
  - '[[modules/frontend-planner-module]]'
  - '[[external/requirements/REQ-planner]]'
branch: release/2.1
---
# Planner Assignment Backend

## Overview
The planner assignment subsystem manages task assignments per employee per date. Core operations: generate, create, patch (move/edit), delete, close-by-tag.

## Key Service Classes

### InternalTaskAssignmentService (434 lines)
Primary business logic. Key methods:
- **create()**: Creates single assignment, sets `position = 0`, emits WebSocket event
- **createForCloseByTag()**: Creates assignment pre-closed via tag, `position = 0`
- **patch()**: Updates assignment fields; if `nextAssignmentId` present, triggers `move()`
- **move()** (307-366): Drag-drop reorder — fetches all assignments for date, sorts, removes/reinserts at target position, rebuilds both linked-list and position indices
- **moveFutureAssignmentsAccordingly()** (382-432): Propagates move to D+1...Dn for same employee
- **delete()**: Removes assignment, emits event

### TaskAssignmentServiceImpl (444 lines)
Higher-level orchestration. Key methods:
- **generate()** (168-228): Creates missing assignments for date, then **overwrites entire ordering** (both nextAssignmentId and position) based on current search results
- **search()**: Returns assignments with employee mapping
- **searchInternal()**: Core query with optional project filter

### TaskAssignmentSorter (42 lines)
Deterministic sorting: assignments with position sorted by (position, taskName); assignments without position sorted by taskName and prepended.

## API Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/assignments` | Search assignments by date/employee/project |
| POST | `/v1/assignments` | Create single assignment |
| POST | `/v1/assignments/generate` | Generate + reorder all assignments for date |
| PATCH | `/v1/assignments/{id}` | Update fields, optionally move (if nextAssignmentId provided) |
| DELETE | `/v1/assignments/{id}` | Delete assignment |

## Close-by-Tag Feature (#2724)
New Sprint 15 feature. PM/Manager can configure tag labels per project. During generation, assignments matching tags are auto-set `closed=true` — only shown if they have reported hours. Tags stored in `planner_close_tag` table, max 200 chars.

## Cell Locking
WebSocket-based. Controller acquires lock before PATCH, releases after. Lock structure: `{cellKey, employeeLogin, taskId, field, timestamp, expiresAt}`. Risk: stale locks if WebSocket disconnects without cleanup.

## Permission Model
- **View**: any employee with project access
- **Edit**: employee (own assignments), manager, department manager, admin
- **Generate**: same as edit (checked in controller)
- Cell locks prevent concurrent edits to same assignment field

## Data Flow
```
Frontend DnD → PATCH {nextAssignmentId} → Controller.patch()
  → InternalTaskAssignmentService.patch()
    → move() → sort → remove → insert → rebuild linked-list + positions
      → moveFutureAssignmentsAccordingly()
    → emit WebSocket events
```

```
Frontend "Open for Editing" → POST /generate {employeeLogin, projectId, dates}
  → TaskAssignmentServiceImpl.generate()
    → searchInternal() → create missing → overwrite all positions
    → emit WebSocket events
```

## Technical Debt
1. **Dual ordering mechanism**: linked-list + position column coexist, must be kept in sync
2. **System.out.println in production** in moveFutureAssignmentsAccordingly()
3. **position=0 for all new assignments**: creates ambiguous ordering until move()
4. **generate() destroys manual ordering**: calling generate resets all positions
5. **No migration backfill**: old assignments have NULL position, always sorted to top
6. **Move test gap**: tests verify linked-list but not position values

## Connections
- [[investigations/planner-ordering-deep-dive]] — bug analysis
- [[modules/frontend-planner-module]] — frontend counterpart
- [[external/requirements/REQ-planner]] — requirements
- [[exploration/data-findings/ttt-backend-schema-deep-dive]] — task_assignment schema

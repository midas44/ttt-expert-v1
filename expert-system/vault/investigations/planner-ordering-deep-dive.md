---
type: investigation
tags:
  - planner
  - ordering
  - linked-list
  - bug
  - backend
  - frontend
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/frontend-planner-module]]'
  - '[[external/requirements/REQ-planner]]'
  - '[[exploration/data-findings/ttt-backend-schema-deep-dive]]'
branch: release/2.1
---
# Planner Ordering Bug Deep Dive

## Overview
The planner uses a **dual ordering mechanism** — a linked-list (`next_assignment` self-FK) AND a `position` integer column added later (migration V2_1_2_202101191720). This creates a fragile system with multiple failure modes.

## Architecture

### Entity: TaskAssignment
- `nextAssignmentId` (Long) — self-FK linking to next assignment in chain
- `position` (Integer, nullable) — ordinal index, added post-launch

### Sorter: TaskAssignmentSorter
Splits assignments into two groups:
1. **With position** (`position != null`): sorted by position ASC, then taskName
2. **Without position** (`position == null`): sorted by taskName, **prepended to front**

Critical: null-position assignments always float to the top regardless of linked-list order.

### Move Logic (InternalTaskAssignmentService.move())
1. Fetch all employee assignments for the date
2. Sort via TaskAssignmentSorter
3. Remove the moving assignment from list
4. Find insertion point (index of `nextAssignmentId` target, or end if null)
5. Re-insert at calculated index
6. Rebuild BOTH linked-list AND positions in a single pass
7. Propagate to future dates via `moveFutureAssignmentsAccordingly()`

### Generate Logic (TaskAssignmentServiceImpl.generate())
Called by `POST /v1/assignments/generate`. **Always overwrites entire linked-list AND position values** based on current order from `searchInternal()`, regardless of any prior manual reordering.

### Repository Query (findAll)
```sql
ORDER BY ta.position, t.name
```
Returns assignments ordered by position then name — ignores linked-list entirely for retrieval.

## Bug Sources Identified

### 1. NULL Position Values (Legacy Data)
Assignments created before position migration have `position = NULL`. The sorter places these at list start, breaking manual reordering for old assignments.

### 2. Initial Position = 0 for New Assignments
Both `create()` and `createForCloseByTag()` set `position = 0`. Multiple new assignments on same date all get position 0, relying on secondary sort by taskName.

### 3. Linked-List ↔ Position Inconsistency
Move and generate rebuild both, but no migration/cleanup logic corrects existing mismatched data. If DB state is inconsistent, sorter produces wrong results.

### 4. Future Date Propagation Bug
`moveFutureAssignmentsAccordingly()` (line 382-432):
- **`System.out.println()` left in production** (line 406) — debug code
- If target task doesn't exist on future date, silently returns without error handling
- Future assignments can be left in inconsistent state

### 5. Generate Overwrites Manual Order
Calling `generate` resets all positions based on `searchInternal()` result order, destroying any manual drag-drop ordering that was done.

## GitLab Ticket Cluster (5 interconnected)

| Ticket | Bug | Layer | State |
|--------|-----|-------|-------|
| #3258 | Master UX: fix assignment order + add-task | Both | Closed |
| #3308 | DnD order not persisted across days | Backend | Closed |
| #3314 | Order resets on "Open for Editing" | **Frontend** (API returns correct order per jsaidov) | Open |
| #3332 | Tasks duplicated after DnD reorder | Frontend | Open |
| #3375 | Member order in project planner broke (regression from #3258) | Both | Open (In Progress) |

### Key Finding
Backend developer Jamshid Saidov confirmed (on #3314) that the API returns tasks in correct position+name order. The "Open for Editing" order reset is a **frontend bug** — the frontend doesn't preserve backend-provided order when switching to edit mode.

### #3332 Duplication Bug
First reported as #3255 (May 2025), still open. Both Chrome and Firefox. Drag-drop produces duplicate entries in the task list. This is a pure **frontend state management bug** in the Redux/generateAssignments logic.

### #3375 Regression
After #3258 fix, employee order in project planner changed from project-defined to alphabetical. The "Project Settings" popup DnD order was supposed to control the main table order — this link was broken.

## Test Coverage
- `InternalTaskAssignmentServiceMoveTest`: tests linked-list chain after moves but **does not verify position column**
- `TaskAssignmentSorterTest`: exists but limited
- No integration tests for the full move→future-propagation→generate cycle

## Key Files
| Component | Path |
|-----------|------|
| Entity | `ttt/db/db-api/.../entity/task/assignment/TaskAssignment.java` |
| Sorter | `ttt/service/service-impl/.../task/assignment/TaskAssignmentSorter.java` |
| Move/Create | `ttt/service/service-impl/.../task/assignment/InternalTaskAssignmentService.java` |
| Generate | `ttt/service/service-impl/.../task/assignment/TaskAssignmentServiceImpl.java` |
| Controller | `ttt/rest/.../controller/v1/task/TaskAssignmentController.java` |
| Repository | `ttt/db/db-api/.../repository/task/TaskAssignmentRepository.java` |
| Migration | `ttt/db/db-migration/.../V2_1_2_202101191720__add_assignment_position.sql` |

## Connections
- [[modules/frontend-planner-module]] — frontend DnD and generateAssignments logic
- [[external/requirements/REQ-planner]] — requirements spec
- [[exploration/data-findings/ttt-backend-schema-deep-dive]] — task_assignment table analysis
- [[external/tickets/sprint-14-15-overview]] — Sprint context
- [[debt/planner-ordering-debt]] — technical debt entry

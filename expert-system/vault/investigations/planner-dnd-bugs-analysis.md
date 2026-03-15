---
type: investigation
tags:
  - planner
  - dnd
  - bugs
  - race-condition
  - ordering
  - frontend
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/frontend-planner-module]]'
  - '[[modules/planner-assignment-backend]]'
  - '[[external/requirements/REQ-planner]]'
branch: release/2.1
---

# Planner DnD Bugs — Root Cause Analysis

Deep code analysis of #3332 (task duplication) and #3314 (order reset). Session 11.

## Architecture
- Two views: Tasks (TaskTableContainer) and Projects (ProjectTableContainer)
- DnD library: react-beautiful-dnd
- State: Redux (assignments saga) + local React state (filteredRowsOrder)
- Backend: `InternalTaskAssignmentService.move()` — updates linked-list + position column
- WebSocket: PATCH events on `/topic/employees/{login}/assignments`

## Bug #3332 — Task Duplication on Drag

**Root cause**: Race condition between 3 competing state update paths.

1. **Optimistic local reorder** (immediate): `tableDatasheetState.js:134-143` — `setFilteredRowsOrder` via splice
2. **WebSocket event** (delayed): `updateTasksAssignment.ts:70-114` — creates new order array → triggers useEffect in TasksPlannerTable.tsx:80-139
3. **Unconditional refetch** (delayed): `assignments/sagas.ts:346` — `fetchProjectAssignments()` always fires after SORT, rebuilds all state from API

Between steps 2 and 3, `prevAssignmentMap.current` refs get out of sync. The useEffect fires twice (once per state source), and if object references differ (WebSocket update vs refetch), filter runs produce duplicate visual entries.

**Key files**: `tableDatasheetState.js:101-153`, `TasksPlannerTable.tsx:80-139`, `assignments/sagas.ts:346`

## Bug #3314 — Order Reset

**4 mechanisms causing order loss:**

### 1. generateAssignments uses push instead of splice
`generateTaskAssignments.ts:90`: `newOrder[groupKey].push(newId)` — appends new ID at end, old ID remains as dangling reference. Commented-out fix exists: `// newOrder[groupKey].splice(sortIndex, 1, newId)`

### 2. ASSIGNMENTS_SORT WebSocket event is a no-op
`manager/sagas.ts:111-113` dispatches `sortAllAssignment()` → `ASSIGNMENTS_SORT` action. **But NO saga handler listens for this action.** Other users' reorder events are silently dropped.

### 3. sortIndex desyncs from array position
`addTaskAssignment.ts:131-165` sets sortIndex, but `generateTaskAssignments.ts` copies old sortIndex. `tableDatasheetState.js:136-137` uses sortIndex for splice positions → wrong indices after generate.

### 4. Unstable readOnly sort in useEffect
`TasksPlannerTable.tsx:108-121`: sort by readOnly returns 0 for equal elements. Array.sort stability not guaranteed across browsers. After generate converts readOnly→non-readOnly, sort may reorder.

## Additional Bugs Discovered

- **409 error condition inversion**: `assignments/sagas.ts:249`: `!existentObject?.closed !== false` — double-negation, shows error for non-closed assignments (opposite of intent)
- **Backend moveFutureAssignmentsAccordingly**: searches by task ID for future dates, fails silently when task doesn't exist, leaving position values inconsistent

## Related
- [[modules/frontend-planner-module]] — frontend planner
- [[modules/planner-assignment-backend]] — backend assignment service
- [[external/requirements/REQ-planner]] — planner requirements

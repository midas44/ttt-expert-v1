---
type: debt
tags:
  - planner
  - ordering
  - technical-debt
  - high-severity
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[investigations/planner-ordering-deep-dive]]'
  - '[[modules/planner-assignment-backend]]'
  - '[[modules/frontend-planner-module]]'
branch: release/2.1
---
# Planner Ordering Technical Debt

## Summary
The planner assignment ordering uses a dual mechanism (linked-list + position column) that creates data consistency risks and multiple active bugs.

## Issues

### 1. Dual Ordering Mechanism (Architecture)
Linked-list (`nextAssignmentId`) and position column coexist. Both must be kept in sync — any operation updating one without the other creates inconsistency. No single source of truth.

### 2. NULL Position Legacy Data (Data Quality)
Assignments created before position migration have `position = NULL`. Sorter prepends these to the front, breaking manual reordering. No backfill migration exists.

### 3. Position=0 Collision (Design)
All new assignments get `position = 0`. Multiple assignments on same date share position 0, relying on secondary sort by task name. Unpredictable until explicit move.

### 4. Generate Destroys Manual Order (Design)
`POST /assignments/generate` overwrites all positions based on query result order. Any manual drag-drop ordering done before "Open for Editing" is lost.

### 5. System.out.println in Production (Code Quality)
`moveFutureAssignmentsAccordingly()` line 406 uses `System.out.println()` instead of SLF4J logger. Debug code left in production.

### 6. Silent Future Propagation Failure (Error Handling)
If target task doesn't exist on future date, `moveFutureAssignmentsAccordingly()` silently returns. Future assignments left in inconsistent state with no error logged.

### 7. Move Tests Don't Verify Position (Test Gap)
`InternalTaskAssignmentServiceMoveTest` checks linked-list chain after moves but never asserts `position` values. The position column could be wrong and tests would pass.

### 8. Frontend DnD State Bugs (Frontend)
Two open bugs: #3332 (task duplication on DnD) and #3314 (order resets on "Open for Editing"). Both are frontend issues — API confirmed returning correct order.

### 9. Member Order Regression (Regression)
#3375: Employee order in project planner changed from project-defined DnD to alphabetical after #3258 fix. Regression in the "Project Settings" → planner table order link.

## Severity: HIGH
Core UX feature (planner ordering) is broken in multiple ways with both backend data integrity risks and frontend state management bugs.

## Connections
- [[investigations/planner-ordering-deep-dive]] — full investigation
- [[modules/planner-assignment-backend]] — backend implementation
- [[modules/frontend-planner-module]] — frontend implementation

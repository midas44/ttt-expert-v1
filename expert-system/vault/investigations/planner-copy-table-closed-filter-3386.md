---
type: investigation
tags: [planner, assignment, closed-filter, copy-table, sprint-15, bug]
created: 2026-03-16
updated: 2026-03-16
status: active
related: ["[[modules/planner-assignment-backend]]", "[[modules/frontend-planner-module]]"]
branch: release/2.1
---

# Planner Copy Table — Closed Tasks Filter Bug — #3386

## Summary
When a task with 0 hours was deleted in Planner edit mode, the "Copy the table" clipboard output still included the deleted task. Root cause: the assignment search API didn't have a `closed` parameter to filter out closed/deleted assignments.

## 2 MRs Merged (backend + frontend)

### !5242 (merged 2026-02-10, 4 files, backend)
**Changes:**
1. `TaskAssignmentSearchRequestDTO` — added `closed` (Boolean) field
2. `TaskAssignmentSearchRequestBO` — added `closed` (Boolean) field
3. `TaskAssignmentGroupByEmployeeServiceImpl.search()` — added post-filter:
```java
// In-memory filter AFTER fetching all assignments
if (request.getClosed() != null) {
    assignments = assignments.stream()
        .filter(a -> request.getClosed().equals(a.isClosed()))
        .collect(Collectors.toList());
}
```
4. Converter updated to pass `closed` from DTO to BO

**Design note**: Filter is applied in-memory after fetching ALL assignments from DB, not at the SQL query level. For large assignment sets, this is less efficient but simpler to implement.

### !5282 (merged 2026-03-01, 5 files, frontend)
**Changes:**
1. `getAllAssignments()` API function — added `closed` parameter to request payload
2. TypeScript interface updated with `closed?: boolean`
3. Three planner sagas now pass `closed: false`:
   - `handleFetchProjectAssignments` — project view
   - `handleFetchCurrentAssignments` — current user view
   - `handleAddNewAssignmentItem` — after adding new assignment
4. Added `yield put(fetchProjectAssignments())` after `handleManageAssignments` — refreshes project view after assignment changes
5. Removed stray `console.log`

## Technical Details

### TaskAssignmentSearchRequestDTO fields
```java
@NotNull private LocalDate startDate;
@NotNull private LocalDate endDate;
@EmployeeLoginExists private String employeeLogin;
@ProjectIdExists private Long projectId;
private Long assignmentId;
private Boolean closed; // NEW — optional filter
```

### Filter behavior:
- `closed=null` (omitted) → returns ALL assignments (open + closed)
- `closed=false` → returns only open assignments
- `closed=true` → returns only closed assignments

### Impact on "Copy the table":
The copy function uses the same assignment data displayed in the planner grid. Since the grid now excludes closed assignments (via `closed: false`), the copy output also excludes them.

### Post-change refresh:
Added `fetchProjectAssignments()` dispatch after `handleManageAssignments` ensures the project view refreshes with correct data after any assignment change (create, edit, close).

## Test Implications
1. API: Verify `closed=false` excludes closed assignments from response
2. API: Verify `closed=true` returns only closed assignments
3. API: Verify omitting `closed` returns all assignments (backward compatible)
4. UI: Delete 0-hours task in edit mode → Copy table → paste → deleted task NOT present
5. UI: Close task by tag → assignment marked closed → excluded from grid
6. UI: After assignment change → project view auto-refreshes

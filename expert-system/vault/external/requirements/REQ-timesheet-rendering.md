---
type: external
tags:
  - timesheet
  - rendering
  - reports
  - requirements
  - google-sheet
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/ttt-report-service]]'
  - '[[modules/frontend-report-module]]'
  - '[[modules/frontend-approve-module]]'
  - '[[external/requirements/google-docs-inventory]]'
---

# Timesheet Rendering Specification (Google Sheet)

Source: Master spreadsheet (15g1NrKHk2R1To3FFps69DGRPjhwKtxhxa9cFCnGSD8U), tab "Timesheet"

## Data Objects
- **TaskReportDTO** (report): individual time report entry
- **TaskDTO** (task): task definition

## Report Rendering Rules (by priority)

| Priority | Condition | Background | Font |
|----------|-----------|------------|------|
| 1 | Closed period, unconfirmed, no hours | Gray | — |
| 2.1 | Closed project, unconfirmed | Gray | Gray |
| 2.2 | Open period, selected date | Yellow | Black |
| 3 | Special task report | Yellow | Black |
| 4 | Default open period | White | Black |
| 5 | Others' projects, open period | White | Gray |
| — | Rejected report | Red bg | Red |
| — | Approved report | Green bg | Green |

## Period Rules
- Selected dates in **closed periods** → cannot be selected (editing blocked)
- Mouse hover highlighting → blue background (open periods only)
- Tasks mismatched to project template → gray background, no editing

## Task Rendering Rules

### Special Tasks (`task.isTaskRequest = true`)
- Own projects → yellow bg / black font
- Others' projects → yellow bg / gray font

### Closed Project Tasks → white bg / gray or black text

### Default → white bg / black text (with approve permissions)

## Sorting Logic

### "My Tasks" Column
1. Pinned tasks (alphabetical)
2. Special tasks (alphabetical)
3. Unpinned tasks (alphabetical)

### Employee Tasks Column
Mixed own/others': pinned → special → unpinned

### Approval View
1. Special tasks for current user
2. Own project tasks (by approval rights)
3. Others' projects tasks

## Permission Conditions
- Approve/reject buttons: `task.permissions.APPROVE = true`
- Edit: `report.permissions.EDIT` AND `task.permissions.EDIT_FOR_EXECUTOR`

## Implications for Testing
- Verify color-coding matches priority order in all combinations
- Test closed vs open period editing restrictions
- Verify sorting order in all three views
- Test special task identification and rendering
- Verify permission-based button visibility

## Related
- [[modules/ttt-report-service]] — backend report service
- [[modules/frontend-report-module]] — frontend report module
- [[modules/frontend-approve-module]] — approval view
- [[external/requirements/google-docs-inventory]] — source catalog

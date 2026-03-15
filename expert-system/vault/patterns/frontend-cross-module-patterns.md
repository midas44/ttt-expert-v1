---
type: pattern
tags:
  - frontend
  - cross-module
  - effort-calculation
  - notifications
  - tech-debt
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/frontend-report-module]]'
  - '[[modules/frontend-planner-module]]'
  - '[[modules/frontend-approve-module]]'
branch: release/2.1
---
# Frontend Cross-Module Patterns

## Shared Notification Controllers
Three notification controllers reused across Report, Planner, and Approve modules:
- `OverReportNotificationController` — all 3 modules
- `AbsencesNotificationController` — Report + Planner
- `ApproveEffortOverLimitNotification` — Approve only

**Concern**: Tight coupling between modules; vacation/absence logic duplicated.

## Effort Aggregation — Three Different Strategies
| Module | Granularity | Output |
|--------|------------|--------|
| Report | Per-task sum | Single total (minutes→hours) |
| Planner | Per-assignment per-date | Nested by employee/project |
| Approve | Per-weekday columns (Mon-Sun) | Reported + approved breakdown |

Effort conversion: all divide by 60 (minutes→hours). Logic duplicated across helpers, selectors, API transforms.

## Task Rename
Shared `TaskRenameContainer` across all 3 modules — cross-module state for task metadata.

## Period Management
All 3 track approval/report periods differently:
- Report: simple date range
- Planner: assignment date ranges
- Approve: week-based periods with statistics

## Permission Models
- Report: simple permission checks in API responses
- Planner: `readOnly` flag on assignments
- Approve: explicit `APPROVE` permission check in effort calculation

## State Persistence
Both Planner (tasks) and Approve (filters) use `redux-persist` to localStorage. No robust cache invalidation strategy.

## Tech Stack Consistency
- All use Redux + Saga (Ducks pattern)
- Report module also uses React Query (emerging pattern)
- Mixed JS/TS across all modules
- No data normalization anywhere

## Connections
- [[modules/frontend-report-module]] — 53 files, 6.8K lines
- [[modules/frontend-planner-module]] — 211 files, 19.3K lines
- [[modules/frontend-approve-module]] — 84 files, 10.1K lines
- [[modules/frontend-vacation-module]] — 377 files, 27.8K lines
- Total frontend TTT: ~725 files, ~64K lines across 4 main modules

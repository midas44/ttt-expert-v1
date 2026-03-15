---
type: architecture
tags:
  - api
  - endpoints
  - swagger
  - rest
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[system-overview]]'
  - '[[backend-architecture]]'
  - '[[vacation-service-implementation]]'
---
# API Surface Map

Total: **233 endpoints** across 4 services + test APIs.

| Service | Main API | Test API | Total |
|---------|----------|----------|-------|
| TTT | 113 | 15 | 128 |
| Vacation | 68 | 11 | 79 |
| Calendar | 21 | — | 21 |
| Email | 3 | 2 | 5 |

## TTT Service (113 endpoints)

Major endpoint groups:
- **Auth/Security** (4): JWT token, permissions check, API token validation
- **Employees** (18): current user, lookup, search, roles, work periods, settings
- **Tasks** (12): CRUD, rename (migrates reports), tracker refresh, pin/unpin, auto-reject listing
- **Task Reports** (12): CRUD, batch create, accounting export, over-reported check, summary, totals by week
- **Assignments** (6): CRUD, generate from recent reports, history
- **Projects** (12): CRUD, search, find managers, types/models/statuses, close-by-tags
- **Project Members** (5): add/remove/patch/search
- **Offices & Periods** (11): list offices, approve/report period get/patch, extended report period management
- **Statistic Reports** (20): 10 JSON views + 10 CSV mirrors covering departments/employees/projects/tasks cross-products
- **Suggest/Autocomplete** (6): employees, projects, tasks, customers, offices
- **Real-time** (5): cell locks (1-min TTL, WS events), selections
- **Other** (6): notifications, feature toggles, CSV export settings, task templates, API tokens

## Vacation Service (68 endpoints)

- **Day-Offs** (12): CRUD, approve/reject, change approver, optional approvers
- **Vacations Core** (7): find/create/update/delete, is-on-vacation check
- **Vacation Workflow** (5): approve, reject, cancel, change approver, pay
- **Vacation Days** (7): get/update days, grouped-by-years, calculate available/payment days, bulk recalculate
- **Sick Leaves** (6): CRUD, overdue count
- **Employees** (10): find, details, permissions, cache eviction
- **Relationships** (3): optional approvers, PMs, watchers
- **Time-Offs** (2): aggregate absence view
- **Statistics** (4): filtered vacations/sick-leaves, employee list, days summary
- **Files** (4): upload/download/preview/delete
- **Other** (8): office lookup, timelines, warnings

## Key Business Logic Endpoints

- `approve-vacation`, `reject-vacation`, `cancel-vacation`, `pay-vacation` — vacation lifecycle
- `approve-using-put`, `reject-using-put` — day-off lifecycle
- `change-approver` — delegation pattern (both vacation + day-off)
- `calculate-available-paid-days`, `calculate-payment-dates` — vacation calculation engine
- `recalculate-days` — bulk recalculation
- `ptch-approve-period`, `ptch-report-period` — accounting period management
- `generate-using-pst` — auto-generate assignments from reports
- `rename-using-ptch` — task rename with report migration
- `over-reported-using-get` — deviation detection
- `send-accounting-notifications` — trigger manager approval notifications

## Test API Highlights

- **Clock manipulation** (TTT): get/patch/reset — time travel for testing
- **Sync triggers**: employees→CS, projects→PM, statistic report cache
- **8 notification triggers**: over-budget, changed/forgotten/rejected reports, vacation availability, digests, calendar alerts
- **Vacation admin**: annual accruals, recalculate employee vacation, pay expired approved

## Patterns

- **Search + Suggest pairs** for employees, projects, tasks, customers, offices
- **Batch operations** for tasks and task reports (upsert semantics)
- **Dual JSON/CSV export** for all statistic views
- **Real-time collaboration** via cell locks + WebSocket events
- **Multi-environment**: same API available on qa-1, timemachine, stage

See also: [[system-overview]], [[backend-architecture]], [[vacation-service-implementation]]

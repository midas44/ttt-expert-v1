---
type: module
tags:
  - frontend
  - planner
  - websocket
  - drag-drop
  - redux
  - real-time
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/frontend-report-module]]'
  - '[[modules/frontend-approve-module]]'
  - '[[modules/frontend-app]]'
branch: release/2.1
---
# Frontend Planner Module

## Overview
211 files, 19,300 lines — largest frontend module. Real-time collaborative editing via WebSocket (STOMP/SockJS). Drag-drop task assignment with cell locking.

## Component Tree
```
PlannerPage
├─ RemovedNotificationController
├─ PlannerEffortOverLimitNotificationContainer
├─ AbsencesNotificationController
├─ OverReportNotificationController
├─ PlannerTitle
├─ PlannerTabs
│  ├─ Tab 1: Tasks (drag-drop assignment table)
│  ├─ Tab 2: Reports (embedded report module)
│  └─ Tab 3: History (change history log)
├─ SocketManager (WebSocket real-time)
│  ├─ SocketManagerWrapper
│  │  └─ SocketManagerLed (connection indicator)
│  └─ Subscriptions: tasks, projectTasks, assignments, reports, selections, members, locks
└─ TaskRenameContainer
```

## State Management (9 Redux Slices)
1. **plannerTasks** — persisted to localStorage, task search/add history
2. **plannerProjects** — project metadata
3. **manager** — manager-specific data
4. **tasks** — task definitions
5. **reports** — integrated report data
6. **focus** — current focus/selection
7. **locks** — cell locks for concurrent editing `{cellKey: {employeeLogin, taskId, field, timestamp, expiresAt}}`
8. **tooltips** — tooltip state
9. **assignments** — nested by employee/project, each with `{id, uniqId, employeeLogin, task, closed, remainingEstimate, comment, internalComment, sortIndex, readOnly}`

## WebSocket Integration (STOMP)
- Protocol: STOMP over WebSocket (SockJS fallback)
- JWT token in connection headers
- **7 subscription channels**: `/user/queue/{tasks,projectTasks,assignments,reports,selections,members,locks}`
- Real-time cell locking, selection awareness, live assignment updates

## API Endpoints
- `GET /v1/assignments {startDate, endDate, employeeLogin?, projectId?, closed}`
- `PATCH /v1/assignments/{id} {closed, comment, internalComment, nextAssignmentId, remainingEstimate, employeeLogin, uiData}`
- `POST /v1/assignments {employeeLogin, task, startDate, endDate, ...}`
- `GET /v1/calendar`, `GET /v1/periods`, `GET /v1/projects`

## Key Business Logic
- **generateAssignments()**: Auto-generates assignment IDs, maps old→new IDs, preserves sortIndex, handles EMPLOYEE/PROJECT grouping modes
- **Cell locking**: Prevents concurrent edits, cleanup on disconnect (risk of stale locks)
- **localStorage persistence**: plannerTasks auto-synced — risk of stale data if not cleared on logout

## Tech Debt
- 9-slice root reducer with deeply nested assignment structures
- localStorage persistence without robust cache invalidation
- TODO in generateAssignments: "проверять пересоздание объекта с ассайментами" (perf concern about unnecessary object recreation)
- Dual focus tracking: Redux focus reducer + socket selections → sync drift risk
- Mixed TypeScript/JavaScript
- 19K lines suggests need for further modularization

## Connections
- Backend linked-list ordering: [[exploration/data-findings/ttt-backend-schema-deep-dive]] (task_assignment self-FK)
- Shares notification controllers with [[modules/frontend-report-module]], [[modules/frontend-approve-module]]
- WebSocket events: [[architecture/system-overview]]

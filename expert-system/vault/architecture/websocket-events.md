---
type: architecture
tags:
  - websocket
  - stomp
  - real-time
  - planner
  - events
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/frontend-planner-module]]'
  - '[[modules/planner-assignment-backend]]'
  - '[[modules/ttt-report-service]]'
  - '[[architecture/security-patterns]]'
  - '[[debt/planner-ordering-debt]]'
branch: release/2.1
---
# WebSocket Events

TTT uses STOMP-over-WebSocket for real-time planner/reporting updates. Dedicated module: `ttt/websocket/` with 32 source files.

## Protocol & Auth

- **STOMP** via `SimpMessagingTemplate`, SockJS fallback
- **Auth on CONNECT**: JWT token (`Headers.JWT_TOKEN_HEADER`) or API token (`Headers.API_TOKEN_HEADER`) — same dual auth as REST
- Config: `WebsocketConfig`, `WebsocketBrokerConfig`, `WebsocketSecurityConfig`

## Event Types (12)

| EventType | Category |
|---|---|
| GENERATE | Planner assignment generation |
| TASK_RENAME | Task name change (cascades to reports + assignments) |
| TASK_REFRESH_START/FINISH | Task list refresh in planner |
| TRACKER_SYNC_START/FINISH | External tracker sync |
| LOCK/UNLOCK | Cell locking in planner |
| SELECT | Cell selection cursor |
| ADD/PATCH/DELETE | Generic CRUD for reports, assignments, members |

## Topics (7 channels)

| Topic Pattern | Listener | Events | Trigger |
|---|---|---|---|
| `/topic/projects/{id}/tasks` | WsTaskEventListener | TASK_RENAME, TASK_REFRESH_START/FINISH | Task rename or refresh |
| `/topic/employees/{login}/reports/{period}` | WsTaskReportEventListener | ADD, PATCH, DELETE, TASK_RENAME | Report CRUD |
| `/topic/employees/{login}/assignments/{period}` | WsTaskAssignmentEventListener | ADD, PATCH, DELETE, GENERATE | Assignment CRUD + generate |
| `/topic/employees/{login}/locks` | WsLockEventListener | LOCK, UNLOCK | Cell lock/unlock |
| `/topic/employees/{login}/selections` | WsSelectionEventListener | SELECT | Cell selection |
| `/topic/projects/{id}/tracker-work-log` | WsTrackerSyncEventListener | TRACKER_SYNC_START/FINISH | Tracker sync |
| `/topic/projects/{id}/members` | WsProjectMemberEventListener | ADD, PATCH, DELETE | Project member CRUD |

## Architecture Patterns

- **All listeners are `@Async`** — events handled in thread pool, non-blocking
- **`@TransactionalEventListener`** for data mutations (reports, assignments, members, rename) — fires after transaction commit
- **`@EventListener`** for UI state events (lock, unlock, select, refresh, tracker sync) — fires immediately
- **Task rename is complex**: sends to 3 channels (tasks, reports, assignments) because renaming affects all views; extracts sub-events and re-publishes to report/assignment channels
- **Event envelope**: `Event<T>` with `EventType`, `initiatorLogin`, `timestamp`, `payload`

## Test Implications

- WebSocket events create **race conditions** in multi-user testing (planner locks, concurrent edits)
- Lock events use employee login as topic key — **stale lock risk on disconnect** (no heartbeat-based cleanup found)
- TASK_RENAME cascading to 3 channels increases test complexity — need to verify all subscribers receive correct data
- GENERATE event on assignment channel — needs verification with frontend state management bugs (#3332, #3314)

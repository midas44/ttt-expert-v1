---
type: module
tags:
  - backend
  - service
  - ttt
  - core
created: '2026-03-12'
updated: '2026-03-12'
status: draft
related:
  - '[[system-overview]]'
branch: release/2.1
---
# TTT Service

Core time tracking service. Largest backend service with 10 Maven modules.

## Modules
- `app/` — Spring Boot main application
- `rest/` — REST API controllers
- `service/service-api/` — Service interfaces
- `service/service-impl/` — Implementations (periodic jobs, notifications, sync)
- `db/` — JPA entities and repositories
- `websocket/` — WebSocket handlers for real-time updates
- `tracker-client/` — Multi-tracker integration layer (8 tracker implementations)
- `ttt-common-enum/` — Shared enums
- `ttt-common-util/` — Shared utilities
- `integration/` — External system integrations

## Key Responsibilities
- Task and report management (hours tracking)
- Employee data management and CS sync
- Tracker integrations (JIRA, GitLab, Asana, ClickUp, Redmine, YouTrack, Presales)
- Periodic scheduling (CSSyncScheduler, StatisticReportScheduler, BudgetNotificationScheduler)
- WebSocket notifications
- Authentication and authorization

## Related
- [[system-overview]]
- [[vacation-service]]
- [[calendar-service]]
- [[email-service]]
- [[tracker-integrations]]

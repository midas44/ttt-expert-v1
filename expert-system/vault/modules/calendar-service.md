---
type: module
tags:
  - backend
  - service
  - calendar
created: '2026-03-12'
updated: '2026-03-12'
status: draft
related:
  - '[[system-overview]]'
branch: release/2.1
---
# Calendar Service

Manages production calendars, salary offices, and working/non-working day configuration.

## Modules (7)
- `app/` — Spring Boot application
- `rest/` — REST API controllers
- `service/` — Business logic
- `db/` — Persistence layer
- `integration/` — External integrations
- `calendar-common-enum/` — Shared enums

## Key Responsibilities
- Production calendar management per office/country
- Salary office configuration
- Working days calculation (supports business logic in TTT and Vacation services)
- Holiday and special day management

## Related
- [[system-overview]]
- [[vacation-service]]
- [[accounting-workflows]]

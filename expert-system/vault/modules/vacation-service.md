---
type: module
tags:
  - backend
  - service
  - vacation
  - absences
  - priority-1
created: '2026-03-12'
updated: '2026-03-13'
status: active
related:
  - '[[system-overview]]'
branch: release/2.1
---
# Vacation Service

Manages all absence types: vacations, days-off, sick leaves.

## Modules (7)
- `app/` — Spring Boot application
- `rest/` — REST API controllers
- `service/` — Business logic
- `db/` — Persistence layer
- `integration/` — External integrations
- `vacation-common-enum/` — Shared enums

## Key Responsibilities
- Vacation request lifecycle (create, edit, approve, reject, cancel, pay)
- Sick leave management
- Day-off management
- Vacation day calculations (accruals, used vs available, advance vacations)
- Approval workflows
- Statistics and reporting

## Priority
**Priority 1** in mission directive — deepest investigation needed.

## Related
- [[system-overview]]
- [[ttt-service]]
- [[calendar-service]]
- [[vacation-workflows]]
- [[vacation-day-calculation]]

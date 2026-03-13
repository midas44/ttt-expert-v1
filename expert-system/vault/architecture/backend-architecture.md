---
type: architecture
tags:
  - backend
  - spring-boot
  - api
  - services
created: '2026-03-12'
updated: '2026-03-12'
status: draft
related:
  - '[[system-overview]]'
  - '[[ttt-service]]'
  - '[[vacation-service]]'
branch: release/2.1
---
# Backend Architecture

4-service Spring Boot monorepo with 366 REST endpoints, 290 DB migrations, 21 scheduled jobs.

## Service Metrics

| Service | Controllers | Services | Repos | Entities | Tests | Migrations |
|---------|------------|----------|-------|----------|-------|------------|
| TTT | 54 | 119 | 10 | 29 | 60 | 142 |
| Vacation | 35 | 76 | 14 | 19 | 51 | 97 |
| Calendar | 8 | 11 | 6 | 0 | 5 | 11 |
| Email | 4 | 5 | 5 | 0 | 1 | 52 |

## API Surface (366 endpoints)
GET: 145 (40%), POST: 61, PATCH: 22, DELETE: 24, PUT: 17, RequestMapping(legacy): 97 (26%)

## Key Patterns
- **TTT**: Monolithic CRUD/reporting (59% of endpoints). Candidate for domain-driven splitting.
- **Vacation**: Complex business logic (72 specialized service classes). Approval, accrual, sync, notification.
- **Calendar/Email**: Thin facades — no JPA entities, delegate to other services.
- **Mixed annotations**: 26% legacy @RequestMapping vs modern @GetMapping — modernization debt.
- **Read-heavy**: 40% GET. Low DELETE — likely soft-delete patterns.

## Vacation Service — 72 Business Logic Classes
- Vacation mechanics: CRUD, search, approval, recalculation, days calculator
- Employee management: days, office, period, role, warning services
- Scheduling: annual accruals, availability, digests
- Synchronization: HR sync, calendar sync, project sync, statistic report sync
- Administrative: office, production calendar, project members

## Related
- [[system-overview]]
- [[ttt-service]]
- [[vacation-service]]
- [[frontend-architecture]]
- [[EXT-cron-jobs]]

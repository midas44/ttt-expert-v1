---
type: meta
tags:
  - index
  - navigation
created: '2026-03-12'
updated: '2026-03-12'
status: active
---
# Vault Index

## Control Files
- [[_SESSION_BRIEFING]]
- [[_INVESTIGATION_AGENDA]]
- [[_KNOWLEDGE_COVERAGE]]

## Architecture
- [[system-overview]] — Microservices overview, tech stack, code scale
- [[database-schema]] — 86 tables across 4 schemas
- [[roles-permissions]] — 11 global roles, project roles
- [[backend-architecture]] — 4 services, 366 endpoints, 290 migrations
- [[frontend-architecture]] — 11 modules, ~500 files, Redux ducks

## Modules
- [[ttt-service]] — Core time tracking (54 controllers, 119 services)
- [[vacation-service]] — Absence management (35 controllers, 76 services)
- [[calendar-service]] — Calendar management (8 controllers)
- [[email-service]] — Email notifications (4 controllers)
- [[frontend-app]] — React SPA (11 feature modules)

## Analysis
- [[absence-data-model]] — Vacation/sick leave/day-off data structures and lifecycles
- [[office-period-model]] — Salary offices, REPORT/APPROVE periods

## Exploration
### Data Findings
- [[db-data-overview-tm]] — Record counts, business enums, data scale

## External Sources
### Requirements
- [[confluence-overview]] — Documentation structure, unfetched pages list
- [[REQ-accrued-vacation-days]] — #3014: advanceVacation=false rules
- [[REQ-advance-vacation]] — #3092: advanceVacation=true, FIFO, overwork
- [[REQ-vacation-day-corrections]] — #3283: inline editing rules
- [[REQ-over-reporting-notification]] — #2932: over/under-reporting banners
- [[EXT-cron-jobs]] — 23 scheduled jobs across 4 services
- [[EXT-tracker-integration]] — 5 active trackers, integration patterns

### Existing Tests
- [[qase-overview]] — 1,116 cases, 258 suites, shallow coverage

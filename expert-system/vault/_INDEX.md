---
type: meta
tags:
  - index
  - navigation
created: '2026-03-12'
updated: '2026-03-13'
status: active
---

# Knowledge Base Index

## Meta
- [[_SESSION_BRIEFING]] — Current session state and history
- [[_INVESTIGATION_AGENDA]] — Prioritized investigation items
- [[_KNOWLEDGE_COVERAGE]] — Coverage tracking by area

## Architecture
- [[architecture/system-overview]] — 4 services, React frontend, PostgreSQL
- [[architecture/database-schema]] — 86 tables across 4 schemas
- [[architecture/roles-permissions]] — 14 roles (spec) vs 11 (DB), scope-based permissions
- [[architecture/backend-architecture]] — Maven multi-module, Spring Boot
- [[architecture/frontend-architecture]] — React, 11 modules
- [[architecture/api-surface]] — 233 endpoints across 4 services + test APIs
- [[architecture/security-patterns]] — JWT + API token + CAS, auth flow, AUTHENTICATED_USER design
- [[architecture/frontend-structural-quality]] — Circular deps, dead code (488), duplication (1.74%)
- [[architecture/websocket-events]] — 12 event types, 7 STOMP topics, dual auth
- [[architecture/rabbitmq-messaging]] — 8 exchanges, no DLQ, cross-service messaging

## Modules — Backend
- [[modules/ttt-service]] — 54 controllers, 119 services, reports/tasks
- [[modules/ttt-report-service]] — Report submission, confirmation, period management
- [[modules/ttt-report-confirmation-flow]] — Full approve/reject flow, permission matrix, warning system
- [[modules/vacation-service]] — 35 controllers, 76 services, absences
- [[modules/vacation-service-implementation]] — State machine, strategies, cron jobs
- [[modules/sick-leave-service-implementation]] — Dual status, 5 events, chain-of-responsibility notifications
- [[modules/day-off-service-implementation]] — Two-table pattern, 9 lifecycle methods, calendar sync
- [[modules/statistics-service-implementation]] — Cache table, 3 update paths, norm calculation
- [[modules/planner-assignment-backend]] — Assignment generation, ordering (linked-list + position), close-by-tag
- [[modules/accounting-backend]] — Period management, vacation payment, day corrections, notifications
- [[modules/calendar-service]] — 8 controllers, production calendars
- [[modules/email-service]] — 4 controllers, notifications
- [[modules/pm-tool-sync-implementation]] — Feign client, rate limiting, validation cascade bug
- [[modules/companystaff-integration]] — CS sync across 3 services, V2 Feign client, 9 post-processors, 7 bugs

## Modules — Frontend
- [[modules/frontend-app]] — React SPA, 500+ source files
- [[modules/frontend-vacation-module]] — 377 files, 7 routes, 14 Redux slices, Formik form
- [[modules/frontend-sick-leave-module]] — 3 routes, 12 modals, split module architecture
- [[modules/frontend-day-off-module]] — Embedded in vacation, transfer modal, 5 manager sub-tabs
- [[modules/frontend-report-module]] — 53 files, 3 Redux slices, React Query, effort calc
- [[modules/frontend-planner-module]] — 211 files, 9 Redux slices, WebSocket, drag-drop
- [[modules/frontend-approve-module]] — 84 files, 2 Redux slices, dual-tab confirmation
- [[modules/frontend-statistics-module]] — Dual sub-systems: classic 13-tab + employee reports RTK
- [[modules/frontend-accounting-module]] — Route swap bug, dead module, stub components

## Patterns
- [[patterns/vacation-day-calculation]] — Regular vs Advance strategies, formulas
- [[patterns/multi-approver-workflow]] — Shared by vacations and day-offs
- [[patterns/frontend-cross-module-patterns]] — Shared notifications, effort calc, persistence
- [[patterns/feature-toggles-unleash]] — 6 toggles, all infrastructure, env-qualified naming
- [[patterns/email-notification-triggers]] — ~35 templates, scheduled + event-driven, actor variants
- [[patterns/error-handling-agreement]] — Backend↔Frontend: 4 error categories, localized errorCode

## Investigations
- [[investigations/vacation-approval-workflow-e2e]] — Two-tier approval model, bug verification
- [[investigations/vacation-recalculation-batch-bug]] — -60 day cluster trace
- [[investigations/bug-verification-s5]] — Bugs #2 (CONFIRMED), #4 (CONFIRMED: FIFO missing)
- [[investigations/vacation-day-calculation-verification]] — Code vs DB vs API end-to-end
- [[investigations/backend-test-suite-analysis]] — 150 tests / 2839 sources, 5.3% ratio, critical gaps
- [[investigations/frontend-test-suite-analysis]] — 28 tests / 1808 sources, 1.5% ratio, 6 untested modules
- [[investigations/figma-vs-live-ui-comparison]] — 4 designs vs live UI, row expansion RESOLVED (chevron-only)
- [[investigations/planner-ordering-deep-dive]] — Dual mechanism, 5 bug sources, 6 tickets, test gap
- [[investigations/planner-dnd-bugs-analysis]] — #3332 race condition (3 paths), #3314 (4 root causes)
- [[investigations/employee-reports-row-expansion]] — Chevron-only click, stale cache bug, spec deviation

## Analysis
- [[analysis/absence-data-model]] — Vacation, sick leave, day-off data models
- [[analysis/office-period-model]] — REPORT/APPROVE dual periods

## Debt
- [[debt/vacation-service-debt]] — 4 bugs, 2 security, schema debt, code quality
- [[debt/planner-ordering-debt]] — Dual ordering mechanism, 9 issues, HIGH severity

## Exploration — UI Flows
- [[exploration/ui-flows/app-navigation]] — Navigation structure, 7 top-level items, login flow
- [[exploration/ui-flows/vacation-pages]] — Vacation creation form, day-off tab, requests, chart
- [[exploration/ui-flows/reporting-and-other-pages]] — My Tasks, Planner, Confirmation, Statistics
- [[exploration/ui-flows/sick-leave-pages]] — 3 views: employee, manager (2 tabs), accounting (richer table)
- [[exploration/ui-flows/accounting-pages]] — 5 sub-pages: salary, periods, payment, correction, sick leave records
- [[exploration/ui-flows/admin-panel-pages]] — 7 admin pages: Projects, Employees, TTT Parameters, Calendars, API, Export, Account
- [[exploration/ui-flows/sick-leave-accounting-workflow]] — Dual status system, any-to-any transitions, 3 views compared
- [[exploration/ui-flows/confirmation-flow-live-testing]] — Full approve/reject UI testing, N+1 API, JS error

## Exploration — API Findings
- [[exploration/api-findings/vacation-crud-api-testing]] — Full CRUD lifecycle, 6 bugs (3 HIGH NPEs)
- [[exploration/api-findings/sick-leave-api-testing]] — Permission design blocks API token access
- [[exploration/api-findings/report-crud-api-testing]] — Full CRUD lifecycle, 6 bugs (3 HIGH: effort/approval)
- [[exploration/api-findings/dayoff-api-testing]] — Full lifecycle (10 ops), 7 bugs (2 HIGH NPEs, 4 MEDIUM)
- [[exploration/api-findings/accounting-api-testing]] — 25 endpoints tested, 3 bugs, 5 design issues
- [[exploration/api-findings/statistics-api-testing]] — 10 endpoints, mixed unit discrepancy, cache pattern
- [[exploration/api-findings/dayoff-rescheduling-warning-bug]] — HIGH: overdue warning broadcast to all users
- [[exploration/api-findings/period-management-api-testing]] — Period PATCH testing, 3 bugs, 5 constraints verified
- [[exploration/api-findings/period-api-live-testing]] — Period advance/revert: 4 bugs (2 HIGH), full business rules, extended periods
- [[exploration/api-findings/dayoff-calendar-conflict-code-analysis]] — 4 conflict paths, architecture issues, entity state bug

## Exploration — Data Findings
- [[exploration/data-findings/db-data-overview-tm]] — Data scale overview
- [[exploration/data-findings/vacation-schema-deep-dive]] — 32 ttt_vacation tables analyzed
- [[exploration/data-findings/ttt-backend-schema-deep-dive]] — 40 tables, task_report 3.57M rows
- [[exploration/data-findings/email-templates-inventory]] — 120 templates, Russian-only
- [[exploration/data-findings/calendar-schema-deep-dive]] — 10 calendars, 9 office transitions
- [[exploration/data-findings/sick-leave-dayoff-data-patterns]] — Sick leave + day-off DB data analysis
- [[exploration/data-findings/ttt-backend-remaining-tables]] — 40 remaining tables, 8 data quality issues
- [[exploration/data-findings/dayoff-rescheduling-data-patterns]] — Status distribution, DELETED_FROM_CALENDAR, overdue analysis
- [[exploration/data-findings/dayoff-calendar-conflict-analysis]] — Mass conflict events, 7 edge cases, 10 test scenarios

## External — Requirements (Confluence)
- [[external/requirements/confluence-overview]] — Entry page summary
- [[external/requirements/REQ-accrued-vacation-days]] — #3014 accrued days (AV=false)
- [[external/requirements/REQ-advance-vacation]] — #3092 advance vacation (AV=true)
- [[external/requirements/REQ-vacation-day-corrections]] — Vacation day corrections
- [[external/requirements/REQ-over-reporting-notification]] — Over-reporting notification
- [[external/requirements/REQ-accounting]] — Accounting, vacation correction
- [[external/requirements/REQ-confirmation]] — Confirmation, reporting deviation banner
- [[external/requirements/REQ-planner]] — Planner assignments and settings
- [[external/requirements/REQ-statistics]] — Statistics, employee reports
- [[external/requirements/REQ-vacations-master]] — Master vacation spec (two modes)
- [[external/requirements/REQ-vacation-calendar-interaction]] — Cross-service interaction
- [[external/requirements/REQ-sick-leave]] — Sick leave: 4-phase design, dual status, regional rules
- [[external/requirements/REQ-day-off]] — Day-off: calendar recalculation, transfer rules
- [[external/requirements/REQ-statistics-employee-reports]] — Employee Reports: norm formula, deviation, comments

## External — Google Docs/Sheets
- [[external/requirements/google-docs-inventory]] — 24 documents cataloged, 8 fetched
- [[external/requirements/REQ-vacations-google-spec]] — Vacation v1.0: 14 events, accrual formula, all workflows
- [[external/requirements/REQ-tracker-integration]] — 5 trackers, zero-trust scripting sandbox
- [[external/requirements/REQ-timesheet-rendering]] — Color-coding, sorting, permission buttons
- [[external/requirements/REQ-dismissal-process]] — 8-step cross-system (TTT+CS+STT)

## External — Designs
- [[external/designs/figma-sprint-14-15-designs]] — 4 Figma nodes

## External — Tickets
- [[external/tickets/sprint-14-15-overview]] — Sprint 14 (42), Sprint 15 (59), Hotfix Sprint 14 (6)
- [[external/tickets/pm-tool-integration]] — 14 tickets: sync, API issues, rate limiting, UI changes

## External — Other
- [[external/existing-tests/qase-overview]] — 1,116 test cases in 258 suites
- [[external/EXT-cron-jobs]] — 21 active cron jobs, code-verified
- [[external/EXT-tracker-integration]] — Tracker integration spec

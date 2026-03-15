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
- [[architecture/deployment-architecture]] — 7 services, Docker Compose, GitLab CI/CD, Spring Cloud Eureka+Gateway
- [[architecture/auth-authorization-doc]] — Developer doc: dual JWT+API token auth, @PreAuthorize patterns, role loading

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
- [[modules/planner-close-tag-permissions]] — Object-level permission system: CREATE/EDIT/DELETE, 4 authorized roles, 8 integration tests
- [[modules/accounting-backend]] — Period management, vacation payment, day corrections, notifications
- [[modules/calendar-service]] — 8 controllers, production calendars
- [[modules/email-service]] — 4 controllers, notifications
- [[modules/pm-tool-sync-implementation]] — Feign client, rate limiting, validation cascade bug
- [[modules/companystaff-integration]] — CS sync across 3 services, V2 Feign client, 9 post-processors, 7 bugs
- [[modules/auto-reject-report-flow]] — Auto-reject: trigger, UI on My Tasks, BO leak, no data on any env

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
- [[investigations/sick-leave-number-validation]] — Backend vs frontend aligned: optional, max 40 chars, whitespace trim
- [[investigations/tracker-integration-deep-dive]] — 8 tracker types, GraalVM sandbox, 222K work logs, low adoption
- [[investigations/rabbitmq-statistic-report-sync]] — Complete PATH 3: vacation/sick-leave → MQ → statistic_report, race condition
- [[investigations/database-performance-analysis]] — PostgreSQL performance: 2.6GB DB, 7 issues, 526MB unused indexes

## Analysis (Phase B Preparation)
- [[analysis/absence-data-model]] — Vacation, sick leave, day-off data models
- [[analysis/office-period-model]] — REPORT/APPROVE dual periods
- [[analysis/phase-b-readiness-assessment]] — Phase B readiness: 99.5% → 100% coverage
- [[analysis/role-permission-matrix]] — 85+ endpoints, 26 routes, 12 permission classes, 5 security gaps
- [[analysis/vacation-business-rules-reference]] — 10 sections, 45+ rules, 12 known bugs
- [[analysis/reports-business-rules-reference]] — 10 sections, 14 bugs, reports/confirmation/periods/statistics
- [[analysis/sick-leave-dayoff-business-rules-reference]] — 2 parts, 23 bugs, 4 calendar conflict paths
- [[analysis/qase-dedup-strategy]] — 258 suites, 1116 cases mapped, priority generation targets
- [[analysis/qase-coverage-detailed-mapping]] — Corrected Qase coverage: Accounting 127 (not 0), sick leave/day-off lifecycle gaps
- [[analysis/vacation-form-validation-rules]] — Frontend Formik + backend DTO/validator rules, min days gap
- [[analysis/report-form-validation-rules]] — Frontend imperative + backend 8 DTOs, effort asymmetry, 62-day search limit
- [[analysis/sick-leave-form-validation-rules]] — Frontend Yup 3 modes + backend DTO, number required on close only
- [[analysis/dayoff-form-validation-rules]] — Frontend imperative + backend custom validators, UI vs API weekend gap
- [[analysis/accounting-form-validation-rules]] — Period, payment (@Range 0-366), day correction, budget notification, statistics search
- [[analysis/admin-calendar-form-validation-rules]] — Calendar CRUD (name uniqueness), events (duration 0-12), tracker config, admin validators

## Branches
- [[branches/cross-branch-release21-vs-stage]] — 193 commits, 8 major features, 17 bug fixes, 10 DB migrations
- [[branches/pm-tool-stage-comparison]] — 34 files, +2209/-225: sync refactoring, rate limiting, UI removal

## Debt
- [[debt/vacation-service-debt]] — 4 bugs, 2 security, schema debt, code quality
- [[debt/planner-ordering-debt]] — Dual ordering mechanism, 9 issues, HIGH severity

## Exploration — UI Flows
- [[exploration/ui-flows/app-navigation]] — Navigation structure, 7 top-level items, login flow
- [[exploration/ui-flows/vacation-pages]] — Vacation creation form, day-off tab, requests, chart
- [[exploration/ui-flows/day-off-pages]] — Day-off UI pages and interactions
- [[exploration/ui-flows/reporting-and-other-pages]] — My Tasks, Planner, Confirmation, Statistics
- [[exploration/ui-flows/sick-leave-pages]] — 3 views: employee, manager (2 tabs), accounting (richer table)
- [[exploration/ui-flows/accounting-pages]] — 5 sub-pages: salary, periods, payment, correction, sick leave records
- [[exploration/ui-flows/admin-panel-pages]] — 7 admin pages: Projects, Employees, TTT Parameters, Calendars, API, Export, Account
- [[exploration/ui-flows/admin-projects-deep-exploration]] — PM Tool links, task templates, edit tracker data, My Projects bug
- [[exploration/ui-flows/admin-employees-deep-exploration]] — 2 tabs, ~400 active employees, ~40 subcontractors, search/sort/filter
- [[exploration/ui-flows/sick-leave-accounting-workflow]] — Dual status system, any-to-any transitions, 3 views compared
- [[exploration/ui-flows/confirmation-flow-live-testing]] — Full approve/reject UI testing, N+1 API, JS error
- [[exploration/ui-flows/figma-tooltip-verification]] — 5 tooltip types verified against Figma specs
- [[exploration/ui-flows/file-upload-sick-leave-flow]] — Full create→attach→view→delete cycle, 3 security findings
- [[exploration/ui-flows/notification-page-budget-monitoring]] — Budget monitoring: create/delete, md/% limits, 5 roles
- [[exploration/ui-flows/production-calendar-management]] — Admin calendar: 2 tabs, 10 calendars, 27 SOs, event CRUD
- [[exploration/ui-flows/budget-norm-tooltip-verification]] — Conditional 3/4-number tooltip format verified, no bugs
- [[exploration/ui-flows/statistics-ui-deep-exploration]] — Session 29: Tab visibility matrix (1-8 tabs by role), 4 search filters, 3 export options, 3 bugs
- [[exploration/ui-flows/sick-leave-ui-verification]] — Session 29: My Sick Leaves (6 cols) vs Accounting (10 cols), inline status dropdown
- [[exploration/ui-flows/sick-leave-crud-lifecycle]] — Session 31: Full CRUD lifecycle, validation rules, 3 bugs, status transitions

## Exploration — API Findings
- [[exploration/api-findings/vacation-crud-api-testing]] — Full CRUD lifecycle, 6 bugs (3 HIGH NPEs)
- [[exploration/api-findings/sick-leave-api-testing]] — Permission design blocks API token access
- [[exploration/api-findings/report-crud-api-testing]] — Full CRUD lifecycle, 6 bugs (3 HIGH: effort/approval)
- [[exploration/api-findings/dayoff-api-testing]] — Full lifecycle (10 ops), 7 bugs (2 HIGH NPEs, 4 MEDIUM)
- [[exploration/api-findings/accounting-api-testing]] — 25 endpoints tested, 3 bugs, 5 design issues
- [[exploration/api-findings/statistics-api-testing]] — 10 endpoints, mixed unit discrepancy, cache pattern
- [[exploration/api-findings/period-management-api-testing]] — Period management API findings
- [[exploration/api-findings/dayoff-rescheduling-warning-bug]] — HIGH: overdue warning broadcast to all users
- [[exploration/api-findings/period-api-live-testing]] — Period advance/revert: 4 bugs (2 HIGH), full business rules
- [[exploration/api-findings/dayoff-calendar-conflict-code-analysis]] — 4 conflict paths, architecture issues, entity state bug
- [[exploration/api-findings/payment-flow-live-testing]] — 5 payment endpoints, 6 bugs, stuck NEW_FOR_PAID
- [[exploration/api-findings/cron-job-live-verification]] — 20 ShedLock jobs verified, legacy entries, dead config
- [[exploration/api-findings/reject-with-comment-e2e]] — Full reject/re-report cycle, reject table model, email gap
- [[exploration/api-findings/vacation-day-correction-live-testing]] — AV validation, pastPeriodsAvailableDays drift bug
- [[exploration/api-findings/statistics-cross-env-comparison]] — Session 31: TM vs Stage field differences (15 vs 17 fields), name format, export 404

## Exploration — Data Findings
- [[exploration/data-findings/db-data-overview-tm]] — Data scale overview
- [[exploration/data-findings/vacation-schema-deep-dive]] — 32 ttt_vacation tables analyzed
- [[exploration/data-findings/ttt-backend-schema-deep-dive]] — 40 tables, task_report 3.57M rows
- [[exploration/data-findings/email-templates-inventory]] — 120 templates, Russian-only
- [[exploration/data-findings/calendar-schema-deep-dive]] — 10 calendars, 9 office transitions
- [[exploration/data-findings/sick-leave-dayoff-data-patterns]] — Sick leave + day-off DB data analysis
- [[exploration/data-findings/ttt-backend-remaining-tables]] — 40 remaining tables, 8 data quality issues
- [[exploration/data-findings/dayoff-rescheduling-data-patterns]] — Status distribution, DELETED_FROM_CALENDAR
- [[exploration/data-findings/dayoff-calendar-conflict-analysis]] — Mass conflict events, 7 edge cases, 10 test scenarios
- [[exploration/data-findings/email-template-field-mapping]] — 120 templates: per-template Mustache variable mapping
- [[exploration/data-findings/dayoff-calendar-conflict-live-test]] — Live create→delete: Path A orphaned, Path B silent deletion
- [[exploration/data-findings/legacy-vs-new-email-templates]] — 50 legacy dead DB artifacts, 70 NOTIFY_* active
- [[exploration/data-findings/test-data-landscape-timemachine]] — Phase B prep: employees, roles, offices, data volumes, test data strategies

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
- [[external/requirements/confirmation-over-under-reporting]] — Over/under-reporting notification banner
- [[external/requirements/planner-requirements]] — Planner full spec: assignments, ordering, Project Settings
- [[external/requirements/vacation-day-correction-spec]] — AV=true/false rules, 5 negative balance scenarios

## External — Google Docs/Sheets
- [[external/requirements/google-docs-inventory]] — 24 documents cataloged, 11 fetched
- [[external/requirements/REQ-vacations-google-spec]] — Vacation v1.0: 14 events, accrual formula
- [[external/requirements/REQ-tracker-integration]] — 5 trackers, zero-trust scripting sandbox
- [[external/requirements/REQ-timesheet-rendering]] — Color-coding, sorting, permission buttons
- [[external/requirements/REQ-dismissal-process]] — 8-step cross-system (TTT+CS+STT)

## External — Designs
- [[external/designs/figma-sprint-14-15-designs]] — 4 Figma nodes

## External — Tickets
- [[external/tickets/sprint-14-15-overview]] — Sprint 14 (42), Sprint 15 (59), Hotfix Sprint 14 (6)
- [[external/tickets/pm-tool-integration]] — 14 tickets: sync, API issues, rate limiting, UI changes
- [[external/tickets/sprint-15-update-session-24]] — 4 new tickets (#3399-3402), #2724 Ready to Test
- [[external/tickets/ticket-3400-statistics-individual-norm-export]] — Statistics CSV export: individual norm, not yet in codebase
- [[external/tickets/ticket-3392-innovationlab-banner]] — InnovationLab banner: frontend-only, hardcoded role bypass
- [[external/tickets/sprint-16-preview]] — Sprint 16: 5 tickets (contractor termination, sick leave working days, vacation event feed bugs)

## External — Testing Documents
- [[external/requirements/EXT-test-plan]] — pytest stack, 11 sections, swagger-coverage, role parametrization
- [[external/requirements/EXT-vacation-testing-notes]] — 14 critical regression cases, test users, CS integration
- [[external/requirements/EXT-knowledge-transfer]] — QA handoff: automation gaps, technical quirks
- [[external/existing-tests/qase-overview]] — 1,116 test cases in 258 suites
- [[external/existing-tests/confluence-automation-plans]] — Two frameworks: Python/pytest (API) + Java/Selenide (grey-box)

## External — Other
- [[external/EXT-cron-jobs]] — 21 active cron jobs, code-verified
- [[external/EXT-tracker-integration]] — Tracker integration spec

## Phase B — Generated Test Documentation
- **Statistics Module** (Session 48): `test-plan-statistics.xlsx` (3 sheets) + `test-cases-statistics.xlsx` (7 sheets, 111 cases)
- **Sick Leave Module** (Session 49): `sick-leave.xlsx` (11 tabs: Plan Overview + Feature Matrix + Risk Assessment + 8 TS-* suites, 120 cases)
- **Day-Off Module** (Session 50): `day-off.xlsx` (11 tabs: Plan Overview + Feature Matrix + Risk Assessment + 8 TS-* suites, 115 cases)

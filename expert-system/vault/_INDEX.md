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
- [[modules/ttt-report-service-deep-dive]] — **[S53]** Code-level: state machine, 13 endpoints, validators, locks, permissions, error handling
- [[modules/ttt-report-confirmation-flow]] — Full approve/reject flow, permission matrix, warning system
- [[modules/vacation-service]] — 35 controllers, 76 services, absences
- [[modules/vacation-service-implementation]] — State machine, strategies, cron jobs
- [[modules/vacation-service-deep-dive]] — **[S53]** Code-level: VacationStatusManager, validators, VacationServiceImpl, permissions, 3 NPE vulns
- [[modules/sick-leave-service-implementation]] — Dual status, 5 events, chain-of-responsibility notifications
- [[modules/sick-leave-service-deep-dive]] — **[S54]** Code-level: dual status model, 6 endpoints, 7 error codes, identity comparison bug, 10 design issues
- [[modules/day-off-service-implementation]] — Two-table pattern, 9 lifecycle methods, calendar sync
- [[modules/dayoff-service-deep-dive]] — **[S54]** Code-level: dual entity, 12 endpoints, 2 validators, 3 conflict paths, 9 design issues
- [[modules/statistics-service-implementation]] — Cache table, 3 update paths, norm calculation
- [[modules/planner-assignment-backend]] — Assignment generation, ordering (linked-list + position), close-by-tag
- [[modules/planner-close-tag-permissions]] — Object-level permission system: CREATE/EDIT/DELETE, 4 authorized roles
- [[modules/accounting-backend]] — Period management, vacation payment, day corrections, notifications
- [[modules/accounting-service-deep-dive]] — **[S55]** Code-level: 5-check payment, dual periods, corrections, norm recalc, 13 design issues
- [[modules/calendar-service]] — 8 controllers, production calendars
- [[modules/calendar-service-deep-dive]] — **[S56]** Code-level: working day calc, cross-year resolution, 8 validators, MQ events, CS sync, 10 design issues
- [[modules/email-service]] — 4 controllers, notifications
- [[modules/email-notification-deep-dive]] — **[S56]** Code-level: Mustache templates, batch SMTP, async RabbitMQ, 35+ templates, 7 jobs, digest system, 8 design issues
- [[modules/pm-tool-sync-implementation]] — Feign client, rate limiting, validation cascade bug
- [[modules/companystaff-integration]] — CS sync across 3 services, V2 Feign client, 9 post-processors, 7 bugs
- [[modules/auto-reject-report-flow]] — Auto-reject: trigger, UI on My Tasks, BO leak, no data on any env
- [[modules/admin-panel-deep-dive]] — **[S55]** Code-level: ProjectController, EmployeeController (missing @PreAuthorize), PmToolSync, 10 design issues

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

## Analysis
- [[analysis/absence-data-model]] — Vacation, sick leave, day-off data models
- [[analysis/office-period-model]] — REPORT/APPROVE dual periods
- [[analysis/phase-b-readiness-assessment]] — Phase B readiness: 99.5% - 100% coverage
- [[analysis/role-permission-matrix]] — 85+ endpoints, 26 routes, 12 permission classes, 5 security gaps
- [[analysis/vacation-business-rules-reference]] — 10 sections, 45+ rules, 12 known bugs
- [[analysis/reports-business-rules-reference]] — 10 sections, 14 bugs, reports/confirmation/periods/statistics
- [[analysis/sick-leave-dayoff-business-rules-reference]] — 2 parts, 23 bugs, 4 calendar conflict paths
- [[analysis/qase-dedup-strategy]] — 258 suites, 1116 cases mapped, priority generation targets
- [[analysis/qase-coverage-detailed-mapping]] — Corrected Qase coverage
- [[analysis/vacation-form-validation-rules]] — Frontend Formik + backend DTO/validator rules
- [[analysis/report-form-validation-rules]] — Frontend imperative + backend 8 DTOs
- [[analysis/sick-leave-form-validation-rules]] — Frontend Yup 3 modes + backend DTO
- [[analysis/dayoff-form-validation-rules]] — Frontend imperative + backend validators
- [[analysis/accounting-form-validation-rules]] — Period, payment, correction validators
- [[analysis/admin-calendar-form-validation-rules]] — Calendar CRUD, events, tracker config
- [[analysis/frontend-backend-validation-gaps]] — **[S56]** Cross-module: 25 gaps, day-off/accounting zero frontend validation
- [[analysis/cross-service-integration]] — **[S57]** RabbitMQ (8 exchanges, 11 events), CS sync (3 services, 9 post-processors), Calendar-Vacation interaction, WebSocket (5 topics), 10 design issues

## Patterns
- [[patterns/vacation-day-calculation]] — Regular vs Advance strategies, formulas
- [[patterns/multi-approver-workflow]] — Shared by vacations and day-offs
- [[patterns/frontend-cross-module-patterns]] — Shared notifications, effort calc, persistence
- [[patterns/feature-toggles-unleash]] — 6 toggles, all infrastructure, env-qualified naming
- [[patterns/email-notification-triggers]] — ~35 templates, scheduled + event-driven, actor variants
- [[patterns/error-handling-agreement]] — Backend-Frontend: 4 error categories, localized errorCode

## Investigations
- [[investigations/vacation-approval-workflow-e2e]] — Two-tier approval model, bug verification
- [[investigations/vacation-recalculation-batch-bug]] — -60 day cluster trace
- [[investigations/bug-verification-s5]] — Bugs #2 (CONFIRMED), #4 (CONFIRMED: FIFO missing)
- [[investigations/vacation-day-calculation-verification]] — Code vs DB vs API end-to-end
- [[investigations/backend-test-suite-analysis]] — 150 tests / 2839 sources, 5.3% ratio
- [[investigations/frontend-test-suite-analysis]] — 28 tests / 1808 sources, 1.5% ratio
- [[investigations/figma-vs-live-ui-comparison]] — 4 designs vs live UI
- [[investigations/planner-ordering-deep-dive]] — Dual mechanism, 5 bug sources
- [[investigations/planner-dnd-bugs-analysis]] — #3332 race condition, #3314 root causes
- [[investigations/employee-reports-row-expansion]] — Chevron-only click, stale cache bug
- [[investigations/sick-leave-number-validation]] — Backend vs frontend aligned
- [[investigations/tracker-integration-deep-dive]] — 8 tracker types, GraalVM sandbox
- [[investigations/rabbitmq-statistic-report-sync]] — Complete PATH 3, race condition
- [[investigations/database-performance-analysis]] — 2.6GB DB, 7 issues, 526MB unused indexes

## Exploration — UI Flows
- [[exploration/ui-flows/app-navigation]] — Navigation structure, 7 top-level items
- [[exploration/ui-flows/vacation-pages]] — Vacation creation form, day-off tab, chart
- [[exploration/ui-flows/day-off-pages]] — Day-off UI pages and interactions
- [[exploration/ui-flows/reporting-and-other-pages]] — My Tasks, Planner, Confirmation, Statistics
- [[exploration/ui-flows/sick-leave-pages]] — 3 views: employee, manager, accounting
- [[exploration/ui-flows/accounting-pages]] — 5 sub-pages
- [[exploration/ui-flows/admin-panel-pages]] — 7 admin pages
- [[exploration/ui-flows/admin-projects-deep-exploration]] — PM Tool links, task templates
- [[exploration/ui-flows/admin-employees-deep-exploration]] — 2 tabs, ~400 active employees
- [[exploration/ui-flows/sick-leave-accounting-workflow]] — Dual status, any-to-any transitions
- [[exploration/ui-flows/confirmation-flow-live-testing]] — Full approve/reject UI testing
- [[exploration/ui-flows/figma-tooltip-verification]] — 5 tooltip types verified
- [[exploration/ui-flows/file-upload-sick-leave-flow]] — Full create-attach-view-delete cycle
- [[exploration/ui-flows/notification-page-budget-monitoring]] — Budget monitoring
- [[exploration/ui-flows/production-calendar-management]] — Admin calendar management
- [[exploration/ui-flows/budget-norm-tooltip-verification]] — Tooltip format verified
- [[exploration/ui-flows/statistics-ui-deep-exploration]] — Tab visibility, filters, exports
- [[exploration/ui-flows/sick-leave-ui-verification]] — My Sick Leaves vs Accounting columns
- [[exploration/ui-flows/sick-leave-crud-lifecycle]] — Full CRUD, validation, status transitions

## Exploration — API Findings
- [[exploration/api-findings/vacation-crud-api-testing]] — Full CRUD, 6 bugs (3 HIGH NPEs)
- [[exploration/api-findings/sick-leave-api-testing]] — Permission design blocks API token
- [[exploration/api-findings/report-crud-api-testing]] — Full CRUD, 6 bugs
- [[exploration/api-findings/dayoff-api-testing]] — Full lifecycle, 7 bugs
- [[exploration/api-findings/accounting-api-testing]] — 25 endpoints, 3 bugs, 5 design issues
- [[exploration/api-findings/statistics-api-testing]] — 10 endpoints, mixed unit discrepancy
- [[exploration/api-findings/period-management-api-testing]] — Period management findings
- [[exploration/api-findings/dayoff-rescheduling-warning-bug]] — Overdue warning broadcast bug
- [[exploration/api-findings/period-api-live-testing]] — Period advance/revert: 4 bugs
- [[exploration/api-findings/dayoff-calendar-conflict-code-analysis]] — 4 conflict paths
- [[exploration/api-findings/payment-flow-live-testing]] — 5 endpoints, 6 bugs
- [[exploration/api-findings/cron-job-live-verification]] — 20 ShedLock jobs verified
- [[exploration/api-findings/reject-with-comment-e2e]] — Full reject/re-report cycle
- [[exploration/api-findings/vacation-day-correction-live-testing]] — AV validation, drift bug
- [[exploration/api-findings/statistics-cross-env-comparison]] — TM vs Stage differences

## Exploration — Data Findings
- [[exploration/data-findings/db-data-overview-tm]] — Data scale overview
- [[exploration/data-findings/vacation-schema-deep-dive]] — 32 ttt_vacation tables
- [[exploration/data-findings/ttt-backend-schema-deep-dive]] — 40 tables, task_report 3.57M rows
- [[exploration/data-findings/email-templates-inventory]] — 120 templates
- [[exploration/data-findings/calendar-schema-deep-dive]] — 10 calendars, 9 office transitions
- [[exploration/data-findings/sick-leave-dayoff-data-patterns]] — Data analysis
- [[exploration/data-findings/ttt-backend-remaining-tables]] — 40 remaining tables
- [[exploration/data-findings/dayoff-rescheduling-data-patterns]] — Status distribution
- [[exploration/data-findings/dayoff-calendar-conflict-analysis]] — Mass conflict events
- [[exploration/data-findings/email-template-field-mapping]] — 120 templates: variable mapping
- [[exploration/data-findings/dayoff-calendar-conflict-live-test]] — Live create-delete paths
- [[exploration/data-findings/legacy-vs-new-email-templates]] — 50 legacy, 70 active
- [[exploration/data-findings/test-data-landscape-timemachine]] — Test data strategies

## External — Requirements
- [[external/requirements/confluence-overview]] — Entry page summary
- [[external/requirements/REQ-accrued-vacation-days]] — #3014 AV=false
- [[external/requirements/REQ-advance-vacation]] — #3092 AV=true
- [[external/requirements/REQ-vacation-day-corrections]] — Corrections
- [[external/requirements/REQ-over-reporting-notification]] — Over-reporting
- [[external/requirements/REQ-accounting]] — Accounting, correction
- [[external/requirements/REQ-confirmation]] — Confirmation, deviation banner
- [[external/requirements/REQ-planner]] — Planner assignments
- [[external/requirements/REQ-statistics]] — Statistics, employee reports
- [[external/requirements/REQ-vacations-master]] — Master vacation spec
- [[external/requirements/REQ-vacation-calendar-interaction]] — Cross-service
- [[external/requirements/REQ-sick-leave]] — Sick leave spec
- [[external/requirements/REQ-day-off]] — Day-off spec
- [[external/requirements/REQ-statistics-employee-reports]] — Employee Reports
- [[external/requirements/confirmation-over-under-reporting]] — Over/under banner
- [[external/requirements/planner-requirements]] — Planner full spec
- [[external/requirements/vacation-day-correction-spec]] — AV rules, 5 scenarios
- [[external/requirements/google-docs-inventory]] — 24 documents
- [[external/requirements/REQ-vacations-google-spec]] — Vacation v1.0
- [[external/requirements/REQ-tracker-integration]] — 5 trackers
- [[external/requirements/REQ-timesheet-rendering]] — Color-coding
- [[external/requirements/REQ-dismissal-process]] — 8-step cross-system
- [[external/requirements/EXT-test-plan]] — pytest stack
- [[external/requirements/EXT-vacation-testing-notes]] — 14 regression cases
- [[external/requirements/EXT-knowledge-transfer]] — QA handoff
- [[external/existing-tests/qase-overview]] — 1,116 test cases
- [[external/existing-tests/confluence-automation-plans]] — Two frameworks

## External — Other
- [[external/EXT-cron-jobs]] — 21 active cron jobs
- [[external/EXT-tracker-integration]] — Tracker integration spec
- [[external/designs/figma-sprint-14-15-designs]] — 4 Figma nodes
- [[external/tickets/sprint-14-15-overview]] — Sprint 14+15 tickets
- [[external/tickets/pm-tool-integration]] — 14 PM Tool tickets
- [[external/tickets/sprint-15-update-session-24]] — 4 new tickets
- [[external/tickets/ticket-3400-statistics-individual-norm-export]] — Statistics CSV export
- [[external/tickets/ticket-3392-innovationlab-banner]] — InnovationLab banner
- [[external/tickets/sprint-16-preview]] — Sprint 16 preview

## Branches
- [[branches/cross-branch-release21-vs-stage]] — 193 commits, 8 features
- [[branches/pm-tool-stage-comparison]] — 34 files, sync refactoring

## Debt
- [[debt/vacation-service-debt]] — 4 bugs, 2 security, schema debt
- [[debt/planner-ordering-debt]] — Dual ordering, 9 issues

## Phase B — Generated Test Documentation (ALL COMPLETE)
- **Vacation** (S58): `vacation/vacation.xlsx` (11 tabs, 130 cases) — 8 suites
- **Sick Leave** (S59): `sick-leave/sick-leave.xlsx` (9 tabs, 120 cases) — 6 suites
- **Day-Off** (S59): `day-off/day-off.xlsx` (9 tabs, 108 cases) — 6 suites
- **Reports** (S60): `reports/reports.xlsx` (10 tabs, 110 cases) — 7 suites
- **Accounting** (S61): `accounting/accounting.xlsx` (9 tabs, 92 cases) — 6 suites
- **Admin** (S62): `admin/admin.xlsx` (9 tabs, 70 cases) — 6 suites
- **Statistics** (S63 regen): `statistics/statistics.xlsx` (10 tabs, 111 cases) — 7 suites
- **Security** (S51): `security/security.xlsx` (11 tabs, 92 cases) — 8 suites

**Total: 833 test cases, 60 test suites, 8 unified XLSX workbooks**

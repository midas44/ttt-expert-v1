# Knowledge Coverage

## Phase B Generation Status — 10 WORKBOOKS, 1090 CASES, 132 TABS

Overall coverage: **95%** (unchanged — remaining 5% depends on unimplemented features)

### Module Deep-Dive Status

| Module | Status | Vault Note | Key Details |
|--------|--------|-----------------|-------------|
| Vacation Service | DONE | [[vacation-service-deep-dive]] | 5 validators, 6 permissions, 10 transitions, 11 exceptions, 3 NPE vulns |
| Reports Service | DONE | [[ttt-report-service-deep-dive]] | 3 states, 13 endpoints, lock management, 3 events, auto-reject |
| Day-Off Service | DONE | [[dayoff-service-deep-dive]] | 4 conflict paths, calendar integration, 6 entity states |
| Sick Leave Service | DONE | [[sick-leave-service-deep-dive]] | Dual status model, 8 transitions, attachment handling |
| Accounting Service | DONE | [[accounting-service-deep-dive]] | Dual period system, payment flow, day correction, 13 design issues |
| Admin Panel | ENRICHED (S76) | [[admin-panel-deep-dive]] | Projects, employees, calendars, settings, PM Tool sync, 10 design issues |
| Calendar Service | DONE | [[calendar-service-deep-dive]] | Production calendars, office calendars, day types |
| Email/Notification | DONE | [[email-notification-deep-dive]] | 12 template types, 2 schedulers, digest system |
| Cross-Service | ENRICHED (S78) | [[cross-service-integration]] | RabbitMQ (8 exchanges, 11 events), CS sync, WebSocket, +banner +build info |
| Frontend-Backend | DONE | [[frontend-backend-validation-gaps]] | 25 validation gaps across all modules |
| Statistics Service | ENRICHED (S72) | [[statistics-service-implementation]] | 3 update paths, norm calculation, 6 design issues |
| Statistics Eff Bounds | DONE (S72) | [[investigations/statistics-effective-bounds-norm]] | effectiveBounds(), 3 sync paths, budget norm, 10 test gaps |
| Statistics Caching | NEW (S75) | [[investigations/statistics-caffeine-caching-performance-3337]] | Materialized view pattern, RabbitMQ events, 8 MRs, 3 QA bugs |
| Frontend Statistics | DONE | [[frontend-statistics-module]] | 12 tech debt items, dual sub-systems |
| PM Tool Integration | ENRICHED (S76) | [[modules/pm-tool-integration-deep-dive]] | Full Sprint 15 cluster: 7 tickets, 16 MRs, pagination, sales filtering, pmtId, UI restructure |
| PM Tool Ratelimit | NEW (S73) | [[investigations/pm-tool-ratelimit-implementation]] | Guava RateLimiter, 50 RPM, shared singleton, blocking acquire |
| Vacation Sprint 15 | DONE (S65) | [[investigations/vacation-sprint-15-technical-details]] | AV logic, next-year blocking, maternity, status job |
| Vacation AV Multi-Year | NEW (S75) | [[investigations/vacation-av-true-multiYear-balance-3361]] | #3361: currentYear→availablePaidDays fix, daysLimitation reducer, 3 sub-bugs |
| Vacation Past-Date Val | NEW (S77) | [[investigations/vacation-past-date-validation-3369]] | #3369: isBefore(today) check, dual errors, missing i18n, #3360 balance fix |
| Contractor Lifecycle | NEW (S77) | [[modules/contractor-lifecycle-architecture]] | Dual sync, no vacation sync, manager hierarchy, CS statuses, Sprint 16 prep |
| InnovationLab Banner | NEW (S78) | [[investigations/innovationlab-banner-3392]] | #3392: 28 reqs, 3 states, compiled ES module, TTT overrides, role bypass |
| CI Build Number | NEW (S78) | [[investigations/ci-build-number-3036]] | #3036: actuator-based footer, CI always-rebuild, frontend reverted |
| Office Sync | DONE (S65) | [[exploration/data-findings/cross-service-office-sync-divergence]] | 62% employee divergence, root cause analysis |
| Sprint 16 Tickets | DONE (S66) | [[external/tickets/sprint-16-overview]] | 5 tickets, #2876 fix confirmed, #3026 3 unimplemented |
| CS Office Settings | DONE (S67) | [[investigations/cs-office-settings-unimplemented]] | 3 unused CS fields: firstVacation, burnOff, sickLeave |
| Maternity Lifecycle | DONE (S67) | [[investigations/maternity-leave-lifecycle]] | Full begin/end event logic, proportional days, V2.1.25 bug |
| Calendar Migration | DONE (S67) | [[investigations/office-calendar-mapping-2024]] | 11 offices migrated calendars, #2876 context |
| Planner Module | ENRICHED (S73) | [[modules/planner-assignment-backend]] | 5+4 API endpoints, dual ordering, cell locking, close-by-tag, 5 known bugs |
| Close-by-Tag Feature | LIVE-TESTED (S74) | [[investigations/planner-close-by-tag-implementation]] | #2724: CRUD API, PATCH 500 bug, XSS concern, deployment gap |
| Confirmation Notification | NEW (S76) | [[investigations/confirmation-notification-bug-3368]] | #3368: 4 MRs, By Employee missing stats, 3 sub-bugs |
| Planner Closed Filter | NEW (S76) | [[investigations/planner-copy-table-closed-filter-3386]] | #3386: 2 MRs, closed parameter, copy table fix |

### Phase B Test Documentation Status — FINAL + SUPPLEMENTS

| Area | Priority | Status | Cases | Suites | Tabs | Output |
|------|----------|--------|-------|--------|------|--------|
| Vacation | P1-Absences | ENRICHED (S77) | 173 | 14 | 18 | vacation/vacation.xlsx |
| Sick Leave | P1-Absences | COMPLETE | 120 | 6 | 10 | sick-leave/sick-leave.xlsx |
| Day-Off | P1-Absences | COMPLETE | 108 | 6 | 10 | day-off/day-off.xlsx |
| Reports | P2-Reports | ENRICHED (S76) | 115 | 8 | 12 | reports/reports.xlsx |
| Accounting | P3-Accounting | COMPLETE | 92 | 6 | 10 | accounting/accounting.xlsx |
| Admin | P4-Admin | ENRICHED (S76) | 92 | 8 | 12 | admin/admin.xlsx |
| Statistics | Cross-cutting | ENRICHED (S75) | 138 | 9 | 13 | statistics/statistics.xlsx |
| Security | Cross-cutting | COMPLETE | 92 | 8 | 12 | security/security.xlsx |
| Cross-Service | Cross-cutting | ENRICHED (S78) | 52 | 6 | 10 | cross-service/cross-service.xlsx |
| Planner | Cross-cutting | ENRICHED (S76) | 108 | 11 | 15 | planner/planner.xlsx |

**Total: 1090 test cases across 10 XLSX workbooks (82 suites + 10 Test Data tabs = 132 tabs)**

### Session 83 Changes
- No new activity — monitoring session
- !5306 auto-merge confirmed merged successfully (conflicts resolved)
- Builds unchanged across all environments
- Sprint 16 remains stalled (5 tickets, 0 MRs)

### Known Gaps (not blocking)
- #2842 contractor termination lifecycle (not yet implemented — architecture note created S77)
- #2954 sick leave working days UI (not yet implemented — stalled 5+ months)
- #3378 tracker script relocation (not yet implemented)
- #2876 vacation event feed (backlog, analytical task)
- #3026 CS office settings implementation (backlog, 3 unimplemented fields)
- #2724 PATCH gateway routing bug (timemachine build 290209 — no new build available)
- !5114 stale MR — should be closed as duplicate of !5116 (has merge conflicts)
- !5284 unnecessary MR — 0 diff, already merged via !5273+!5277
- Frontend architecture analysis (P3 — useful but not required for test documentation)

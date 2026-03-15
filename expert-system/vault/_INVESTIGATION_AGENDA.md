---
type: meta
tags:
  - agenda
  - planning
created: '2026-03-12'
updated: '2026-03-15'
status: active
---
# Investigation Agenda

## Priority Legend
- P0: Critical — must complete this session
- P1: High — target for next 1-2 sessions
- P2: Medium — within next 5 sessions
- P3: Low — backlog

## Completed (Sessions 1-52)
<details>
<summary>Sessions 1-9 completed items (click to expand)</summary>

### Session 1
- [x] Bootstrap vault, SQLite, QMD, repo clone
- [x] Map repo structure, create architecture overview and module skeletons
- [x] Pull Confluence entry page and key requirements
- [x] Check Qase, explore DB schema, roles, periods, absence model

### Session 2
- [x] Confluence deep-read: Accounting, Confirmation, Planner, Statistics, Vacations
- [x] DB vacation deep-dive, backend vacation service, calculation formulas, multi-approver, debt

### Session 3
- [x] GitLab tickets (107 total), full API surface mapping (233 endpoints), UI exploration (12 pages)

### Session 4
- [x] Frontend vacation module, TTT report service, vacation approval e2e, DB deep-dives, Figma designs

### Session 5
- [x] Frontend report/planner/approve modules, cross-module patterns, bug verification (#2, #4), maintenance

### Session 6
- [x] Sick leave (backend, frontend, DB, requirements), day-off (full stack), statistics (full stack)

### Session 7
- [x] Vacation CRUD API testing (6 bugs), sick leave API testing (blocked), security patterns

### Session 8
- [x] Report CRUD API testing (6 bugs), confirmation flow, frontend dependency analysis

### Session 9
- [x] Test suite analysis (backend + frontend), day-off API testing (7 bugs), Figma vs live UI

</details>

<details>
<summary>Sessions 10-29 completed items (click to expand)</summary>

### Session 10
- [x] Maintenance, feature toggles, WebSocket, RabbitMQ, accounting API, admin panel, DB tables, frontend accounting, email triggers, PM Tool sync

### Session 11
- [x] Statistics API (10 endpoints), planner DnD bugs, sick leave accounting, CompanyStaff integration, Google Docs, Confluence statistics

### Session 12
- [x] Confirmation flow live testing, day-off rescheduling warning bug, day-off data patterns

### Session 13
- [x] Period advance/revert (4 bugs), day-off calendar conflict code analysis, employee reports row expansion

### Session 14
- [x] Payment flow (6 bugs), Figma tooltip verification, Google Docs testing docs

### Session 15
- [x] Email template mapping, day-off conflict live triggering, auto-reject, cron jobs, file upload, maintenance

### Session 16
- [x] Confluence automation plans, Google Docs (inaccessible), notification page, production calendars

### Session 17
- [x] Reject with comment e2e, legacy vs new email templates, vacation day correction

### Session 18
- [x] Admin Projects deep exploration, remaining Confluence pages, Phase B readiness assessment

### Session 19
- [x] Cross-branch comparison (193 commits), Admin Employees deep exploration, sick leave number validation

### Session 20
- [x] Maintenance (vault audit, SQLite cleanup), tracker integration deep dive, RabbitMQ statistic sync

### Session 21
- [x] Database performance analysis (7 issues), deployment architecture, budget/norm tooltip verification

### Session 22
- [x] Role-permission access matrix (5 security gaps), vacation business rules reference

### Session 23
- [x] Reports/confirmation business rules reference, sick leave/day-off business rules reference

### Session 24
- [x] New code (#2724 permissions, auth doc), PM Tool stage comparison, Sprint 15 tickets, Qase dedup strategy

### Session 25
- [x] Maintenance: index consolidation, SQLite cleanup (3 refs + severity normalization), coverage assessment

### Session 26
- [x] Sprint 15 ticket scan (60 tickets, 8 new/updated investigated), #3400 CSV export gap, #3392 InnovationLab banner, PM Tool cluster

### Session 27
- [x] #2724 planner close-by-tag evolution (4 iterations), #3401 PM Tool ratelimit

### Session 28
- [x] Test data landscape (timemachine DB), Qase granular coverage (258 suites, corrected Accounting 0→127)

### Session 29
- [x] Statistics UI deep exploration (tab matrix, filters, exports, 3 bugs), sick leave UI verification

</details>

<details>
<summary>Sessions 30-52 completed items (click to expand)</summary>

### Session 30
- [x] Maintenance §9.4: Vault audit (154 notes, all indexed), SQLite cleanup (severity normalization, finding_type 37→13)

### Session 31
- [x] Sick leave CRUD lifecycle via Playwright (7 fields, 4 validation rules, 3 bugs)
- [x] Statistics cross-env comparison (TM vs Stage: 15 vs 17 fields, name format diff, export 404)

### Session 32
- [x] Day-off employee view via Playwright (QA-1), TransferDaysoffModal date constraints, BUG-DO-11 live confirmation

### Session 33
- [x] Form validation rules: vacation (Formik + 2 backend validators), reports (imperative + 8 DTOs), sick leave (Yup 3 modes), day-off (imperative + custom validators)

### Session 34
- [x] Fixed session 33 artifacts (4 files renamed .md), accounting form validation rules, admin/calendar form validation rules

### Session 35
- [x] Maintenance §9.4: 4 orphan files deleted, SQLite normalized (12 records), 15 wikilink path mismatches fixed
- [x] Monitoring: No new commits (7th session), no Sprint 15 updates (7th session)

### Sessions 36-47
- [x] Monitoring only (8th-19th consecutive no-change sessions)
- [x] Sprint 16 forward intelligence: 5 tickets (3 relevant)
- [x] Session 40: Maintenance §9.4 — 43 broken wikilinks fixed, 3 monitoring records compressed
- [x] Session 42: Corrected GitLab project ID from 622 to 1288
- [x] Session 45: Maintenance §9.4 — compressed sessions 41-44 monitoring (4→1), vault audit (159 notes, 0 issues)

### Session 48 (Phase B begins)
- [x] Phase B transition: config updated, generation mode active
- [x] Statistics module: test-plan-statistics.xlsx (3 sheets) + test-cases-statistics.xlsx (7 sheets, 111 cases)
- [x] All 111 test cases tracked in test_case_tracking SQLite table

### Session 49
- [x] Sick Leave module: sick-leave.xlsx (11 tabs: 3 plan + 8 test suites, 120 cases)
- [x] 120 test cases tracked in SQLite (total: 231)

### Session 50
- [x] Day-Off module: day-off.xlsx (11 tabs: 3 plan + 8 test suites, 115 cases)
- [x] 115 test cases tracked in SQLite (total: 346)

### Session 51
- [x] Security/Permissions: security.xlsx (11 tabs: 3 plan + 8 test suites, 92 cases)
- [x] 92 test cases tracked in SQLite (total: 438)

### Session 52
- [x] Accounting supplements: accounting.xlsx (11 tabs: 3 plan + 8 test suites, 82 cases)
- [x] 82 test cases tracked in SQLite (total: 520)

</details>

## Active Items — Phase B Generation

### P1: Vacations Supplements (Next Session)
- [ ] Read Qase vacation suites (200+ cases) — identify gaps
- [ ] Generate vacations-supplements.xlsx covering gaps not in Qase
- [ ] Focus: API edge cases (12 bugs), business rule boundaries, approval workflow edge cases, day calculation, form validation
- [ ] Track cases in SQLite, update vault

### P2: Reports Supplements (Sessions 54-55)
- [ ] Generate supplement test cases for gaps not in Qase
- [ ] Focus: confirmation edge cases, auto-reject, period advance effects on reports

### P3: Admin Supplements
- [ ] PM Tool sync, close-by-tag permissions, tracker integration

### Known Gaps (not blocking)
- [ ] #3400 individual norm export — "Production Ready" ticket but no code in codebase
- [ ] Planner spec (Google Doc — 401, need access)

### Sprint 16 Awareness (for Phase B context)
- [ ] #2842 Contractor termination — include in sick leave/vacation lifecycle edge cases
- [ ] #2954 Sick leave working days column — include in sick leave UI test cases
- [ ] #2876 Vacation event feed + calendar change bugs — include in vacation supplement tests

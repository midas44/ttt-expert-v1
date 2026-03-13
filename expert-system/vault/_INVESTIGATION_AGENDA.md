---
type: meta
tags:
  - agenda
  - planning
created: '2026-03-12'
updated: '2026-03-12'
status: active
---
# Investigation Agenda

## Priority Legend
- P0: Critical — must complete this session
- P1: High — target for next 1-2 sessions
- P2: Medium — within next 5 sessions
- P3: Low — backlog

## Completed (Session 1)
- [x] Bootstrap vault, SQLite, QMD, repo clone
- [x] Map repo structure (frontend + backend)
- [x] Create architecture overview note
- [x] Create module skeleton notes for major modules
- [x] Pull Confluence entry page and key requirements
- [x] Check Qase test suite structure
- [x] Database schema exploration (86 tables, 4 schemas)
- [x] Roles and permissions mapping (11 global roles)
- [x] Office/period model analysis
- [x] Absence data model analysis (vacation, sick leave, day-off)

## Active Items

### P1 — Sessions 2-3
- [ ] Deep-read Confluence: Accounting (130387462), Confirmation (130385094), Planner (130386435), Statistics (119244531), Vacations parent (130385085)
- [ ] Confluence: Vacations-Calendar interaction (110297393)
- [ ] Map Vacation API surface via Swagger endpoints
- [ ] Map TTT API surface via Swagger endpoints
- [ ] Database deep-dive: vacation_payment, employee_vacation, office_annual_leave, timeline, confirmation_period_days_distribution
- [ ] GitLab tickets: Sprint 14-15 labels (#3283, #3303, #3337, #3345, #3346, #3347)
- [ ] Frontend vacation module: component tree, state flow
- [ ] Backend vacation service: key implementation classes
- [ ] UI exploration via Playwright: login flow, navigation, vacation request

### P2 — Sessions 4-8
- [ ] Dependency analysis: circular deps, dead code
- [ ] Code duplication scan (jscpd)
- [ ] Business logic tracing: vacation approval workflow (code level)
- [ ] Business logic tracing: report submission workflow
- [ ] Business logic tracing: vacation day calculation (code level)
- [ ] Figma design inventory and comparison with implementation
- [ ] Security patterns review (JWT, authorization)
- [ ] Test suite analysis (existing backend/frontend tests)
- [ ] API exploratory testing: vacation CRUD flow
- [ ] API exploratory testing: report submission flow
- [ ] Planner module investigation
- [ ] Statistics module investigation

### P3 — Backlog
- [ ] Accounting workflows deep-dive (period changes, payment processing)
- [ ] Administration features mapping
- [ ] Email notification templates and triggers
- [ ] Cron job behavior verification
- [ ] Tracker integration testing (JIRA, GitLab)
- [ ] Cross-branch comparison (release/2.1 vs stage)
- [ ] WebSocket events investigation
- [ ] CompanyStaff integration details
- [ ] Feature flags inventory (Unleash)
- [ ] Performance analysis (3.5M task_reports queries)

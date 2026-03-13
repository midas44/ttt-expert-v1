---
type: meta
tags:
  - agenda
  - planning
created: '2026-03-12'
updated: '2026-03-13'
status: active
---
# Investigation Agenda

## Priority Legend
- P0: Critical — must complete this session
- P1: High — target for next 1-2 sessions
- P2: Medium — within next 5 sessions
- P3: Low — backlog

## Completed (Sessions 1-9)
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

## Completed (Session 10)
- [x] Maintenance: SQLite cleanup, stale notes, cross-ref audit, category consolidation
- [x] Feature toggles, WebSocket events, RabbitMQ messaging
- [x] Accounting API testing, Admin panel, DB remaining tables
- [x] Frontend accounting module, Email notification triggers, PM Tool sync code

## Completed (Session 11)
- [x] Statistics API live testing: 10 endpoints, mixed unit discrepancy, cache pattern
- [x] Planner DnD bugs: #3332 race condition, #3314 4 root causes
- [x] Sick leave accounting workflow: 3 views, dual status, 5 UX issues
- [x] CompanyStaff integration: 3-service sync, 9 post-processors, 7 bugs
- [x] Google Docs/Sheets: 8 specs fetched
- [x] Confluence Statistics requirements: Employee Reports spec

## Completed (Session 12)
- [x] Confirmation flow live testing: Full approve/reject UI testing, N+1 API pattern, JS error
- [x] Day-off rescheduling warning bug: Overdue warning broadcast to all users (HIGH bug)
- [x] Day-off data patterns: DELETED_FROM_CALENDAR analysis, overdue request investigation

## Completed (Session 13)
- [x] **Period advance/revert live testing**: 4 bugs (2 HIGH), full business rules, extended periods, RabbitMQ events
- [x] **Day-off calendar conflict code analysis**: 4 distinct paths mapped, architecture issues, entity state bug
- [x] **Employee Reports row expansion**: RESOLVED UNCLEAR — chevron-only, stale cache bug, spec deviation

## Active Items

### P1 — Session 14
- [ ] Payment flow live testing (vacation payment endpoints, accounting workflow)
- [ ] Figma tooltip interactions manual verification (sick leave display, norm tooltips)
- [ ] Remaining Google Docs: test plan, vacation testing notes, knowledge transfer docs

### P2 — Sessions 15-16
- [ ] Google Sheet: notifications spec deeper analysis (per-template field mapping)
- [ ] Day-off calendar conflict live triggering (safe test with calendar mutation + restore)
- [ ] Auto-reject behavior verification on confirmation page

### P3 — Backlog
- [ ] Cron job behavior verification on live environment
- [ ] Tracker integration testing (JIRA, GitLab, ClickUp)
- [ ] Cross-branch comparison (release/2.1 vs stage)
- [ ] Performance analysis (3.5M task_reports, 2.5M task_assignments)
- [ ] Remaining Confluence pages exploration
- [ ] Notification page exploration
- [ ] Legacy vs new email template coexistence investigation
- [ ] RabbitMQ message flow for statistic report sync
- [ ] Administration employee management features
- [ ] Deployment architecture investigation
- [ ] Production calendar management UI testing
- [ ] File upload flow live testing (sick leave attachments)
- [ ] Planner spec (Google Doc — 401, need access)

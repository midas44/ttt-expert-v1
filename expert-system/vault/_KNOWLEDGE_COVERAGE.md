---
type: meta
tags:
  - coverage
  - tracking
created: '2026-03-12'
updated: '2026-03-13'
status: active
---

# Knowledge Coverage

**Overall Coverage: ~95%** (Session 13 — Period API + Day-Off Conflicts + Employee Reports Expansion)

## Coverage by Area

### Architecture (99%)
- [x] System overview, 4 services mapped
- [x] Database schema (86 tables, 4 schemas), all deep-dives complete
- [x] Roles and permissions (14 roles from spec vs 11 from DB, reconciled)
- [x] Frontend module structure, cross-module patterns
- [x] API surface: 233 endpoints cataloged
- [x] Security patterns, token model, auth mechanisms
- [x] Frontend structural quality analysis
- [x] Backend + frontend test suites analyzed
- [x] WebSocket, RabbitMQ, feature toggles
- [x] Error handling agreement (backend↔frontend): 4 categories, localized errorCode
- [x] CompanyStaff integration: sync flow, data mapping, 9 post-processors, 7 bugs
- [ ] Deployment architecture

### Vacation Module (98%)
- [x] All previous coverage items
- [x] Google Doc functional spec v1.0: complete spec with 14 event types, accrual formula, all workflows
- [ ] Figma tooltip interactions (minor)

### Sick Leave (93%)
- [x] All previous coverage items
- [x] Accounting workflow explored: 3 views, dual status system, any-to-any transitions
- [ ] File upload flow live testing

### Calendar/Day-Off (97%) ↑ from 95%
- [x] All previous coverage items
- [x] Day-off rescheduling warning system: full chain traced
- [x] Overdue warning bug: deployed code broadcasts to all users
- [x] DELETED_FROM_CALENDAR pattern: 82 records from holiday removal
- [x] **4 conflict paths fully mapped**: CalendarChanged(move), CalendarDeleted(DELETED_FROM_CALENDAR), PeriodChanged(REJECTED), OfficeChange(DELETED_FROM_CALENDAR)
- [x] **Architecture issues**: entity state bug in updateAll(), race condition, PreviousWorkingDayCalculator limitation
- [ ] Live conflict triggering (calendar mutation test)
- [ ] Production calendar management UI

### Reports/TTT Module (90%)
- [x] All previous coverage items
- [x] Timesheet rendering spec: color-coding priorities, sorting logic, permission-based buttons
- [ ] Planner frontend DnD state bugs — root-caused but not verified as fixed

### Confirmation (90%)
- [x] All previous coverage items
- [x] Live UI testing: both tabs, approve/reject, JS error, N+1 API, network trace
- [ ] Auto-reject behavior verification
- [ ] Reject with comment flow end-to-end verification

### Planner (93%)
- [x] All previous coverage items
- [x] DnD bugs root-caused: #3332 race condition (3 paths), #3314 (4 root causes)
- [ ] Planner spec (Google Doc — 401, not accessible)

### Statistics (97%) ↑ from 95%
- [x] All previous coverage items
- [x] API live testing: 10 endpoints, mixed unit discrepancy
- [x] Confluence Employee Reports spec: norm formula, deviation edge cases
- [x] **Employee Reports row expansion**: chevron-only click (spec deviation), stale cache bug, full component architecture
- [x] **Figma comparison resolved**: UNCLEAR → confirmed chevron-only, row click misleading
- [ ] RabbitMQ event flow for cache sync

### Accounting (92%) ↑ from 88%
- [x] All previous coverage items
- [x] **Period advance/revert live testing**: 4 bugs (2 HIGH), full business rules mapped
- [x] **Extended periods mechanism**: time-limited reopening, cron cleanup, blocking logic
- [x] **Period RabbitMQ events**: PeriodChangedEvent vs PeriodReopenedEvent
- [ ] Payment flow live testing

### Email/Notifications (85%)
- [x] All previous coverage items
- [x] Google Sheets email notification spec: complete catalog with Handlebars templates
- [ ] Per-template field mapping verification

### PM Tool Integration (92%)
- [x] All previous coverage items
- [ ] Admin Projects UI live testing with PM Tool context

### External Sources (95%)
- [x] Confluence: 14+ pages read
- [x] Qase: 1,116 test cases inventoried
- [x] Figma: key nodes identified, 4 designs compared
- [x] GitLab tickets: Sprint 14, 15, Hotfix Sprint 14, planner cluster, PM Tool cluster
- [x] Google Docs/Sheets: 8 of 24 documents fetched
- [ ] Google Docs: test plan, vacation testing notes, knowledge transfer (6 remaining)
- [ ] Remaining Confluence pages

### CompanyStaff Integration (92%)
- [x] Feign client architecture, V1→V2 evolution
- [x] Sync flow, data mapping, 9 post-processors, 7 bugs
- [ ] Admin Projects UI with CS context

## Session 13 Statistics
- Vault notes: 105 (102 prior + 3 new)
- Analysis runs: 63 (62 prior + 1 new)
- Design issues: 101 (93 prior + 8 new)
- External refs: 51 (unchanged)
- Exploration findings: 97 (87 prior + 10 new)
- Module health: 25 modules tracked

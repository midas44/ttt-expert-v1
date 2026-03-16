---
type: external
tags:
  - sprint-16
  - tickets
  - gitlab
  - vacation
  - contractor
  - sick-leave
  - office-sync
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[external/tickets/sprint-14-15-overview]]'
  - '[[investigations/vacation-sprint-15-technical-details]]'
  - '[[exploration/data-findings/cross-service-office-sync-divergence]]'
---
# Sprint 16 GitLab Tickets Overview

## Summary
5 tickets total, all open, no merge requests. No "HotFix Sprint 16" label exists.
Primarily focused on absences/vacation subsystem — assigned to Irina Malakhovskaia.

## Tickets

### #2842 — Contractor Termination (Увольнение подрядчиков)
- **Status**: Open, In Progress
- **Assignee**: imalakhovskaia
- **Labels**: In Progress, Sprint 16
- **Created**: 2023-12-06

**Key details**:
- Contractors lack a proper termination process — only have a blocking mechanism
- "Calculate salary" button missing for contractors
- Contractor statuses in CS API: NEW, PENDING, ACTIVE, BLOCKING, BLOCKED
- Use case: contractor→employee transition requires blocking on last day of month, then hiring on 1st of next month
- CS cannot accept a new employee before the current date
- Related to #3273 (parent process), #3295

### #2954 — Sick Leave Working Days Display
- **Status**: Open, To Do
- **Assignee**: imalakhovskaia
- **Labels**: Sprint 16, To Do
- **Created**: 2024-04-15
- **Blocked by**: #2622 (Sprint 10)

**Key details**:
- Add "Working days" column to "My sick leaves" and "Employee sick leaves" pages
- Change "Calendar days" → "Days", add "Working days"
- Useful for individual contractor (IP) employees needing compensation info
- Consistency with Accounting view

### #2876 — Vacation Event Feed: Office/Calendar Sync Bugs
- **Status**: Open, Analytical Task, To Do
- **Assignee**: imalakhovskaia
- **Labels**: Analytical Task, Sprint 16, To Do
- **Created**: 2024-01-25
- **Related**: #2859, #2634, #2789, #2790

**Feature request**: Add DAYS_PER_YEAR_CHANGED event to vacation event feed.

**Bug 1 — Missing recalculation**: When production calendar changes or employee transfers to different calendar office:
- No event feed logging
- No recalculation of days in open vacation requests
- No recalculation of available vacation days
- **Critical**: ttt_backend.employee.salary_office ≠ ttt_vacation.employee.office_id possible

**Bug 2 — "Calculation error"**: After calendar change (bug 8 from #2859):
- Edit (type change) or delete affected vacation → global "Calculation error"
- Date/payment month edits work fine
- Reproducible with Saturn RC + Cyprus calendar switch

**Fix status in release/2.1**: EmployeeOfficeChangedProcessor is present (commit 07eaa225, 2024-03-06). Handles same-calendar changes immediately, defers different-calendar mid-year changes. Bug 2 status unclear.

### #3378 — Relocate Custom Project-Tracker Sync Scripts
- **Status**: Open
- **Assignee**: amaksimenko
- **Labels**: Sprint 16
- **Created**: 2026-01-20

**Key details**:
- Custom sync scripts stored externally on cloud.noveogroup.com
- Office blackout → cloud unreachable → sync failed
- Request: upload scripts into TTT codebase via admin UI
- Default script already in codebase: `ttt.noveogroup.com/api/ttt/resource/defaultTaskInfoScript.js`

### #3026 — CS Office Settings Behavior (Integration)
- **Status**: Open, Analytical Task, To Do
- **Assignee**: imalakhovskaia
- **Labels**: Analytical Task, Sprint 16, To Do
- **Created**: 2024-07-10

**6 CS settings tracked**:
| # | Setting | Status |
|---|---------|--------|
| 1 | Vacation days per year (per RC) | Done |
| 2 | Months before first vacation (#3068) | **NOT IMPLEMENTED** — hardcoded 3 months |
| 3 | Advance vacation (`advanceVacation`) | Done (Sprint 14) |
| 4 | Overtime/undertime in vacation calc | Done — tied to AV flag |
| 5 | Vacation day expiration after N months (#2472) | **NOT IMPLEMENTED** |
| 6 | Include sick leaves | **NOT IMPLEMENTED** — need to disable for contractor RCs |

Additional:
- Contractors should not have vacations (currently can take administrative leave since base days = 0)
- Contractor day-off transfers likely unnecessary

## Test Implications
- #2842: New contractor termination flow → potential test cases for contractor lifecycle
- #2954: UI change → verify column display and data accuracy
- #2876: Critical office sync → 12 vacation supplement + 6 cross-service test cases generated in S66
- #3378: Admin UI change → script upload test cases
- #3026: 3 unimplemented settings → test when implemented, document current hardcoded behavior

## Connections
- [[external/tickets/sprint-14-15-overview]] — prior sprint context
- [[investigations/vacation-sprint-15-technical-details]] — AV and office sync details
- [[exploration/data-findings/cross-service-office-sync-divergence]] — 62% divergence finding
- [[modules/vacation-service-implementation]] — vacation service architecture

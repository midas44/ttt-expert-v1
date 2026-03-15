---
type: external
tags:
  - sprint-16
  - tickets
  - planning
  - phase-b-context
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[external/tickets/sprint-14-15-overview]]'
  - '[[frontend-vacation-module]]'
  - '[[sick-leave-service-implementation]]'
---
# Sprint 16 Preview — Upcoming Changes

5 tickets planned for Sprint 16 (none started on codebase as of 2026-03-15). Key tickets relevant to Phase B test documentation:

## #2842 — Contractor Termination (In Progress, analytical)

**Gap filled**: Currently contractors have no termination process — only blocking via CS statuses (BLOCKING/BLOCKED). No "Calculate salary" button. New process needed for contractor→employee conversions (must settle contractor before 1st of next month).

**Phase B impact**: Test cases for employee lifecycle and accounting must consider contractor-specific flows. Current knowledge base treats contractors as a role variant but their termination/settlement is a distinct feature area.

**Related**: CS integration, salary calculation, employee status transitions.

## #2954 — Sick Leave Working Days Column (To Do)

**Change**: Add "Working days" column to My Sick Leaves and Employee Sick Leaves pages. Rename "Calendar days" to "Days". UI column width adjustments.

**Phase B impact**: Sick leave test cases should anticipate this column. Useful for contractors (IP) who get compensated per working days. Blocked by #2622 (Sprint 10).

## #2876 — Vacation Event Feed + Calendar Change Bugs (Analytical Task)

**Two requirements + two bugs**:
1. New DAYS_PER_YEAR_CHANGED event type
2. Descriptions for calendar-change actions affecting vacation duration

**Bug 1**: No event feed logging or recalculation when office production calendar changes while employee has existing vacation request. Data inconsistency: `salary_office` in `ttt_backend.employee` doesn't sync with `office_id` in `ttt_vacation.employee` after CS sync.

**Bug 2**: "Calculation error" on edit/delete vacation after calendar change + event addition sequence. Reproducible with Saturn office + Cyprus calendar change.

**Phase B impact**: Vacation test cases must include cross-office calendar change scenarios and event feed verification. The data inconsistency between ttt_backend and ttt_vacation employee tables is a significant finding for data integrity test cases.

## Other Sprint 16 Tickets (Lower Priority)
- **#3026**: CS RC (reporting center) settings implementation — integration changes
- **#3378**: Relocate custom tracker sync scripts to TTT codebase — infrastructure

## Connections
- [[frontend-vacation-module]] — #2876 affects vacation calculations
- [[sick-leave-service-implementation]] — #2954 adds UI column
- [[exploration/data-findings/db-data-overview-tm]] — #2876 data inconsistency
- [[external/tickets/sprint-14-15-overview]] — Sprint context continuity

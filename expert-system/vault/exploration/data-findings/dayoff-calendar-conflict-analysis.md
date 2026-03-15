---
type: exploration
tags:
  - day-off
  - calendar-conflict
  - DELETED_FROM_CALENDAR
  - conflict-resolution
  - edge-cases
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[day-off-service-implementation]]'
  - '[[calendar-service]]'
  - '[[dayoff-rescheduling-data-patterns]]'
  - '[[dayoff-rescheduling-warning-bug]]'
branch: release/2.1
---

# Day-Off Calendar Conflict Handling — Database Analysis

## Conflict Resolution Mechanism

When a production calendar is updated (new holiday added to a date with existing day-off requests), the system:
1. Changes request status to `DELETED_FROM_CALENDAR`
2. A new request is created for the employee with a different `personal_date`

Of 82 DELETED_FROM_CALENDAR entries, **56 (68%)** have a corresponding newer APPROVED request for same employee+original_date. The remaining 26 may have been re-deleted or never rescheduled.

## Mass Conflict Events

| Holiday | Original Date | Affected Employees | Reassignment Spread |
|---------|--------------|-------------------|-------------------|
| Cyprus National Holiday | 2025-04-01 | 52 | 273 days |
| Russia Day | 2025-06-12 | 19 | 197 days |
| Orthodox Pentecost Monday | 2025-06-09 | 7 | 181 days |

## Edge Cases Discovered

1. **Half-days (duration=7) NOT treated as conflicts** — Day-offs on half-day calendar entries are valid. `CalendarUpdateProcessorImpl.processDay` only triggers for duration=0 changes.

2. **Weekend make-up days** — APPROVED requests exist where `personal_date` falls on Saturday when production calendar marks it as a working day (make-up day). Valid scenario.

3. **Cascading conflicts** — Employee 615: Cyprus National Holiday moved to Jun 12 → DELETED when Jun 12 became Russia Day → moved to Jul 31 → DELETED again → finally Dec 31 (APPROVED). System handles iteratively, not atomically.

4. **Extreme reassignment distances** — Up to 358 days from original holiday (QA-1). Employees choose future dates freely.

5. **Ledger/request inconsistency** — Some DELETED_FROM_CALENDAR requests have ledger entries with different `original_date` than the request, suggesting ledger tracks a different origin point.

6. **No stale NEW requests** — Zero NEW requests with personal_date in the past on TM, indicating cleanup works.

7. **REJECTED vs DELETED_FROM_CALENDAR** — 14 REJECTED requests exist with holiday reasons, suggesting rejection path when no valid reassignment date available.

## Cross-Environment Comparison

TM and QA-1 have identical DELETED_FROM_CALENDAR data (82 records, same IDs/dates/reasons). Shared historical snapshot. Minor differences in recent activity (TM: 2902 APPROVED, QA-1: 2933).

## Critical Test Scenarios

1. Mass conflict resolution when holiday added to date with multiple employee day-offs
2. Cascading conflict: reassigned date later becomes a holiday too
3. Half-day boundary: duration=7 change must NOT trigger conflict resolution
4. Weekend/make-up day: day-offs valid on calendar working Saturdays
5. Ledger consistency after DELETED_FROM_CALENDAR (no orphans)
6. REJECTED path conditions (no available working days?)
7. Cross-calendar: employee's office calendar vs other calendars
8. Reason field preservation on new request after conflict
9. Approval table tracking during conflict resolution
10. Date boundary: Dec 31 as non-working day with no valid "previous working day"

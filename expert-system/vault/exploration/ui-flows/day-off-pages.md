---
type: exploration
tags:
  - ui-flow
  - day-off
  - weekend
  - playwright
  - timemachine
  - qa-1
  - reschedule-modal
  - date-constraints
created: '2026-03-12'
updated: '2026-03-14'
status: active
related:
  - '[[frontend-day-off-module]]'
  - '[[day-off-service-implementation]]'
  - '[[vacation-pages]]'
  - '[[sick-leave-dayoff-business-rules-reference]]'
branch: release/2.1
---
# Day-Off UI Exploration

Combined findings from Session 4 (Timemachine, manager view) and Session 32 (QA-1, employee view).

## Page 1: /vacation/my/daysoff — Employee "Days off" Tab

### Session 4 — Dmitry Dergachev (Manager, Russia/Novosibirsk, Timemachine)

**Title**: "My vacations and days off". Two top-level tabs: Vacations | Days off (orange underline).

**Year selector**: Datepicker showing current year. "Weekend regulation" info-link → Confluence page 63836489.

**Table columns**: Date of the event (sortable) | Duration (sortable, hours) | Reason (sortable, Russian holiday names) | Approved by (sortable, CS link) | Status (sortable) | Actions

**Row data (2026)**: 17 rows for all Russian public holidays. All status "Approved", approver = Pavel Weinmeister.

**Edit button logic**: Only appears when: NOT a weekend AND duration=0 AND lastApprovedDate >= today. 5 of 17 rows show edit (future dates: 01.05, 11.05, 12.06, 06.11, 31.12.2026). When status=NEW: additional red X cancel button appears.

**Date format**: `DD.MM.YYYY (abbreviated weekday)`, e.g. "01.05.2026 (fr)". NEW status shows `originalDate → personalDate` arrow format.

### Session 32 — Aleksei Smirnov (Regular Employee, Cyprus, QA-1)

**Build**: 2.1.26-SNAPSHOT.290209 (QA-1 environment)

**Table columns**: Same 6 columns as above. Year selector present.

**Row data (2026)**: 6 rows for Cyprus public holidays (fewer than Russia's 17). All status "Approved". Holidays include May Day (01.05), Greek Easter Monday, Cyprus National Day, etc.

**Edit pencil**: Present on future holidays with duration=0 (same logic as Russian office).

**BUG-DO-11 confirmed live**: Overdue day-off warning banner appears for Aleksei Smirnov (regular employee with no approver role). Clicking the banner link navigates to /vacation/request/daysoff-request/APPROVER which returns 403. Warning should only show to users with pending approval authority.

**Screenshots**: 
- `artefacts/dayoff-employee-table-2026.png` — Full table view

## TransferDaysoffModal (Reschedule) — Deep Dive (Session 32)

### Code Analysis (TransferDaysoffModal.tsx)

**minDate logic** (lines 127-129):
```
isMinCurrentDay = moment().isAfter(moment(originalDate))
minDate = isMinCurrentDay ? moment().subtract(1, 'd') : moment(originalDate)
```
- Future holidays: minDate = originalDate (can't pick earlier)
- Past holidays: minDate = yesterday (allows selecting today onward)

**maxDate logic** (lines 50-52):
```
maxDate = moment(originalDate).add(1, 'year').endOf('year')
```
- Always Dec 31 of year after originalDate's year
- E.g., May Day 2026 → maxDate = 2027-12-31; Christmas 2026 → maxDate = 2027-12-31

**renderDay disabled logic** (lines 58-98):
1. Weekends (Sat/Sun) → disabled grey
2. Dates matching existing dayoff personalDates → disabled (prevents double-booking)
3. Short-day conflicts (calendar day with duration=7 and matching personalDate) → disabled
4. **Exception**: Working weekends (calendar entries marking Sat/Sun as working) → re-enabled

### UI Validation vs API Gap
UI blocks weekend selection via renderDay, but API endpoint accepts weekend personalDate without validation (**BUG-DO-5**). Critical for test cases: UI-only tests miss the validation gap.

### Live Observation (QA-1, Aleksei Smirnov)

**Modal structure**: Title "Reschedule an event", read-only "Day off date" field (original), full calendar month-view datepicker, Cancel + OK buttons.

**OK button**: Disabled until valid date selected. Enables immediately on valid click.

**Arrow format**: After selection shows "01.05.2026 → 11.05.2026" (originalDate → selectedDate).

**Past dates**: Dates before minDate are greyed/unresponsive. No error message — silently ignored.

**Calendar navigation**: Left/right arrows to change months. Month/year header clickable for broader navigation.

**Screenshots**:
- `artefacts/dayoff-reschedule-modal-empty.png` — Empty modal state
- `artefacts/dayoff-reschedule-modal-selected.png` — With May 11 selected
- `artefacts/dayoff-reschedule-march-calendar.png` — Past dates disabled
- `artefacts/dayoff-reschedule-jan2027.png` — Future year navigation

## Page 2: /vacation/request → Days off rescheduling — Manager View (Session 4)

**Title**: "Employees' requests". Two top-level tabs: Vacation requests (N) | Days off rescheduling (N).

**5 sub-tabs**: Approval | Agreement | My department | My projects | Redirected

**Table columns (shared across sub-tabs)**: Employee | Initial date (default sort desc) | Requested date | Manager | Approved by | Agreed by | Status (filterable on MY_DEPARTMENT) | Actions

**Actions**: Info/details icon (always shown) → opens "Request details" modal. Approve/Reject/Redirect icons (when status=NEW AND user is approver). Optional approve/reject (when user is optional approver).

**Status filter values**: Approved, NEW, Rejected.

**Pagination**: 20 items/page. 3 pages on My department tab.

## Request Details Modal (Session 4)

Shows: Employee (CS link), Manager (CS link), Reason, Initial date (YYYY-MM-DD), Requested date, Status.

**"Agreed by" sub-table**: Shows optional approver chain with individual statuses (e.g. Requested, Agreed).

## Behavioral Findings

1. **Navigation bug**: Clicking "Days off" tab button on /vacation/my sometimes navigates to /sick-leave/my instead of /vacation/my/daysoff. Direct URL works correctly. (S4)
2. **Edit button conditional**: Only future public holidays with duration=0 (not weekends) get the edit pencil. Past and short-day (7h) rows have no actions. (S4)
3. **Overdue warning banner**: Global warning for managers with pending day-off approvals, links to /vacation/request/daysoff-request/APPROVER. **BUG-DO-11**: Also shown to regular employees who get 403 on the target page. (S4 discovery, S32 live confirmation)
4. **"Agreed by" empty in table**: Optional approval values only visible in details modal, not in main table column. (S4)
5. **OK disabled until date selected**: TransferDaysoffModal OK starts disabled, enables after valid date pick. (S32)
6. **UI-only weekend blocking**: Calendar disables weekends but API doesn't validate — UI-bypass attacks possible. (S32 code analysis)
7. **Localization**: Reasons display in Russian even in EN mode. (S4, BUG-DO-12)

Links: [[frontend-day-off-module]], [[day-off-service-implementation]], [[vacation-pages]], [[app-navigation]], [[sick-leave-dayoff-business-rules-reference]]

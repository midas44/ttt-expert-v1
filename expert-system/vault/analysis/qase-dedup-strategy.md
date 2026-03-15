---
type: analysis
tags:
  - qase
  - deduplication
  - phase-b
  - test-planning
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[analysis/vacation-business-rules-reference]]'
  - '[[analysis/reports-business-rules-reference]]'
  - '[[analysis/sick-leave-dayoff-business-rules-reference]]'
---
# Qase Deduplication Strategy for Phase B

**Qase TIMEREPORT project:** 258 suites, 1116 test cases, all manual (automation=0).

## Existing Qase Coverage Map

### Well-Covered Areas (avoid duplication)
- **My Tasks** (suite 1): 9 general + 10 task creation + 9 comments + 8 rename + 8 time reporting + color indicators (28 cases) + 5 rejected block + 3 alerts = ~80 cases
- **Employee Tasks** (suite 22): 12 PM reports + 9 manager reports + 3 admin + color indicators = ~55 cases
- **Vacations** (suite 36): Deep coverage — My Vacations (employee CRUD, view/create/edit/cancel/restore/delete = ~90 cases), Vacation Requests (chart, filters ~30), vacation day events (hire/fire/maternity/new year/correction = ~40), notifications (~40) = ~200+ cases
- **Confirmation** (suite 131): By-employee (filters, approve, reject, comments, color, table = ~80), By-project (~60) = ~140+ cases
- **Planner** (suite 157): Tasks (generated/non-generated, tables ~50), Projects (members, tracker ~30), ticket refresh = ~80 cases
- **Admin** (suite 183): Projects (All/My/Create/Edit/Info/History/Transfer = ~70), Employees (~12), Parameters (~10), Calendars (~20), API (~2) = ~115 cases

### Weak/Empty in Qase (our primary generation targets)
- **Statistics** (suite 182): 0 cases — our major value-add
- **Sick Leave**: Only in color indicator sub-suites (~9 cases) — needs comprehensive standalone coverage
- **Day-Off**: Only in calendar day-off transfers (~12 cases) — needs full lifecycle
- **Accounting**: No dedicated suite — salary, vacation payout, days correction, periods
- **PM Tool Integration**: No coverage — new sync architecture
- **Email/Notifications**: Scattered across suites — needs consolidation
- **Security/Auth**: No coverage — JWT/API token, permissions
- **Tracker Integration**: No dedicated coverage beyond planner ticket errors

## Deduplication Strategy

### Rule 1: Check Before Generate
Before generating test cases for any area, query Qase for that module/feature:
- `list_cases(suite_id=X)` for the relevant suite
- Compare case titles with planned test coverage
- Skip or mark as "exists in Qase" any overlapping cases

### Rule 2: Complement, Don't Duplicate
Our XLSX test cases should:
- Focus on areas NOT in Qase (Statistics, Sick Leave, Day-Off, Accounting, Security)
- For overlapping areas (Vacations, Confirmation), generate only cases that test **business rules, edge cases, API-level behavior** not covered by existing UI-focused Qase cases
- Include explicit "Qase ref" column noting related Qase suite/case IDs where overlap exists

### Rule 3: Priority Generation Order
1. **Statistics** — 0 Qase cases, full vault knowledge
2. **Sick Leave** — 9 Qase cases vs. 8 known bugs, complex lifecycle
3. **Day-Off** — 12 Qase cases vs. 15 known bugs, 4 calendar conflict paths
4. **Accounting** — 0 Qase cases, period management + payment flow
5. **Vacations** — supplement existing 200+ cases with API/edge/business rule cases
6. **Security/Auth** — 0 Qase cases, new auth doc + permission matrix
7. **Reports** — supplement existing with confirmation edge cases, period advance/revert
8. **Admin** — supplement existing with PM Tool sync, close-by-tag permissions

## XLSX Generation Pipeline

1. `openpyxl 3.1.5` — verified available
2. Template: `expert-system/output/test-plan-<module>.xlsx` + `test-cases-<module>.xlsx`
3. Per §11 format requirements: professional formatting, filters, alternating rows
4. Track in `test_case_tracking` SQLite table

See also: [[analysis/qase-coverage-detailed-mapping]], [[analysis/vacation-business-rules-reference]]

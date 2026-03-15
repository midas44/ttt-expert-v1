---
type: analysis
tags:
  - qase
  - test-coverage
  - phase-b-prep
  - deduplication
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[qase-overview]]'
  - '[[frontend-sick-leave-module]]'
  - '[[frontend-day-off-module]]'
  - '[[frontend-statistics-module]]'
  - '[[frontend-accounting-module]]'
---
# Qase Test Coverage — Detailed Mapping for Phase B Deduplication

Granular analysis of existing Qase test cases per module to prevent duplication during Phase B generation. Suite IDs reference TIMEREPORT project.

## Statistics (Suite 182) — 0 cases
Completely empty. No sub-suites. **Full generation needed.**

## Sick Leave — ~57 related cases (0 lifecycle CRUD)
Existing cases cover only display effects and notifications, NOT the sick leave creation/editing/closing workflow:

| Area | Suites | Cases | Content |
|------|--------|-------|---------|
| Color indication (My Tasks) | 18 | 3 | Open/Closed/Deleted SL display |
| Color indication (Employee Tasks) | 34 | 3 | Same for manager view |
| Confirmation table (by employees) | 142 | 3 | SL display in confirmation |
| Confirmation table (by projects) | 153 | 3 | SL display in confirmation |
| Planner tasks | 162 | 3 | SL display in planner |
| Planner projects | 176 | 3 | SL display in planner |
| Email notifications | 248 | 14 | SL notification emails |
| Accounting: sort/filter | 230 | 11 | SL accounting table filters |
| Accounting: table | 231 | 6 | SL accounting table display |
| Accounting: actions column | 232 | 4 | Action buttons |
| Accounting: actions | 233 | 2 | Accept/reject actions |
| Accounting: alerts | 234 | 2 | Overdue SL alerts |
| My Sick Leaves | 273 | 0 | Empty placeholder |
| Employee Sick Leaves | 276 | 0 | Empty placeholder |

**Gaps for generation**: Create, edit dates, close, delete, reject, reopen, file upload, number validation, dual status model (status × accounting_status), role-based visibility, API CRUD.

## Day-Off — ~19 related cases (0 request lifecycle)
All cases are about dayoff transfers (calendar shifts), not the day-off request workflow:

| Area | Suites | Cases | Content |
|------|--------|-------|---------|
| Dayoff transfers (My Tasks) | 17 | 2 | Transfer display |
| Dayoff transfers (Employee Tasks) | 33 | 2 | Same for manager |
| Confirmation (by employees) | 144 | 2 | Transfer in confirmation |
| Confirmation (by projects) | 156 | 2 | Transfer in confirmation |
| Planner tasks | 165 | 2 | Transfer in planner |
| Planner projects | 175 | 2 | Transfer in planner |
| Email notifications | 247 | 7 | Transfer notifications |
| My Days Off (Выходные) | 271 | 0 | Empty placeholder |

**Gaps for generation**: Create request, approval/rejection, rescheduling (4 conflict paths), calendar conflict resolution, multi-day requests, reason field, role-based visibility, API CRUD.

## Accounting (Suite 207) — ~127 cases (substantial coverage)
Previously estimated at 0 — CORRECTED to ~127:

| Area | Suites | Cases | Content |
|------|--------|-------|---------|
| Salary: search | 209 | 2 | Payroll search |
| Salary: filters | 210 | 8 | Filter by period/office |
| Salary: table | 211 | 6 | Table display/sorting |
| Period changes | 212-214 | 14 | Individual + sorting |
| Vacation payment: table | 215-217 | 26 | Table + sorting |
| Vacation payment: pay | 218-221 | 20 | Single + batch payment |
| Vacation day correction | 222-228 | 22 | Correction + event feed |
| Sick leave accounting | 229-234 | 27 | Sort/filter + actions + alerts |

**Gaps**: Period advance/revert error cases, edge cases in payment (already-paid, cross-period), notification triggers on period change, API-level operations.

## Revised Phase B Generation Priority
1. **Statistics** — 0 Qase cases, full generation
2. **Sick Leave lifecycle** — 0 lifecycle cases despite 57 display/notification cases
3. **Day-Off lifecycle** — 0 lifecycle cases despite 19 display cases
4. **Security/Permissions** — 0 cases
5. **Accounting supplements** — 127 existing, fill gaps
6. **Vacations supplements** — 200+ existing, fill gaps
7. **Reports supplements** — existing coverage, fill gaps
8. **Admin supplements** — 115 existing, fill gaps

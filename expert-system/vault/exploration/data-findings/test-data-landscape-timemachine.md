---
type: exploration
tags:
  - test-data
  - timemachine
  - phase-b-prep
  - data-findings
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[frontend-vacation-module]]'
  - '[[frontend-sick-leave-module]]'
  - '[[frontend-day-off-module]]'
  - '[[frontend-accounting-module]]'
  - '[[frontend-report-module]]'
  - '[[frontend-statistics-module]]'
---
# Test Data Landscape — Timemachine Environment

Reference for Phase B test case generation: describes available test data, user accounts, and data distribution for constructing test preconditions and input data.

## Employees (ttt_backend.employee)
- **Total**: 1841 (410 enabled, 1431 disabled)
- **Contractors**: 159
- **Being dismissed**: 7

### Role Distribution (employee_global_roles)
| Role | Count |
|------|-------|
| ROLE_EMPLOYEE | 1683 |
| ROLE_CONTRACTOR | 159 |
| ROLE_PROJECT_MANAGER | 136 |
| ROLE_OFFICE_HR | 50 |
| ROLE_DEPARTMENT_MANAGER | 29 |
| ROLE_TECH_LEAD | 19 |
| ROLE_ACCOUNTANT | 18 |
| ROLE_VIEW_ALL | 13 |
| ROLE_ADMIN | 8 |
| ROLE_CHIEF_ACCOUNTANT | 2 |
| ROLE_CHIEF_OFFICER | 1 |

### Key Multi-Role Test Users (enabled, 4+ roles)
- **perekrest** (7 roles): ACCOUNTANT, ADMIN, CHIEF_ACCOUNTANT, DEPT_MGR, EMPLOYEE, HR, PM
- **pvaynmaster** (7 roles): ACCOUNTANT, ADMIN, CHIEF_OFFICER, DEPT_MGR, EMPLOYEE, HR, PM
- **ilnitsky** (6 roles): ACCOUNTANT, ADMIN, DEPT_MGR, EMPLOYEE, HR, PM
- **ann** (6 roles): ACCOUNTANT, ADMIN, DEPT_MGR, EMPLOYEE, HR, PM
- **juliet_nekhor** (5 roles): DEPT_MGR, EMPLOYEE, HR, PM, VIEW_ALL
- **kcherenkov** (4 roles): DEPT_MGR, EMPLOYEE, PM, TECH_LEAD

## Offices / Salary Offices (28 offices)
Top offices by employee count (ttt_vacation.employee_office):
| Office | Name | Employees |
|--------|------|-----------|
| 2 | Сатурн | 2093 |
| 10 | Венера | 1642 |
| 4 | Юпитер | 1539 |
| 27 | Венера (РФ) | 476 |
| 19 | Андромеда | 88 |
| 11 | Нептун | 85 |

## Production Calendars (10)
Russia (275 holidays), Cyprus (40), Vietnam (39), France (29), Germany (29), Montenegro (27), Uzbekistan (25), Georgia (22), Armenia (17), Empty (0).

## Office Periods (as of session date)
Most offices: REPORT period starts 2026-03-01, APPROVE period starts 2026-02-01. Exception: office 9 ("Не указано") stuck at 2020-03-01.

## Projects (ttt_backend.project)
- **Total**: 3138 (200 ACTIVE, 2869 FINISHED, 59 CANCELED, 10 SUSPENDED)
- **Tasks**: 666,629 across 3,061 projects

## Vacations (ttt_vacation.vacation)
- **Total**: 14,199
- Status: PAID 13,412 | APPROVED 187 | NEW 81 | REJECTED 60 | DELETED 459
- All period_type = EXACT
- Payment types: REGULAR 12,455 | ADMINISTRATIVE 1,744
- Date range: 2013-08-19 to 2026-12-28
- March 2026: ~30+ active vacations

## Sick Leaves (ttt_vacation.sick_leave)
- **Total**: 349
- Status × Accounting: CLOSED/NEW 215 | CLOSED/PAID 96 | DELETED/NEW 17 | REJECTED/REJECTED 13 | OPEN/NEW 8
- All 349 have `number` field populated
- Date range: 2023-02-06 to 2026-03-16

## Day-Off Requests (ttt_vacation.employee_dayoff_request)
- **Total**: 3,241
- Status: APPROVED 2,902 | DELETED 226 | DELETED_FROM_CALENDAR 82 | NEW 17 | REJECTED 14
- Day-off records (employee_dayoff): 5,340 across 415 employees (2024-01-01 to 2026-12-25)

## Task Reports (ttt_backend.task_report)
- **Total**: 3,568,066
- Date range: 2010-06-01 to 2026-04-03
- States: APPROVED 23,557 | REPORTED 2,332 (Feb-Mar 2026)
- March 2026: 2,694 reports by 214 employees

## Statistic Reports (ttt_backend.statistic_report)
- **Total**: 9,662 covering 469 employees
- Date range: 2025-01-01 to 2026-12-01

## Test Data Generation Strategies

### For Vacation Tests
- Use enabled employees with ROLE_EMPLOYEE who are NOT on maternity
- Pick employees from offices with REPORT period in current month (all except office 9)
- Create vacations starting after current report period start date
- Available statuses to create: NEW (via API POST)
- For approval tests: use employee's manager (approver field)

### For Sick Leave Tests
- Create via API with employee ID, start_date, end_date
- Close by PATCH with number field
- Accounting workflow: accountant accepts/rejects
- 8 OPEN sick leaves available for testing close/accounting flows

### For Day-Off Tests
- Create via vacation API with employee ID, original_date, duration, reason
- 17 NEW requests available for approval/rejection testing
- Rescheduling: change personal_date (requires calendar conflict check)

### For Report Tests
- Use employees assigned to ACTIVE projects with tasks
- Report in current REPORT period (March 2026)
- States flow: REPORTED → APPROVED (via confirmation)

### For Accounting Tests
- Period advance/revert via accounting API
- Vacation payment: 187 APPROVED vacations available for payment
- Sick leave accounting: 8 OPEN sick leaves for processing

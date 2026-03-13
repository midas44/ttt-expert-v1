---
type: exploration
tags:
  - data
  - database
  - timemachine
  - enums
  - statistics
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[database-schema]]'
  - '[[vacation-service]]'
  - '[[ttt-service]]'
branch: release/2.1
---
# Database Data Overview (Timemachine)

Data scale and business enum values from timemachine environment.

## Record Counts

| Table | Count | Notes |
|-------|-------|-------|
| ttt_backend.employee | 1,841 | All employees (active+inactive) |
| ttt_backend.task_report | 3,568,066 | Core reporting data — largest table |
| ttt_backend.task | 666,628 | Tasks across all projects |
| ttt_backend.project | 3,138 | All projects |
| ttt_vacation.employee | 1,609 | Vacation service employee mirror |
| ttt_vacation.vacation | 14,195 | All vacation requests |
| ttt_vacation.sick_leave | 348 | Sick leave records |
| ttt_vacation.employee_dayoff | 5,334 | Day-off records |
| ttt_email.email | 660 | Email records |
| ttt_calendar.calendar | 10 | Production calendars |

## Business Enums

### Vacation Statuses
NEW → APPROVED → PAID (happy path)
NEW → REJECTED
NEW → DELETED (cancelled)
APPROVED → DELETED (cancelled after approval)

### Vacation Payment Types
- REGULAR — paid vacation days
- ADMINISTRATIVE — unpaid (administrative leave / за свой счёт)

### Vacation Period Type
- EXACT — only value observed (specific date range)

### Sick Leave Statuses
OPEN → CLOSED (happy path)
OPEN → REJECTED
OPEN → DELETED

### Sick Leave Accounting Statuses
NEW → PAID
NEW → REJECTED

### Task Report States
REPORTED → APPROVED (happy path)
REPORTED → REJECTED

## Key Observations
- Employee count mismatch (1841 vs 1609) — backend has more employees than vacation service, likely due to sync timing or contractors
- Task reports table is massive (3.5M) — performance-critical
- Unique constraint on task_report(task, executor, report_date) — one report per task per person per day
- Vacation has separate regular_days and administrative_days columns — mixed-type vacations possible
- Sick leave has dual status tracking: `status` (lifecycle) and `accounting_status` (payment)

## Related
- [[database-schema]]
- [[vacation-service]]
- [[ttt-service]]

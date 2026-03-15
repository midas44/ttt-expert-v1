---
type: exploration
tags:
  - database
  - ttt-backend
  - schema
  - task-report
  - planner
  - period
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[architecture/database-schema]]'
  - '[[analysis/office-period-model]]'
  - '[[modules/ttt-service]]'
branch: release/2.1
---
# TTT Backend Schema Deep Dive

Analysis of `ttt_backend` schema on timemachine environment. 40 tables, dominated by task_report (3.57M rows, 1.5GB).

## Core Data Tables

### task_report (3.57M rows, 1.5GB)
Central table. Columns: id, task (FK), executor (FK employee), reporter (FK employee), approver (FK employee), reject (FK), state, actual_efforts (bigint — minutes), report_date, last_reported, comment.

**States**: APPROVED (3.56M, 99.9%), REPORTED (2.5K), REJECTED (963). Simple 3-state lifecycle: REPORTED → APPROVED or REJECTED. Unique constraint: (task, executor, report_date) — one report per task per employee per day.

### task (667K rows, 361MB)
Columns: id, project (FK), name (unique case-insensitive via `upper(name)` index), ticket_url, ticket_name, ticket_info, created_time, last_reported_time, creator (FK), bound_employee (FK — personal tasks), is_project_open.

Trigram GIN index on name for fuzzy search. Ticket URL indexed for tracker integration lookups.

### task_assignment (2.57M rows, 594MB) — Planner
Columns: id, assignee (FK), task (FK), assigner (FK), remaining_estimate, comment, internal_comment, date, next_assignment (FK self — **linked list**), closed, ui_data, updated_time, show_in_history, position.

**Linked list pattern** via `next_assignment` self-FK — this is why planner ordering bugs (#3308, #3332) are persistent. Position column added later as alternative. Unique: (assignee, task, date).

### tracker_work_log (222K rows, 52MB)
External tracker hours imported from JIRA/GitLab/ClickUp.

## Organizational Tables

### office (32 rows)
28 active salary offices. Names are celestial bodies (Сатурн, Юпитер, Венера etc.) with geographic suffixes (РФ, Уз, Франция, СПб, Нск).

### office_period (56 rows = 28 offices × 2 types)
Two period types per office:
- **REPORT** — start_date of current open reporting month (mostly 2026-03-01)
- **APPROVE** — start_date of current approval month, always one month behind REPORT (mostly 2026-02-01)

Exception: "Не указано" (Not specified) office frozen at 2020-03-01 — likely a catch-all/default.

Columns: id, office (FK), type, start_date. Unique: (office, type).

### employee (1.8K rows)
Columns: id, login (unique), settings (FK), company_staff_id, salary_office (FK), senior_manager, tech_lead, plus name fields (russian/latin first/last). Multiple trigram GIN indexes for fuzzy name search in both Russian and Latin.

### project (3.1K rows)
Columns: id, name (unique), manager (FK), senior_manager (FK), old_owner (FK). Trigram GIN on name.

## Rejection Workflow

### reject (1.9K rows)
Columns: id, rejector (FK employee), description, created_time, executor_notified.

**Data anomaly**: Recent rejects have NULL created_time and NULL description — suggests auto-rejection (system-generated) doesn't populate these fields. `executor_notified` is FALSE for recent entries — notification may be pending or the auto-reject notification path is different.

### rejected_week
Columns: id, employee (FK). Tracks which employees have rejected weeks (for notification/display purposes).

## Supporting Tables

| Table | Rows | Purpose |
|-------|------|---------|
| statistic_report | 9.7K | **NEW S15**: Caching table for employee stats. Cols: employee_login, report_date, reported_effort, month_norm, budget_norm, comment |
| fixed_task | 4.3K | Pinned tasks per employee (PK: task+employee) |
| budget_notification | 1.3K | Over-budget alerts. FKs: employee, project, task, watcher |
| project_member | 423 | Project ↔ employee membership |
| employee_managers | — | Employee ↔ manager relationships |
| office_accountants/managers/hrs | — | Office role assignments |
| employee_tracker_credentials | — | Per-employee tracker auth (unique: employee+tracker_url) |
| planner_close_tag | — | Planner closed tags per project |
| pm_sync_status / pm_tool_sync_failed_entity | — | **NEW S15**: PM Tool sync tracking |
| cs_sync_status / cs_sync_failed_entity | — | CompanyStaff sync tracking |
| shedlock | 13 | Distributed lock for scheduled tasks |
| token / token_permissions | — | API token system (4.8MB permissions!) |

## Key Patterns

1. **Employee references by ID** (bigint FK) in ttt_backend vs **by login** (text) in ttt_vacation — cross-service join requires employee table lookup
2. **Trigram GIN indexes** on employee names and project names — supports autocomplete/suggest API
3. **Linked list for planner ordering** — fragile pattern, explains persistent ordering bugs
4. **Dual period system** per office — REPORT always one month ahead of APPROVE
5. **statistic_report as materialized view** — new denormalized caching layer from Sprint 15

See also: [[architecture/database-schema]], [[analysis/office-period-model]], [[modules/ttt-service]], [[exploration/data-findings/vacation-schema-deep-dive]]


## Employee Model Details

### employee (1,841 rows)
33 columns. Key fields beyond basics:
- **Lifecycle**: enabled, being_dismissed, read_only, last_date
- **Maternity**: maternity_start_date, maternity_end_date (10 employees with maternity records, some with no end_date = ongoing)
- **Contractor**: is_contractor, contractor_manager_id
- **Management**: senior_manager, tech_lead, hr, is_employees_manager, is_cs_manager
- **Org**: department_type, specializations, salary_office (FK)
- **Localization**: language, city_ru, city_en, russian/latin first/last names
- **Dedup**: is_name_duplicate (for display disambiguation)

**Active counts**: 378 regular employees + 26 contractors active. 1,298 regular + 132 contractor disabled. 7 being dismissed.

### Roles Distribution (from employee_global_roles)
| Role | Count |
|------|-------|
| ROLE_EMPLOYEE | 1,683 |
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

### work_period (876 rows)
Tracks employment start/end dates. Some employees have 2 periods (left and returned). Data goes back to 2003. Critical for individual norm calculations (#3353) — determines when employee was/wasn't employed.

### employee_extended_period
Columns: employee (unique), deadline, created_by. Tracks individual reporting deadline extensions.

## Scheduled Tasks (from shedlock)

**Active (running on timemachine 2026-03-12):**
1. `LockServiceImpl.cleanUpCache` — frequent cache cleanup
2. `TaskReportNotificationScheduler.sendRejectNotifications` — every hour at :10
3. `ExtendedPeriodScheduler.cleanUp` — every hour at :10
4. `BudgetNotificationScheduler.sendBudgetNotifications` — every hour at :00
5. `PmToolSyncScheduler.doPmToolSynchronization` — every hour at :00
6. `CSSyncScheduler.doCsSynchronization` — every hour at :00
7. `TaskReportNotificationScheduler.sendReportsForgottenDelayedNotifications` — daily at 09:30
8. `TaskReportNotificationScheduler.sendReportsChangedNotifications` — daily at 00:50
9. `StatisticReportScheduler.sync` — daily at 21:00 (populates statistic_report cache)
10. `TaskReportNotificationScheduler.sendReportsForgottenNotifications` — workdays at 09:00

**Legacy (inactive — CS sync evolution):**
- `CompanyStaffScheduler` (2023) → `CSSyncLauncher` (2024-04) → `CSSyncScheduler` + `CSFullSyncScheduler` (current)

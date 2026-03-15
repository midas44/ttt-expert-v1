---
type: exploration
tags:
  - database
  - ttt-backend
  - schema
  - data-quality
  - code-verified
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[exploration/data-findings/ttt-backend-schema-deep-dive]]'
  - '[[architecture/database-schema]]'
  - '[[modules/ttt-service]]'
  - '[[architecture/security-patterns]]'
branch: release/2.1
---
# TTT Backend — Remaining Tables Deep-Dive

Code-verified analysis of previously uncovered tables in ttt_backend schema (timemachine).

## Key Tables Analyzed

### token_permissions (38,554 rows)
- Join table for API token → permission mapping
- 22 flat permission strings per token (ApiPermission enum values)
- `permissions_idx` column ALL NULL (Hibernate @ElementCollection artifact — dead column)
- CALENDAR_* permissions added later — only ~50% of tokens have them

### project_event (7,479 rows)
- Audit trail for project changes
- Denormalized: stores before/after text values, not structured diffs
- Useful for tracking project state history but hard to query systematically

### budget_notification (1,332 rows)
- Only 5 unique watchers monitoring 6 employees across 8 projects
- 99.4% use percentage-based thresholds (not absolute)
- Only 7 notifications ever triggered (reached_date populated)
- Feature exists but extremely low real-world activation

### work_period (876 rows)
- **Legacy table** — employment period tracking
- 32 records have `start_date = 0002-11-30` (sentinel/default, never cleaned)
- Being replaced by CS sync data

### fixed_task (4,324 rows)
- Pinned/favorite tasks per employee
- FK to task table, used by planner "pin" feature

### reject (1,910 rows)
- 1:1 with rejected task_reports
- `description` field almost universally NULL — rejectors don't explain reasons
- Only 0.05% of 3.57M task_reports have been rejected

### rejected_week (106 rows)
- **Deprecated** — old rejection model (entire week rejected)
- Data ends Feb 2020, replaced by per-report `reject` table

### application_settings (18 rows)
- System-wide key-value configuration
- Key params: notification emails, reporting thresholds (over: 10%, under: -10%), extended period duration (60 min)

### shedlock (13 entries)
- Distributed scheduling locks (3 deprecated entries from 2023-2024)
- Active locks for all current scheduled jobs

### 12 Empty Tables
pm_sync_status, pm_tool_sync_failed_entity, cs_sync_failed_entity, employee_work_period, employee_extended_period, office_managers, planner_close_tag, and others — new features not yet active or deprecated features.

## Data Quality Issues (8)

1. **work_period sentinel dates**: 32 rows with `start_date = 0002-11-30`
2. **project_member.role chaos**: 120+ distinct values, typos, mixed RU/EN
3. **project_member.access_type**: Universally NULL — dead column
4. **Missing unique constraints**: project_observers, employee_managers join tables
5. **statistic_report denormalization**: employee_login text instead of FK
6. **Dual FK on reject.rejector**: redundant constraint (migration artifact)
7. **token_permissions.permissions_idx**: all NULL, Hibernate artifact
8. **office_managers empty**: table exists but never used

## Architecture Patterns
- **Flyway**: 142 migrations (V1.0 through V2.1.27, latest 2026-03-11)
- **ShedLock**: distributed scheduling across Docker container instances
- **Legacy retention**: old tables kept alongside replacements

---
type: architecture
tags:
  - database
  - schema
  - postgresql
created: '2026-03-12'
updated: '2026-03-13'
status: active
related:
  - '[[system-overview]]'
  - '[[ttt-service]]'
  - '[[vacation-service]]'
branch: release/2.1
---
# Database Schema

Single PostgreSQL 12.2 database `ttt` with 4 service schemas (86 tables total).

## ttt_backend (40 tables)
Core time tracking data.

**Employee & Roles:**
employee, employee_global_roles, employee_managers, employee_settings, employee_tracker_credentials, employee_work_period, employee_extended_period, managers_watched_employees

**Projects & Tasks:**
project, project_member, project_observers, project_event, task, task_assignment, task_report, task_template, fixed_task, tracker_work_log

**Offices & Periods:**
office, office_accountants, office_hrs, office_managers, office_period, work_period

**Reports & Approvals:**
statistic_report, reject, rejected_week, forgotten_report_notification

**Planning & Notifications:**
planner_close_tag, budget_notification, message

**Sync:**
cs_sync_status, cs_sync_failed_entity, pm_sync_status, pm_tool_sync_failed_entity

**System:**
application_settings, token, token_permissions, schema_version, shedlock

## ttt_vacation (32 tables)
Absence management.

**Vacations:**
vacation, vacation_approval, vacation_days_distribution, vacation_notify_also, vacation_payment, vacation_status_updates, employee_vacation, confirmation_period_days_distribution, scheduled_vacation_notification

**Days Off:**
employee_dayoff, employee_dayoff_approval, employee_dayoff_request

**Sick Leaves:**
sick_leave, sick_leave_file, sick_leave_notify_also

**Employee & Office:**
employee, employee_office, employee_period, employee_projects, office, office_accountants, office_annual_leave, office_notification_receiver, office_sick_leave_notification_receiver

**Other:**
timeline, file, delayed_digest_notification, java_migration, cs_sync_status, cs_sync_failed_entity, schema_version, shedlock

## ttt_calendar (8 tables)
Calendar management.

calendar, calendar_days, office, office_calendar, cs_sync_status, cs_sync_failed_entity, schema_version, shedlock

## ttt_email (6 tables)
Email notifications.

email, attachment, email_template, email_signature, schema_version, shedlock

## Observations
- Each schema has its own `shedlock` (distributed locking) and `schema_version` (Flyway)
- Employee and office data replicated across schemas (denormalized microservice pattern)
- CS sync tracking in backend, vacation, and calendar schemas — each service syncs independently
- Vacation schema is the most complex absence schema — vacations, day-offs, sick leaves each with approval workflows

## Related
- [[system-overview]]
- [[ttt-service]]
- [[vacation-service]]
- [[calendar-service]]
- [[email-service]]

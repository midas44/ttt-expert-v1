---
type: exploration
tags:
  - email
  - notifications
  - templates
  - field-mapping
  - per-template
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[patterns/email-notification-triggers]]'
  - '[[exploration/data-findings/email-templates-inventory]]'
  - '[[modules/email-service]]'
  - '[[modules/vacation-service]]'
  - '[[ttt-service]]'
branch: release/2.1
---
# Email Template Per-Field Mapping

Complete mapping of all 120 email templates → Mustache variables → Java injection source. 50 legacy + 70 new (NOTIFY_*). Only `BASE_TTT_TEMPLATE` has no variables.

## Rendering Engine

`EmailTemplateServiceImpl.render()` — Mustache compilation. Data arrives as JSON string, converted to `Map<String, Object>`. Supports `{{var}}`, `{{#section}}...{{/section}}`, `{{.}}` (current item).

## Vacation Templates (50 legacy + new combined)

### Base Variables (injected by `AbstractVacationNotificationHelper.fillBaseInfo()`)

All new NOTIFY_VACATION_* templates inherit these:

| Variable | Source | Format |
|----------|--------|--------|
| `employee` | VacationBO → employeeBO.russianFullName | Russian full name |
| `approver` | VacationBO → approverBO.russianFullName | Russian full name |
| `department_manager` | VacationBO → seniorManagerBO.russianFullName | "-" if null |
| `type` | VacationBO.type | "Очередная" / "Административная" |
| `status` | VacationBO.status | "Новая"/"Подтверждена"/"Отклонена"/"Отменена"/"Оплачена" |
| `period_start` | VacationBO.startDate | "DD Month YYYY" (Russian months) |
| `period_end` | VacationBO.endDate | "DD Month YYYY" |
| `regular_days` | VacationBO.regularDays | Integer |
| `administrative_days` | VacationBO.administrativeDays | Integer |
| `payment_date` | VacationBO.paymentDate | "Month/Year" or "" |
| `comment` | VacationBO.comment | String or "" |
| `to_name` | Recipient's russianFullName | Russian full name |
| `confirmation_url` | Hardcoded | "https://ttt.noveogroup.com/vacation/request" |

### Per-Event Template Variants

**CREATE** (4 recipients): `NOTIFY_VACATION_CREATE_TO_{EMPLOYEE,MANAGER,SENIOR_MANAGER,ALSO}`
- EMPLOYEE: base + `administrative_days, comment, department_manager, payment_date, regular_days, type`
- MANAGER: `department_manager, employee, period_start, period_end, to_name`
- SENIOR_MANAGER: base + `confirmation_url`
- ALSO: `employee, period_start, period_end, to_name`

**CHANGE** (5 recipients): `NOTIFY_VACATION_CHANGE_TO_{EMPLOYEE,MANAGER,SENIOR_MANAGER,APPROVER,ALSO}`
- APPROVER adds: `confirmation_url, department_manager`
- Others: same pattern as CREATE variants

**STATUS_CHANGE** (4 recipients): `NOTIFY_VACATION_STATUS_CHANGE_TO_{EMPLOYEE,MANAGER,SENIOR_MANAGER,ALSO}`
- Additional: `action` ("подтвердил(а)" / "удалил(а)" / "отклонил(а)"), `approver`

**DELETE_CANCEL** (5): `NOTIFY_VACATION_DELETE_CANCEL_TO_{EMPLOYEE,MANAGER,SENIOR_MANAGER,APPROVER,ALSO}`
- Additional: `action`

**AUTODELETE** (5): `NOTIFY_VACATION_AUTODELETE_TO_{EMPLOYEE,MANAGER,SENIOR_MANAGER,APPROVER,ALSO}`

**RECOVERED** (5): `NOTIFY_VACATION_RECOVERED_TO_{EMPLOYEE,MANAGER,SENIOR_MANAGER,APPROVER,ALSO}`

**CHANGE_APPROVER** (3): `NOTIFY_VACATION_CHANGE_APPROVER_TO_{EMPLOYEE,APPROVER,SENIOR_MANAGER}`
- Additional: `previous_approver`

### Standalone Vacation Templates

| Template | Variables | Trigger |
|----------|-----------|---------|
| `NOTIFY_VACATION_ABSENCE_LAST_DAY_TO_{EMPLOYEE,MANAGER}` | `to_name, startDate, endDate, localizedType` + `block` list | AvailabilityScheduleNotificationScheduler |
| `NOTIFY_VACATION_ALERT_SOON_VACATION` | `to_name, employee, period_start, period_end` | Approaching vacation date |
| `NOTIFY_VACATION_PUSH_APPROVER` | `to_name, employee, confirmation_url, time_left` | Reminder to approve |
| `NOTIFY_VACATION_SOON_AUTODELETE` | `to_name, period_start, period_end, delete_date, page_link` | Autodelete countdown |
| `NOTIFY_VACATION_GREETINGS_AFTER_VACATION` | `to_name` | First day back |
| `NOTIFY_VACATION_ACCRUALS_BY_HIRE` | `name, days, link` | Annual accrual by hire date |
| `NOTIFY_VACATION_CALENDAR_NEXT_YEAR_{FIRST,LAST}` | `to_name, year, calendars` | Calendar creation notification |

### Calendar Impact Templates

| Template | Variables |
|----------|-----------|
| `NOTIFY_VACATION_CALENDAR_UPDATE_LESS_MIN` | `to_name, period_start, period_end` |
| `NOTIFY_VACATION_CALENDAR_UPDATE_NOT_ENOUGH` | `to_name, period_start, period_end, day, month, page_link` |
| `NOTIFY_VACATION_CALENDAR_UPDATE_0H_DAY_MOVED` | `to_name, from_day, from_month, from_year, to_day, to_month, to_year, day_off_url` |
| `NOTIFY_VACATION_CALENDAR_UPDATE_7H_DAY_MOVED` | Same as above |

## Sick Leave Templates (16 templates)

Three-axis naming: `NOTIFY_SICKLEAVE_{ACTION}[_BY_{ACTOR}]`

### Common Variables (from `SickLeaveNotificationHelper`)

| Variable | Source | Condition |
|----------|--------|-----------|
| `employee` | SickLeaveBO.russianFullName | Always |
| `period_start` | "DD Month YYYY" | Always |
| `period_end` | "DD Month YYYY" | Always |
| `calendar_days` | Total days | Always |
| `sickleave_number` | SickLeaveBO.number | Only if showNumber=true |
| `accountant` | Actor russianFullName | BY_ACCOUNTANT variants |
| `manager` | Actor russianFullName | BY_SUPERVISOR variants |

### Templates by Action

| Action | Self | BY_ACCOUNTANT | BY_SUPERVISOR | To Employee |
|--------|------|---------------|---------------|-------------|
| OPEN | ✓ | — | ✓ | — |
| CLOSED | ✓ | ✓ | ✓ | `_CLOSED_BY_ACCOUNTANT` |
| DATES_CHANGED | ✓ | ✓ | ✓ | `_DATA_CHANGED_BY_ACCOUNTANT` |
| NUMBER_CHANGED | ✓ | ✓ | ✓ | — |
| DELETE | ✓ | — | ✓ | — |
| FILES_ADDED | ✓ | — | — | — |
| REJECTED | — | ✓ | — | `_REJECTED_BY_ACCOUNTANT` |
| OVERLAPS_VACATION | — | — | — | ✓ |

Note: `FILES_ADDED` only uses `employee` variable (minimal template).

## Day-Off Templates (6 templates)

| Template | Variables |
|----------|-----------|
| `NOTIFY_DAYOFF_STATUS_CHANGE_TO_EMPLOYEE` | `to_name, initial_date, requested_date, approver, action` |
| `NOTIFY_DAYOFF_CHANGE_APPROVER_TO_EMPLOYEE` | `to_name, initial_date, requested_date, approver, previous_approver` |
| `NOTIFY_DAYOFF_AUTODELETE_TO_EMPLOYEE` | `to_name, initial_date, requested_date` |
| `NOTIFY_DAYOFF_AUTODELETE_CALENDAR_UPDATE_TO_EMPLOYEE` | `to_name, year, day_off_url` |
| `NOTIFY_CALENDAR_UPDATE_DAYOFF_DELETED_TO_EMPLOYEE` | `to_name, initial_date, from_date, to_date, day_off_url` |

**Key asymmetry**: Day-off notifications only go to employee. No manager/approver/DM fan-out (unlike vacation).

## Reports/Approval Templates (10 templates)

| Template | Variables | Source Class |
|----------|-----------|-------------|
| `APPROVE_REJECT` | `to_name, period_start, period_end, manager, cause, page_link` | RejectNotificationServiceImpl |
| `APPROVE_REJECT_PERIOD_CLOSE` | `to_name` + `{{#block}}{{.}}{{/block}}` (period list) | Period close batch |
| `APPROVE_REQUEST` | `period_start, period_end, approve_page_link` | — |
| `APPROVE_REQUEST_FOR_EMPLOYEE` | `employee_name, period_start, period_end, approve_page_link` | — |
| `FORGOTTEN_REPORT` | `to_name` | TaskReportsForgottenNotificationServiceImpl |
| `STATISTICS_FORGOTTEN_REPORT` | `manager, period_start, period_end` | Period-specific variant |
| `REPORT_SHEET_CHANGED` | `to_name` + nested: `manager, reportDate, taskName, actualEfforts, comment` | TaskReportsChangedNotificationServiceImpl |
| `REJECTED_WEEK_FIX` | `employee, period_start, period_end` | — |
| `EXTENDED_PERIOD_OPENED` | `employee_name, period_start, duration` | Period extension |
| `EXTENDED_PERIOD_CLOSED` | `employee_name, period_start` | Period close |

**`REPORT_SHEET_CHANGED` uses nested model**: `TaskReportUpdateNotificationDataModel` with `managerDateLine[].taskReportLine[]` — Mustache iterates over nested lists.

## Budget/Project Templates (7 templates)

| Template | Variables |
|----------|-----------|
| `BUDGET_NOTIFICATION_EXCEEDED` | `to_name, reached_date, budget, period_start, period_end` + conditional: `{{#project}}`, `{{#task}}`, `{{#user}}` |
| `BUDGET_NOTIFICATION_NOT_REACHED` | Same minus `reached_date` |
| `BUDGET_NOTIFICATION_DATE_UPDATED` | Same as EXCEEDED |
| `PROJECT_CREATE` | `project_name, date, customer, country, senior_manager, manager, status, type, model, presales_urls, redmine_url, creator, sales_manager` (14 vars!) |
| `PROJECT_CLOSE` | `project, date, manager` |
| `REQUEST_TURN_OFF_BONUS` | `employee, project` |

## Employee Lifecycle (5 templates)

| Template | Variables |
|----------|-----------|
| `EMPLOYEE_FIRE` | `employee, manager` |
| `EMPLOYEE_HIRE` | `employee, manager` |
| `EMPLOYEE_NEW` | `employee, vacation_days` |
| `EMPLOYEE_RATING_EVALUATION` | `number` |
| `MANAGER_REASSIGN` | `employee, old_manager, new_manager` |

## Other Templates

| Template | Variables |
|----------|-----------|
| `DIGEST` | Complex: `period, firstName, lastName, name, startDate, endDate, daysCount, mergedDaysCount, daysUntil, comment, vacationApproveURL, dayOffApproveURL, vacationOptionalApproveURL, dayOffOptionalApproveURL, eventsLength` (20,594 bytes — largest template) |
| `HAPPY_BONUS` | `date, month, bonus, comment` |
| `BAD_EVALUATION_{SINGULAR,PLURAL}` | `content` |
| `NOTIFY_APPROVER_ABOUT_MANAGERS_APPROVE` | `to_name, employee, confirmation_url` |
| `ASK_MANAGER_FOR_VACATION_APPROVAL` | `to_name, employee, period_start, period_end, confirmation_url` |

## Legacy Template Coexistence

50 legacy templates (non-NOTIFY_* prefixed) coexist with 70 new templates. Legacy use simpler variable sets and generic subjects ("[TTT] Уведомление об отпуске"). DB `email` table has no `template_code` column — impossible to track usage per template from DB alone. Code analysis needed to determine if legacy templates are still triggered.

## Key Findings

1. **DIGEST is most complex**: 20KB template with nested iteration over vacation/dayoff/sickleave events, conditional approve links, multi-section layout
2. **Vacation fan-out**: 7 event types × up to 5 recipients = potential 35 notifications per vacation lifecycle
3. **Date format inconsistency**: Vacation uses "DD Month YYYY" (Russian months), Budget uses "dd-MM-yyyy", Calendar uses split day/month/year
4. **Russian-only**: All 120 subjects in Russian. No i18n despite EN language option in UI
5. **`confirmation_url` hardcoded**: Points to production domain, not env-specific — will be wrong on test environments

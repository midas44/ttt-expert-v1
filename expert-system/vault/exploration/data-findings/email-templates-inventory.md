---
type: exploration
tags:
  - email
  - notifications
  - templates
  - vacation
  - sick-leave
  - database
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/email-service]]'
  - '[[modules/vacation-service]]'
  - '[[EXT-cron-jobs]]'
branch: release/2.1
---
# Email Templates Inventory

120 email templates in `ttt_email.email_template`. All subjects in Russian — no English language templates exist. 660 emails sent (609 SENT, 51 INVALID).

## Template Categories

### Vacation (~50 templates) — largest category
**Recipient taxonomy** per event: EMPLOYEE, MANAGER, SENIOR_MANAGER, APPROVER, ALSO, PM, DM

Events with multi-recipient templates:
- **CREATE**: to employee, manager, senior_manager, also (4)
- **CHANGE**: to employee, manager, senior_manager, approver, also (5)
- **STATUS_CHANGE**: to employee, manager, senior_manager, also (4)
- **DELETE_CANCEL**: to employee, manager, senior_manager, approver, also (5)
- **AUTODELETE**: to employee, manager, senior_manager, approver, also (5)
- **RECOVERED**: to employee, manager, senior_manager, approver, also (5)
- **CHANGE_APPROVER**: to employee, approver, senior_manager (3)
- **ABSENCE_LAST_DAY**: to employee, manager (2)

Standalone:
- ALERT_SOON_VACATION, PUSH_APPROVER, SOON_AUTODELETE, GREETINGS_AFTER_VACATION ("С возвращением!")
- Calendar impact: CALENDAR_NEXT_YEAR_FIRST/LAST, CALENDAR_UPDATE_* (5 variants for different day types)
- Accruals: ACCRUALS_BY_HIRE

**Legacy templates** (separate naming): NEW_VACATION_{DM,PM,ALSO}, UPDATE_VACATION_{ALSO,DM}, CANCEL_VACATION_{DM,EMPLOYEE,PM}, DELETE_VACATION_{AUTO,BY_MANAGER,DM,EMPLOYEE,PM}, VACATION_CONFIRMED_PM, VACATION_IS_COMING{_TO_PM}, VACATION_*_DAY_*, VACATION_STATUS_CHANGED_EMPLOYEE, VACATION_UPDATE_REGULAR_DAYS

### Sick Leave (~15 templates)
Three-axis naming: action × role
- Actions: OPEN, CLOSED, DELETE, DATES_CHANGED, NUMBER_CHANGED, FILES_ADDED, REJECTED, OVERLAPS_VACATION
- Roles: BY_SUPERVISOR, BY_ACCOUNTANT, to EMPLOYEE

### Day-Off (~4 templates)
- DAYOFF_AUTODELETE_TO_EMPLOYEE, DAYOFF_AUTODELETE_CALENDAR_UPDATE_TO_EMPLOYEE
- DAYOFF_CHANGE_APPROVER_TO_EMPLOYEE, DAYOFF_STATUS_CHANGE_TO_EMPLOYEE
Note: Day-off templates only go to employee — no multi-recipient fan-out like vacations.

### Reports/Approval (~10 templates)
- APPROVE_REJECT — "[TTT] Ваши часы за период {{period_start}}-{{period_end}} были отклонены менеджером {{manager}}"
- APPROVE_REJECT_PERIOD_CLOSE — rejection on period close
- APPROVE_REQUEST / APPROVE_REQUEST_FOR_EMPLOYEE — approval reminders
- FORGOTTEN_REPORT — "[TTT] Скорее всего вы забыли зарепортиться за прошлую неделю"
- STATISTICS_FORGOTTEN_REPORT — period-specific forgotten report
- REPORT_SHEET_CHANGED, REJECTED_WEEK_FIX
- EXTENDED_PERIOD_OPENED/CLOSED — extended deadline notifications

### Budget/Project (~7 templates)
- BUDGET_NOTIFICATION_EXCEEDED/NOT_REACHED/DATE_UPDATED
- PROJECT_CREATE/CLOSE
- REQUEST_TURN_OFF_BONUS

### Employee Lifecycle (~5 templates)
- EMPLOYEE_FIRE/HIRE/NEW — hiring/firing notifications
- EMPLOYEE_RATING_EVALUATION — reminder to rate employees
- MANAGER_REASSIGN

### Other
- **DIGEST** — "ТТТ Дайджест отсутствий" (absence digest)
- BAD_EVALUATION_SINGULAR/PLURAL
- HAPPY_BONUS
- BASE_TTT_TEMPLATE (base template)

## Key Observations

1. **Vacation notification explosion**: ~50 templates for vacation events alone, with up to 5 recipients per event (employee, manager, senior_manager, approver, also-notify). This is the most complex notification area.
2. **Legacy vs new naming**: Older templates use `NEW_VACATION_PM`, newer use `NOTIFY_VACATION_CREATE_TO_MANAGER`. Both coexist — unclear if legacy ones are still used.
3. **Russian-only subjects**: All 120 templates have Russian subjects. No English versions. This is a localization gap for the EN language option.
4. **Template variables**: Mustache-style `{{variable}}` and block syntax `{{#block}}{{.}}{{/block}}`.
5. **Day-off notification asymmetry**: Only employee receives day-off notifications, unlike vacations where 5 roles are notified.

See also: [[modules/email-service]], [[modules/vacation-service]], [[exploration/ui-flows/vacation-pages]], [[EXT-cron-jobs]]

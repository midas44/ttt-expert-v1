---
type: exploration
tags:
  - notifications
  - budget
  - ui-flow
  - live-testing
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/email-service]]'
  - '[[email-template-field-mapping]]'
  - '[[architecture/roles-permissions]]'
---
# Notification Page — Budget Monitoring

## Overview

The `/notifications` page is a **budget/hour limit monitoring system** — NOT a general notification center. Managers and admins set up alerts to be notified when employees approach or exceed hour limits on specific project-task combinations within date ranges.

Page title: "Notification" (singular in EN UI). Only accessible to users with management roles.

## UI Structure

### List View
- Table columns: Project (sortable), Task, Employee, Limit, Period, Date of reaching the limit, Actions
- "Create a notification" button (green, top right)
- Supports pagination and sorting

### Create Dialog ("Creating notification")
Fields:
- **Project*** — autocomplete dropdown (required)
- **Task** — autocomplete dropdown (optional — can monitor whole project)
- **Employee*** — autocomplete dropdown (required)
- **Limit*** — numeric spinner + unit dropdown:
  - **md** (man-days) — absolute limit
  - **%** (percentage of month) — relative limit
- **Period*** — date range picker (DD.MM.YYYY – DD.MM.YYYY)
- Buttons: Cancel, Create

### Hidden field: `repeatMonthly` (boolean)
Not visible in UI create form, but exists in the backend. The frontend code has a `repeatMonthly` field in the request DTO but no UI toggle was observed. Default appears to be `false`.

## Backend Architecture

- **Controller**: `BudgetNotificationController` at `/v1/notifications` (GET, POST, DELETE)
- **Entity**: `budget_notification` table with fields: id, watcher (FK→employee), employee (FK), project (FK), task (FK), start_date, end_date, budget_limit, budget_limit_percent, reached_date, repeat_monthly
- **Service**: `BudgetNotificationServiceImpl` — handles limit recalculation, monthly auto-renewal, email triggering
- **Email templates**: `BUDGET_NOTIFICATION_NOT_REACHED`, `BUDGET_NOTIFICATION_EXCEEDED`, `BUDGET_NOTIFICATION_DATE_UPDATED`
- **Test endpoint**: POST `/v1/test/budgets/notify` — triggers notification sending

## Permissions

- **View**: `AUTHENTICATED_USER` (but scoped to watcher's own notifications)
- **Create/Edit/Delete**: ADMIN, VIEW_ALL, PROJECT_MANAGER, DEPARTMENT_MANAGER, OFFICE_DIRECTOR (non-read-only)
- **Permission service**: `BudgetNotificationPermissionService` — enforces role-based access

## Live Data (Stage)
- 1,332 rows in `budget_notification` table
- 5 distinct watchers, 6 employees, 8 projects
- 1,324 rows from single user (Nikita Petrov) — likely test/automation data
- Only 8 rows use `budget_limit` (md); 1,324 use `budget_limit_percent`
- Only 7 rows have `reached_date` populated
- Only 1 row has `repeat_monthly=true`

## Findings

1. **UX gap**: No `repeatMonthly` toggle in UI despite backend support — users cannot set monthly auto-renewal through the UI
2. **Data quality**: Massive duplicate entries in stage DB suggest either a bug in monthly renewal or heavy test pollution
3. **Sparse usage**: Very few real notifications (8 non-test entries from 4 watchers over 2010-2021)
4. **No edit**: Only create and delete — no update/edit endpoint or UI

## Related
- [[modules/email-service]] — notification email templates
- [[email-template-field-mapping]] — BUDGET_NOTIFICATION templates
- [[architecture/roles-permissions]] — PM/admin access
- [[cron-job-live-verification]] — budget notification recalculation may run on cron

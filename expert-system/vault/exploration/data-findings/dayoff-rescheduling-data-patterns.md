---
type: exploration
tags:
  - day-off
  - rescheduling
  - data-patterns
  - calendar-conflict
  - DELETED_FROM_CALENDAR
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[day-off-service-implementation]]'
  - '[[calendar-service]]'
  - '[[dayoff-rescheduling-warning-bug]]'
branch: release/2.1
---

# Day-Off Rescheduling Data Patterns

## Two-Table Architecture

- `employee_dayoff` — ledger of granted day-offs (id, employee, original_date, personal_date, duration, reason)
- `employee_dayoff_request` — workflow for rescheduling (adds: approver, last_approved_date, status, creation_date)

## Status Distribution (timemachine)

| Status | Count | Description |
|--------|-------|-------------|
| APPROVED | 2902 | Approved rescheduling requests |
| DELETED | 226 | Manually deleted by user/admin |
| DELETED_FROM_CALENDAR | 82 | Auto-deleted when calendar holiday removed |
| NEW | 17 | Pending approval |
| REJECTED | 14 | Rejected by approver |

## DELETED_FROM_CALENDAR Pattern

All 82 records trace to "День России" (Russia Day, June 12 2025) removal from calendar. Created between April-May 2025. This is the [[calendar-service]] in action — when a production calendar holiday is removed, existing day-off requests linked to that holiday get status `DELETED_FROM_CALENDAR`.

## Overdue Requests

5 of 17 NEW requests have `last_approved_date` ≤ today (2026-03-13), meaning the original holiday has passed but the rescheduling hasn't been approved. The `last_approved_date` field holds the original holiday date, and `personal_date` is the employee's chosen rescheduling date.

Key overdue approvers:
- Pavel Weinmeister (id=249): 4 overdue requests
- Nikolay Gerasimov (id=94): 1 overdue request

## Rescheduling Reasons

Requests are auto-created when production calendar holidays are set. Common reasons (Russian holiday names): Международный женский день, День защитника отечества, День Победы, День труда. Cyprus-specific: Cyprus National Holiday, Good Friday/Easter Monday (Orthodox), Greek Independence Day.

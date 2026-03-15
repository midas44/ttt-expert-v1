---
type: exploration
tags:
  - day-off
  - rescheduling
  - warning
  - bug
  - notification
  - authorization
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[day-off-service-implementation]]'
  - '[[vacation-service-implementation]]'
  - '[[frontend-day-off-module]]'
branch: release/2.1
---

# Day-Off Rescheduling Warning Bug — Global Broadcast to All Users

## Finding

The `GET /api/vacation/v1/employees/current/warnings` endpoint returns `EXPIRED_NON_APPROVED_DAY_OFF` warnings to **all users** regardless of whether they are the approver. Verified on both timemachine and stage environments.

## Evidence

Tested with 3 users of different roles — all received identical 3 overdue warnings:
- **Perekrest** (ADMIN+DM+PM+ACCOUNTANT) → 3 warnings (dayOffIds: 3184, 3221, 3225)
- **Weinmeister** (PM, actual approver) → same 3 warnings
- **Turetskii** (ROLE_EMPLOYEE only, no PM/DM/Admin) → same 3 warnings

All 3 overdue requests belong to approver Weinmeister (vacation employee id=249). Perekrest (id=41) has zero requests as approver.

## Code vs Deployed Behavior

The **release/2.1 code** appears correct:
- `ExpiredNonApprovedEmployeeDayOffCommand` checks roles (PM/DM/Admin gate)
- `findOverdueRequests(employeeId, date)` filters by `approver = employeeId`

But the **deployed code** on both timemachine and stage ignores these filters, returning all overdue requests globally. The command was introduced in commit `ad7822e4` (2024-03-26, ticket #2930).

## UI Impact

Banner text: *"You have overdue day off rescheduling requests. Please approve or reject them"* with link to `/vacation/request/daysoff-request/APPROVER`. When non-approvers click through, the APPROVER tab shows 0 items — creating confusion.

## Banner Architecture

Frontend chain: `RequestVacationNotificationController` → dispatches `fetchVacationNotifications` → calls `vacationApiRequest.get('/v1/employees/current/warnings')` → Redux selectors check for `EXPIRED_NON_APPROVED_DAY_OFF` type → `ExpiredNonApprovedNotification` component renders banner.

The frontend correctly displays whatever the backend returns — the bug is server-side.

## Data Context

Day-off request status distribution (timemachine):
| Status | Count |
|--------|-------|
| APPROVED | 2902 |
| DELETED | 226 |
| DELETED_FROM_CALENDAR | 82 |
| NEW | 17 |
| REJECTED | 14 |

5 of 17 NEW requests are overdue (original_date < 2026-03-13). The `last_approved_date` field triggers overdue status when ≤ today.

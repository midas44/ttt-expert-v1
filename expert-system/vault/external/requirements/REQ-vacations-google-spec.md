---
type: external
tags:
  - vacation
  - requirements
  - google-doc
  - specification
  - complete
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/vacation-service-implementation]]'
  - '[[external/requirements/REQ-vacations-master]]'
  - '[[modules/frontend-vacation-module]]'
  - '[[external/requirements/google-docs-inventory]]'
---

# Vacation Specification (Google Doc — Original Functional Spec)

Source: docs.google.com/document/d/13MQVPLvtFsxvNNcuIBvQfhZosdULINHzhoyE33OhvO4
Version: 1.0 (Oct 2017 – Feb 2019)

## Core System: Two Counters
- **availableDays**: current-year vacation days
- **nextYearAvailableDays**: next-year days (cap: 20)
- Jan 1: nextYear → available, nextYear resets to 20

## Accrual Formula (R008-R010)
```
days = round(20 × remainingDaysInYear / totalDaysInYear)
```

## Event Taxonomy (14 event types)
Employment Start, New Year, Termination, Maternity Enter/Exit, Request Create/Edit/Cancel/Restore/Delete, Approval, Rejection, Payment, Manual Correction.

Each event records: Days Accrued, Regular Days Used, Administrative Days Used.

## Day Deduction Rules
- **Create request**: deduct from availableDays (current year) + nextYearAvailableDays (next year portions)
- **Cancel/Delete**: return nextYear first (cap 20), remainder to available
- **Payment**: delta between approved and paid days → restore prioritizing nextYear

## Request Types
- **Basic**: standard vacation request
- **Provisional**: uncertain timing, auto-deletes 1 week before start unless converted

## Status Transitions
New → Approved (by manager), New → Rejected, Approved → Rejected, Rejected → Approved, New/Approved/Rejected → Canceled, Canceled → Restored (→New), Approved → Paid (by accountant)

## Closed Period Restrictions
- Cannot cancel Basic+Approved if payment month in closed report period
- Cannot delete Basic if Paid, or Approved with closed period

## Payment Month Selection (R046)
- Months containing any vacation date
- Up to 2 months before start (if report period open)
- One month after end

## Manager Workflow (R068-R079)
- 4 tabs: Awaiting Approval, My Department, My Projects, Forwarded
- Actions: Approve, Reject, Forward (change approver)
- Approach notifications: 1 month, 2 weeks, 1 week before start (if unconfirmed)
- Confirmed requests: PM + manager notified 1 week before

## Accountant Workflow (R080-R093)
- 5 month tabs centered on first open approval period
- Pay single: adjust regular/admin day split (total preserved)
- Batch pay: select multiple, no individual editing
- Correction: edit day balance (0-200), comment required

## Production Calendar Impact (R103-R109)
- Any calendar day change → recalculate all affected requests
- If working days < 5 → change type to Administrative, return days
- If new count > balance → change to Administrative
- Zero working days → delete request, send notification

## Vacation Calendar View (R110-R122)
- 7 months visible, scrollable ±1 month
- Color coding: orange (New+Basic), light blue (New+Provisional), green (Approved+Basic), dark blue (Approved+Provisional), purple (Paid)
- Tooltip: status, dates, type, payment month, comment (restricted visibility)

## Auto-Delete Provisional (R067)
- 1 month before: warning notification
- 1 week before: auto-delete + return days + notification

## Boundary Notifications
- 1 business day before: "Last day before vacation" (different templates for PM vs others)
- 1 business day after: "Welcome back!"

## Related
- [[modules/vacation-service-implementation]] — backend implementation
- [[external/requirements/REQ-vacations-master]] — Confluence requirements
- [[modules/frontend-vacation-module]] — frontend implementation
- [[exploration/data-findings/vacation-schema-deep-dive]] — data patterns
- [[external/requirements/google-docs-inventory]] — source catalog

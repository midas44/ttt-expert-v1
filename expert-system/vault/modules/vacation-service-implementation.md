---
type: module
tags:
  - vacation
  - backend
  - implementation
  - service
  - state-machine
  - cron
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[vacation-day-calculation]]'
  - '[[modules/vacation-service]]'
  - '[[REQ-vacations-master]]'
branch: release/2.1
---
# Vacation Service Implementation

Root: `vacation/` — Maven multi-module (common-enum, db/db-api, service/service-api, service/service-impl, rest, app, integration/mq).

## Status State Machine (VacationStatusManager)
```
NEW → NEW, CANCELED (employee), REJECTED/APPROVED (PM/DM/ADMIN)
REJECTED → APPROVED (PM/DM/ADMIN)  
APPROVED → NEW/CANCELED (employee), REJECTED (PM/DM/ADMIN), PAID (accountant)
CANCELED → NEW (employee)
```
PAID and DELETED are terminal — no outgoing transitions. DELETED set programmatically (soft delete).

## Key Service Classes

**VacationServiceImpl (update orchestrator):** Create/update/approve/reject/cancel/delete. Uses pessimistic write locking (`findByIdAndAcquireWriteLock`). Every mutation: validate → lock → process → recalculate days → sync approvers → publish events.

**VacationCRUDServiceImpl:** Low-level CRUD, crossing detection, payment date validation.

**VacationRecalculationServiceImpl:** On every mutation — returns all REGULAR+EXACT vacation days to balance, then redistributes. Insufficient days → auto-converts to ADMINISTRATIVE.

**PayVacationServiceImpl:** Validates APPROVED+EXACT. Creates VacationPaymentEntity. `payExpiredApproved()` auto-pays overdue (>2 months) approved vacations daily.

**SickLeaveServiceImpl:** Dual status (main + accounting). Dual workflow. PM-only access check. Closing requires sick leave certificate number. Cannot delete if PAID.

**EmployeeDayOffServiceImpl:** Day-off creation/approval. `rejectedBySystem()` — bulk-rejects day-offs for an office/date on calendar changes.

## Approver Logic (Create)
- CPO → self-approval + manager as optional approver
- Regular employee → manager as approver
- No manager → self-approval

## 12 Scheduled Tasks
Employee sync (15min), full sync (midnight), annual accruals (Jan 1), auto-pay expired (midnight), vacation days check (5min), notifications (14:00), digest (8:00), prod calendar notif (Nov 1), employee-project sync (3:00). All use `@SchedulerLock`.

Links: [[vacation-day-calculation]], [[multi-approver-workflow]], [[vacation-service-debt]], [[modules/vacation-service]], [[REQ-vacations-master]], [[exploration/data-findings/vacation-schema-deep-dive]]

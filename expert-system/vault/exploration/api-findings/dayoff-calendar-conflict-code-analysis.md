---
type: exploration
tags:
  - day-off
  - calendar
  - conflict
  - rabbitmq
  - code-analysis
created: '2026-03-13'
updated: '2026-03-13'
status: active
branch: release/2.1
related:
  - '[[day-off-service-implementation]]'
  - '[[calendar-service]]'
  - '[[rabbitmq-messaging]]'
---
# Day-Off Calendar Conflict Handling — Code Analysis

## Summary

Four distinct code paths handle calendar-dayoff interactions, triggered by different RabbitMQ events. The system is more complex than initially assumed — not just one conflict resolution mechanism but four paths with different behaviors.

## Path A: Calendar Day Changed → Day-Off MOVE (Silent)

**Trigger:** Admin creates/updates calendar day (e.g., adds holiday where employees have day-off).

**Chain:** `CalendarDaysServiceImpl.create()/update()` → `CalendarChangedApplicationEvent` → RabbitMQ `ttt.calendar.changed.topic` → `CalendarUpdateProcessorImpl.processDay()` → checks if day becomes non-working or half-working → finds affected employees via `employee_dayoff` ledger → `PreviousWorkingDayCalculator.getPreviousWorkingDay()` → saves new ledger entry with moved date → email notification.

**Key behavior:** Does NOT change request status. Silently moves the ledger entry. The request table (`day_off_request`) is untouched. Hard to detect without ledger inspection.

**Notifications:** `NOTIFY_VACATION_CALENDAR_UPDATE_0H_DAY_MOVED` (non-working) or `NOTIFY_VACATION_CALENDAR_UPDATE_7H_DAY_MOVED` (half-day).

## Path B: Calendar Day Deleted → DELETED_FROM_CALENDAR

**Trigger:** Admin deletes a calendar day entry entirely.

**Chain:** `CalendarDaysServiceImpl.delete()` → `CalendarDeletedApplicationEvent` → RabbitMQ `ttt.calendar.deleted.topic` → `EmployeeDayOffCalendarUpdateServiceImpl.deleteDayOffs()` → finds requests with `original_date = date` AND status IN (NEW, APPROVED) → **bulk sets status to DELETED_FROM_CALENDAR** via hardcoded SQL → **physically deletes** all ledger entries for that date → recalculates vacation days → notification.

**This is what caused the 82 DELETED_FROM_CALENDAR records** from the June 2025 "День России" removal.

## Path C: Period Changed → Day-Off REJECTED by System

**Trigger:** Approve period changes for an office.

**Chain:** `PeriodChangedEventHandler.handle()` (when `periodType == APPROVE`) → `employeeDayOffService.rejectedBySystem()` → finds NEW requests with `last_approved_date = date` → sets status to REJECTED → notification `NOTIFY_DAYOFF_AUTODELETE_TO_EMPLOYEE`.

## Path D: Employee Office Change → DELETED_FROM_CALENDAR (Year-wide)

**Trigger:** Employee changes office.

**Chain:** `EmployeeDayOffAutoDeleteToCalendarUpdateHelper.update()` → finds ALL NEW/APPROVED requests for that employee's year (max 100) → sets each to DELETED_FROM_CALENDAR → physically deletes ALL ledger entries for the year → notification.

## Architecture Issues

1. **`updateAll()` entity state bug:** Repository at `EmployeeDayOffRequestRepositoryImpl.java:359` hardcodes DELETED_FROM_CALENDAR in SQL, but the Java entities passed to post-update events still have original status (NEW/APPROVED).

2. **Race condition risk:** Path A and Path B use separate RabbitMQ queues. Rapid create-then-delete could cause both to fire, with Path A writing a ledger entry that Path B doesn't fully clean up.

3. **`PreviousWorkingDayCalculator` limitation:** Checks only Saturday/Sunday as weekends. Doesn't query actual production calendar for offices with different weekend patterns.

4. **Hardcoded production URL** in all notification templates: `https://ttt.noveogroup.com/vacation/my/daysoff`.

## DB State (Timemachine)

| Status | Count |
|--------|-------|
| APPROVED | 2,902 |
| DELETED | 226 |
| DELETED_FROM_CALENDAR | 82 |
| NEW | 17 |
| REJECTED | 14 |

All 82 DELETED_FROM_CALENDAR: `original_date = 2025-06-12`, single batch at 2025-05-26T20:14:02 UTC.

## Related

- [[dayoff-rescheduling-warning-bug]] — related day-off bug from S12
- [[dayoff-rescheduling-data-patterns]] — data analysis from S12
- [[day-off-service-implementation]] — service implementation
- [[calendar-service]] — calendar-side event publishing
- [[rabbitmq-messaging]] — event routing
- [[email-service]] — notification templates

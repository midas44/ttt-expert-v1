---
type: pattern
tags:
  - email
  - notifications
  - rabbitmq
  - scheduling
  - cross-service
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[rabbitmq-messaging]]'
  - '[[EXT-cron-jobs]]'
  - '[[ttt-service]]'
  - '[[vacation-service]]'
  - '[[email-service]]'
  - '[[calendar-service]]'
branch: release/2.1
---

# Email Notification Triggers

## Architecture

Email sending follows two patterns:
1. **Scheduled batch** — Cron jobs collect recipients, publish to RabbitMQ `ttt.email.topic` exchange
2. **Event-driven** — Spring `@EventListener` reacts to domain events, routes through `SendEmailApplicationEventListener` → RabbitMQ → `EmailSendScheduler` batch sender

Central processor: [[email-service]] `EmailBatchService` picks up queued messages via `EmailSendScheduler` cron and sends via SMTP.

## TTT Service — 5 Scheduled Triggers

| Template | Cron Property | Purpose |
|----------|--------------|---------|
| `TASK_REPORT_CHANGED` | `task-report.changed.notifications.cron` | Report status changes |
| `FORGOTTEN_REPORT` | `task-report.forgotten.notifications.cron` | Missing weekly reports |
| (delayed resend) | `task-report.forgotten.delayed.notifications.cron` | Re-send if still missing, skip day-off |
| `REPORT_REJECTED` | `task-report.reject.notifications.cron` | Manager rejected report |
| (budget) | `budget.notifications.cron` | Budget threshold alerts |

All via `TaskReportNotificationScheduler` and `BudgetNotificationScheduler`.

## Vacation Service — 2 Scheduled + ~25 Event-Driven

**Scheduled**: `DIGEST` (weekly/daily aggregated summary via `DigestScheduler`) and availability schedule notifications (`AvailabilityScheduleNotificationScheduler`).

**Event-driven templates** (30+ variants):
- **Vacation**: status change, approver change, calendar conflicts (less-than-min, not-enough, 7h-day-moved, 0h-day-moved, next-year-first) — 7 templates
- **Day-off**: status change, approver change, auto-delete, calendar-update-delete — 6 templates  
- **Sick leave**: open, close, delete, dates-changed, number-changed, files-added — 6 base templates × 3 actor variants (employee, accountant, supervisor) = ~16 templates

Total: ~30 unique email templates in vacation service alone.

## Calendar Service — No Emails

Calendar service has no email sending capability. It only manages date/holiday data and CS sync.

## Message Flow

```
Domain Event → @EventListener → SendEmailApplicationEvent
  → SendEmailApplicationEventListener → RabbitMQ (ttt.email.topic)
    → SendEmailListener (@RabbitListener) → MqEventHandler
      → EmailBatchService → SMTP
```

## Key Finding

The vacation service has the richest email logic with complex conditional notification routing — different templates for same action depending on who performed it (employee vs accountant vs supervisor). This is a high-priority area for test coverage.

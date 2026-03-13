---
type: external
tags:
  - cron
  - scheduling
  - background-jobs
  - notifications
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[system-overview]]'
  - '[[ttt-service]]'
  - '[[vacation-service]]'
---
# Cron Jobs Inventory

**Source**: Confluence 32904541 | All run on Asia/Novosibirsk (GMT+7) | 23 jobs across 4 services.

## TTT Service (8 jobs)
- Unreported hours notifications: Mon+Fri 16:00 and daily 16:30 (delayed)
- Manager-changed report notifications: daily 7:50
- Rejected hours notifications: every 10 min
- Budget exceeded notifications: every 30 min
- CompanyStaff sync: 15 min partial + daily full
- Extended reporting period cleanup: every 5 min
- PM Tool sync (#3083): 15 min + full at startup
- Periodic statistic report sync: daily 4:00

## Vacation Service (10 jobs)
- CompanyStaff sync: 15 min + daily full
- New Year vacation day accrual: Jan 1
- Delete expired preliminary vacations: hourly
- Close unconfirmed expired vacations: hourly
- Vacation notifications: daily 8:00
- Production calendar reminder: Nov 1
- Auto-pay approved vacations: 1 month after period close, daily
- APPROVED-to-PAID transition: 2h after approval period change, every 10 min
- Employee-project sync (#3262): daily 3:00
- Full statistic report sync (#3345/3346): once at startup

## Calendar Service (1 job)
- CompanyStaff sync: 15 min + daily full

## Email Service (2 jobs)
- Send queued emails: every 20 sec
- Prune emails older than 30 days: daily midnight

## Testing
All jobs have test endpoints under `/api/{service}/v1/test/...` for manual triggering.

## Related
- [[system-overview]]
- [[ttt-service]]
- [[vacation-service]]
- [[email-service]]

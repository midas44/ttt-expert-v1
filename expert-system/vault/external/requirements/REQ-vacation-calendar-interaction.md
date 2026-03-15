---
type: external
tags:
  - vacation
  - calendar
  - requirements
  - confluence
  - day-off
  - interaction
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-vacations-master]]'
  - '[[modules/calendar-service]]'
  - '[[modules/vacation-service]]'
branch: release/2.1
---
# Vacation-Calendar Interaction Requirements

Confluence page 110297393, version 1. Describes post-sprint-11 interaction between Vacations and Calendar services.

## Key Rules

1. **Preliminary requests eliminated** after sprint 11
2. **Migration #3053:** Existing preliminary NEW/APPROVED become regular. APPROVED in closed period → payment month changed to first open period.

## Trigger Events for Vacation Adjustment
When day-off transfer (after confirmation) or production calendar change increases vacation days in a request → check if total exceeds available.

**Trigger:** day-off deletion (transfer confirmation or admin calendar removal).

## Two-Phase Check

**Phase 1 (immediate):** Check if annual days exceeded. If yes → affected request becomes administrative. Done.

**Phase 2 (#3049, 10 minutes after Phase 1):** If annual NOT exceeded, check accrued days for:
- The affected request's payment month
- Same-payment-month requests with later start dates
- All requests with later payment months

**On insufficient days (#3049):**
- Change request type to Administrative
- Send notification ID_85

## Staleness Warning
This page is version 1 and may be partially superseded by [[REQ-vacations-master]] (version 31), which describes a more detailed checking algorithm (#3281+#2736). The 10-minute Phase 2 delay is a notable race condition risk.

Links: [[REQ-vacations-master]], [[modules/vacation-service]], [[modules/calendar-service]], [[analysis/absence-data-model]], [[EXT-cron-jobs]]
Tickets: #3053, #3049. External: Email notifications Google Sheet.

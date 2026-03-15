---
type: external
tags:
  - requirements
  - confluence
  - day-off
  - weekend
  - absences
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[day-off-service-implementation]]'
  - '[[frontend-day-off-module]]'
  - '[[REQ-vacations-master]]'
---
# REQ: Day-Off / Weekend Transfer Requirements

No dedicated requirements page exists in Confluence. Rules scattered across vacation requirements and sprint notes.

## Sources
- Vacations / Отпуск (page 130385085)
- Calendar-Vacation interaction (page 110297393)
- Sprint 10 (page 130385485), Sprint 12 (130385389), Sprint 13 (130385479), Sprint 14 (160466191)

## Calendar-Triggered Recalculation Rules

When day-off removed from production calendar or transfer confirmed:

**For advanceVacation = false (Russia):**
1. Check if affected vacation has sufficient accrued days for year
2. If insufficient → convert to ADMINISTRATIVE type
3. If sufficient → delayed check (10 min) including all same-payment-month requests with later start dates + all requests with later payment months
4. If any insufficient → convert to administrative + send email notification (ID_85)

**For advanceVacation = true (Cyprus/Germany):**
- Day-off removal deducts from current year balance (can go negative)
- No automatic conversion to administrative

## Pending Transfers at Month Close
Unconfirmed day-off transfers automatically rejected at month close.

## Day-Off Counting in Sick Leave
Unconfirmed transfers not counted as transferred in BL working-day count — original date still treated as "day off" until manager confirms.

## Notification Rules (Sprint 13-14)
- Day-offs in middle of week included in pre-absence email notification
- Notification sent once on last working day before absence
- Sprint 14: new notification when calendar changes cause vacation request insufficiency

## Known Gaps
- No standalone day-off requirements page exists
- Day-off feature treated as sub-concern of vacation, not standalone domain
- No specification for the two-table storage pattern (request + ledger)
- No specification for the credit/debit duration semantics (0 vs 8 hours)
- DELETED_FROM_CALENDAR status not described in requirements
- Calendar conflict resolution (move to previous working day) not formally specified

## Discrepancies vs Implementation
| Documentation | Implementation |
|--------------|---------------|
| "Day-off deleted from calendar" described as trigger | Two separate code paths: rejectedBySystem (→REJECTED) vs deleteDayOffs (→DELETED_FROM_CALENDAR) |
| Transfer as simple calendar event | Complex two-table pattern with credit/debit ledger |
| No mention of CANCELED status | Dead code: CANCELED in entity enum, never used |

Links: [[day-off-service-implementation]], [[frontend-day-off-module]], [[REQ-vacations-master]], [[REQ-vacation-calendar-interaction]]

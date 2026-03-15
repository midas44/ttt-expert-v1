---
type: exploration
tags:
  - day-off
  - calendar-conflict
  - live-test
  - timemachine
  - data-integrity
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[dayoff-calendar-conflict-code-analysis]]'
  - '[[dayoff-calendar-conflict-analysis]]'
  - '[[day-off-service-implementation]]'
  - '[[email-notification-triggers]]'
  - '[[email-template-field-mapping]]'
branch: release/2.1
env: timemachine
---

# Day-Off Calendar Conflict — Live Test Results

Live verification of conflict resolution paths A (calendar entry creation → MOVE) and B (calendar entry deletion → DELETE) on timemachine environment.

## Test Setup

- **Employee**: vstrakhov (id=990052), office: Russia
- **Pre-existing state**: Ledger entry 5351 (personal_date=2026-04-16, original_date=2026-02-20, reason="День защитника отечества"), Request 3166 (status=APPROVED)
- **Test action**: Created holiday "Test Holiday - Session 15" on April 16, 2026 in Russia production calendar via admin UI (user: Galina Perekrest)

## Path A: Calendar Entry Created → Day-Off MOVE

When a new holiday is added on a date where an employee has an approved day-off:

1. **New ledger entry created**: id=5491, personal_date=Apr 15 (previous working day), original_date=Apr 16, reason="Test Holiday - Session 15"
2. **Old ledger entry UNCHANGED**: id=5351 remains with personal_date=Apr 16 — NOT cleaned up (orphaned)
3. **Request UNCHANGED**: id=3166 stays APPROVED with personal_date=Apr 16
4. **Email notification SENT**: Template `NOTIFY_VACATION_CALENDAR_UPDATE_0H_DAY_MOVED`, subject "[TIMEMACHINE][TTT] Изменения в производственном календаре", body confirms move from Apr 16 to Apr 15

### Data Integrity Issue — Orphaned Ledger Entry
The system creates a NEW moved entry but does NOT update or remove the OLD entry that was already on the conflicting date. Entry 5351 (originally moved there from Feb 20) remains pointing to Apr 16 even though Apr 16 is now a holiday. This is Path A's orphan behavior — it only handles the immediate conflict by creating a new entry, not cleaning up prior entries on the same date.

## Path B: Calendar Entry Deleted → Day-Off DELETE

When the test holiday was deleted from the calendar:

1. **Moved ledger entry DELETED**: id=5491 removed entirely
2. **Old ledger entry UNCHANGED**: id=5351 still has personal_date=Apr 16
3. **Request UNCHANGED**: id=3166 still APPROVED
4. **NO email notification sent** — deletion path is silent

### Net Result After Full Cycle
State effectively restored to pre-test: entry 5351 remains pointing to Apr 16 (now a regular working day again), request 3166 still APPROVED. Entry 5491 was created and deleted — net zero.

## Key Findings

1. **Path A creates but doesn't clean up**: Adds new moved entry without removing/updating existing entries on the conflicting date
2. **Path B deletes only the entry it created**: Correctly removes the moved entry (5491) but doesn't touch pre-existing entries
3. **Deletion is silent**: No notification email on calendar entry deletion (unlike creation which sends NOTIFY_VACATION_CALENDAR_UPDATE_0H_DAY_MOVED)
4. **Request table is never modified**: Both paths leave employee_dayoff_request untouched — status stays APPROVED regardless of ledger changes
5. **Hardcoded production URL in email**: Notification body contains `https://ttt.noveogroup.com/vacation/my/daysoff` regardless of environment — known bug

## Confirmed Code Paths

| Path | Trigger | Ledger Action | Notification | Request Change |
|------|---------|---------------|-------------|----------------|
| A: Create holiday on day-off date | RabbitMQ calendar.changed | Create new entry (moved to prev working day) | NOTIFY_VACATION_CALENDAR_UPDATE_0H_DAY_MOVED | None |
| B: Delete holiday from day-off date | Admin UI delete | Delete the moved entry | None | None |

## Test Implications

- Test cases must verify orphaned entries don't cause downstream issues (double day-offs, incorrect balance calculations)
- Notification asymmetry (send on create, silent on delete) should be tested
- Request table immutability during calendar conflicts needs verification for edge cases (what if request is still NEW/pending?)

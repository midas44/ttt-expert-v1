---
type: investigation
tags:
  - calendar
  - office
  - migration
  - bug-2876
  - production-calendar
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[vacation-service]]'
  - '[[exploration/data-findings/cross-service-office-sync-divergence]]'
  - '[[external/tickets/sprint-16-overview]]'
branch: release/2.1
---
# Office-Calendar Mapping and 2024 Calendar Migration

## Summary

In 2024, 11 salary offices migrated from the Russia production calendar to their local country calendars. This created a one-time calendar switch event tracked in `ttt_calendar.office_calendar` via `since_year`. This is directly related to #2876 Bug 2 (calculation error after calendar change).

## Calendar Mapping (timemachine env)

### Offices that switched calendars (Russia → local, since_year=2024):
| Office ID | Office Name | New Calendar |
|-----------|------------|-------------|
| 10 | Венера | Cyprus |
| 11 | Нептун | Cyprus |
| 12 | Уран | Cyprus |
| 14 | Титан (Черногория) | Cyprus |
| 15 | Протей (Грузия) | Georgia |
| 16 | Каллисто (Армения) | Armenia |
| 17 | Сириус (Париж) | France |
| 20 | Персей | Germany |
| 26 | Плутон | Cyprus |
| 31 | Венера Франция | France |
| 32 | Улугбек | Uzbekistan |
| 33 | Венера (Уз) | Cyprus |

### Offices that stayed on Russia calendar:
| Office ID | Office Name |
|-----------|------------|
| 2 | Сатурн |
| 3 | Марс (Нск) |
| 4 | Юпитер |
| 18 | Кассиопея |
| 19 | Андромеда |
| 21 | Пегас |
| 22 | ГолденСтар (Vietnam since 2023) |
| 23 | Феникс |
| 24 | Скорпион |
| 25 | Марс (СПб) |
| 27 | Венера (РФ) |
| 28 | Уран (РФ) |
| 29 | Плутон (РФ) |
| 30 | Альтаир |

## Employee Office Changes (cross-calendar)

Employees who changed offices (different offices in different years) include cases that cross calendar boundaries:

Examples from timemachine data:
- **abeloborodov**: Венера (2024-2025) → Сатурн (2026+) — Cyprus → Russia
- **aburiev**: Венера (2024) → Венера (РФ) (2025+) — Cyprus → Russia
- **adanilevskaya**: Сатурн (2024) → Уран (РФ) (2025+) — Russia → Russia (same calendar)
- **aenovikova**: Венера (РФ) (2024-2025) → Венера (2026+) — Russia → Cyprus
- **alaptev**: Марс (СПб) (2024) → Юпитер (2025+) — Russia → Russia (same calendar)

## #2876 Bug 2 — Calendar Switch Calculation Error

**Ticket**: #2876
**Bug**: Calculation error on edit/delete vacation after calendar change + event addition sequence
**Reproduction scenario**: Saturn office + Cyprus calendar change

The bug occurs when:
1. An office changes its production calendar (e.g., Russia → Cyprus)
2. The working day norms change (different holidays)
3. Vacation edit/delete triggers recalculation using the new calendar norms
4. But existing vacation day allocations were based on old calendar norms
5. This mismatch causes incorrect available days calculation

**EmployeeOfficeChangedProcessor** is present in release/2.1 (commit 07eaa225) and handles:
- Same-calendar office changes: immediate update
- Different-calendar mid-year changes: intentionally deferred (architectural decision)

**Status**: Fix infrastructure exists but Bug 2 (the specific calculation error scenario) may not be fully addressed.

## Test Implications

1. Employee moves from Russia-calendar office to Cyprus-calendar office mid-year
2. Employee moves from Cyprus-calendar office to Russia-calendar office
3. Office itself changes calendar (since_year boundary)
4. Vacation spanning the calendar change boundary
5. Vacation edit/delete after calendar change
6. Working day norm recalculation with different holiday sets

## References

- [[exploration/data-findings/cross-service-office-sync-divergence]]
- [[vacation-service]]
- [[external/tickets/sprint-16-overview]]
- [[investigations/cs-office-settings-unimplemented]]

---
type: exploration
tags:
  - database
  - calendar
  - production-calendar
  - norm
  - schema
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[architecture/database-schema]]'
  - '[[analysis/office-period-model]]'
  - '[[modules/calendar-service]]'
branch: release/2.1
---
# Calendar Schema Deep Dive

8 tables in `ttt_calendar`. Simple but critical for norm calculations.

## Production Calendars (10)

Country-based calendars: Russia (dominant, data since 2013), Germany, Georgia, Armenia, Vietnam, Cyprus, France, Montenegro, Uzbekistan, Empty (no holidays).

**calendar_days**: Overrides from standard work schedule. Each record: date, duration (0=holiday, 7=short day 7h), reason, calendar_id.

| Calendar | Days | Holidays | Short days | Range |
|----------|------|----------|------------|-------|
| Russia | 275 | 210 | 62 | 2013-2026 |
| Cyprus | 40 | 40 | 0 | 2024-2026 |
| Vietnam | 39 | 39 | 0 | 2024-2026 |
| France | 29 | 29 | 0 | 2024-2026 |
| Germany | 29 | 29 | 0 | 2024-2026 |
| Montenegro | 27 | 27 | 0 | 2024-2025 |
| Uzbekistan | 25 | 19 | 5 | 2024-2026 |
| Georgia | 22 | 22 | 0 | 2024-2025 |
| Armenia | 17 | 17 | 0 | 2024-2025 |

Only Russia and Uzbekistan have short working days (7h instead of 8h).

## Office-Calendar Mapping

**Critical pattern**: `since_year` determines which calendar applies for which year. Multiple offices transitioned from Russian to country-specific calendars in 2024:

| Office | Calendar 2023 | Calendar 2024+ |
|--------|---------------|----------------|
| Венера (418 emp) | Russia | Cyprus |
| Нептун | Russia | Cyprus |
| Плутон | Russia | Cyprus |
| Уран | Russia | Cyprus |
| Титан (Черногория) | Russia | Cyprus |
| Персей | Russia | Germany |
| Сириус (Париж) | Russia | France |
| Каллисто (Армения) | Russia | Armenia |
| Протей (Грузия) | Russia | Georgia |

Offices with only Russian calendar: Сатурн, Юпитер, Марс (Нск/СПб), Альтаир, Андромеда, Скорпион, Пегас, Феникс, Кассиопея, Венера (РФ), Уран (РФ), Плутон (РФ).

**Anomaly**: Венера (Уз) uses Cyprus calendar (not Uzbekistan) since 2024 — possible misconfiguration.

## Impact on Norm Calculations

Working hours norm = (working days in month × 8) - (short days × 1). The production calendar determines:
1. Which days are working days (excluding holidays)
2. Which working days are shortened (7h vs 8h)
3. Monthly norm per employee (based on their salary office's calendar)

This directly feeds into: [[patterns/vacation-day-calculation]], [[REQ-statistics]] individual norm, budget norm deviations.

## Schema Notes

- `office` table (28 rows) mirrors `ttt_backend.office` (32 rows) — 4 fewer offices in calendar service (likely including "Не указано" and other legacy entries)
- `cs_sync_status/cs_sync_failed_entity` — calendar service also syncs with CompanyStaff
- `shedlock` — distributed lock for calendar sync jobs

See also: [[architecture/database-schema]], [[analysis/office-period-model]], [[modules/calendar-service]]

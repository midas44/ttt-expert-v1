---
type: module
tags:
  - calendar
  - production-calendar
  - norm
  - deep-dive
  - working-days
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[architecture/database-schema]]'
  - '[[exploration/data-findings/calendar-schema-deep-dive]]'
  - '[[modules/accounting-service-deep-dive]]'
  - '[[modules/admin-panel-deep-dive]]'
branch: release/2.1
---
# Calendar Service Deep Dive

The calendar microservice (`calendar/`) manages production calendars, office-calendar mappings, working day/hour calculations, and CompanyStaff office synchronization. Port 9580. Separate Spring Boot app with its own `ttt_calendar` database.

## 1. Architecture Overview

```
CalendarControllerV2 (/v2/calendars)     — Calendar CRUD
CalendarDaysController (/v2/days)        — Calendar day CRUD + working day calculation
OfficeCalendarController (/v2/offices)   — Office-calendar mapping
TestSalaryOfficeSyncController           — Manual CS sync trigger
    ↓
CalendarService / CalendarDaysService / OfficeCalendarService
    ↓
CalendarRepository / CalendarDaysRepository / OfficeCalendarRepository (JOOQ)
    ↓
ttt_calendar DB (8 tables)
    ↓ (events)
ApplicationEventPublisher → CalendarChangedApplicationEventListener → RabbitMQ
                          → CalendarDeletedApplicationEventListener → RabbitMQ
```

**Key concept**: Production calendars define exceptions to the standard Mon-Fri 8h work schedule. A `calendar_days` record means "this date deviates from normal" — duration=0 means holiday, duration=7 means short day, duration>0 on weekend means working weekend.

## 2. CalendarDaysServiceImpl — Core Business Logic

### Working Day Calculation Algorithm

```java
// CalendarDaysServiceImpl.calculateWorkingDaysInPeriod()
PeriodStatisticsBO response = new PeriodStatisticsBO();
response.setTotalDays(daysInBetween(datePeriod));  // inclusive: ChronoUnit.DAYS.between + 1

// Step 1: Calculate base working days (Mon-Fri count)
int workingDaysWithoutHolidays = calculateWorkingDaysInPeriodWithoutHolidays(datePeriod);

// Step 2: Base working hours = working days × reportingNorm (configurable, typically 8)
int workingHours = workingDaysWithoutHolidays * calendarProperties.getReportingNorm();

// Step 3: Apply calendar day compensations
int workingHoursCompensation = calculateHoursCompensationInPeriod(calendars);
int workingDaysCompensation = calculateWeekendDaysCompensationInPeriod(calendars);

response.setReportingNorm(workingHours - workingHoursCompensation);
response.setWorkingDays(workingDaysWithoutHolidays - workingDaysCompensation);
response.setWeekendDays(totalDays - workingDays);
```

### Hours Compensation Logic (calculateHoursCompensationInPeriod)

For each calendar day entry:

| Day Type | Duration | Compensation |
|----------|----------|-------------|
| Weekday (Mon-Fri) | > 0 (short day) | `+= reportingNorm - duration` (e.g., 8-7=1h) |
| Weekend (Sat-Sun) | > 0 (working weekend) | `-= duration` (adds hours back) |
| Weekday (Mon-Fri) | = 0 (holiday) | `+= reportingNorm` (full day removed) |

### Working Days Compensation Logic (calculateWeekendDaysCompensationInPeriod)

| Day Type | Duration | Compensation |
|----------|----------|-------------|
| Weekend (Sat-Sun) | > 0 (working weekend) | `-= 1` (adds working day) |
| Weekday (Mon-Fri) | = 0 (holiday) | `+= 1` (removes working day) |

### Cross-Year Calendar Resolution

```java
// getCalendarDays() — handles period spanning two calendar years
Optional<OfficeCalendar> startDateYearCalendar = officeCalendarRepository
    .findYearLessOrEqual(officeId, startDate.getYear());
Optional<OfficeCalendar> endDateYearCalendar = officeCalendarRepository
    .findYearLessOrEqual(officeId, endDate.getYear());

if (startYear != endYear && both present) {
    // Split: query start year calendar up to Dec 31, then end year calendar from Jan 1
    request.setCalendarId(startDateYearCalendar.get().getCalendarId());
    request.setEndDate(startDate.with(lastDayOfYear()));
    // ... then switch calendar for end year portion
}
```

**Design issue**: `whetherStartAndEndDatesAreInSameYear()` returns `true` when years differ but one Optional is empty — this silently falls through to the else branch which uses only the start year calendar. No error is raised.

### Changed Days Merging

`mergeChangedDays()` allows callers to pass hypothetical day changes (for "what-if" calculations):
- If a changed day matches an existing calendar day, the duration is overridden
- If it doesn't match, a new CalendarDays entry is added
- Days outside the period are filtered out afterward

### CalendarUtils.calculateDiff

```java
// Determines if a calendar day change adds or removes a working day
public static int calculateDiff(LocalDate date, Integer prevDuration, Integer newDuration) {
    boolean isPrevDayOff = isDayOff(date, prevDuration);
    boolean isNewDayOff = isDayOff(date, newDuration);
    if (!isPrevDayOff && isNewDayOff) return -1;  // lost a working day
    if (isPrevDayOff && !isNewDayOff) return 1;   // gained a working day
    return 0;
}

// isDayOff: if customDuration != null → dayOff iff duration == 0
//           if customDuration == null → dayOff iff Saturday or Sunday
```

## 3. CalendarProperties — Configuration

```java
@ConfigurationProperties("calendar")
public class CalendarProperties {
    private List<DayOfWeek> weekends;   // Configurable weekend days (typically [SATURDAY, SUNDAY])
    private Integer reportingNorm;       // Hours per working day (typically 8)
}
```

**Design note**: Weekends and reporting norm are configurable per deployment, not per office. All offices share the same weekend definition. Country-specific holidays are handled through production calendar entries, not weekend configuration.

## 4. Calendar CRUD (CalendarServiceImpl)

Simple CRUD for named production calendars (e.g., "Russia", "Germany", "Cyprus").

```java
// create() — sets createdAt/updatedAt from TimeUtils, createdBy/updatedBy from current user login
// update() — sets updatedAt/updatedBy, name is nullable (skipped if null)
// delete() — simple repository delete + log
// findAll() — paginated, sorted by name ASC
```

**Design issue**: `update()` does `calendar.setId(calendar.getId())` — redundant self-assignment (no-op but suggests copy-paste artifact).

**Design issue**: `delete()` has no cascade check — deleting a calendar that has associated calendar_days or office_calendar entries may fail at DB level or leave orphaned records depending on FK constraints.

## 5. Calendar Days CRUD (CalendarDaysServiceImpl)

### Create
```java
// create(CalendarDaysCreateRequestBO)
// 1. Build entity from request (date, duration, reason, calendarId)
// 2. Fill audit fields (createdAt, createdBy)
// 3. Save to DB
// 4. Calculate diff (was it a working day before? is it now?)
// 5. Find all offices using this calendar for this year
// 6. Publish CalendarUpdatedEvent with diff per office
```

### Patch
```java
// patch(dayId, CalendarDaysPatchRequestBO)
// Only updates reason field (if non-null)
// Does NOT publish any event (reason change doesn't affect working days)
```

**Design issue**: Patch only allows changing `reason`. Cannot change `date` or `duration` via PATCH. To change duration, must delete and recreate — which triggers two events instead of one.

### Delete
```java
// delete(Integer id)
// 1. Load entity
// 2. Calculate diff
// 3. Find affected offices
// 4. If diff != 0, publish CalendarUpdatedEvent
// 5. Delete from DB
// 6. Always publish CalendarDeletedEvent (even if diff == 0)
```

### Legacy v1 Methods
- `createOrUpdateCalendar()` — @Deprecated, hardcoded to `RUSSIAN_CALENDAR_ID`, upsert pattern
- `find(year, startDate, endDate)` — @Deprecated, hardcoded to `RUSSIAN_CALENDAR_ID`
- `update(calendarId, date, workNorm, reason)` — hardcoded to `RUSSIAN_CALENDAR_ID`

## 6. OfficeCalendarServiceImpl — Office-Calendar Mapping

### Update Logic (Calendar Assignment)

```java
// update(officeId, calendarId) — complex conditional logic for 3 scenarios
int year = LocalDate.now().getYear();

// Scenario 1: No calendar exists for this office → create initial mapping for current year
if (!currentYearExists) {
    setInitialCalendarForOfficeAndSendEvent(officeId, calendarId);
}

// Scenario 2: Current year calendar matches + next year mapping exists → remove next year override
// (revert to single calendar)
if (currentYearCalendarEquals && nextYearExists) {
    setSameCalendarForNextYearAndSendEvent(...);  // deletes next year record
}

// Scenario 3: Different calendar or no next year record → create/update next year mapping
else {
    setNewCalendarForNextYearAndSendEvent(...);
}
```

**Key pattern**: Calendar changes always take effect **next year**, never retroactively. The `since_year` column in `office_calendar` determines when a calendar mapping starts. `findYearLessOrEqual(officeId, year)` returns the most recent applicable mapping.

**Event publishing on calendar change**: When reassigning an office's calendar, the service:
1. Queries all calendar days for the OLD calendar (for next year) → publishes decrease events
2. Saves the new mapping
3. Queries all calendar days for the NEW calendar (for next year) → publishes increase events
4. Sends combined CalendarUpdatedEvent

### Design Issues
- `update()` uses `LocalDate.now()` directly — not the test clock. Calendar mapping changes in timemachine environment will use real system time.
- No validation that the calendar has days defined for the target year. Assigning "Armenia" calendar to an office for 2027 when no Armenian holidays are defined for 2027 silently produces no events.

## 7. Validators (8 Custom)

| Validator | Target | Logic | Error Message |
|-----------|--------|-------|---------------|
| `@CalendarIdExists` | Long field | `calendarService.exists(id)` | "Calendar id not found" |
| `@CalendarDaysIdExists` | Integer field/param | `calendarDaysService.exists(id)` | "Calendar days id not found" |
| `@CalendarNameExists` | String field | `calendarService.existsByName(name)` — creation only | "Calendar name already exists" |
| `@CalendarExists` | String field | `existsByNameExceptId(calendarId, name)` — update, extracts calendarId from path | "Calendar name already exists" |
| `@DateUniqueOnCreate` | Class-level on DTO | `calendarDaysService.exists(calendarId, date)` | "Date must be unique" |
| `@DateUniqueOnPatch` | LocalDate field | `existsExceptId(calendarId, date, dayId)` — extracts dayId from path | "Date must be unique" |
| `@DatePeriodValid` | Class-level on DTO | `!start.isAfter(end)` | "Start date should be before or equals to end" |
| `@OfficeIdExists` | Long field | `officeService.exists(id)` | "Office id not found" |

**All validators return `true` when input is null** — they don't enforce required. `@NotNull` must be used separately.

`WebUtil.getPathValue(name)` extracts path variables from the current HTTP request for validators that need cross-field context.

## 8. REST API Endpoints

### Calendar Days (`/v2/days`)

| Method | Path | Auth | Validation | Notes |
|--------|------|------|-----------|-------|
| GET | `/v2/days` | `AUTHENTICATED_USER` or `CALENDAR_VIEW` | Pagination defaults: page=0, size=100 | Search with filters |
| POST | `/v2/days` | `ADMIN` or `CHIEF_ACCOUNTANT` | calendarId exists, date unique, duration 0-12, reason non-empty | Publishes CalendarUpdatedEvent |
| PATCH | `/v2/days/{dayId}` | `ADMIN` or `CHIEF_ACCOUNTANT` | dayId exists, reason min 1 char | Only updates reason, no event |
| DELETE | `/v2/days/{dayId}` | `ADMIN` or `CHIEF_ACCOUNTANT` | None on path param! | Publishes both Updated + Deleted events |
| GET | `/v2/days/by-date` | `AUTHENTICATED_USER` or `CALENDAR_VIEW` | calendarId + date required | Returns null if not found (not 404) |

**Design issue**: DELETE endpoint has no `@CalendarDaysIdExists` validation on the path variable. If the ID doesn't exist, `calendarDaysRepository.getById(id)` will return null and cause NPE.

### Calendars (`/v2/calendars`)

| Method | Path | Auth | Validation |
|--------|------|------|-----------|
| GET | `/v2/calendars` | `AUTHENTICATED_USER` or `CALENDAR_VIEW` | Pagination |
| POST | `/v2/calendars` | `ADMIN` or `CHIEF_ACCOUNTANT` | Name unique (`@CalendarNameExists`) |
| PATCH | `/v2/calendars/{calendarId}` | `ADMIN` or `CHIEF_ACCOUNTANT` | ID exists, name unique except self |
| DELETE | `/v2/calendars/{calendarId}` | `ADMIN` or `CHIEF_ACCOUNTANT` | ID exists |

### Office Calendars (`/v2/offices`)

| Method | Path | Auth | Validation |
|--------|------|------|-----------|
| GET | `/v2/offices` | `AUTHENTICATED_USER` or `CALENDAR_VIEW` | Year filter, active filter |
| PUT | `/v2/offices/{officeId}/calendars/{calendarId}` | `ADMIN` or `CHIEF_ACCOUNTANT` | officeId + calendarId validated |
| GET | `/v2/offices/{officeId}/year/{year}` | `AUTHENTICATED_USER` or `CALENDAR_VIEW` | Returns null if not found |

### DTO Validation Rules

**CalendarDaysCreateRequestDTO**:
- `calendarId`: Long, `@CalendarIdExists`
- `date`: LocalDate, `@NotNull`, format `yyyy-MM-dd`
- `duration`: Integer, `@NotNull`, `@Min(0)`, `@Max(12)`
- `reason`: String, `@NotNull`, `@Size(min=1)`
- Class-level: `@DateUniqueOnCreate`

**CalendarDaysPatchRequestDTO**:
- `reason`: String, `@Size(min=1)` (optional, null means no change)

**CalendarCreateRequestDTO**:
- `name`: String, `@CalendarNameExists` (uniqueness check)

**CalendarUpdateRequestDTO**:
- `name`: String, `@CalendarExists` (uniqueness except self)

## 9. Event Publishing — RabbitMQ Integration

### CalendarUpdatedEvent Flow
```
CalendarDaysServiceImpl.create()/delete() or OfficeCalendarServiceImpl.update()
  → eventPublisher.publishEvent(new CalendarUpdatedEvent(payload))
    → CalendarEventListener catches Spring ApplicationEvent
      → Publishes CalendarChangedApplicationEvent
        → CalendarChangedApplicationEventListener (@Async @EventListener)
          → rabbitTemplate.convertAndSend(
              exchange: "ttt.calendar.topic",
              routingKey: "calendar-changed",
              message: CalendarChangedEvent with header TYPE
            )
```

### CalendarDeletedEvent Flow
```
CalendarDaysServiceImpl.delete()
  → eventPublisher.publishEvent(new CalendarDeletedEvent(payload))
    → CalendarDeletedApplicationEventListener (@Async @EventListener)
      → rabbitTemplate.convertAndSend(
          exchange: "ttt.calendar.deleted.topic",
          routingKey: "calendar-deleted",
          message: CalendarDeletedEvent with header TYPE
        )
```

**Payload structure**:
- `CalendarChangedEventPayload` → list of `CalendarOfficeChangedPayload` (one per affected office)
  - Each contains `officeId` + list of `CalendarDaysChanged` (date, diff, duration, reason)
- `CalendarDeletedEventPayload` → `date` + list of `officeIds`

**Consumers**: TTT backend and Vacation service listen to these events to recalculate norms and resolve absence conflicts.

## 10. CompanyStaff Synchronization

### CSSyncScheduler
- Cron: `${companyStaff.cron}` (configurable)
- ShedLock: `CSSyncScheduler.doCsSynchronization`
- Calls `CSSyncLauncher.sync(false)` — incremental sync

### CSFullSyncScheduler
- Separate full sync (includes inactive offices)

### CSSalaryOfficeSynchronizer
- Fetches salary offices from CS API via `CompanyStaffV2Client` (page size 50)
- For each CS salary office:
  1. Get or create local `Office` entity (by CS ID)
  2. Update name, nameLatin, lastSyncTime, active status
  3. Set `salary = (id != UNDEFINED_ID)` — the "Не указано" office is not a salary office
  4. If active AND no office_calendar exists AND office ID is in `DEFAULT_CALENDAR_OFFICE_IDS`:
     - Create office_calendar with `RUSSIAN_CALENDAR_ID` for current year
  5. If active AND office_calendar exists with null calendarId AND in default list:
     - Set calendarId to `RUSSIAN_CALENDAR_ID`

**Design issue**: New offices from CS get Russian calendar by default only if their ID is in the hardcoded `DEFAULT_CALENDAR_OFFICE_IDS` set. Non-Russian offices added in CS require manual calendar assignment in TTT.

## 11. Design Issues Catalog

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| 1 | **Critical** | `CalendarDaysController.delete()` | No `@CalendarDaysIdExists` validation on dayId path variable — NPE on non-existent ID |
| 2 | **Major** | `OfficeCalendarServiceImpl.update()` | Uses `LocalDate.now()` instead of test clock — timemachine env gets real dates |
| 3 | **Major** | `CalendarDaysServiceImpl` | Patch only allows `reason` change. Duration/date changes require delete+recreate = 2 events |
| 4 | **Major** | `CalendarServiceImpl.delete()` | No cascade check — may fail silently or leave orphaned calendar_days/office_calendar |
| 5 | **Minor** | `CalendarServiceImpl.update()` | `calendar.setId(calendar.getId())` — redundant self-assignment |
| 6 | **Minor** | `CalendarDaysServiceImpl.whetherStartAndEndDatesAreInSameYear()` | Returns true when cross-year but one Optional empty — silently uses wrong calendar |
| 7 | **Minor** | `CSSalaryOfficeSynchronizer` | Default Russian calendar assignment only for hardcoded office IDs. New non-Russian offices need manual setup |
| 8 | **Minor** | `CalendarDaysController.findByDate()` | Returns null body instead of 404 when no calendar day found |
| 9 | **Minor** | `OfficeCalendarServiceImpl.update()` | No validation that target calendar has days for the target year |
| 10 | **Minor** | `CalendarDaysServiceImpl` | Deprecated v1 methods hardcoded to `RUSSIAN_CALENDAR_ID` still in interface |

## 12. Boundary Values for Testing

- Duration: min=0 (holiday), max=12, typical values: 0, 7 (short day), 8 (regular)
- Reason: min 1 char, no max defined
- Calendar name: must be unique, can be empty string? (no `@NotNull` on CalendarCreateRequestDTO.name)
- Cross-year periods: Dec 31 → Jan 1 transitions, different calendars per year
- Weekend overrides: Saturday/Sunday with duration > 0 (working weekends)
- Weekday holidays: Mon-Fri with duration = 0
- Page defaults: page=0, pageSize=100 for calendar days
- Authorities: ADMIN, ROLE_CHIEF_ACCOUNTANT for writes; AUTHENTICATED_USER, CALENDAR_VIEW for reads

See also: [[exploration/data-findings/calendar-schema-deep-dive]], [[modules/accounting-service-deep-dive]], [[patterns/vacation-day-calculation]]

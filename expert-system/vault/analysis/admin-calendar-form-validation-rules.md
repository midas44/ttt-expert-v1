---
type: analysis
tags:
  - admin
  - calendar
  - validation
  - phase-b-prep
  - form-rules
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[admin-panel-pages]]'
  - '[[production-calendar-management]]'
  - '[[calendar-service]]'
  - '[[accounting-backend]]'
  - '[[tracker-integration-deep-dive]]'
branch: release/2.1
---
# Admin & Calendar Form Validation Rules

Field-level validation rules for admin panel and calendar service operations — extracted from frontend + backend code for Phase B test case generation.

## 1. Calendar CRUD

### Backend — CalendarCreateRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| name | @CalendarNameExists | String | YES (implied) | Name must not already exist |

**CalendarNameExistsValidator:** Checks uniqueness of calendar name in the system.

### Backend — CalendarUpdateRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| name | @CalendarExists | String | YES (implied) | Name must not conflict with other calendars (excludes current via path ID) |

**CalendarExistsValidator:** Uses `WebUtil.getPathValue("calendarId")` to exclude the calendar being updated from the uniqueness check.

### Frontend — AddCalendarValidationSchema.ts (Yup)

| Field | Rule | Detail |
|-------|------|--------|
| calendarName | Required | Trimmed string, required |
| calendarName | Unique check | Custom test `calendarExists` — case-insensitive check against existing names via context |

## 2. Calendar Events (Days)

### Backend — CalendarDaysCreateRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| calendarId | @CalendarIdExists | Long | YES | Calendar must exist |
| date | @NotNull | LocalDate | YES | Format yyyy-MM-dd |
| duration | @NotNull, @Min(0), @Max(12) | Integer | YES | 0-12 hours |
| reason | @NotNull, @Size(min=1) | String | YES | At least 1 character |
| (class) | @DateUniqueOnCreate | — | — | Date must be unique per calendar |

### Backend — CalendarDaysPatchRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| reason | @Size(min=1) | String | NO | If provided: 1+ chars |

**Asymmetry:** Create requires all fields; patch only validates reason if provided. Duration and date are immutable on patch.

### Frontend — EventValidationSchema.js (Yup)

| Field | Rule | Detail |
|-------|------|--------|
| eventReason | Required | Trimmed string, required |

**No frontend validation for duration/date** — these are handled by the calendar widget/datepicker constraints, not Yup.

## 3. Salary Office / Period Assignment

### Backend — PeriodRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| officeId | @OfficeIdExists | Long | YES (implied) | Office must exist |
| calendarId | @CalendarIdExists | Long | YES (implied) | Calendar must exist |
| datePeriod | @Valid | DatePeriodDTO | NO | Cascading validation |
| changedCalendarDays | @Valid | List\<String\> | NO | — |

### Backend — DatePeriodDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| startDate | — | LocalDate | NO | — |
| endDate | — | LocalDate | NO | — |
| (class) | @DatePeriodValid | — | — | endDate >= startDate |

**DatePeriodValidValidator:** Validates endDate >= startDate only if both dates are non-null.

## 4. Admin Tracker Configuration

### Frontend — TrackerValidationSchema.js (Yup)

| Field | Rule | Detail |
|-------|------|--------|
| type | Required | Object (select dropdown) |
| trackerUrl | Required | Trimmed string |
| login | Conditional | Required for JIRA_TOKEN, JIRA_LOGPASS tracker types |
| credentials | Conditional | Required for GITLAB, REDMINE, YOU_TRACK, JIRA_TOKEN |
| password | Conditional | Required only for JIRA_LOGPASS |

**TrackerEditValidationSchema:** Factory function that accepts `initialValues` — only enforces credential requirements if value changed from initial.

### Frontend — Admin General Validators (validation.js)

| Validator | Rule | Used For |
|-----------|------|----------|
| Required | Non-empty | General required fields |
| OnlyEnAndNumbers | `/^[a-zA-Z0-9.]*$/g` | Project names |
| LessThanTwoChars | length >= 2 | Project names |
| IsUrl | Domain/path regex | Tracker URLs |
| IsSelect | Object with label+value OR string | Dropdown selections |

## 5. Admin Project Forms

No Yup schema found for project CRUD — uses the general admin validators above applied to individual fields in form components.

## Key Test Case Implications

1. **Calendar name uniqueness is case-sensitive in backend** — but frontend does case-insensitive check; test case sensitivity gap
2. **Calendar event duration 0-12** — test 13, -1, null boundary values
3. **Calendar event reason required on create only** — patch allows omitting reason entirely
4. **Calendar event date uniqueness per calendar** — test duplicate dates within same calendar
5. **Salary office existence validators** — test with non-existent officeId/calendarId
6. **DatePeriod null pass-through** — both dates null passes validation (no period constraint)
7. **Tracker credential conditional logic** — test each tracker type's required field matrix
8. **Project name regex** — test special characters, spaces, unicode in project names

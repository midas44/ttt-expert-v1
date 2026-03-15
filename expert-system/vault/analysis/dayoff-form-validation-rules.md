---
type: analysis
tags:
  - day-off
  - validation
  - phase-b-prep
  - form-rules
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[sick-leave-dayoff-business-rules-reference]]'
  - '[[day-off-service-implementation]]'
  - '[[frontend-day-off-module]]'
  - '[[day-off-pages]]'
branch: release/2.1
---
# Day-Off Form Validation Rules

Field-level validation rules for day-off operations — extracted from frontend + backend code for Phase B test case generation.

## Frontend Validation

### TransferDaysoffModal (Reschedule)

| Field | Rule | Detail |
|-------|------|--------|
| dayOffTransferDate | Required | Submit disabled until value selected |
| dayOffTransferDate | minDate | >= originalDate (future holidays) OR >= yesterday (past holidays) |
| dayOffTransferDate | maxDate | originalDate + 1 year - 1 day (end of next year) |
| dayOffTransferDate | Day filter | Weekends disabled, existing day-off dates disabled, short-day conflicts (duration=7) disabled |
| dayOffTransferDate | Working weekend exception | Working weekends ARE selectable despite being weekends |

### WeekendRedirectFormContainer (Approver Change)

| Field | Rule | Detail |
|-------|------|--------|
| APPROVER | Required | Must select approver; error key `vacation.required` |

### No Yup Schema

Day-off uses imperative validation (submit button disabled state), not Formik/Yup declarative schema.

## Backend Validation — Create

### EmployeeDayOffCreateRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| publicDate | @EmployeeDayOffPublicDateExists | LocalDate | YES (implied) | Must exist in calendar AND no existing request |
| personalDate | @EmployeeDayOffPersonalDateExists | LocalDate | YES (implied) | Must be unique (no other day-off with same personal date) |
| duration | — | Integer | NO | No DTO-level validation |
| reason | — | String | NO | No DTO-level validation |

### Custom Validators

**EmployeeDayOffPublicDateExistsValidator** (3-step check):
1. If day-off request already exists for publicDate → FAIL (`EMPLOYEE_DAY_OFF_PUBLIC_DATE_EXISTS`)
2. Check office calendar for date OR employee's existing day-offs
3. If neither found → FAIL (`PUBLIC_DATE_NOT_FOUND_IN_CALENDAR`)
4. Pass only if: no existing request AND date exists in calendar/day-offs

**EmployeeDayOffPersonalDateExistsValidator**:
- Null → valid (pass-through)
- Personal date already used → FAIL

## Backend Validation — Patch (Reschedule)

### EmployeeDayOffPatchRequestDTO

| Field | Annotation | Constraints |
|-------|-----------|-------------|
| personalDate | @EmployeeDayOffPersonalDateExists | Must be unique |

Only validates the new personal date. Original public date preserved.

## Backend Validation — Approver Operations

### ChangeEmployeeDayOffApproverDTO
| Field | Annotation | Constraints |
|-------|-----------|-------------|
| approver | @EmployeeLoginExists | Must exist in system |

### EmployeeDayOffApproverCreateRequestDTO
| Field | Annotation | Constraints |
|-------|-----------|-------------|
| dayOffId | @NotNull | Required |
| login | @NotNull | Required |

### EmployeeDayOffApproverPatchRequestDTO
| Field | Annotation | Constraints |
|-------|-----------|-------------|
| status | @NotNull | Required (approval status enum) |

## Calendar Service — Day Creation

### CalendarDaysCreateRequestDTO

| Field | Annotation | Constraints |
|-------|-----------|-------------|
| calendarId | @CalendarIdExists | Calendar must exist |
| date | @NotNull | Required, format yyyy-MM-dd |
| duration | @NotNull, @Min(0), @Max(12) | 0-12 hours range |
| reason | @NotNull, @Size(min=1) | Required, at least 1 char |
| (class) | @DateUniqueOnCreate | Date must be unique per calendar |

### CalendarDaysPatchRequestDTO
| Field | Annotation | Constraints |
|-------|-----------|-------------|
| reason | @Size(min=1) | If provided: 1+ chars |

## Key Test Case Implications

1. **No duration/reason DTO validation on day-off**: Validated at service level, not DTO — test missing/invalid values
2. **Public date dual check**: Must exist in calendar + no prior request — test both conditions
3. **Personal date uniqueness**: Test duplicate personal dates across day-offs
4. **Calendar duration 0-12**: Test boundary values 0, 12, 13, -1
5. **Calendar reason required on create but optional on patch**: Asymmetry
6. **UI vs API weekend gap**: Frontend blocks weekends, API accepts them (known BUG-DO-5)
7. **Working weekend exception**: Calendar days with type "working weekend" bypass weekend block
8. **maxDate calculation**: originalDate + 1 year - 1 day — test boundary

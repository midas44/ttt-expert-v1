---
type: analysis
tags:
  - validation
  - gap-analysis
  - frontend
  - backend
  - cross-cutting
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[modules/vacation-service-deep-dive]]'
  - '[[modules/ttt-report-service-deep-dive]]'
  - '[[modules/dayoff-service-deep-dive]]'
  - '[[modules/sick-leave-service-deep-dive]]'
  - '[[modules/calendar-service-deep-dive]]'
  - '[[modules/accounting-service-deep-dive]]'
branch: release/2.1
---
# Frontend-Backend Validation Gap Analysis

Systematic comparison of frontend (React/Formik/Yup) validation against backend (Java/Spring/Bean Validation) for all major modules. Gaps create test scenarios where one layer accepts data the other rejects, or where server errors bypass client-side feedback.

## 1. Vacation — Most Complex Gap Profile

### Frontend Validation (vacationValidationForm.js — imperative)
- `startDate`, `endDate`: valid moment dates, not crossing existing vacations (client-side overlap check)
- `vacationDays`: minimum `VACATION_MIN_DAYS` constant
- `paymentMonth`: propagates API errors
- `comment`: propagates API errors
- No Yup schema — pure imperative validation on form change

### Backend Validation ([[vacation-service-deep-dive]])
- **VacationCreateValidator**: 10+ checks including status, available days (AV flag), date overlap with ALL other vacations, employee existence, approver existence, vacation type vs payment type combinations
- **VacationUpdateValidator**: Status transition matrix (only from NEW/APPROVED), immutable fields check, date re-overlap, available days re-check
- **DTO annotations**: @NotNull on dates, @Size on comment

### Gaps

| Gap | Frontend | Backend | Test Scenario |
|-----|----------|---------|---------------|
| **Available days check** | Not validated | AV flag check, available days recalculation | Create vacation exceeding available days with AV=true — frontend accepts, backend rejects |
| **Status transition** | Not validated | Status matrix enforced | Try to edit REJECTED vacation — frontend shows form, backend returns error |
| **Vacation type + payment type** | Not validated | Combination rules enforced | Set incompatible type/payment combination |
| **Approver existence** | Not validated | Employee lookup | Set non-existent approver ID |
| **Cross-user overlap** | Overlap check uses current user data only | Server checks ALL vacations | Two users creating overlapping vacations simultaneously |
| **Date ordering** | Not explicitly validated | Implicit in overlap logic | Start date after end date |

### Missing Frontend Validation
- No `@NotNull` equivalent for required fields (relies on form UX disabling submit)
- No vacation type validation
- No advance vacation limit check (backend: 14 day max advance)

## 2. Day-Off — NO Frontend Validation Schema

### Frontend Validation
**NONE FOUND.** No Yup schema, no imperative validator. Day-off creation/editing relies entirely on backend validation.

### Backend Validation ([[dayoff-service-deep-dive]])
- **EmployeeDayOffCreateValidator**: Date uniqueness per employee, not in past, within report period, calendar working day check
- **EmployeeDayOffEditValidator**: Same + status constraints (only PENDING or APPROVED can be edited)
- **DTO annotations**: @NotNull on date and comment
- Optional approval: separate validator for approver changes

### Gaps

| Gap | Frontend | Backend | Test Scenario |
|-----|----------|---------|---------------|
| **All validation** | None | Full server-side | Submit empty form — no client feedback, server returns 400 |
| **Date in past** | None | Blocked | Select past date in UI — no frontend warning |
| **Working day check** | None | Calendar lookup | Select weekend/holiday — frontend allows, backend rejects |
| **Duplicate date** | None | Per-employee uniqueness | Create two day-offs for same date |

**This is the largest gap** — user experience is entirely dependent on server error messages being properly displayed.

## 3. Sick Leave — Partial Coverage

### Frontend Validation (Yup schemas)
- **Create**: `employee` required, `startDate` required, `endDate` required, `number` max 40 chars
- **Edit**: `startDate` required, `endDate` required, `number` max 40 chars
- **Close**: `number` required, non-empty, max 40 chars

### Backend Validation ([[sick-leave-service-deep-dive]])
- **SickLeaveValidator**: Close flow validation (status must be OPEN to close), force flag, number required on close
- **DTO**: CreateDTO has @NotNull on startDate, endDate, employeeLogin; PatchDTO extends CreateDTO (inherits all annotations)
- No explicit number length validation in backend

### Gaps

| Gap | Frontend | Backend | Test Scenario |
|-----|----------|---------|---------------|
| **Number max length** | 40 chars | Not validated | Submit number with 100+ chars — frontend blocks, backend accepts |
| **Date ordering** | Not validated | Not explicit | startDate after endDate — both layers may accept |
| **Status check on close** | Not validated | OPEN required | Close already-closed sick leave — frontend shows form, backend rejects |
| **Employee login format** | Required (object) | @NotNull (string) | Type mismatch potential |
| **Force flag** | Not in UI | Server-side logic | Force-close bypasses date validation |

### Unique Frontend Rule
- `number` max 40 chars — **frontend-only**, backend has no length constraint. This means the frontend is MORE restrictive than the backend.

## 4. Reports (Task Reports) — Minimal Frontend Validation

### Frontend Validation
- **SearchTaskValidationSchema**: Complex task name validation (format, @ signs, login, edit permission)
- **No effort validation schema found** — no Yup schema for report hours

### Backend Validation ([[ttt-report-service-deep-dive]])
- **Create**: @Min(1) on effort (hours)
- **Edit**: @Min(0) on effort (allows zero to "clear" a report)
- Status-based validation: can't edit confirmed/locked reports
- Report period validation: date within open period

### Gaps

| Gap | Frontend | Backend | Test Scenario |
|-----|----------|---------|---------------|
| **Effort minimum** | Not validated | @Min(1) create, @Min(0) edit | Submit 0 hours on create — frontend allows, backend rejects |
| **Effort maximum** | Not validated | None defined | Submit 999 hours — both layers accept |
| **Report period** | Not validated | Period must be open | Report in closed period — frontend shows form, backend rejects |
| **Report lock** | Not validated | Lock management | Edit locked report — frontend shows edit UI, backend rejects |
| **Task name format** | Complex validation | Basic string check | Frontend validates more than backend on task name format |

## 5. Calendar/Production Calendar — Backend-Heavy

### Frontend Validation (AddCalendarValidationSchema.ts + EventValidationSchema.js)
- `calendarName`: required, unique (case-insensitive, client-side check against loaded calendars)
- `eventReason`: required, trimmed

### Backend Validation ([[calendar-service-deep-dive]])
- **CalendarDaysCreateRequestDTO**: @CalendarIdExists, @DateUniqueOnCreate, @NotNull date, @Min(0) @Max(12) duration, @NotNull @Size(min=1) reason
- **CalendarDaysPatchRequestDTO**: @Size(min=1) reason
- **CalendarCreateRequestDTO**: @CalendarNameExists
- **CalendarUpdateRequestDTO**: @CalendarExists (unique except self)
- **DatePeriodDTO**: @DatePeriodValid (start <= end)

### Gaps

| Gap | Frontend | Backend | Test Scenario |
|-----|----------|---------|---------------|
| **Duration range** | Not validated | @Min(0) @Max(12) | Enter duration 15 — frontend allows, backend rejects |
| **Date uniqueness** | Not validated | @DateUniqueOnCreate | Create duplicate date for same calendar |
| **Calendar ID existence** | Not validated | @CalendarIdExists | API call with non-existent calendarId |
| **Calendar name unique** | Client-side check (case-insensitive) | Server-side check | Race condition: two users creating same name simultaneously |
| **Date format** | DatePicker enforces format | @JsonFormat yyyy-MM-dd | Invalid date string via API |

## 6. Accounting — NO Frontend Validation Found

### Frontend Validation
**No Yup schemas found for accounting operations** (period changes, payment, corrections).

### Backend Validation ([[accounting-service-deep-dive]])
- **PayVacationServiceImpl**: 5-check payment validation (status, period, already paid, available days, vacation type)
- **OfficePeriodServiceImpl**: Period constraint (APPROVE_START <= REPORT_START), max 1-month change
- **EmployeeDaysServiceImpl**: Positive/negative correction branches, AV=false blocks negative corrections

### Gaps

| Gap | Frontend | Backend | Test Scenario |
|-----|----------|---------|---------------|
| **All payment validation** | None | 5 checks (same error code!) | All payment error cases return generic error to frontend |
| **Period change limits** | None | Max 1 month | Move period 3 months — frontend allows, backend rejects |
| **Correction sign** | None | AV-based logic | Negative correction with AV=false — opaque server error |

## 7. Cross-Cutting Findings

### Pattern: Frontend Validates Less Than Backend
In every module, the backend has significantly more validation rules than the frontend. This is architecturally appropriate for security, but creates UX gaps where users get generic server errors instead of field-specific feedback.

### Pattern: No Day-Off or Accounting Frontend Validation
Two entire functional areas have zero client-side validation, making server error display quality critical.

### Pattern: Frontend-Only Rules
- Sick leave `number` max 40 chars (not enforced server-side)
- Task name format regex (more restrictive than backend)
- Calendar name case-insensitive uniqueness check (backend is case-sensitive via SQL)

### Pattern: Imperative vs Declarative
- Vacation uses imperative Formik validation (harder to test, more flexible)
- All other modules use Yup declarative schemas (easier to test, more rigid)

### Test Priority Ranking (by gap severity)

1. **Day-off creation** — zero frontend validation, 100% backend-dependent
2. **Accounting operations** — zero frontend validation, opaque error codes
3. **Vacation available days** — critical business rule not checked client-side
4. **Report effort boundaries** — no frontend effort validation
5. **Sick leave status checks** — close flow not validated client-side
6. **Calendar duration range** — not validated frontend, 0-12 range backend

See also: [[modules/vacation-service-deep-dive]], [[modules/dayoff-service-deep-dive]], [[modules/sick-leave-service-deep-dive]], [[modules/ttt-report-service-deep-dive]], [[modules/calendar-service-deep-dive]], [[modules/accounting-service-deep-dive]]

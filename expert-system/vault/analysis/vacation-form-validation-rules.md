---
type: analysis
tags:
  - vacation
  - validation
  - phase-b-prep
  - form-rules
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[vacation-business-rules-reference]]'
  - '[[vacation-crud-api-testing]]'
  - '[[frontend-vacation-module]]'
  - '[[vacation-service]]'
branch: release/2.1
---
# Vacation Form Validation Rules

Field-level validation rules extracted from frontend + backend code for Phase B test case generation.

## Frontend Validation

**File:** `modules/vacation/services/validation/vacationValidationForm.js`

Custom Formik validation (not Yup schema). Rules:

| Field | Rule | Detail |
|-------|------|--------|
| startDate | Required | Must have both start+end or vacation days |
| endDate | Required | Same as above |
| startDate | Min duration | vacationDays >= VACATION_MIN_DAYS (=1) |
| startDate/endDate | Overlap check | Cannot overlap existing vacations (3-way: start-in-range, end-in-range, enclosing) |
| paymentMonth | Server error passthrough | Displays API error if returned |
| comment | Server error passthrough | Displays API error if returned |
| duration | Server error passthrough | Duration errors for insufficient days |

**Gap:** Frontend min days = 1, backend min days = 5 (REGULAR). Frontend passes all, backend rejects < 5 day REGULAR vacations.

## Backend Validation — Create

**DTO:** `AbstractVacationRequestDTO` → `VacationCreateRequestDTO`

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| login | @NotNull, @EmployeeLoginExists, @CurrentUser(create) | String | YES | Must exist; must be current user on create |
| startDate | @NotNull | LocalDate | YES | Cannot be in past; must <= endDate |
| endDate | @NotNull | LocalDate | YES | Must >= startDate |
| paymentType | @NotNull | Enum | YES | REGULAR or ADMINISTRATIVE |
| paymentMonth | — | LocalDate | NO | No constraints |
| comment | — | String | NO | No length limit in DTO |
| notifyAlso | @EmployeeLoginCollectionExists | List\<String\> | NO | All logins must exist |
| optionalApprovers | @EmployeeLoginCollectionExists | List\<String\> | NO | All logins must exist |

**Class-level validator** (`VacationCreateValidator`, 235 lines):
- Start date not in past
- startDate <= endDate
- REGULAR: min 5 calendar days (from `vacationProperties.getMinimalVacationDuration()`)
- ADMINISTRATIVE: any duration >= 1 day (skips duration check)
- Available days calculation against limits
- Next year vacation unavailable before Feb 1st (configurable)

## Backend Validation — Update

**DTO:** `VacationUpdateRequestDTO` extends `AbstractVacationRequestDTO`

| Field | Extra | Constraints |
|-------|-------|-------------|
| id | @NotNull, @Min(1) | Must reference existing vacation |
| (inherited) | Same as create | Excludes self from available days calc |

## Payment Type Impact

| Type | Min Duration | Duration Checks | Availability Checks |
|------|-------------|-----------------|---------------------|
| REGULAR | 5 days | Full | Full (paid days, limits) |
| ADMINISTRATIVE | 1 day | Skipped | Skipped |

## Key Test Case Implications

1. **Frontend-backend min days gap**: UI allows 1-day REGULAR vacation but API rejects < 5 days
2. **@CurrentUser on create only**: Update allows changing login (manager editing?)
3. **No comment length limit**: Potential for very long strings
4. **Next year Feb 1 cutoff**: Boundary test at Jan 31 vs Feb 1
5. **Overlap detection**: 3 patterns — start inside, end inside, enclosing existing
6. **optionalApprovers validation**: Each login checked individually

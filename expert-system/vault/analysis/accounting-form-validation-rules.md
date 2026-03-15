---
type: analysis
tags:
  - accounting
  - validation
  - phase-b-prep
  - form-rules
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[accounting-backend]]'
  - '[[reports-business-rules-reference]]'
  - '[[accounting-api-testing]]'
  - '[[payment-flow-live-testing]]'
  - '[[period-api-live-testing]]'
branch: release/2.1
---
# Accounting Form Validation Rules

Field-level validation rules for accounting operations — extracted from frontend + backend code for Phase B test case generation.

## 1. Period Management (Report/Approve Period)

### Backend — PeriodPatchRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| start | @NotNull | LocalDate | YES | Must be first day of month (documented, not DTO-enforced) |

**Minimal DTO** — only one field. Business logic (first-of-month, sequential advance) enforced at service level, not in DTO annotations.

### Frontend — OfficeValidationSchema.js (Yup)

| Field | Rule | Detail |
|-------|------|--------|
| reportDate | Required | string, Yup required |
| approveDate | Required | string, Yup required |

**Gap:** Frontend has two date fields (report + approve), backend DTO has one (`start`). Different endpoints for report vs approve period.

## 2. Vacation Payment

### Backend — VacationPaymentDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| payedAt | @JsonFormat("yyyy-MM-dd") | LocalDate | NO | Optional payment date |
| regularDaysPayed | @NotNull, @Range(0, 366) | Integer | YES | 0-366 days |
| administrativeDaysPayed | @NotNull, @Range(0, 366) | Integer | YES | 0-366 days |

**Class-level validation** (in service): `regularDaysPayed + administrativeDaysPayed` must equal `vacation.getDays()`. See [[accounting-backend]].

### Frontend

No dedicated frontend payment form validation found — payment is an accountant-only action invoked from the vacation detail/list view.

## 3. Vacation Day Correction

### Backend — UpdateVacationDaysDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| availableDays | @NotNull | BigDecimal | YES | No range limit in DTO |
| comment | @NotNull, @Size(min=1, max=255) | String | YES | 1-255 characters |

### Frontend — CorrectVacationDaysModalContainer

| Field | Rule | Detail |
|-------|------|--------|
| comment | Required | Manual state check: `comment !== ''` → `commentIsValid` |
| availableDays | Display only | Shows current + new value, no frontend validation on the number |

**Pattern:** No Yup/Formik — manual React state validation. Only comment is validated client-side; the numeric value is accepted as-is.

## 4. Budget Notification

### Backend — BudgetNotificationAddRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| startDate | @NotNull | LocalDate | YES | — |
| endDate | @NotNull | LocalDate | YES | — |
| employeeLogin | @EmployeeLoginExists | String | NO | Must exist if provided |
| projectId | @ProjectIdExists | Long | NO | Must exist if provided |
| taskId | — | Long | NO | No validation |
| limit | @Min(0) | Long | NO | >= 0 man-days |
| limitPercent | @Min(0), @Max(100) | Integer | NO | 0-100% |
| repeatMonthly | — | Boolean | NO | — |

**Class-level validators:**
- `@NotificationLimit`: At least one of `limit` or `limitPercent` must be provided
- `@NotificationPeriod`: If percent or repeatMonthly → period must be exactly one calendar month (1st to last day)

### Frontend — NotificationValidationSchema.js (Yup)

| Field | Rule | Detail |
|-------|------|--------|
| project | Required | object, nullable |
| employee | Required | object, nullable |
| startDate | Conditional | Required if limit type is "MD" |
| endDate | Conditional | Required if limit type is "MD" |
| chosenMonth | Conditional | Required if limit type is "PERCENT" |
| number (limit) | Required | Must be > 0, not NaN |
| limitType | Required | object, nullable; triggers hacky cross-field validation |

**Key difference:** Frontend splits by "limit type" (MD vs PERCENT), backend uses @NotificationLimit to check at least one present.

## 5. Statistics Search

### Backend — StatisticRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| startDate | @NotNull, @DateTimeFormat("yyyy-MM-dd") | LocalDate | YES | — |
| endDate | @NotNull, @DateTimeFormat("yyyy-MM-dd") | LocalDate | YES | — |
| employeesLogins | — | Set<@EmployeeLoginExists String> | NO | Each login validated individually |

**Minimal DTO** — date range required, optional employee filter with per-element validation.

## Key Test Case Implications

1. **Period start not validated as first-of-month in DTO** — send mid-month date, expect service-level rejection
2. **Payment days sum constraint** — regularDaysPayed + administrativeDaysPayed must equal vacation total
3. **Payment day range 0-366** — test 367, -1 boundary values
4. **Day correction no numeric limit** — test extreme BigDecimal values (negative, very large)
5. **Day correction comment 255 char limit** — test 256 chars
6. **Notification mutual exclusion** — limit vs limitPercent; both null should fail
7. **Notification period constraint** — percent mode requires exact month boundaries
8. **Statistics per-element login validation** — one invalid login in set should fail entire request

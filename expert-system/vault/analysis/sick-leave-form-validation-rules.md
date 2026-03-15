---
type: analysis
tags:
  - sick-leave
  - validation
  - phase-b-prep
  - form-rules
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[sick-leave-dayoff-business-rules-reference]]'
  - '[[sick-leave-service-implementation]]'
  - '[[frontend-sick-leave-module]]'
  - '[[sick-leave-crud-lifecycle]]'
branch: release/2.1
---
# Sick Leave Form Validation Rules

Field-level validation rules for sick leave CRUD — extracted from frontend + backend code for Phase B test case generation.

## Frontend Validation (Yup schemas)

### Create Mode (`sickLeavesOfEmployees/validationSchema.ts`)

| Field | Rule | Detail |
|-------|------|--------|
| employee | Required | `mixed().required('common.is_required')` |
| startDate | Required | `mixed().required('common.is_required')` |
| endDate | Required | `mixed().required('common.is_required')` |
| number | Max length 40 | `SickListNumberLengthValidation` — trim + max 40 chars |

### Edit Mode (same file + `SickListEdit/validation.js`)

| Field | Rule | Detail |
|-------|------|--------|
| startDate | Required | `mixed().required` |
| endDate | Required | `mixed().required` |
| number | Max length 40 | `SickListNumberLengthValidation` |
| attachments | Optional array | No constraints |

### Close/End Mode (`SickListClose/validation.js`)

| Field | Rule | Detail |
|-------|------|--------|
| number | Required | `mixed().required('common.is_required')` |
| number | Non-whitespace | `.test('only-spaces', ...)` — String(val).trim().length > 0 |
| number | Max length 40 | `SickListNumberLengthValidation` |

**Key:** Number is **optional on create/edit** but **required on close**. This is a deliberate asymmetry.

**Validation timing:** `validateOnBlur={false}`, `validateOnChange={false}` — validates on submit only.

## Backend Validation

### SickLeaveCreateRequestDTO

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| login | @NotNull (Create group), @EmployeeLoginExists | String | YES | Must exist |
| startDate | @NotNull (Create group) | LocalDate | YES | Must be <= endDate |
| endDate | @NotNull (Create group) | LocalDate | YES | Must be >= startDate |
| number | @Size(max=40) | String | NO | Max 40 chars |
| notifyAlso | @EmployeeLoginCollectionExists | Set\<String\> | NO | All logins must exist |
| filesIds | @Size(max=5), elements @FileUuidExists | Set\<UUID\> | NO | Max 5 files, each must exist |
| force | @NotNull (Create group) | Boolean | YES | Overlap force flag |

**Class-level:** `@SickLeaveCreateRequest` → `SickLeaveCreateValidator`:
- startDate must be <= endDate (or equal)
- Error key: `validation.sickLeave.dates.order`

### SickLeavePatchRequestDTO (extends Create)

Inherits all create validations. Additional optional fields with NO constraints:
- `status` (SickLeaveStatusTypeDTO enum)
- `accountingStatus` (SickLeaveAccountingStatusTypeDTO enum)
- `accountantComment` (String)

### SickLeaveSearchRequestDTO

| Field | Annotation | Constraints |
|-------|-----------|-------------|
| employeeLogin | @EmployeeLoginExists | Must exist if provided |
| datePeriod | @Valid | Cascading validation on DatePeriodDTO |
| departmentManagerLogin | @EmployeeLoginExists | Must exist if provided |
| techLeadLogin | @EmployeeLoginExists | Must exist if provided |
| sort | @Sort(names={...}) | 14 allowed sort field names |

## Key Test Case Implications

1. **Number required on close only**: Create/edit allow empty number, close requires it
2. **Whitespace-only number rejected on close**: `.trim().length > 0` check
3. **Max 5 file attachments**: Backend limit, test 5 vs 6
4. **File UUID must exist**: Upload file first, then reference
5. **Force flag for overlap**: Tests with force=true vs false when dates overlap existing sick leave
6. **No past date restriction**: Unlike vacation, sick leave has NO "start date in past" check
7. **Date order only**: startDate <= endDate is the only date constraint (no period check)
8. **Validation groups**: Create group separates create-only rules from edit/patch

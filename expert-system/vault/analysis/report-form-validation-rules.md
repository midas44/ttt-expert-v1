---
type: analysis
tags:
  - reports
  - validation
  - phase-b-prep
  - form-rules
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[reports-business-rules-reference]]'
  - '[[report-crud-api-testing]]'
  - '[[frontend-report-module]]'
  - '[[ttt-report-service]]'
branch: release/2.1
---
# Report Form Validation Rules

Field-level validation rules for task report CRUD — extracted from frontend + backend code for Phase B test case generation.

## Frontend Validation

**No Formik/Yup schema.** Uses imperative input filtering in event handlers.

### Effort Input (`WeekdayEffortContainer`)
- Strips non-numeric chars except `.,юЮБб` via regex `[^0-9.,юЮБб]+`
- Converts comma and Cyrillic chars (,юЮБб) to period for decimal
- Hours → minutes conversion via `MINUTES_IN_HOUR` constant
- Guarded by `isUpdateEffortAvailable` flag

### Task Name Parsing (`convertTaskSearchName`)
- Effort extraction: regex `^\d+[,бюБЮ.]?\d{0,2}[hрHР]` at end of name
- Max 2 decimal places
- Accepts h/r/H/R suffixes (Latin + Cyrillic hour markers)
- Executor extraction: `(?: @)([a-zA-Z.-_]+)` for @mention

## Backend Validation — Create

**DTO:** `TaskReportCreateRequestDTO`

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| taskId | @NotNull | Long | YES | — |
| reportDate | @NotNull | LocalDate | YES | Must be >= employee's report period start |
| executorLogin | @NotNull, @EmployeeLoginExists | String | YES | Must exist in system |
| effort | @NotNull, @Min(1) | Integer | YES | Min 1 minute on create (not zero) |

**Class-level:** `@ReportPeriod` — reportDate must be within employee's open report period.

## Backend Validation — Edit

**DTO:** `TaskReportEditRequestDTO`

| Field | Annotation | Type | Required | Constraints |
|-------|-----------|------|----------|-------------|
| effort | @Min(0) | Integer | NO | **Zero allowed on edit** (unlike create @Min(1)) |
| reportComment | @Size | String | NO | Optional, size-limited |
| state | — | TaskReportState enum | NO | Optional state change |
| stateComment | @Size | String | NO | Optional |

**Key difference:** Create requires effort >= 1, edit allows effort = 0.

## Backend Validation — Update

**DTO:** `TaskReportUpdateRequestDTO` extends `TaskReportEditRequestDTO`

| Field | Annotation | Constraints |
|-------|-----------|-------------|
| id | @NonNull (Lombok) | Required |
| (inherited) | effort, reportComment, state, stateComment | Same as edit |

## Backend Validation — Search

**DTO:** `TaskReportSearchRequestDTO`

| Field | Annotation | Constraints |
|-------|-----------|-------------|
| taskId | Optional | Long |
| executorLogin | @EmployeeLoginExists | Must exist if provided |
| projectId | @ProjectIdExists | Must exist if provided |
| executorsProjectId | @ProjectIdExists | Must exist if provided |
| startDate/endDate | @NotNull (if period search) | Required together |

**Class-level validators:**
- `@TaskReportSearchRequest`: At least one of taskId, executorLogin, executorsProjectId, projectId required
- `@TaskReportSearchRequestPeriod`: Date range max 62 days (2 months + 1 day)

## Backend Validation — Batch Delete

**DTO:** `TaskReportBatchDeleteRequestDTO`

Two mutually exclusive modes:
1. **By IDs:** `ids` set (non-empty)
2. **By filters:** projectId/taskId/executorsLogins + startDate + endDate

**3-method validator:**
- `validateRequiredParameters`: non-empty ids OR period filter
- `validateParametersCompatibility`: cannot mix ids with period filters
- `validatePeriodFilled`: startDate and endDate required together

## Key Test Case Implications

1. **Create vs Edit effort asymmetry**: @Min(1) on create, @Min(0) on edit — test zero effort on both
2. **Report period constraint**: reportDate must be in open period — test boundary dates
3. **Search 62-day limit**: Max 2 months + 1 day range — test 62 vs 63 day range
4. **Search requires at least one filter**: Test with no filters → should fail
5. **Batch delete mutual exclusion**: Test ids + period together → should fail
6. **Cyrillic effort input**: Frontend accepts Cyrillic б/ю as decimal separators
7. **@mention parsing**: Task name can embed executor via @login syntax
8. **No frontend effort max**: No maximum hours validation on frontend side

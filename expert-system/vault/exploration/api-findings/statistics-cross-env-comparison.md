---
type: exploration
tags:
  - statistics
  - cross-env
  - api-testing
  - comparison
  - phase-b-prep
created: '2026-03-15'
updated: '2026-03-15'
status: active
branch: release/2.1
related:
  - '[[modules/statistics-service-implementation]]'
  - '[[statistics-api-testing]]'
  - '[[external/tickets/ticket-3400-statistics-individual-norm-export]]'
  - '[[branches/cross-branch-release21-vs-stage]]'
---
# Statistics API — Cross-Environment Comparison

Timemachine (release/2.1) vs Stage (stage branch) comparison of statistics-related API endpoints. Tested 2026-03-15.

## Summary Endpoint (`/v1/reports/summary`)

**Parameters**: `login` (required) + `date` (required). Both missing → 500 with `MissingServletRequestParameterException`.

| Aspect | Timemachine | Stage |
|--------|------------|-------|
| Response shape | `{week: {...}, month: {...}}` | Identical |
| Week fields | reported, personalNorm, norm, personalNormForDate, normForDate | Identical |
| Month fields | Same as week | Identical |
| Error handling | 500 on missing params | Identical |

**Conclusion**: Summary endpoint — **identical behavior and structure**.

## Statistic Report Employees (`/v1/statistic/report/employees`)

**Parameters**: `startDate`, `endDate` (required), `pageSize` (optional). Returns JSON array (not paginated object).

### Field Set Differences (SIGNIFICANT)

| Field | Timemachine | Stage |
|-------|------------|-------|
| **id** | ❌ absent | ✅ present (employee DB ID) |
| **normForDate** | ❌ absent | ✅ present (norm for date range) |
| budgetNorm | ✅ | ✅ |
| excess | ✅ | ✅ |
| expandable | ✅ | ✅ |
| login | ✅ | ✅ |
| managerLogin | ✅ | ✅ |
| managerName | ✅ | ✅ |
| managerRussianName | ✅ | ✅ |
| name | ✅ | ✅ |
| nodeType | ✅ | ✅ |
| nodeUuid | ✅ | ✅ |
| norm | ✅ | ✅ |
| reported | ✅ | ✅ |
| reportedNotificationStatus | ✅ | ✅ |
| reportedStatus | ✅ | ✅ |
| russianName | ✅ | ✅ |

**TM: 15 fields, Stage: 17 fields** — stage has `id` and `normForDate` extra.

### Behavioral Differences

| Aspect | Timemachine | Stage |
|--------|------------|-------|
| Decimal precision | 3 places (223.250) | 2 places (223.25) |
| Russian name format (manager) | "Ильницкий Иван" (Last First) | "Иван Ильницкий" (First Last) |
| Data values | Same employee data | Same employee data |
| Sorting | Same default order | Same default order |

### Interpretation

The field differences suggest **release/2.1 removed `id` and `normForDate`** from the statistics employee report response. This may relate to:
- Refactoring of the statistic report DTO
- #3400 individual norm feature preparation (restructuring norm fields)
- The name format change (Last-First vs First-Last) may be a separate fix or regression

## Over-Reported Employees (`/v1/reports/employees-over-reported`)

**Parameters**: `date` (required). Returns `{total, data: [...]}`.

| Aspect | Timemachine | Stage |
|--------|------------|-------|
| Total (Feb 2026) | 91 | 91 |
| Response structure | `{total, data: [{employeeId, names, month, year, norm, reported}]}` | Identical |
| Data content | Same employees | Same employees (minor ordering diff) |

**Conclusion**: Over-reported endpoint — **identical structure, same data**.

## Export Endpoint (`/v1/statistic/report/employees/export`)

| Aspect | Timemachine | Stage |
|--------|------------|-------|
| HTTP status | 404 | 404 |

**Conclusion**: #3400 individual norm CSV export — **not deployed on either environment**.

## Total Endpoint (`/v1/reports/total`)

Both require `type` parameter (TaskReportTotalType enum). Same 400 error structure.

## Phase B Implications

- Statistics test cases must document the **field set differences** between environments
- Test data generation should account for decimal precision variations
- Russian name formatting direction should be documented as environment-specific behavior
- Export feature tests should be marked as "pending implementation"

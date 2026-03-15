---
type: exploration
tags:
  - statistics
  - api-testing
  - timemachine
  - qa1
  - bugs
  - units
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/statistics-service-implementation]]'
  - '[[external/requirements/REQ-statistics-employee-reports]]'
branch: release/2.1
---

# Statistics API Testing Results

Tested on timemachine + qa1 (cross-environment comparison). Session 11.

## Endpoints Tested (10)

### /v1/reports/summary (GET)
- Params: `login` (required), `date` (required, YYYY-MM-DD)
- Returns: `week` + `month` objects with `reported`, `personalNorm`, `norm`, `personalNormForDate`, `normForDate`
- **Units: HOURS**
- `normForDate`/`personalNormForDate` = 0 for closed months, incremental for current
- Missing params → 500 (bug: should be 400)

### /v1/reports/total (GET)
- Params: `type` (EMPLOYEE|PROJECT, required), `startDate`, `endDate`, `periodType` (DAY/WEEK/MONTH)
- Returns: `{items: [{periodStartDate, employee/project, statuses, effort}]}`
- **Units: MINUTES** (300/day = 5 hours)
- Statuses: NOTHING_APPROVE, APPROVED, WAITING_APPROVAL, REPORTED

### /v1/reports/effort (GET)
- Params: `taskId` (required), `executorLogin` (optional)
- **Units: MINUTES** — cumulative all-time

### /v1/reports/employees-over-reported (GET)
- Params: `date` (required), `isPersonalNorm` (boolean, default=true)
- **Units: HOURS**
- isPersonalNorm=true: 91 employees; =false: 77 (14 fewer, those with personalNorm < office norm)

### /v1/statistic/{employees|projects|tasks|departments} (GET)
- 18 optional filter params including employeeLogin, projectId, officeId, etc.
- Returns tree-structured data (expandable nodes)
- **Units: MINUTES** (effortForPeriod=9120 = 152 hours)

### /v1/statistic/permissions (GET)
- Returns array of permission strings
- API key auth → all 5 permissions

### /v1/statistic/export/employees-largest-customers (GET)
- Returns CSV, **units: HOURS** by default (configurable via timeUnit param)

## Critical Finding: Mixed Unit Discrepancy

| Endpoint Family | Unit |
|----------------|------|
| `/v1/reports/summary` | HOURS |
| `/v1/reports/total` | MINUTES |
| `/v1/reports/effort` | MINUTES |
| `/v1/reports/employees-over-reported` | HOURS |
| `/v1/statistic/*` tree endpoints | MINUTES |
| `/v1/statistic/export/*` | HOURS |
| DB `statistic_report` | HOURS |
| DB `task_report.actual_efforts` | MINUTES |

Conversion verified: 152 hours = 9120 minutes = SUM(task_report.actual_efforts).

## month_norm vs budget_norm Clarified
- **month_norm** = personal norm (adjusted for individual schedule, part-time, absences)
- **budget_norm** = standard office norm
- 97.3% match; 2.7% differ (e.g. part-time: month_norm=64, budget_norm=152)

## Cache Pattern
- **Timemachine**: `statistic_report` table exists (9662 rows), batch sync nightly, per-employee updates on report submission
- **QA1**: NO `statistic_report` table — computes on-the-fly from task_report
- Both environments return identical data → cache is performance optimization only

## Error Handling Bugs
- Missing required params on `/v1/reports/summary` and `/v1/reports/effort` → **500** (should be 400)
- Missing params on `/v1/reports/total` → proper 400

## Related
- [[modules/statistics-service-implementation]] — backend
- [[external/requirements/REQ-statistics-employee-reports]] — requirements
- [[external/requirements/google-docs-inventory]] — statistics spec

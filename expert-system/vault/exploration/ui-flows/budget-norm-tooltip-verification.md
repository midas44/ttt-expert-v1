---
type: exploration
tags:
  - ui-flow
  - tooltip
  - budget
  - norm
  - verification
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[frontend-report-module]]'
  - '[[statistics-service-implementation]]'
branch: release/2.1
---
# Budget/Norm Tooltip Format Verification

Verified the budget/norm tooltip on My Tasks page (`/report`) and Employee Reports page.

## My Tasks Page — "Worked in [Month]" Tooltip

The info icon next to the header shows a tooltip with **conditionally 3 or 4 numbers**:

### 3-Number Format (no absences affecting norm)
`reported / personalNormForDate / norm`
Example: `32.1/72/168` — employee with no vacations/sick leave this month.

### 4-Number Format (absences reduce personal norm)
`reported / personalNormForDate / personalNorm / norm`
Example: `24/40/96/168` — employee with vacation Mar 9-13.

| # | Value | Meaning |
|---|-------|---------|
| 1 | reported | Total hours reported for current month |
| 2 | personalNormForDate | Adjusted norm up to today, minus vacation/sick leave |
| 3 | personalNorm | Adjusted norm for full month (only shown when ≠ norm) |
| 4 | norm | Calendar norm for month (working days × 8) |

### Conditional Logic
Frontend code at `modules/report/components/EffortForPeriod/index.js:49-55,134-143`: personalNorm shown only when `norm !== personalNorm`.

## Employee Reports Page — Norm Column
Separate but related: Norm column shows `norm (budgetNorm)` in brackets when budget norm differs from personal norm. Header tooltip explains the bracket number represents "how many hours can be worked beyond the personal adjusted norm without exceeding the budget."

## Verification Status
- Both 3 and 4 number formats verified working correctly
- Tooltips render consistently on hover
- Screenshots saved: `artefacts/my-tasks-3number-tooltip.png`, `artefacts/4-number-norm-tooltip.png`, `artefacts/employee-reports-norm-header-tooltip.png`
- **No bugs found** — behavior matches design intent

## Related
- [[frontend-report-module]] — report module where tooltip appears
- [[statistics-service-implementation]] — employee reports with budget norm display
- [[statistics-api-testing]] — API data behind the numbers

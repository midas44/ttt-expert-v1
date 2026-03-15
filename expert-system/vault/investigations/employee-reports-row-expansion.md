---
type: investigation
tags:
  - statistics
  - employee-reports
  - expansion
  - frontend
  - bugs
created: '2026-03-13'
updated: '2026-03-13'
status: active
branch: release/2.1
related:
  - '[[frontend-statistics-module]]'
  - '[[REQ-statistics-employee-reports]]'
  - '[[figma-vs-live-ui-comparison]]'
---
# Employee Reports Row Expansion Investigation

## Summary

Resolved the S9 "UNCLEAR" finding about row expansion in Statistics > Employee Reports. The expansion is **chevron-only**, not row click — deviating from the Confluence requirement spec.

## Click Handler: Chevron Only

In `EmployeeRow.tsx` (lines 46-55), the expand click handler is on the `IconDropDown` div with `e.stopPropagation()`. The `<tr>` in `TableAsyncBody.tsx` has NO `onClick`. However, CSS class `.clickableRow` applies `cursor: pointer` to the full row — **misleading UX**.

**Requirement (Confluence 119244531, §4.1):** "Row click (anywhere except name) → expand accordion"
**Implementation:** Only chevron icon (16x16 `IconDropDown` SVG) responds to click.
**Verdict:** Deviation from spec.

## Component Architecture

```
EmployeeReportsContainer (Redux)
  → EmployeeReportsPage (layout, filters)
    → ReportsTable (headers, TableAsync)
      → EmployeeRow (chevron + name + icons)
      → ProjectRow (name only, 50px indent)

Hooks:
  useProjectBreakdown (expansion state, API dispatch)
  useTableData (flat row assembly: employee + project rows)

Redux: sagas.ts → fetchProjectBreakdownAction → GET /v1/statistic/report/projects
```

## API

**Employee list:** `GET /v1/statistic/report/employees` — params: startDate, endDate, employee, exceedingLimit, managerLogins
**Project breakdown:** `GET /v1/statistic/report/projects` — params: employeeLogin, startDate, endDate

Backend: `StatisticReportController.java` — both require `AUTHENTICATED_USER || STATISTICS_VIEW`.

Response format: `StatisticReportNodeDTO[]` with `nodeType: "PROJECT"`, fields: nodeUuid, name, reported.

## Expansion Data Flow

1. Chevron click → `useProjectBreakdown.handleRowClick(nodeUuid, login)`
2. Toggle `expandedRows` state (local useState)
3. If not loaded, dispatch `fetchProjectBreakdownAction`
4. Saga calls API, stores in `state.employeeReports.projectBreakdown[login]`
5. `useTableData` builds flat array: employee row → [loading/nodata/project rows]

## Bugs Found

1. **Row click vs chevron mismatch** (MEDIUM) — Requirement says row click, only chevron works. cursor:pointer misleads.
2. **Stale cache on date change** (MEDIUM) — `projectBreakdown` keyed by login only, not login+dateRange. Changing month shows stale data for previously expanded employees.
3. **`projectDataLoaded` never resets** (MEDIUM) — Local useState flag prevents re-fetch after date change.
4. **Double sorting** (LOW) — Projects sorted in both API layer (`reportsApi.ts:147`) and hook (`useTableData.tsx:160`).
5. **Missing `id` in project response** — TypeScript `ProjectBreakdown` expects `id: number` but API returns no `id` for project nodes.

## Visual Behavior

- Chevron: gray SVG (#999999, 12x8), rotates 180° on expand (CSS transition 0.2s)
- Loading: spinner + "Loading..." text
- Project rows: white bg, gray text (#555, 13px), 50px left indent
- Data cached per login in Redux — re-expand after collapse does NOT re-fetch

## Related

- [[frontend-statistics-module]] — parent module
- [[REQ-statistics-employee-reports]] — Confluence requirement
- [[figma-vs-live-ui-comparison]] — previous UNCLEAR finding now resolved
- [[REQ-statistics]] — role-based access rules

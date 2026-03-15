---
type: external
tags:
  - ticket
  - statistics
  - export
  - sprint-15
  - individual-norm
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[modules/statistics-service-implementation]]'
  - '[[external/tickets/sprint-14-15-overview]]'
  - '[[exploration/api-findings/statistics-api-testing]]'
branch: release/2.1
---
# Ticket #3400 — Statistics: Individual Norm CSV Export

## Overview
New CSV export feature in Statistics module. Exports per-employee individual working-hour norms.

**Status**: Production Ready (QA passed by omaksimova 2026-03-12)
**Assignee**: omaksimova | **Author**: snavrockiy

## CSV Columns
1. `login` — employee login
2. `name` — employee first name
3. `surname` — employee last name
4. `department_manager_login` — department manager login
5. `salary_office` — employee's salary office
6. `individual_norm` — individual working-hour norm for the month

## Business Logic — Individual Norm Definition
Per QA clarification (omaksimova): **individual_norm = monthly norm accounting for**:
- Vacations (any type)
- Sick leaves
- Transferred weekends/holidays (Russian production calendar adjustments)

This is the **personalNorm** calculation from [[modules/statistics-service-implementation]], not the budgetNorm. It subtracts ALL absence types from the calendar norm.

## Implementation Notes
- No linked MRs found — implementation may be a backend-only API/export endpoint
- No Figma designs — pure data export, no UI component
- Related to existing individual norm work: #3353 (exclude pre/post employment), #3356 (part-month), #3381 (admin vacation hours)

## Test Implications
- Verify CSV format and column accuracy
- Cross-reference individual_norm with personalNorm calculation in [[modules/statistics-service-implementation]]
- Edge cases: employees with partial months, maternity leave, multiple salary offices
- Compare with Statistics page norm display

## Connections
- [[modules/statistics-service-implementation]] — norm calculation logic
- [[exploration/api-findings/statistics-api-testing]] — API test results
- [[external/tickets/sprint-14-15-overview]] — Sprint 15 context
- [[REQ-statistics-employee-reports]] — requirements


## Codebase Analysis (Session 26)

**Finding: Individual norm CSV export does NOT exist in the release/2.1 codebase.**

### Current Statistics Export Architecture
Controller: `StatisticExportController.java` — 10 endpoints under `/v1/statistic/export/`:
- departments, employees, employees/projects, employees/tasks, task-bound-employees/tasks, tasks, tasks/employees, projects, projects/employees, employees-largest-customers

### Export Node Structure (ExportEmployeeNode headers)
`EmployeeLogin, EmployeeName, Contractor, DepartmentManagerLogin, DepartmentManagerName, EffortForPeriod, EffortTotal, BeginDate, EndDate, NodeType`

**Missing from export infrastructure:**
- `salary_office` — exists in Employee entity (`salaryOfficeId`) but never queried for export
- `individual_norm` — not present anywhere in CSV export code
- `EmployeeStatisticInfoMapping` projection only fetches: id, departmentManagerLogin, departmentManagerName

### Gap Assessment
The ticket columns (login, name, surname, department_manager_login, salary_office, individual_norm) require:
1. Extend `EmployeeStatisticInfoMapping` with salary office query
2. Add new `ExportEmployeeNode` fields + headers
3. Source individual norm from personalNorm calculation or statistic_report table
4. New endpoint or extension to existing export

**Status discrepancy**: Ticket marked "Production Ready" but code not present. Possible explanations:
- Implementation exists in an unmerged branch
- One-off script/SQL export rather than API endpoint
- QA tested via different mechanism (direct DB query)

---
type: module
tags:
  - contractor
  - architecture
  - cs-sync
  - employee
  - sprint-16
  - lifecycle
created: '2026-03-16'
updated: '2026-03-16'
status: active
related:
  - '[[admin-panel-deep-dive]]'
  - '[[external/tickets/sprint-16-overview]]'
  - '[[exploration/data-findings/cross-service-office-sync-divergence]]'
branch: release/2.1
---
# Contractor Lifecycle Architecture

## Overview
Contractors share the same `employee` table as regular employees in both TTT backend and vacation service, differentiated by `is_contractor` boolean and `ROLE_CONTRACTOR` vs `ROLE_EMPLOYEE` roles. The contractor subsystem is architecturally incomplete — many features assume employee-only usage.

## Data Model

### TTT Backend Employee Entity
Key contractor-specific fields:
- **`is_contractor`** (boolean) — primary differentiator
- **`contractor_manager_id`** (Long) — FK to department manager. Separate from `senior_manager` which holds the PM for contractors
- **`being_dismissed`** (boolean) — NOT set during contractor sync (only employee sync)
- **`is_employees_manager`** — explicitly ignores contractors in its count

### Vacation Service EmployeeEntity
- **`is_contractor`** (boolean)
- **`is_working`** (boolean) — active status tracking
- **`maternity`** (boolean)
- NO `contractor_manager_id` — vacation service doesn't track contractor's dept manager
- NO `being_dismissed` — not synced for contractors

### Manager Hierarchy (Dual Path)
For contractors:
- `senior_manager` = PM (from `csContractor.getPmId()`)
- `contractor_manager_id` = department manager (from `csContractor.getManagerId()`)

For employees:
- `senior_manager` = department manager (from `employeePosition.getManagerId()`)
- `contractor_manager_id` = null

Subordinate lookup `findAllSubordinatesIds()` combines BOTH paths for department managers.

## CS Sync Architecture

### TTT Backend — Two Separate Synchronizers
`CSSyncServiceV2` orchestrates in order:
1. `CSEmployeeSynchronizer` — employees from `/employees` endpoint
2. `CSContractorSynchronizer` — contractors from `/contractors` endpoint
3. `CSSalaryOfficeSynchronizer` — offices

**CSContractorSynchronizer differences from employee sync:**
- Always sets `contractor = true`, adds `ROLE_CONTRACTOR`, removes `ROLE_EMPLOYEE`
- Sets `contractorManagerId` (not available in employee sync)
- Does NOT set: `beingDismissed`, `lastDate`, `departmentType`, `hrId`, `csManager`, `maternityStartDate/EndDate`
- Does NOT update work periods (`EmployeeWorkPeriod`)
- Does NOT assign PM/Chief/HR roles (contractors don't have CS positions)

### Vacation Service — NO Contractor Sync
**Critical gap:** The vacation service `CSSyncServiceV2` only syncs employees and salary offices — there is NO `CSContractorSynchronizer`. Contractors may exist in vacation DB but are not actively maintained via sync. Employee sync explicitly sets `contractor = false`.

### CS API Model
- **v1 API:** Unified endpoint with `isContractor` boolean flag
- **v2 API:** Separate endpoints `/employees` and `/contractors` with different response models

## CS Contractor Statuses
`NEW → PENDING → ACTIVE → BLOCKING → BLOCKED`

No intermediate "terminating" status like employees have. No `beingDismissed` equivalent.

## Business Logic Restrictions

### Contractor Exclusions
| Area | Restriction | Implementation |
|------|------------|----------------|
| Vacation active employees | Excluded | `WHERE contractor = FALSE` in EmployeeRepository queries |
| Vacation cache eviction | Skipped | `EmployeeEventListener` checks `isContractor()` |
| Project manager role | Forbidden | `PossibleProjectManagerValidator` returns false |
| Task suggestions | Restricted to own reports | `SuggestionTaskServiceImpl` limits scope |
| Ticket URL autocomplete | Restricted | `TicketUrlAutocompleteCommand` passes employee filter |
| Any-tasks autocomplete | Skipped entirely | `AnyTasksFromAnyProjectsAutocompleteCommand` |
| Work periods | Not tracked | `CSContractorSynchronizer` skips |
| Dismissal tracking | Not tracked | `beingDismissed` not set |

### Statistics Module — Contractor Support
- `StatisticFilterBO.contractor` — nullable filter for statistics
- `StatisticQdslRepoBase` applies `contractor.eq(filter)` to queries
- `DepartmentStatisticServiceImpl` creates **separate department trees** — flat for contractors, hierarchical for employees
- Department manager subordinate search limited to **depth 1** for contractors

### Office Defaults
- Contractors without office → `Office.REMOTE_ID` (10L)
- Employees without office → `Office.UNDEFINED_ID` (9L)

### Contractor Payment Offices
Known offices: Pluton, Pluton RF, Altair (B2B), Sirius (Paris)

## Frontend — Admin UI
- Separate tabs: "Employees" and "Contractors" in `EmployeesTabs.tsx`
- Both call same API endpoint `/v1/employees` with `roles: ROLE_EMPLOYEE` or `roles: ROLE_CONTRACTOR`
- Same `EmployeeDTO` type

## Known Gaps (Sprint 16 Scope)

### #2842 — Contractor Termination
No termination process exists. Only BLOCKING/BLOCKED. Missing "Calculate Salary" button for contractors. Critical for contractor→employee transition.

### #3026 — CS Office Settings Not Implemented
| Setting | Status |
|---------|--------|
| Months before first vacation (#3068) | NOT implemented — hardcoded 3 months |
| Vacation day expiration (#2472) | NOT implemented |
| Track sick leaves | NOT implemented — contractors shouldn't create sick leaves |

### Calendar Service Bypass
System does NOT query Calendar service for contractors, causing:
- Incorrect norm display for contractors with non-standard production calendars
- No awareness of payment office calendar differences

### Office Sync Divergence
`ttt_backend.employee.salary_office` can differ from `ttt_vacation.employee.office_id` after CS sync — known data integrity issue.

## Test Implications
- Contractor lifecycle (create/block/transition) → not testable until #2842 implemented
- Contractor permissions → verify existing restrictions hold
- Statistics contractor filter → verify flat hierarchy, depth-1 subordinate search
- Contractor absence prevention → verify vacation/sick-leave exclusions
- Admin UI contractor tab → verify separate display, same API pattern
- CS sync → verify contractor sync populates correct fields, employee sync doesn't touch contractors

## Connections
- [[admin-panel-deep-dive]] — admin UI architecture
- [[external/tickets/sprint-16-overview]] — Sprint 16 ticket details
- [[exploration/data-findings/cross-service-office-sync-divergence]] — office sync findings
- [[investigations/cs-office-settings-unimplemented]] — CS settings analysis

---
type: module
tags:
  - frontend
  - accounting
  - routing
  - bug
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[frontend-architecture]]'
  - '[[accounting-backend]]'
  - '[[frontend-vacation-module]]'
  - '[[frontend-app]]'
branch: release/2.1
---

# Frontend Accounting Module

## Route Architecture

The accounting module (`/accounting/*`) uses a fragmented routing strategy — menu items point to 3 different route prefixes:

| Menu Item | Actual Route | Module |
|-----------|-------------|--------|
| Salary | `/admin/salary` | Admin |
| Periods | `/admin/offices` | Admin |
| Vacation Payment | `/vacation/payment` | Vacation |
| Vacation Days Correction | `/vacation/days-correction` | Vacation |
| Sick Leave Accounting | `/accounting/sick-leaves` | Accounting |

Only Sick Leave Accounting actually lives under `/accounting/`. The rest redirect to admin or vacation modules.

## Critical Bug: Swapped Route-Component Mapping

In `src/modules/accounting/index.js` (lines 23-28), the `vacationPayout` route renders `VacationDaysCorrection` and vice versa. The components are assigned to the wrong routes. This means navigating to `/accounting/vacation-payout` shows the days correction UI, and `/accounting/vacation-days-correction` shows the payout UI.

**Impact**: Low in practice — the menu bypasses these routes entirely (uses `/vacation/payment` and `/vacation/days-correction` instead), so users likely never hit the swapped accounting routes. But the dead code with swapped mappings is a maintenance hazard.

## Component Status

All accounting-specific page components are stubs/TODOs:
- `Salary/index.js` — loading spinner placeholder
- `VacationPayout/index.js` — placeholder
- `VacationDaysCorrection/index.js` — placeholder
- `Periods/index.js` — placeholder

The real implementations live in [[frontend-vacation-module]] (`CorrectVacationDaysPage`, vacation payment components) and admin module.

## Design Issues

1. **Dead module**: Accounting routes exist but components are unimplemented stubs — all real functionality lives in other modules
2. **Route fragmentation**: One menu, three different route prefixes — confusing for maintenance
3. **Swapped components**: Even the stub components are assigned to wrong routes

Key files: `src/modules/accounting/index.js`, `src/common/constants/routes.js`, `src/common/constants/menuConfig.js`

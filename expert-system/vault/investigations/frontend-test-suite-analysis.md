---
type: investigation
tags:
  - testing
  - frontend
  - quality
  - coverage
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[backend-test-suite-analysis]]'
  - '[[architecture/frontend-structural-quality]]'
branch: release/2.1
---
# Frontend Test Suite Analysis

## Summary
28 test files covering 1,808 source files — **1.5% test-to-source ratio**. Jest + React Testing Library properly configured but critically underused. Cypress e2e installed but zero tests written.

## Framework Stack
- **Jest** (via react-scripts 5.0.1, react-app-rewired) — test runner
- **React Testing Library** (14.2.1) — component testing
- **@testing-library/jest-dom** (6.6.3) — DOM matchers
- **react-test-renderer** (18.2.0) — snapshot testing (1 usage)
- **Cypress** (13.6.6) — e2e framework (configured, 0 tests)
- **mockdate** (3.0.5) — date mocking utility

## Coverage by Module

| Module | Source Files | Test Files | Ratio |
|--------|-------------|-----------|-------|
| common | 523 | 15 | 2.9% |
| approve | 80 | 4 | 5.0% |
| planner | 207 | 4 | 1.9% |
| vacation | 374 | 2 | 0.5% |
| admin | 308 | 2 | 0.6% |
| statistics | 144 | 1 | 0.7% |
| **report** | **53** | **0** | **0%** |
| **sickLeave** | **54** | **0** | **0%** |
| **accounting** | **5** | **0** | **0%** |
| **taskRename** | **32** | **0** | **0%** |
| **budgetNotifications** | **27** | **0** | **0%** |
| **faq** | **1** | **0** | **0%** |

## Test Types
- **Unit tests** (25 files, 89%): utility functions, services, helpers
- **Component tests** (6 files, 21%): render + fireEvent + assertion
- **Snapshot tests** (1 file): pageLoading component only
- **E2E tests**: 0 (Cypress scaffold exists but empty)

## What's Actually Tested
- Common services: date formatting, effort calculation, data transformations
- Input filter hooks (3 tests)
- Approve module: selectors, helper functions
- Planner: service-layer utility functions
- Vacation: chart component, service function
- Admin: firing helper, service function

## Critical Gaps
1. **6 modules with zero tests**: report, sickLeave, accounting, taskRename, budgetNotifications, faq
2. **No Redux store/slice tests** — 14+ slices in vacation module alone
3. **No API integration tests** — no MSW or mock server
4. **No component tests** for major UI: vacation forms, report tables, planner grid
5. **No e2e tests** despite Cypress being installed
6. **No test utilities** — no render wrappers for Redux/Context providers
7. **No testing documentation** or guidelines

## Configuration
- Module aliases configured in Jest (`@vacation/`, `@report/`, etc.)
- `setupTests.js` — minimal (imports jest-dom only)
- Test naming: `.test.js/.test.ts/.test.tsx` (no `.spec` variants)
- Directory patterns: `__test__/` and `_test_/` (inconsistent)

## Assessment
The frontend test suite is **functionally absent** for business-critical modules. The 28 existing tests cover only utility functions and simple helpers — no business logic, no user flows, no state management. This represents the **largest quality gap** in the entire project.

Related: [[backend-test-suite-analysis]], [[architecture/frontend-structural-quality]], [[frontend-vacation-module]], [[frontend-approve-module]]

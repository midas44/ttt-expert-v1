---
type: architecture
tags:
  - frontend
  - react
  - redux
  - routing
created: '2026-03-12'
updated: '2026-03-13'
status: active
related:
  - '[[system-overview]]'
  - '[[frontend-app]]'
branch: release/2.1
---
# Frontend Architecture

React 18 + Redux SPA with 11 feature modules, ~500+ source files, lazy-loaded routing.

## Feature Modules

| Module | Components | Redux Slices | Complexity |
|--------|-----------|-------------|------------|
| vacation | 87 | 12 | XL — most complex |
| admin | 27 | 2 | Large |
| planner | 15 | 12 | Large (complex state) |
| report | 14 | 1 | Medium |
| sickLeave | 12 | 1 | Medium |
| statistics | 12 | 5 | Medium |
| approve | 4 | modular | Small |
| accounting | 0 | 1 | Data layer only |
| budgetNotifications | 0 | 1 | Data layer only |
| taskRename | 0 | 1 | Data layer only |
| faq | 0 | 0 | Minimal/static |

## State Management
~40 Redux slices using ducks pattern (actions, reducer, selectors, sagas, api). Redux Saga for async. @tanstack/react-query for data fetching/caching.

## Common Infrastructure
- 38 shared component directories (forms, display, layout, utility)
- 14 API service files (Axios + React Query)
- RC component library (table, select, tabs, dialog, checkbox)
- i18next: 345 keys across 24 files (EN/RU)
- Permission-gated routes via PrivateRoute

## Routes
/accounting, /planner, /admin, /approve, /notifications, /faq, /report/:employeeLogin, /statistics/general, /statistics/employee-reports, /vacation/*, /sick-leave, /logout

## Key Observations
- Vacation module is massive (87 components, 12 Redux slices) — matches business complexity
- Mixed JS/TS codebase — gradual TypeScript migration
- Code splitting via React.lazy() per module
- Heavy use of Formik+Yup for form validation

## Related
- [[system-overview]]
- [[frontend-app]]
- [[frontend-state-management]]

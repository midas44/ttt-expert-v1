---
type: module
tags:
  - frontend
  - react
  - typescript
created: '2026-03-12'
updated: '2026-03-13'
status: active
related:
  - '[[system-overview]]'
branch: release/2.1
---
# Frontend Application

React SPA with 12 feature modules, served via Spring Boot wrapper.

## Structure
- `frontend-js/` — Main React/TypeScript application
- `frontend-app/` — Spring Boot server wrapper

## Feature Modules (12)
1. `accounting/` — Accounting/billing management
2. `admin/` — Admin panel (roles, users, firing)
3. `approve/` — Approval workflows
4. `budgetNotifications/` — Budget alerts
5. `faq/` — FAQ management
6. `planner/` — Project planning
7. `report/` — Time report generation
8. `sickLeave/` — Sick leave management
9. `statistics/` — Analytics/stats dashboard
10. `taskRename/` — Task renaming
11. `vacation/` — Vacation requests

## Common Infrastructure
- `api/` — API client layer
- `services/` — Business logic utilities
- `components/` — Shared UI components
- `ducks/` — Redux slices (Redux Toolkit)
- `styles/` — CSS/SCSS
- `assets/` — Static files
- `containers/` — Container components
- `localisation/` — i18n (i18next, RU/EN)

## Tech Stack
- React 18.2, Redux Toolkit 2.4, Redux Saga
- @tanstack/react-query 5.60 for data fetching
- Formik + Yup for forms
- i18next for internationalization (RU/EN)
- STOMP/SockJS for WebSocket
- rc-* component library (table, select, tabs, dialog)
- Moment.js for dates

## Scale
1,270 JS/JSX + 670 TS/TSX files. ~28 test files.

## Related
- [[system-overview]]
- [[frontend-architecture]]
- [[frontend-state-management]]

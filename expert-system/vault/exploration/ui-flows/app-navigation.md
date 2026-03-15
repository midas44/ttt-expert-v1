---
type: exploration
tags:
  - ui
  - navigation
  - playwright
  - timemachine
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[frontend-architecture]]'
  - '[[vacation-pages]]'
  - '[[roles-permissions]]'
---
# Application Navigation Structure

Explored on timemachine (build 2.1.26-SNAPSHOT.290209, 2026-03-11). Login: dergachev (manager with admin access).

## Login Page (`/`)

- Username-only auth (no password). Field: `#username`, submit: `button[type="submit"]`
- POST to `/api/ttt/authorization/jwt/new?login=<username>`
- Returns JWT on success, 400 with `EmployeeLoginExistsValidator` if unknown login
- Note: `v.burykin` does not exist on timemachine

## Header Navigation (7 items)

| Nav Item | Type | URL | Subitems |
|---|---|---|---|
| My tasks | Link | `/report` | — |
| Calendar of absences | Dropdown | — | 6 items (see below) |
| Confirmation | Link | `/approve` | — |
| Planner | Link | `/planner` | — |
| Statistics | Dropdown | — | 2 items |
| Admin panel | Dropdown | — | 2 items |
| Notifications | Link | `/notifications` | — |

**Header right side:** Language switcher (EN/RU), User avatar+name (→ `/admin/account`), Logout button.

### Calendar of Absences Subitems
1. My vacations and days off → `/vacation/my`
2. My sick leaves → `/sick-leave/my`
3. Availability chart → `/vacation/chart`
4. Employees requests → `/vacation/request`
5. Employees vacation days → `/vacation/vacation-days`
6. Sick leaves of employees → `/vacation/sick-leaves-of-employees`

### Statistics Subitems
1. General statistics → `/statistics/general`
2. Employee reports → `/statistics/employee-reports`

### Admin Panel Subitems
1. Projects → `/admin/projects`
2. Employees and subcontractors → `/admin/employees`

## Persistent UI Elements
- **Notification banners** (up to 3 simultaneous): overdue day-off rescheduling, over-reported hours, non-working days reminder
- **NoveoAI widget**: floating chatbot icon (bottom-right corner, every page)
- **Footer**: copyright + build info + "Report an error" link to GitLab
- **CS profile links**: employee names throughout link to `cs.noveogroup.com/profile/<login>`
- **Confluence links**: "Vacation regulation", "Weekend regulation"

## Date Format
DD.MM.YYYY throughout the application.

## Console Issues (non-critical)
- Manifest.json syntax error
- Failed feedback script from cs-preprod.noveogroup.com
- CORS errors for cas-demo.noveogroup.com

See also: [[frontend-architecture]], [[vacation-pages]], [[roles-permissions]]

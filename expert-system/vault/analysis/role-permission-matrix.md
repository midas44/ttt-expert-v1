---
type: analysis
tags:
  - roles
  - permissions
  - access-control
  - security
  - matrix
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[architecture/roles-permissions]]'
  - '[[architecture/security-patterns]]'
branch: release/2.1
---
# Role-Permission Access Matrix

Comprehensive mapping of global roles → permission classes → UI pages → API endpoints. Built from backend PermissionProvider classes, frontend PrivateRoute guards, and @PreAuthorize annotations.

## Permission Class → Role Mapping

Each row = permission class. Checkmark = role has that permission.

### VIEW Permissions

| Permission Class | EMP | CON | PM | DM | TL | ACC | CACC | DIR | HR | ADM | VALL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ACCOUNTING:VIEW | | | | | | ✓ | ✓ | | | ✓ | ✓ |
| ACCOUNTING:NOTIFY | | | | | | ✓* | ✓* | | | ✓* | |
| BUDGET_NOTIF:VIEW | | | | ✓ | | | | ✓ | | ✓ | ✓ |
| CALENDARS:VIEW | | | | | | | ✓ | | | ✓ | ✓ |
| EMPLOYEES:VIEW | | | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| OFFICES:VIEW | | | | | | ✓ | ✓ | | | ✓ | ✓ |
| PROJECTS:VIEW | | | ✓ | ✓ | | | | | | ✓ | ✓ |
| SETTINGS:VIEW | | | | | | | | | | ✓ | ✓ |
| STATISTICS:EXPORT | | | | | | | | | | ✓ | |
| SUGGESTIONS:VIEW_CUST | | | ✓ | ✓ | | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| TASKS:VIEW_APPROVES | | | ✓ | ✓ | | ✓ | ✓ | | | ✓ | ✓ |
| TOKENS:VIEW | | | | | | | | | | ✓ | ✓ |
| VACATIONS:VIEW | ✓ | | | | | | | | | | |
| VACATIONS:VIEW_APPROVES | | | ✓ | ✓ | ✓ | | | | | ✓ | ✓ |
| VACATIONS:VIEW_PAYMENTS | | | | | | ✓ | ✓ | | | ✓ | ✓ |
| VACATIONS:VIEW_DAYS | | | | | | ✓ | ✓ | | | ✓ | ✓ |
| VACATIONS:VIEW_EMPLOYEES | | | | ✓ | | | | | | | |
| VACATIONS:SICK_LEAVE_VIEW | | | | | | ✓ | ✓ | | | ✓ | ✓ |

*\* = respects readOnly flag*

Legend: EMP=Employee, CON=Contractor, PM=ProjectManager, DM=DepartmentManager, TL=TechLead, ACC=Accountant, CACC=ChiefAccountant, DIR=OfficeDirector, HR=OfficeHR, ADM=Admin, VALL=ViewAll

### WRITE Permissions (CREATE/EDIT — blocked by readOnly flag)

| Permission | Roles |
|---|---|
| PROJECTS:CREATE | PM, DM, ADM |
| SETTINGS:CREATE | ADM |
| TOKENS:CREATE | ADM |
| TASKS:CREATE | All except readOnly |
| VACATIONS:CREATE | EMP (non-readOnly) |
| BUDGET_NOTIF:CREATE | PM, DM, DIR, ADM |

## Frontend Page Access Matrix

| Page | Path | Required Permission | Accessible Roles |
|---|---|---|---|
| My Tasks | `/` | None (default) | All |
| Planner | `/planner` | None | All |
| FAQ | `/faq` | None | All |
| Statistics | `/statistics` | None | All |
| Approve (Confirmation) | `/approve` | TASKS:VIEW_APPROVES | PM, DM, ACC, CACC, ADM, VALL |
| Budget Notifications | `/budget-notifications` | BUDGET_NOTIF:VIEW | PM, DM, DIR, ADM, VALL |
| Employee Reports | `/employee-reports/:login` | EMPLOYEES:VIEW (+ self-access) | PM, DM, TL, ACC, CACC, DIR, HR, ADM, VALL + self |
| **Vacation subroutes:** | | | |
| My Vacations | `/vacation/my` | VACATIONS:VIEW | EMP (all logged-in) |
| Vacation Requests | `/vacation/request` | VACATIONS:VIEW_APPROVES | PM, DM, TL, ADM, VALL |
| Vacation Chart | `/vacation/chart` | VACATIONS:VIEW | EMP (all logged-in) |
| Payment | `/vacation/payment` | VACATIONS:VIEW_PAYMENTS | ACC, CACC, ADM, VALL |
| Days Correction | `/vacation/days-correction` | VACATIONS:VIEW_DAYS | ACC, CACC, ADM, VALL |
| Vacation Days | `/vacation/vacation-days` | VACATIONS:VIEW_EMPLOYEES | DM |
| Sick Leaves (employees) | `/vacation/sick-leaves-of-employees` | VACATIONS:SICK_LEAVE_VIEW | ACC, CACC, ADM, VALL |
| **Admin subroutes:** | | | |
| Projects | `/admin/projects` | PROJECTS:VIEW | PM, DM, ADM, VALL |
| Employees | `/admin/employees` | EMPLOYEES:VIEW | PM, DM, TL, ACC, CACC, DIR, HR, ADM, VALL |
| Settings | `/admin/settings` | SETTINGS:VIEW | ADM, VALL |
| Calendar | `/admin/calendar` | CALENDARS:VIEW | CACC, ADM, VALL |
| API (Tokens) | `/admin/api` | TOKENS:VIEW | ADM, VALL |
| Export | `/admin/export` | STATISTICS:EXPORT | ADM |
| Salary | `/admin/salary` | ACCOUNTING:NOTIFY | ACC, CACC, ADM |
| Offices | `/admin/offices` | OFFICES:VIEW | ACC, CACC, ADM, VALL |
| Account | `/admin/account` | None | All |
| **Accounting subroutes:** | | | |
| Salary | `/accounting/salary` | None (!) | All (security gap) |
| Vacation Payout | `/accounting/vacation-payout` | None (!) | All (security gap) |
| Days Correction | `/accounting/days-correction` | None (!) | All (security gap) |
| Periods | `/accounting/periods` | None (!) | All (security gap) |
| Sick Leaves | `/accounting/sick-leaves` | VACATIONS:SICK_LEAVE_ACCOUNTING_VIEW | ACC, CACC, ADM, VALL |
| **Sick Leave:** | | | |
| Sick Leave | `/sick-leave` | None (TODO in code) | All (planned gap) |

## Security Gaps Identified

1. **Accounting pages unprotected** — 4 of 5 accounting subroutes lack frontend permission checks. Backend API has auth but UI is open.
2. **Sick leave route TODO** — Frontend code has explicit Russian comment: "Add permission check. Component created for future sprints."
3. **Contractor permissions unclear** — ROLE_CONTRACTOR gets no explicit permissions in any provider. Likely gets basic personal access only.
4. **Sick leave API: AUTHENTICATED_USER only** — CRUD operations block API tokens entirely (no fallback permission).
5. **Calendar service: role + authority AND** — Uses compound `hasAnyRole AND hasAnyAuthority` — stricter than other services.

## Backend @PreAuthorize Patterns

Three auth patterns across services:
- **Pattern A** (Both): `hasAuthority('AUTHENTICATED_USER') || hasAuthority('SPECIFIC')` — correct, most endpoints
- **Pattern B** (JWT only): `hasAuthority('AUTHENTICATED_USER')` — sick leave CRUD, settings, some admin
- **Pattern C** (Compound): `hasAnyRole(...) AND hasAnyAuthority(...)` — calendar service only

## Related
- [[architecture/roles-permissions]] — role definitions and counts
- [[architecture/security-patterns]] — auth mechanisms (JWT, API token, CAS)
- [[exploration/api-findings/sick-leave-api-testing]] — AUTHENTICATED_USER gap
- [[exploration/api-findings/accounting-api-testing]] — 403 on accounting endpoint


## Session 24 Updates

### New: Object-Level Permission Pattern (Sprint 15)

Ticket #2724 introduces `PlannerCloseTagPermissionService` — the first object-level permission implementation for planner features. Grants CREATE/EDIT/DELETE to admin, project manager, senior manager, and project owner. All-or-nothing (no partial grants). See [[modules/planner-close-tag-permissions]].

### New: Auth/Authorization Developer Documentation

`docs/auth-and-authorization.md` (687 lines) committed — first-party reference confirming dual auth (JWT + API token), `@PreAuthorize` patterns, and `AUTHENTICATED_USER` convention. See [[architecture/auth-authorization-doc]].

This confirms Pattern A/B/C categorization above and adds detail on:
- JWT `authorities` claim loading from `employee_global_roles`
- API token `ASSIGNMENTS_ALL` / `CALENDAR_VIEW` / `EMPLOYEES_VIEW` permissions from `token_permissions` table
- `EmployeeActivationResolver` as the employee resolution mechanism

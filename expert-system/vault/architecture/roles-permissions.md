---
type: architecture
tags:
  - roles
  - permissions
  - security
  - authorization
created: '2026-03-12'
updated: '2026-03-13'
status: active
related:
  - '[[system-overview]]'
  - '[[database-schema]]'
  - '[[architecture/security-patterns]]'
  - '[[patterns/error-handling-agreement]]'
  - '[[external/requirements/google-docs-inventory]]'
branch: release/2.1
---

# Roles and Permissions

## Global Roles (employee_global_roles)
System-wide access control roles. An employee can have multiple roles.

| Role | Count | Description |
|------|-------|-------------|
| ROLE_EMPLOYEE | 1,683 | Base role for all employees |
| ROLE_CONTRACTOR | 159 | External contractors — likely limited access |
| ROLE_PROJECT_MANAGER | 136 | PM — manages project members, approves reports |
| ROLE_OFFICE_HR | 50 | HR for salary offices |
| ROLE_DEPARTMENT_MANAGER | 29 | Department-level management |
| ROLE_TECH_LEAD | 19 | Technical leadership role |
| ROLE_ACCOUNTANT | 18 | Accounting operations (payments, periods) |
| ROLE_VIEW_ALL | 13 | Read-only access to all data |
| ROLE_ADMIN | 8 | System administration |
| ROLE_CHIEF_ACCOUNTANT | 2 | Elevated accounting (chief accountant) |
| ROLE_CHIEF_OFFICER | 1 | Top-level executive access |

**Note**: Mission Directive mentioned 6 roles (employee, contractor, manager, department manager, accountant, admin). Actual system has 11 — adds OFFICE_HR, TECH_LEAD, VIEW_ALL, CHIEF_ACCOUNTANT, CHIEF_OFFICER.

## Google Sheets Roles Spec (14 roles)
The official Google Sheets specification lists **14 roles** — 3 more than found in DB:

| Spec Role | DB Equivalent | Notes |
|-----------|---------------|-------|
| EMPLOYEE | ROLE_EMPLOYEE | Baseline |
| CONTRACTOR | ROLE_CONTRACTOR | |
| PROJECT_MANAGER | ROLE_PROJECT_MANAGER | |
| **PROJECT_SENIOR_MANAGER** | — | Inherits PROJECT_MANAGER. Not in DB as separate role |
| **PROJECT_OBSERVER** | — | Not in DB as separate global role |
| **PROJECT_OWNER** | — | Not in DB as separate global role |
| DEPARTMENT_MANAGER | ROLE_DEPARTMENT_MANAGER | |
| OFFICE_HR | ROLE_OFFICE_HR | |
| OFFICE_ACCOUNTANT | ROLE_ACCOUNTANT | Name differs |
| CHIEF_ACCOUNTANT | ROLE_CHIEF_ACCOUNTANT | |
| OFFICE_DIRECTOR | ROLE_CHIEF_OFFICER | Name differs |
| VIEW_ALL | ROLE_VIEW_ALL | |
| ADMIN | ROLE_ADMIN | |

**Discrepancy analysis**: PROJECT_SENIOR_MANAGER, PROJECT_OBSERVER, and PROJECT_OWNER appear to be **project-scoped roles** (not global_roles). They may be resolved via project_member table or ApiPermission enum rather than employee_global_roles. TECH_LEAD exists in DB but not in spec — may be a newer or internal-only role.

### Permission Model (from spec)
- **Scope levels**: personal → project → department → office → system-wide
- **Action levels**: VIEW, EDIT, APPROVE, DELETE
- Budget & Notifications: scoped by role (personal→project→office)
- Employees visibility: scoped (self→department→office→all)
- Projects: members→managers→owners→admins
- Task assignments & reports: personal→project→department→office
- Vacations: personal→team→department→office
- Settings & tokens: directors and admins only

## Project Roles (project_member.role)
Free-text field describing person's role on a project (e.g., "QA", "PM", "Developer", "iOS developer"). Not standardized — over 100 unique values, mixed languages (RU/EN), inconsistent naming (e.g., "developer" vs "Developer" vs "Разработчик").

**access_type** field on project_member is always NULL — likely unused/deprecated.

## Related
- [[system-overview]]
- [[database-schema]]
- [[ttt-service]]
- [[architecture/security-patterns]] — auth mechanisms
- [[patterns/error-handling-agreement]] — error response by role
- [[external/requirements/google-docs-inventory]] — source specification

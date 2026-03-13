---
type: architecture
tags:
  - roles
  - permissions
  - security
  - authorization
created: '2026-03-12'
updated: '2026-03-12'
status: draft
related:
  - '[[system-overview]]'
  - '[[database-schema]]'
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

## Project Roles (project_member.role)
Free-text field describing person's role on a project (e.g., "QA", "PM", "Developer", "iOS developer"). Not standardized — over 100 unique values, mixed languages (RU/EN), inconsistent naming (e.g., "developer" vs "Developer" vs "Разработчик").

**access_type** field on project_member is always NULL — likely unused/deprecated.

## Role-Feature Matrix (inferred, needs verification)
- **Employees/Contractors**: Submit reports, create absence requests
- **Project Managers**: Approve reports, manage project members
- **Department Managers**: Broader approval scope, department view
- **Tech Leads**: Similar to PM with technical oversight
- **Accountants**: Period management, payment processing
- **HR**: Employee management, salary office configuration
- **Admin**: Full system access, settings management

## Related
- [[system-overview]]
- [[database-schema]]
- [[ttt-service]]

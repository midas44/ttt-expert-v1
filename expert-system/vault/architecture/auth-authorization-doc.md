---
type: architecture
tags:
  - auth
  - security
  - jwt
  - api-token
  - spring-security
  - sprint-15
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[analysis/role-permission-matrix]]'
  - '[[modules/planner-close-tag-permissions]]'
branch: release/2.1
---
# Auth & Authorization Documentation (Developer Doc)

Sprint 15 addition — `docs/auth-and-authorization.md` (687 lines, Russian) added to repo. Comprehensive developer reference for TTT's dual authentication and authorization system.

## Key Findings from the Document

### Dual Authentication Mechanisms

1. **JWT Token (`TTT_JWT_TOKEN` header)**
   - Represents a real employee from `employee` table
   - Contains: profile data (login, officeId, managerId) + `authorities` claim with global roles
   - Generated via `POST /v1/security/jwt`, RSA-signed, 1-day validity
   - Always grants `AUTHENTICATED_USER` authority on success

2. **API Token (`API_SECRET_TOKEN` header)**
   - Technical secret key, UUID-based, stored in `token` table
   - Permissions in `token_permissions` table (e.g. `CALENDAR_VIEW`, `EMPLOYEES_VIEW`, `ASSIGNMENTS_ALL`)
   - Generated via `POST /v1/tokens`
   - **Does NOT grant `AUTHENTICATED_USER`** — only carries explicit `ApiPermission` values

### @PreAuthorize Unification Pattern

- `hasAuthority('AUTHENTICATED_USER')` — JWT-only endpoints
- `hasAnyAuthority('AUTHENTICATED_USER', 'CALENDAR_VIEW')` — JWT users pass via AUTHENTICATED_USER; API tokens pass only with specific permission
- This is the **single mechanism** bridging both auth paths

### Role Source

- Table: `employee_global_roles` (FK to `employee`)
- Entity: `EmployeeRole` with enum `EmployeeGlobalRole`
- Roles: `ROLE_ADMIN`, `ROLE_PROJECT_MANAGER`, `ROLE_EMPLOYEE`, `ROLE_CHIEF_ACCOUNTANT`, etc.
- Loaded into JWT `authorities` claim

### Spring Security Chain

- `JwtTokenAuthenticationFilter` → `JwtTokenAuthenticationProvider` → resolves employee via `EmployeeActivationResolver` → constructs `JwtAuthenticationToken`
- Parallel filter/provider chain for API tokens

### Token Management Endpoints

`GET/POST/PATCH/DELETE /v1/tokens` — all require `hasAuthority('AUTHENTICATED_USER')` (JWT-only). Tokens are `APPLICATION` type with UUID `secret_key`.

## Validation Against Our Knowledge

This doc **confirms and enriches** our [[analysis/role-permission-matrix]]:
- The dual auth model explains why some endpoints use `hasAnyAuthority` with both `AUTHENTICATED_USER` and specific API permissions
- The `AUTHENTICATED_USER` convention is the key distinction between JWT and API token access
- Role loading from `employee_global_roles` matches our DB schema findings in [[ttt-backend-schema-deep-dive]]

## Significance for Phase B

This document is a **first-party authoritative reference** for security testing. Test cases should verify:
- JWT vs API token access boundaries
- `AUTHENTICATED_USER` authority gating
- API token permission granularity
- Token CRUD lifecycle
- Cross-cutting with object-level permissions (like [[modules/planner-close-tag-permissions]])

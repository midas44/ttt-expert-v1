---
type: exploration
tags:
  - api-testing
  - sick-leave
  - permission-bug
  - security
created: '2026-03-12'
updated: '2026-03-12'
status: active
branch: release/2.1
related:
  - '[[modules/sick-leave-service-implementation]]'
  - '[[architecture/api-surface]]'
---
# Sick Leave API Testing

## Environment
Timemachine + QA-1, user: pvaynmaster. API token with 21 permissions.

## Permission Inconsistency (Critical Finding)

Sick leave endpoints use `AUTHENTICATED_USER` authority only (no API token permission alternative), unlike vacation endpoints which accept `AUTHENTICATED_USER` OR specific permissions (VACATIONS_CREATE, etc.).

| Endpoint | Required Permission | API Token | Result |
|----------|-------------------|-----------|--------|
| Search (GET /v1/sick-leaves) | AUTHENTICATED_USER OR VACATIONS_VIEW | ✓ Has VACATIONS_VIEW | **200 OK** |
| Count (GET /v1/sick-leaves/count) | AUTHENTICATED_USER OR VACATIONS_VIEW | ✓ Has VACATIONS_VIEW | **200 OK** |
| Get by ID (GET /v1/sick-leaves/{id}) | AUTHENTICATED_USER only | ✗ | **403 Forbidden** |
| Create (POST /v1/sick-leaves) | AUTHENTICATED_USER only | ✗ | **403 Forbidden** |
| Patch (PATCH /v1/sick-leaves/{id}) | AUTHENTICATED_USER only | ✗ | **403 Forbidden** |
| Delete (DELETE /v1/sick-leaves/{id}) | AUTHENTICATED_USER only | ✗ | **403 Forbidden** |

This means sick leave CRUD is completely inaccessible via API tokens on ALL environments (qa-1 and timemachine both have identical 21-permission token sets, none include AUTHENTICATED_USER).

## What Works

- **Search**: 348 sick leaves on timemachine, pagination with page/pageSize/sort
- **Count**: Returns 348
- **Data visible in search**: status, accountingStatus, employee, dates, totalDays, workDays, number, files, office

## Create Request Structure (from code analysis)

```json
{
  "login": "string (required)",
  "startDate": "YYYY-MM-DD (required)",
  "endDate": "YYYY-MM-DD (required)",
  "force": "boolean (required, bypass vacation crossing)",
  "number": "string (optional, max 40 chars)",
  "notifyAlso": ["string"] "(optional)",
  "filesIds": ["UUID"] "(optional, max 5)"
}
```

## PATCH extends Create with:
- `status`: OPEN or CLOSED
- `accountingStatus`: NEW, PROCESSING, PAID, REJECTED
- `accountantComment`: string

## Impact
- Sick leave lifecycle cannot be tested via API automation
- Only UI-based or session-auth-based testing possible
- Inconsistent with vacation module design pattern

## Related
- [[modules/sick-leave-service-implementation]] — Backend implementation
- [[architecture/api-surface]] — API surface map
- [[exploration/api-findings/vacation-crud-api-testing]] — Vacation CRUD (working)

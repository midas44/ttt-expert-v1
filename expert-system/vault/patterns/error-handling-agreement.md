---
type: pattern
tags:
  - error-handling
  - api
  - frontend
  - backend
  - agreement
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[architecture/security-patterns]]'
  - '[[architecture/api-surface]]'
  - '[[architecture/frontend-architecture]]'
  - '[[external/requirements/google-docs-inventory]]'
---

# Error Handling Agreement (Backend ↔ Frontend)

Source: Google Doc (14c8eeBhj_SRJIGVLhj0HilhvZuSy8FtZsrfsdWS0M2M)

## Error Classification (4 types)

### 1. Validation Errors (400 Bad Request)
- Tied to specific request fields
- May span multiple fields (e.g. task name must contain ticket number)
- Examples: reporting hours on completed projects, invalid date ranges

### 2. Object Existence Errors (404 / 409)
- **404 Not Found**: object does not exist
- **409 Conflict**: attempting to create pre-existing object
- Not field-specific — different from validation errors
- 409 may be informational rather than user-facing

### 3. Access Control Errors (401 / 403)
- **401 Unauthorized**: requires token refresh, CAS redirect, or auth notice
- **403 Forbidden**: explicitly warn user of insufficient permissions

### 4. Global Errors (5xx)
- All 500 Internal Server Error and other 5xx
- All uncategorized errors outside types 1-3

## Frontend Display Rules
- **Field validation errors** → red highlighting on corresponding form fields
- **Global errors** → red banner: "В системе произошла ошибка. Попробуйте позже" ("A system error occurred. Try again later.")

## Protocol Requirements
1. Frontend must **NOT rely on HTTP status codes** for business logic
2. Response body must contain **localized `errorCode`** parameter
3. Error codes must **specify entity type**: `exception.project.already.exists` (not generic `exception.already.exists`)

## Implications for Testing
- All API error responses should include `errorCode` in body
- Error codes should follow entity-specific naming convention
- Frontend should handle all 4 error categories with appropriate UI
- 409 responses may not always warrant user-visible error messages

## Related
- [[architecture/security-patterns]] — auth error handling (401/403)
- [[architecture/api-surface]] — API endpoint testing
- [[architecture/frontend-architecture]] — frontend error display
- [[external/requirements/google-docs-inventory]] — source document

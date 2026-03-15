---
type: exploration
tags:
  - api-testing
  - reports
  - bugs
  - timemachine
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[exploration/api-findings/vacation-crud-api-testing]]'
  - '[[architecture/security-patterns]]'
  - '[[modules/ttt-report-service]]'
branch: release/2.1
---
# Report CRUD API Testing

Full lifecycle testing of task report submission flow on timemachine environment via API.

## Test Employee
- Login: pvaynmaster (Pavel Weinmeister), Office: Persei (id=20)
- Project: Estimations (id=2), single project membership
- Test task created: "Estimations / API Test Task Session8" (id=707600)

## Report Period Context
- Office report period starts: 2026-03-01
- Office approve period starts: 2026-02-01
- Monthly norm: 176h, weekly norm: 40h

## Endpoints Tested

### READ Operations
| Endpoint | Permission | Status | Notes |
|----------|-----------|--------|-------|
| GET /v1/reports | REPORTS_VIEW | Works | startDate+endDate required; returns employee→tasks→reports grouped |
| GET /v1/reports/summary | REPORTS_VIEW | Works | Requires login+date params; returns week/month norm+reported |
| GET /v1/reports/total | REPORTS_VIEW | Works | type=PROJECT or EMPLOYEE required; periodType=DAY/WEEK/MONTH |
| GET /v1/reports/effort | No @PreAuthorize | Works | Requires taskId; **missing auth annotation** |
| GET /v1/reports/employee-projects | No @PreAuthorize | Works | **Missing auth annotation** |
| GET /v1/reports/accounting | AUTHENTICATED_USER only | 403 | Not accessible via API token |
| GET /v1/reports/employees-over-reported | REPORTS_VIEW | Works | Requires date param |
| GET /v1/task-report-warnings | AUTHENTICATED_USER only | 403 | Not accessible via API token |
| GET /v1/task-auto-reject-warnings | AUTHENTICATED_USER only | 403 | Not accessible via API token |

### WRITE Operations
| Endpoint | Permission | Status | Notes |
|----------|-----------|--------|-------|
| POST /v1/reports | REPORTS_EDIT | Works | Creates single report |
| PUT /v1/reports | REPORTS_EDIT | Works | Batch create/replace |
| PATCH /v1/reports/{id} | REPORTS_EDIT or REPORTS_APPROVE | Works | Edit effort, comment, state |
| PATCH /v1/reports | REPORTS_EDIT or REPORTS_APPROVE | Works | Batch patch |
| DELETE /v1/reports | REPORTS_EDIT or REPORTS_APPROVE | Works | By ids array, 204 on success |

## CRUD Lifecycle Verified
1. **CREATE** → POST with taskId, executorLogin, reportDate, effort(min), state → returns id, permissions
2. **READ** → GET with startDate/endDate/executorLogin → grouped by employee→task→reports
3. **PATCH effort** → PATCH /{id} with new effort+comment → state preserved
4. **APPROVE** → PATCH /{id} with state=APPROVED → approverLogin set
5. **REJECT** → PATCH /{id} with state=REJECTED → stateComment preserved
6. **RE-REPORT** → PATCH /{id} with state=REPORTED → resets from REJECTED
7. **DELETE** → DELETE with ids= → 204 No Content
8. **BATCH CREATE** → PUT with items array → returns array
9. **BATCH APPROVE** → PATCH with items array → bulk state change

## Bugs Found

### HIGH: No upper bound on effort (BUG-REPORT-1)
- Created report with effort=1500 min (25 hours) → **accepted without validation**
- Summary counted it (29h total), but over-reported endpoint returned 0
- Minimum validated (>=1 min), maximum not

### HIGH: Self-approval via API (BUG-REPORT-2)
- PATCH with state=APPROVED → approverLogin=pvaynmaster (same as executor)
- Same pattern as vacation module — no executor≠approver check
- Also works for batch approve

### HIGH: Direct create-as-APPROVED (BUG-REPORT-3)
- POST with state=APPROVED → accepted, approverLogin=pvaynmaster
- Completely bypasses the approval workflow
- No validation that creator ≠ approver

### MEDIUM: Cross-employee reporting (BUG-REPORT-4)
- POST with executorLogin=sterekhin (different from token owner pvaynmaster)
- **Accepted** — report created with executor=sterekhin, reporter=pvaynmaster
- API token owner can report hours for any employee

### MEDIUM: Future date accepted (BUG-REPORT-5)
- POST with reportDate=2026-03-25 (13 days ahead) → accepted
- May be intentional design, but allows pre-reporting

### LOW: Missing @PreAuthorize on two endpoints (BUG-REPORT-6)
- /reports/effort — no auth check at all
- /reports/employee-projects — no auth check at all
- Any valid API request (even with minimal permissions) can access

## Validation Behavior
| Input | Result |
|-------|--------|
| Zero effort (0) | Rejected: Min=1 |
| Negative effort (-60) | Rejected: Min=1 |
| Excessive effort (1500 min = 25h) | **Accepted** (no max) |
| Duplicate (same task+date) | Rejected: 409 Conflict + existentObject |
| Closed period (Feb 2026) | Rejected: 400 validation |
| Future date (Mar 25) | **Accepted** |
| Invalid task name format | Rejected: TaskName validator |

## Data Cleanup
All test reports deleted. Test task (707600) remains in Estimations project.

## Related
- [[exploration/api-findings/vacation-crud-api-testing]] — similar self-approval and cross-entity bugs
- [[architecture/security-patterns]] — AUTHENTICATED_USER design confirmed
- [[modules/ttt-report-service]] — backend service implementation
- [[modules/frontend-report-module]] — frontend report module
- [[modules/ttt-report-confirmation-flow]] — confirmation flow details

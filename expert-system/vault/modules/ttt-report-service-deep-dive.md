---
type: module
tags:
  - reports
  - backend
  - deep-dive
  - code-level
  - validators
  - permissions
  - error-handling
  - state-machine
  - locks
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[modules/ttt-report-service]]'
  - '[[modules/ttt-report-confirmation-flow]]'
  - '[[analysis/reports-business-rules-reference]]'
  - '[[exploration/api-findings/report-crud-api-testing]]'
branch: release/2.1
---
# TTT Report Service Deep Dive — Code-Level Reference

Comprehensive code-level reference for the task report / confirmation module. Contains exact code snippets, error codes, validation rules, permission logic, state machine, lock management, and API response formats.

## 1. State Machine (TaskReportState)

Three states with automatic transitions on effort changes:

```
CREATE → REPORTED
PATCH effort (any state) → automatic reset to REPORTED
PATCH state=APPROVED (from REPORTED) → APPROVED (requires APPROVE permission)
PATCH state=REJECTED (from REPORTED) → REJECTED (requires APPROVE permission)
PATCH state=REPORTED → REPORTED (manual reset)
effort = 0 → DELETE report (publishes TaskReportDeleteEvent)
```

**Key behavioral rules:**
- Changing effort ALWAYS resets state to REPORTED, regardless of current state
- Setting effort to 0 deletes the report entirely
- APPROVED and REJECTED are "soft terminal" — they block edits but effort change resets them
- There is no explicit "un-approve" — changing effort is the mechanism to un-approve

## 2. Controller Endpoints (TaskReportController: `/v1/reports`)

| Method | Path | Permission | Validators | HTTP Status |
|---|---|---|---|---|
| GET | `/search` | AUTHENTICATED_USER / REPORTS_VIEW | @TaskReportSearchRequest, @TaskReportSearchRequestPeriod | 200 |
| POST | `/create` | AUTHENTICATED_USER / REPORTS_EDIT | @NotNull(taskId, reportDate, executorLogin), @Min(1) effort, @ReportPeriod | 201 |
| PUT | `/create-batch` | AUTHENTICATED_USER / REPORTS_EDIT | Each item validated independently | 200 |
| PATCH | `/{id}` | AUTHENTICATED_USER / REPORTS_EDIT / REPORTS_APPROVE | @Min(0) effort, locks checked | 200 (or 423) |
| PATCH | (batch) | AUTHENTICATED_USER / REPORTS_EDIT / REPORTS_APPROVE | Per-item validation | 200 |
| DELETE | (visible) | AUTHENTICATED_USER / REPORTS_EDIT / REPORTS_APPROVE | — | 200 |
| GET | `/effort` | AUTHENTICATED_USER | — | 200 |
| GET | `/accounting` | AUTHENTICATED_USER | Paginated + filtered | 200 |
| POST | `/send-accounting-notifications` | AUTHENTICATED_USER | — | 200 |
| GET | `/total` | — | — | 200 |
| GET | `/summary` | — | — | 200 |
| GET | `/over-reported` | — | — | 200 |

**NOTE:** PATCH endpoint returns **HTTP 423** on `TttLockException` — unique to this module.
**NOTE:** Create returns **HTTP 201**, not 200 — differs from vacation module.

## 3. Validation Rules

### TaskReportCreateRequestDTO

```java
// Extends TaskReportEditRequestDTO, adds:
taskId:        @NotNull Long        // Task to report on
reportDate:    @NotNull LocalDate   // Date of work
executorLogin: @NotNull @EmployeeLoginExists String  // Employee
effort:        @NotNull @Min(1) Long  // Minutes (minimum 1 for create!)

// Class-level: @ReportPeriod
// Initial state forced to TaskReportState.REPORTED
```

### TaskReportEditRequestDTO (base for edits)

```java
effort:       @Min(0) Long          // Minutes (allows 0 → triggers deletion!)
reportComment: String               // Optional
state:        TaskReportState       // REPORTED, APPROVED, REJECTED
stateComment: String                // Rejection reason
```

**Critical difference:** Create requires `@Min(1)`, edit allows `@Min(0)`. Setting effort=0 on edit deletes the report.

### ReportPeriodValidator

```java
// Validates reportDate against employee's report period
public boolean isValid(TaskReportCreateRequestDTO request, ConstraintValidatorContext ctx) {
    if (executorLogin is blank || reportDate is null) return true; // skip validation
    EmployeeBO executor = employeeService.getByLogin(request.getExecutorLogin());
    LocalDate reportPeriodStart = periodService.getReportPeriod(executor).getStart();
    return !request.getReportDate().isBefore(reportPeriodStart);
}
// Error code: constraint.report.period (implicit)
```

### TaskReportSearchRequestValidator

```java
// At least one filter criterion required:
return taskId != null || executorLogin is not blank
    || executorsProjectId != null || projectId != null;
```

## 4. Permission Model

### TaskReportPermissionType (per-report permissions)

| Permission | Who Gets It | Conditions |
|---|---|---|
| EDIT | User with TaskPermissionType.REPORT | reportDate >= report period start AND (project not FINISHED or reportDate <= finishDate) |
| DELETE | Same as EDIT | (implies EDIT) |
| APPROVE | User with TaskPermissionType.APPROVE | reportDate >= approval period start |

### Permission Calculation Flow

```
1. Group reports by executor → by task
2. For each task: TaskPermissionService → TaskPermissionType set
3. For each report:
   canEdit = has REPORT permission + date in period + project active
   canApprove = has APPROVE permission + date in approval period
4. PeriodState = CLOSED if reportDate < period start, OPEN otherwise
```

### State Change Permission Requirements

```java
// In InternalTaskReportService.patch():
// If changing effort → requires EDIT permission
// If changing state to APPROVED/REJECTED → requires APPROVE permission
// Effort change automatically resets state to REPORTED (even if APPROVED)
```

## 5. Lock Management

Per-field locks with 1-minute timeout:

```java
// Lock fields tracked per report:
EFFORT, REPORT_COMMENT, STATE, STATE_COMMENT

// Lock conflict handling:
// If field locked by another employee → TttLockException → HTTP 423
// Locks are employee-specific and auto-expire after 1 minute
// Must re-create lock to extend duration
// Batch operations synchronized per executor
```

**HTTP 423 (Locked)** is unique to the reports module — vacation module doesn't use locking.

## 6. Error Handling (TTT Service RestErrorHandler)

| Exception | HTTP Status | Error Code |
|---|---|---|
| NotFoundException | 404 | NOT_FOUND |
| TttLockException | 423 | `exception.ttt.lock` |
| TttSecurityException | 403 | `exception.ttt.security` |
| ProjectFinishedException | 403 | FORBIDDEN |
| AlreadyExistsException | 409 | CONFLICT |
| ValidationException | 400 | BAD_REQUEST |
| MethodArgumentNotValidException | 400 | BAD_REQUEST (with field details) |
| ConstraintViolationException | 400 | BAD_REQUEST (with field details) |
| AccessDeniedException | 403 | FORBIDDEN |
| ServiceException | 500 | INTERNAL_SERVER_ERROR |

**NOTE:** ServiceException maps to **500** in TTT service, but **400** in vacation service — inconsistent!

## 7. Create/Update/Delete Orchestration

### Create Flow

```java
create(TaskReportCreateRequestDTO request)
  1. Validate: taskId, reportDate, executorLogin, effort >= 1
  2. Check: AlreadyExistsException if report exists for task+date+executor
  3. Check: ProjectFinishedException if project is finished
  4. Check: TttSecurityException if no EDIT permission
  5. Set initial state: REPORTED
  6. Create locks per field: EFFORT, REPORT_COMMENT, STATE, STATE_COMMENT
  7. Publish: TaskReportAddEvent
  8. Return: HTTP 201 + TaskReportDTO
```

### Patch Flow (Single Report)

```java
patch(id, TaskReportEditRequestDTO request)
  1. Fetch report + acquire lock
  2. Check field locks → TttLockException (423) if locked by another user
  3. If effort changes:
     a. Update effort/comment via fillEfforts()
     b. If effort becomes 0 → delete report, publish TaskReportDeleteEvent
     c. If state not explicitly changing → auto-reset to REPORTED
  4. If state changes:
     a. If state=APPROVED → set approverLogin, clear rejection, audit
     b. If state=REJECTED → create reject entity with comment, clear approver
     c. Requires APPROVE permission for APPROVED/REJECTED transitions
  5. Publish: TaskReportPatchEvent
  6. Return: HTTP 200 + TaskReportDTO
```

### Auto-Reject Flow (System-Initiated)

Reports can be auto-rejected by the system when:
- Report period advances past the report date
- Accounting period closes
- Triggered via `send-accounting-notifications` endpoint or cron job

## 8. Event System

| Event | Trigger | Payload |
|---|---|---|
| TaskReportAddEvent | Report creation | TaskReportBO |
| TaskReportPatchEvent | Report update | TaskReportEditRequestBO + before-state |
| TaskReportDeleteEvent | Report deletion (including effort=0) | TaskReportBO |

Events drive:
- Statistics/cache updates (via RabbitMQ to vacation service)
- Audit trail
- Notification triggers

## 9. Response DTO Structure

```json
{
    "id": 12345,
    "state": "REPORTED",         // REPORTED | APPROVED | REJECTED
    "stateComment": null,        // Non-null when REJECTED
    "effort": 480,               // Minutes
    "reportDate": "2026-03-15",
    "executorLogin": "ivanov",
    "reportComment": "API development",
    "reporterLogin": "ivanov",   // Who submitted
    "approverLogin": null,       // Non-null when APPROVED
    "periodState": "OPEN",       // OPEN | CLOSED
    "projectState": {            // Embedded project info
        "id": 42,
        "name": "TTT",
        "status": "ACTIVE"
    },
    "permissions": ["EDIT", "DELETE"]  // Current user's allowed actions
}
```

## Related
- [[modules/ttt-report-service]] — compressed overview
- [[modules/ttt-report-confirmation-flow]] — confirmation workflow
- [[analysis/reports-business-rules-reference]] — business rules
- [[analysis/report-form-validation-rules]] — frontend validation
- [[exploration/api-findings/report-crud-api-testing]] — API test results (6 bugs)
- [[modules/vacation-service-deep-dive]] — comparison with vacation error handling

---
type: module
tags:
  - vacation
  - backend
  - deep-dive
  - code-level
  - validators
  - permissions
  - error-handling
  - state-machine
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[analysis/vacation-business-rules-reference]]'
  - '[[modules/vacation-service-implementation]]'
  - '[[analysis/vacation-form-validation-rules]]'
  - '[[exploration/api-findings/vacation-crud-api-testing]]'
branch: release/2.1
---
# Vacation Service Deep Dive — Code-Level Reference

Comprehensive code-level reference for the vacation service module. Contains exact code snippets, error codes, validation rules, permission logic, and API response formats needed for test case generation.

## 1. State Machine Implementation (VacationStatusManager)

The state machine is implemented as a static transition map in `VacationStatusManager`:

```java
// VacationStatusManager.java — static initializer block
static {
    // NEW → ...
    add(NEW, NEW, ROLE_EMPLOYEE);          // Self-update
    add(NEW, CANCELED, ROLE_EMPLOYEE);     // Employee cancels
    add(NEW, REJECTED, ROLE_PROJECT_MANAGER, ROLE_DEPARTMENT_MANAGER, ROLE_ADMIN);
    add(NEW, APPROVED, ROLE_PROJECT_MANAGER, ROLE_DEPARTMENT_MANAGER, ROLE_ADMIN);

    // REJECTED → ...
    add(REJECTED, APPROVED, ROLE_PROJECT_MANAGER, ROLE_DEPARTMENT_MANAGER, ROLE_ADMIN);
    // NOTE: No REJECTED→NEW transition exists in code!
    // The business rules reference says "REJECTED → APPROVED (re-approval without edit)" is confirmed.

    // APPROVED → ...
    add(APPROVED, NEW, ROLE_EMPLOYEE);     // Employee edits dates → resets
    add(APPROVED, CANCELED, ROLE_EMPLOYEE);
    add(APPROVED, REJECTED, ROLE_PROJECT_MANAGER, ROLE_DEPARTMENT_MANAGER, ROLE_ADMIN);
    add(APPROVED, PAID, ROLE_ACCOUNTANT, ROLE_CHIEF_ACCOUNTANT, ROLE_ADMIN);

    // CANCELED → ...
    add(CANCELED, NEW, ROLE_EMPLOYEE);     // Re-open
}

// Terminal statuses (no outgoing transitions):
private static final Set<VacationStatusType> FINAL_STATUSES = Set.of(PAID, CANCELED);
// NOTE: CANCELED is in FINAL_STATUSES but has CANCELED→NEW transition!
// This means isNextStateAvailable() allows CANCELED→CANCELED (same status check bypasses
// FINAL_STATUSES for non-equal transitions) but CANCELED→NEW works via explicit map.
```

### Access Check Logic (`hasAccess`)

```java
public boolean hasAccess(EmployeeBO employee, VacationEntity request, VacationStatusType status) {
    if (employee == null || request == null) return false;

    // Owner check: ROLE_EMPLOYEE + owns the vacation
    if (employee.getRoles().contains(ROLE_EMPLOYEE)
        && request.getEmployeeId().equals(employee.getId())) {
        return true;
    }

    // Approver check: not PAID status AND not canceling, AND is manager role, AND is current approver
    if (request.getStatus() != PAID && status != CANCELED) {
        return employee.getRoles().stream().anyMatch(MANAGER_ROLES::contains)
               && Objects.equals(request.getApproverId(), employee.getId());
    }
    return false;
}
// MANAGER_ROLES = {ROLE_PROJECT_MANAGER, ROLE_DEPARTMENT_MANAGER, ROLE_CHIEF_ACCOUNTANT}
// NOTE: ROLE_CHIEF_ACCOUNTANT is in MANAGER_ROLES (not ACCOUNTANT_ROLES only!)
// BUG: ROLE_ADMIN is NOT in MANAGER_ROLES but IS in transition map → admin can transition
// but hasAccess() returns false for admin-as-approver → ServiceException thrown
```

### `isNextStateAvailable` Logic

```java
public boolean isNextStateAvailable(Collection<EmployeeGlobalRole> userRoles,
                                     VacationEntity request, VacationStatusType nextStatus) {
    VacationStatusType currentStatus = request.getStatus();
    // Same-status update: allowed unless current is a FINAL status (PAID, CANCELED)
    if (currentStatus.equals(nextStatus) && !FINAL_STATUSES.contains(currentStatus)) {
        return true;
    }
    // Check transition map
    List<EmployeeGlobalRole> allowedRoles = ALLOWED_TRANSITIONS.get(st(currentStatus, nextStatus));
    return allowedRoles != null && isContains(userRoles, allowedRoles);
}
// Edge case: CANCELED is FINAL but CANCELED→NEW transition IS in the map
// So isNextStateAvailable(CANCELED, NEW) checks the map → works if ROLE_EMPLOYEE
```

## 2. Vacation CRUD Orchestration (VacationServiceImpl)

### Create Flow

```java
public VacationBO createVacation(VacationCreateRequestBO request) {
    // 1. Class-level permission check
    classPermissionService.validate(PermissionVacationActionType.CREATE);

    // 2. Lookup employee
    EmployeeBO employee = employeeService.findByLogin(request.getLogin());

    // 3. Correct payment month (adjusts if needed)
    vacationCRUDService.correctPaymentMonth(request);

    // 4. Validate payment date
    if (!vacationCRUDService.isPaymentDateCorrect(request)) {
        throw new ServiceException(ErrorCode.of("validation.vacation.dates.payment"));
    }

    // 5. Check crossing vacations
    if (!vacationCRUDService.findCrossingVacations(employee.getId(), startDate, endDate).isEmpty()) {
        throw new ValidationException("startDate", "exception.validation.vacation.dates.crossing");
    }

    // 6. Determine approver (CPO vs regular vs no-manager)
    if (employee.getManager() != null && isCPO) {
        vacation.setApproverId(employee.getId());  // Self-approve
        request.getOptionalApprovers().add(employee.getManager().getLogin()); // Manager as optional
    } else if (employee.getManager() != null) {
        vacation.setApproverId(employee.getManager().getId()); // Manager approves
    } else {
        vacation.setApproverId(employee.getId()); // Self-approve (no manager)
    }

    // 7. Save, calculate days, recalculate, sync approvers, publish event
    savedVacation = vacationRepository.save(vacation);
    VacationState vacationState = vacationStateFactory.create(savedVacation);
    savedVacation.setDays(vacationState.getVacationDays().getTotal().intValue());
    vacationRecalculationService.recalculate(employee.getId(), null, false);
    synchronizeOptionalApprovals(savedVacation, request.getOptionalApprovers());
    synchronizeNotifyAlso(savedVacation, request.getNotifyAlso());
    eventPublisher.publishEvent(new VacationCreatedEvent(savedVacationBO));
}
```

### Approve Flow

```java
public VacationBO approveVacation(Long vacationId) {
    VacationEntity entity = vacationRepository.findByIdAndAcquireWriteLock(vacationId);
    VacationBO vacation = convert(entity);

    // 1. Permission check (validates current user is approver with APPROVE permission)
    permissionService.validate(vacation, PermissionType.APPROVE);

    // 2. Status transition check
    checkVacation(entity, APPROVED, true); // true = check for crossing

    // 3. Payment date adjustment
    EmployeeBO employee = employeeService.findById(entity.getEmployeeId());
    LocalDate approvePeriodStartDate = tttClient.getApprovePeriod(employee.getOfficeId()).getStart();
    LocalDate paymentDate = vacationCRUDService.getPaymentDate(entity);
    if (paymentDate.isBefore(approvePeriodStartDate)) {
        entity.setPaymentDate(approvePeriodStartDate.with(TemporalAdjusters.firstDayOfMonth()));
    }

    // 4. Status update + recalculation
    entity.setStatus(APPROVED);
    vacationRecalculationService.recalculate(employee.getId(), null, false);
    eventPublisher.publishEvent(new VacationStatusChangedEvent(updatedVacation, previousStatus));
}
```

### Delete Flow — Critical Guard

```java
private void deleteVacation(VacationEntity vacation) {
    // GUARD: Cannot delete PAID + EXACT vacations
    if (vacation.getStatus().equals(PAID)
        && vacation.getPeriodType() == VacationPeriodType.EXACT) {
        throw new ServiceException(ErrorCode.of("exception.vacation.delete.notAllowed"));
    }
    vacationRecalculationService.recalculate(vacation.getEmployeeId(), vacation.getId(), false);
    vacation.setStatus(VacationStatusType.DELETED);
    vacationRepository.save(vacation);
}
// NOTE: PAID + NON-EXACT can be deleted! (This is a design issue — PAID should be terminal)
```

### checkVacation — Combined Pre-check for Status Changes

```java
public void checkVacation(VacationEntity entity, VacationStatusType status, boolean checkForCrossing) {
    EmployeeBO employee = employeeService.getCurrent();

    // 1. ReadOnly check
    if (employee.isReadOnly()) throw new VacationSecurityException();

    // 2. Access check (owner or approver)
    if (!statusManager.hasAccess(employee, entity, status))
        throw new ServiceException(ErrorCode.of("exception.vacation.status.notAllowed"));

    // 3. State transition check
    if (!statusManager.isNextStateAvailable(employee.getRoles(), entity, status))
        throw new ServiceException(ErrorCode.of("exception.vacation.status.notAllowed"));

    // 4. Crossing check (only for approve)
    if (checkForCrossing && !vacationCRUDService.findCrossingVacations(...).isEmpty())
        throw new ValidationException("startDate", "exception.validation.vacation.dates.crossing");
}
```

## 3. Permission Service Logic (VacationPermissionService)

### Permission Calculation

```java
// Status sets controlling permission availability:
APPROVABLE_STATUSES = {NEW, REJECTED}
REJECTABLE_STATUSES = {NEW, APPROVED}
NON_EDITABLE_STATUSES = {CANCELED, PAID}

private Set<PermissionType> calculate(VacationBO vacation, EmployeeBO currentEmployee) {
    // GUARD: readOnly users or non-ROLE_EMPLOYEE → no permissions
    if (currentEmployee.isReadOnly()
        || !currentEmployee.getRoles().contains(ROLE_EMPLOYEE)) {
        return Collections.emptySet();
    }

    boolean isApprover = Objects.equals(currentEmployee, vacation.getApprover());
    boolean isOwner = vacation.getEmployee().getId().equals(currentEmployee.getId());

    // APPROVER permissions:
    if (isApprover) {
        if (!NON_EDITABLE_STATUSES.contains(status))  → EDIT_APPROVER
        if (APPROVABLE_STATUSES.contains(status))      → APPROVE
        if (REJECTABLE_STATUSES.contains(status) && canBeCancelled) → REJECT
    }

    // OWNER permissions (status != PAID):
    if (isOwner && status != PAID) {
        if (canBeCancelled) → DELETE, CANCEL (unless CANCELED)
        → EDIT (always, if not PAID)
    }
}

// canBeCancelled guard:
private boolean canBeCancelled(VacationBO vacation, LocalDate reportPeriod) {
    return vacation.getPaymentType() != REGULAR
           || vacation.getStatus() != APPROVED
           || !reportPeriod.isAfter(vacation.getPaymentDate());
}
// This means: REGULAR + APPROVED + reportPeriod after paymentDate → CANNOT cancel/reject/delete
// This protects against canceling vacations after the accounting period has closed.
```

### Permission Types Used

| Permission | Who Gets It | When |
|---|---|---|
| EDIT_APPROVER | Approver | Status not CANCELED/PAID |
| APPROVE | Approver | Status is NEW or REJECTED |
| REJECT | Approver | Status is NEW or APPROVED, canBeCancelled=true |
| DELETE | Owner | Status not PAID, canBeCancelled=true |
| CANCEL | Owner | Status not PAID/CANCELED, canBeCancelled=true |
| EDIT | Owner | Status not PAID (always) |

## 4. Validation Rules — Complete Error Code Catalog

### VacationCreateValidator Error Codes

| Error Code | Condition | Fields |
|---|---|---|
| `validation.vacation.start.date.in.past` | startDate < today | startDate |
| `validation.vacation.dates.order` | startDate > endDate | startDate, endDate |
| `validation.vacation.next.year.not.available` | startDate.year > today.year AND today < Feb 1 | startDate |
| `validation.vacation.duration` | REGULAR type AND (thisYear + nextYear < minimalVacationDuration OR availablePaidDays < total) | startDate, endDate |
| `exception.validation.vacation.too.early` | Vacation days under limitation date exceed limit | startDate, endDate |

### VacationUpdateValidator — Differences from Create

```java
// Key difference: CANCELED or REJECTED vacations + ADMINISTRATIVE type skip day limit checks
if (VacationPaymentType.ADMINISTRATIVE.equals(entity.getPaymentType())
    || VacationStatusType.CANCELED.equals(entity.getStatus())
    || VacationStatusType.REJECTED.equals(entity.getStatus())) {
    // Uses raw daysLimitations from employee (original limits)
} else {
    // Adjusts limitations: adds back the current vacation's consumed days
    // This allows editing within the same day budget
}
// NOTE: Update validator does NOT call isNextVacationAvailable()
// → Next year check only applies to create, not update!
```

### Service-Level Error Codes (VacationServiceImpl)

| Error Code | Condition | HTTP Status |
|---|---|---|
| `validation.vacation.dates.payment` | Payment date invalid (correctPaymentMonth + isPaymentDateCorrect) | 400 |
| `exception.validation.vacation.dates.crossing` | Overlapping vacation exists | 400 (ValidationException) |
| `exception.vacation.status.notAllowed` | No access or invalid transition | 400 (ServiceException) |
| `exception.vacation.delete.notAllowed` | Delete PAID+EXACT, or changeApprover to self | 400 |
| `exception.vacation.no.permission` | VacationSecurityException | 403 |

### DTO-Level Validation Annotations

```java
// AbstractVacationRequestDTO
login:            @NotNull @EmployeeLoginExists @CurrentUser(groups=CreateGroup.class)
startDate:        @NotNull
endDate:          @NotNull
paymentType:      @NotNull (VacationPaymentTypeDTO enum)
paymentMonth:     (NO ANNOTATIONS — NPE if null when REGULAR type!)
comment:          (optional)
notifyAlso:       @EmployeeLoginCollectionExists (can be null)
optionalApprovers: @EmployeeLoginCollectionExists (can be null → NPE in synchronizeOptionalApprovals!)

// VacationUpdateRequestDTO extends AbstractVacationRequestDTO
id:               @Min(1) @NotNull

// VacationPaymentDTO (for pay endpoint)
payedAt:          @JsonFormat("yyyy-MM-dd") (optional)
regularDaysPayed:      @NotNull @Range(min=0, max=366)
administrativeDaysPayed: @NotNull @Range(min=0, max=366)
```

## 5. API Error Response Format

### Standard Error Response (ErrorResponse)

```json
{
    "error": "Bad Request",           // HTTP status reason phrase
    "status": 400,                    // HTTP status code
    "exception": "com.noveogroup.ttt.common.exception.ServiceException",
    "errorCode": "validation.vacation.dates.payment",
    "message": "Payment date is incorrect",
    "path": "/api/vacation/v1/vacations",
    "timestamp": "2026-03-15T10:30:00"
}
```

### Validation Error Response (extends ErrorResponse)

```json
{
    "error": "Bad Request",
    "status": 400,
    "errorCode": "exception.validation",
    "exception": "javax.validation.ConstraintViolationException",
    "message": "...",
    "path": "/api/vacation/v1/vacations",
    "timestamp": "...",
    "errors": [
        {
            "field": "startDate",
            "code": "validation.vacation.start.date.in.past",
            "message": "Start date is in the past"
        },
        {
            "field": "endDate",
            "code": "validation.vacation.dates.order",
            "message": "End date must be after start date"
        }
    ]
}
```

### Error Handler Exception Mapping

| Exception | HTTP Status | Error Code |
|---|---|---|
| ConstraintViolationException | 400 | Validator class name in `errors[].code` |
| MethodArgumentNotValidException | 400 | Message template in `errors[].code` |
| ValidationException | 400 | `exception.validation` + `errors[0].code` = field-level code |
| ServiceException | 400 | exception.getErrorCode() |
| VacationSecurityException | 403 | `exception.vacation.no.permission` |
| NotFoundException | 404 | exception.getErrorCode() |
| EntityNotFoundException | 404 | `exception.not.found` |
| SickLeaveCrossingVacationException | 409 (CONFLICT) | exception.getErrorCode() |
| IllegalArgumentException | 400 | `exception.illegal.argument` |
| HttpMessageNotReadableException | 400 | (empty body!) |
| MethodArgumentTypeMismatchException | 400 | `exception.type.mismatch` |
| FeignException | Proxied status | `exception.integration` (if deserialization fails) |

**CRITICAL NOTE:** `HttpMessageNotReadableException` returns **empty body** with 400 status!
This means sending malformed JSON gets no error details — just `ResponseEntity<Void>`.

**INFO DISCLOSURE:** `exception` field contains full Java class name (e.g., `com.noveogroup.ttt.common.exception.ServiceException`). This leaks internal implementation details.

## 6. Controller Endpoint Security Matrix

### VacationController (`/v1/vacations`)

| Method | Path | Permission | Custom Validators |
|---|---|---|---|
| GET | `/{vacationId}` | AUTHENTICATED_USER / VACATIONS_VIEW | @VacationIdExists |
| GET | (list) | AUTHENTICATED_USER / VACATIONS_VIEW | — |
| POST | (create) | AUTHENTICATED_USER / VACATIONS_CREATE | @Validated(CreateGroup) + @VacationCreateRequest |
| PUT | `/{vacationId}` | AUTHENTICATED_USER / VACATIONS_EDIT | @Validated(UpdateGroup) + @VacationUpdate |
| POST | `/{vacationId}/approve` | AUTHENTICATED_USER / VACATIONS_APPROVE | @VacationIdExists |
| PUT | `/{vacationId}/reject` | AUTHENTICATED_USER / VACATIONS_DELETE | — |
| PUT | `/{vacationId}/change-approver` | AUTHENTICATED_USER / VACATIONS_APPROVE | — |
| PUT | `/{vacationId}/cancel` | AUTHENTICATED_USER / VACATIONS_DELETE | — |
| PUT | `/{vacationId}/pay` | AUTHENTICATED_USER / VACATIONS_PAY | @Valid |
| DELETE | `/{vacationId}` | AUTHENTICATED_USER / VACATIONS_DELETE | @VacationIdExists |

**NOTE:** Reject uses `VACATIONS_DELETE` permission, not a dedicated REJECT permission.
**NOTE:** Cancel also uses `VACATIONS_DELETE` — same permission for reject, cancel, and delete.

## 7. Known NPE Vulnerabilities (from code analysis)

1. **`paymentMonth: null`** — VacationCreateRequestDTO has no @NotNull on paymentMonth. When REGULAR type, `correctPaymentMonth()` may NPE.
2. **`optionalApprovers: null`** — `synchronizeOptionalApprovals()` calls `optionalApproversLogins == null` → calls `deleteAll()`. But `request.getOptionalApprovers().add()` in CPO path will NPE if originally null.
3. **`pagination: null`** — Availability schedule endpoints accept nullable Pageable → NPE in repository.

## Related
- [[analysis/vacation-business-rules-reference]] — business rules summary
- [[modules/vacation-service-implementation]] — compressed overview
- [[analysis/vacation-form-validation-rules]] — frontend validation
- [[exploration/api-findings/vacation-crud-api-testing]] — API test results with bugs
- [[exploration/api-findings/payment-flow-live-testing]] — payment bug findings
- [[analysis/role-permission-matrix]] — cross-module permission matrix
- [[patterns/error-handling-agreement]] — error handling patterns

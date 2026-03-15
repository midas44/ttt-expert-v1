---
type: module
tags:
  - day-off
  - service
  - deep-dive
  - code-analysis
  - permissions
  - validation
  - calendar
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[vacation-service-deep-dive]]'
  - '[[day-off-overview]]'
  - '[[vacation-approval-flow]]'
  - '[[calendar-management]]'
branch: release/2.1
---
# Day-Off Service Deep Dive

Code-level analysis of the employee day-off subsystem within the vacation service. Covers service implementation, validators, permission logic, calendar conflict resolution, optional approvers, and event system.

## 1. Status Model

### EmployeeDayOffStatusType (6 values)
```java
public enum EmployeeDayOffStatusType {
    NEW,                    // Initial state on creation
    APPROVED,               // Manager approved
    REJECTED,               // Manager rejected OR system-rejected
    DELETED,                // Soft-deleted by owner
    DELETED_FROM_CALENDAR,  // Auto-deleted when calendar day removed
    CANCELED                // Unused in code — dead status?
}
```

**Key difference from vacation**: Day-off has no PAID status (day-offs are not paid separately). Has DELETED_FROM_CALENDAR — a system-driven status absent from vacation.

### EmployeeDayOffApproveStatusType (optional approvers)
```java
public enum EmployeeDayOffApproveStatusType {
    ASKED,     // Awaiting response
    APPROVED,  // Optional approver approved
    REJECTED   // Optional approver rejected
}
```

## 2. Entity Model — Dual Entity Pattern

Day-off uses TWO separate entities unlike vacation's single entity:

### EmployeeDayOffRequestEntity (the request)
```java
public class EmployeeDayOffRequestEntity {
    private Long id;
    private Long employeeId;
    private Long approverId;
    private LocalDate lastApprovedDate;   // Previous approved date (for transfer tracking)
    private LocalDate originalDate;       // The calendar date being transferred FROM
    private LocalDate personalDate;       // The target date being transferred TO
    private Integer duration;
    private String reason;
    private EmployeeDayOffStatusType status;
}
```

### EmployeeDayOffEntity (the calendar entry)
```java
public class EmployeeDayOffEntity {
    private Long id;
    private Long employeeId;
    private LocalDate originalDate;
    private LocalDate personalDate;
    private Integer duration;
    private String reason;
}
```

**Design pattern**: Request tracks approval workflow. Entity tracks actual calendar impact. On approve, the entity record is created/updated reflecting the day swap.

## 3. REST API — EmployeeDayOffController

Base path: `/v1/employee-dayOff`

| Method | Path | @PreAuthorize | Purpose |
|--------|------|---------------|---------|
| GET | `/` | AUTHENTICATED_USER \|\| VACATIONS_VIEW | Find all (paginated) |
| POST | `/` | AUTHENTICATED_USER \|\| VACATIONS_CREATE | Create day-off request |
| PATCH | `/{id}` | AUTHENTICATED_USER \|\| VACATIONS_EDIT | Update personal date |
| PUT | `change-approver/{id}/{approverLogin}` | AUTHENTICATED_USER \|\| VACATIONS_APPROVE | Change approver |
| PUT | `approve/{id}` | AUTHENTICATED_USER \|\| VACATIONS_APPROVE | Approve day-off |
| PUT | `reject/{id}` | AUTHENTICATED_USER \|\| VACATIONS_APPROVE | Reject day-off |
| DELETE | `/{id}` | AUTHENTICATED_USER \|\| VACATIONS_DELETE | Delete day-off |
| GET | `list` | AUTHENTICATED_USER \|\| VACATIONS_VIEW | Find approved (list) |

**Design issue**: Uses the same VACATIONS_* authorities as vacation — no separate DAY_OFF_* authorities. This means vacation-level permissions grant day-off access.

### EmployeeDayOffOptionalApproversController

Base path: `/v1/employee-dayOff-approvers`

| Method | Path | @PreAuthorize | Purpose |
|--------|------|---------------|---------|
| GET | `/` | AUTHENTICATED_USER \|\| VACATIONS_VIEW | List optional approvers |
| POST | `/` | AUTHENTICATED_USER \|\| VACATIONS_VIEW | Add optional approver |
| PATCH | `/{id}` | AUTHENTICATED_USER \|\| VACATIONS_VIEW | Update approval status |
| DELETE | `/{id}` | AUTHENTICATED_USER \|\| VACATIONS_VIEW | Remove optional approver |

**Design issue**: POST/PATCH/DELETE use VACATIONS_VIEW authority — should be a write authority. Any user with view permission can add/modify/delete optional approvers.

## 4. DTO Validation

### EmployeeDayOffCreateRequestDTO
```java
public class EmployeeDayOffCreateRequestDTO {
    @EmployeeDayOffPublicDateExists    // Custom validator
    private LocalDate publicDate;
    
    @EmployeeDayOffPersonalDateExists  // Custom validator
    private LocalDate personalDate;
    
    private LocalDate originalDate;     // No validation!
    private Integer duration;           // No validation!
    private String reason;              // No validation!
}
```

**Missing validations**: No @NotNull on any field. No @Min/@Max on duration. No size limit on reason.

### EmployeeDayOffPatchRequestDTO
```java
public class EmployeeDayOffPatchRequestDTO {
    @EmployeeDayOffPersonalDateExists
    private LocalDate personalDate;     // Only field modifiable via PATCH
}
```

## 5. Custom Validators

### EmployeeDayOffPublicDateExistsValidator
Validates the `publicDate` (the calendar date being transferred from):

```java
public boolean isValid(final LocalDate value, final ConstraintValidatorContext context) {
    if (value == null) return true;  // null = valid (no @NotNull enforcement)
    
    final boolean isEmployeeDayOffRequestExists = employeeDayOffService.existsByPublicDate(value);
    final boolean isOfficeDayOffExists = calendarService.isCalendarDayExists(employeeBO, value);
    final boolean isEmployeeDayOffExists = employeeDayOffService.existInEmployeeDayOff(value);
    
    if (isEmployeeDayOffRequestExists) {
        // Error: "validation.EmployeeDayOffPublicDateExists.message"
    }
    if (!isOfficeDayOffExists && !isEmployeeDayOffExists) {
        // Error: "validation.PublicDateNotFoundInCalendar.message"
    }
    return !isEmployeeDayOffRequestExists && (isOfficeDayOffExists || isEmployeeDayOffExists);
}
```

**Error codes**:
- `validation.EmployeeDayOffPublicDateExists.message` — duplicate request for same public date
- `validation.PublicDateNotFoundInCalendar.message` — date doesn't exist in office calendar or employee's day-off calendar

**Logic**: The public date must exist in either the office production calendar OR the employee's personal day-off entries, AND must not already have a request.

### EmployeeDayOffPersonalDateExistsValidator
```java
public boolean isValid(final LocalDate value, final ConstraintValidatorContext context) {
    if (value == null) return true;
    return !employeeDayOffService.existsByPersonalDate(value);
}
```

Checks that the target personal date isn't already used by another day-off request. Uses default constraint message.

## 6. Permission Service — EmployeeDayOffPermissionService

```java
private static final Set<EmployeeDayOffStatusTypeBO> APPROVABLE_STATUSES = {NEW, REJECTED};
private static final Set<EmployeeDayOffStatusTypeBO> REJECTABLE_STATUSES = {NEW, APPROVED};
```

### Permission calculation
```java
private Set<PermissionType> calculate(EmployeeDayOffBO dayOff, EmployeeBO currentEmployee) {
    // Blocked: readOnly users OR non-ROLE_EMPLOYEE
    if (currentEmployee.isReadOnly() || !currentEmployee.getRoles().contains(ROLE_EMPLOYEE))
        return emptySet();
    
    if (isApprover) addApproverPermissions(dayOff, permissions, reportPeriod);
    if (isOwner) addOwnerPermissions(dayOff, permissions, reportPeriod);
    return permissions;
}
```

### Approver permissions
```java
private void addApproverPermissions(dayOff, permissions, reportPeriod) {
    if (APPROVABLE_STATUSES.contains(dayOff.getStatus()))   → APPROVE
    if (REJECTABLE_STATUSES.contains(status) && canBeCancelled)  → REJECT
    permissions.add(EDIT_APPROVER);  // ALWAYS — no status check!
}
```

**Design issue**: `EDIT_APPROVER` is granted unconditionally to the approver regardless of status. This means approver can change approver even on DELETED or DELETED_FROM_CALENDAR day-offs. Compare with vacation where EDIT_APPROVER is blocked for NON_EDITABLE_STATUSES {CANCELED, PAID}.

### Owner permissions
```java
private void addOwnerPermissions(dayOff, permissions, reportPeriod) {
    if (canBeCancelled(dayOff, reportPeriod))  → DELETE
    permissions.add(EDIT);  // ALWAYS — no status check!
}
```

**Design issue**: Owner gets EDIT permission regardless of status — can PATCH a DELETED or DELETED_FROM_CALENDAR day-off. No CANCEL permission type (unlike vacation which has separate CANCEL).

### canBeCancelled guard
```java
private boolean canBeCancelled(EmployeeDayOffBO dayOff, LocalDate reportPeriod) {
    return dayOff.getStatus() != APPROVED || !reportPeriod.isAfter(dayOff.getPersonalDate());
}
```

If status is not APPROVED → can cancel. If APPROVED but personal date is on or after report period start → can cancel. APPROVED and personal date before report period → cannot cancel (already "consumed").

## 7. Service Implementation — EmployeeDayOffServiceImpl

### Create Flow
```java
@Transactional
public EmployeeDayOffBO create(EmployeeDayOffCreateRequestBO requestBO) {
    EmployeeBO current = internalEmployeeService.getCurrent();
    EmployeeDayOffRequestEntity saved = employeeDayOffRequestRepository
            .save(conversionService.convert(requestBO, EmployeeDayOffCreateRequest.class));
    synchronizeOptionalApprovals(saved.getId(), current.getLogin());
    EmployeeDayOffBO savedBO = conversionService.convert(saved, EmployeeDayOffBO.class);
    eventPublisher.publishEvent(new EmployeeDayOffCreatedEvent(savedBO));
    return savedBO;
}
```

No explicit permission check on create — relies on @PreAuthorize at controller level. Auto-syncs optional approvers from employee's configured default approvers.

### Approve Flow — Complex Date Logic
```java
public EmployeeDayOffBO approveDayOff(Long dayOffId) {
    changeDayOffDaysAfterApprove(dayOffId);  // Handle calendar swap
    return changeDayOffStatus(dayOffId, APPROVED, PermissionType.APPROVE);
}
```

`changeDayOffDaysAfterApprove` does the actual calendar manipulation:
1. Gets the day-off request
2. Gets the employee
3. Checks if new date exists in calendar via `calendarService.getCalendarDay()`
4. Gets existing employee_dayoff records for both old date (`lastApprovedDate`) and new date (`personalDate`)
5. Restores the old date's duration/reason (or uses calendar data)
6. Sets new date's duration/reason from the request

**Critical logic**: Uses `@Value("${calendar.reporting-norm}")` as default duration when no existing record found. This is the reporting norm hours value.

### System Rejection
```java
@Transactional
public void rejectedBySystem(Long officeId, LocalDate date) {
    // Get all employees of this office
    List<Long> employeesIds = employeeOfficeRepository.getByOffice(officeId, date.getYear())
            .stream().map(EmployeeOfficeEntity::getEmployeeId).toList();
    // Find all day-off requests for this date
    List<EmployeeDayOffRequestEntity> availableDayOffs =
            employeeDayOffRequestRepository.findByDateAndEmployeesIds(date, employeesIds);
    // Reject all
    availableDayOffs.forEach(dayOff -> {
        dayOff.setStatus(REJECTED);
        // save and publish EmployeeDayOffRejectedBySystemEvent
    });
}
```

Called when a calendar day is removed/changed at office level. Auto-rejects all non-final day-off requests for that date.

### Delete
```java
public EmployeeDayOffBO deleteById(Long dayOffId) {
    return changeDayOffStatus(dayOffId, DELETED, PermissionType.DELETE);
}
```

Soft-delete via status change. Uses same `changeDayOffStatus` as approve/reject.

**Design issue**: No @Transactional on `changeDayOffStatus`, but it's called by `approveDayOff` which also lacks @Transactional. Wraps in `transactionActions.performInTransaction()` instead — works but inconsistent.

### Null return issue
```java
public List<EmployeeDayOffBO> findApprovedByEmployeeAndDate(long employeeId, LocalDate date) {
    List<EmployeeDayOffRequestEntity> entities = ...;
    if (CollectionUtils.isEmpty(entities)) return null;  // Should return empty list!
    return entities.stream()...;
}
```

## 8. Calendar Conflict Resolution

### EmployeeDayOffCalendarUpdateServiceImpl
Handles deletion of day-offs when production calendar changes:

```java
public void deleteDayOffs(LocalDate date) {
    List<EmployeeDayOffStatusType> statuses = List.of(NEW, APPROVED);
    
    // Find requests with matching originalDate AND status NEW/APPROVED
    List<EmployeeDayOffRequestEntity> dayOffRequests = 
            employeeDayOffRequestRepository.findByOriginalDate(date, statuses);
    
    // Find employee_dayoff entries for that date
    List<EmployeeDayOffEntity> dayOffEntities = employeeDayOffRepository.getAllByOriginalDate(date);
    
    // Update request statuses (to DELETED_FROM_CALENDAR implied)
    employeeDayOffRequestRepository.updateAll(dayOffRequests);
    
    // Delete calendar entries
    employeeDayOffRepository.deleteByDate(date);
    
    // Recalculate vacation days for affected employees
    dayOffEntities.forEach(this::recalculateVacation);
    
    // Publish event for notifications
    eventPublisher.publishEvent(new EmployeeDayOffDeletedFromCalendarEvent(dayOffsBO));
}
```

Overloaded with `(date, officeIds)` for office-specific calendar changes.

### CalendarUpdateHasDayOffConflictEventListener
Handles conflicts when a calendar update adds a day that intersects with existing day-offs:

```java
@EventListener
public void handle(CalendarUpdateHasDayOffConflictEvent event) {
    // 1. Save day-off info
    saveDayOff(day, employeeId, originalDate);
    
    // 2. Recalculate vacations (only if duration diff != 0)
    if (day.getDiff() != 0) {
        vacationCalendarUpdateService.recalculateVacations(day, List.of(employeeId), officeId);
    }
    
    // 3. Send notification based on type
    if (day.getDiff() == 0) {
        // Half-working day intersection
        notificationHelper.onCalendarUpdateAddedIntersectedHalfWorkingDay(...);
    } else {
        // Full day-off intersection
        notificationHelper.onCalendarUpdateAddedIntersectedDayOff(...);
    }
}
```

Two notification types based on `diff`: half-working day (duration change) vs full day-off (day added/removed).

### EmployeeDayOffAutoDeleteToCalendarUpdateHelper
For employee-level calendar updates (e.g., employee changes office):

```java
public void update(long employeeId, int year) {
    List<EmployeeDayOffRequestEntity> dayOffs = getEmployeeDayOffs(employeeId, year);
    dayOffs.forEach(dayOff -> {
        dayOff.setStatus(DELETED_FROM_CALENDAR);
        employeeDayOffRequestRepository.save(dayOff);
        createTimeline(dayOff);  // TimelineEventType.EMPLOYEE_DAY_OFF_DELETED_FROM_CALENDAR
    });
    employeeDayOffRepository.deleteByEmployeeAndYear(employeeId, year);
    notificationHelper.notifyAutoDeleteCalendarUpdateToEmployee(employee, year);
}
```

Only affects NEW and APPROVED day-offs. MAX_PAGE_SIZE=100 for query.

## 9. Optional Approval Service

### Create with constraints
```java
public EmployeeDayOffOptionalApproverBO create(EmployeeDayOffApproverCreateRequestBO requestBO) {
    checkConstraints(requestBO);  // 4 validation checks
    validateAccess(requestBO.getDayOffId());  // Access check
    // ... create with ASKED status
}
```

### Constraint checks (4 rules):
1. Day-off must exist → `NotFoundException`
2. Can't add day-off creator as optional approver → `ValidationException("Day off request creator can't be added...")`
3. Can't add main approver as optional → `ValidationException("Manager already exists as approver")`
4. Can't add same person twice → `AlreadyExistsException("Manager already added")`

### Access validation
```java
private void validateAccess(Long dayOffId) {
    // Allowed: day-off owner, approver, OR employee's manager
    if (!current.equals(employee) && !current.equals(approver) && !current.equals(manager))
        throw new EmployeeDayOffSecurityException();
}
```

### Status update (optional approver response)
```java
public EmployeeDayOffOptionalApproverBO updateStatusOfOptionalApproval(Long id, requestBO) {
    // Only the optional approver themselves can update their status
    if (!current.getId().equals(approval.getEmployeeId()))
        throw new EmployeeDayOffSecurityException();
    approval.setStatusType(EmployeeDayOffApproveStatusType.valueOf(requestBO.getStatus().name()));
}
```

### Approver change cascade
```java
public void deleteNewAndAddPreviousDayOffApproverToOptionalApproval(
        Long dayOffId, Long newApprover, Long previousApprover) {
    deleteAll(dayOffId, Set.of(newApprover));  // Remove new approver from optional list
    // Add previous approver to optional list with ASKED status
}
```

## 10. Event System

7 domain events + 8 event listeners:
- `EmployeeDayOffCreatedEvent` → notification to approver
- `EmployeeDayOffStatusChangedEvent` → notification on approve/reject/delete
- `EmployeeDayOffDateChangedEvent` → notification on date change
- `EmployeeDayOffApproverChangedEvent` → notification + cascade approver swap
- `EmployeeDayOffOptionalApproverAddedEvent` → notification to optional approver
- `EmployeeDayOffDeletedFromCalendarEvent` → batch notification on calendar removal
- `EmployeeDayOffRejectedBySystemEvent` → notification on system rejection

## 11. Error Codes Summary

| Error Code | Trigger |
|------------|---------|
| `exception.employee.dayOff.no.permission` | EmployeeDayOffSecurityException — access denied |
| `exception.day.off.crossing.vacation` | DayOffCrossingVacationException — day-off crosses vacation |
| `validation.EmployeeDayOffPublicDateExists.message` | Duplicate request for same public date |
| `validation.PublicDateNotFoundInCalendar.message` | Date not in office/employee calendar |

## 12. Design Issues and Test Implications

1. **EDIT_APPROVER unconditional**: Approver gets EDIT_APPROVER even on DELETED/DELETED_FROM_CALENDAR day-offs. Test: change approver on deleted day-off.
2. **EDIT unconditional for owner**: Owner can PATCH a deleted day-off. Test: patch personal date on deleted/rejected day-off.
3. **No CANCEL permission**: Unlike vacation, day-off has no separate CANCEL action. Delete is the only way to cancel.
4. **Missing @NotNull on DTO fields**: publicDate, personalDate, duration, reason — all optional. Test: create with all nulls.
5. **Null return from findApprovedByEmployeeAndDate**: Returns null instead of empty list. Consumers may NPE.
6. **Shared authorities with vacation**: VACATIONS_VIEW/CREATE/EDIT/APPROVE/DELETE control both vacation and day-off access.
7. **Optional approver controller uses VACATIONS_VIEW for writes**: POST/PATCH/DELETE on optional approvers only needs view permission.
8. **No @Transactional on approve/reject/delete**: Uses `transactionActions.performInTransaction()` wrapper instead.
9. **PAGE_SIZE=100 hard limit in auto-delete helper**: Employees with >100 day-offs per year won't be fully processed.

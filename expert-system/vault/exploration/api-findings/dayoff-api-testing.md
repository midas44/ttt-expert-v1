---
type: exploration
tags:
  - api-testing
  - day-off
  - bugs
  - timemachine
  - priority-1
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[day-off-service-implementation]]'
  - '[[frontend-day-off-module]]'
branch: release/2.1
---
# Day-Off API Exploratory Testing

## Environment & Context
- **Env**: timemachine (clock: 2026-03-13)
- **User**: pvaynmaster (Pavel Weinmeister) — roles: PROJECT, EMPLOYEE, OFFICE, DEPARTMENT_MANAGER
- **Approver for**: 13 employees' day-off requests (ypetrova, pbelova, egalkina, esizikov, vstrakhov, atushov)
- **Own approver**: self (CPO self-approval pattern) with ilnitsky as optional approver

## Full Lifecycle Verified

| Step | Action | Result |
|------|--------|--------|
| CREATE | POST /v1/employee-dayOff | NEW, auto-assigned approver=self (CPO), optional=ilnitsky |
| EDIT | PATCH /{id} personalDate change | Accepted, optional approvers stay ASKED |
| APPROVE (self) | PUT /approve/{id} | APPROVED, self-approval works |
| REJECT (approved) | PUT /reject/{id} on APPROVED | REJECTED (status only, ledger not undone) |
| RE-APPROVE | PUT /approve/{id} on REJECTED | APPROVED again |
| DELETE (approved) | DELETE /{id} on APPROVED | DELETED (allowed: personalDate in future) |
| APPROVE (cross) | PUT /approve/{id} on another employee | APPROVED (2976, ypetrova) |
| REJECT (cross) | PUT /reject/{id} | REJECTED back |
| CHANGE APPROVER | PUT /change-approver/{id}/{login} | Old approver → optional, new approver assigned |
| DUPLICATE CREATE | POST same publicDate | Upsert — shadows original record with new ID |

## Bugs Found (7)

### HIGH
1. **NPE on findAll without type**: GET /v1/employee-dayOff with no `type` → NPE at EmployeeDayOffSearchServiceImpl.java:134 (ordinal() on null EmployeeDayOffTypeFilter)
2. **NPE on list endpoint**: GET /v1/employee-dayOff/list → NPE in Caffeine cache computeIfAbsent at InternalEmployeeService.java:160 (null key passed to cache)

### MEDIUM
3. **No duplicate prevention**: POST with existing publicDate creates new record via upsert, silently replacing previous. Delete of new record restores original (shadow pattern, not destructive), but inconsistent IDs.
4. **Past personalDate accepted**: PATCH /{id} with personalDate=2026-02-01 (past) accepted on 2026-03-13. No date validation.
5. **Weekend personalDate accepted**: POST with personalDate=2026-06-13 (Saturday) creates request. No working-day validation.
6. **Ledger not reverted on reject**: APPROVE writes 2 ledger entries + recalculates vacation. REJECT only changes status — ledger entries remain orphaned. Repeated approve/reject cycles compound phantom entries.

### LOW
7. **APPROVER search over-includes**: type=APPROVER returns 484 results including requests where user is department manager or optional approver, not just primary approver. 13 of 18 NEW results had pvaynmaster as actual approver.

## Key Observations

**Vacation balance unaffected by day-offs**: Balance stayed at 29.0 through approve/reject cycle. Credit (+1 for working holiday) and debit (-1 for taking compensatory day) cancel out in vacation day calculation.

**Self-approval (CPO pattern)**: Users with PROJECT role get self-assigned as approver. Manager (ilnitsky) becomes optional approver with ASKED status. This enables self-approval without any external validation.

**Type filters available**: MY, ALL, APPROVER, OPTIONAL_APPROVER, RELATED, DELEGATED, DELEGATED_TO_ME, MY_DEPARTMENT, ON_PAID. Only MY and APPROVER were tested with type=MY also returning calendar-based entries (no status, no personalDate).

**Upsert shadow pattern**: Creating duplicate for existing publicDate produces new ID shadowing old. Deleting the shadow restores original. This is by-design (onDuplicateKeyUpdate) but confusing.

**Residual data impact**: ID 5486 (phantom ledger entry from approve/delete cycle), 2976 (ypetrova REJECTED), 3003 (approver changed to ilnitsky).

## DTOs Documented
- **Create**: `{publicDate, originalDate, personalDate, duration, reason}` — publicDate is the holiday
- **Edit**: `{personalDate}` — only personalDate changeable
- **Response**: Full EmployeeDayOffDTO with employee, approver, manager, optionalApprovers, status

Related: [[day-off-service-implementation]], [[frontend-day-off-module]], [[vacation-service-implementation]], [[report-crud-api-testing]]

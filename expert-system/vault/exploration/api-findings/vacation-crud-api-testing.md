---
type: exploration
tags:
  - api-testing
  - vacation
  - crud
  - bugs
created: '2026-03-12'
updated: '2026-03-12'
status: active
branch: release/2.1
related:
  - '[[architecture/api-surface]]'
  - '[[modules/vacation-service-implementation]]'
---
# Vacation CRUD API Testing

## Environment
Timemachine (ttt-timemachine.noveogroup.com), clock at 2026-03-13T04:56 (UTC+7), user: pvaynmaster (roles: PROJECT, EMPLOYEE, OFFICE, DEPARTMENT_MANAGER).

## CRUD Flow Verified

| Step | Endpoint | Method | Result |
|------|----------|--------|--------|
| Create | /v1/vacations | POST | ✓ NEW, auto-assigns approver |
| Read | /v1/vacations/{id} | GET | ✓ Full vacation DTO with permissions |
| Approve | /v1/vacations/approve/{id} | PUT | ✓ NEW→APPROVED, self-approval works |
| Reject | /v1/vacations/reject/{id} | PUT | ✓ NEW→REJECTED |
| Cancel | /v1/vacations/cancel/{id} | PUT | ✓ APPROVED→CANCELED |
| Pay | /v1/vacations/pay/{id} | PUT | ✓ APPROVED→PAID (terminal state) |
| Delete | /v1/vacations/{id} | DELETE | ✓ CANCELED/REJECTED OK, PAID 403 |
| Pass | /v1/vacations/pass/{id} | PUT | ✓ Changes approver |
| List v2 | /v2/availability-schedule | GET | ✓ With all required params |

## Bugs Found (6 new)

1. **NPE: v1/v2 availability-schedule missing pagination** — Both endpoints throw `NullPointerException` at `PageableRequestDTOToBOConverter.java:33-34` when `page` or `pageSize` params are null. No default values. (HIGH)

2. **NPE: vacation create with null paymentMonth** — `VacationAvailablePaidDaysCalculatorImpl.java:73` — `paymentDate.getYear()` NPE during validation when `paymentMonth` is omitted. Field documented as optional but effectively required. (HIGH)

3. **NPE: vacation create with null optionalApprovers** — `VacationServiceImpl.java:155` — `getOptionalApprovers().add()` NPE when list is null. Service tries to add manager to list without null check. (HIGH)

4. **Self-approval allowed** — DEPARTMENT_MANAGER can create and approve their own vacation. Approver auto-assigned to self. Possible business logic gap. (MEDIUM)

5. **Re-approval after rejection** — REJECTED vacations still show APPROVE in permissions. Can be re-approved without edit. (LOW — may be intentional)

6. **v2 sort params undocumented** — Sort format is `[+-]fieldname` with valid fields `[login, russianName, latinName]` only — not discoverable from API docs. (LOW)

## Create Request Structure

Required fields: `login`, `startDate`, `endDate`, `paymentType` (REGULAR/ADMINISTRATIVE), `paymentMonth`, `optionalApprovers` (even if empty []), `notifyAlso` (even if empty []).

Optional: `comment`.

## Behavioral Observations

- Auto-approver assignment: DEPARTMENT_MANAGER → self; otherwise → senior manager
- Senior manager auto-added as optional approver (status: ASKED)
- `advanceVacation: true` on office enables advance vacation days
- Available days updated atomically on create/delete (34→29 after 5-day create)
- Permissions field dynamically changes based on status and user role
- PAID vacation has empty permissions (fully immutable)

## Related
- [[architecture/api-surface]] — 79 vacation API endpoints
- [[modules/vacation-service-implementation]] — Backend implementation
- [[patterns/multi-approver-workflow]] — Approval model

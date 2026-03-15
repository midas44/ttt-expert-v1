---
type: analysis
tags:
  - vacation
  - business-rules
  - reference
  - phase-b-prep
  - priority-1
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[patterns/vacation-day-calculation]]'
  - '[[modules/vacation-service-implementation]]'
  - '[[patterns/multi-approver-workflow]]'
  - '[[analysis/role-permission-matrix]]'
  - '[[analysis/absence-data-model]]'
branch: release/2.1
---
# Vacation Business Rules Reference

Structured compilation of all vacation business rules from code, requirements, DB analysis, and live testing. Organized for Phase B test case generation.

## 1. Two Calculation Modes

Office-level setting `advanceVacation` (from CompanyStaff) drives fundamentally different behavior.

| Rule | AV=false (Russia) | AV=true (Cyprus/Germany) |
|---|---|---|
| Available days | Monthly accrual formula | Full year immediately |
| Negative balance | Never (display 0) | Allowed for current year |
| Over/undertime impact | None | Adjusts balance monthly |
| Insufficient days | Red error, block submit | Error 11.4 "Insufficient days" |
| Payment month display | "X of Y" form | No "X of Y" display |
| Manual correction | Cannot go negative | Can go negative |
| FIFO consumption | Yes | Yes |
| Norm deviation | None | BOTH type → fractional days |

**Formulas:**
- AV=false: `available = (month × norm/12) + yearRemainder + priorYears − norm + futureDays + editedDays`
- AV=true: `available = currentYearDays + pastYearDays + futureDays + editedDays`
- Norm deviation (AV=true): `available = norm + deviation − consumed`

## 2. Status State Machine

```
NEW → APPROVED (main approver approves)
NEW → REJECTED (main approver rejects)
NEW → CANCELED (employee cancels)
NEW → DELETED (employee deletes)
REJECTED → APPROVED (re-approval without edit — confirmed possible)
APPROVED → NEW (employee edits dates — resets status)
APPROVED → CANCELED (employee cancels)
APPROVED → REJECTED (approver rejects)
APPROVED → PAID (accountant pays — terminal)
CANCELED → NEW (employee re-opens)
PAID → terminal (no transitions out)
DELETED → terminal (soft delete)
```

**Live distribution**: PAID 94.3%, DELETED 3.2%, APPROVED 1.5%, NEW 0.6%, REJECTED 0.4%

## 3. Approval Workflow

**Auto-assignment on creation:**
- CPO (chief) → self-approval + manager as optional approver
- Regular employee → manager as primary approver
- No manager → self-approval
- DEPARTMENT_MANAGER → self-approval (confirmed in live testing)

**Two-tier model:**
- Primary approver: single, stored on `vacation.approver`. Their action drives state changes.
- Optional approvers: `vacation_approval` table. Statuses: ASKED → APPROVED/REJECTED. **Not required** for vacation to advance.
- Notify-also: `vacation_notify_also` table. `required=true` → acts as additional mandatory approver.

**Reassignment:** `changeApprover()` — old becomes optional (ASKED), new becomes primary. 21% of vacations reassigned.

**State resets:** Editing dates resets all optional approvals back to ASKED.

## 4. FIFO Day Consumption

Days consumed from **earliest year first**. Cross-year splits tracked in `vacation_days_distribution` (vacation_id + year → days).

**On cancel/reject/edit:** Days returned to pool, redistributed among remaining NEW/APPROVED vacations using FIFO.

**Recalculation service:** Returns ALL regular+exact days to balance, then re-distributes. Insufficient days → auto-converts later requests to ADMINISTRATIVE.

**Sprint 15 (#3347):** Smart reallocation — validates both current and future-year requests, reallocates without converting to admin.

## 5. Payment Flow

**Trigger:** Accountant pays individual vacation or cron auto-pays expired (>2 months old approved).

**Validation:** Status must be APPROVED, period must be EXACT, `regularDaysPayed + administrativeDaysPayed` must equal `vacation.getDays()`.

**Key behavior:** Days deducted at **approval** time, not payment. Payment is purely status transition APPROVED → PAID.

**Payment types:** REGULAR (paid leave), ADMINISTRATIVE (unpaid / за свой счёт). Mixed possible.

**Auto-pay cron:** `payExpiredApproved()` runs daily, finds APPROVED >2 months old, auto-distributes by type.

**Known bugs:** No type alignment validation (admin vacation paid with regular split accepted); 2-hour orphan window in status update job; DB/API day-type transposition.

## 6. Vacation-Calendar Interaction

**Trigger:** Day-off deletion/transfer or production calendar change that increases vacation days.

**Phase 1 (immediate):** Check if annual days exceeded → convert to ADMINISTRATIVE.

**Phase 2 (10 min delay):** If annual OK, check accrued days for affected payment month and all later months → convert if insufficient, send notification.

## 7. Create Request Validations

| Validation | AV=false | AV=true | Both |
|---|---|---|---|
| Employment +3 months | ✓ (regular only) | ✓ | |
| Min 1 day | | | ✓ |
| Available days ≥ requested | Red error, block | Error 11.4 | |
| Future request impact | Orange warning | Orange warning | |
| Payment month in range | 2mo before → end month | 2mo before → end month | |
| Payment month not closed | ✓ | ✓ | |
| `paymentMonth` required | ✓ (NPE if null) | ✓ (NPE if null) | |
| `optionalApprovers` not null | | | ✓ (NPE if null) |
| Overlapping vacation check | | | ✓ |

## 8. Day Correction Rules

- **AV=false:** Prohibit negative values in inline editing
- **AV=true:** Allow negative values
- Causes: underwork, day-off moves, admin adding work days, manual edits
- Corrections reflected in Event Feed
- **Bug found:** `pastPeriodsAvailableDays` drift — DB accepts edit but recalculation may not honor AV=false negative prohibition

## 9. Permissions (Who Can Do What)

| Action | Roles |
|---|---|
| View own vacations | EMP (all logged-in) |
| View approval requests | PM, DM, TL, ADM, VALL |
| Create vacation | EMP (non-readOnly) |
| Approve/Reject | Primary approver (PM/DM/ADM role) |
| Change approver | Primary approver |
| Pay vacation | ACC, CACC, ADM |
| Edit vacation days | ACC, CACC, ADM, VALL |
| View vacation days | ACC, CACC, ADM, VALL |
| View payments | ACC, CACC, ADM, VALL |
| View employees | DM |
| Cancel | Employee (own, pre-PAID) |
| Delete | Employee (own, CANCELED/REJECTED) |

## 10. Known Bugs (from live testing)

| # | Description | Severity | Source |
|---|---|---|---|
| 1 | NPE on null pagination (v1/v2 availability-schedule) | HIGH | API testing |
| 2 | NPE on null paymentMonth | HIGH | API testing |
| 3 | NPE on null optionalApprovers | HIGH | API testing |
| 4 | Self-approval for DM | MEDIUM | API testing |
| 5 | Re-approval after rejection without edit | LOW | API testing |
| 6 | No payment type alignment validation | MEDIUM | Payment testing |
| 7 | 2-hour orphan window in status update job | HIGH | Payment testing |
| 8 | DB/API day-type transposition | MEDIUM | Payment testing |
| 9 | -60 day cluster (batch recalculation bug) | HIGH | DB analysis |
| 10 | pastPeriodsAvailableDays drift | MEDIUM | Day correction |
| 11 | FIFO validation gap at creation | MEDIUM | Code analysis |
| 12 | Orphaned approvals on deletion (no cascade) | LOW | DB analysis |

## Related
- [[patterns/vacation-day-calculation]] — formula details
- [[modules/vacation-service-implementation]] — backend implementation
- [[patterns/multi-approver-workflow]] — approval pattern
- [[analysis/absence-data-model]] — data model
- [[analysis/role-permission-matrix]] — access control
- [[exploration/api-findings/vacation-crud-api-testing]] — CRUD test results
- [[exploration/api-findings/payment-flow-live-testing]] — payment test results
- [[investigations/vacation-day-calculation-verification]] — formula verification
- [[investigations/vacation-approval-workflow-e2e]] — approval trace
- [[external/requirements/REQ-vacations-master]] — master requirements
- [[external/requirements/REQ-accrued-vacation-days]] — AV=false spec
- [[external/requirements/REQ-advance-vacation]] — AV=true spec
- [[external/requirements/REQ-vacation-day-corrections]] — correction rules

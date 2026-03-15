---
type: investigation
tags:
  - vacation
  - approval
  - workflow
  - end-to-end
  - bugs
  - database
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[modules/vacation-service]]'
  - '[[modules/vacation-service-implementation]]'
  - '[[patterns/multi-approver-workflow]]'
  - '[[debt/vacation-service-debt]]'
branch: release/2.1
---
# Vacation Approval Workflow — End-to-End Trace

Traced via database queries on timemachine. 14,195 total vacations, 53K+ timeline events.

## State Machine (from live data)

```
NEW → APPROVED (main approver) → PAID (batch per office) → end
NEW → REJECTED
APPROVED → DELETED (cancel)
Any pre-PAID → DELETED
DELETED → RECOVERED (rare, 20 events)
```

**Status distribution**: PAID 94.3% (13,385) | DELETED 3.2% (456) | APPROVED 1.5% (213) | NEW 0.6% (81) | REJECTED 0.4% (60)

## Two-Tier Approval Model

**Main approver** (stored in `vacation.approver`): Single person. Their approval transitions NEW → APPROVED. Typically the employee's manager.

**Optional approvers** (in `vacation_approval` table): Multiple per vacation. Statuses: ASKED, APPROVED, REJECTED. **Not required** for vacation to advance — 9,679 ASKED-but-never-responded approvals on PAID vacations prove this. 94 optional approvals exist on NEW-status vacations that the main approver hasn't acted on.

21% of vacations get approver reassignment (2,498 APPROVER_CHANGED events).

## Payment Flow

Batch operation per office via `vacation_status_updates` table. Creates `vacation_payment` records with regular_days + administrative_days. Most recent batch: 2026-03-02, processing 20 offices in rapid succession.

## Bug Verification Results

| Bug | Verdict | Evidence |
|-----|---------|----------|
| #1: PayVacationServiceImpl null paymentDate on year-boundary | **NOT CONFIRMED** | All 15 cross-year vacations have non-null payment_date |
| #2: VacationRecalculationServiceImpl no locking | **INCONCLUSIVE** | No shedlock entry for recalculation; 26 REVERSE events could indicate race conditions |
| #3: Advance vacation allows negative days | **CONFIRMED** | 20 employee-year records with negative balances. 8 employees at exactly -60.000 (batch bug) |
| #4: FIFO edge case with office transfer | **INCONCLUSIVE** | No case found with different entitlement rates + cross-year vacation |

## Key Anomalies

1. **-60 day cluster**: 8 employees with identical -60.000 (2025) and -19.000 (2024) balances — batch recalculation bug
2. **Orphaned approvals**: 414 approval records on DELETED vacations — deletion doesn't cascade
3. **PAID with REJECTED optional approver**: 2 cases — consistent with model but confusing
4. **advance_vacation column**: NULL everywhere in `office_annual_leave`, not present on vacation table — feature controlled elsewhere

See also: [[modules/vacation-service]], [[modules/vacation-service-implementation]], [[patterns/multi-approver-workflow]], [[patterns/vacation-day-calculation]], [[debt/vacation-service-debt]]

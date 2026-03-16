---
type: investigation
tags:
  - cs-settings
  - office
  - unimplemented
  - vacation
  - sick-leave
  - contractor
created: '2026-03-15'
updated: '2026-03-15'
status: active
related:
  - '[[vacation-service]]'
  - '[[patterns/vacation-day-calculation]]'
  - '[[external/tickets/sprint-16-overview]]'
branch: release/2.1
---
# CS Office Settings — 3 Unimplemented Features (#3026)

## Summary

GitLab ticket #3026 identifies 3 CompanyStaff (CS) salary office settings that exist in the CS data model but are **NOT implemented** in TTT's vacation service. The fields are synced from CS but ignored during processing.

## CSSalaryOfficeVacationData Model

From `CSSalaryOfficeVacationData.java`:
```java
private Integer year;
private Integer days;              // ← USED: synced to office_annual_leave
private Integer firstVacation;     // ← NOT USED
private Boolean advanceVacation;   // ← USED: synced to office.advance_vacation
private CSSalaryOfficeNormDeviationType overworkUnderwork; // ← USED
private Integer burnOff;           // ← NOT USED
private Boolean sickLeave;         // ← NOT USED
```

**Sync code** (`CSSalaryOfficeSynchronizer.java`):
- Lines 130-132: Only `advanceVacation` and `overworkUnderwork` are synced to the `office` entity
- Line 193: `days` synced to `office_annual_leave`
- `firstVacation`, `burnOff`, `sickLeave` are read from CS but never written or referenced

## 1. firstVacation — Months Before First Vacation

**CS field**: `CSSalaryOfficeVacationData.firstVacation` (Integer)
**Intended behavior**: Number of months an employee must work before being eligible for their first vacation
**Current TTT behavior**: Hardcoded to 3 months (per ticket #3026)
**DB column**: Does NOT exist in `ttt_vacation.office` table

**Impact**: All offices enforce a uniform 3-month waiting period regardless of the CS-configured value. Offices in different jurisdictions (e.g., Cyprus vs Russia) may have different legal requirements.

**Code path (where it should be used)**: Likely in `VacationAvailabilityChecker` or `VacationCreationValidator` — need to find the actual hardcoded 3.

## 2. burnOff — Vacation Day Expiration

**CS field**: `CSSalaryOfficeVacationData.burnOff` (Integer)
**Intended behavior**: Number of months/years after which unused vacation days expire
**Current TTT behavior**: Vacation days NEVER expire — they accumulate indefinitely across years
**DB column**: Does NOT exist in `ttt_vacation.office` table

**Evidence from DB**: `employee_vacation.available_vacation_days` can carry over across years with no expiration logic.

**Impact**: Employees in jurisdictions where vacation days have a legal expiration period (e.g., must be used within 18 months in some EU countries) have no enforcement.

## 3. sickLeave — Include Sick Leaves for Contractors

**CS field**: `CSSalaryOfficeVacationData.sickLeave` (Boolean)
**Intended behavior**: Whether contractors in this office can create/use sick leaves
**Current TTT behavior**: The boolean is defined in the CS model but NOT used in vacation service logic
**DB column**: Does NOT exist in `ttt_vacation.office` table

**Related**: `syncSickLeaveNotificationReceivers()` does sync notification recipients from CS, but the `sickLeave` boolean that controls contractor eligibility is ignored.

## Office DB Schema

`ttt_vacation.office` columns: `id`, `name`, `norm_deviation_type`, `last_sync_time`, `name_latin`, `active`, `advance_vacation`

No columns for `first_vacation`, `burn_off`, or `sick_leave`.

## Test Implications

These settings are currently NOT IMPLEMENTED, so test cases should cover:
1. **Current hardcoded behavior** — verify the 3-month first vacation restriction works as expected
2. **No expiration** — verify days carry over indefinitely across years
3. **Contractor sick leave** — verify contractor sick leave behavior with/without the setting
4. **Future implementation** — placeholder test cases for when these settings are implemented

## References

- GitLab ticket: #3026
- [[vacation-service]] — main vacation service
- [[patterns/vacation-day-calculation]] — day calculation strategies
- [[external/tickets/sprint-16-overview]] — Sprint 16 context

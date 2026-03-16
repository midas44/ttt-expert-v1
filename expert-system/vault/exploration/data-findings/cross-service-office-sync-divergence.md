---
type: exploration
tags: [data-integrity, cross-service, employee, office, sync, bug, high-severity]
created: 2026-03-15
updated: 2026-03-15
status: active
related:
  - "[[exploration/data-findings/db-data-overview-tm]]"
  - "[[architecture/cross-service-integration]]"
  - "[[modules/vacation-service-implementation]]"
  - "[[modules/ttt-service]]"
  - "[[external/tickets/sprint-16-preview]]"
branch: release/2.1
---

# Cross-Service Employee Office Sync Divergence

## Summary

**62% of employees (736/1190) have different salary office assignments** between `ttt_backend.employee.salary_office` and `ttt_vacation.employee.office_id`. Confirmed on ALL three environments (qa-1, timemachine, stage) with identical numbers.

## Evidence

### Mismatch Statistics (all envs identical)
| Metric | Value |
|--------|-------|
| Total employees (joined) | 1190 |
| Mismatched office | **736 (62%)** |
| Matched office | 454 (38%) |

### Mismatch Categories
| Type | Count | Description |
|------|-------|-------------|
| Both real offices, different | **628** | Two legitimate offices disagree |
| Backend = "Не указано" (id=9) | 99 | Backend defaulted, vacation correct |
| Vacation = "Не указано" (id=9) | 9 | Vacation defaulted, backend correct |

### Top Mismatch Patterns (office ID → office ID, count)
```
Backend → Vacation    Count  Offices
2 → 4                 83     Сатурн → Юпитер
9 → 2                 66     Не указано → Сатурн
4 → 2                 58     Юпитер → Сатурн
4 → 10                55     Юпитер → Венера
10 → 4                52     Венера → Юпитер
2 → 10                52     Сатурн → Венера
10 → 2                41     Венера → Сатурн
4 → 27                20     Юпитер → Венера (РФ)
27 → 10               20     Венера (РФ) → Венера
```

### Year Records Consistent Within Vacation Service
`ttt_vacation.employee_office[year].office` matches `ttt_vacation.employee.office_id` — the divergence is strictly between services, not within the vacation service.

## Root Cause

### Independent CS Sync Paths
Both services sync employee data from CompanyStaff (CS) independently:

1. **ttt_backend** — `ttt/service/service-impl/.../periodic/cs/synchronization/v2/employee/CSEmployeeSynchronizer.java`
   - Sets `employee.setSalaryOfficeId(salaryOfficeId)` from CS API
   
2. **ttt_vacation** — `vacation/service/service-impl/.../periodical/cs/synchronization/v2/employee/CSEmployeeSynchronizer.java`
   - Sets `employee.setOfficeId(officeFactory.getOrCreate(accountingData.getSalaryOfficeId()))`
   - Also triggers `EmployeeOfficeChangedEvent` → updates `employee_office[year]` records

### No Cross-Service Reconciliation
- No shared event bus between services
- No data validation comparing the two tables
- No audit mechanism detecting divergence
- Sync timing differences compound over time

### Conditional Year Record Update Bug
In `EmployeeOfficeChangedProcessor.createOrUpdate()`:
```java
if (!isSalaryOfficesAreEqual(oldEmployeeOffice, salaryOfficeId)) {
    if (isCalendarsAreEqual(oldEmployeeOffice, salaryOfficeId, year)) {
        updateOffice(employeeOffice.get(), salaryOfficeId);
    } else if (nextYear.equals(year) || isTodayFirstDayOfYear()) {
        updateOffice(employeeOffice.get(), salaryOfficeId);
        employeeDayOffUpdateHelper.update(employeeId, year);
    }
    // ELSE: NOT UPDATED if calendars differ AND it's not next year AND not Jan 1
}
```
Mid-year office changes with different calendars silently skip the year record update.

## Impact Assessment

### HIGH — Vacation Day Calculations
- `ttt_vacation` uses `employee.office_id` → `office_annual_leave.days` for accrual
- `ttt_backend` uses `salary_office` → may show different office in reports/statistics
- Employee sees office A's norm in reports but gets office B's vacation days

### HIGH — Production Calendar Mismatch  
- Working hours norm in statistics uses backend office's calendar
- Vacation duration calculation uses vacation office's calendar
- Different offices may have different production calendars (Russian vs non-Russian)

### MEDIUM — Accounting Period Assignment
- Accountant manages periods per salary office
- If employee appears in wrong office, period open/close affects wrong group

### Related to #2876
Ticket #2876 explicitly documents this: "Data inconsistency: `salary_office` in `ttt_backend.employee` doesn't sync with `office_id` in `ttt_vacation.employee` after CS sync."

## Additional Code Gaps Found

### Null Office Handling
When CompanyStaff returns no accounting data, `salaryOfficeId` is set to NULL with no fallback:
```java
if (accountingData != null) {
    salaryOfficeId = officeFactory.getOrCreate(accountingData.getSalaryOfficeId());
} else {
    salaryOfficeId = null;
}
```

### Office Stubs With Empty Names
`SalaryOfficeFactory.getOrCreate()` creates new offices with empty name:
```java
newOffice.setName(StringUtils.EMPTY);  // Never backfilled
```

### No Termination Cleanup
Terminated employees retain office assignments in both services. No listener for deactivation events cleans up `employee_office` records.

## Test Implications

1. **Data integrity test cases** — verify office consistency between services after CS sync
2. **Office transfer scenarios** — test that mid-year office change propagates to both services
3. **Calendar norm accuracy** — verify statistics and vacation use consistent office data
4. **Accounting period assignment** — verify employee appears in correct office for period management
5. **Regression for #2876** — specific test for the event feed + calendar change bug

## Connections
- [[architecture/cross-service-integration]] — RabbitMQ messaging between services
- [[modules/vacation-service-implementation]] — vacation day calculation uses office_id
- [[modules/ttt-service]] — backend service uses salary_office for norms
- [[external/tickets/sprint-16-preview]] — #2876 documents this exact bug
- [[exploration/data-findings/db-data-overview-tm]] — database schema context

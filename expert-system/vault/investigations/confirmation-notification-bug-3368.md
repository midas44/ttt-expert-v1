---
type: investigation
tags: [confirmation, notification, reports, frontend, sprint-15, bug]
created: 2026-03-16
updated: 2026-03-16
status: active
related: ["[[modules/ttt-report-service-deep-dive]]", "[[modules/frontend-approve-module]]"]
branch: release/2.1
---

# Confirmation Notification Bug — #3368

## Summary
The "Confirmation > By Employee" tab did not show over/under report notifications, while "By Projects" did. Root cause: By Employee tab never called the statistics endpoint to get norm data.

## 4 MRs Merged (all frontend, release/2.1)

### !5118 (merged 2026-01-14, 2 files) — Initial Fix
- Added `setEmployeeStatistic` dispatch in `employeeTabSagas.ts`
- Fetches employee statistics via `sendRequestForEmployeeReportPeriod` + `fetchEmployeeReports`
- Computes `isCurrentMonth` flag
- Puts statistic data into Redux store

### !5132 (merged 2026-01-20, 7 files) — Norm Display Fix
- Added `norm` field to `TEmployeeStatistics` type
- Fixed `normForDate` fallback: `normForDate || norm` — uses general norm if date-specific norm unavailable
- Fixed employee name display fallback via `EmployeeDto.getEmployeeName()`
- Changed `updateEmployeesWeeksAndMonths` from `spawn` to `call` — ensures data refresh completes before proceeding
- Added null guard: `!employee || !employee?.login` prevents crashes on missing employee data
- After approve: passes `employee` to properly re-fetch data (not just refresh list)

### !5205 (merged 2026-02-04, 4 files) — Approve Period Fix
- **Critical fix**: Switched from `sendRequestForEmployeeReportPeriod` (per-employee report period) to `sendRequestForEmployeeApprovePeriod` (per-office approve period)
- Added `approvePeriod` to `TEmployeeStatistics` type and Redux flow
- Notification month now uses approve period start date instead of current month when `!isCurrentMonth`
- **Debug code left**: `console.log(approvePeriod)` at line ~122

### !5256 (merged 2026-02-17, 1 file) — OfficeId Resolution Fix
- Fixed officeId path: `(employee as any).officeId || (employee as any).office.id`
- Different employee DTO shapes have officeId at different paths
- Fallback prevents undefined officeId from breaking approve period fetch

## Sub-Bugs Found During QA (3)
1. **Approve button doesn't switch to next user** — after approving, notification didn't show `Monthly norm` and `Norm as of {date}`
2. **Approve month < current month**: By Employee shows wrong notification when employee's report month = current month
3. **Double overwork**: Employee has overwork in both past and current month — By Employee showed current month notification (incorrect), By Projects showed approve month (correct)

## Code Analysis: employeeTabSagas.ts (256 lines)

### handleGetEmployeeWeekPeriods (core saga)
```typescript
// Fetches approve period for office
const approvePeriod = yield call(sendRequestForEmployeeApprovePeriod, officeId);
console.log(approvePeriod); // DEBUG LEFT IN PRODUCTION

// Calculates date range
const startDate = moment(approvePeriod.periodStart).startOf('month');
const endDate = isCurrentMonth ? moment() : moment(approvePeriod.periodStart).endOf('month');

// Fetches employee statistics
const employeeStatistic = yield call(fetchEmployeeReports, ...);
yield put(setEmployeeStatistic(employeeStatistic));
```

### Key Logic: isCurrentMonth determination
- `isCurrentMonth = moment().isSame(approvePeriod.periodStart, 'month')`
- If approve month IS current month → uses current date as endDate
- If approve month is in the past → uses end of approve month as endDate
- This affects which notification the user sees (current vs. past month)

### Stale-check mechanism
- `currentUser.login !== executorLogin` → returns early if user changed while saga was running
- Prevents race conditions during rapid employee switching

## Design Issues
1. `console.log(approvePeriod)` left in production code
2. Multiple `// TODO: handle request error` comments (lines 82, 185, 242)
3. `(employee as any)` type casting — no proper TypeScript typing for employee DTO
4. officeId at two different paths indicates inconsistent DTO shapes between tabs

## Test Implications
- Must verify By Employee and By Projects tabs show SAME notification
- Test with approve month = current month AND approve month < current month
- Test with employee having overwork in multiple months
- Test approve button → next user transition → notification refresh
- Test normForDate fallback when date-specific norm is null
- Test employee with officeId at `office.id` path (not direct `officeId`)

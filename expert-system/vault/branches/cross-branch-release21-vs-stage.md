---
type: analysis
tags: [branches, sprint-15, release-comparison, cross-branch]
created: 2026-03-14
updated: 2026-03-14
status: active
related: ["[[architecture/system-overview]]", "[[planner-requirements]]", "[[confirmation-over-under-reporting]]", "[[vacation-day-correction-spec]]", "[[companystaff-integration]]", "[[admin-projects-deep-exploration]]"]
branch: release/2.1 vs stage
---

# Cross-Branch Comparison: release/2.1 vs stage

**Scope:** 193 commits, 656 files changed (+25464/-4915 lines). Covers Sprint 14-15 development not yet in production.

## Major New Features

### 1. Advance Vacation — CS Integration (#3092, 11 commits)
New `AdvanceCalculationStrategy` — employees can take full year vacation norm at year start without monthly accrual. Formula: `currentYearDays + pastYearDays + futureDays + editedVacationDays`. New `JavaMigrationExecutor` one-time data migration framework in vacation service.

### 2. Planner Close-by-Tag (#2724, 6 commits)
Full-stack feature: new `planner_close_tag` table (V2.1.27), entity, repository, service, validator, controller, DTOs, integration tests. When tracker ticket has matching tag, assignment auto-closes on Refresh/Load from tracker. Per-project tag configuration in [[admin-projects-deep-exploration|Project Settings popup]].

### 3. Auto-Reject Unconfirmed Hours (#2698, 8 commits)
Backend: auto-reject unconfirmed hours after approval period change. Notification banner SQL. Frontend banner on Confirmation page.

### 4. Over/Under Report Notification (#2932, 5 commits)
Frontend `OverReportNotificationByEmployeesController.tsx`. Show notification at Confirmation > By Employee when employee over/under-reported. Admin threshold settings (M%/L%). See [[confirmation-over-under-reporting]].

### 5. Statistics Performance (#3337, 8 commits)
Denormalize `reported_effort`, `month_norm`, `budget_norm` into `statistic_report` table (3 migrations). POST-based optimization. Monthly norm update after sick leave events.

### 6. Individual Work Period (#3353, 2 commits)
New `EmployeeWorkPeriod` entity + table (V1_59). Exclude periods before first/after last working day from individual norm calculation.

### 7. Feedback Surveys (#3340, 4 commits)
Integration with external pop-up survey system in TTT UI.

### 8. Approval Period Backdate Limit (#3350, 7 commits)
Restrict backdating approval period to max 1 month from previously set month.

## Bug Fixes (17 total)
- **Vacation:** #3361 (multi-year AV=True), #3357 (cross-year AV=False), #3355 (maternity balance), #3324 (admin vacations calendar), #3344 (Russian in EN events feed), #3204 (underwork recalculation), #3338 (calendar change conversion)
- **Confirmation/Planner:** #3368 (missing notification), #3334 (Planner hours cross-entry), #3386 (deleted tasks in Copy), #3308 (DnD order), #3266 (Planner not confirming), #3367 (auto-rejected edit)
- **Other:** #3313 (timestamps in availability chart), #3330 (Sunday week start), #3364 (Notification Employee field validation), #3150 (contractor spinner), #3205 (day-off approver UI), #3321 (rejection notification gap)

## DB Migrations (10 new)
**V2.1.25 (PM Tool):** 4 migrations — pm_sync_status, pm_tool_id rename, sync_failed_entity, indexes
**V2.1.26:** reported_effort+month_norm on statistic_report, statistics_view permission, budget_norm, pmt_id on project, java_migration table
**V2.1.27:** planner_close_tag table

## Feature Toggle Changes
- **Removed:** `CS_API_V2` (v1 support dropped per #3072)
- **Added:** `EMPLOYEE_PROJECT_INITIAL_SYNC` (disable initial sync per #3303)

## Infrastructure
- Node.js 18.17.0, dart-sass compatibility (#3343)
- Enhanced CI pipeline for pre-release (#3371, #3036)
- InnovationLab banner (#3392)
- Approve module Redux→TypeScript (#3055, 5 commits)

## Impact on Test Documentation
Most changed areas: **vacation** (118 files, +7581/-1067), **ttt** (193 files, +11400/-1081), **frontend** (258 files, +3166/-2678). High test case impact on: advance vacation rules, planner close-by-tag, auto-reject flow, over/under notification thresholds, approval backdate logic.

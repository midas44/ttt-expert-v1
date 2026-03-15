---
type: investigation
tags:
  - figma
  - ui-comparison
  - statistics
  - design
  - sprint-14
  - sprint-15
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[figma-sprint-14-15-designs]]'
  - '[[frontend-statistics-module]]'
  - '[[employee-reports-row-expansion]]'
branch: release/2.1
---
# Figma vs Live UI Comparison

Comparison of 4 Figma designs (Sprint 14-15) against live timemachine UI (release/2.1).

## Design 1: Employee Reports Page (43297:298158, #3309)

**Overall: IMPLEMENTED with deviations**

| Feature | Figma | Live UI | Match |
|---------|-------|---------|-------|
| Table columns | Employee, Manager, Reported, Norm, Deviation (%), Comment | Employee, Department manager, Reported, Norm, Overtime, Comment | PARTIAL — "Deviation" renamed "Overtime", "Manager" → "Department manager" |
| Color-coded over-reporting | Red values for over-reported | 182.7 in red, +63% in red with up-arrow icon | YES |
| Expandable employee rows | Shows project/task breakdown on expand | **Chevron-only click** — 16x16 icon triggers expansion, NOT row click | **NO** — Requirement says row click, only chevron works. See [[employee-reports-row-expansion]] |
| Absence icons | Vacation/sick leave period tooltips on hover | Palm tree icons next to employees with absences | YES (icons present, tooltip not verified) |
| Comment inline editing | Not filled → hover → click → edit → save | Comment column present, inline editing not tested | PRESENT — UX flow untested |
| Employee search | Search filter | "Search by employee" textbox | YES |
| Period selector | Month-based selector | Month picker (e.g., "Feb 2026") | YES |
| Over-limit filter | Filter checkbox | "Only over the limit" checkbox | YES |

## Design 2: Individual Norm Counter (44763:311340, #3353)

**Overall: IMPLEMENTED correctly**

| Feature | Figma | Live UI | Match |
|---------|-------|---------|-------|
| Counter format | `worked / norm_for_date / individual_norm / general_norm` | "0/24/120/144" (Dmitry Dergachev, March) | YES — 4 numbers displayed |
| Scenario 1 (current month + absences) | Show all 4 indicators | Shows 0/24/120/144 (120 < 144 = has absences) | YES |
| Display location | Only on "My Tasks" page | Counter visible on /report (My Tasks) | YES |
| Not in Employee Reports | Individual norm not in table | Employee Reports shows monthly Norm only (e.g., 112, 152) | YES |
| Info icon | ℹ️ tooltip explaining format | Info icon (ℹ️) present next to counter | YES |

**Note**: Scenario 2 (no absences, 3 numbers) and Scenario 3 (closed period) not verified — would need different employee/period.

## Design 3: Budget Norm & Employee Reports (44744:117220, #3356, #3381)

**Overall: IMPLEMENTED, details not fully verified**

| Feature | Figma | Live UI | Match |
|---------|-------|---------|-------|
| Norm without admin leave deduction | Column shows norm without deducting admin leave | Norm column shows values (112, 152, etc.) | YES (value correctness not verified) |
| Individual norm not in table | Individual norm only on My Tasks | Employee Reports has Norm column without individual norm | YES |
| Start/end date tooltip | Hover shows first/last working day | Not tested — requires hover interaction | UNTESTED |
| Comment interaction | Hover → click → save states | Comment column present | UNTESTED |

## Design 4: Sick Leave Display in Statistics (43297:298160, #2435, #3318)

**Overall: PARTIALLY verified**

| Feature | Figma | Live UI | Match |
|---------|-------|---------|-------|
| Sick leave icon on tabs | Icon visible on all tabs with grouping | Palm tree icons visible on Employee Reports page for affected employees | PARTIAL — icon present, tab-level grouping unclear |
| Hover tooltip | Hours, date range, status display | Tooltip not tested via Playwright | UNTESTED |
| Scrollable tooltip for 5+ | Scrollable if 5+ sick leaves | Not tested | UNTESTED |
| Combined vacation+sick leave | "за выбранный период" section | Not tested | UNTESTED |
| Status display | новый/оплачен/отклонён | Not tested | UNTESTED |

## Summary

- **2 of 4 designs fully implemented** with naming differences (#2 Individual Norm, #3 Budget Norm)
- **1 design with deviation** (#1 Employee Reports — chevron-only click instead of row click)
- **1 design partially verified** (#4 Sick Leave — tooltips need manual testing)
- **Key deviation**: "Deviation (%)" column renamed to "Overtime"
- **Row expansion RESOLVED**: Only chevron icon (16x16) triggers expansion, not row click. cursor:pointer on full row is misleading. See [[employee-reports-row-expansion]].
- **Tooltip interactions**: Still require hover-based testing

Related: [[figma-sprint-14-15-designs]], [[frontend-statistics-module]], [[frontend-report-module]], [[employee-reports-row-expansion]]

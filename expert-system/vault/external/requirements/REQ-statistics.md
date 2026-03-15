---
type: external
tags:
  - statistics
  - requirements
  - confluence
  - employee-reports
  - deviation
  - norm
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-confirmation]]'
  - '[[analysis/office-period-model]]'
branch: release/2.1
---
# Statistics Requirements (Статистика)

Confluence page 119244531, version 22 (heavily iterated). Main ticket: #3195. Also: #2435, #3309, #3381, #3353, #3356.

## Pages and Access
- Regular users: single "Statistics" page, no title
- ADMIN, CHIEF_ACCOUNTANT: "General Statistics" + "Employee Reports" (all employees)
- OFFICE_ACCOUNTANT: employees of their POs only
- DEPARTMENT_MANAGER: their department employees
- TechLead: their employees (possibly = DM since DM = CS.user.Employees > 0)

## General Statistics Page
Minor UI fixes: paddings, N-dash in date range, sick leave icon+tooltip (#2435).

## Employee Reports Page (#3195) — NEW
- **Search:** by first/last name (Latin+Cyrillic), login, wrong keyboard layout detection
- **Date picker:** default = last month open for confirmation in user's PO
- **Toggle:** "Only over-limit deviations" — filters by threshold

### Key Columns
- **Reported (Зарепорчено):** Sum of reported hours. Red ↑ over-report, purple ↓ under-report. Color threshold from TTT Parameters.
- **Norm (Норма) #3381:** Budget norm = individual norm + admin vacation hours. Display: `{individual} ({budget})` if has admin vacation, else just `{budget}`.
- **Deviation (Превышение):** `(Reported - budget_norm) / budget_norm * 100%`. Integer except (-1,+1) range → 1 decimal. Norm=0 AND reported>0 → "+N/A%" (sorts to top).
- **Comment (#3309):** Per employee per month-year. Inline edit.

### Edge Cases
- Fired employees: shown in last active month, hidden after
- TBD Sprint 15: #3353, #3356 — mid-month start/termination
- N/A% for zero-norm is special sort value

Links: [[REQ-confirmation]], [[analysis/office-period-model]], [[modules/ttt-service]]
Figma: nodes 41531-341639, 44767-69810, 44763-311340

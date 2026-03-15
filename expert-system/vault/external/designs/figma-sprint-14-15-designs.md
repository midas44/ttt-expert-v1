---
type: external
tags:
  - figma
  - design
  - statistics
  - sprint-14
  - sprint-15
  - sick-leave
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-statistics]]'
  - '[[sprint-14-15-overview]]'
  - '[[exploration/ui-flows/reporting-and-other-pages]]'
---
# Figma Design Specs: Sprint 14-15

Figma file: `H2aXBseq7Ui60zlh5vhyjy` (Noveo-TTT)

## Node 43297:298158 — Employee Reports Page (#3309)
**Page**: Statistics → Employee Reports ("Репорты сотрудников")

Design shows a table with columns: Employee, Manager, Reported, Norm, Deviation (%), Comment. Key features:
- Expandable employee rows showing project/task breakdown with individual hours
- Vacation/sick leave period tooltips on hover (showing date ranges, status, hours)
- Color-coded rows (green highlight for selected/focused)
- Comment field with inline editing: not filled → hover → click to edit → 1 line / 2+ lines → tab/click elsewhere to save
- Two variants shown: full table (with all columns) and simplified view

Related: [[REQ-statistics]], [[sprint-14-15-overview]]

## Node 44763:311340 — Individual Norm Calculation (#3353)
**Feature**: Hours counter display rules with individual norm

Detailed specification for the 4-number counter format: `worked / norm_for_date / individual_norm / general_norm` (e.g., "24/32/140/160").

Three display scenarios:
1. **Current month with vacation/sick leave** — show all 4 indicators: [1] worked hours, [2] norm for selected day accounting for vacation/sick leave, [3] individual norm (month norm minus vacation/sick leave hours), [4] general norm
2. **Current month, no absences** — hide individual norm [3], show only [1]/[2]/[4], with "norm on dd.mm.yyyy" label
3. **Closed/past period** — don't show "norm for selected day" [2]

**NEW #3353 rule**: If employee has vacation, sick leave, or days when not yet/no longer employed → display individual norm for both the month and the selected day.

Notes:
- a) If day-off transfer is in progress, use confirmed day-offs only (#2672)
- b) If employee changed production calendar (ПК) mid-year (#3189), use individual calendar for that employee, not current office calendar
- c) Individual norm accounts for vacation/sick leave immediately after creation (not just after confirmation)

Related: [[REQ-statistics]], [[patterns/vacation-day-calculation]], [[analysis/office-period-model]]

## Node 44744:117220 — Budget Norm & Employee Reports (#3356, #3381)
**Page**: Statistics → Employee Reports with norm/deviation display

Design shows the same Employee Reports table with annotations for Sprint 15 features:
- **#3356**: Individual norm for part-month employees (start/end date within period)
- **#3320/#3281**: Requirements for current implementation changes
- Norm tooltip showing: "Первый рабочий день: 14 октября 2024" / "Последний рабочий день: 14 октября 2024"
- Comment field interaction states (detailed UX: hover, click, save behavior)

Key rule from annotations: "В столбце — норма сотрудника безвычета дней административного отпуска" (Column shows norm without deducting administrative leave days). Individual norm should only be shown on "Мои задачи" page, not in this table.

Related: [[REQ-statistics]], [[sprint-14-15-overview]]

## Node 43297:298160 — Sick Leave Display in Statistics (#2435, #3318)
**Page**: My Tasks page with sick leave information overlay

Ticket #2435 "Display sick leave information" — 7 detailed rules:
1. If employee has sick leave overlapping selected period (and exists+not deleted), show icon on all tabs with grouping
2. On hover, show tooltip with: "Часы: Больничный за выбранный период, [Х]ч" + "[Y]h [Start date – End date], [Status/Статус], [Tags]"
3. X = total sick leave hours for period, can be "отклонён" (rejected) or "удалён" (deleted)
4. Open/close dates in format: "дата открытия" (open date) as start, "дата закрытия" (close date) or end of reporting period
5. If sick leave period started before reporting period, use period start date instead
6. If 5+ sick leaves, show scrollable tooltip
7. Vacation AND sick leave tooltip: add "за выбранный период" section

Status display: новый (new), оплачен (paid), отклонён (rejected)

Related: [[modules/vacation-service]], [[exploration/ui-flows/reporting-and-other-pages]]

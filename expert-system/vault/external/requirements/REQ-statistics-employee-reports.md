---
type: external
tags:
  - statistics
  - employee-reports
  - requirements
  - confluence
  - norm-calculation
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/statistics-service-implementation]]'
  - '[[modules/frontend-statistics-module]]'
  - '[[external/requirements/google-docs-inventory]]'
  - '[[architecture/roles-permissions]]'
---

# Statistics: Employee Reports Requirements (Confluence 119244531)

Source: Confluence page 119244531 — "Статистика" (Statistics)
Ticket: #3195 (new Employee Reports page), #3381 (norm calculation), #3309 (comments)

## Menu Structure
- **Regular users**: Statistics menu — no sub-items, no page title
- **Privileged users**: Statistics → "General Statistics" + "Employee Reports"
  - ADMIN, CHIEF_ACCOUNTANT → all employees
  - OFFICE_ACCOUNTANT → own salary offices only
  - DEPARTMENT_MANAGER → own department only
  - TECH_LEAD → own employees only

## General Statistics Page Fixes
1. Fix Filter block padding (anchor "Reset all filters" button)
2. Date range filter: use N-dash (–)
3. Align padding around "Update data" / "Export" buttons
4. Column header: "Сотрудник / проект / задача" — add spaces
5. Translation fix: "За период" = "For period" (EN header breaks)
6. #2435: Sick leave icon + tooltip (show only period within range, N-dash dates)

## Employee Reports Page (#3195)

### Controls
1. **Search field**: by name/surname (Latin/Cyrillic) + login, including wrong keyboard layout. Table updates as user types.
2. **Date picker**: month selection. Default = last month open for confirmation in user's salary office.
3. **Toggle "Only excess over limit"**: On = show only employees with reported hours above/below thresholds from admin settings.

### Table Columns

#### 4.1 Employee
- Name clickable → CS profile page
- **Vacation/sick leave icons** if present in selected month (tooltip: dates within period, per #2435)
- **Report icon** on row hover → tooltip "Employee report page", click → open report page
- **Row click** (anywhere except name) → expand accordion with project breakdown, sorted by hours descending

#### 4.2 Manager
- Filter enabled
- Value links to CS manager profile

#### 4.3 Reported
- Sum of reported hours for selected month
- **Red arrow up** if over-reported (deviation > 0)
- **Purple arrow down** if under-reported (deviation < 0)
- Red text if deviation % > `notification.reporting.over` (admin setting)
- Purple text if |deviation %| > `notification.reporting.under` (admin setting)

#### 4.4 Norm (#3381)
Budget norm = Individual norm + admin vacation work hours (from production calendar)

**Display cases:**
- **Case 1** (has admin vacation): `{individual norm} ({budget norm})`
- **Case 2** (has regular vacation or sick leave, no admin): `{budget norm}` (= individual norm)
- **Case 3** (no absences): `{budget norm}` (= general norm)

**Info icon** with tooltip near "Norm" header (Figma: 44767-69810)

#### 4.5 Deviation (Превышение)
Formula: `(Reported - BudgetNorm) / BudgetNorm * 100%`

Display: integer, except (-1, +1) range → 1 decimal place

**Edge cases:**
- Low norm but many hours → show calculated %, even if very large
- **Norm = 0, reported = 0** → show 0%
- **Norm = 0, reported > 0** → show "+ N/A%", treat as MAXIMUM value in sort order

Color: same red/purple rules as Reported column

**Behavior notes (#3381):**
- Working during **regular vacation / sick leave** → over-report
- Not working during **admin vacation** (but no overtime other days) → under-report

#### 4.6 Comment (#3309)
- Hover → edit frame (like "My Tasks")
- Click → edit mode with cursor
- Enter → new paragraph inside comment
- Exit: Tab or click outside
- Stores **last value** per employee
- **Per-month storage**: changing month shows that month's comments

### Sorting
Default: by deviation percentage descending (highest over-reporters first)

### Displayed Users
- Active employees in selected month
- Terminated employees: show in their last active month, not in subsequent months
- TBD (Sprint 15): #3353 + #3356 — employees starting/ending mid-month

### Admin Settings
- `notification.reporting.over` — threshold for over-report highlighting
- `notification.reporting.under` — threshold for under-report highlighting

## Related
- [[modules/statistics-service-implementation]] — backend
- [[modules/frontend-statistics-module]] — frontend
- [[external/requirements/google-docs-inventory]] — Google Sheets statistics spec (role access matrix)
- [[architecture/roles-permissions]] — role-based access

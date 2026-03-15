---
type: exploration
tags: [admin, employees, subcontractors, ui-exploration, companystaff]
created: 2026-03-14
updated: 2026-03-14
status: active
related: ["[[admin-panel-pages]]", "[[companystaff-integration]]", "[[architecture/roles-permissions]]", "[[app-navigation]]"]
branch: release/2.1
---

# Admin Employees & Subcontractors — Deep Exploration

Explored on timemachine as perekrest (admin). URL: `/admin/employees/`.

## Page Structure

Title: "Employees and subcontractors". Two tabs with distinct URLs:
- **Employees** tab → `/admin/employees/employees-list` (default)
- **Subcontractor** tab → `/admin/employees/contract-list`

Both tabs share: search field, "Show dismissed employees" checkbox, sortable table, pagination (20 rows/page).

## Employees Tab

**Columns:** Employee | Manager | (Report page link)
**Active employees:** ~400 (20 pages × 20 rows)
**With dismissed:** ~1700 (85 pages)

### Table Row Structure
Each row has 3 cells:
1. **Employee name** — link to `https://cs.noveogroup.com/profile/{login}` (opens CompanyStaff profile)
2. **Manager name** — link to `https://cs.noveogroup.com/profile/{login}`
3. **"Report page"** — link to `/report/{login}` (opens employee's report page as admin)

### Search
- Placeholder: "First name, last name of the employee or of the manager"
- Matches **both** employee name AND manager name (searching "dergachev" returns Dergachev + all his managed employees)
- Case-insensitive, instant filter (no debounce observed)
- Clear button (X icon) appears when text entered
- Pagination adjusts to search results

### Sort
- Employee column: sortable (arrow indicator), default ascending alphabetical
- Manager column: sortable (no arrow by default)

### Show Dismissed
- Unchecked by default (active employees only)
- When checked: dismissed employees added, total jumps from ~400 to ~1700

### Findings
1. **Data quality**: One dismissed row shows empty employee name cell for login `maxim.raykhrud` — link exists but display name is empty. Manager shows "Ivan Ilnitsky".
2. **Test accounts visible**: "ponofidin Security" appears in dismissed list — test/security accounts mixed with real employees.
3. **Entirely read-only**: No create/edit/delete actions. All employee data sourced from [[companystaff-integration|CompanyStaff]] sync.
4. **External links only**: Employee/manager names link to CS profiles (external domain `cs.noveogroup.com`), not to any TTT detail view.

## Subcontractor Tab

**Columns:** Subcontractor | Responsible manager | (Report page link)
**Active subcontractors:** ~40 (2 pages)

Same structure as Employees tab but different column headers:
- "Subcontractor" instead of "Employee"
- "Responsible manager" instead of "Manager"
- Search placeholder: "First name, last name of the subcontractor or of the responsible manager"
- Same dismissed checkbox and pagination behavior

### Observations
- Subcontractor logins use dot notation (e.g., `ammar.hannachi`, `soraya.azzaoui`) vs employees' single-word logins
- Many subcontractors managed by Anna Astakhova (French office pattern — foreign names)
- Same read-only behavior, same CS profile links

## Summary for Test Cases

| Feature | Test Points |
|---------|-------------|
| Tab switching | URL changes, data reloads, correct column headers |
| Search | By employee name, by manager name, case-insensitive, clear button |
| Show dismissed | Toggle adds/removes dismissed, pagination adjusts |
| Sorting | Employee/Subcontractor column ascending/descending |
| Links | CS profile links correct, Report page links correct |
| Pagination | Navigation, page count accuracy |
| Edge cases | Empty name display, test accounts visibility |

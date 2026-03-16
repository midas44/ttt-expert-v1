#!/usr/bin/env python3
"""Generate statistics.xlsx — unified test workbook for Statistics module.

Phase B output for the TTT Expert System (Session 63 — regenerated with enriched knowledge).
Covers: General Statistics UI (tabs, filters, tree/flat views, export), Employee Reports
        (access, search, norm display, deviation, comments, absence icons),
        Statistics API (12 endpoints, mixed units, error handling),
        Norm Calculation (personal vs budget, absences, caching),
        Access Control (role-based tab visibility + data scoping),
        Data & Cache (statistic_report table, nightly sync, MQ events),
        Export & Individual Norm CSV (#3400).

Knowledge sources:
  - modules/statistics-service-implementation.md (6 design issues, norm calc, 3 update paths)
  - modules/frontend-statistics-module.md (12 tech debt items, dual sub-systems)
  - exploration/ui-flows/statistics-ui-deep-exploration.md (tab matrix, 3 bugs)
  - exploration/api-findings/statistics-api-testing.md (10 endpoints, mixed units)
  - exploration/api-findings/statistics-cross-env-comparison.md (TM vs Stage field diffs)
  - external/tickets/ticket-3400-statistics-individual-norm-export.md (not in codebase)
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

# ── Styling constants ────────────────────────────────────────

FONT_HEADER = Font(name="Arial", bold=True, size=11, color="FFFFFF")
FONT_BODY = Font(name="Arial", size=10)
FONT_TITLE = Font(name="Arial", bold=True, size=14)
FONT_SUBTITLE = Font(name="Arial", bold=True, size=12)
FONT_LINK = Font(name="Arial", size=10, color="0563C1", underline="single")
FONT_LINK_BOLD = Font(name="Arial", size=11, bold=True, color="0563C1", underline="single")
FONT_SECTION = Font(name="Arial", bold=True, size=11)
FONT_SMALL = Font(name="Arial", size=9, italic=True, color="666666")

FILL_HEADER = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
FILL_ROW_ODD = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
FILL_ROW_EVEN = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
FILL_GREEN_HEADER = PatternFill(start_color="548235", end_color="548235", fill_type="solid")
FILL_RISK_HIGH = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
FILL_RISK_MED = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
FILL_RISK_LOW = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
FILL_RISK_CRITICAL = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
FILL_SECTION = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
ALIGN_LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)
ALIGN_LEFT_CENTER = Alignment(horizontal="left", vertical="center", wrap_text=True)

THIN_BORDER = Border(
    left=Side(style="thin", color="B4C6E7"),
    right=Side(style="thin", color="B4C6E7"),
    top=Side(style="thin", color="B4C6E7"),
    bottom=Side(style="thin", color="B4C6E7"),
)

TAB_COLOR_PLAN = "548235"
TAB_COLOR_TS = "2F5496"


# ── Helper functions ─────────────────────────────────────────

def style_header_row(ws, row, num_cols, fill=None):
    f = fill or FILL_HEADER
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = FONT_HEADER
        cell.fill = f
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER


def write_row(ws, row, values, font=None, fill=None, alignment=None):
    for col, val in enumerate(values, 1):
        cell = ws.cell(row=row, column=col, value=val)
        cell.font = font or FONT_BODY
        cell.alignment = alignment or ALIGN_LEFT
        cell.border = THIN_BORDER
        if fill:
            cell.fill = fill


def add_autofilter(ws, row, num_cols):
    ws.auto_filter.ref = f"A{row}:{get_column_letter(num_cols)}{ws.max_row}"


def add_back_link(ws, row=1):
    cell = ws.cell(row=row, column=1)
    cell.value = "<- Back to Plan"
    cell.font = FONT_LINK
    cell.hyperlink = "#'Plan Overview'!A1"


def write_ts_tab(ws, suite_name, test_cases):
    add_back_link(ws, row=1)
    ws.cell(row=1, column=2, value=f"Suite: {suite_name}").font = FONT_SUBTITLE

    headers = [
        "Test ID", "Title", "Preconditions", "Steps",
        "Expected Result", "Priority", "Type",
        "Requirement Ref", "Module/Component", "Notes"
    ]
    header_row = 3
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    for i, tc_item in enumerate(test_cases):
        row = header_row + 1 + i
        fill = FILL_ROW_EVEN if i % 2 == 0 else FILL_ROW_ODD
        values = [
            tc_item["id"], tc_item["title"], tc_item["preconditions"],
            tc_item["steps"], tc_item["expected"], tc_item["priority"],
            tc_item["type"], tc_item["req_ref"], tc_item["module"],
            tc_item.get("notes", "")
        ]
        write_row(ws, row, values, fill=fill)

    add_autofilter(ws, header_row, len(headers))

    col_widths = [14, 40, 35, 55, 45, 10, 12, 20, 25, 35]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = "A4"
    return len(test_cases)


def tc(id_, title, pre, steps, expected, priority, type_, req, module, notes=""):
    return {
        "id": id_, "title": title, "preconditions": pre,
        "steps": steps, "expected": expected, "priority": priority,
        "type": type_, "req_ref": req, "module": module, "notes": notes
    }


# =====================================================================
# TEST CASE DATA — 7 suites, 111 cases
# =====================================================================

# ── TS-STAT-GeneralUI (General Statistics Page) ─────────────

TS_STAT_GENERAL_UI = [
    tc("TC-STAT-001",
       "Tab visibility — EMPLOYEE-only user sees 1 tab",
       "Logged in as EMPLOYEE-only user (e.g. alsmirnov on timemachine).\n"
       "User has only VIEW_MY_TASKS permission.",
       "1. Navigate to /statistics/general\n"
       "2. Count visible tabs in StatisticsFiltersPanel\n"
       "3. Verify tab label",
       "Exactly 1 tab visible: 'My tasks'.\n"
       "No other tabs (My projects, Department, Office, etc.) shown.\n"
       "rc-tabs component renders single tab.",
       "High", "UI/Functional",
       "REQ-statistics-permissions", "StatisticsPage, TabsWithFiltersContainer",
       "Verified in S29: alsmirnov sees 1 tab"),

    tc("TC-STAT-002",
       "Tab visibility — multi-role user sees 8 tabs",
       "Logged in as user with 7+ roles (e.g. pvaynmaster on timemachine).\n"
       "Permissions include VIEW_MY_TASKS, VIEW_MY_PROJECTS, VIEW_MY_DEPARTMENT,\n"
       "VIEW_MY_OFFICE, VIEW_PROJECT.",
       "1. Navigate to /statistics/general\n"
       "2. Count visible tabs\n"
       "3. Verify tab labels match permissions",
       "8 tabs visible: My tasks, My projects, Employees on my projects,\n"
       "Department projects, Department employees, Office projects,\n"
       "Office employees, Tasks by employees.\n"
       "Customer tabs (2) not shown — require VIEW_CUSTOMER.",
       "High", "UI/Functional",
       "REQ-statistics-permissions", "TabsWithFiltersContainer",
       "Verified in S29: pvaynmaster sees 8 tabs"),

    tc("TC-STAT-003",
       "Tab visibility — maximum 13 tabs with all permissions",
       "User with ALL statistics permissions including VIEW_CUSTOMER.\n"
       "May require admin or special role combination.",
       "1. Navigate to /statistics/general\n"
       "2. Verify all 13 tabs visible per code-defined list\n"
       "3. Check Customer projects and Customer employees tabs",
       "All 13 tabs visible: My tasks, My projects, Employees on my projects,\n"
       "Department projects, Department employees, Office projects,\n"
       "Office employees, Tasks by employees, Tasks by employees (alt),\n"
       "Customer projects, Customer employees, + 2 manager variants.\n"
       "Note: VIEW_CUSTOMER permission rarely granted — tabs never observed in S29.",
       "Medium", "UI/Functional",
       "REQ-statistics-permissions", "TabsWithFiltersContainer",
       "13 tabs defined in code; max observed in testing = 8"),

    tc("TC-STAT-004",
       "Tab visibility — DEPARTMENT_MANAGER sees department tabs",
       "Logged in as DEPARTMENT_MANAGER (has VIEW_MY_DEPARTMENT).",
       "1. Navigate to /statistics/general\n"
       "2. Check for 'Department projects' and 'Department employees' tabs",
       "Department projects and Department employees tabs visible.\n"
       "Data scoped to department manager's department only.",
       "High", "UI/Functional",
       "REQ-statistics-permissions", "TabsWithFiltersContainer"),

    tc("TC-STAT-005",
       "Tab switching preserves date range (redux-persist)",
       "Logged in as multi-role user. Set custom date range.",
       "1. Set date range to Jan 1 - Jun 30 on 'My tasks' tab\n"
       "2. Switch to 'Office employees' tab\n"
       "3. Switch back to 'My tasks' tab\n"
       "4. Close browser tab, reopen /statistics/general",
       "Date range preserved across tab switches (step 2-3).\n"
       "Date range preserved after browser restart (step 4) via redux-persist.\n"
       "Known debt: stale filter persistence may cause confusion.",
       "Medium", "UI/Functional",
       "DEBT-frontend-statistics-11", "StatisticsFiltersPanel",
       "redux-persist stores state.statistics across sessions — tech debt #11"),

    tc("TC-STAT-006",
       "Search filter — by project name",
       "Logged in as multi-role user with VIEW_MY_PROJECTS.",
       "1. On 'My projects' tab, type a project name in search filter\n"
       "2. Wait for SearchMultiFilterContainer suggestions\n"
       "3. Select suggestion\n"
       "4. Verify table filters to show only that project",
       "Suggestions appear matching typed text (debounced).\n"
       "Table data filtered to selected project.\n"
       "Clear filter restores full data.",
       "High", "UI/Functional",
       "REQ-statistics-filters", "SearchMultiFilterContainer"),

    tc("TC-STAT-007",
       "Search filter — by employee name",
       "Logged in as multi-role user. On employee-related tab.",
       "1. Type employee name (Latin or Cyrillic) in search filter\n"
       "2. Verify suggestions include matching employees\n"
       "3. Select and verify table filtering",
       "Employee suggestions match typed text.\n"
       "Both Latin and Cyrillic names supported.\n"
       "Table filtered to selected employee's data.",
       "High", "UI/Functional",
       "REQ-statistics-filters", "SearchMultiFilterContainer"),

    tc("TC-STAT-008",
       "Search filter — by task name",
       "Logged in as multi-role user. On 'My tasks' tab.",
       "1. Type task name in search filter\n"
       "2. Verify suggestions\n"
       "3. Select and verify table filtering",
       "Task suggestions appear.\n"
       "Table shows only data for selected task.",
       "Medium", "UI/Functional",
       "REQ-statistics-filters", "SearchMultiFilterContainer"),

    tc("TC-STAT-009",
       "Search filter — by customer (VIEW_CUSTOMER required)",
       "Logged in as user with VIEW_CUSTOMER permission.",
       "1. Navigate to Customer projects/employees tab\n"
       "2. Verify 4th search filter (customer) is visible\n"
       "3. Type customer name and verify suggestions",
       "Customer filter visible (4th filter, hidden for users without VIEW_CUSTOMER).\n"
       "Customer suggestions appear.\n"
       "For users without VIEW_CUSTOMER: only 3 filters shown.",
       "Medium", "UI/Functional",
       "REQ-statistics-permissions", "SearchMultiFilterContainer",
       "EMPLOYEE sees 3 filters; multi-role with VIEW_CUSTOMER sees 4"),

    tc("TC-STAT-010",
       "Reset all filters clears all active filters",
       "Logged in as multi-role user. Multiple filters active.",
       "1. Set date range, select project filter, choose employee filter\n"
       "2. Verify 'Reset all filters' button is enabled\n"
       "3. Click 'Reset all filters'\n"
       "4. Verify all filters cleared to default state",
       "Button enabled when any filter is active.\n"
       "Button disabled when no filters active.\n"
       "All filters reset: date range returns to default (Jan 1 - Dec 31),\n"
       "search filters cleared, tab reset to first.",
       "Medium", "UI/Functional",
       "REQ-statistics-filters", "StatisticsFiltersPanel"),

    tc("TC-STAT-011",
       "Date range — custom date selection",
       "Logged in. On any statistics tab.",
       "1. Click start date picker, select March 1\n"
       "2. Click end date picker, select March 31\n"
       "3. Verify table data reloads for selected range",
       "Date pickers accept valid dates.\n"
       "Table data refreshes to show statistics for March only.\n"
       "Default: Jan 1 - Dec 31 of current year.",
       "High", "UI/Functional",
       "REQ-statistics-filters", "SelectDateContainer"),

    tc("TC-STAT-012",
       "Date range — period presets dropdown",
       "Logged in. On any statistics tab.",
       "1. Click 'Please select a date range' dropdown\n"
       "2. Select a preset (e.g., 'This month', 'Last quarter')\n"
       "3. Verify date pickers updated to preset range",
       "Preset options available in dropdown.\n"
       "Selecting preset auto-fills start/end date pickers.\n"
       "Table data refreshes to preset date range.",
       "Medium", "UI/Functional",
       "REQ-statistics-filters", "SelectDateContainer"),

    tc("TC-STAT-013",
       "View toggle — Tree vs Flat mode",
       "Logged in as multi-role user. Data visible in table.",
       "1. Select 'Tree' radio button\n"
       "2. Verify hierarchical rows with expand arrows\n"
       "3. Select 'Flat' radio button\n"
       "4. Verify all rows at same level",
       "Tree mode: Rows have expand/collapse arrows.\n"
       "  Employee -> Project -> Task hierarchy.\n"
       "Flat mode: All rows at same level, no nesting.\n"
       "Default: Flat mode.",
       "High", "UI/Functional",
       "REQ-statistics-views", "ListTypeRadioGroupContainer"),

    tc("TC-STAT-014",
       "Time format toggle — Hours vs Days",
       "Logged in. Data visible in table.",
       "1. Select 'Hours' radio button\n"
       "2. Note values in 'For the period' and 'Total' columns\n"
       "3. Select 'Days' radio button\n"
       "4. Verify values converted (hours / 8 = days)",
       "Hours mode: Values in decimal hours (e.g. 152.0).\n"
       "Days mode: Values in days (e.g. 19.0 = 152/8).\n"
       "Default: Hours.\n"
       "Conversion: 1 day = 8 hours.",
       "High", "UI/Functional",
       "REQ-statistics-views", "EffortTypeRadioGroupContainer"),

    tc("TC-STAT-015",
       "Refresh data button reloads current view",
       "Logged in. Data displayed in table.",
       "1. Note current data state\n"
       "2. Click blue 'Refresh data' button\n"
       "3. Verify loading indicator appears then data refreshes",
       "Loading spinner shown during refresh.\n"
       "Data reloaded from API with current filters.\n"
       "No filter/tab state change.",
       "Low", "UI/Functional",
       "REQ-statistics-views", "TableControls"),

    tc("TC-STAT-016",
       "Tree mode — expand employee row to see projects and tasks",
       "Logged in as multi-role user. Tree mode selected.\n"
       "Employee tab with data.",
       "1. Click expand arrow on an employee row\n"
       "2. Verify project rows appear nested under employee\n"
       "3. Click expand arrow on a project row\n"
       "4. Verify task rows appear nested under project",
       "Three-level hierarchy: Employee > Project > Task.\n"
       "Each level shows 'For the period' and 'Total' effort.\n"
       "Lazy loading: child data fetched on expand.\n"
       "Collapse hides child rows.",
       "High", "UI/Functional",
       "REQ-statistics-views", "StatisticsTableContainer",
       "Uses rc-table tree-table with lazy expansion"),

    tc("TC-STAT-017",
       "Employee row — CompanyStaff profile link",
       "Logged in as multi-role user. Employee tab, data visible.",
       "1. Hover over an employee row\n"
       "2. Locate CompanyStaff profile link icon\n"
       "3. Click the link",
       "CompanyStaff icon visible on employee rows.\n"
       "Link points to https://companystaff.noveogroup.com/profile/{login}.\n"
       "Opens in new tab.",
       "Low", "UI/Integration",
       "DEBT-frontend-statistics-4", "StatisticsTableContainer",
       "Hardcoded CompanyStaff URL — tech debt #4"),

    tc("TC-STAT-018",
       "Employee row — Report page navigation link",
       "Logged in as multi-role user. Employee tab.",
       "1. Hover over employee row\n"
       "2. Click report page navigation icon\n"
       "3. Verify navigation to /reports page for that employee",
       "Navigation icon appears on employee rows.\n"
       "Clicking navigates to /reports with employee context.\n"
       "Date range preserved in navigation.",
       "Low", "UI/Integration",
       "REQ-statistics-views", "StatisticsTableContainer"),

    tc("TC-STAT-019",
       "Column sorting — ascending and descending",
       "Logged in. Data visible in table.",
       "1. Click column header 'For the period'\n"
       "2. Verify ascending sort (arrow indicator)\n"
       "3. Click same column header again\n"
       "4. Verify descending sort",
       "First click: ascending sort, up arrow indicator.\n"
       "Second click: descending sort, down arrow indicator.\n"
       "Sortable columns: Employee/Project/Task, For the period, Total.",
       "Medium", "UI/Functional",
       "REQ-statistics-views", "StatisticsTableContainer"),

    tc("TC-STAT-020",
       "Sick leave absence icon and tooltip",
       "Logged in as multi-role user. Employee with sick leave in date range.",
       "1. Find employee row with sick leave icon (red cross)\n"
       "2. Hover to show tooltip\n"
       "3. Verify tooltip content",
       "IconSick displayed inline on employee row.\n"
       "Tooltip shows: total sick leave hours + individual periods\n"
       "  (dates, status, payment type).\n"
       "Hours/days unit follows effortDisplayType setting.",
       "Medium", "UI/Functional",
       "REQ-statistics-absences", "AbsencesIcon",
       "Absence data from POST /v1/statistic (vacation service)"),

    tc("TC-STAT-021",
       "Vacation absence icon and tooltip",
       "Logged in as multi-role user. Employee with vacation in date range.",
       "1. Find employee row with vacation icon (sun/palm)\n"
       "2. Hover to show tooltip\n"
       "3. Verify tooltip content includes all vacation types",
       "IconVacation displayed inline on employee row.\n"
       "Tooltip shows: total vacation hours + individual periods\n"
       "  (dates, type: paid/unpaid/advance, status).\n"
       "Hours/days unit follows effortDisplayType setting.",
       "Medium", "UI/Functional",
       "REQ-statistics-absences", "AbsencesIcon"),

    tc("TC-STAT-022",
       "Permission denied message — typo verification",
       "EMPLOYEE-only user attempting to access restricted tab via URL.",
       "1. Login as EMPLOYEE-only user\n"
       "2. Navigate directly to a statistics URL requiring higher permissions\n"
       "3. Check error message text",
       "Error message displayed. Current text has typo:\n"
       "\"You do'nt have access\" (misplaced apostrophe).\n"
       "Expected: \"You don't have access\".\n"
       "BUG-STAT-UI-1 (Low severity).",
       "Low", "UI/Bug verification",
       "BUG-STAT-UI-1", "StatisticsPage",
       "Confirmed in S29 exploration"),

    tc("TC-STAT-023",
       "Export — Download CSV",
       "Logged in as multi-role user. Data visible in table.",
       "1. Click Export dropdown\n"
       "2. Select 'Download CSV'\n"
       "3. Verify file download with correct data",
       "CSV file downloads.\n"
       "File contains columns matching visible table data.\n"
       "Units: HOURS (matches export API default).\n"
       "All filtered data included.",
       "High", "UI/Functional",
       "REQ-statistics-export", "TableControls"),

    tc("TC-STAT-024",
       "Export — Copy the table to clipboard",
       "Logged in. Data visible.",
       "1. Click Export dropdown\n"
       "2. Select 'Copy the table'\n"
       "3. Paste in spreadsheet application",
       "Table data copied to clipboard in TSV format.\n"
       "Pasteable into Excel/Google Sheets.\n"
       "Headers included.",
       "Medium", "UI/Functional",
       "REQ-statistics-export", "TableControls"),

    tc("TC-STAT-025",
       "Export — Copy link for Google tables",
       "Logged in. Data visible.",
       "1. Click Export dropdown\n"
       "2. Select 'Copy link for Google tables'\n"
       "3. Paste link into Google Sheets IMPORTDATA formula",
       "Link copied to clipboard.\n"
       "Link is a direct URL to CSV export endpoint with auth token.\n"
       "IMPORTDATA in Google Sheets fetches and displays data.",
       "Medium", "UI/Integration",
       "REQ-statistics-export", "TableControls",
       "IMPORTDATA compatibility tested in S29"),

    tc("TC-STAT-026",
       "Export — employees-largest-customers CSV",
       "Logged in with sufficient permissions. Date range set.",
       "1. GET /api/ttt/v1/statistic/export/employees-largest-customers\n"
       "   With params: startDate, endDate, timeUnit=HOURS\n"
       "2. Verify CSV format and columns",
       "HTTP 200. CSV response with correct headers.\n"
       "Units: HOURS (configurable via timeUnit param).\n"
       "Columns: employee info, customer, effort.",
       "Medium", "API/Functional",
       "REQ-statistics-export", "StatisticExportController"),
]

# ── TS-STAT-EmpReports (Employee Reports Sub-Page) ──────────

TS_STAT_EMP_REPORTS = [
    tc("TC-STAT-027",
       "Employee Reports — access granted for ADMIN",
       "Logged in as ADMIN user.",
       "1. Navigate to /statistics/employee-reports\n"
       "2. Verify page loads without 403\n"
       "3. Verify all employees visible (not scoped)",
       "Page loads successfully.\n"
       "All employees across all offices/departments visible.\n"
       "Full access: ADMIN sees everyone.",
       "High", "UI/Security",
       "REQ-employee-reports-access", "EmployeeReportsContainer"),

    tc("TC-STAT-028",
       "Employee Reports — access granted for CHIEF_ACCOUNTANT",
       "Logged in as CHIEF_ACCOUNTANT.",
       "1. Navigate to /statistics/employee-reports\n"
       "2. Verify access and scope",
       "Page loads. All employees visible (same scope as ADMIN).\n"
       "CHIEF_ACCOUNTANT = full access to Employee Reports.",
       "High", "UI/Security",
       "REQ-employee-reports-access", "EmployeeReportsContainer"),

    tc("TC-STAT-029",
       "Employee Reports — OFFICE_ACCOUNTANT sees own office only",
       "Logged in as ACCOUNTANT (office-scoped).",
       "1. Navigate to /statistics/employee-reports\n"
       "2. Verify employees are from accountant's office only\n"
       "3. Search for employee from different office",
       "Only employees from accountant's assigned office visible.\n"
       "Search returns no results for out-of-scope employees.\n"
       "Data scoping enforced at backend level (EmployeeAccessService).",
       "High", "UI/Security",
       "REQ-employee-reports-access", "EmployeeReportsContainer, EmployeeAccessService"),

    tc("TC-STAT-030",
       "Employee Reports — DEPARTMENT_MANAGER sees subordinates only",
       "Logged in as DEPARTMENT_MANAGER.",
       "1. Navigate to /statistics/employee-reports\n"
       "2. Verify only department subordinates visible",
       "Only employees in manager's department visible.\n"
       "Scoping: department_manager_login matches current user.\n"
       "Subordinates include direct reports only.",
       "High", "UI/Security",
       "REQ-employee-reports-access", "EmployeeReportsContainer"),

    tc("TC-STAT-031",
       "Employee Reports — 403 for EMPLOYEE-only user",
       "Logged in as EMPLOYEE-only user (e.g. alsmirnov).",
       "1. Navigate directly to /statistics/employee-reports\n"
       "2. Verify access denied",
       "HTTP 403 or frontend access denied message.\n"
       "EMPLOYEE role cannot access Employee Reports.\n"
       "Redirect to statistics general or error page.",
       "High", "UI/Security",
       "REQ-employee-reports-access", "EmployeeReportsContainer",
       "Verified in S29: alsmirnov gets 403"),

    tc("TC-STAT-032",
       "Employee search — by Latin first/last name",
       "Logged in with Employee Reports access. Page loaded.",
       "1. Type Latin first name in employee search field\n"
       "2. Verify suggestions dropdown\n"
       "3. Clear and type Latin last name\n"
       "4. Select suggestion",
       "Suggestions appear for both first and last name.\n"
       "Table filters to selected employee.\n"
       "API: GET /v1/statistic/report/employees with employee filter.",
       "High", "UI/Functional",
       "REQ-employee-reports-search", "EmployeeReportsPage, Filters"),

    tc("TC-STAT-033",
       "Employee search — by Cyrillic name",
       "Logged in. Employee Reports page.",
       "1. Type Cyrillic first or last name\n"
       "2. Verify suggestions in Cyrillic",
       "Suggestions work for Cyrillic names (russianName field).\n"
       "Display shows both Latin and Cyrillic names.",
       "High", "UI/Functional",
       "REQ-employee-reports-search", "Filters"),

    tc("TC-STAT-034",
       "Employee search — by login",
       "Logged in. Employee Reports page.",
       "1. Type employee login (e.g. 'pvaynmaster')\n"
       "2. Verify suggestions match by login",
       "Login-based search supported.\n"
       "Suggestion shows employee name + login.",
       "Medium", "UI/Functional",
       "REQ-employee-reports-search", "Filters"),

    tc("TC-STAT-035",
       "Employee search — wrong keyboard layout detection",
       "Logged in. Employee Reports page. Keyboard in Russian layout.",
       "1. Type 'gdfyv' (intended: 'pvayn' in wrong layout)\n"
       "2. Check if system suggests correct employee",
       "System may or may not detect layout mismatch.\n"
       "Verify: does search fall back to transliteration or show no results?\n"
       "If no detection: document as expected behavior.",
       "Medium", "UI/Functional",
       "REQ-employee-reports-search", "Filters",
       "Layout detection is frontend-side if present"),

    tc("TC-STAT-036",
       "Month picker — default value",
       "Logged in. Navigate to Employee Reports first time.",
       "1. Check month picker default selection\n"
       "2. Verify default matches current month",
       "Month picker defaults to current month.\n"
       "API called with startDate/endDate for current month.\n"
       "State in state.employeeReports.params (not redux-persisted).",
       "High", "UI/Functional",
       "REQ-employee-reports-filters", "Filters"),

    tc("TC-STAT-037",
       "Month picker — change month",
       "Logged in. Employee Reports page.",
       "1. Click month picker\n"
       "2. Select previous month\n"
       "3. Verify data reloads for selected month",
       "Month picker shows month/year navigation.\n"
       "Data reloads with new startDate/endDate params.\n"
       "Comment field values change per-month.",
       "High", "UI/Functional",
       "REQ-employee-reports-filters", "Filters"),

    tc("TC-STAT-038",
       "Over-limit toggle — filter employees above/below thresholds",
       "Logged in. Employee Reports with data.",
       "1. Enable 'exceeding limit' toggle\n"
       "2. Verify only employees above ±10% threshold shown\n"
       "3. Disable toggle\n"
       "4. Verify all employees shown",
       "Toggle ON: server-side filter (exceedingLimit=true).\n"
       "Shows only employees with |deviation| > 10%.\n"
       "Threshold from application_settings (default ±10%).\n"
       "Toggle OFF: all employees visible.",
       "High", "UI/Functional",
       "REQ-employee-reports-filters", "Filters, StatisticReportService"),

    tc("TC-STAT-039",
       "Reported column — over-report indicator (red arrow up)",
       "Employee with reported > budgetNorm + 10%.",
       "1. Find over-reporting employee row\n"
       "2. Check reported column styling\n"
       "3. Verify red color and up arrow",
       "reportedNotificationStatus = HIGH → overReported CSS class (red).\n"
       "reportedStatus = HIGH → up arrow icon.\n"
       "Formula: (reported - budgetNorm) / budgetNorm * 100 > 10%.",
       "High", "UI/Functional",
       "REQ-employee-reports-display", "ReportsTable, EmployeeRow"),

    tc("TC-STAT-040",
       "Reported column — under-report indicator (purple arrow down)",
       "Employee with reported < budgetNorm - 10%.",
       "1. Find under-reporting employee row\n"
       "2. Check reported column styling\n"
       "3. Verify purple color and down arrow",
       "reportedNotificationStatus = LOW → underReported CSS class (purple).\n"
       "reportedStatus = LOW → down arrow icon.\n"
       "Formula: (reported - budgetNorm) / budgetNorm * 100 < -10%.",
       "High", "UI/Functional",
       "REQ-employee-reports-display", "ReportsTable, EmployeeRow"),

    tc("TC-STAT-041",
       "Norm display — with admin vacation ({individual} ({budget}))",
       "Employee who took administrative (unpaid) vacation this month.",
       "1. Find employee with personalNorm != budgetNorm\n"
       "2. Check norm column display format",
       "Norm shows: '{personalNorm} ({budgetNorm})' format.\n"
       "personalNorm < budgetNorm because admin vacation subtracted from personal\n"
       "but NOT from budget norm.\n"
       "renderNormHours function appends ({budgetNorm}) when different.",
       "High", "UI/Functional",
       "REQ-employee-reports-norms", "ReportsTable",
       "Key business rule: admin vacation affects personal but not budget norm"),

    tc("TC-STAT-042",
       "Norm display — without admin vacation (single budget value)",
       "Employee with regular (paid) vacation only or no absences.",
       "1. Find employee where personalNorm == budgetNorm\n"
       "2. Check norm column display",
       "Single value shown: '{budgetNorm}'.\n"
       "No parenthetical when norms are equal.\n"
       "Paid vacation subtracted from both norms equally.",
       "High", "UI/Functional",
       "REQ-employee-reports-norms", "ReportsTable"),

    tc("TC-STAT-043",
       "Norm display — no absences (general norm)",
       "Employee with no vacations/sick leaves in selected month.",
       "1. Find employee with no absence icons\n"
       "2. Verify norm equals office calendar working hours",
       "Single norm value = office calendar working hours for month.\n"
       "personalNorm == budgetNorm == monthNorm.\n"
       "No absence icons displayed.",
       "Medium", "UI/Functional",
       "REQ-employee-reports-norms", "ReportsTable"),

    tc("TC-STAT-044",
       "Deviation display — integer value",
       "Employee with clear over/under reporting.",
       "1. Find employee with integer deviation value\n"
       "2. Verify format: 'N%' or '-N%'",
       "Deviation displayed as integer percentage.\n"
       "Excess formula: (reported - budgetNorm) / budgetNorm * 100.\n"
       "Positive = over-reported, negative = under-reported.",
       "High", "UI/Functional",
       "REQ-employee-reports-display", "ReportsTable"),

    tc("TC-STAT-045",
       "Deviation display — decimal in (-1, +1) range",
       "Employee with very small deviation.",
       "1. Find employee with deviation close to 0%\n"
       "2. Check decimal formatting",
       "Deviation shows decimal (e.g. '0.5%', '-0.3%').\n"
       "No rounding to zero for small non-zero values.",
       "Medium", "UI/Functional",
       "REQ-employee-reports-display", "ReportsTable"),

    tc("TC-STAT-046",
       "Deviation display — N/A% for zero-norm employee",
       "Employee with budgetNorm = 0 but reported > 0.\n"
       "(e.g. maternity leave, full-month absence).",
       "1. Find employee with 0 norm and >0 reported\n"
       "2. Check deviation display",
       "ExcessStatus = NA when budgetNorm = 0 but reported > 0.\n"
       "Display: 'N/A%' or infinity indicator.\n"
       "Division by zero handled gracefully.",
       "High", "UI/Data",
       "REQ-employee-reports-display", "StatisticReportService",
       "Design issue #3: excess uses budgetNorm not personalNorm"),

    tc("TC-STAT-047",
       "Deviation display — 0% for zero-norm and zero-reported",
       "Employee with both budgetNorm = 0 and reported = 0.",
       "1. Find employee with 0/0 scenario\n"
       "2. Check deviation display",
       "ExcessStatus = NEUTRAL when both are 0.\n"
       "Display: '0%' (neutral indicator).\n"
       "No division by zero error.",
       "Medium", "UI/Data",
       "REQ-employee-reports-display", "StatisticReportService"),

    tc("TC-STAT-048",
       "Default sort — by deviation descending",
       "Logged in. Employee Reports loads data.",
       "1. Check initial sort order (no column clicked)\n"
       "2. Verify most over-reported employees at top",
       "Default sort: deviation descending (highest over-report first).\n"
       "state.employeeReports.params.sort = 'excess',\n"
       "state.employeeReports.params.order = 'desc'.\n"
       "Server-side sorting via API params.",
       "High", "UI/Functional",
       "REQ-employee-reports-display", "EmployeeReportsPage"),

    tc("TC-STAT-049",
       "Comment field — create new comment",
       "Logged in as user with comment write access. Employee Reports page.",
       "1. Click comment field on an employee row\n"
       "2. Type comment text\n"
       "3. Click outside (blur) to save\n"
       "4. Reload page and verify comment persisted",
       "Textarea appears on click.\n"
       "Comment saved on blur via POST /v1/statistic/report.\n"
       "Comment persisted per employee + month combination.\n"
       "Visible on reload.",
       "High", "UI/Functional",
       "REQ-employee-reports-comments", "CommentField"),

    tc("TC-STAT-050",
       "Comment field — edit existing comment",
       "Employee has existing comment for current month.",
       "1. Click existing comment to edit\n"
       "2. Modify text\n"
       "3. Blur to save\n"
       "4. Verify updated text persisted",
       "Existing comment text loaded in textarea.\n"
       "Modified text saved on blur (POST replaces).\n"
       "Updated text visible on reload.",
       "Medium", "UI/Functional",
       "REQ-employee-reports-comments", "CommentField"),

    tc("TC-STAT-051",
       "Comment field — per-month storage",
       "Employee has comments in different months.",
       "1. View comment for March (has text)\n"
       "2. Switch to February\n"
       "3. Verify different (or empty) comment\n"
       "4. Switch back to March, verify original",
       "Comments stored per (employee_login, report_date) combination.\n"
       "Switching months loads that month's comment.\n"
       "report_date = 1st of selected month.",
       "High", "UI/Functional",
       "REQ-employee-reports-comments", "CommentField, StatisticReportService"),

    tc("TC-STAT-052",
       "Comment field — data loss on navigate away without blur",
       "Typing in comment field, not yet blurred.",
       "1. Click comment field, start typing\n"
       "2. Navigate away (click link or change month) WITHOUT blurring\n"
       "3. Return to original view",
       "BUG: Comment NOT saved — data lost.\n"
       "CommentField saves on blur only, no auto-save.\n"
       "No unsaved changes warning.\n"
       "Tech debt #9: saves on blur only.",
       "Medium", "UI/Bug verification",
       "DEBT-frontend-statistics-9", "CommentField",
       "Known tech debt — saves only on blur, no auto-save or dirty warning"),

    tc("TC-STAT-053",
       "Absence icons — vacation icon with tooltip",
       "Employee with approved vacation in selected month.",
       "1. Find employee row with vacation icon (sun/palm)\n"
       "2. Hover over icon\n"
       "3. Verify tooltip shows vacation details",
       "IconVacation visible on row.\n"
       "Tooltip: total hours + breakdown (dates, status, type).\n"
       "Data from POST /v1/statistic (vacation service).\n"
       "Dual API calls: both sub-systems fetch independently (debt #8).",
       "Medium", "UI/Functional",
       "REQ-employee-reports-absences", "AbsencesIcon"),

    tc("TC-STAT-054",
       "Absence icons — sick leave icon with tooltip",
       "Employee with sick leave in selected month.",
       "1. Find employee row with sick leave icon\n"
       "2. Hover over icon\n"
       "3. Verify tooltip shows sick leave details",
       "IconSick visible on row.\n"
       "Tooltip: total hours + periods (dates, status, payment type).\n"
       "Data from POST /v1/statistic/report/sick-leaves (vacation service).",
       "Medium", "UI/Functional",
       "REQ-employee-reports-absences", "AbsencesIcon"),

    tc("TC-STAT-055",
       "Expand project breakdown",
       "Employee Reports. Employee row visible.",
       "1. Click expand arrow on employee row\n"
       "2. Verify project breakdown rows appear\n"
       "3. Check project name, reported hours, manager columns",
       "ProjectRow components rendered under expanded EmployeeRow.\n"
       "Each project shows: name, reported effort, manager name.\n"
       "projectBreakdown fetched from GET /v1/statistic/report/projects.\n"
       "Re-fetched on every navigation (debt #10 — not cached).",
       "High", "UI/Functional",
       "REQ-employee-reports-detail", "ReportsTable, ProjectRow"),

    tc("TC-STAT-056",
       "Manager filter column",
       "Employee Reports with multiple managers.",
       "1. Locate 'Manager' column header with filter\n"
       "2. Click filter dropdown (ManagerFilter component)\n"
       "3. Select a specific manager\n"
       "4. Verify table shows only that manager's subordinates",
       "ManagerFilter provides dropdown of unique managers.\n"
       "Selecting filters by managersLogin param.\n"
       "Server-side filtering via API.\n"
       "Clear filter restores all employees.",
       "Medium", "UI/Functional",
       "REQ-employee-reports-filters", "ManagerFilter"),

    tc("TC-STAT-057",
       "Employee name — CS profile link",
       "Employee Reports. Employee row visible.",
       "1. Find CompanyStaff profile icon next to employee name\n"
       "2. Click icon\n"
       "3. Verify navigation to CS profile",
       "Icon links to https://companystaff.noveogroup.com/profile/{login}.\n"
       "Opens in new tab.\n"
       "Hardcoded URL (tech debt #4).",
       "Low", "UI/Integration",
       "DEBT-frontend-statistics-4", "EmployeeRow"),

    tc("TC-STAT-058",
       "Report page link on row hover",
       "Employee Reports. Employee row visible.",
       "1. Hover over employee row\n"
       "2. Click report page navigation icon\n"
       "3. Verify navigation to /reports page for that employee",
       "Navigation icon appears.\n"
       "Clicking navigates to report page with employee login context.\n"
       "Date preserved.",
       "Low", "UI/Integration",
       "REQ-employee-reports-detail", "EmployeeRow"),

    tc("TC-STAT-059",
       "Terminated employee — visible in last active month",
       "Employee terminated mid-month (work period endDate in past).",
       "1. Navigate to month of termination\n"
       "2. Verify employee appears with correct norm\n"
       "3. Navigate to month after termination\n"
       "4. Verify employee NOT listed",
       "Employee visible in termination month with pro-rated norm.\n"
       "Not visible in subsequent months.\n"
       "Norm clamped to effectiveBounds (work period).\n"
       "statistic_report entry exists only for active months.",
       "Medium", "UI/Data",
       "REQ-employee-reports-lifecycle", "StatisticReportService"),
]

# ── TS-STAT-API (Statistics API Endpoints) ───────────────────

TS_STAT_API = [
    tc("TC-STAT-060",
       "GET /v1/reports/summary — valid request",
       "API key or JWT auth. Employee login known.",
       "1. GET /api/ttt/v1/reports/summary?login=pvaynmaster&date=2026-03-01\n"
       "2. Verify response structure",
       "HTTP 200. JSON: {week: {reported, personalNorm, norm,\n"
       "  personalNormForDate, normForDate}, month: {...}}.\n"
       "Units: HOURS.\n"
       "normForDate = 0 for closed months, incremental for current month.",
       "High", "API",
       "REQ-statistics-api", "TaskReportController"),

    tc("TC-STAT-061",
       "GET /v1/reports/summary — missing login param (500 bug)",
       "API key auth.",
       "1. GET /api/ttt/v1/reports/summary?date=2026-03-01\n"
       "   (omit login parameter)\n"
       "2. Verify response",
       "BUG: HTTP 500 (MissingServletRequestParameterException).\n"
       "Expected: HTTP 400 with clear error message.\n"
       "@RequestParam required params return 500 instead of 400.\n"
       "Same bug on missing date param.",
       "Medium", "API/Negative",
       "BUG-STAT-API-500", "TaskReportController",
       "Systemic: all @RequestParam-required params return 500 when missing"),

    tc("TC-STAT-062",
       "GET /v1/reports/total — EMPLOYEE type, MONTH period",
       "API key auth.",
       "1. GET /api/ttt/v1/reports/total?type=EMPLOYEE&startDate=2026-03-01\n"
       "   &endDate=2026-03-31&periodType=MONTH\n"
       "2. Verify response structure",
       "HTTP 200. JSON: {items: [{periodStartDate, employee: {...},\n"
       "  statuses: {APPROVED, WAITING_APPROVAL, NOTHING_APPROVE, REPORTED},\n"
       "  effort}]}.\n"
       "Units: MINUTES (300/day = 5 hours).\n"
       "Employee type returns employee object in each item.",
       "High", "API",
       "REQ-statistics-api", "TaskReportController"),

    tc("TC-STAT-063",
       "GET /v1/reports/total — PROJECT type",
       "API key auth.",
       "1. GET /api/ttt/v1/reports/total?type=PROJECT&startDate=2026-03-01\n"
       "   &endDate=2026-03-31&periodType=MONTH\n"
       "2. Compare with EMPLOYEE type response",
       "HTTP 200. Polymorphic response: PROJECT type returns project object\n"
       "instead of employee object.\n"
       "Same statuses and effort fields.\n"
       "Units: MINUTES.",
       "Medium", "API",
       "REQ-statistics-api", "TaskReportController"),

    tc("TC-STAT-064",
       "GET /v1/reports/total — DAY and WEEK period types",
       "API key auth.",
       "1. GET with periodType=DAY, same date range\n"
       "2. GET with periodType=WEEK\n"
       "3. Compare aggregation levels",
       "DAY: one item per day per employee/project.\n"
       "WEEK: items grouped by week start.\n"
       "MONTH: items grouped by month.\n"
       "All return same total effort, different granularity.",
       "Medium", "API",
       "REQ-statistics-api", "TaskReportController"),

    tc("TC-STAT-065",
       "GET /v1/reports/effort — valid request",
       "API key auth. Known task ID.",
       "1. GET /api/ttt/v1/reports/effort?taskId={validTaskId}\n"
       "2. Verify response",
       "HTTP 200. Units: MINUTES.\n"
       "Returns cumulative all-time effort for task.\n"
       "Optional executorLogin param filters to specific employee.",
       "Medium", "API",
       "REQ-statistics-api", "TaskReportController"),

    tc("TC-STAT-066",
       "GET /v1/reports/effort — missing taskId (500 bug)",
       "API key auth.",
       "1. GET /api/ttt/v1/reports/effort (no params)\n"
       "2. Verify error response",
       "BUG: HTTP 500 (MissingServletRequestParameterException).\n"
       "Expected: HTTP 400.\n"
       "Same @RequestParam bug as /reports/summary.",
       "Low", "API/Negative",
       "BUG-STAT-API-500", "TaskReportController"),

    tc("TC-STAT-067",
       "GET /v1/reports/employees-over-reported — isPersonalNorm toggle",
       "API key auth.",
       "1. GET /api/ttt/v1/reports/employees-over-reported?date=2026-02-01\n"
       "   &isPersonalNorm=true\n"
       "2. Note count (e.g. 91)\n"
       "3. GET same with isPersonalNorm=false\n"
       "4. Note count (e.g. 77)",
       "HTTP 200. JSON: {total, data: [{employeeId, names, month, year,\n"
       "  norm, reported}]}.\n"
       "isPersonalNorm=true: more employees (uses individual norm).\n"
       "isPersonalNorm=false: fewer (uses office norm).\n"
       "Difference = employees where personalNorm < office norm.\n"
       "Units: HOURS.",
       "Medium", "API",
       "REQ-statistics-api", "TaskReportController",
       "Verified S11: true=91, false=77 for Feb 2026 on timemachine"),

    tc("TC-STAT-068",
       "GET /v1/statistic/employees — tree data",
       "API key auth.",
       "1. GET /api/ttt/v1/statistic/employees with date range params\n"
       "2. Verify tree-structured response",
       "HTTP 200. Tree-structured response (expandable nodes).\n"
       "18 optional filter params (employeeLogin, projectId, officeId, etc.).\n"
       "Units: MINUTES (effortForPeriod=9120 = 152 hours).\n"
       "Verified: 152 hours = SUM(task_report.actual_efforts).",
       "High", "API",
       "REQ-statistics-api", "StatisticController"),

    tc("TC-STAT-069",
       "GET /v1/statistic/permissions — permission list",
       "API key auth.",
       "1. GET /api/ttt/v1/statistic/permissions\n"
       "2. Verify response",
       "HTTP 200. Array of permission strings.\n"
       "API key auth: all 22 permissions returned.\n"
       "Permissions: EMPLOYEES_VIEW, OFFICES_VIEW, STATISTICS_VIEW,\n"
       "SUGGESTIONS_VIEW, PROJECTS_ALL, TASKS_EDIT, ASSIGNMENTS_VIEW/ALL,\n"
       "REPORTS_VIEW/EDIT/APPROVE, VACATIONS_*, CALENDAR_VIEW/EDIT, FILES_VIEW.",
       "Medium", "API",
       "REQ-statistics-api", "StatisticController"),

    tc("TC-STAT-070",
       "GET /v1/statistic/report/employees — Employee Reports data",
       "API key auth.",
       "1. GET /api/ttt/v1/statistic/report/employees\n"
       "   ?startDate=2026-03-01&endDate=2026-03-31\n"
       "2. Verify response fields",
       "HTTP 200. JSON array (not paginated).\n"
       "Fields per item: login, name, russianName, managerLogin, managerName,\n"
       "  managerRussianName, nodeType, nodeUuid, norm, budgetNorm, reported,\n"
       "  excess, expandable, reportedNotificationStatus, reportedStatus.\n"
       "NOTE: TM has 15 fields, Stage has 17 (extra: id, normForDate).\n"
       "Decimal precision: TM=3 places, Stage=2 places.",
       "High", "API",
       "REQ-statistics-api", "StatisticReportController",
       "Cross-env field difference documented in S63 cross-env comparison"),

    tc("TC-STAT-071",
       "POST /v1/statistic/report — save comment",
       "API key auth or JWT with write access.",
       "1. POST /api/ttt/v1/statistic/report\n"
       "   Body: {login: 'pvaynmaster', reportDate: '2026-03-01',\n"
       "          comment: 'Test comment'}\n"
       "2. GET /v1/statistic/report/employees and verify comment",
       "HTTP 200. Comment saved for employee + month.\n"
       "GET returns comment field populated.\n"
       "Overwrites previous comment for same employee/month.",
       "Medium", "API",
       "REQ-employee-reports-comments", "StatisticReportController"),

    tc("TC-STAT-072",
       "Mixed unit consistency — cross-endpoint verification",
       "API key auth. Same employee/date range.",
       "1. GET /v1/reports/summary (HOURS)\n"
       "2. GET /v1/reports/total (MINUTES)\n"
       "3. GET /v1/statistic/employees (MINUTES)\n"
       "4. Cross-verify: summary_hours * 60 == total_minutes == stat_minutes",
       "Unit mapping verified:\n"
       "  /reports/summary: HOURS\n"
       "  /reports/total: MINUTES\n"
       "  /reports/effort: MINUTES\n"
       "  /reports/employees-over-reported: HOURS\n"
       "  /statistic/* tree endpoints: MINUTES\n"
       "  /statistic/export/*: HOURS\n"
       "  DB statistic_report: HOURS\n"
       "  DB task_report.actual_efforts: MINUTES\n"
       "Conversion: 152 HOURS = 9120 MINUTES.",
       "High", "API/Data",
       "BUG-STAT-UNITS", "Multiple controllers",
       "Systemic design issue: inconsistent units across endpoints"),

    tc("TC-STAT-073",
       "Cross-environment field comparison — TM vs Stage",
       "API key auth on both timemachine and stage.",
       "1. GET /v1/statistic/report/employees on timemachine\n"
       "2. GET same on stage\n"
       "3. Compare field sets and values",
       "Field differences:\n"
       "  Stage has 'id' and 'normForDate' — TM does not.\n"
       "  TM: 15 fields, Stage: 17 fields.\n"
       "Decimal: TM=3 places (223.250), Stage=2 (223.25).\n"
       "Russian name format: TM='Last First', Stage='First Last'.\n"
       "Data values (effort, norm): identical.",
       "Medium", "API/Cross-env",
       "ENV-field-diff", "StatisticReportController",
       "release/2.1 removed id + normForDate from response vs stage branch"),

    tc("TC-STAT-074",
       "GET /v1/reports/effort — no auth required (security bug)",
       "No authentication headers.",
       "1. GET /api/ttt/v1/reports/effort?taskId={validId}\n"
       "   WITHOUT any auth header\n"
       "2. Verify response",
       "Verify whether endpoint requires authentication.\n"
       "Expected: HTTP 401 Unauthorized without auth.\n"
       "If HTTP 200: SECURITY BUG — endpoint accessible without auth.",
       "High", "API/Security",
       "SEC-effort-endpoint", "TaskReportController",
       "Check @PreAuthorize or security config for this endpoint"),

    tc("TC-STAT-075",
       "Statistics export endpoint — CSV format verification",
       "API key auth.",
       "1. GET /api/ttt/v1/statistic/export/employees\n"
       "   With startDate, endDate params\n"
       "2. Verify CSV format, headers, data types",
       "HTTP 200. Content-Type: text/csv.\n"
       "Headers: EmployeeLogin, EmployeeName, Contractor,\n"
       "  DepartmentManagerLogin, DepartmentManagerName,\n"
       "  EffortForPeriod, EffortTotal, BeginDate, EndDate, NodeType.\n"
       "10 export endpoints under /v1/statistic/export/.",
       "Medium", "API",
       "REQ-statistics-export", "StatisticExportController"),
]

# ── TS-STAT-NormCalc (Norm Calculation Logic) ────────────────

TS_STAT_NORM_CALC = [
    tc("TC-STAT-076",
       "Personal norm — employee with no absences",
       "Employee with no vacations, sick leaves, or day-offs in target month.\n"
       "Office calendar configured with working hours.",
       "1. GET /v1/statistic/report/employees for target employee/month\n"
       "2. Compare 'norm' field with office calendar working hours\n"
       "3. Verify via DB: SELECT * FROM statistic_report\n"
       "   WHERE employee_login = ? AND report_date = ?",
       "personalNorm = totalNorm (office calendar hours for month).\n"
       "budgetNorm = totalNorm (same, since no admin vacation).\n"
       "No subtraction. personalNorm == budgetNorm.\n"
       "Example: 22 working days * 8h = 176 hours.",
       "High", "Data/Calculation",
       "REQ-norm-calculation", "NormCalculationService"),

    tc("TC-STAT-077",
       "Personal norm — employee with regular vacation",
       "Employee with approved paid vacation (5 working days) in target month.",
       "1. Verify vacation exists via vacation service\n"
       "2. GET /v1/statistic/report/employees for employee\n"
       "3. Calculate expected: monthNorm - (5 * 8) = monthNorm - 40",
       "personalNorm = monthNorm - 40 (5 days * 8h subtracted).\n"
       "budgetNorm = monthNorm - 40 (paid vacation subtracted from both).\n"
       "personalNorm == budgetNorm for paid vacation.\n"
       "Off-periods from vacation service merged before calculation.",
       "High", "Data/Calculation",
       "REQ-norm-calculation", "NormCalculationService"),

    tc("TC-STAT-078",
       "Personal norm — employee with admin (unpaid) vacation",
       "Employee with administrative (unpaid) vacation in target month.",
       "1. Verify admin vacation exists\n"
       "2. GET /v1/statistic/report/employees\n"
       "3. Compare personalNorm vs budgetNorm",
       "personalNorm = monthNorm - adminVacationHours (subtracted).\n"
       "budgetNorm = monthNorm (admin vacation NOT subtracted from budget).\n"
       "KEY DIFFERENCE: personalNorm < budgetNorm.\n"
       "Budget norm filters out administrative vacations before building off-periods.",
       "High", "Data/Calculation",
       "REQ-norm-calculation", "NormCalculationService",
       "Core business rule: admin vacation affects personal but not budget norm"),

    tc("TC-STAT-079",
       "Personal norm — employee with sick leave",
       "Employee with sick leave in target month.",
       "1. Verify sick leave exists via vacation service\n"
       "2. GET /v1/statistic/report/employees\n"
       "3. Calculate expected norm reduction",
       "personalNorm = monthNorm - sickLeaveHours.\n"
       "budgetNorm = monthNorm - sickLeaveHours.\n"
       "Sick leave treated same as paid vacation for norm calculation.\n"
       "Both norms reduced equally.",
       "Medium", "Data/Calculation",
       "REQ-norm-calculation", "NormCalculationService"),

    tc("TC-STAT-080",
       "Personal norm — overlapping absences merged",
       "Employee with overlapping vacation and sick leave periods.",
       "1. Create scenario: vacation Mar 10-15, sick leave Mar 13-18\n"
       "2. GET norm for March\n"
       "3. Verify overlapping days NOT double-counted",
       "Overlapping off-periods merged before subtraction.\n"
       "Merged range: Mar 10-18 (9 calendar days, ~6 working days).\n"
       "personalNorm = monthNorm - mergedWorkingHours.\n"
       "No double-counting of Mar 13-15.",
       "Medium", "Data/Calculation",
       "REQ-norm-calculation", "NormCalculationService",
       "Merging logic in BaseStatistic.mergeOverlappingPeriods"),

    tc("TC-STAT-081",
       "Personal norm — clamped to employee work period",
       "Employee hired mid-month (e.g. effectiveDate = March 15).",
       "1. GET norm for March for mid-month hire\n"
       "2. Verify norm covers only working days from hire date",
       "personalNorm = working hours from Mar 15 to Mar 31 only.\n"
       "Clamped by effectiveBounds (start = max(periodStart, hireDate),\n"
       "  end = min(periodEnd, terminationDate)).\n"
       "Pro-rated norm: ~50% of full month for mid-month hire.",
       "High", "Data/Calculation",
       "REQ-norm-calculation", "NormCalculationService",
       "Step 1 of norm calc: clamp date range to employee work period"),

    tc("TC-STAT-082",
       "Budget norm — admin vacation excluded from off-periods",
       "Employee with both paid and admin vacation in same month.",
       "1. Verify both vacation types exist\n"
       "2. GET norm data\n"
       "3. Verify: personalNorm includes both, budgetNorm excludes admin",
       "personalNorm subtracted by: paid vac + admin vac + sick leave.\n"
       "budgetNorm subtracted by: paid vac + sick leave ONLY.\n"
       "Difference = admin vacation hours.\n"
       "Code path: budgetNorm filters ADMINISTRATIVE type before building off-periods.",
       "High", "Data/Calculation",
       "REQ-norm-calculation", "NormCalculationService"),

    tc("TC-STAT-083",
       "Deviation formula verification",
       "Employee with known reported and budgetNorm values.",
       "1. GET /v1/statistic/report/employees for employee\n"
       "2. Note: reported, budgetNorm, excess values\n"
       "3. Verify: excess = (reported - budgetNorm) / budgetNorm * 100",
       "Formula: (reported - budgetNorm) / budgetNorm * 100.\n"
       "ExcessStatus:\n"
       "  HIGH: excess > 0% (over-reported)\n"
       "  LOW: excess < 0% (under-reported)\n"
       "  NEUTRAL: excess == 0%\n"
       "  NA: budgetNorm == 0\n"
       "NOTE: Uses budgetNorm, not personalNorm (design issue #3).",
       "High", "Data/Calculation",
       "REQ-norm-calculation", "StatisticReportService",
       "Design issue: admin vacation employee penalized in deviation calc"),

    tc("TC-STAT-084",
       "budgetNorm null fallback to monthNorm",
       "Scenario where budgetNorm is null in statistic_report table.",
       "1. Check DB for records with budget_norm IS NULL\n"
       "2. GET /v1/statistic/report/employees for those employees\n"
       "3. Verify API returns monthNorm as fallback",
       "When budgetNorm is null, service falls back to monthNorm.\n"
       "API response still shows a valid budgetNorm value.\n"
       "Design issue #2: silent fallback may mask data problems.",
       "Medium", "Data/Calculation",
       "DEBT-statistics-2", "StatisticReportService",
       "budgetNorm null fallback is implicit — no logging or warning"),

    tc("TC-STAT-085",
       "Norm cache — Caffeine 5min TTL",
       "Multiple rapid requests for same employee norm.",
       "1. GET norm for employee X\n"
       "2. Immediately GET again (within 5 min)\n"
       "3. Wait 6 minutes, GET again\n"
       "4. Compare response times",
       "First request: slower (calendar service call + computation).\n"
       "Second request (cached): faster response.\n"
       "After TTL (5 min): cache expired, full recalculation.\n"
       "Cache: Caffeine in-memory, max 1000 entries.\n"
       "Cache key: reportingNorm per employee/month.",
       "Low", "Performance",
       "REQ-norm-caching", "NormCalculationService",
       "Caffeine TTL 5min, max 1000 entries for calendar service calls"),
]

# ── TS-STAT-Access (Access Control & Permissions) ────────────

TS_STAT_ACCESS = [
    tc("TC-STAT-086",
       "ADMIN — full access to all statistics views",
       "Logged in as ADMIN.",
       "1. Navigate to /statistics/general — verify all tabs\n"
       "2. Navigate to /statistics/employee-reports — verify all employees\n"
       "3. Verify can create/edit comments",
       "All tabs visible in General Statistics.\n"
       "All employees across all offices visible in Employee Reports.\n"
       "Comment write access granted.\n"
       "No data scoping restrictions.",
       "High", "Security",
       "REQ-statistics-access", "EmployeeAccessService"),

    tc("TC-STAT-087",
       "CHIEF_ACCOUNTANT — full access scope",
       "Logged in as CHIEF_ACCOUNTANT.",
       "1. Verify General Statistics tabs\n"
       "2. Verify Employee Reports shows all employees",
       "Same scope as ADMIN: all employees visible.\n"
       "All tabs accessible based on permissions.\n"
       "Comment write access granted.",
       "Medium", "Security",
       "REQ-statistics-access", "EmployeeAccessService"),

    tc("TC-STAT-088",
       "ACCOUNTANT — office-scoped access",
       "Logged in as ACCOUNTANT assigned to specific salary office.",
       "1. Navigate to Employee Reports\n"
       "2. Verify only office employees visible\n"
       "3. Search for employee from different office",
       "Only employees from accountant's salary office visible.\n"
       "Out-of-office employees not returned in search.\n"
       "Scoping: EmployeeAccessService filters by salaryOfficeId.",
       "High", "Security",
       "REQ-statistics-access", "EmployeeAccessService"),

    tc("TC-STAT-089",
       "DEPARTMENT_MANAGER — department-scoped access",
       "Logged in as DEPARTMENT_MANAGER.",
       "1. Navigate to Employee Reports\n"
       "2. Verify only department subordinates visible\n"
       "3. Check General Statistics department tabs",
       "Employee Reports: only direct subordinates.\n"
       "General Statistics: Department tabs show department data.\n"
       "Scoping: departmentManagerLogin = current user.",
       "High", "Security",
       "REQ-statistics-access", "EmployeeAccessService"),

    tc("TC-STAT-090",
       "TECH_LEAD — subordinate-scoped access",
       "Logged in as TECH_LEAD.",
       "1. Navigate to Employee Reports\n"
       "2. Verify scope matches DEPARTMENT_MANAGER",
       "Similar to DEPARTMENT_MANAGER: subordinates visible.\n"
       "Scoping based on team lead assignments.",
       "Medium", "Security",
       "REQ-statistics-access", "EmployeeAccessService"),

    tc("TC-STAT-091",
       "EMPLOYEE — restricted to My tasks tab only",
       "Logged in as EMPLOYEE-only (no additional roles).",
       "1. Navigate to /statistics/general\n"
       "2. Verify only 1 tab: 'My tasks'\n"
       "3. Verify no access to other tabs even via URL manipulation",
       "1 tab visible: My tasks.\n"
       "Only VIEW_MY_TASKS permission.\n"
       "Cannot see other employees' data.\n"
       "Direct URL to other tabs: empty data or access denied.",
       "High", "Security",
       "REQ-statistics-access", "TabsWithFiltersContainer",
       "Verified in S29: alsmirnov sees exactly 1 tab"),

    tc("TC-STAT-092",
       "EMPLOYEE — cannot access Employee Reports via URL",
       "Logged in as EMPLOYEE-only.",
       "1. Navigate directly to /statistics/employee-reports URL\n"
       "2. Verify access denied (403 or redirect)",
       "HTTP 403 Forbidden or frontend access denied page.\n"
       "Backend enforces role check before returning data.\n"
       "Frontend shows error or redirects to General Statistics.",
       "High", "Security",
       "REQ-statistics-access", "EmployeeReportsContainer",
       "Verified in S29"),

    tc("TC-STAT-093",
       "API key authentication — returns full permissions",
       "Using API_SECRET_TOKEN header (API key auth).",
       "1. GET /api/ttt/v1/statistic/permissions\n"
       "   With header: API_SECRET_TOKEN={api_key}\n"
       "2. Verify all permissions returned",
       "All 22 permissions returned (flat list).\n"
       "API key acts as superuser for statistics endpoints.\n"
       "Same as ADMIN access level.",
       "Medium", "Security/API",
       "REQ-statistics-api-auth", "StatisticController"),

    tc("TC-STAT-094",
       "Employee Reports — OFFICE_HR access scope",
       "Logged in as OFFICE_HR user.",
       "1. Navigate to Employee Reports\n"
       "2. Verify employees visible match HR assignment",
       "Only employees assigned to this HR visible.\n"
       "Scoping: officeHrLogin = current user.\n"
       "More granular than ACCOUNTANT (HR-specific assignments).",
       "Medium", "Security",
       "REQ-statistics-access", "EmployeeAccessService"),
]

# ── TS-STAT-DataCache (Data & Cache: statistic_report) ───────

TS_STAT_DATA_CACHE = [
    tc("TC-STAT-095",
       "statistic_report — nightly sync creates/updates records",
       "Database access. Nightly cron at 4:00 AM.",
       "1. Check current statistic_report record count\n"
       "2. Wait for nightly sync (or trigger via test API)\n"
       "3. Verify records updated for current + previous month\n"
       "4. Check last_updated_time timestamps",
       "Nightly sync (4:00 AM, ShedLock distributed lock):\n"
       "  Recalculates current + previous month for ALL employees.\n"
       "  Deletes records for terminated employees.\n"
       "  Updates reported_effort, month_norm, budget_norm.\n"
       "Records count matches active employee count * 2 months.",
       "Medium", "Data/Cron",
       "REQ-statistic-report-sync", "StatisticReportScheduler",
       "ShedLock prevents duplicate execution across instances"),

    tc("TC-STAT-096",
       "statistic_report — task report event triggers update",
       "Employee submits a time report.",
       "1. Note employee's statistic_report.reported_effort\n"
       "2. Submit a task report (POST /v1/task-reports)\n"
       "3. Wait briefly for async event processing\n"
       "4. Re-check statistic_report.reported_effort",
       "reported_effort updated for that employee/month.\n"
       "@TransactionalEventListener triggers after commit.\n"
       "@Async processing — may have slight delay.\n"
       "Creates record if missing (upsert behavior).\n"
       "Only reported_effort updated, not norms.",
       "Medium", "Data/Event",
       "REQ-statistic-report-sync", "StatisticReportService",
       "Async event: TaskReportEventListener"),

    tc("TC-STAT-097",
       "statistic_report — RabbitMQ vacation change event",
       "Vacation created/modified/cancelled for employee.",
       "1. Note employee's statistic_report norms\n"
       "2. Create/modify vacation via vacation service\n"
       "3. Wait for MQ event processing\n"
       "4. Re-check statistic_report norms",
       "RabbitMQ event triggers norm recalculation.\n"
       "Event types: INITIAL_SYNC, VACATION_CHANGES, SICK_LEAVE_CHANGES.\n"
       "INITIAL_SYNC: deletes extras. Others: upsert only.\n"
       "month_norm and budget_norm recalculated.",
       "Medium", "Data/Event",
       "REQ-statistic-report-sync", "StatisticReportService",
       "MQ topic: TTT_BACKEND_STATISTIC_REPORT"),

    tc("TC-STAT-098",
       "statistic_report — data consistency with task_report",
       "Database access to both tables.",
       "1. SELECT SUM(actual_efforts) FROM task_report\n"
       "   WHERE executor_login = ? AND report_date BETWEEN ? AND ?\n"
       "2. SELECT reported_effort FROM statistic_report\n"
       "   WHERE employee_login = ? AND report_date = ?\n"
       "3. Compare: statistic.reported_effort (HOURS) =\n"
       "   SUM(task_report.actual_efforts) (MINUTES) / 60",
       "reported_effort in statistic_report (HOURS) =\n"
       "SUM(task_report.actual_efforts) (MINUTES) / 60.\n"
       "Verified: 152 hours = 9120 minutes.\n"
       "Any discrepancy indicates sync lag or race condition.",
       "High", "Data/Consistency",
       "REQ-statistic-report-integrity", "statistic_report, task_report"),

    tc("TC-STAT-099",
       "statistic_report — 2-month sync window limitation",
       "Nightly sync scope: current + previous month only.",
       "1. Check statistic_report for 3 months ago\n"
       "2. Modify a task_report from 3 months ago\n"
       "3. Wait for nightly sync\n"
       "4. Check if statistic_report updated",
       "statistic_report NOT updated for months outside 2-month window.\n"
       "Historical data frozen after 2-month window passes.\n"
       "Design issue #4: no historical back-fill mechanism.\n"
       "Manual intervention required for corrections.",
       "Low", "Data/Limitation",
       "DEBT-statistics-4", "StatisticReportScheduler",
       "2-month window means retroactive corrections not reflected"),

    tc("TC-STAT-100",
       "statistic_report — terminated employee cleanup",
       "Employee terminated (work period ended).",
       "1. Note employee's statistic_report records\n"
       "2. Trigger nightly sync (or wait)\n"
       "3. Verify records deleted for terminated employee",
       "Nightly sync deletes statistic_report records for\n"
       "employees no longer active.\n"
       "INITIAL_SYNC MQ event also removes extras.\n"
       "Employee disappears from Employee Reports after cleanup.",
       "Medium", "Data/Lifecycle",
       "REQ-statistic-report-sync", "StatisticReportScheduler"),

    tc("TC-STAT-101",
       "Race condition — concurrent MQ + task report event",
       "Simultaneous vacation change (MQ) and report submission (event).",
       "1. Submit task report while vacation change MQ is processing\n"
       "2. Check final statistic_report state\n"
       "3. Verify no data corruption",
       "POTENTIAL ISSUE: No pessimistic locking between MQ handler\n"
       "and task report event handler.\n"
       "Design issue #1: race condition possible.\n"
       "Last-write-wins may cause norm or effort to be stale.\n"
       "Low probability in practice due to async timing.",
       "Low", "Data/Negative",
       "DEBT-statistics-1", "StatisticReportService",
       "No pessimistic lock — theoretical race condition"),

    tc("TC-STAT-102",
       "QA-1 environment — no statistic_report table (on-the-fly)",
       "QA-1 environment access.",
       "1. Query statistic_report table on QA-1\n"
       "2. Verify table absent or empty\n"
       "3. Verify statistics API still returns data",
       "QA-1: NO statistic_report table (or empty).\n"
       "Statistics computed on-the-fly from task_report.\n"
       "Timemachine: table exists (9662+ rows), batch sync.\n"
       "Both environments return identical data values.\n"
       "Cache = performance optimization only.",
       "Low", "Data/Cross-env",
       "ENV-statistic-cache", "StatisticReportService",
       "Verified in S11 API testing"),

    tc("TC-STAT-103",
       "Hardcoded CEO login — special handling",
       "Database access. CEO login = 'ilnitsky'.",
       "1. Search codebase for CEO_LOGIN constant\n"
       "2. Verify special handling in BaseStatistic\n"
       "3. Check if CEO excluded from certain calculations",
       "CEO_LOGIN = 'ilnitsky' hardcoded in BaseStatistic.\n"
       "Special handling: CEO may be excluded from certain\n"
       "aggregate calculations or reports.\n"
       "Design issue #5: hardcoded business logic.",
       "Low", "Data/Design",
       "DEBT-statistics-5", "BaseStatistic",
       "Hardcoded: should be config or role-based"),
]

# ── TS-STAT-Export (Export & Individual Norm CSV) ────────────

TS_STAT_EXPORT = [
    tc("TC-STAT-104",
       "CSV export — column headers match spec",
       "API key auth.",
       "1. GET /api/ttt/v1/statistic/export/employees\n"
       "   With startDate, endDate\n"
       "2. Parse CSV headers\n"
       "3. Compare with ExportEmployeeNode headers",
       "CSV headers: EmployeeLogin, EmployeeName, Contractor,\n"
       "DepartmentManagerLogin, DepartmentManagerName,\n"
       "EffortForPeriod, EffortTotal, BeginDate, EndDate, NodeType.\n"
       "10 columns. Comma-separated. UTF-8 encoding.",
       "Medium", "API/Export",
       "REQ-statistics-export", "StatisticExportController"),

    tc("TC-STAT-105",
       "CSV export — data accuracy vs UI display",
       "Same filters used for UI and CSV export.",
       "1. Note employee effort values in UI\n"
       "2. Download CSV export\n"
       "3. Compare values",
       "CSV values match UI display.\n"
       "Units: HOURS in export (matches UI hours mode).\n"
       "Floating point precision may differ slightly.\n"
       "All filtered employees included in CSV.",
       "High", "API/Export",
       "REQ-statistics-export", "StatisticExportController"),

    tc("TC-STAT-106",
       "CSV export — Contractor flag accuracy",
       "Mix of employees and contractors in data.",
       "1. Download CSV export\n"
       "2. Check 'Contractor' column values\n"
       "3. Cross-reference with employee records",
       "Contractor column: true/false for each row.\n"
       "Matches employee.contractor field in database.\n"
       "Contractors properly flagged in export.",
       "Low", "API/Data",
       "REQ-statistics-export", "StatisticExportController"),

    tc("TC-STAT-107",
       "Google Sheets link — IMPORTDATA compatibility",
       "Copy link for Google tables feature.",
       "1. Copy export link via UI\n"
       "2. In Google Sheets: =IMPORTDATA(\"<copied_url>\")\n"
       "3. Verify data loads correctly",
       "IMPORTDATA successfully fetches CSV from export URL.\n"
       "Auth token embedded in URL (time-limited?).\n"
       "Data renders in Google Sheets with correct columns.\n"
       "Note: URL may expire — verify TTL.",
       "Medium", "UI/Integration",
       "REQ-statistics-export", "TableControls"),

    tc("TC-STAT-108",
       "#3400 Individual norm CSV export — endpoint exists",
       "API key auth.",
       "1. GET /api/ttt/v1/statistic/report/employees/export\n"
       "   (or similar endpoint per #3400 spec)\n"
       "2. Verify HTTP status",
       "EXPECTED: HTTP 404 — endpoint NOT deployed.\n"
       "Ticket #3400 marked 'Production Ready' but code NOT in codebase.\n"
       "Verified on both timemachine and stage: 404.\n"
       "Implementation may be in unmerged branch.",
       "Medium", "API/Feature",
       "TICKET-3400", "StatisticExportController",
       "Status discrepancy: ticket says 'Production Ready' but endpoint 404"),

    tc("TC-STAT-109",
       "#3400 Individual norm CSV — column accuracy (when deployed)",
       "Assumes #3400 endpoint is deployed.",
       "1. GET export endpoint\n"
       "2. Verify columns: login, name, surname,\n"
       "   department_manager_login, salary_office, individual_norm\n"
       "3. Verify individual_norm = personalNorm (not budgetNorm)",
       "Columns per spec: login, name, surname,\n"
       "department_manager_login, salary_office, individual_norm.\n"
       "individual_norm = personalNorm (accounts for all absences\n"
       "+ transferred weekends/holidays).\n"
       "NOTE: Currently not deployable — mark as 'pending implementation'.",
       "Medium", "API/Feature",
       "TICKET-3400", "StatisticExportController",
       "Pending: exercise when #3400 is deployed"),

    tc("TC-STAT-110",
       "Export — all 10 export endpoints return valid CSV",
       "API key auth.",
       "1. Call each of 10 export endpoints:\n"
       "   departments, employees, employees/projects,\n"
       "   employees/tasks, task-bound-employees/tasks,\n"
       "   tasks, tasks/employees, projects,\n"
       "   projects/employees, employees-largest-customers\n"
       "2. Verify each returns HTTP 200 with CSV content",
       "All 10 endpoints return HTTP 200 with text/csv.\n"
       "Each has appropriate column headers.\n"
       "Data filtered by date range and permissions.\n"
       "No 500 errors on valid requests.",
       "Medium", "API/Export",
       "REQ-statistics-export", "StatisticExportController"),

    tc("TC-STAT-111",
       "Export — timeUnit parameter for largest-customers",
       "API key auth.",
       "1. GET /v1/statistic/export/employees-largest-customers\n"
       "   ?startDate=...&endDate=...&timeUnit=HOURS\n"
       "2. GET same with timeUnit=DAYS\n"
       "3. Compare effort values",
       "HOURS: effort in hours (e.g. 152.0).\n"
       "DAYS: effort in days (e.g. 19.0 = 152/8).\n"
       "Default: HOURS.\n"
       "Only employees-largest-customers supports timeUnit param.",
       "Low", "API/Export",
       "REQ-statistics-export", "StatisticExportController"),
]


# =====================================================================
# RISK DATA
# =====================================================================

RISKS = [
    ("Mixed API units (HOURS vs MINUTES)", "Data corruption in cross-endpoint aggregation",
     "High", "High", "Critical",
     "TC-STAT-072: Verify unit conversion across all endpoints"),
    ("Missing @RequestParam validation (500 bugs)", "Poor error handling, user confusion",
     "High", "Medium", "High",
     "TC-STAT-061, TC-STAT-066: Missing params return 500 instead of 400"),
    ("Race condition: MQ + event handler", "Stale norm or effort data in statistic_report",
     "Low", "Medium", "Medium",
     "TC-STAT-101: No pessimistic locking between concurrent update paths"),
    ("Cross-env field differences (TM vs Stage)", "Test failures when migrating to production",
     "High", "Medium", "High",
     "TC-STAT-073: Stage has 2 extra fields, different decimal precision"),
    ("#3400 Individual norm — not in codebase", "Feature gap for production",
     "Medium", "Medium", "Medium",
     "TC-STAT-108: Marked 'Production Ready' but endpoint returns 404"),
    ("Comment data loss on navigate without blur", "Lost user work, no warning",
     "High", "Low", "Medium",
     "TC-STAT-052: CommentField saves only on blur, no auto-save"),
    ("2-month sync window limitation", "Stale historical statistics",
     "Medium", "Low", "Low",
     "TC-STAT-099: No historical back-fill for retroactive corrections"),
    ("Hardcoded CEO login", "Maintenance burden, single point of failure",
     "Low", "Low", "Low",
     "TC-STAT-103: CEO_LOGIN = 'ilnitsky' hardcoded in BaseStatistic"),
    ("Stale redux-persist filters", "Confusing UX: old filters from previous sessions",
     "High", "Low", "Medium",
     "TC-STAT-005: Filters persisted across browser sessions via redux-persist"),
    ("Effort endpoint unauthenticated access", "Information disclosure",
     "Medium", "High", "High",
     "TC-STAT-074: Verify /v1/reports/effort requires authentication"),
    ("Vacation statistic 403 silent failure", "Missing absence data on employee rows",
     "Medium", "Medium", "Medium",
     "BUG-STAT-UI-2: Vacation statistic endpoint 403 causes silent data failure"),
    ("Budget norm null fallback", "Incorrect deviation calculations for affected employees",
     "Low", "Medium", "Medium",
     "TC-STAT-084: Silent fallback to monthNorm when budgetNorm is null"),
    ("Excess uses budgetNorm not personalNorm", "Admin-vacation employees penalized in deviation",
     "High", "Medium", "High",
     "TC-STAT-083: Design issue — admin vacation counted against employee"),
    ("Permission denied typo", "Minor UI quality issue",
     "High", "Low", "Low",
     "TC-STAT-022: 'You do\\'nt have access' — misplaced apostrophe"),
]


# =====================================================================
# BUILD WORKBOOK
# =====================================================================

def build_workbook():
    wb = openpyxl.Workbook()

    # ── SUITE REGISTRY ─────────────────────────────────────
    suites = [
        ("TS-STAT-GeneralUI", "General Statistics UI", TS_STAT_GENERAL_UI),
        ("TS-STAT-EmpReports", "Employee Reports", TS_STAT_EMP_REPORTS),
        ("TS-STAT-API", "Statistics API", TS_STAT_API),
        ("TS-STAT-NormCalc", "Norm Calculation", TS_STAT_NORM_CALC),
        ("TS-STAT-Access", "Access Control", TS_STAT_ACCESS),
        ("TS-STAT-DataCache", "Data & Cache", TS_STAT_DATA_CACHE),
        ("TS-STAT-Export", "Export & Norm CSV", TS_STAT_EXPORT),
    ]

    total_cases = sum(len(s[2]) for s in suites)

    # ── Plan Overview ──────────────────────────────────────
    ws_plan = wb.active
    ws_plan.title = "Plan Overview"
    ws_plan.sheet_properties.tabColor = TAB_COLOR_PLAN

    r = 1
    ws_plan.cell(row=r, column=1, value="Statistics Module — Test Plan").font = FONT_TITLE
    r += 2

    plan_info = [
        ("Module", "Statistics (General Statistics + Employee Reports)"),
        ("Phase", "Phase B — Test Documentation Generation (Session 63, regenerated)"),
        ("Version", "release/2.1"),
        ("Date", datetime.now().strftime("%Y-%m-%d")),
        ("Total Test Cases", str(total_cases)),
        ("Test Suites", str(len(suites))),
        ("Risks Assessed", str(len(RISKS))),
        ("Qase Overlap", "0 (no existing statistics cases in Qase TIMEREPORT)"),
    ]
    for label, value in plan_info:
        ws_plan.cell(row=r, column=1, value=label).font = FONT_SECTION
        ws_plan.cell(row=r, column=2, value=value).font = FONT_BODY
        r += 1

    r += 1
    ws_plan.cell(row=r, column=1, value="Scope").font = FONT_SUBTITLE
    r += 1
    scope_items = [
        "General Statistics page: 13 permission-gated tabs, tree/flat views, search filters, date range, export",
        "Employee Reports sub-page: access control, norm/deviation display, comments, absence icons, project breakdown",
        "Statistics API: 12+ endpoints across 2 controller families with mixed units (HOURS/MINUTES)",
        "Norm Calculation: personal vs budget norm, absence types, overlapping period merging, work period clamping",
        "Access Control: 6 role scoping levels, API key superuser, frontend tab gating",
        "Data & Cache: statistic_report table, 3 update paths (nightly cron, event, MQ), cross-env differences",
        "Export: 10 CSV endpoints, Google Sheets IMPORTDATA, #3400 individual norm (pending deployment)",
    ]
    for item in scope_items:
        ws_plan.cell(row=r, column=1, value=f"  - {item}").font = FONT_BODY
        r += 1

    r += 1
    ws_plan.cell(row=r, column=1, value="Test Suites").font = FONT_SUBTITLE
    r += 1

    for suite_id, suite_label, suite_cases in suites:
        cell = ws_plan.cell(row=r, column=1)
        cell.value = f"{suite_label} — {len(suite_cases)} cases"
        cell.font = FONT_LINK_BOLD
        cell.hyperlink = f"#'{suite_id}'!A1"
        r += 1

    r += 1
    ws_plan.cell(row=r, column=1, value="Knowledge Sources").font = FONT_SUBTITLE
    r += 1
    sources = [
        "modules/statistics-service-implementation.md — backend (6 design issues, norm calc, 3 update paths)",
        "modules/frontend-statistics-module.md — frontend (12 tech debt items, dual sub-systems)",
        "exploration/ui-flows/statistics-ui-deep-exploration.md — live UI testing across roles (S29)",
        "exploration/api-findings/statistics-api-testing.md — 10 endpoints tested, mixed units found",
        "exploration/api-findings/statistics-cross-env-comparison.md — TM vs Stage field differences",
        "external/tickets/ticket-3400-statistics-individual-norm-export.md — not in codebase",
    ]
    for src in sources:
        ws_plan.cell(row=r, column=1, value=f"  - {src}").font = FONT_SMALL
        r += 1

    r += 1
    ws_plan.cell(row=r, column=1, value="Test Data Generation").font = FONT_SUBTITLE
    r += 1
    data_gen = [
        "Employee logins: Use known test accounts — alsmirnov (EMPLOYEE-only), pvaynmaster (multi-role 7+), perekrest (multi-role)",
        "Date ranges: Current month for live data, previous month for closed period data",
        "Norm scenarios: Find employees via DB: SELECT * FROM statistic_report WHERE month_norm != budget_norm (admin vacation cases)",
        "Over/under report: Filter by excess > 10 or excess < -10 in statistic_report table",
        "Absence data: Cross-reference vacation/sick_leave tables with statistic_report for same employee/month",
        "API auth: Use API_SECRET_TOKEN from env config for full-access API testing",
        "Cross-env: Test same employee on both timemachine and stage for field comparison tests",
    ]
    for item in data_gen:
        ws_plan.cell(row=r, column=1, value=f"  - {item}").font = FONT_BODY
        r += 1

    ws_plan.column_dimensions["A"].width = 100
    ws_plan.column_dimensions["B"].width = 60

    # ── Feature Matrix ──────────────────────────────────────
    ws_fm = wb.create_sheet("Feature Matrix")
    ws_fm.sheet_properties.tabColor = TAB_COLOR_PLAN

    fm_headers = ["Feature Area", "UI Tests", "API Tests", "Data Tests",
                  "Security Tests", "Total", "Suite Link"]
    r = 1
    for col, h in enumerate(fm_headers, 1):
        cell = ws_fm.cell(row=r, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_GREEN_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    features = [
        ("General Statistics UI", 26, 0, 0, 0, "TS-STAT-GeneralUI"),
        ("Employee Reports", 33, 0, 0, 0, "TS-STAT-EmpReports"),
        ("Statistics API", 0, 16, 0, 0, "TS-STAT-API"),
        ("Norm Calculation", 0, 0, 10, 0, "TS-STAT-NormCalc"),
        ("Access Control", 0, 0, 0, 9, "TS-STAT-Access"),
        ("Data & Cache", 0, 0, 9, 0, "TS-STAT-DataCache"),
        ("Export & Norm CSV", 0, 8, 0, 0, "TS-STAT-Export"),
    ]
    for i, (feat, ui, api, data, sec, link) in enumerate(features):
        r = 2 + i
        total = ui + api + data + sec
        fill = FILL_ROW_EVEN if i % 2 == 0 else FILL_ROW_ODD
        write_row(ws_fm, r, [feat, ui, api, data, sec, total], fill=fill)
        cell = ws_fm.cell(row=r, column=7)
        cell.value = link
        cell.font = FONT_LINK
        cell.hyperlink = f"#'{link}'!A1"
        cell.border = THIN_BORDER
        if fill:
            cell.fill = fill

    # Totals row
    r = 2 + len(features)
    write_row(ws_fm, r, ["TOTAL", 59, 24, 19, 9, total_cases],
              font=FONT_SECTION, fill=FILL_SECTION)

    add_autofilter(ws_fm, 1, len(fm_headers))
    for i, w in enumerate([30, 12, 12, 12, 14, 10, 22], 1):
        ws_fm.column_dimensions[get_column_letter(i)].width = w

    # ── Risk Assessment ──────────────────────────────────────
    ws_risk = wb.create_sheet("Risk Assessment")
    ws_risk.sheet_properties.tabColor = TAB_COLOR_PLAN

    risk_headers = ["Risk", "Impact", "Likelihood", "Impact Level",
                    "Severity", "Mitigation / Test Focus"]
    r = 1
    for col, h in enumerate(risk_headers, 1):
        cell = ws_risk.cell(row=r, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_GREEN_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    for i, (risk, impact, likelihood, impact_lvl, severity, mitigation) in enumerate(RISKS):
        r = 2 + i
        fill_map = {"Critical": FILL_RISK_HIGH, "High": FILL_RISK_HIGH,
                    "Medium": FILL_RISK_MED, "Low": FILL_RISK_LOW}
        fill = fill_map.get(severity, FILL_ROW_ODD)
        write_row(ws_risk, r, [risk, impact, likelihood, impact_lvl,
                                severity, mitigation], fill=fill)

    add_autofilter(ws_risk, 1, len(risk_headers))
    for i, w in enumerate([40, 45, 12, 12, 12, 55], 1):
        ws_risk.column_dimensions[get_column_letter(i)].width = w

    # ── Test Suite tabs ──────────────────────────────────────
    for suite_id, suite_label, suite_cases in suites:
        ws = wb.create_sheet(suite_id)
        ws.sheet_properties.tabColor = TAB_COLOR_TS
        write_ts_tab(ws, suite_label, suite_cases)

    return wb, total_cases


if __name__ == "__main__":
    wb, count = build_workbook()
    outpath = "statistics.xlsx"
    wb.save(outpath)
    print(f"Generated {outpath} — {count} test cases")

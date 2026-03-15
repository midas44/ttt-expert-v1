#!/usr/bin/env python3
"""Generate admin.xlsx — unified test workbook for Administration module.

Phase B output for the TTT Expert System (Session 62).
Covers: Project management (search/detail/templates/tracker), Employee management,
        Production calendars (CRUD/events/working days), TTT settings/API/export,
        Tracker integration (credentials/sync/scripts), API errors & permissions.

Knowledge sources:
  - modules/admin-panel-deep-dive.md (10 design issues, full code analysis)
  - analysis/admin-calendar-form-validation-rules.md (field-level validation)
  - exploration/ui-flows/admin-panel-pages.md (7 admin pages)
  - exploration/ui-flows/admin-projects-deep-exploration.md (project page deep testing)
  - investigations/tracker-integration-deep-dive.md (8 tracker types, GraalVM sandbox)
  - exploration/data-findings/ttt-backend-schema-deep-dive.md (DB schema)
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
# TEST CASE DATA — 6 suites
# =====================================================================

# ── TS-ADM-Projects (Project Management) ────────────────────

TS_ADM_PROJECTS = [
    tc("TC-ADM-001",
       "All Projects: default view loads active projects",
       "Logged in as admin. Navigate to /admin/projects/all.",
       "1. Open Admin > Projects\n"
       "2. Verify default tab is 'All projects'\n"
       "3. Verify default status filter excludes Finished and Cancelled\n"
       "4. Verify pagination (20 per page)",
       "All Projects tab active by default.\n"
       "Table shows: Name, Customer, Supervisor, Manager, Type, Status, Actions.\n"
       "Status defaults: Active, Unconfirmed, Suspended, Acceptance, Warranty visible.\n"
       "Finished and Cancelled hidden.\n"
       "~200 active projects across 11 pages (20/page).",
       "High", "Functional",
       "REQ-admin-projects", "ProjectController, AdminProjectsPage"),

    tc("TC-ADM-002",
       "All Projects: search by project name with keyboard layout correction",
       "Admin on /admin/projects/all. Scope = Project.",
       "1. Enter 'Noveo' in search box\n"
       "2. Verify filtered results\n"
       "3. Switch keyboard to RU and type Cyrillic equivalent\n"
       "4. Verify auto-correction applies (SuggestionMappingUtil.correctLayout)",
       "Search filters instantly by project name.\n"
       "RU keyboard input auto-corrected to EN equivalent.\n"
       "Results match regardless of keyboard layout.",
       "Medium", "Functional",
       "REQ-admin-projects", "ProjectController.search, SuggestionMappingUtil"),

    tc("TC-ADM-003",
       "All Projects: search by customer name",
       "Admin on /admin/projects/all. Scope = Customer.",
       "1. Click 'Customer' scope button\n"
       "2. Enter customer name in search\n"
       "3. Verify results filtered by customer field",
       "Only projects matching customer name shown.\n"
       "Scope toggle between Project/Customer works.",
       "Medium", "Functional",
       "REQ-admin-projects", "ProjectController.search"),

    tc("TC-ADM-004",
       "All Projects: column filters (Supervisor, Manager, Type, Status)",
       "Admin on /admin/projects/all.",
       "1. Open Supervisor filter dropdown — verify ~55 people listed\n"
       "2. Select one supervisor — verify filter applied\n"
       "3. Open Type filter — verify 9 types: Production, Learning, Administration,\n"
       "   Commercial, Idle time, Internal, Investment, Investment without invoicing, PM\n"
       "4. Open Status filter — verify 7 statuses: Active, Finished, Unconfirmed,\n"
       "   Suspended, Acceptance, Warranty, Cancelled\n"
       "5. Combine multiple filters",
       "Each filter narrows results. Combining filters uses AND logic.\n"
       "9 project types confirmed. 7 status values confirmed.\n"
       "Filter dropdowns use checkbox multi-select.",
       "High", "Functional",
       "REQ-admin-projects", "ProjectSearchRequestDTO"),

    tc("TC-ADM-005",
       "All Projects: 'Show inactive projects' toggle",
       "Admin on /admin/projects/all.",
       "1. Verify Finished/Cancelled projects hidden by default\n"
       "2. Check 'Show inactive projects' checkbox\n"
       "3. Verify ~2900+ projects across 147 pages\n"
       "4. Uncheck — verify back to ~200 active",
       "Toggle adds Finished+Cancelled to visible statuses.\n"
       "Total with inactive: ~2900+ (147 pages).\n"
       "Total active only: ~200 (11 pages).",
       "Medium", "Functional",
       "REQ-admin-projects", "AdminProjectsPage"),

    tc("TC-ADM-006",
       "My Projects tab: shows only managed projects",
       "Admin/manager on /admin/projects/my.",
       "1. Click 'My projects' tab\n"
       "2. Verify tab label shows count: 'My projects (N)'\n"
       "3. Verify columns: Name, Manager, Status, Actions (no Customer/Supervisor/Type)\n"
       "4. Verify only projects where current user = Manager shown",
       "My projects tab shows subset. Reduced column set.\n"
       "Tab label includes count.\n"
       "BUG: Name column has href='#' — non-functional link.",
       "Medium", "Functional",
       "REQ-admin-projects", "AdminProjectsPage",
       "Known bug: My Projects name link is href='#' — incomplete PM Tool integration"),

    tc("TC-ADM-007",
       "Project detail dialog: all fields read-only",
       "Admin on /admin/projects/all.",
       "1. Click 'More about project' action button\n"
       "2. Verify dialog opens with URL hash #<projectId>\n"
       "3. Verify all fields read-only: Name, Account name, Customer, Country,\n"
       "   Supervisor, Manager, Owner, Watchers, Status, Type, Model, Total cost,\n"
       "   First/Last report dates\n"
       "4. Verify Name links to PM Tool: pm.noveogroup.com/projects/{pmtId}/profile/general\n"
       "5. Verify Supervisor/Manager/Owner link to CS profiles",
       "All fields read-only. PM Tool link correct.\n"
       "Employee names link to cs.noveogroup.com/profile/{username}.\n"
       "Total cost shown with 'md' unit (e.g., '4759.5 md').\n"
       "Dates in DD.MM.YYYY format.",
       "High", "Functional",
       "REQ-admin-projects", "ProjectController.find, ProjectServiceImpl.fillReportInfo"),

    tc("TC-ADM-008",
       "Project detail: History of changes section",
       "Admin viewing project detail dialog.",
       "1. Expand 'History of changes' section\n"
       "2. Verify chronological entries with date, user, field change (from → to)",
       "History section shows audit trail.\n"
       "Each entry: timestamp, user who made the change, field changed, old → new value.\n"
       "Changes from PM Tool sync also logged.",
       "Medium", "Functional",
       "REQ-admin-projects", "ProjectController, project_events table"),

    tc("TC-ADM-009",
       "Edit Tracker Data dialog: 3 editable URL fields",
       "Admin on /admin/projects/all.",
       "1. Click 'Edit tracker data' action button\n"
       "2. Verify 3 fields: Script of sync, Link to task tracker, Link to proxy server\n"
       "3. Edit 'Link to task tracker' with valid HTTPS URL\n"
       "4. Save and re-open — verify persistence\n"
       "5. Try invalid URL format",
       "Only 3 fields editable. All URL fields have 'https://' prefix.\n"
       "Script field pre-populated with default sync script.\n"
       "IsUrl validator checks domain/path format.\n"
       "Proxy server field includes helper link to Google Doc.",
       "High", "Functional",
       "REQ-admin-projects", "ProjectController.patch, TrackerValidation"),

    tc("TC-ADM-010",
       "Task Templates: CRUD operations",
       "Admin on /admin/projects/all.",
       "1. Click 'Task templates' action button\n"
       "2. Verify empty state: 'No templates' + 'Add a template' button\n"
       "3. Add a template — verify format: project name prefix + ' /' + suffix\n"
       "4. Toggle 'Assign the task to employee' per template\n"
       "5. Add multiple templates — verify numbering ('1 task template', '2 task templates')\n"
       "6. Delete a template\n"
       "7. Save and verify persistence",
       "Template format: '<project-name> / <suffix>'.\n"
       "'Assign to employee' toggle off by default.\n"
       "Templates auto-numbered. Save/Cancel buttons present.\n"
       "Templates define available tasks for report entry in this project.",
       "High", "Functional",
       "REQ-admin-projects", "TaskTemplateController",
       "Task templates are important for report entry — they define available tasks per project"),

    tc("TC-ADM-011",
       "Project API: GET by ID with permission check",
       "API key/user with PROJECTS_ALL or AUTHENTICATED_USER.",
       "1. GET /api/ttt/v1/projects/{projectId}\n"
       "2. Verify response includes report info (lastReportDate, totalEffort)\n"
       "3. GET with non-existent projectId\n"
       "4. Verify @ProjectIdExists validator response",
       "Step 1: HTTP 200 with full project BO including report enrichment.\n"
       "Step 3: HTTP 404 — @ProjectIdExists validation fails.\n"
       "Service validates PROJECTS VIEW permission internally.",
       "High", "API",
       "REQ-admin-projects", "ProjectController.find, ProjectServiceImpl"),

    tc("TC-ADM-012",
       "Project API: search with filters",
       "API user with PROJECTS_ALL.",
       "1. GET /api/ttt/v1/projects?managersLogins=perekrest\n"
       "2. GET /api/ttt/v1/projects?status=ACTIVE&type=COMMERCIAL\n"
       "3. GET /api/ttt/v1/projects?employeeLogins=testuser&role=MEMBER",
       "Step 1: Projects where perekrest is manager.\n"
       "Step 2: Active commercial projects.\n"
       "Step 3: Projects where testuser has MEMBER role.\n"
       "ProjectSearchRequestDTO supports: managersLogins, seniorManagersLogins,\n"
       "ownerLogin, employeeLogins + role filter (MANAGER, SENIOR_MANAGER, OWNER, MEMBER, OBSERVER).",
       "Medium", "API",
       "REQ-admin-projects", "ProjectController.search, ProjectSearchRequestDTO"),

    tc("TC-ADM-013",
       "Project API: PATCH triggers AlreadyExistsException handling",
       "Admin patching project with conflicting name.",
       "1. PATCH /api/ttt/v1/projects/{id} with name matching another project\n"
       "2. Verify error response contains conflicting project DTO",
       "Controller catches AlreadyExistsException.\n"
       "Converts existing conflicting object to DTO.\n"
       "Returns HTTP 409 with the conflicting project data.\n"
       "Design: provides conflicting entity for client-side conflict resolution.",
       "Medium", "Negative",
       "REQ-admin-projects", "ProjectController.patch",
       "AlreadyExistsException handling is unique to ProjectController"),

    tc("TC-ADM-014",
       "Project API: DELETE with object-level permission",
       "Admin attempting to delete a project.",
       "1. DELETE /api/ttt/v1/projects/{projectId} as admin\n"
       "2. Verify service checks ProjectPermissionService for DELETE\n"
       "3. DELETE as non-admin user without DELETE permission\n"
       "4. Verify rejection",
       "Step 1: Succeeds if user has DELETE permission on this specific project.\n"
       "Step 3: HTTP 403 — ProjectPermissionType.DELETE not granted.\n"
       "Design issue: Controller uses AUTHENTICATED_USER for DELETE endpoint —\n"
       "service-level guard (ProjectPermissionService) is the real security boundary.",
       "High", "Security",
       "REQ-admin-projects", "ProjectController.delete, ProjectPermissionService",
       "Controller @PreAuthorize allows any authenticated user — service layer enforces DELETE"),

    tc("TC-ADM-015",
       "Project enums: models, types, statuses",
       "Any authenticated user.",
       "1. GET /api/ttt/v1/projects/models — verify enum values\n"
       "2. GET /api/ttt/v1/projects/types — verify enum values\n"
       "3. GET /api/ttt/v1/projects/statuses — verify enum values",
       "Models: enum list returned.\n"
       "Types: COMMERCIAL, INTERNAL, ADMINISTRATION, PRODUCTION, etc. (9 values).\n"
       "Statuses: ACTIVE, FINISHED, UNCONFIRMED, SUSPENDED, ACCEPTANCE, WARRANTY, CANCELLED.\n"
       "No @PreAuthorize on these endpoints — publicly accessible to authenticated users.",
       "Low", "API",
       "REQ-admin-projects", "ProjectController"),

    tc("TC-ADM-016",
       "PM Tool sync: incremental sync runs on cron",
       "System cron configured with pmTool.sync.cron.",
       "1. Verify PmToolSyncScheduler runs incremental sync (fullSync=false)\n"
       "2. Check ShedLock entry for PmToolSyncScheduler.doPmToolSynchronization\n"
       "3. Verify rate limiter: 50 req/min default\n"
       "4. Verify page size: 100 entities per fetch",
       "Cron triggers PmToolSyncLauncher.sync(false).\n"
       "Incremental: updatedAfter = lastSucceeded.toLocalDate().\n"
       "Rate limiter (Guava): 50 req/min configurable.\n"
       "Page size: 100 entities. ShedLock-protected.",
       "High", "Functional",
       "REQ-pm-tool-sync", "PmToolSyncScheduler, PmToolEntitySyncLauncher"),

    tc("TC-ADM-017",
       "PM Tool sync: full sync vs incremental",
       "Admin triggering manual full sync.",
       "1. Trigger full sync (fullSync=true)\n"
       "2. Verify no updatedAfter date filter\n"
       "3. Compare with incremental (fullSync=false)\n"
       "4. Verify incremental uses lastSucceeded date",
       "Full sync: no date filter — processes ALL projects.\n"
       "Incremental: only projects updated since lastSucceeded.toLocalDate().\n"
       "Both use same rate limiter and page size.\n"
       "Full sync significantly slower due to volume.",
       "Medium", "Functional",
       "REQ-pm-tool-sync", "PmToolEntitySyncLauncher"),

    tc("TC-ADM-018",
       "PM Tool sync: field mapping and draft status conversion",
       "Project with 'draft' status in PM Tool.",
       "1. Sync project with status='draft' from PM Tool\n"
       "2. Verify TTT maps draft → ACTIVE\n"
       "3. Verify field mapping: name → name+accountingName, customer ← customerName,\n"
       "   model ← parseProjectModel(), type ← ProjectType.valueOf(uppercase)\n"
       "4. Verify preSalesIds joined with ','",
       "draft → ACTIVE (special case in PmToolProjectSynchronizer).\n"
       "name and accountingName both set to PM Tool project name.\n"
       "Type: uppercased before valueOf(). Status: uppercased except 'draft'.\n"
       "preSalesIds: ticket IDs joined with comma separator.",
       "Medium", "Functional",
       "REQ-pm-tool-sync", "PmToolProjectSynchronizer",
       "Draft → ACTIVE is a deliberate design decision, not a bug"),

    tc("TC-ADM-019",
       "PM Tool sync: sales filtering removes sales employees",
       "Project with sales-type references in PM, owner, supervisor, watchers.",
       "1. Sync project with sales employees assigned\n"
       "2. Verify removeSalesFromProject() removes all sales references\n"
       "3. Check PM, owner, supervisor, watchers fields post-sync",
       "Sales employees exist in PM Tool but not in TTT.\n"
       "removeSalesFromProject() strips sales from: PM, owner, supervisor, watchers.\n"
       "Null watcher entries also filtered out.",
       "Medium", "Functional",
       "REQ-pm-tool-sync", "PmToolProjectSynchronizer.removeSalesFromProject"),

    tc("TC-ADM-020",
       "PM Tool sync: missing employee validation triggers HTTP 500",
       "Project referencing a CompanyStaff ID that doesn't exist in TTT.",
       "1. Sync project with employee CS ID not in TTT\n"
       "2. Verify validateEmployeesExist() throws IllegalStateException\n"
       "3. Verify HTTP 500 error (not a proper business exception)",
       "IllegalStateException thrown with missing employee details.\n"
       "Results in HTTP 500 — no proper error handling.\n"
       "Design issue: should be a business exception with meaningful error code.",
       "High", "Negative",
       "REQ-pm-tool-sync", "PmToolProjectSynchronizer.validateEmployeesExist",
       "Design issue: IllegalStateException → HTTP 500 instead of business error"),

    tc("TC-ADM-021",
       "PM Tool sync: failed entity retry with batching",
       "Sync encounters timeout/error for some entities.",
       "1. Simulate entity sync timeout (TIMEOUT=10000ms)\n"
       "2. Verify failed entity ID saved to PmToolSyncFailedProjectRepository\n"
       "3. Verify retry in batches (configurable batch size, default 10)\n"
       "4. On retry success: verify removed from failed repository\n"
       "5. Verify PmToolSyncStatusRepository tracks status",
       "Failed entities stored and retried after main sync.\n"
       "Batch size: pmTool.sync.retry-batch-size (default 10).\n"
       "Timeout per entity: 10000ms.\n"
       "Successful retry removes from failed table. Status tracked.",
       "Medium", "Functional",
       "REQ-pm-tool-sync", "PmToolEntitySyncLauncher"),

    tc("TC-ADM-022",
       "PM Tool sync: cache eviction after project sync",
       "Project synced from PM Tool.",
       "1. Sync a project\n"
       "2. Verify projectService.evictFromCache() called\n"
       "3. Verify observer sync via batchChangeObservers()\n"
       "4. Verify postProcess() called after entities synced",
       "Cache evicted for each synced project.\n"
       "Observers batch-synced via InternalProjectObserverService.\n"
       "postProcess() called if any entities were synced.",
       "Low", "Functional",
       "REQ-pm-tool-sync", "PmToolProjectSynchronizer, InternalProjectObserverService"),
]

# ── TS-ADM-Employees (Employee Management) ──────────────────

TS_ADM_EMPLOYEES = [
    tc("TC-ADM-023",
       "Employees page: default view with search",
       "Logged in as admin. Navigate to /admin/employees.",
       "1. Verify two tabs: 'Employees' and 'Subcontractor'\n"
       "2. Verify Employees tab has ~20 pages of employees\n"
       "3. Verify Subcontractor tab has ~2 pages\n"
       "4. Search by employee name\n"
       "5. Toggle 'Show dismissed' checkbox",
       "Employees tab: paginated list (20/page).\n"
       "Subcontractor tab: separate listing.\n"
       "Page is entirely read-only — no create/edit/delete buttons.\n"
       "Employee data comes from CompanyStaff sync.\n"
       "Search filters by name. 'Show dismissed' adds inactive employees.",
       "High", "Functional",
       "REQ-admin-employees", "EmployeeController, AdminEmployeesPage"),

    tc("TC-ADM-024",
       "Employee API: search with role-based visibility",
       "Different users: admin, manager, regular employee.",
       "1. GET /api/ttt/v1/employees as admin — full list\n"
       "2. GET /api/ttt/v1/employees as manager — filtered list\n"
       "3. Verify searchSecured() applies role-based visibility\n"
       "4. Verify PageableUtil.correct() normalizes pagination",
       "Admin sees all employees.\n"
       "Manager/employee: searchSecured() limits visibility based on role.\n"
       "Pagination: PageableUtil.correct() normalizes page/size params.",
       "High", "Security",
       "REQ-admin-employees", "EmployeeController.search, EmployeeServiceImpl.searchSecured"),

    tc("TC-ADM-025",
       "Employee API: get current employee",
       "Any authenticated user.",
       "1. GET /api/ttt/v1/employees/current\n"
       "2. Verify response matches logged-in user data",
       "Returns current user's employee record.\n"
       "Requires EMPLOYEES_VIEW or AUTHENTICATED_USER authority.",
       "Medium", "Functional",
       "REQ-admin-employees", "EmployeeController.current"),

    tc("TC-ADM-026",
       "Employee API: get by login with @EmployeeLoginExists validation",
       "Admin querying employee by login.",
       "1. GET /api/ttt/v1/employees/{login} with valid login\n"
       "2. GET /api/ttt/v1/employees/{login} with non-existent login\n"
       "3. Verify @EmployeeLoginExists validator response",
       "Step 1: HTTP 200 with employee data.\n"
       "Step 2: HTTP 404 — @EmployeeLoginExists validation fails.\n"
       "Requires EMPLOYEES_VIEW or AUTHENTICATED_USER.",
       "Medium", "API",
       "REQ-admin-employees", "EmployeeController.find"),

    tc("TC-ADM-027",
       "Employee API: get work periods",
       "Admin querying employee work periods.",
       "1. GET /api/ttt/v1/employees/{login}/work-periods\n"
       "2. Verify work period entries with start/end dates\n"
       "3. Query for employee with multiple work periods (e.g., re-hired)",
       "Returns list of work period entries.\n"
       "Each entry has startDate, endDate (null if current).\n"
       "Re-hired employees have multiple entries.",
       "Medium", "Functional",
       "REQ-admin-employees", "EmployeeController.getWorkPeriods"),

    tc("TC-ADM-028",
       "Employee API: get roles",
       "Admin querying employee roles.",
       "1. GET /api/ttt/v1/employees/{login}/roles\n"
       "2. Verify role list for admin user\n"
       "3. Verify role list for regular employee\n"
       "4. Verify role list for accountant",
       "Returns list of roles assigned to the employee.\n"
       "Roles: employee, contractor, manager, department manager, accountant, admin.\n"
       "Requires EMPLOYEES_VIEW or AUTHENTICATED_USER.",
       "Medium", "Functional",
       "REQ-admin-employees", "EmployeeController.getRoles"),

    tc("TC-ADM-029",
       "BUG: Employee PATCH has no @PreAuthorize annotation",
       "Regular employee (non-admin) attempting to PATCH another employee.",
       "1. PATCH /api/ttt/v1/employees/{login} as regular employee\n"
       "2. Verify whether request is blocked or processed\n"
       "3. Compare with other endpoints that have @PreAuthorize",
       "Design issue: PATCH /{login} has no @PreAuthorize annotation.\n"
       "Relies entirely on service-level security.\n"
       "All other employee endpoints have explicit EMPLOYEES_VIEW/AUTHENTICATED_USER.\n"
       "Test: does service layer properly reject unauthorized PATCH?",
       "Critical", "Security",
       "BUG-ADM-EMPATCH", "EmployeeController.patch",
       "Missing @PreAuthorize — inconsistent with all other employee endpoints"),

    tc("TC-ADM-030",
       "CompanyStaff sync: employee data synchronization",
       "System cron running CS sync.",
       "1. Verify CSSynchronizer periodic sync\n"
       "2. Check employee data after sync: name, department, office, status\n"
       "3. Verify dismissed employees marked correctly\n"
       "4. Verify new employees appear after sync",
       "TTT imports employees from CompanyStaff — no local create/delete.\n"
       "PATCH is the only employee mutation in TTT.\n"
       "CS sync updates: name, department, salary office, active status.\n"
       "ShedLock-protected.",
       "High", "Functional",
       "REQ-admin-employees", "CSSynchronizer",
       "Employees are CS-managed — TTT has no employee CRUD"),

    tc("TC-ADM-031",
       "Employee search: keyboard layout auto-correction",
       "Admin searching employees.",
       "1. Search with RU keyboard layout for an EN name\n"
       "2. Verify SuggestionMappingUtil.correctLayout() auto-corrects\n"
       "3. Verify results match expected employee",
       "Layout correction works for employee search.\n"
       "Same SuggestionMappingUtil used in project search.\n"
       "Corrects RU → EN and EN → RU keyboard input.",
       "Low", "Functional",
       "REQ-admin-employees", "EmployeeController.search, SuggestionMappingUtil"),
]

# ── TS-ADM-Calendars (Production Calendar Management) ────────

TS_ADM_CALENDARS = [
    tc("TC-ADM-032",
       "Calendar page: default view with year picker and calendar dropdown",
       "Admin on /admin/calendar.",
       "1. Navigate to Admin > Production calendars\n"
       "2. Verify two tabs: 'Setting up calendars' and 'Calendars for SO'\n"
       "3. Verify year picker defaults to current year\n"
       "4. Verify calendar dropdown (Russia shown by default)\n"
       "5. Verify event list shows non-standard days (e.g., 18 events for Russia 2026)",
       "Two tabs. Year picker + calendar dropdown.\n"
       "'Setting up calendars' shows event list: date, duration, reason.\n"
       "Events: holidays (0h), pre-holiday (7h), etc.\n"
       "'Add calendar' and 'Create event' buttons available.",
       "High", "Functional",
       "REQ-admin-calendars", "CalendarControllerV2, AdminCalendarPage"),

    tc("TC-ADM-033",
       "Calendar CRUD: create new calendar",
       "Admin or Chief Accountant. Navigate to /admin/calendar.",
       "1. Click 'Add calendar'\n"
       "2. Enter unique calendar name\n"
       "3. Submit\n"
       "4. Verify calendar appears in dropdown\n"
       "5. Try duplicate name — verify rejection",
       "Step 3: HTTP 201. Calendar created with audit fields (createdAt, createdBy).\n"
       "Step 5: @CalendarNameExists validator rejects duplicate.\n"
       "Frontend: case-insensitive uniqueness check (Yup calendarExists test).\n"
       "Backend: uniqueness check via CalendarNameExistsValidator.",
       "High", "Functional",
       "REQ-admin-calendars", "CalendarControllerV2.create, CalendarServiceImpl"),

    tc("TC-ADM-034",
       "Calendar CRUD: case sensitivity gap in name uniqueness",
       "Admin creating calendars.",
       "1. Create calendar 'TestCalendar'\n"
       "2. Try creating 'testcalendar' (lowercase)\n"
       "3. Frontend: case-insensitive check should reject\n"
       "4. Backend: check if CalendarNameExistsValidator is case-sensitive",
       "Frontend does case-insensitive check (Yup custom test).\n"
       "Backend CalendarNameExistsValidator may be case-sensitive.\n"
       "Gap: if backend is case-sensitive, bypass frontend creates near-duplicate.",
       "Medium", "Validation",
       "REQ-admin-calendars", "CalendarNameExistsValidator, AddCalendarValidationSchema",
       "Known gap: frontend case-insensitive but backend may be case-sensitive"),

    tc("TC-ADM-035",
       "Calendar CRUD: update calendar name",
       "Admin with existing calendar.",
       "1. Select calendar from dropdown\n"
       "2. PATCH /api/calendar/v2/calendars/{calendarId} with new name\n"
       "3. Verify name updated, updatedAt/By set\n"
       "4. Try updating to name of another existing calendar — verify conflict",
       "PATCH updates name and updatedAt/updatedBy.\n"
       "CalendarExistsValidator uses WebUtil.getPathValue('calendarId')\n"
       "to exclude current calendar from uniqueness check.\n"
       "Design issue: update() contains calendar.setId(calendar.getId()) — dead code.",
       "Medium", "Functional",
       "REQ-admin-calendars", "CalendarControllerV2.update, CalendarServiceImpl",
       "Design issue: redundant self-assignment in update()"),

    tc("TC-ADM-036",
       "Calendar CRUD: delete calendar",
       "Admin with existing calendar.",
       "1. DELETE /api/calendar/v2/calendars/{calendarId}\n"
       "2. Verify calendar removed from dropdown\n"
       "3. Verify @CalendarIdExists on non-existent calendarId → 404\n"
       "4. Try deleting calendar assigned to a salary office — verify behavior",
       "Step 1: HTTP 200/204. Calendar deleted.\n"
       "Step 3: @CalendarIdExists validator returns 404.\n"
       "Step 4: May fail if calendar has active salary office assignments (FK constraint).",
       "Medium", "Negative",
       "REQ-admin-calendars", "CalendarControllerV2.delete"),

    tc("TC-ADM-037",
       "Calendar CRUD: permission check — ADMIN or CHIEF_ACCOUNTANT only",
       "Regular employee, manager, accountant (non-chief).",
       "1. POST calendar create as regular employee — verify 403\n"
       "2. PATCH calendar update as manager — verify 403\n"
       "3. DELETE calendar as regular accountant — verify 403\n"
       "4. GET calendars as any CALENDAR_VIEW user — verify 200\n"
       "5. Verify role naming: hasAnyRole('ADMIN', 'ROLE_CHIEF_ACCOUNTANT')",
       "Create/Update/Delete: restricted to ADMIN or CHIEF_ACCOUNTANT.\n"
       "GET (list): available to any user with CALENDAR_VIEW.\n"
       "Design issue: inconsistent role naming — 'ADMIN' vs 'ROLE_CHIEF_ACCOUNTANT'.",
       "High", "Security",
       "REQ-admin-calendars", "CalendarControllerV2",
       "Inconsistent role naming: 'ADMIN' (no prefix) vs 'ROLE_CHIEF_ACCOUNTANT'"),

    tc("TC-ADM-038",
       "Calendar events: create event with validation",
       "Admin on /admin/calendar. Calendar selected.",
       "1. Click 'Create event'\n"
       "2. Set date (YYYY-MM-DD), duration (0-12), reason (min 1 char)\n"
       "3. Submit and verify event appears in list\n"
       "4. Verify @DateUniqueOnCreate — duplicate date in same calendar rejected\n"
       "5. Test boundary: duration=0 (holiday), duration=12 (max), duration=13 (invalid)",
       "Event created with CalendarUpdatedEvent published.\n"
       "Validation: calendarId exists, date not null, duration 0-12 (@Min(0)/@Max(12)),\n"
       "reason not null + min 1 char, date unique per calendar.\n"
       "duration=13: HTTP 400. duration=-1: HTTP 400.",
       "High", "Functional",
       "REQ-admin-calendars", "CalendarDaysController.create, CalendarDaysCreateRequestDTO"),

    tc("TC-ADM-039",
       "Calendar events: PATCH only updates reason (asymmetric update)",
       "Admin with existing calendar event.",
       "1. PATCH /api/calendar/v2/days/{dayId} with new reason\n"
       "2. Verify reason updated\n"
       "3. PATCH with new duration — verify duration NOT updated\n"
       "4. PATCH with new date — verify date NOT updated\n"
       "5. PATCH with empty reason — verify @Size(min=1) validation",
       "Only reason field can be patched.\n"
       "CalendarDaysPatchRequestDTO only has reason with @Size(min=1).\n"
       "Design issue: duration and date are immutable after creation.\n"
       "To change duration/date: delete + re-create.",
       "Medium", "Functional",
       "REQ-admin-calendars", "CalendarDaysController.patch, CalendarDaysPatchRequestDTO",
       "Design asymmetry: PATCH only updates reason, not duration/date"),

    tc("TC-ADM-040",
       "Calendar events: delete triggers cascade to vacation service",
       "Admin deleting a calendar event that affects existing absences.",
       "1. DELETE /api/calendar/v2/days/{dayId}\n"
       "2. Verify CalendarUpdatedEvent published (with diff calculation)\n"
       "3. Verify CalendarDeletedEvent published\n"
       "4. Verify vacation service handles cascade: day-off deletion, vacation day recalculation",
       "Delete publishes both CalendarUpdatedEvent and CalendarDeletedEvent.\n"
       "CalendarDeletedEvent triggers absence conflict resolution in vacation service.\n"
       "Cascade: existing vacations/day-offs may be affected by calendar change.",
       "High", "Functional",
       "REQ-admin-calendars", "CalendarDaysController.delete, CalendarDaysServiceImpl",
       "Cross-service cascade: calendar → vacation service for absence conflict resolution"),

    tc("TC-ADM-041",
       "Calendar events: findByDate returns null instead of 404",
       "API user querying calendar day by date.",
       "1. GET /api/calendar/v2/days/by-date?date=2026-03-15&calendarId=1\n"
       "2. Verify response for existing date\n"
       "3. GET with date that has no event\n"
       "4. Verify null/empty response (not 404)",
       "Existing date: HTTP 200 with calendar day data.\n"
       "Non-existent date: returns null/empty body — NOT 404.\n"
       "Design issue: inconsistent REST convention. Client must handle null response.",
       "Low", "API",
       "REQ-admin-calendars", "CalendarDaysController.findByDate",
       "Design issue: returns null instead of 404 for missing entries"),

    tc("TC-ADM-042",
       "Working days calculation: base + holiday compensation",
       "Calendar with holidays and pre-holidays for a given period.",
       "1. Query working days for a month with known holidays\n"
       "2. Verify base calculation: Mon-Fri working days in period\n"
       "3. Verify holiday compensation: hours adjustment from calendar entries\n"
       "4. Verify weekend compensation: working weekends, non-working weekdays\n"
       "5. Test cross-year period (e.g., Dec 2025 - Jan 2026)",
       "calculateWorkingDaysInPeriod():\n"
       "1. Base working days = Mon-Fri count.\n"
       "2. Holiday compensation = sum of hour adjustments.\n"
       "3. Weekend compensation = working weekends added, non-working weekdays removed.\n"
       "Constants: DAYS_IN_WEEK=7, WORKING_DAYS_IN_WEEK=5, START_WEEK_COMPENSATION=8.\n"
       "Cross-year: queries different calendars per year via OfficeCalendar mapping.",
       "High", "Functional",
       "REQ-admin-calendars", "CalendarDaysServiceImpl.calculateWorkingDaysInPeriod"),

    tc("TC-ADM-043",
       "Salary office calendar mapping (Calendars for SO tab)",
       "Admin on /admin/calendar > 'Calendars for SO' tab.",
       "1. View salary office → calendar mapping\n"
       "2. Verify each salary office has an assigned calendar\n"
       "3. Verify RUSSIAN_CALENDAR_ID is the default",
       "Calendars for SO tab shows office → calendar assignments.\n"
       "Design issue: RUSSIAN_CALENDAR_ID hardcoded as default.\n"
       "Each office can be assigned a different production calendar.",
       "Medium", "Functional",
       "REQ-admin-calendars", "CalendarDaysServiceImpl, OfficeCalendar",
       "Legacy: RUSSIAN_CALENDAR_ID hardcoded constant"),

    tc("TC-ADM-044",
       "Calendar event: date format and timezone handling",
       "Admin creating calendar event with various date formats.",
       "1. POST event with date=2026-03-15 (ISO 8601)\n"
       "2. POST event with date including time info (e.g., 2026-03-15T10:00:00)\n"
       "3. Verify time/timezone information is ignored per Javadoc",
       "Date format: yyyy-MM-dd (LocalDate).\n"
       "Javadoc: 'All time and timezone information will be ignored.'\n"
       "Only date portion used.",
       "Low", "Validation",
       "REQ-admin-calendars", "CalendarDaysController"),
]

# ── TS-ADM-Settings (TTT Parameters, API, Export, Account) ───

TS_ADM_SETTINGS = [
    tc("TC-ADM-045",
       "TTT Parameters page: view and edit 18 settings",
       "Admin on /admin/settings.",
       "1. Navigate to Admin > TTT parameters\n"
       "2. Verify 18 key-value parameters displayed\n"
       "3. Edit: task autocomplete ranges (30/90/180 days)\n"
       "4. Edit: notification email threshold (over: 10%, under: -10%)\n"
       "5. Edit: extended period duration (60 min)\n"
       "6. Save and verify persistence",
       "18 editable parameters including:\n"
       "- Task autocomplete ranges (30/90/180)\n"
       "- Notification emails and thresholds (over: 10%, under: -10%)\n"
       "- Extended period duration (60 min)\n"
       "- CSV export settings, presales URL\n"
       "- Budget notification last handled timestamp.\n"
       "Admin-only access.",
       "High", "Functional",
       "REQ-admin-settings", "SettingsController, AdminSettingsPage"),

    tc("TC-ADM-046",
       "API page: view API keys and permissions",
       "Admin on /admin/api.",
       "1. Navigate to Admin > API\n"
       "2. Verify 12 API keys listed\n"
       "3. Verify each key shows: Name, Creator, UUID value, Allowed API methods\n"
       "4. Verify 22 permission types: PROJECTS_ALL, VACATIONS_EDIT, TASKS_EDIT, etc.\n"
       "5. Verify notable keys: Autotest, Companystaff-vacations, Google-apps, InvoicingProd",
       "12 API keys displayed.\n"
       "Each key: name, creator, UUID, method permissions.\n"
       "22 permission types available.\n"
       "Key management for integrations with external systems.",
       "Medium", "Functional",
       "REQ-admin-api", "ApiKeyController, AdminAPIPage"),

    tc("TC-ADM-047",
       "Export page: download highest hours by customer CSV",
       "Admin on /admin/export.",
       "1. Navigate to Admin > Export\n"
       "2. Set date range\n"
       "3. Click 'Download CSV'\n"
       "4. Verify CSV file downloaded with customer data",
       "Single-purpose page: 'Highest number of hours by customer'.\n"
       "Date range picker → CSV download.\n"
       "CSV contains hours-per-customer summary for selected period.",
       "Medium", "Functional",
       "REQ-admin-export", "ExportController, AdminExportPage"),

    tc("TC-ADM-048",
       "User Account: General tab — API token and task carry-over",
       "Any user on /admin/account > General tab.",
       "1. Navigate to user icon > Account\n"
       "2. Verify General tab: API token section, task carry-over setting\n"
       "3. Generate new API token\n"
       "4. Toggle task carry-over\n"
       "5. Verify persistence after page refresh",
       "General tab contains:\n"
       "- Personal API token (generate/regenerate)\n"
       "- Task carry-over toggle (auto-copy tasks to next period).\n"
       "Available to all authenticated users, not admin-only.",
       "Medium", "Functional",
       "REQ-admin-account", "AccountController, AdminAccountPage"),

    tc("TC-ADM-049",
       "User Account: Export tab — CSV format settings",
       "Any user on /admin/account > Export tab.",
       "1. Navigate to Account > Export tab\n"
       "2. Verify decimal separator settings\n"
       "3. Verify value separator settings\n"
       "4. Change settings and verify CSV output format changes",
       "Export tab settings control CSV format:\n"
       "- Decimal separator types (from DecimalSeparatorType enum)\n"
       "- Value separator types (from ValSeparatorType enum)\n"
       "Available to all users for personal CSV export preferences.",
       "Low", "Functional",
       "REQ-admin-account", "AccountController",
       "Uses DecimalSeparatorType and ValSeparatorType enums from /api/ttt API"),
]

# ── TS-ADM-Trackers (Tracker Integration) ────────────────────

TS_ADM_TRACKERS = [
    tc("TC-ADM-050",
       "User Account: Trackers tab — view configured trackers",
       "User on /admin/account > Trackers tab.",
       "1. Navigate to Account > Trackers tab\n"
       "2. Verify list of configured tracker credentials\n"
       "3. Verify supported types: GITLAB, REDMINE, JIRA_TOKEN, JIRA_LOGPASS,\n"
       "   ASANA, CLICK_UP, PRESALES, YOU_TRACK",
       "Trackers tab shows per-user tracker configurations.\n"
       "8 tracker types defined in enum.\n"
       "Live data: 19 credentials for 14 employees.\n"
       "Distribution: GITLAB(7), JIRA_LOGPASS(5), REDMINE(2), CLICK_UP(2),\n"
       "JIRA_TOKEN(2), PRESALES(1). No ASANA or YOU_TRACK credentials in use.",
       "Medium", "Functional",
       "REQ-admin-trackers", "EmployeeTrackerCredentialsController, AdminTrackersTab"),

    tc("TC-ADM-051",
       "Tracker credentials: create with connectivity validation",
       "User on Trackers tab. No existing credential for target tracker.",
       "1. Click 'Add tracker'\n"
       "2. Select type (e.g., GITLAB)\n"
       "3. Enter tracker URL (required, trimmed)\n"
       "4. Enter credentials (required for GITLAB, REDMINE, YOU_TRACK, JIRA_TOKEN)\n"
       "5. Submit — verify getCurrentUser() connectivity check\n"
       "6. Verify credential stored encrypted in employee_tracker_credentials table",
       "POST /api/ttt/v1/employees/current/settings/trackers.\n"
       "Validates via getCurrentUser() on the external tracker.\n"
       "If tracker unreachable: TRACKER_NOT_AVAILABLE error.\n"
       "If auth fails: TRACKER_NOT_AUTHORIZED error.\n"
       "Credentials stored encrypted in DB.",
       "High", "Functional",
       "REQ-admin-trackers", "EmployeeTrackerCredentialsController, TrackerClientFactory"),

    tc("TC-ADM-052",
       "Tracker credentials: conditional field requirements by type",
       "User creating tracker credentials for each type.",
       "1. Type=JIRA_LOGPASS: verify login + password required (no credentials field)\n"
       "2. Type=JIRA_TOKEN: verify login + credentials required (no password)\n"
       "3. Type=GITLAB: verify credentials required (no login, no password)\n"
       "4. Type=REDMINE: verify credentials required\n"
       "5. Type=YOU_TRACK: verify credentials required\n"
       "6. Type=CLICK_UP: verify credentials required\n"
       "7. Type=PRESALES: verify URL required only",
       "Frontend TrackerValidationSchema conditional logic:\n"
       "- login: required for JIRA_TOKEN, JIRA_LOGPASS\n"
       "- credentials: required for GITLAB, REDMINE, YOU_TRACK, JIRA_TOKEN\n"
       "- password: required only for JIRA_LOGPASS.\n"
       "TrackerEditValidationSchema: only enforces if value changed from initial.",
       "High", "Validation",
       "REQ-admin-trackers", "TrackerValidationSchema, TrackerEditValidationSchema"),

    tc("TC-ADM-053",
       "Tracker credentials: update with change detection",
       "User with existing tracker credential.",
       "1. Open edit for existing tracker\n"
       "2. Change only URL — verify no credential re-validation\n"
       "3. Change credentials — verify re-validation via getCurrentUser()\n"
       "4. Verify TrackerEditValidationSchema only enforces changed fields",
       "PATCH /api/ttt/v1/employees/current/settings/trackers.\n"
       "TrackerEditValidationSchema accepts initialValues — \n"
       "only enforces requirements on fields that differ from initial.\n"
       "Connectivity re-checked only if credentials changed.",
       "Medium", "Functional",
       "REQ-admin-trackers", "EmployeeTrackerCredentialsController"),

    tc("TC-ADM-054",
       "Tracker credentials: delete",
       "User with existing tracker credential.",
       "1. DELETE /api/ttt/v1/employees/current/settings/trackers\n"
       "2. Verify credential removed\n"
       "3. Verify encrypted data purged from employee_tracker_credentials table",
       "DELETE removes the credential entry.\n"
       "Only the current user can manage their own credentials.\n"
       "Existing work log data preserved (tracker_work_log table unaffected).",
       "Medium", "Functional",
       "REQ-admin-trackers", "EmployeeTrackerCredentialsController"),

    tc("TC-ADM-055",
       "Tracker error codes: all 9 error types",
       "User with various tracker misconfigurations.",
       "1. No tracker configured → TRACKER_NOT_CONFIGURED\n"
       "2. Tracker server down → TRACKER_NOT_AVAILABLE\n"
       "3. Invalid credentials → TRACKER_NOT_AUTHORIZED\n"
       "4. Insufficient permissions → TRACKER_NOT_PERMITTED\n"
       "5. HTTP URL (not HTTPS) → TRACKER_HTTPS_REQUIRED\n"
       "6. Unsupported tracker type → TRACKER_NOT_SUPPORTED\n"
       "7. Proxy issue → PROXY_NOT_AVAILABLE\n"
       "8. Unknown error → TRACKER_UNKNOWN\n"
       "9. Resource naming issue → TRACKER_RESOURCE_NAME",
       "9 distinct error codes returned by tracker integration.\n"
       "Each maps to specific conditions in TrackerClient implementations.\n"
       "TRACKER_HTTPS_REQUIRED: enforces secure connections.\n"
       "PROXY_NOT_AVAILABLE: proxy configuration for VPN-restricted trackers.",
       "High", "Negative",
       "REQ-admin-trackers", "TrackerClientFactory, TrackerErrorCodes"),

    tc("TC-ADM-056",
       "Tracker credential resolution: fallback chain",
       "Project with manager and owner tracker credentials.",
       "1. Current user has credentials → verify used directly\n"
       "2. Current user has no credentials, project manager has → verify PM fallback\n"
       "3. Neither user nor PM has credentials → verify owner fallback (read-only)\n"
       "4. None have credentials → verify TRACKER_NOT_CONFIGURED error",
       "Resolution chain: current user → project manager → project owner.\n"
       "Owner fallback is read-only (no work log push).\n"
       "IssueTrackerService handles credential resolution.",
       "Medium", "Functional",
       "REQ-admin-trackers", "IssueTrackerService"),

    tc("TC-ADM-057",
       "Work log sync: bidirectional TTT ↔ tracker",
       "Project with tracker configured. User with credentials.",
       "1. POST /api/ttt/v1/projects/{id}/tracker-work-log/sync with direction=TO_TRACKER\n"
       "2. Verify SendToTrackerCommand execution\n"
       "3. POST sync with direction=FROM_TRACKER\n"
       "4. Verify LoadFromTrackerCommand execution\n"
       "5. GET /api/ttt/v1/projects/{id}/tracker-work-log/info — verify sync status",
       "Bidirectional sync via Command pattern.\n"
       "TO_TRACKER: pushes TTT work logs to external tracker.\n"
       "FROM_TRACKER: pulls tracker work logs into TTT.\n"
       "TrackerSyncStartEvent/FinishEvent published for lifecycle.\n"
       "DB: 222K rows in tracker_work_log, 41K unique tasks.",
       "High", "Functional",
       "REQ-admin-trackers", "ProjectTrackerWorkLogServiceImpl, Command pattern"),

    tc("TC-ADM-058",
       "GraalVM custom scripts: task mapping sandbox",
       "Project with custom taskNameScript configured.",
       "1. Verify CustomScriptService executes taskNameScript in GraalVM sandbox\n"
       "2. Verify beforeScript.js blocks: while, for, do, goto loops\n"
       "3. Verify Java reflection blocked (ILLEGAL_JAVA_CALL_ERROR)\n"
       "4. Verify host access blocked\n"
       "5. Test boundEmployeeScript and workLogScript execution",
       "3 script types: taskNameScript, boundEmployeeScript, workLogScript.\n"
       "GraalVM JavaScript sandbox with security:\n"
       "- Loop prevention via string matching (not AST)\n"
       "- Java interop blocked\n"
       "- Host access blocked.\n"
       "Error codes: ILLEGAL_OPERATOR_ERROR, ILLEGAL_FUNCTION_CALL_ERROR, ILLEGAL_JAVA_CALL_ERROR.",
       "High", "Security",
       "REQ-admin-trackers", "CustomScriptService, GraalVM sandbox",
       "Design issue: loop prevention via string matching is fragile — not AST-based"),

    tc("TC-ADM-059",
       "Tracker type: ASANA listed but not implemented",
       "User attempting to configure ASANA tracker.",
       "1. Verify ASANA exists in EmployeeTrackerCredentialsType enum\n"
       "2. Try creating ASANA credential\n"
       "3. Verify behavior (error or phantom success)",
       "ASANA enum value exists but Confluence says 'NOT supported'.\n"
       "No ASANATrackerClient implementation found.\n"
       "TrackerClientFactory may throw TRACKER_NOT_SUPPORTED.\n"
       "No ASANA or YOU_TRACK credentials exist in live data.",
       "Low", "Negative",
       "REQ-admin-trackers", "EmployeeTrackerCredentialsType, TrackerClientFactory",
       "Design issue: enum value for unsupported tracker type"),

    tc("TC-ADM-060",
       "Admin project: Edit Tracker Data validation",
       "Admin editing tracker data for a project.",
       "1. Enter invalid URL in 'Link to task tracker' field\n"
       "2. Verify IsUrl validator rejects non-URL\n"
       "3. Verify OnlyEnAndNumbers regex: /^[a-zA-Z0-9.]*$/g\n"
       "4. Verify LessThanTwoChars: length >= 2\n"
       "5. Enter URL without https:// prefix",
       "Frontend admin validators (validation.js):\n"
       "- Required: non-empty\n"
       "- OnlyEnAndNumbers: /^[a-zA-Z0-9.]*$/g\n"
       "- LessThanTwoChars: minimum 2 characters\n"
       "- IsUrl: domain/path regex\n"
       "- IsSelect: object with label+value OR string.",
       "Medium", "Validation",
       "REQ-admin-trackers", "AdminProjectTrackerValidation"),
]

# ── TS-ADM-APIErrors (API Errors & Permissions) ─────────────

TS_ADM_APIERRORS = [
    tc("TC-ADM-061",
       "Permission hierarchy: PROJECTS_ALL vs AUTHENTICATED_USER",
       "Users with different authority levels.",
       "1. GET /api/ttt/v1/projects as AUTHENTICATED_USER — verify access\n"
       "2. GET /api/ttt/v1/projects as PROJECTS_ALL — verify access\n"
       "3. DELETE project as AUTHENTICATED_USER (no DELETE permission) — verify service rejection\n"
       "4. Verify controller @PreAuthorize allows both, service layer enforces",
       "Controller uses PROJECTS_ALL or AUTHENTICATED_USER for all endpoints.\n"
       "Service layer provides real security: PermissionClassType.PROJECTS VIEW.\n"
       "Design issue: AUTHENTICATED_USER on DELETE endpoint — service guard critical.",
       "High", "Security",
       "REQ-admin-permissions", "ProjectController, ProjectPermissionService"),

    tc("TC-ADM-062",
       "Calendar API: unauthorized access attempts",
       "Regular employee (no ADMIN/CHIEF_ACCOUNTANT role).",
       "1. POST calendar create as employee — verify 403\n"
       "2. PATCH calendar update as employee — verify 403\n"
       "3. DELETE calendar as employee — verify 403\n"
       "4. GET calendar list as employee with CALENDAR_VIEW — verify 200",
       "Create/Update/Delete: ADMIN or CHIEF_ACCOUNTANT only → HTTP 403 for others.\n"
       "GET: CALENDAR_VIEW authority required → 200 for authorized viewers.\n"
       "hasAnyRole('ADMIN', 'ROLE_CHIEF_ACCOUNTANT') guard.",
       "High", "Security",
       "REQ-admin-permissions", "CalendarControllerV2"),

    tc("TC-ADM-063",
       "Calendar day: @CalendarDaysIdExists validation",
       "API user referencing non-existent day ID.",
       "1. PATCH /api/calendar/v2/days/99999 — verify 404\n"
       "2. DELETE /api/calendar/v2/days/99999 — verify 404\n"
       "3. Verify @CalendarDaysIdExists validator message",
       "@CalendarDaysIdExists validator checks dayId path variable.\n"
       "Non-existent: HTTP 404 with validation error.\n"
       "Applied to both PATCH and DELETE endpoints.",
       "Medium", "Validation",
       "REQ-admin-permissions", "CalendarDaysController"),

    tc("TC-ADM-064",
       "Calendar day: @DateUniqueOnCreate — duplicate date rejection",
       "Admin creating event with same date as existing event in same calendar.",
       "1. Create event for 2026-01-01 in calendar 'Russia'\n"
       "2. Try creating another event for 2026-01-01 in same calendar\n"
       "3. Verify @DateUniqueOnCreate validator rejects duplicate\n"
       "4. Create event for 2026-01-01 in different calendar — verify accepted",
       "Step 2: HTTP 400 — date must be unique per calendar.\n"
       "Step 4: HTTP 201 — uniqueness is per-calendar, not global.\n"
       "@DateUniqueOnCreate is class-level validator on CalendarDaysCreateRequestDTO.",
       "High", "Validation",
       "REQ-admin-calendars", "CalendarDaysCreateRequestDTO, DateUniqueOnCreateValidator"),

    tc("TC-ADM-065",
       "Salary office period: DatePeriod validation edge cases",
       "Admin managing salary office period assignments.",
       "1. PUT period with startDate > endDate — verify @DatePeriodValid rejects\n"
       "2. PUT period with startDate = endDate — verify accepted (same day period)\n"
       "3. PUT period with both dates null — verify accepted (null pass-through)\n"
       "4. PUT period with one date null, one set — verify accepted",
       "DatePeriodValidValidator: validates endDate >= startDate only if BOTH non-null.\n"
       "If either is null, validation passes (no constraint).\n"
       "Null pass-through is intentional — partial period assignment allowed.\n"
       "@OfficeIdExists and @CalendarIdExists validators also applied.",
       "Medium", "Validation",
       "REQ-admin-calendars", "PeriodRequestDTO, DatePeriodValidValidator",
       "DatePeriod null pass-through: both null → passes validation"),

    tc("TC-ADM-066",
       "Project API: @ProjectIdExists validation",
       "API user with non-existent project ID.",
       "1. GET /api/ttt/v1/projects/99999 — verify 404\n"
       "2. PATCH /api/ttt/v1/projects/99999 — verify 404\n"
       "3. DELETE /api/ttt/v1/projects/99999 — verify 404\n"
       "4. Verify @ProjectIdExists validator error message format",
       "@ProjectIdExists validator on projectId path variable.\n"
       "All CRUD endpoints validate project existence first.\n"
       "HTTP 404 with validation error for non-existent IDs.",
       "Medium", "Validation",
       "REQ-admin-projects", "ProjectController"),

    tc("TC-ADM-067",
       "Employee API: @EmployeeLoginExists validation",
       "API user with non-existent employee login.",
       "1. GET /api/ttt/v1/employees/nonexistent_user — verify 404\n"
       "2. PATCH /api/ttt/v1/employees/nonexistent_user — verify 404\n"
       "3. GET /api/ttt/v1/employees/nonexistent_user/roles — verify 404\n"
       "4. GET /api/ttt/v1/employees/nonexistent_user/work-periods — verify 404",
       "@EmployeeLoginExists validator on login path variable.\n"
       "All endpoints with {login} parameter validate existence.\n"
       "HTTP 404 for non-existent employee logins.",
       "Medium", "Validation",
       "REQ-admin-employees", "EmployeeController"),

    tc("TC-ADM-068",
       "Calendar event validation: boundary values for duration field",
       "Admin creating calendar events with edge-case durations.",
       "1. POST event with duration=0 (holiday) — verify accepted\n"
       "2. POST event with duration=12 (max) — verify accepted\n"
       "3. POST event with duration=13 — verify rejected (@Max(12))\n"
       "4. POST event with duration=-1 — verify rejected (@Min(0))\n"
       "5. POST event with duration=null — verify rejected (@NotNull)\n"
       "6. POST event with duration=7 (typical pre-holiday) — verify accepted",
       "Duration validation: @NotNull, @Min(0), @Max(12).\n"
       "Valid range: 0-12 inclusive.\n"
       "0 = holiday (full non-working day).\n"
       "7 = typical pre-holiday (reduced day).\n"
       "12 = theoretical max.\n"
       "null, negative, >12: HTTP 400.",
       "High", "Boundary",
       "REQ-admin-calendars", "CalendarDaysCreateRequestDTO"),

    tc("TC-ADM-069",
       "Calendar event validation: reason field boundary",
       "Admin creating/patching calendar events with edge-case reasons.",
       "1. POST event with reason='' (empty) — verify rejected (@Size(min=1))\n"
       "2. POST event with reason=null — verify rejected (@NotNull)\n"
       "3. POST event with reason='X' (1 char) — verify accepted\n"
       "4. PATCH event with reason='' — verify rejected (@Size(min=1))\n"
       "5. PATCH event without reason field — verify accepted (optional on PATCH)",
       "Create: reason is @NotNull + @Size(min=1) — required, min 1 char.\n"
       "Patch: reason is @Size(min=1) only — optional, but if provided must be 1+ chars.\n"
       "No max length constraint found — test very long reasons.",
       "Medium", "Boundary",
       "REQ-admin-calendars", "CalendarDaysCreateRequestDTO, CalendarDaysPatchRequestDTO"),

    tc("TC-ADM-070",
       "Office management: synced from CompanyStaff (no local CRUD)",
       "Admin attempting office operations.",
       "1. Verify no office create/delete endpoints in OfficeController\n"
       "2. Verify offices synced via CSSalaryOfficeSynchronizer\n"
       "3. Check sync runs in 3 services: TTT, vacation, calendar\n"
       "4. Verify office search/suggest endpoints available",
       "Offices are managed externally in CompanyStaff.\n"
       "CSSalaryOfficeSynchronizer runs in TTT, vacation, and calendar services.\n"
       "OfficeController provides: period management, employee extended periods,\n"
       "suggestion/search — but no create/delete.\n"
       "Period endpoints covered in accounting test suite (TS-ACC-Periods).",
       "Low", "Functional",
       "REQ-admin-offices", "OfficeController, CSSalaryOfficeSynchronizer",
       "Cross-reference: TS-ACC-Periods covers period management endpoints"),
]


# =====================================================================
# SUITE REGISTRY
# =====================================================================

SUITES = [
    ("TS-ADM-Projects", "Project Management", TS_ADM_PROJECTS),
    ("TS-ADM-Employees", "Employee Management", TS_ADM_EMPLOYEES),
    ("TS-ADM-Calendars", "Production Calendar Management", TS_ADM_CALENDARS),
    ("TS-ADM-Settings", "TTT Settings, API Keys & Account", TS_ADM_SETTINGS),
    ("TS-ADM-Trackers", "Tracker Integration", TS_ADM_TRACKERS),
    ("TS-ADM-APIErrors", "API Errors & Permissions", TS_ADM_APIERRORS),
]

TOTAL_CASES = sum(len(s[2]) for s in SUITES)


# =====================================================================
# WORKBOOK GENERATION
# =====================================================================

def build_plan_overview(wb):
    ws = wb.active
    ws.title = "Plan Overview"
    ws.sheet_properties.tabColor = TAB_COLOR_PLAN

    # Title
    ws.merge_cells("A1:J1")
    title = ws.cell(row=1, column=1, value="Administration Module — Test Plan")
    title.font = FONT_TITLE
    title.alignment = ALIGN_LEFT_CENTER

    ws.merge_cells("A2:J2")
    subtitle = ws.cell(row=2, column=1,
                       value=f"Generated {datetime.now().strftime('%Y-%m-%d')} | "
                             f"{TOTAL_CASES} test cases | 6 suites | TTT Expert System Session 62")
    subtitle.font = FONT_SMALL

    # Scope section
    row = 4
    ws.cell(row=row, column=1, value="Scope & Objectives").font = FONT_SECTION
    ws.cell(row=row, column=1).fill = FILL_SECTION
    ws.merge_cells(f"A{row}:J{row}")

    scope_items = [
        ("Scope", "Administration features of the TTT application: project management (search, detail, "
                   "templates, tracker data), employee management (search, roles, work periods, CS sync), "
                   "production calendars (CRUD, events, working day calculations, SO mapping), "
                   "TTT settings/API keys/export, tracker integration (credentials, work log sync, "
                   "GraalVM scripts), and cross-cutting admin API permissions."),
        ("Objectives", "Verify all admin CRUD operations, permission boundaries (ADMIN, CHIEF_ACCOUNTANT, "
                       "AUTHENTICATED_USER), PM Tool sync correctness, calendar event cascade effects, "
                       "tracker credential lifecycle, and validation rules including known design issues."),
        ("Approach", "Combined UI (Playwright), API (Swagger/curl), and DB (PostgreSQL) testing. "
                     "UI-level testing for admin pages; API testing for all REST endpoints; "
                     "DB verification for sync operations and audit trails."),
        ("Environments", "Primary: timemachine (dev). Secondary: qa-1. Prod-like: stage.\n"
                         "App URL: https://ttt-{env}.noveogroup.com\n"
                         "Admin user: perekrest (full admin access)"),
        ("Known Limitations", "1. Projects are read-only in TTT (managed via PM Tool)\n"
                              "2. Employees imported from CompanyStaff — no local CRUD\n"
                              "3. Offices synced from CS — no create/delete\n"
                              "4. ASANA tracker type: enum exists but not implemented\n"
                              "5. GraalVM sandbox: loop prevention via string matching (fragile)"),
    ]

    for i, (label, text) in enumerate(scope_items):
        r = row + 1 + i
        ws.cell(row=r, column=1, value=label).font = FONT_SECTION
        ws.cell(row=r, column=2, value=text).font = FONT_BODY
        ws.cell(row=r, column=2).alignment = ALIGN_LEFT
        ws.merge_cells(f"B{r}:J{r}")

    # Suite links section
    row = row + 1 + len(scope_items) + 1
    ws.cell(row=row, column=1, value="Test Suites").font = FONT_SECTION
    ws.cell(row=row, column=1).fill = FILL_SECTION
    ws.merge_cells(f"A{row}:J{row}")

    headers = ["Suite ID", "Suite Name", "Cases", "Focus Area"]
    row += 1
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_GREEN_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    focus_areas = [
        "Project search/filter, detail dialog, tracker data editing, task templates, "
        "PM Tool sync, project permissions, enum endpoints",
        "Employee search with role-based visibility, CS sync, PATCH security gap, "
        "work periods, roles, keyboard layout correction",
        "Calendar CRUD with name uniqueness, event CRUD with cascade, working day "
        "calculations, SO mapping, date/duration validation, cross-year handling",
        "TTT parameters (18 settings), API key management (12 keys, 22 permissions), "
        "CSV export, user account settings (token, trackers, export format)",
        "8 tracker types, credential CRUD with connectivity validation, conditional "
        "field requirements, work log sync, GraalVM sandbox, error codes",
        "Permission hierarchy tests, validator coverage (@ProjectIdExists, "
        "@EmployeeLoginExists, @CalendarIdExists, @DateUniqueOnCreate), "
        "boundary values, date period validation",
    ]

    for i, (sid, sname, cases) in enumerate(SUITES):
        r = row + 1 + i
        fill = FILL_ROW_EVEN if i % 2 == 0 else FILL_ROW_ODD
        link_cell = ws.cell(row=r, column=1, value=sid)
        link_cell.font = FONT_LINK_BOLD
        link_cell.hyperlink = f"#'{sid}'!A1"
        link_cell.border = THIN_BORDER
        if fill:
            link_cell.fill = fill

        for col, val in enumerate([sname, len(cases), focus_areas[i]], 2):
            cell = ws.cell(row=r, column=col, value=val)
            cell.font = FONT_BODY
            cell.alignment = ALIGN_LEFT
            cell.border = THIN_BORDER
            if fill:
                cell.fill = fill

    # Knowledge sources
    row = row + 1 + len(SUITES) + 1
    ws.cell(row=row, column=1, value="Knowledge Sources").font = FONT_SECTION
    ws.cell(row=row, column=1).fill = FILL_SECTION
    ws.merge_cells(f"A{row}:J{row}")

    sources = [
        "modules/admin-panel-deep-dive.md — Full code analysis: ProjectController, EmployeeController, "
        "CalendarControllerV2, PM Tool sync, 10 design issues",
        "analysis/admin-calendar-form-validation-rules.md — Field-level DTO validation for calendars, "
        "events, salary offices, tracker configuration",
        "exploration/ui-flows/admin-panel-pages.md — 7 admin pages: Projects, Employees, TTT Parameters, "
        "Calendars, API, Export, Account",
        "exploration/ui-flows/admin-projects-deep-exploration.md — Project page deep testing: search, "
        "filters, detail dialog, tracker data, task templates",
        "investigations/tracker-integration-deep-dive.md — 8 tracker types, GraalVM sandbox, work log "
        "sync, 222K DB rows, 19 credentials",
        "Qase TIMEREPORT: 0 existing admin panel test cases (no overlap)",
    ]
    for i, src in enumerate(sources):
        r = row + 1 + i
        ws.cell(row=r, column=1, value=f"  {i+1}.").font = FONT_BODY
        ws.cell(row=r, column=2, value=src).font = FONT_BODY
        ws.cell(row=r, column=2).alignment = ALIGN_LEFT
        ws.merge_cells(f"B{r}:J{r}")

    # Column widths
    ws.column_dimensions["A"].width = 20
    for col in "BCDEFGHIJ":
        ws.column_dimensions[col].width = 18
    ws.column_dimensions["B"].width = 45
    ws.column_dimensions["D"].width = 60


def build_feature_matrix(wb):
    ws = wb.create_sheet("Feature Matrix")
    ws.sheet_properties.tabColor = TAB_COLOR_PLAN

    ws.cell(row=1, column=1, value="Feature × Test Type Matrix").font = FONT_TITLE
    ws.merge_cells("A1:I1")

    headers = ["Feature Area", "Functional", "Validation", "Security",
               "API", "Boundary", "Negative", "Bug Verification", "Total"]
    row = 3
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_GREEN_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    # Count by feature and type
    features = {
        "Project Management": ("TS-ADM-Projects", TS_ADM_PROJECTS),
        "Employee Management": ("TS-ADM-Employees", TS_ADM_EMPLOYEES),
        "Production Calendars": ("TS-ADM-Calendars", TS_ADM_CALENDARS),
        "Settings, API & Account": ("TS-ADM-Settings", TS_ADM_SETTINGS),
        "Tracker Integration": ("TS-ADM-Trackers", TS_ADM_TRACKERS),
        "API Errors & Permissions": ("TS-ADM-APIErrors", TS_ADM_APIERRORS),
    }

    type_cols = ["Functional", "Validation", "Security", "API", "Boundary", "Negative", "Bug verification"]

    for i, (feature, (suite_id, cases)) in enumerate(features.items()):
        r = row + 1 + i
        fill = FILL_ROW_EVEN if i % 2 == 0 else FILL_ROW_ODD

        # Feature name as hyperlink to suite
        cell = ws.cell(row=r, column=1, value=feature)
        cell.font = FONT_LINK_BOLD
        cell.hyperlink = f"#'{suite_id}'!A1"
        cell.border = THIN_BORDER
        cell.fill = fill

        type_counts = {}
        for c in cases:
            t = c["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        total = 0
        for j, ttype in enumerate(type_cols):
            count = type_counts.get(ttype, 0)
            total += count
            cell = ws.cell(row=r, column=j + 2, value=count if count > 0 else "")
            cell.font = FONT_BODY
            cell.alignment = ALIGN_CENTER
            cell.border = THIN_BORDER
            cell.fill = fill

        cell = ws.cell(row=r, column=len(type_cols) + 2, value=total)
        cell.font = Font(name="Arial", bold=True, size=10)
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER
        cell.fill = fill

    # Totals row
    totals_row = row + 1 + len(features)
    ws.cell(row=totals_row, column=1, value="TOTAL").font = Font(name="Arial", bold=True, size=11)
    ws.cell(row=totals_row, column=1).fill = FILL_SECTION
    ws.cell(row=totals_row, column=1).border = THIN_BORDER

    all_cases = []
    for _, cases in features.values():
        all_cases.extend(cases)
    all_type_counts = {}
    for c in all_cases:
        t = c["type"]
        all_type_counts[t] = all_type_counts.get(t, 0) + 1

    grand_total = 0
    for j, ttype in enumerate(type_cols):
        count = all_type_counts.get(ttype, 0)
        grand_total += count
        cell = ws.cell(row=totals_row, column=j + 2, value=count)
        cell.font = Font(name="Arial", bold=True, size=10)
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER
        cell.fill = FILL_SECTION

    cell = ws.cell(row=totals_row, column=len(type_cols) + 2, value=grand_total)
    cell.font = Font(name="Arial", bold=True, size=11)
    cell.alignment = ALIGN_CENTER
    cell.border = THIN_BORDER
    cell.fill = FILL_SECTION

    # Column widths
    ws.column_dimensions["A"].width = 30
    for col_letter in "BCDEFGHI":
        ws.column_dimensions[col_letter].width = 16

    add_autofilter(ws, 3, len(headers))


def build_risk_assessment(wb):
    ws = wb.create_sheet("Risk Assessment")
    ws.sheet_properties.tabColor = TAB_COLOR_PLAN

    ws.cell(row=1, column=1, value="Risk Assessment — Administration Module").font = FONT_TITLE
    ws.merge_cells("A1:G1")

    headers = ["Feature", "Risk", "Likelihood", "Impact", "Severity", "Mitigation / Test Focus"]
    row = 3
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    risks = [
        ("Project DELETE",
         "AUTHENTICATED_USER on DELETE endpoint — any authenticated user reaches service layer",
         "Medium", "High", "High",
         "TC-ADM-014: Verify ProjectPermissionService enforces DELETE. "
         "TC-ADM-061: Permission hierarchy test."),
        ("Employee PATCH",
         "Missing @PreAuthorize on PATCH /{login} — controller allows any request through",
         "High", "High", "Critical",
         "TC-ADM-029: Test unauthenticated PATCH. "
         "Verify service-level guards catch unauthorized access."),
        ("Calendar cascade",
         "Calendar event deletion triggers vacation/day-off recalculation across services",
         "Medium", "High", "High",
         "TC-ADM-040: Delete event and verify cascade. "
         "TC-ADM-042: Working days recalculation."),
        ("PM Tool sync failure",
         "Missing employees → IllegalStateException → HTTP 500",
         "Medium", "Medium", "Medium",
         "TC-ADM-020: Trigger sync with missing CS IDs. "
         "Verify error handling."),
        ("PM Tool rate limiting",
         "Aggressive sync may exceed rate limit, blocking other API calls",
         "Low", "Medium", "Medium",
         "TC-ADM-016: Verify rate limiter (50 req/min). "
         "TC-ADM-021: Failed entity retry batching."),
        ("Calendar name uniqueness",
         "Frontend case-insensitive but backend may be case-sensitive — bypass creates near-duplicates",
         "Medium", "Low", "Medium",
         "TC-ADM-034: Test case sensitivity gap."),
        ("GraalVM sandbox bypass",
         "Loop prevention via string matching (not AST) — potentially fragile",
         "Low", "High", "Medium",
         "TC-ADM-058: Test sandbox security boundaries. "
         "Test creative loop constructs."),
        ("Tracker credential encryption",
         "Encrypted credentials stored in DB — key management not visible",
         "Low", "High", "Medium",
         "TC-ADM-051/054: Credential lifecycle. "
         "Verify encrypted storage."),
        ("Work log sync data volume",
         "222K tracker work log rows — bulk sync may timeout",
         "Medium", "Medium", "Medium",
         "TC-ADM-057: Bidirectional sync. "
         "TC-ADM-021: Timeout handling."),
        ("Calendar PATCH asymmetry",
         "Event PATCH only updates reason — users may expect duration/date editable",
         "Medium", "Low", "Low",
         "TC-ADM-039: Verify only reason updated on PATCH."),
        ("Draft → ACTIVE mapping",
         "PM Tool draft projects silently become ACTIVE in TTT",
         "Low", "Low", "Low",
         "TC-ADM-018: Verify mapping."),
        ("Role naming inconsistency",
         "'ADMIN' vs 'ROLE_CHIEF_ACCOUNTANT' — inconsistent Spring Security convention",
         "Low", "Low", "Low",
         "TC-ADM-037: Verify both role formats work."),
        ("findByDate null response",
         "Returns null instead of 404 — clients may not handle null",
         "Low", "Low", "Low",
         "TC-ADM-041: Verify null response for missing dates."),
    ]

    for i, (feature, risk, likelihood, impact, severity, mitigation) in enumerate(risks):
        r = row + 1 + i
        if severity == "Critical":
            fill = FILL_RISK_HIGH
        elif severity == "High":
            fill = FILL_RISK_HIGH
        elif severity == "Medium":
            fill = FILL_RISK_MED
        else:
            fill = FILL_RISK_LOW

        values = [feature, risk, likelihood, impact, severity, mitigation]
        write_row(ws, r, values, fill=fill)

    add_autofilter(ws, 3, len(headers))

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 55


def main():
    wb = openpyxl.Workbook()

    # Plan tabs (green)
    build_plan_overview(wb)
    build_feature_matrix(wb)
    build_risk_assessment(wb)

    # Test suite tabs (blue)
    for suite_id, suite_name, cases in SUITES:
        ws = wb.create_sheet(suite_id)
        ws.sheet_properties.tabColor = TAB_COLOR_TS
        count = write_ts_tab(ws, suite_name, cases)
        print(f"  {suite_id}: {count} cases")

    out_path = "/home/v/Dev/ttt-expert-v1/expert-system/output/admin/admin.xlsx"
    wb.save(out_path)
    print(f"\nSaved: {out_path}")
    print(f"Total: {TOTAL_CASES} test cases across {len(SUITES)} suites")


if __name__ == "__main__":
    main()

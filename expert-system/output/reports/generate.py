#!/usr/bin/env python3
"""Generate reports.xlsx — unified test workbook for Reports & Confirmation module.

Phase B output for the TTT Expert System.
Covers: CRUD operations, confirmation (approval/rejection) flow, period management,
        lock management, statistics/norm calculation, permissions, API errors & edge cases.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

# ── Styling constants (identical to other workbooks) ────────────

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


# ── Helper functions ─────────────────────────────────────────────

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
# TEST CASE DATA — 7 suites
# =====================================================================

# ── TS-RPT-CRUD ─────────────────────────────────────────────────
# Create, update (PATCH), delete, batch operations

TS_RPT_CRUD = [
    tc("TC-RPT-001",
       "Create report with minimum required fields",
       "Logged in as employee with REPORTS_EDIT on target task.\n"
       "Report period is OPEN for current date.",
       "1. POST /api/ttt/v1/reports/create\n"
       "2. Body: {taskId: <valid>, reportDate: '<today>', executorLogin: '<own>', effort: 60}\n"
       "3. Verify response status 201\n"
       "4. GET /api/ttt/v1/reports?taskId=<id>&executorLogin=<own>",
       "HTTP 201. Report created with state=REPORTED.\n"
       "Response includes id, effort=60, executorLogin, reportDate, periodState=OPEN.\n"
       "permissions array includes EDIT, DELETE.",
       "Critical", "Functional",
       "REQ-reports Create", "TaskReportController, InternalTaskReportService",
       "Note: returns 201 (not 200 like vacation module)"),

    tc("TC-RPT-002",
       "Create report with optional reportComment",
       "Employee with REPORTS_EDIT. Open report period.",
       "1. POST /api/ttt/v1/reports/create\n"
       "2. Body: {taskId, reportDate, executorLogin, effort: 120, reportComment: 'API development'}\n"
       "3. Verify reportComment in response",
       "HTTP 201. reportComment='API development' stored and returned.\n"
       "Comment visible in My Tasks table cell tooltip.",
       "High", "Functional",
       "REQ-reports Create", "TaskReportController",
       ""),

    tc("TC-RPT-003",
       "Create report -- duplicate (same task+date+executor) returns 409",
       "Existing report for task X on date Y by employee Z.",
       "1. POST /api/ttt/v1/reports/create\n"
       "2. Body: {taskId: X, reportDate: Y, executorLogin: Z, effort: 60}\n"
       "3. Expect error response",
       "HTTP 409 Conflict. AlreadyExistsException.\n"
       "Response contains 'existentObject' field with existing report ID.\n"
       "Unique constraint: (task_id, executor_login, report_date).",
       "Critical", "Negative",
       "", "InternalTaskReportService",
       "DB constraint: unique (task_id, executor_login, report_date)"),

    tc("TC-RPT-004",
       "Create report -- effort minimum 1 minute (boundary)",
       "Open report period.",
       "1. POST with effort: 1\n"
       "2. POST with effort: 0\n"
       "3. POST with effort: -1",
       "effort=1: HTTP 201 (minimum accepted).\n"
       "effort=0: HTTP 400 @Min(1) violation.\n"
       "effort=-1: HTTP 400 @Min(1) violation.\n"
       "Create requires @Min(1), unlike edit which allows @Min(0).",
       "High", "Boundary",
       "", "TaskReportCreateRequestDTO",
       "Critical difference: create @Min(1), edit @Min(0)"),

    tc("TC-RPT-005",
       "BUG: No upper bound on effort -- 1500 min (25h) accepted",
       "Open report period.",
       "1. POST with effort: 1500 (25 hours)\n"
       "2. POST with effort: 99999\n"
       "3. Verify both succeed",
       "BUG: Both succeed. No maximum effort validation.\n"
       "1500 minutes = 25 hours on a single day accepted.\n"
       "Daily report limit should be 36h (2160 min) but not enforced on create.\n"
       "Warning system exists (DATE_EFFORT_OVER_LIMIT) but doesn't prevent creation.",
       "High", "Bug verification",
       "BUG-REPORT-1", "TaskReportController, TaskReportCreateRequestDTO",
       "No @Max annotation on effort field"),

    tc("TC-RPT-006",
       "Create report -- closed report period returns 400",
       "Report period start date is 2026-03-01. Attempt report for 2026-02-15.",
       "1. GET /api/ttt/v1/offices/<id>/periods/report to verify period\n"
       "2. POST /api/ttt/v1/reports/create with reportDate=2026-02-15\n"
       "3. Expect error",
       "HTTP 400. ReportPeriodValidator rejects date before period start.\n"
       "Error: constraint.report.period (implicit).\n"
       "ReportDate must be >= office report period start.",
       "Critical", "Negative",
       "REQ-reports Period", "ReportPeriodValidator",
       "Period boundary enforced per executor's office"),

    tc("TC-RPT-007",
       "BUG: Future date accepted without restriction",
       "Open report period.",
       "1. POST with reportDate = '2026-12-31' (far future)\n"
       "2. Verify creation succeeds",
       "BUG: HTTP 201. Report created for future date.\n"
       "No forward-date restriction in backend.\n"
       "Only backward restriction (report period) exists.",
       "Medium", "Bug verification",
       "BUG-REPORT-5", "ReportPeriodValidator",
       "Missing future date validation"),

    tc("TC-RPT-008",
       "Create report -- FINISHED project returns 403",
       "Project with status=FINISHED in project database.",
       "1. POST with taskId belonging to FINISHED project\n"
       "2. Expect error",
       "HTTP 403. ProjectFinishedException.\n"
       "Cannot create reports for FINISHED or CANCELED projects.\n"
       "Code checks project status before creation.",
       "High", "Negative",
       "", "InternalTaskReportService",
       "Also applies to CANCELED projects"),

    tc("TC-RPT-009",
       "Create report -- invalid executorLogin returns 400",
       "Open report period.",
       "1. POST with executorLogin: 'nonexistent_user_xyz'\n"
       "2. Expect validation error",
       "HTTP 400. @EmployeeLoginExists custom validator rejects.\n"
       "Login must exist in employee registry.",
       "Medium", "Negative",
       "", "TaskReportCreateRequestDTO",
       "@EmployeeLoginExists annotation"),

    tc("TC-RPT-010",
       "BUG: Cross-employee reporting -- any employee login accepted",
       "Employee A reporting for Employee B on a shared task.",
       "1. Login as employee A\n"
       "2. POST with executorLogin: '<employee_B>'\n"
       "3. Verify report created under Employee B",
       "BUG: Report created with executorLogin=B, reporterLogin=A.\n"
       "API doesn't restrict reporting to own login only.\n"
       "Intended for manager-reports-on-behalf but no role check.\n"
       "Any authenticated user can report for any employee.",
       "Medium", "Bug verification",
       "BUG-REPORT-4", "TaskReportController",
       "No executor=currentUser check on create"),

    tc("TC-RPT-011",
       "PATCH report -- change effort resets state to REPORTED",
       "Existing report with state=APPROVED.",
       "1. PATCH /api/ttt/v1/reports/<id>\n"
       "2. Body: {effort: 120}\n"
       "3. Verify state in response",
       "State automatically reset from APPROVED to REPORTED.\n"
       "approverLogin cleared.\n"
       "Key rule: effort change ALWAYS resets state to REPORTED.",
       "Critical", "Functional",
       "REQ-reports State", "InternalTaskReportService",
       "This is the mechanism to 'un-approve' a report"),

    tc("TC-RPT-012",
       "PATCH report -- set effort=0 deletes the report",
       "Existing report with effort=60.",
       "1. PATCH /api/ttt/v1/reports/<id>\n"
       "2. Body: {effort: 0}\n"
       "3. GET the same report ID",
       "PATCH returns 200 but report is deleted.\n"
       "GET returns 500 (no GET by ID endpoint) or report absent from search.\n"
       "TaskReportDeleteEvent published.\n"
       "Edit allows @Min(0) — setting to 0 triggers deletion.",
       "Critical", "Functional",
       "", "InternalTaskReportService",
       "Deletion via effort=0 is the only way to delete via PATCH"),

    tc("TC-RPT-013",
       "PATCH report -- update reportComment only",
       "Existing report with state=REPORTED.",
       "1. PATCH with {reportComment: 'Updated comment'}\n"
       "2. Verify state unchanged, comment updated",
       "reportComment updated. State remains REPORTED.\n"
       "Comment-only change does not trigger state reset.\n"
       "Only effort change triggers state reset.",
       "Medium", "Functional",
       "", "InternalTaskReportService",
       ""),

    tc("TC-RPT-014",
       "DELETE reports -- batch delete by IDs",
       "2+ existing reports owned by current user.",
       "1. DELETE /api/ttt/v1/reports\n"
       "2. Body: {ids: [id1, id2]}\n"
       "3. Verify both removed",
       "HTTP 200. Reports deleted.\n"
       "Requires REPORTS_EDIT or REPORTS_APPROVE permission.",
       "High", "Functional",
       "REQ-reports Delete", "TaskReportController",
       "Batch delete with ID array"),

    tc("TC-RPT-015",
       "Batch create -- PUT /v1/reports (upsert array)",
       "Open report period. 3 valid task/date combinations.",
       "1. PUT /api/ttt/v1/reports\n"
       "2. Body: array of 3 report objects\n"
       "3. Verify all created",
       "HTTP 200. All 3 reports created (not 201 like single create).\n"
       "Each item validated independently.\n"
       "Batch PUT skips locking (unlike PATCH).",
       "High", "Functional",
       "REQ-reports Batch", "TaskReportController",
       "PUT batch returns 200, POST single returns 201"),

    tc("TC-RPT-016",
       "Batch PATCH -- approve multiple reports at once",
       "3 reports in REPORTED state, user has REPORTS_APPROVE.",
       "1. PATCH /api/ttt/v1/reports\n"
       "2. Body: {items: [{id: id1, state: 'APPROVED'}, {id: id2, state: 'APPROVED'}, ...]}\n"
       "3. Verify all approved",
       "All reports state=APPROVED. approverLogin set.\n"
       "Batch PATCH supports bulk approve/reject.\n"
       "Per-item validation applied.",
       "High", "Functional",
       "REQ-reports Confirmation", "TaskReportController",
       "Main use case for manager bulk approval"),

    tc("TC-RPT-017",
       "BUG: Direct create-as-APPROVED bypasses workflow",
       "Open report period. User has REPORTS_APPROVE.",
       "1. POST /api/ttt/v1/reports/create\n"
       "2. Body: {taskId, reportDate, executorLogin, effort: 60, state: 'APPROVED'}\n"
       "3. Verify state in response",
       "BUG: Report created directly with state=APPROVED.\n"
       "Bypasses REPORTED -> APPROVED workflow entirely.\n"
       "Initial state should be forced to REPORTED regardless of input.",
       "High", "Bug verification",
       "BUG-REPORT-3", "TaskReportController",
       "Initial state not forced to REPORTED on create"),

    tc("TC-RPT-018",
       "Search reports -- at least one filter required",
       "Authenticated user.",
       "1. GET /api/ttt/v1/reports without any filter parameters\n"
       "2. GET with taskId filter\n"
       "3. GET with executorLogin filter\n"
       "4. GET with projectId filter",
       "No filters: HTTP 400 (TaskReportSearchRequestValidator rejects).\n"
       "With any filter: HTTP 200 with results.\n"
       "Validator requires at least one of: taskId, executorLogin, executorsProjectId, projectId.",
       "High", "Negative",
       "", "TaskReportSearchRequestValidator",
       "Empty search prevented by custom validator"),

    tc("TC-RPT-019",
       "GET /reports/total -- aggregated by week",
       "Authenticated user with REPORTS_VIEW.",
       "1. GET /api/ttt/v1/reports/total?type=PROJECT&date=2026-03-01\n"
       "2. Verify grouped result structure",
       "Returns aggregated totals grouped by project or employee.\n"
       "type param: PROJECT or EMPLOYEE.\n"
       "Used by Confirmation page week tabs.",
       "Medium", "Functional",
       "REQ-reports Confirmation UI", "TaskReportController",
       ""),

    tc("TC-RPT-020",
       "GET /reports/summary -- employee period summary",
       "Authenticated user.",
       "1. GET /api/ttt/v1/reports/summary?executorLogin=<login>&date=2026-03-01",
       "Returns summary with totalEffort, norm, budgetNorm for period.\n"
       "Used by My Tasks EffortForPeriodContainer.\n"
       "Displays week + month norms.",
       "Medium", "Functional",
       "", "TaskReportController",
       ""),
]

# ── TS-RPT-Confirmation ─────────────────────────────────────────
# Approval, rejection, re-reporting, auto-reject flow

TS_RPT_CONFIRMATION = [
    tc("TC-RPT-021",
       "Approve report -- REPORTED -> APPROVED transition",
       "Report in REPORTED state. User has REPORTS_APPROVE on task.\n"
       "reportDate >= approve period start.",
       "1. PATCH /api/ttt/v1/reports/<id>\n"
       "2. Body: {state: 'APPROVED'}\n"
       "3. Verify state and approverLogin",
       "state=APPROVED. approverLogin set to current user.\n"
       "stateComment cleared. Rejection record deleted if existed.\n"
       "Audit trail updated.",
       "Critical", "Functional",
       "REQ-reports Confirmation", "InternalTaskReportService",
       ""),

    tc("TC-RPT-022",
       "Reject report -- REPORTED -> REJECTED with comment",
       "Report in REPORTED state. User has REPORTS_APPROVE.",
       "1. PATCH /api/ttt/v1/reports/<id>\n"
       "2. Body: {state: 'REJECTED', stateComment: 'Wrong project'}\n"
       "3. Verify state, stateComment\n"
       "4. Check reject table in DB",
       "state=REJECTED. stateComment='Wrong project'.\n"
       "Reject record created in ttt_backend.reject table:\n"
       "rejector, description='Wrong project', executor_notified=false.\n"
       "Notification sent within 5 min by sendRejectNotifications scheduler.",
       "Critical", "Functional",
       "REQ-reports Confirmation", "InternalTaskReportService",
       "Reject creates DB record in reject table"),

    tc("TC-RPT-023",
       "Reject report -- stateComment is optional (API allows null)",
       "Report in REPORTED state.",
       "1. PATCH with {state: 'REJECTED'} (no stateComment)\n"
       "2. Verify rejection succeeds",
       "Rejection succeeds without comment.\n"
       "Reject record created with NULL description.\n"
       "Note: UI requires comment (textarea), but API doesn't enforce.",
       "Medium", "Functional",
       "", "InternalTaskReportService",
       "Frontend requires comment, backend doesn't"),

    tc("TC-RPT-024",
       "Re-report after rejection -- effort change resets to REPORTED",
       "Report in REJECTED state with reject record.",
       "1. PATCH with {effort: 90} (changed effort)\n"
       "2. Verify state and reject record",
       "State reset from REJECTED to REPORTED.\n"
       "Reject record DELETED from ttt_backend.reject table (no history preserved).\n"
       "approverLogin cleared. Employee can re-report after rejection.",
       "Critical", "Functional",
       "REQ-reports Re-report", "InternalTaskReportService",
       "Reject record deleted -- no rejection history kept"),

    tc("TC-RPT-025",
       "BUG: Self-approval -- no executor != approver check",
       "Employee's own report in REPORTED state.\n"
       "Employee also has REPORTS_APPROVE (PM role on own project).",
       "1. Login as employee who is PM on their own project\n"
       "2. PATCH own report with {state: 'APPROVED'}\n"
       "3. Verify approval succeeds",
       "BUG: Self-approval succeeds.\n"
       "approverLogin = executorLogin.\n"
       "No business rule prevents approving own reports.\n"
       "Should require executor != approver.",
       "High", "Bug verification",
       "BUG-REPORT-2", "InternalTaskReportService",
       "No executor!=approver check anywhere in the chain"),

    tc("TC-RPT-026",
       "Approve blocked for PROJECT_MANAGER type projects",
       "Report on a project with type=PROJECT_MANAGER.\n"
       "User has REPORTS_APPROVE.",
       "1. PATCH with {state: 'APPROVED'} for project type PROJECT_MANAGER\n"
       "2. Expect rejection or skip",
       "Approval blocked for PROJECT_MANAGER type projects.\n"
       "Business rule: these projects cannot be approved.\n"
       "State remains REPORTED.",
       "High", "Negative",
       "", "InternalTaskReportService",
       "PROJECT_MANAGER type special handling"),

    tc("TC-RPT-027",
       "Approve blocked if reportDate < approve period start",
       "Report with reportDate before approve period start.\n"
       "User has REPORTS_APPROVE.",
       "1. GET approve period start for office\n"
       "2. PATCH report with reportDate before that start\n"
       "3. Body: {state: 'APPROVED'}",
       "Approval blocked. reportDate must be >= approve period start.\n"
       "Only affects approval, not rejection.\n"
       "periodState shows CLOSED in response.",
       "High", "Negative",
       "REQ-reports Periods", "InternalTaskReportService",
       ""),

    tc("TC-RPT-028",
       "Confirmation page -- By employees view",
       "Logged in as PM with REPORTS_APPROVE. Navigate to /approve.",
       "1. Open Confirmation page\n"
       "2. Select 'By employees' tab\n"
       "3. Observe layout: employee rows, week tabs, task columns",
       "Week navigation: 6 week tabs. Orange dot on tabs with pending items.\n"
       "Employee rows expand to show tasks with daily effort cells.\n"
       "Approve button per task (all days in week).\n"
       "Bulk approve header button available.",
       "High", "Functional",
       "REQ-reports Confirmation UI", "frontend-approve-module",
       ""),

    tc("TC-RPT-029",
       "Confirmation page -- By projects view",
       "PM with multiple projects.",
       "1. Switch to 'By projects' tab\n"
       "2. Observe grouping",
       "Projects listed with employees grouped under each.\n"
       "N+1 API pattern: ~5N requests for N employees.\n"
       "Same approve/reject controls as By employees view.",
       "High", "Functional",
       "REQ-reports Confirmation UI", "frontend-approve-module",
       "Known performance issue: N+1 API pattern"),

    tc("TC-RPT-030",
       "Confirmation page -- reject with comment via tooltip",
       "Report in REPORTED state. PM on Confirmation page.",
       "1. Click reject icon on a task row\n"
       "2. Observe tooltip with textarea\n"
       "3. Enter rejection comment\n"
       "4. Click reject button",
       "Tooltip opens with textarea for rejection comment.\n"
       "Comment required in UI (submit button disabled without text).\n"
       "PATCH sent with state=REJECTED, stateComment=<entered text>.\n"
       "Report shows as rejected in the table.",
       "High", "Functional",
       "REQ-reports Confirmation UI", "frontend-approve-module",
       "UI requires comment; API makes it optional"),

    tc("TC-RPT-031",
       "BUG: 'employee is undefined' TypeError after approve click",
       "PM on Confirmation page. Approve a task.",
       "1. Open browser console (F12)\n"
       "2. Click Approve on a task\n"
       "3. Check console for errors",
       "BUG: 'employee is undefined' TypeError in console.\n"
       "Non-blocking race condition.\n"
       "Approval still succeeds, but console error logged.\n"
       "Likely timing issue in React state update.",
       "Low", "Bug verification",
       "BUG-CONFIRM-1", "frontend-approve-module",
       "Non-blocking race condition in React"),

    tc("TC-RPT-032",
       "Confirmation page -- 'With approved hours' toggle",
       "PM with approved and unapproved reports in same week.",
       "1. Toggle 'With approved hours' filter\n"
       "2. Observe table changes",
       "Toggle OFF (default): only REPORTED state visible.\n"
       "Toggle ON: both REPORTED and APPROVED visible.\n"
       "Affects which reports are shown in the grid.",
       "Medium", "Functional",
       "", "frontend-approve-module",
       ""),

    tc("TC-RPT-033",
       "Confirmation page -- 'Of other projects' checkbox",
       "PM with reports on projects they don't manage.",
       "1. Check 'Of other projects' checkbox\n"
       "2. Observe additional rows",
       "Shows reports on projects where user has VIEW but not APPROVE.\n"
       "Read-only — no approve/reject buttons on these rows.",
       "Medium", "Functional",
       "", "frontend-approve-module",
       ""),

    tc("TC-RPT-034",
       "Auto-reject on approve period close",
       "Reports in REPORTED state. Accountant advances approve period.",
       "1. Identify reports in REPORTED state within current approve period\n"
       "2. PATCH /<officeId>/periods/approve to advance\n"
       "3. Verify reports now REJECTED\n"
       "4. Check reject table for auto.reject.state",
       "All REPORTED reports in closed period auto-rejected.\n"
       "Single shared Reject record with description='auto.reject.state'.\n"
       "Notification emails sent to affected employees.\n"
       "PeriodChangedEvent published.",
       "Critical", "Functional",
       "REQ-reports Auto-reject", "TaskReportServiceImpl, InternalTaskReportService",
       "Distinguish auto from manual: reject.description='auto.reject.state'"),

    tc("TC-RPT-035",
       "Auto-reject warnings on My Tasks page",
       "Employee with auto-rejected reports.",
       "1. Navigate to /report (My Tasks)\n"
       "2. Check for auto-reject notification banners at top",
       "AutoRejectedReportsContainer shows error notifications:\n"
       "'Unconfirmed hours for task {taskName} were automatically rejected upon month closure'\n"
       "'Go to the report page' link navigates to rejection week.\n"
       "Close button hides via localStorage (hiddenAutoRejectWarnings).",
       "High", "Functional",
       "", "frontend-report-module, AutoRejectedReportsContainer",
       "Displays on /report page, NOT /approve page"),

    tc("TC-RPT-036",
       "Auto-reject -- no data exists on testing environments",
       "Timemachine/qa-1/stage environments.",
       "1. SELECT * FROM ttt_backend.reject WHERE description = 'auto.reject.state'\n"
       "2. GET /api/ttt/v1/task-auto-reject-warnings",
       "No auto-reject records exist on any testing environment.\n"
       "Feature never triggered.\n"
       "Warning endpoint returns empty array.\n"
       "Must trigger manually to test.",
       "Medium", "Functional",
       "", "TaskReportAutoRejectController",
       "Feature untested in practice"),

    tc("TC-RPT-037",
       "Reject notification -- sent within 5 minutes by scheduler",
       "Reject a report. Wait for notification dispatch.",
       "1. PATCH report to state=REJECTED\n"
       "2. Verify reject.executor_notified=false in DB\n"
       "3. Trigger sendRejectNotifications scheduler (or wait 5 min)\n"
       "4. Check email via GET /api/email/v1/emails",
       "Reject record created with executor_notified=false.\n"
       "Scheduler sendRejectNotifications runs every 5 min.\n"
       "Sends APPROVE_REJECT email template to executor.\n"
       "After send: executor_notified=true.",
       "High", "Functional",
       "REQ-reports Notifications", "sendRejectNotifications scheduler",
       "Schedule: every 5 minutes"),

    tc("TC-RPT-038",
       "BUG: Reject email not reliably sent (timing/date filtering)",
       "Reject a report and trigger notification scheduler.",
       "1. Reject a report via PATCH\n"
       "2. Trigger send-reject-notifications\n"
       "3. Check if email sent via GET /api/email/v1/emails",
       "BUG: Reject email sometimes not sent.\n"
       "Suspected timing/date filtering issue in scheduler query.\n"
       "executor_notified may not update correctly.",
       "Medium", "Bug verification",
       "BUG-CONFIRM-2", "sendRejectNotifications",
       "Intermittent -- timing-dependent"),

    tc("TC-RPT-039",
       "BUG: APPROVE permission appears/disappears between PATCH and GET",
       "Manager approves a report.",
       "1. PATCH report to APPROVED (returns permissions array)\n"
       "2. Immediately GET same report\n"
       "3. Compare permissions arrays",
       "BUG: APPROVE permission present in PATCH response\n"
       "but absent from subsequent GET response (or vice versa).\n"
       "Permission calculation race condition.",
       "Low", "Bug verification",
       "BUG-CONFIRM-3", "TaskReportPermissionType",
       "Timing-dependent permission inconsistency"),
]

# ── TS-RPT-Periods ──────────────────────────────────────────────
# Report and approve period management, extended periods

TS_RPT_PERIODS = [
    tc("TC-RPT-040",
       "GET report period for office",
       "Authenticated user with OFFICES_VIEW.",
       "1. GET /api/ttt/v1/offices/<officeId>/periods/report",
       "Returns current report period start date (1st of month).\n"
       "Format: {start: '2026-03-01'}.\n"
       "Defines earliest date employees can submit reports.",
       "High", "Functional",
       "REQ-reports Periods", "PeriodController",
       ""),

    tc("TC-RPT-041",
       "GET approve period for office",
       "Authenticated user with OFFICES_VIEW.",
       "1. GET /api/ttt/v1/offices/<officeId>/periods/approve",
       "Returns current approve period start date.\n"
       "Always <= report period (invariant).\n"
       "Defines earliest date managers can approve reports.",
       "High", "Functional",
       "REQ-reports Periods", "PeriodController",
       "Approve period always <= report period"),

    tc("TC-RPT-042",
       "PATCH report period -- advance forward",
       "Accountant JWT auth. Office with report period 2026-03-01.",
       "1. PATCH /api/ttt/v1/offices/<id>/periods/report\n"
       "2. Body: {start: '2026-04-01'}\n"
       "3. Verify period updated",
       "Report period advanced to 2026-04-01.\n"
       "Employees can no longer submit reports before April.\n"
       "Cache evicted for this office.",
       "Critical", "Functional",
       "REQ-reports Period close", "PeriodController",
       "Must be 1st of month (validated)"),

    tc("TC-RPT-043",
       "PATCH report period -- must be 1st of month",
       "Accountant JWT auth.",
       "1. PATCH with {start: '2026-03-15'} (not 1st)\n"
       "2. Expect validation error",
       "HTTP 400. getDayOfMonth() != 1 check fails.\n"
       "Report period must always be the 1st of a month.",
       "High", "Negative",
       "", "PeriodServiceImpl",
       "Backend validates day-of-month"),

    tc("TC-RPT-044",
       "PATCH report period -- cannot precede approve period",
       "Approve period = 2026-02-01. Attempt report period = 2026-01-01.",
       "1. PATCH report period to 2026-01-01\n"
       "2. Expect error",
       "HTTP 400. Report period cannot go before approve period.\n"
       "Invariant: approve <= report maintained.",
       "High", "Negative",
       "", "PeriodServiceImpl",
       "Invariant enforcement"),

    tc("TC-RPT-045",
       "PATCH report period -- no upper limit (can jump far forward)",
       "Current report period 2026-03-01.",
       "1. PATCH with {start: '2026-12-01'}\n"
       "2. Verify jump accepted",
       "Jump forward accepted. No maximum limit on report period.\n"
       "Contrast: approve period limited to 1-month jumps.",
       "Medium", "Boundary",
       "", "PeriodServiceImpl",
       "Asymmetry: report unlimited, approve limited to 1-month"),

    tc("TC-RPT-046",
       "PATCH approve period -- advance 1 month",
       "Accountant. Approve period 2026-02-01, report period 2026-03-01.",
       "1. PATCH /api/ttt/v1/offices/<id>/periods/approve\n"
       "2. Body: {start: '2026-03-01'}\n"
       "3. Verify period updated",
       "Approve period advanced to 2026-03-01.\n"
       "PeriodChangedEvent published.\n"
       "Triggers auto-reject for REPORTED reports in February.\n"
       "Vacation recalculation triggered.",
       "Critical", "Functional",
       "REQ-reports Period close", "PeriodController",
       "Side effects: auto-reject + vacation recalc"),

    tc("TC-RPT-047",
       "BUG: Approve period -- missing first-day-of-month validation",
       "Accountant JWT auth.",
       "1. PATCH approve period with {start: '2026-03-15'}\n"
       "2. Verify response",
       "BUG: Accepts non-first-day date.\n"
       "Report period validates getDayOfMonth()!=1 but approve period does NOT.\n"
       "Missing validation at line 104 of PeriodServiceImpl.",
       "High", "Bug verification",
       "BUG-PERIOD-1", "PeriodServiceImpl",
       "Asymmetric validation: report validates, approve doesn't"),

    tc("TC-RPT-048",
       "PATCH approve period -- max 1-month jump",
       "Approve period 2026-02-01.",
       "1. PATCH with {start: '2026-04-01'} (2-month jump)\n"
       "2. Expect error",
       "HTTP 400. Maximum 1-month jump in either direction.\n"
       "Cannot advance approve period by more than 1 month at a time.",
       "High", "Negative",
       "", "PeriodServiceImpl",
       "Approve period has stricter jump limit than report period"),

    tc("TC-RPT-049",
       "PATCH approve period -- cannot go back >2 months from today",
       "Today is 2026-03-15.",
       "1. PATCH approve period with {start: '2025-12-01'}\n"
       "2. Expect error",
       "HTTP 400. Cannot go back more than 2 months from current date.\n"
       "Lower bound: today minus 2 months.",
       "Medium", "Negative",
       "", "PeriodServiceImpl",
       ""),

    tc("TC-RPT-050",
       "PATCH approve period -- cannot exceed report period",
       "Report period 2026-03-01.",
       "1. PATCH approve period with {start: '2026-04-01'}\n"
       "2. Expect error",
       "HTTP 400. Approve period cannot exceed report period.\n"
       "Invariant: approve <= report.",
       "High", "Negative",
       "", "PeriodServiceImpl",
       ""),

    tc("TC-RPT-051",
       "PATCH approve period -- blocked by active extended period",
       "Employee with active extended report period in office.",
       "1. PUT /api/ttt/v1/periods/report/employees/<login> (extend)\n"
       "2. PATCH approve period to advance\n"
       "3. Expect error",
       "HTTP 400. Blocked: employee has active extended period.\n"
       "Must wait for extended period to expire or remove it first.",
       "High", "Negative",
       "", "PeriodServiceImpl",
       "Extended periods block approve advancement"),

    tc("TC-RPT-052",
       "BUG: PATCH approve period with empty body -> NPE",
       "Accountant JWT auth.",
       "1. PATCH /api/ttt/v1/offices/<id>/periods/approve\n"
       "2. Body: {}\n"
       "3. Observe error",
       "BUG: HTTP 500 NullPointerException.\n"
       "start is null, getMonth() fails with NPE.\n"
       "Missing null check on request body.",
       "High", "Bug verification",
       "BUG-PERIOD-2", "PeriodServiceImpl",
       "NPE on null start field"),

    tc("TC-RPT-053",
       "BUG: Invalid date format leaks stack trace",
       "Accountant JWT auth.",
       "1. PATCH approve period with {start: 'not-a-date'}\n"
       "2. Observe error response body",
       "BUG: Full Java stack trace (50+ frames) leaked in response.\n"
       "Exposes internal class names, package structure, framework version.\n"
       "Should return clean 400 with format hint.",
       "Medium", "Bug verification",
       "BUG-PERIOD-3", "PeriodController",
       "Stack trace leakage -- security concern"),

    tc("TC-RPT-054",
       "Extended report period -- grant to employee",
       "Accountant. Employee's report period is 2026-03-01.",
       "1. PUT /api/ttt/v1/periods/report/employees/<login>\n"
       "2. Verify employee can now report before 2026-03-01",
       "Employee gets individual extended report period.\n"
       "Can submit reports before the office report period start.\n"
       "Auto-cleaned by ExtendedPeriodScheduler every 5 minutes.",
       "High", "Functional",
       "REQ-reports Extended", "PeriodController",
       "Schedule: ExtendedPeriodScheduler every 5 min cleanup"),

    tc("TC-RPT-055",
       "Period endpoints -- JWT only (no API token)",
       "API token with standard permissions.",
       "1. PATCH report period with API_SECRET_TOKEN header\n"
       "2. PATCH approve period with API_SECRET_TOKEN header",
       "Both return 403 or equivalent.\n"
       "Period management requires AUTHENTICATED_USER (JWT only).\n"
       "BUG-PERIOD-4: report min/max accepts JWT only, approve min/max accepts both.",
       "Medium", "Security",
       "BUG-PERIOD-4", "PeriodController",
       "Inconsistent permission model between report and approve"),

    tc("TC-RPT-056",
       "Period reopen -- PeriodReopenedEvent published",
       "Approve period was advanced. Revert 1 month back.",
       "1. PATCH approve period to go back 1 month\n"
       "2. Verify PeriodReopenedEvent effects",
       "Approve period reverted. PeriodReopenedEvent published.\n"
       "Previously auto-rejected reports remain REJECTED (not restored).\n"
       "Employees can now submit new reports in reopened period.",
       "Medium", "Functional",
       "", "PeriodServiceImpl",
       "Auto-rejected reports NOT restored on reopen"),

    tc("TC-RPT-057",
       "GET period min/max -- non-salary offices return 404",
       "Office without salary configuration.",
       "1. GET /api/ttt/v1/offices/<non-salary-id>/periods/report",
       "HTTP 404. Non-salary offices don't have period management.\n"
       "GET returns computed default for salary offices, 404 for others.",
       "Medium", "Negative",
       "", "PeriodController",
       ""),
]

# ── TS-RPT-Locks ────────────────────────────────────────────────
# Per-field locking, HTTP 423, concurrent access

TS_RPT_LOCKS = [
    tc("TC-RPT-058",
       "Lock acquisition on PATCH -- field-level locks created",
       "Report in REPORTED state. User A has REPORTS_EDIT.",
       "1. PATCH /api/ttt/v1/reports/<id> as User A with {effort: 120}\n"
       "2. Verify lock created (check response or subsequent attempt)",
       "Lock acquired on fields: EFFORT, REPORT_COMMENT, STATE, STATE_COMMENT.\n"
       "Lock is employee-specific (User A owns it).\n"
       "Lock auto-expires after 1 minute.",
       "High", "Functional",
       "", "LockService, InternalTaskReportService",
       "4 lock fields tracked per report"),

    tc("TC-RPT-059",
       "Lock conflict -- HTTP 423 when field locked by another user",
       "User A holds lock on report. User B attempts same field.",
       "1. User A: PATCH report effort (acquires lock)\n"
       "2. Within 1 minute, User B: PATCH same report effort\n"
       "3. Observe User B's response",
       "User B gets HTTP 423 Locked.\n"
       "TttLockException thrown.\n"
       "Error code: exception.ttt.lock.\n"
       "Unique to reports module -- vacation doesn't use locking.",
       "Critical", "Functional",
       "", "LockService, TttLockException",
       "HTTP 423 unique to reports module"),

    tc("TC-RPT-060",
       "Lock auto-expiry after 1 minute",
       "User A holds lock on report.",
       "1. User A: PATCH report (acquires lock)\n"
       "2. Wait >1 minute\n"
       "3. User B: PATCH same report",
       "User B succeeds after 1-minute lock expiry.\n"
       "Locks auto-expire -- no manual release needed.\n"
       "Must re-create lock to extend duration.",
       "High", "Functional",
       "", "LockService",
       "1-minute TTL, no extension mechanism"),

    tc("TC-RPT-061",
       "Lock owner can edit own locked field",
       "User A holds lock on report EFFORT field.",
       "1. User A: PATCH report effort again (same user)\n"
       "2. Verify no 423 error",
       "Same user can edit their own locked field.\n"
       "Locks are employee-specific -- only block OTHER users.",
       "Medium", "Functional",
       "", "LockService",
       ""),

    tc("TC-RPT-062",
       "Batch PUT skips locking",
       "2 users concurrently using batch PUT /v1/reports.",
       "1. User A: PUT /api/ttt/v1/reports (batch create)\n"
       "2. User B: PUT same tasks concurrently",
       "No 423 errors. Batch PUT does not acquire locks.\n"
       "Lock mechanism only applies to PATCH endpoint.\n"
       "Potential data race on batch operations.",
       "Medium", "Functional",
       "", "TaskReportController",
       "Design: batch operations bypass locking"),

    tc("TC-RPT-063",
       "Lock cleanup -- LockServiceImpl.cleanUpCache runs every 10 min",
       "Long-running session with expired locks.",
       "1. Check lock cache state via LockService\n"
       "2. Wait for cleanUpCache cycle (*/10 * * * *)",
       "cleanUpCache runs every 10 minutes.\n"
       "Removes expired locks from in-memory cache.\n"
       "Individual locks expire at 1 min; cleanup is background garbage collection.",
       "Low", "Functional",
       "", "LockServiceImpl",
       "Schedule: */10 * * * *"),

    tc("TC-RPT-064",
       "Lock state field -- blocks state change by other user",
       "Manager A starts rejection (acquires STATE lock). Manager B attempts approve.",
       "1. Manager A: PATCH with {state: 'REJECTED'}\n"
       "2. Manager B (within 1 min): PATCH with {state: 'APPROVED'}\n"
       "3. Observe Manager B response",
       "Manager B gets HTTP 423 Locked on STATE field.\n"
       "Both effort and state fields are independently lockable.\n"
       "Prevents concurrent approve/reject conflict.",
       "High", "Functional",
       "", "LockService",
       "Independent per-field locking"),
]

# ── TS-RPT-Statistics ───────────────────────────────────────────
# Norm calculation, statistic reports, over/under-reporting

TS_RPT_STATISTICS = [
    tc("TC-RPT-065",
       "Personal norm calculation -- excludes time-offs",
       "Employee with 5 vacation days in March 2026.\n"
       "Office calendar has 22 working days in March.",
       "1. GET /api/ttt/v1/reports/summary for March\n"
       "2. Verify norm = (22 - 5) * 8 * 60 minutes\n"
       "3. Cross-reference with DB: statistic_report table",
       "personalNorm = max(0, calendarNorm - offHours).\n"
       "Off hours include: vacations + sick leaves + day-offs + maternity.\n"
       "Overlapping off-periods merged before calculation.\n"
       "Result in minutes.",
       "Critical", "Functional",
       "REQ-reports Norms", "NormService",
       "Norm = (workDays - timeOffDays) * 8h * 60min"),

    tc("TC-RPT-066",
       "Budget norm -- excludes admin vacations from off-periods",
       "Employee with both paid vacation (5 days) and admin/unpaid vacation (3 days).",
       "1. GET summary or statistic_report\n"
       "2. Compare personal vs budget norm",
       "budgetNorm = calendarNorm - (offHours EXCLUDING admin vacations).\n"
       "Employee on unpaid leave still counted in budget.\n"
       "Display (#3381): '{individual} ({budget})' when admin vacation exists.",
       "High", "Functional",
       "REQ-reports Norms #3381", "NormService",
       "Budget includes admin vacation days as working"),

    tc("TC-RPT-067",
       "Norm display format -- with/without admin vacation",
       "Employee A: has admin vacation. Employee B: no admin vacation.",
       "1. Check norm display for Employee A\n"
       "2. Check norm display for Employee B",
       "Employee A: '{individual} ({budget})' format (two values).\n"
       "Employee B: just '{budget}' (single value).\n"
       "Format switches based on presence of admin vacation.",
       "Medium", "Functional",
       "REQ-reports #3381", "frontend-report-module",
       "#3381 display format"),

    tc("TC-RPT-068",
       "Forgotten report threshold -- 90% of personal norm",
       "Employee with personalNorm=9600 min (20 days * 8h).\n"
       "Reported effort = 8500 min (88.5% of norm).",
       "1. Check if employee receives forgotten notification\n"
       "2. Trigger sendReportsForgottenNotifications",
       "Threshold: 90% of personalNorm = 8640 min.\n"
       "8500 < 8640 → employee is under-reported.\n"
       "Forgotten report notification sent.\n"
       "Schedule: Mon/Fri 16:00.",
       "High", "Functional",
       "REQ-reports Notifications", "sendReportsForgottenNotifications",
       "Threshold: 90% of personal norm"),

    tc("TC-RPT-069",
       "Statistic report table -- nightly sync updates cache",
       "Timemachine environment.",
       "1. SELECT * FROM ttt_backend.statistic_report WHERE employee_login='<login>' AND report_date='2026-03-01'\n"
       "2. Verify fields: reported_effort, month_norm, budget_norm",
       "Pre-computed cache in ttt_backend.statistic_report.\n"
       "Nightly sync at 4:00 AM updates current + previous month.\n"
       "Three update paths: nightly cron, task report @Async, RabbitMQ.",
       "Medium", "Functional",
       "", "StatisticReportScheduler",
       "3 update paths can cause race conditions (BUG-STATS-1)"),

    tc("TC-RPT-070",
       "Deviation formula and ExcessStatus enum",
       "Employee with reported=9000 min, budgetNorm=8800 min.",
       "1. Calculate: (9000-8800)/8800 * 100 = 2.27%\n"
       "2. Verify ExcessStatus in API response",
       "excess = (reported - budgetNorm) / budgetNorm * 100%.\n"
       "ExcessStatus: HIGH (>0%), LOW (<0%), NEUTRAL (==0%), NA (budgetNorm=0).\n"
       "Display: integer %. Exception: (-1,+1) range shows 1 decimal.\n"
       "NA displays as '+N/A%' and sorts to top.",
       "Medium", "Functional",
       "", "StatisticReportService",
       "Special display for values near zero"),

    tc("TC-RPT-071",
       "Over/under-reporting banner on Confirmation page",
       "PM with over-reported employee in current month.",
       "1. Navigate to /approve (Confirmation page)\n"
       "2. Observe banner notification",
       "Non-dismissible banner visible to ADMIN, PM, SPM.\n"
       "Triggers: over-reporting today (current month) OR at month end.\n"
       "Employee names: red=over, purple=under.\n"
       "Clock icon tooltip: deviation %, month, DM, projects with PM names.",
       "High", "Functional",
       "REQ-reports Over-reporting", "frontend-approve-module",
       "Non-dismissible -- always visible when condition exists"),

    tc("TC-RPT-072",
       "GET /over-reported endpoint",
       "Authenticated user with REPORTS_VIEW.",
       "1. GET /api/ttt/v1/reports/over-reported",
       "Returns employees with over-reported hours.\n"
       "Legacy endpoint with N+1 pattern, superseded by statistic_report cache.\n"
       "Still functional but inefficient.",
       "Low", "Functional",
       "", "TaskReportController",
       "Legacy N+1 endpoint"),

    tc("TC-RPT-073",
       "Employee Reports page access by role",
       "Users with different roles.",
       "1. ADMIN: access /employee-reports -> sees all employees\n"
       "2. OFFICE_DIRECTOR: sees their office only\n"
       "3. DEPARTMENT_MANAGER: sees subordinates only\n"
       "4. EMPLOYEE: cannot access",
       "ADMIN, CHIEF_ACCOUNTANT: all employees.\n"
       "OFFICE_DIRECTOR, ACCOUNTANT: their office.\n"
       "DEPARTMENT_MANAGER, TECH_LEAD: subordinates.\n"
       "EMPLOYEE: no access (no route guard).",
       "High", "Functional",
       "REQ-reports Statistics view", "frontend-report-module",
       "Role-scoped data access"),

    tc("TC-RPT-074",
       "BUG: Race condition between MQ and task report event paths",
       "Concurrent statistic_report update from two sources.",
       "1. Submit report (triggers @Async task report event)\n"
       "2. Simultaneously process RabbitMQ vacation change\n"
       "3. Check statistic_report for inconsistency",
       "BUG: No pessimistic locking between MQ handler and task report event.\n"
       "Both paths update statistic_report.reported_effort.\n"
       "Race condition can produce incorrect cached values.\n"
       "Inconsistency resolves on next nightly sync.",
       "Medium", "Bug verification",
       "BUG-STATS-1", "StatisticReportService",
       "Self-healing via nightly sync, but incorrect during day"),

    tc("TC-RPT-075",
       "Statistic report -- 2-month sync window only",
       "Historical data older than 2 months.",
       "1. Check statistic_report for dates 3+ months ago\n"
       "2. Verify nightly sync only covers current + previous month",
       "Nightly sync covers current + previous month only.\n"
       "No historical back-fill mechanism.\n"
       "Older months may have stale data if never manually refreshed.",
       "Low", "Functional",
       "", "StatisticReportScheduler",
       "Design limitation: no historical sync"),

    tc("TC-RPT-076",
       "Reports changed notification -- manager reported on behalf",
       "Manager reports hours for employee on employee's task.",
       "1. Manager: POST /api/ttt/v1/reports/create with executorLogin=employee\n"
       "2. Trigger sendReportsChangedNotifications (daily 07:50)\n"
       "3. Check email",
       "Notification sent to employee: manager reported on their behalf.\n"
       "Template shows: task name, date, effort, reporter name.\n"
       "Schedule: daily at 07:50.",
       "Medium", "Functional",
       "REQ-reports Notifications", "sendReportsChangedNotifications",
       "Triggered when reporterLogin != executorLogin"),

    tc("TC-RPT-077",
       "Forgotten report delayed notification",
       "Employee still under-reported after initial notification.",
       "1. Trigger sendReportsForgottenDelayedNotifications (daily 16:30)",
       "Retry notification for employees who received initial forgotten notification\n"
       "but still haven't reached 90% threshold.\n"
       "Schedule: daily at 16:30 (30 min after initial batch).",
       "Low", "Functional",
       "", "sendReportsForgottenDelayedNotifications",
       "Retry mechanism for forgotten reports"),
]

# ── TS-RPT-Permissions ──────────────────────────────────────────
# Permission matrix, role-based access, security gaps

TS_RPT_PERMISSIONS = [
    tc("TC-RPT-078",
       "REPORTS_VIEW -- search and aggregation endpoints",
       "User with REPORTS_VIEW permission (any authenticated user on project).",
       "1. GET /api/ttt/v1/reports?taskId=<id>\n"
       "2. GET /api/ttt/v1/reports/total\n"
       "3. GET /api/ttt/v1/reports/summary\n"
       "4. GET /api/ttt/v1/reports/over-reported",
       "All return 200 with data.\n"
       "REPORTS_VIEW grants read access to report data.\n"
       "Includes total, summary, and over-reported endpoints.",
       "High", "Functional",
       "", "TaskReportController",
       ""),

    tc("TC-RPT-079",
       "REPORTS_EDIT -- create, batch create, PATCH effort, delete",
       "User with REPORTS_EDIT (has REPORT TaskPermissionType on task).",
       "1. POST /api/ttt/v1/reports/create\n"
       "2. PUT /api/ttt/v1/reports (batch)\n"
       "3. PATCH /api/ttt/v1/reports/<id> with {effort: 120}\n"
       "4. DELETE /api/ttt/v1/reports with {ids: [<id>]}",
       "All succeed. REPORTS_EDIT grants full CRUD.\n"
       "EDIT condition: reportDate >= report period start AND project not FINISHED.",
       "High", "Functional",
       "", "TaskReportController, TaskReportPermissionType",
       "EDIT = REPORT permission + date in period + project active"),

    tc("TC-RPT-080",
       "REPORTS_APPROVE -- state change to APPROVED/REJECTED",
       "User with REPORTS_APPROVE (PM/SPM/ADMIN on task's project).",
       "1. PATCH /api/ttt/v1/reports/<id> with {state: 'APPROVED'}\n"
       "2. PATCH another with {state: 'REJECTED'}\n"
       "3. Verify approverLogin set",
       "Both succeed. REPORTS_APPROVE grants state change rights.\n"
       "APPROVE condition: has APPROVE TaskPermissionType + reportDate >= approve period.\n"
       "approverLogin set to current user on approve.",
       "High", "Functional",
       "", "TaskReportPermissionType, InternalTaskReportService",
       "APPROVE = APPROVE permission + date in approve period"),

    tc("TC-RPT-081",
       "User without REPORTS_EDIT cannot create reports",
       "User with REPORTS_VIEW only (no REPORT TaskPermissionType on task).",
       "1. POST /api/ttt/v1/reports/create for a task where user has VIEW only",
       "HTTP 403. TttSecurityException.\n"
       "Error code: exception.ttt.security.\n"
       "REPORTS_EDIT requires REPORT permission on the specific task.",
       "High", "Negative",
       "", "InternalTaskReportService",
       "Per-task permission check"),

    tc("TC-RPT-082",
       "User without REPORTS_APPROVE cannot change state",
       "Regular employee (no PM role on project).",
       "1. PATCH own report with {state: 'APPROVED'}\n"
       "2. Expect error",
       "HTTP 403. Requires APPROVE TaskPermissionType.\n"
       "Only PM, Senior PM, ADMIN on the project can approve.",
       "High", "Negative",
       "", "InternalTaskReportService",
       ""),

    tc("TC-RPT-083",
       "EDIT permission lost when report period closes",
       "Report with reportDate=2026-02-15. Report period advanced to 2026-03-01.",
       "1. GET report -- check permissions array\n"
       "2. PATCH report with {effort: 120}",
       "permissions array: EDIT absent.\n"
       "PATCH returns 403 or permission denied.\n"
       "periodState=CLOSED in response.\n"
       "EDIT requires reportDate >= report period start.",
       "High", "Functional",
       "", "TaskReportPermissionType",
       "Period closure removes EDIT/DELETE permissions"),

    tc("TC-RPT-084",
       "APPROVE permission lost when approve period closes",
       "Report with reportDate=2026-01-15. Approve period advanced to 2026-02-01.",
       "1. PATCH with {state: 'APPROVED'}\n"
       "2. Expect error",
       "APPROVE permission not granted for reports before approve period.\n"
       "Must be: reportDate >= approve period start.",
       "High", "Functional",
       "", "TaskReportPermissionType",
       ""),

    tc("TC-RPT-085",
       "BUG: /effort endpoint missing @PreAuthorize",
       "Unauthenticated or API token request.",
       "1. GET /api/ttt/v1/reports/effort without JWT\n"
       "2. Observe response",
       "BUG: Endpoint accessible without authentication.\n"
       "No @PreAuthorize annotation on /effort endpoint.\n"
       "Should require AUTHENTICATED_USER at minimum.",
       "Medium", "Bug verification",
       "BUG-REPORT-6", "TaskReportController",
       "Missing @PreAuthorize on 2 endpoints"),

    tc("TC-RPT-086",
       "BUG: /employee-projects endpoint missing @PreAuthorize",
       "Unauthenticated request.",
       "1. GET /api/ttt/v1/reports/employee-projects without JWT\n"
       "2. Observe response",
       "BUG: Accessible without authentication.\n"
       "Same issue as /effort -- missing @PreAuthorize.\n"
       "Both endpoints return data without auth check.",
       "Medium", "Bug verification",
       "BUG-REPORT-6", "TaskReportController",
       "Same bug as TC-RPT-085"),

    tc("TC-RPT-087",
       "Accounting endpoints -- AUTHENTICATED_USER only",
       "1. JWT authenticated user\n2. API token with permissions",
       "1. GET /api/ttt/v1/reports/accounting with JWT -> verify access\n"
       "2. POST /api/ttt/v1/reports/send-accounting-notifications with JWT\n"
       "3. Same endpoints with API_SECRET_TOKEN header",
       "JWT: both endpoints accessible.\n"
       "API token: both return 403.\n"
       "Accounting endpoints require AUTHENTICATED_USER (JWT only).",
       "High", "Security",
       "", "TaskReportController",
       "No API token access to accounting endpoints"),

    tc("TC-RPT-088",
       "Warning endpoints -- AUTHENTICATED_USER only",
       "JWT vs API token access.",
       "1. GET /api/ttt/v1/task-report-warnings with JWT\n"
       "2. GET /api/ttt/v1/task-auto-reject-warnings with JWT\n"
       "3. Same with API_SECRET_TOKEN",
       "JWT: accessible. API token: 403.\n"
       "Warning endpoints require AUTHENTICATED_USER.\n"
       "Auto-reject controller returns BO directly (no DTO -- design issue).",
       "Medium", "Security",
       "", "TaskReportWarningController, TaskReportAutoRejectController",
       "Auto-reject returns BO instead of DTO (BO leak)"),

    tc("TC-RPT-089",
       "Permission calculation flow -- per-task, per-report",
       "User with PM role on Project A, employee on Project B.",
       "1. GET reports for tasks on Project A\n"
       "2. GET reports for tasks on Project B\n"
       "3. Compare permissions arrays",
       "Project A reports: permissions include EDIT, DELETE, APPROVE.\n"
       "Project B reports: permissions include EDIT, DELETE only.\n"
       "Permissions calculated: group by executor → by task → per report.",
       "Medium", "Functional",
       "", "TaskReportPermissionType",
       "Per-task permission, not global"),

    tc("TC-RPT-090",
       "Auth polling -- excessive /authentication/check calls",
       "Open Confirmation page in browser with network monitor.",
       "1. Navigate to /approve\n"
       "2. Monitor network tab for 60 seconds\n"
       "3. Count GET /v1/authentication/check calls",
       "50+ GET /v1/authentication/check calls per session.\n"
       "Excessive auth polling pattern.\n"
       "Performance concern but functionally harmless.",
       "Low", "Functional",
       "", "frontend-approve-module",
       "Performance: excessive auth polling"),
]

# ── TS-RPT-APIErrors ────────────────────────────────────────────
# Error codes, edge cases, boundary values, scheduled jobs

TS_RPT_APIERRORS = [
    tc("TC-RPT-091",
       "Error code: NOT_FOUND (404) on non-existent report",
       "Authenticated user.",
       "1. PATCH /api/ttt/v1/reports/999999999\n"
       "2. Observe error response",
       "HTTP 404. Error code: NOT_FOUND.\n"
       "NotFoundException from InternalTaskReportService.\n"
       "Note: GET /reports/{id} returns 500 (no GET-by-ID endpoint).",
       "Medium", "Negative",
       "", "InternalTaskReportService, RestErrorHandler",
       "GET by ID returns 500 -- must use search"),

    tc("TC-RPT-092",
       "Error code: exception.ttt.lock (423) on lock conflict",
       "Two concurrent users editing same report.",
       "1. User A: PATCH report (acquires lock)\n"
       "2. User B (within 1 min): PATCH same report\n"
       "3. Observe User B error",
       "HTTP 423 Locked.\n"
       "Error code: exception.ttt.lock.\n"
       "TttLockException with lock holder details.",
       "High", "Negative",
       "", "LockService, RestErrorHandler",
       "423 is unique to reports module"),

    tc("TC-RPT-093",
       "Error code: exception.ttt.security (403) on permission denied",
       "User without REPORTS_EDIT on target task.",
       "1. POST /api/ttt/v1/reports/create for task without REPORT permission",
       "HTTP 403. Error code: exception.ttt.security.\n"
       "TttSecurityException.\n"
       "Distinct from AccessDeniedException (which gives FORBIDDEN).",
       "High", "Negative",
       "", "InternalTaskReportService, RestErrorHandler",
       "Different from vacation's exception.vacation.no.permission"),

    tc("TC-RPT-094",
       "Error code: CONFLICT (409) on duplicate report",
       "Existing report for same task+date+executor.",
       "1. POST duplicate report\n"
       "2. Inspect error response",
       "HTTP 409. Error code: CONFLICT.\n"
       "AlreadyExistsException with 'existentObject' field.\n"
       "existentObject contains the existing report's ID.",
       "High", "Negative",
       "", "InternalTaskReportService, RestErrorHandler",
       "Response contains existing report reference"),

    tc("TC-RPT-095",
       "Error code: FORBIDDEN (403) on FINISHED project",
       "Task on FINISHED project.",
       "1. POST report for FINISHED project task\n"
       "2. Inspect error",
       "HTTP 403. ProjectFinishedException.\n"
       "Error code: FORBIDDEN (mapped from ProjectFinishedException).",
       "Medium", "Negative",
       "", "RestErrorHandler",
       "ProjectFinishedException -> 403"),

    tc("TC-RPT-096",
       "Error code: BAD_REQUEST (400) with field-level details",
       "Invalid create request.",
       "1. POST with missing required fields\n"
       "2. Inspect validation error structure",
       "HTTP 400. Error code: BAD_REQUEST.\n"
       "MethodArgumentNotValidException provides field-level details.\n"
       "Each invalid field listed with violation message.",
       "Medium", "Negative",
       "", "RestErrorHandler",
       "ConstraintViolationException also maps to 400"),

    tc("TC-RPT-097",
       "ServiceException maps to 500 (inconsistent with vacation's 400)",
       "Trigger an internal service error.",
       "1. Create scenario causing ServiceException\n"
       "2. Observe HTTP status",
       "HTTP 500. ServiceException maps to INTERNAL_SERVER_ERROR in TTT.\n"
       "Inconsistency: same ServiceException maps to 400 in vacation service.\n"
       "Different RestErrorHandler implementations per service.",
       "Medium", "Functional",
       "", "RestErrorHandler",
       "TTT: 500, Vacation: 400 -- inconsistent across services"),

    tc("TC-RPT-098",
       "Effort boundary: @Min(0) on PATCH allows negative effect via 0",
       "Existing report.",
       "1. PATCH with {effort: 0} -> deletes report\n"
       "2. PATCH with {effort: -1} -> validation error",
       "effort=0: report deleted (valid, @Min(0)).\n"
       "effort=-1: HTTP 400 @Min(0) violation.\n"
       "Boundary at 0: deletes. Below 0: rejected.",
       "High", "Boundary",
       "", "TaskReportEditRequestDTO",
       "Asymmetry: create @Min(1), edit @Min(0)"),

    tc("TC-RPT-099",
       "Report with effort displayed in hours (÷60 conversion)",
       "Report with effort=90 minutes.",
       "1. Create report with effort=90\n"
       "2. Check UI display in My Tasks\n"
       "3. Check API response",
       "API: effort=90 (minutes, integer).\n"
       "UI: displays 1.5 (hours, effort/60).\n"
       "Conversion in frontend: calcEmployeeEffort() divides by 60.",
       "Medium", "Functional",
       "", "frontend-report-module",
       "API uses minutes, UI shows hours"),

    tc("TC-RPT-100",
       "My Tasks page -- task add via quick search",
       "Employee on /report page.",
       "1. Click 'Add task' search field\n"
       "2. Type task name (partial match)\n"
       "3. Select from suggestions\n"
       "4. Verify task appears in report grid",
       "TaskAddContainer provides type-ahead search.\n"
       "Suggestion endpoint: GET /api/ttt/v1/tasks?search=<query>.\n"
       "Selected task added to employee's visible report grid.",
       "High", "Functional",
       "", "frontend-report-module, TaskAddContainer",
       ""),

    tc("TC-RPT-101",
       "My Tasks page -- pin/unpin task for quick access",
       "Employee with tasks on /report page.",
       "1. Pin a task: POST /api/ttt/v1/tasks/<id>/employees/<login>/pin\n"
       "2. Verify task appears at top of list\n"
       "3. Unpin: DELETE /api/ttt/v1/tasks/<id>/employees/<login>/pin",
       "Pinned tasks appear at top of My Tasks table.\n"
       "Pin persists across sessions.\n"
       "Unpin removes from pinned list.",
       "Medium", "Functional",
       "", "frontend-report-module",
       "Pin/unpin via POST/DELETE endpoints"),

    tc("TC-RPT-102",
       "My Tasks page -- week switcher navigation",
       "Employee on /report page.",
       "1. Click previous/next week arrows\n"
       "2. Observe date range update\n"
       "3. Verify reports refresh for new week",
       "Week navigation with left/right arrows.\n"
       "Shows Monday-Sunday range.\n"
       "Complex date math with Moment.js (tech debt -- should use date-fns).",
       "Medium", "Functional",
       "", "frontend-report-module, WeekSwitcherContainer",
       "Moment.js tech debt"),

    tc("TC-RPT-103",
       "My Tasks page -- grouped by project vs ungrouped toggle",
       "Employee with tasks across multiple projects.",
       "1. Toggle 'Grouped by project' switch\n"
       "2. Verify table layout changes",
       "Ungrouped: flat task list.\n"
       "Grouped: tasks organized under project headers.\n"
       "Toggle state persisted in Redux uiFiltersReducer.",
       "Medium", "Functional",
       "", "frontend-report-module, ProjectsGroupedSwitcher",
       ""),

    tc("TC-RPT-104",
       "Report event system -- add/patch/delete events published",
       "Create, edit, delete reports.",
       "1. POST /api/ttt/v1/reports/create -> TaskReportAddEvent\n"
       "2. PATCH /api/ttt/v1/reports/<id> -> TaskReportPatchEvent\n"
       "3. DELETE -> TaskReportDeleteEvent (also via effort=0)",
       "Three event types published:\n"
       "- TaskReportAddEvent: on creation\n"
       "- TaskReportPatchEvent: on update (with before-state)\n"
       "- TaskReportDeleteEvent: on delete AND on effort=0\n"
       "Events drive: statistics cache, audit trail, notifications.",
       "Medium", "Functional",
       "", "TaskReportEventListener",
       "Async + transactional event listener"),

    tc("TC-RPT-105",
       "Accounting notifications -- send reminders to employees",
       "Accountant on accounting page with unconfirmed reports.",
       "1. POST /api/ttt/v1/reports/send-accounting-notifications\n"
       "2. Check emails sent",
       "Sends reminder notifications to employees with unconfirmed hours.\n"
       "Accountant-initiated action (not scheduled).\n"
       "AUTHENTICATED_USER only (no API token).",
       "Medium", "Functional",
       "", "TaskReportController",
       "Manual trigger by accountant"),

    tc("TC-RPT-106",
       "GET /reports/accounting -- paginated by office and date range",
       "Accountant JWT auth.",
       "1. GET /api/ttt/v1/reports/accounting?officeId=<id>&from=2026-03-01&to=2026-03-31\n"
       "2. Verify pagination structure",
       "Paginated response filtered by office and date range.\n"
       "Used by accountant confirmation view.\n"
       "JWT only -- API token returns 403.",
       "Medium", "Functional",
       "", "TaskReportController",
       ""),

    tc("TC-RPT-107",
       "Hardcoded CEO login in statistics -- ilnitsky",
       "Code inspection / behavior verification.",
       "1. Check StatisticReportService for CEO_LOGIN constant\n"
       "2. Verify special handling for CEO login",
       "Hardcoded: CEO_LOGIN = 'ilnitsky'.\n"
       "CEO excluded from certain statistics calculations.\n"
       "Design issue: hardcoded login instead of role-based check.",
       "Low", "Functional",
       "", "StatisticReportService",
       "Hardcoded CEO login -- design debt"),

    tc("TC-RPT-108",
       "Daily report effort limit -- 36h (2160 minutes) warning threshold",
       "Employee reporting >36h on a single day.",
       "1. Create reports totaling >2160 min on one day\n"
       "2. Check for warning generation",
       "Warning type: DATE_EFFORT_OVER_LIMIT generated.\n"
       "36h = 2160 minutes per day threshold.\n"
       "Warning only -- does not prevent report creation.",
       "Medium", "Boundary",
       "", "TaskReportWarningController",
       "Warning only, not enforcement"),

    tc("TC-RPT-109",
       "DTO response structure -- all fields verified",
       "Create a report and inspect full response.",
       "1. POST /api/ttt/v1/reports/create\n"
       "2. Inspect response JSON structure",
       "Response DTO fields:\n"
       "- id (Long), state (REPORTED|APPROVED|REJECTED)\n"
       "- stateComment (null unless REJECTED)\n"
       "- effort (Long, minutes), reportDate (ISO date)\n"
       "- executorLogin, reporterLogin, approverLogin\n"
       "- periodState (OPEN|CLOSED), reportComment\n"
       "- projectState {id, name, status}\n"
       "- permissions[] (EDIT, DELETE, APPROVE subset)",
       "Medium", "Functional",
       "", "TaskReportDTO",
       ""),

    tc("TC-RPT-110",
       "Reject response shows approverLogin derived from reject.rejector",
       "Report in REJECTED state.",
       "1. Reject a report with known rejector\n"
       "2. GET report via search\n"
       "3. Check approverLogin field",
       "API response shows approverLogin for rejected reports.\n"
       "But DB column task_report.approver is NULL.\n"
       "Value derived from reject.rejector (join query).\n"
       "Confusing: field named 'approver' but shows rejector.",
       "Low", "Functional",
       "", "InternalTaskReportService",
       "Naming confusion: approverLogin shows rejector on rejected reports"),
]


# =====================================================================
# SUITE REGISTRY
# =====================================================================

ALL_SUITES = [
    ("TS-RPT-CRUD", "Report CRUD Operations & Batch", TS_RPT_CRUD),
    ("TS-RPT-Confirmation", "Confirmation (Approval/Rejection) Flow", TS_RPT_CONFIRMATION),
    ("TS-RPT-Periods", "Period Management (Report & Approve)", TS_RPT_PERIODS),
    ("TS-RPT-Locks", "Lock Management & Concurrent Access", TS_RPT_LOCKS),
    ("TS-RPT-Statistics", "Statistics, Norms & Notifications", TS_RPT_STATISTICS),
    ("TS-RPT-Permissions", "Permissions, Security & Access Control", TS_RPT_PERMISSIONS),
    ("TS-RPT-APIErrors", "API Errors, Edge Cases & Integration", TS_RPT_APIERRORS),
]


# =====================================================================
# FEATURE MATRIX DATA
# =====================================================================

FEATURES = [
    # (feature, functional, negative, boundary, security, bug_verif, integration, total, suite_ref)
    ("CRUD (Create/Update/Delete/Batch)", 11, 4, 2, 0, 3, 0, 20, "TS-RPT-CRUD"),
    ("Confirmation (Approve/Reject/Auto)", 12, 0, 0, 0, 4, 3, 19, "TS-RPT-Confirmation"),
    ("Period Management", 7, 7, 1, 1, 3, 0, 18, "TS-RPT-Periods"),  # 1 security (JWT-only)
    ("Lock Management", 5, 1, 0, 0, 0, 1, 7, "TS-RPT-Locks"),
    ("Statistics & Norms", 10, 0, 0, 0, 1, 2, 13, "TS-RPT-Statistics"),
    ("Permissions & Security", 6, 2, 0, 3, 2, 0, 13, "TS-RPT-Permissions"),
    ("API Errors & Edge Cases", 9, 5, 2, 0, 0, 4, 20, "TS-RPT-APIErrors"),
]


# =====================================================================
# RISK ASSESSMENT DATA
# =====================================================================

RISKS = [
    ("Self-approval via API",
     "No executor!=approver check in backend. Employees with PM role "
     "on their own projects can approve their own reports via API. "
     "UI may mask this by hiding approve button on own reports.",
     "High", "High", "Critical",
     "Test PM approving own reports. Verify no backend check exists. "
     "Document UI vs API behavior difference."),

    ("Direct create-as-APPROVED bypasses workflow",
     "POST /reports with state=APPROVED creates pre-approved report. "
     "Skips REPORTED->APPROVED state machine entirely. "
     "Initial state should be forced to REPORTED regardless of input.",
     "Medium", "Critical", "Critical",
     "POST with state=APPROVED. Verify report created with APPROVED state. "
     "Document bypass path."),

    ("No upper bound on effort (25h+ accepted)",
     "No @Max annotation on effort field. Reports can be created with "
     "effort=99999 minutes. Warning system exists but doesn't prevent creation. "
     "Data integrity concern.",
     "High", "High", "Critical",
     "Create reports with extreme effort values. Verify no rejection. "
     "Check if warning threshold (36h/2160min) generates warning only."),

    ("Missing @PreAuthorize on /effort and /employee-projects",
     "Two GET endpoints accessible without any authentication. "
     "No @PreAuthorize annotation. Data exposed to unauthenticated callers.",
     "High", "Medium", "High",
     "Access both endpoints without JWT or API token. "
     "Verify data returned without authentication."),

    ("Lock bypass via batch PUT",
     "Batch PUT /v1/reports skips locking mechanism. "
     "Concurrent batch operations can cause data races. "
     "Individual PATCH properly acquires locks.",
     "Medium", "Medium", "High",
     "Concurrent batch PUT operations on same tasks. "
     "Verify no lock conflict raised (by design)."),

    ("Auto-reject never triggered on test environments",
     "Auto-reject feature (approve period close) has never been triggered. "
     "No reject records with description='auto.reject.state' exist. "
     "Feature functionally untested in practice.",
     "Medium", "High", "High",
     "Manually advance approve period to trigger auto-reject. "
     "Verify reports rejected, emails sent, warnings displayed."),

    ("Missing first-day-of-month validation on approve period",
     "Report period validates getDayOfMonth()!=1 but approve period does NOT. "
     "Any day of month accepted for approve period. "
     "Asymmetric validation between the two period types.",
     "Medium", "High", "High",
     "PATCH approve period with mid-month date. "
     "Verify accepted (bug). Compare with report period rejection."),

    ("NPE on empty PATCH body for approve period",
     "PATCH /periods/approve with {} body causes NullPointerException. "
     "start field is null, getMonth() fails. "
     "Missing null check on request body.",
     "Medium", "Medium", "High",
     "Send empty PATCH body. Verify 500 NPE response. "
     "Document missing null validation."),

    ("Stack trace leakage in period error responses",
     "Invalid date format in PATCH body returns full Java stack trace. "
     "Exposes internal class names, package structure, Spring version. "
     "Information disclosure vulnerability.",
     "Medium", "Medium", "Medium",
     "Send invalid date format. Verify stack trace in response."),

    ("Race condition in statistic_report updates",
     "No pessimistic locking between RabbitMQ handler and @Async task report event. "
     "Concurrent updates to statistic_report can produce incorrect cached values. "
     "Self-heals on nightly sync but incorrect during the day.",
     "Medium", "Medium", "Medium",
     "Trigger concurrent report + vacation change. "
     "Check statistic_report for inconsistency."),

    ("Cross-employee reporting without role check",
     "Any authenticated user can POST reports with any executorLogin. "
     "Intended for manager-reports-on-behalf but no PM role verification. "
     "Data attribution concern.",
     "High", "Medium", "Medium",
     "Employee A reports for Employee B. "
     "Verify no role check prevents this."),

    ("Reject history not preserved",
     "Re-reporting (effort change) on REJECTED report deletes the Reject record. "
     "No rejection history maintained. Cannot audit how many times report was rejected. "
     "approverLogin cleared on re-report.",
     "Low", "Medium", "Medium",
     "Reject report, then re-report. "
     "Verify reject record deleted from DB."),

    ("ServiceException: 500 in TTT vs 400 in vacation",
     "Same ServiceException class maps to HTTP 500 in TTT service "
     "but HTTP 400 in vacation service. Different RestErrorHandler implementations. "
     "Inconsistent error contract across services.",
     "Low", "Low", "Low",
     "Trigger ServiceException in both services. "
     "Compare HTTP status codes."),

    ("Future date accepted without restriction",
     "No forward-date validation on reportDate. "
     "Reports can be created for dates far in the future. "
     "Only backward restriction (report period) exists.",
     "High", "Low", "Medium",
     "Create report with date 6+ months in future. "
     "Verify accepted."),
]


# =====================================================================
# BUILD WORKBOOK
# =====================================================================

OUTPUT = "/home/v/Dev/ttt-expert-v1/expert-system/output/reports/reports.xlsx"

wb = openpyxl.Workbook()

# ═══════════════════════════════════════════════════════════════════
# TAB 1: Plan Overview
# ═══════════════════════════════════════════════════════════════════

ws = wb.active
ws.title = "Plan Overview"
ws.sheet_properties.tabColor = TAB_COLOR_PLAN

plan_rows = [
    ("Reports & Confirmation Module -- Test Plan", FONT_TITLE),
    (f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", FONT_SMALL),
    ("", None),
    ("Scope", FONT_SUBTITLE),
    ("Comprehensive testing of the Reports & Confirmation module covering task report", FONT_BODY),
    ("CRUD operations (create/update/delete/batch), the 3-state approval workflow", FONT_BODY),
    ("(REPORTED -> APPROVED/REJECTED), auto-reject on period close, dual period", FONT_BODY),
    ("management (report + approve periods with extended exceptions), per-field lock", FONT_BODY),
    ("management (HTTP 423), statistics/norm calculation, over/under-reporting,", FONT_BODY),
    ("permission matrix, and scheduled notification jobs.", FONT_BODY),
    ("", None),
    ("Objectives", FONT_SUBTITLE),
    ("1. Validate report CRUD: create, PATCH, delete, batch create/patch operations", FONT_BODY),
    ("2. Test 3-state machine: REPORTED -> APPROVED/REJECTED with re-reporting reset", FONT_BODY),
    ("3. Verify auto-reject flow when approve period closes (never triggered on test envs)", FONT_BODY),
    ("4. Test dual period management: report period + approve period invariants", FONT_BODY),
    ("5. Verify per-field locking with HTTP 423 conflict response (unique to this module)", FONT_BODY),
    ("6. Validate norm calculation: personal vs budget, forgotten report threshold (90%)", FONT_BODY),
    ("7. Test permission matrix: REPORTS_VIEW/EDIT/APPROVE across roles", FONT_BODY),
    ("8. Document and verify 14 known bugs across 4 categories", FONT_BODY),
    ("9. Verify 5 scheduled notification jobs with correct templates and timing", FONT_BODY),
    ("", None),
    ("Approach", FONT_SUBTITLE),
    ("Testing combines UI (Playwright on /report and /approve pages), API (curl/Swagger),", FONT_BODY),
    ("and DB (PostgreSQL ttt_backend schema) verification.", FONT_BODY),
    ("UI testing on timemachine environment with roles:", FONT_BODY),
    ("employee, project manager, senior PM, department manager, accountant, admin.", FONT_BODY),
    ("API testing via JWT session auth. API token access tested for coverage gaps.", FONT_BODY),
    ("Known bugs verified inline: 14 bugs (2 Critical, 5 High, 5 Medium, 2 Low).", FONT_BODY),
    ("", None),
    ("Test Data Strategy", FONT_SUBTITLE),
    ("- Timemachine env: use test clock to control reportDate relative to periods", FONT_BODY),
    ("- Effort values in minutes (API) displayed as hours (UI, /60)", FONT_BODY),
    ("- Boundary testing: effort=0 (delete), effort=1 (create min), effort=1500+ (no max)", FONT_BODY),
    ("- Period testing: use PATCH to move report/approve periods, verify constraints", FONT_BODY),
    ("- Lock testing: two concurrent sessions needed (two browser tabs / two API clients)", FONT_BODY),
    ("- Statistics: cross-reference statistic_report table with API responses", FONT_BODY),
    ("- DB mining: ttt_backend.task_report, ttt_backend.reject, ttt_backend.statistic_report", FONT_BODY),
    ("", None),
    ("Environment Requirements", FONT_SUBTITLE),
    ("- Primary: timemachine (ttt-timemachine.noveogroup.com)", FONT_BODY),
    ("- Secondary: qa-1 (ttt-qa-1.noveogroup.com)", FONT_BODY),
    ("- Cross-env: stage (ttt-stage.noveogroup.com) for comparison", FONT_BODY),
    ("- Browser: Chrome via Playwright (VPN required)", FONT_BODY),
    ("- Database: PostgreSQL port 5433, schema ttt_backend", FONT_BODY),
    ("- API: JWT auth for most endpoints; API tokens for search only", FONT_BODY),
    ("- Concurrent sessions: 2 users needed for lock conflict testing", FONT_BODY),
    ("", None),
    ("Qase Existing Coverage", FONT_SUBTITLE),
    ("2 existing cases in Qase (Russian, suite 213) about approve period vs report dates.", FONT_BODY),
    ("No overlap with this test plan. No lifecycle, CRUD, or confirmation flow cases exist.", FONT_BODY),
    ("THIS TEST PLAN covers 110 new test cases across 7 suites.", FONT_BODY),
    ("", None),
    ("Test Suite Index", FONT_SUBTITLE),
]

row_num = 1
for text, font in plan_rows:
    cell = ws.cell(row=row_num, column=1, value=text)
    if font:
        cell.font = font
    cell.alignment = ALIGN_LEFT
    row_num += 1

# Suite hyperlinks
for tab_name, title, cases in ALL_SUITES:
    count = len(cases)
    cell = ws.cell(row=row_num, column=1)
    cell.value = f"{tab_name}: {title} -- {count} cases"
    cell.font = FONT_LINK_BOLD
    cell.hyperlink = f"#'{tab_name}'!A1"
    row_num += 1

# Totals
row_num += 1
total_cases = sum(len(cases) for _, _, cases in ALL_SUITES)
ws.cell(row=row_num, column=1,
        value=f"Total: {total_cases} test cases across {len(ALL_SUITES)} test suites").font = FONT_SECTION

ws.column_dimensions["A"].width = 100


# ═══════════════════════════════════════════════════════════════════
# TAB 2: Feature Matrix
# ═══════════════════════════════════════════════════════════════════

ws_fm = wb.create_sheet("Feature Matrix")
ws_fm.sheet_properties.tabColor = TAB_COLOR_PLAN

fm_headers = [
    "Feature Area", "Functional", "Negative", "Boundary",
    "Security", "Bug Verification", "Integration", "Total", "Test Suite"
]

for col, h in enumerate(fm_headers, 1):
    ws_fm.cell(row=1, column=col, value=h)
style_header_row(ws_fm, 1, len(fm_headers))

for i, (feat, func, neg, bnd, sec, bug, integ, total, ref) in enumerate(FEATURES):
    r = i + 2
    fill = FILL_ROW_EVEN if i % 2 == 0 else FILL_ROW_ODD
    values = [feat, func, neg, bnd, sec, bug, integ, total, ref]
    write_row(ws_fm, r, values, fill=fill)
    link_cell = ws_fm.cell(row=r, column=9)
    link_cell.font = FONT_LINK
    link_cell.hyperlink = f"#'{ref}'!A1"

# Totals row
total_r = len(FEATURES) + 2
ws_fm.cell(row=total_r, column=1, value="TOTAL").font = FONT_SECTION
for c in range(2, 9):
    val = sum(f[c - 1] for f in FEATURES)
    ws_fm.cell(row=total_r, column=c, value=val).font = FONT_SECTION
for c in range(1, len(fm_headers) + 1):
    cell = ws_fm.cell(row=total_r, column=c)
    cell.border = THIN_BORDER
    cell.fill = FILL_SECTION

fm_widths = [35, 12, 10, 10, 10, 16, 12, 8, 22]
for i, w in enumerate(fm_widths, 1):
    ws_fm.column_dimensions[get_column_letter(i)].width = w
add_autofilter(ws_fm, 1, len(fm_headers))


# ═══════════════════════════════════════════════════════════════════
# TAB 3: Risk Assessment
# ═══════════════════════════════════════════════════════════════════

ws_risk = wb.create_sheet("Risk Assessment")
ws_risk.sheet_properties.tabColor = TAB_COLOR_PLAN

risk_headers = [
    "Risk", "Description", "Likelihood", "Impact", "Severity", "Mitigation / Test Focus"
]
for col, h in enumerate(risk_headers, 1):
    ws_risk.cell(row=1, column=col, value=h)
style_header_row(ws_risk, 1, len(risk_headers))

for i, (risk, desc, like, impact, sev, mit) in enumerate(RISKS):
    r = i + 2
    fill = FILL_ROW_EVEN if i % 2 == 0 else FILL_ROW_ODD
    values = [risk, desc, like, impact, sev, mit]
    write_row(ws_risk, r, values, fill=fill)
    sev_cell = ws_risk.cell(row=r, column=5)
    if sev == "Critical":
        sev_cell.fill = FILL_RISK_HIGH
    elif sev == "High":
        sev_cell.fill = FILL_RISK_HIGH
    elif sev == "Medium":
        sev_cell.fill = FILL_RISK_MED
    elif sev == "Low":
        sev_cell.fill = FILL_RISK_LOW

risk_widths = [38, 60, 12, 12, 12, 55]
for i, w in enumerate(risk_widths, 1):
    ws_risk.column_dimensions[get_column_letter(i)].width = w
add_autofilter(ws_risk, 1, len(risk_headers))


# ═══════════════════════════════════════════════════════════════════
# TABs 4-10: Test Suite sheets (TS-*)
# ═══════════════════════════════════════════════════════════════════

for tab_name, title, cases in ALL_SUITES:
    ws_ts = wb.create_sheet(tab_name)
    ws_ts.sheet_properties.tabColor = TAB_COLOR_TS
    write_ts_tab(ws_ts, title, cases)


# ═══════════════════════════════════════════════════════════════════
# Save
# ═══════════════════════════════════════════════════════════════════

wb.save(OUTPUT)

total_cases = sum(len(c) for _, _, c in ALL_SUITES)
print(f"Generated: {OUTPUT}")
print(f"Tabs: Plan Overview + Feature Matrix + Risk Assessment + {len(ALL_SUITES)} TS-* sheets")
print(f"Total test cases: {total_cases}")
print(f"Risks: {len(RISKS)}")
print()
for tab_name, title, cases in ALL_SUITES:
    print(f"  {tab_name}: {title} -- {len(cases)} cases")

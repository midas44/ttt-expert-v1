#!/usr/bin/env python3
"""Generate planner.xlsx — unified test workbook for Planner module.

Phase B output for the TTT Expert System (Session 68).
Covers: Assignment CRUD, search, generate, drag-drop ordering,
        close-by-tag, cell locking, history, known bugs.

Knowledge sources:
  - modules/planner-assignment-backend.md (enriched with API/DB details)
  - modules/frontend-planner-module.md (211 files, 19K lines, WebSocket)
  - modules/planner-close-tag-permissions.md (permission system, race conditions)
  - investigations/planner-ordering-deep-dive.md (dual ordering bugs)
  - external/requirements/REQ-planner.md (Confluence requirements)
  - architecture/websocket-events.md (STOMP, 12 event types)
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

    col_widths = [14, 40, 30, 50, 40, 10, 14, 20, 22, 30]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ═══════════════════════════════════════════════════════════════
#  TEST CASE DATA
# ═══════════════════════════════════════════════════════════════

# ── TS-Planner-Search (assignment search) ─────────────────────

TS_SEARCH = [
    {
        "id": "TC-PLN-001", "title": "Search assignments by employee and date range",
        "preconditions": "Employee 'diborisov' has generated assignments for 2026-03-03",
        "steps": "1. GET /v1/assignments?startDate=2026-03-03&endDate=2026-03-03&employeeLogin=diborisov",
        "expected": "200 OK. Response contains employees[] with single entry. assignments[] includes generated (with id, position, nextAssignmentId) and non-generated (id=null) assignments.",
        "priority": "High", "type": "Functional",
        "req_ref": "Confluence 130386435", "module": "TaskAssignmentController",
        "notes": "Verified on timemachine: 257 assignments for this employee"
    },
    {
        "id": "TC-PLN-002", "title": "Search assignments — missing required startDate",
        "preconditions": "Valid API token",
        "steps": "1. GET /v1/assignments?endDate=2026-03-03&employeeLogin=diborisov",
        "expected": "400 Bad Request. Error: 'startDate must not be null'",
        "priority": "High", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "Both startDate and endDate are @NotNull"
    },
    {
        "id": "TC-PLN-003", "title": "Search assignments — missing required endDate",
        "preconditions": "Valid API token",
        "steps": "1. GET /v1/assignments?startDate=2026-03-03&employeeLogin=diborisov",
        "expected": "400 Bad Request. Error: 'endDate must not be null'",
        "priority": "High", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-004", "title": "Search assignments — invalid employee login",
        "preconditions": "Valid API token",
        "steps": "1. GET /v1/assignments?startDate=2026-03-03&endDate=2026-03-03&employeeLogin=nonexistent_user",
        "expected": "400 Bad Request. Error: 'Employee login not found' (EmployeeLoginExists validation)",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "Validated via @EmployeeLoginExists annotation"
    },
    {
        "id": "TC-PLN-005", "title": "Search assignments — invalid project ID",
        "preconditions": "Valid API token",
        "steps": "1. GET /v1/assignments?startDate=2026-03-03&endDate=2026-03-03&projectId=999999",
        "expected": "400 Bad Request. Error: project not found (ProjectIdExists validation)",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "Validated via @ProjectIdExists annotation"
    },
    {
        "id": "TC-PLN-006", "title": "Search assignments — filter by projectId",
        "preconditions": "Employee has assignments across multiple projects",
        "steps": "1. GET /v1/assignments?startDate=2026-03-03&endDate=2026-03-03&employeeLogin=diborisov&projectId={validProjectId}",
        "expected": "200 OK. Only assignments for the specified project are returned.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-007", "title": "Search assignments — filter by closed status",
        "preconditions": "Employee has both open and closed assignments",
        "steps": "1. GET /v1/assignments?startDate=2026-03-01&endDate=2026-03-05&employeeLogin={login}&closed=true\n2. GET same with closed=false",
        "expected": "Step 1: only closed assignments. Step 2: only open assignments. Both return 200 OK.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-008", "title": "Search assignments — multi-day range returns grouped by day",
        "preconditions": "Employee has assignments across multiple days",
        "steps": "1. GET /v1/assignments?startDate=2026-03-01&endDate=2026-03-05&employeeLogin={login}",
        "expected": "200 OK. Response groups assignments by employee, each assignment has its date. Generated assignments have sequential position values.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-009", "title": "Search assignments — response includes permissions",
        "preconditions": "Valid API token for a manager user",
        "steps": "1. GET /v1/assignments?startDate=2026-03-03&endDate=2026-03-03&employeeLogin={subordinate}",
        "expected": "200 OK. Each assignment has 'permissions' array. Employee object has 'readOnly' field.",
        "priority": "Low", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "Permissions determine UI edit capabilities"
    },
    {
        "id": "TC-PLN-010", "title": "Search assignments — no data for date returns empty list",
        "preconditions": "Valid employee login",
        "steps": "1. GET /v1/assignments?startDate=2020-01-01&endDate=2020-01-01&employeeLogin={login}",
        "expected": "200 OK. employees[] contains single entry with empty assignments[].",
        "priority": "Low", "type": "Boundary",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-011", "title": "Search assignments — non-generated vs generated differentiation",
        "preconditions": "Employee has task reports but planner not opened (no generate called)",
        "steps": "1. GET /v1/assignments for a date where reports exist but generate was not called",
        "expected": "200 OK. Non-generated assignments have id=null, no position/nextAssignmentId. They have 'task', 'closed', 'updatedTime', 'reports', 'permissions' fields.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "Confluence 130386435 (generated vs non-generated)", "module": "TaskAssignmentController",
        "notes": "Non-generated appear from task reports without planner assignments"
    },
]

# ── TS-Planner-CRUD (create + patch assignments) ─────────────

TS_CRUD = [
    {
        "id": "TC-PLN-012", "title": "Create assignment — valid request",
        "preconditions": "Employee and task exist. No existing assignment for employee+task+date.",
        "steps": "1. POST /v1/assignments with body: {employeeLogin: '{login}', taskId: {id}, date: '2026-03-20'}\n2. GET /v1/assignments for same employee+date",
        "expected": "Step 1: 200 OK, returns TaskAssignmentDTO with generated id, position=0.\nStep 2: new assignment appears in list.",
        "priority": "High", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "New assignments always get position=0"
    },
    {
        "id": "TC-PLN-013", "title": "Create assignment — duplicate returns 409 Conflict",
        "preconditions": "Assignment already exists for employee+task+date",
        "steps": "1. POST /v1/assignments with same employeeLogin, taskId, date as existing assignment",
        "expected": "409 Conflict. Response body contains the existing assignment DTO (AlreadyExistsException).",
        "priority": "High", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "AlreadyExistsException wraps the existent object in response"
    },
    {
        "id": "TC-PLN-014", "title": "Create assignment — missing required employeeLogin",
        "preconditions": "Valid API token",
        "steps": "1. POST /v1/assignments with body: {taskId: 1, date: '2026-03-20'}",
        "expected": "400 Bad Request. Validation error: employeeLogin must not be null.",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-015", "title": "Create assignment — missing required taskId",
        "preconditions": "Valid API token",
        "steps": "1. POST /v1/assignments with body: {employeeLogin: '{login}', date: '2026-03-20'}",
        "expected": "400 Bad Request. Validation error: taskId must not be null.",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-016", "title": "Create assignment — with optional fields (comment, remainingEstimate)",
        "preconditions": "Valid employee, task, date",
        "steps": "1. POST /v1/assignments with body including: comment: '<p>Test comment</p>', remainingEstimate: '2h', internalComment: '<p>Internal</p>'",
        "expected": "200 OK. Assignment created with all optional fields populated. Comment stored as HTML.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "Comments support HTML content"
    },
    {
        "id": "TC-PLN-017", "title": "Patch assignment — update comment",
        "preconditions": "Assignment exists with id={assignmentId}",
        "steps": "1. PATCH /v1/assignments/{assignmentId} with body: {comment: '<p>Updated comment</p>'}",
        "expected": "200 OK. Assignment returned with updated comment field.",
        "priority": "High", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-018", "title": "Patch assignment — update remainingEstimate",
        "preconditions": "Assignment exists",
        "steps": "1. PATCH /v1/assignments/{id} with body: {remainingEstimate: '4h'}",
        "expected": "200 OK. remainingEstimate updated to '4h'.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "Free text field, no format validation"
    },
    {
        "id": "TC-PLN-019", "title": "Patch assignment — close assignment",
        "preconditions": "Open assignment exists",
        "steps": "1. PATCH /v1/assignments/{id} with body: {closed: true}\n2. POST /v1/assignments/generate for same employee+next day",
        "expected": "Step 1: 200 OK, closed=true.\nStep 2: closed assignment NOT included in generated assignments for future dates.",
        "priority": "High", "type": "Functional",
        "req_ref": "Confluence 130386435", "module": "TaskAssignmentController",
        "notes": "Closed assignments are excluded from future generation"
    },
    {
        "id": "TC-PLN-020", "title": "Patch assignment — update internalComment (not sent to customer)",
        "preconditions": "Assignment exists",
        "steps": "1. PATCH /v1/assignments/{id} with body: {internalComment: '<p>For internal use only</p>'}",
        "expected": "200 OK. internalComment updated. This field is marked as 'should not be sent to customer'.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "Internal comment vs regular comment distinction"
    },
    {
        "id": "TC-PLN-021", "title": "Patch assignment — locked by another user returns 423",
        "preconditions": "Assignment exists. Another user holds a lock on a field of this assignment.",
        "steps": "1. User A: POST /v1/locks with lock for assignment field 'comment'\n2. User B: PATCH /v1/assignments/{id} with body: {comment: 'new value'}",
        "expected": "Step 2: 423 Locked. Error indicates lock is held by another employee.",
        "priority": "High", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController / LockController",
        "notes": "Lock enforcement at PATCH level"
    },
    {
        "id": "TC-PLN-022", "title": "Patch assignment — update uiData (JSON string)",
        "preconditions": "Assignment exists",
        "steps": "1. PATCH /v1/assignments/{id} with body: {uiData: '{\"collapsed\": true, \"color\": \"blue\"}'}",
        "expected": "200 OK. uiData stored as-is (JSON string). Not parsed by backend.",
        "priority": "Low", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": "Frontend-managed opaque JSON blob"
    },
    {
        "id": "TC-PLN-023", "title": "Patch non-existent assignment returns 404",
        "preconditions": "Valid API token",
        "steps": "1. PATCH /v1/assignments/999999999 with body: {comment: 'test'}",
        "expected": "404 Not Found.",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
]

# ── TS-Planner-Generate (assignment generation) ──────────────

TS_GENERATE = [
    {
        "id": "TC-PLN-024", "title": "Generate assignments — creates from recent non-closed",
        "preconditions": "Employee has non-closed assignments on previous day. No assignments exist for target date.",
        "steps": "1. POST /v1/assignments/generate with body: {employeeLogin: '{login}', date: '2026-03-20'}",
        "expected": "200 OK. Returns TaskAssignmentsEmployeeResponseDTO with newly created assignments copied from recent non-closed ones.",
        "priority": "High", "type": "Functional",
        "req_ref": "Confluence 130386435", "module": "TaskAssignmentServiceImpl",
        "notes": "Core 'Open for Editing' functionality"
    },
    {
        "id": "TC-PLN-025", "title": "Generate assignments — includes task reports without assignments",
        "preconditions": "Employee has task reports on target date but no planner assignments",
        "steps": "1. Submit time report for task X on date D\n2. POST /v1/assignments/generate for same employee+date",
        "expected": "200 OK. Generated assignments include an assignment for task X (from the report).",
        "priority": "High", "type": "Functional",
        "req_ref": "Confluence 130386435", "module": "TaskAssignmentServiceImpl",
        "notes": "Non-generated -> generated transition"
    },
    {
        "id": "TC-PLN-026", "title": "Generate assignments — overwrites existing ordering",
        "preconditions": "Employee has manually reordered assignments via drag-drop on target date",
        "steps": "1. Note current assignment order (custom DnD order)\n2. POST /v1/assignments/generate for same employee+date\n3. GET assignments for same employee+date",
        "expected": "Step 3: All positions and nextAssignmentId values have been overwritten. Manual ordering is destroyed.",
        "priority": "High", "type": "Functional",
        "req_ref": "#3314", "module": "TaskAssignmentServiceImpl.generate()",
        "notes": "KNOWN ISSUE: generate() resets all ordering. This is by design but causes UX confusion."
    },
    {
        "id": "TC-PLN-027", "title": "Generate assignments — with projectId filter",
        "preconditions": "Employee works on multiple projects",
        "steps": "1. POST /v1/assignments/generate with body: {employeeLogin: '{login}', date: '2026-03-20', projectId: {id}}",
        "expected": "200 OK. Only assignments for the specified project are generated. Other projects' assignments remain unchanged.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentServiceImpl",
        "notes": ""
    },
    {
        "id": "TC-PLN-028", "title": "Generate assignments — excludes closed assignments",
        "preconditions": "Employee has some closed assignments",
        "steps": "1. Close assignment X via PATCH (closed=true)\n2. POST /v1/assignments/generate for next day",
        "expected": "200 OK. Closed assignment X is NOT included in generated assignments.",
        "priority": "High", "type": "Functional",
        "req_ref": "Confluence 130386435", "module": "TaskAssignmentServiceImpl",
        "notes": ""
    },
    {
        "id": "TC-PLN-029", "title": "Generate assignments — missing required employeeLogin",
        "preconditions": "Valid API token",
        "steps": "1. POST /v1/assignments/generate with body: {date: '2026-03-20'}",
        "expected": "400 Bad Request. Validation error: employeeLogin must not be null.",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-030", "title": "Generate assignments — missing required date",
        "preconditions": "Valid API token",
        "steps": "1. POST /v1/assignments/generate with body: {employeeLogin: '{login}'}",
        "expected": "400 Bad Request. Validation error: date must not be null.",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-031", "title": "Generate assignments — WebSocket GENERATE event emitted",
        "preconditions": "WebSocket client subscribed to /topic/employees/{login}/assignments/{period}",
        "steps": "1. POST /v1/assignments/generate\n2. Observe WebSocket events",
        "expected": "GENERATE event received on the assignments channel with updated assignment data.",
        "priority": "Medium", "type": "Integration",
        "req_ref": "", "module": "WsTaskAssignmentEventListener",
        "notes": "Verify via WebSocket subscription or browser dev tools"
    },
    {
        "id": "TC-PLN-032", "title": "Generate assignments — idempotent on re-call (no duplicates)",
        "preconditions": "Assignments already generated for employee+date",
        "steps": "1. POST /v1/assignments/generate (first call)\n2. POST /v1/assignments/generate (second call, same params)\n3. Compare assignment counts",
        "expected": "No duplicate assignments created. Second call returns same set (may re-order).",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentServiceImpl",
        "notes": "generate() should skip existing assignments"
    },
]

# ── TS-Planner-Ordering (drag-drop, move, position) ─────────

TS_ORDERING = [
    {
        "id": "TC-PLN-033", "title": "Move assignment via PATCH with nextAssignmentId",
        "preconditions": "Employee has 3+ generated assignments A, B, C (positions 0, 1, 2)",
        "steps": "1. PATCH /v1/assignments/{A.id} with body: {nextAssignmentId: {C.id}}\n2. GET assignments for same date",
        "expected": "Assignment A moved to position before C. New order: B, A, C. Both position and nextAssignmentId updated consistently.",
        "priority": "High", "type": "Functional",
        "req_ref": "#3258", "module": "InternalTaskAssignmentService.move()",
        "notes": "Drag-drop core mechanism"
    },
    {
        "id": "TC-PLN-034", "title": "Move assignment to end of list (nextAssignmentId=0)",
        "preconditions": "Employee has 3+ assignments",
        "steps": "1. PATCH /v1/assignments/{A.id} with body: {nextAssignmentId: 0}\n2. GET assignments",
        "expected": "Assignment A moved to last position. nextAssignmentId of A becomes null (end of chain).",
        "priority": "High", "type": "Functional",
        "req_ref": "", "module": "InternalTaskAssignmentService.move()",
        "notes": "nextAssignmentId=0 means 'move to bottom'"
    },
    {
        "id": "TC-PLN-035", "title": "Move propagates to future dates",
        "preconditions": "Employee has same assignments on day D and D+1",
        "steps": "1. Reorder assignment on day D via PATCH with nextAssignmentId\n2. GET assignments for day D+1",
        "expected": "Day D+1 assignments reflect the same ordering change as day D (propagated by moveFutureAssignmentsAccordingly).",
        "priority": "High", "type": "Functional",
        "req_ref": "#3308", "module": "InternalTaskAssignmentService.moveFutureAssignmentsAccordingly()",
        "notes": "Propagation to future dates is critical for consistency"
    },
    {
        "id": "TC-PLN-036", "title": "Move propagation — target task absent on future date",
        "preconditions": "Assignment A exists on D and D+1, but assignment B only on D (not D+1)",
        "steps": "1. Move A to position before B on day D\n2. GET assignments for day D+1",
        "expected": "Day D+1 remains unchanged (silent return when target task doesn't exist on future date).",
        "priority": "Medium", "type": "Edge Case",
        "req_ref": "", "module": "InternalTaskAssignmentService.moveFutureAssignmentsAccordingly()",
        "notes": "No error handling — silent skip"
    },
    {
        "id": "TC-PLN-037", "title": "Dual ordering consistency — position matches linked-list",
        "preconditions": "Employee has generated assignments",
        "steps": "1. GET assignments for a date\n2. Verify: for each assignment, position N should have nextAssignmentId pointing to assignment at position N+1\n3. Last assignment should have nextAssignmentId=null",
        "expected": "Position values and nextAssignmentId chain are fully consistent.",
        "priority": "High", "type": "Data Integrity",
        "req_ref": "", "module": "InternalTaskAssignmentService",
        "notes": "DB query: SELECT id, position, next_assignment FROM task_assignment WHERE date=D AND assignee=E ORDER BY position"
    },
    {
        "id": "TC-PLN-038", "title": "NULL position assignments float to top",
        "preconditions": "Database has legacy assignments with position=NULL (pre-migration V2_1_2_202101191720)",
        "steps": "1. Insert test assignment with position=NULL directly in DB\n2. GET assignments for same employee+date",
        "expected": "NULL-position assignments appear at the top of the list, sorted by task name, before all positioned assignments.",
        "priority": "Medium", "type": "Boundary",
        "req_ref": "", "module": "TaskAssignmentSorter",
        "notes": "Legacy data handling — no backfill migration exists"
    },
    {
        "id": "TC-PLN-039", "title": "Multiple new assignments — all get position=0",
        "preconditions": "Employee has no assignments for target date",
        "steps": "1. POST /v1/assignments — create assignment A (position=0)\n2. POST /v1/assignments — create assignment B (position=0)\n3. GET assignments for date",
        "expected": "Both A and B have position=0. Ordering relies on secondary sort by taskName until move() or generate() is called.",
        "priority": "Medium", "type": "Boundary",
        "req_ref": "", "module": "InternalTaskAssignmentService.create()",
        "notes": "Design debt: ambiguous ordering for new assignments"
    },
    {
        "id": "TC-PLN-040", "title": "DB ordering: ORDER BY position, task.name",
        "preconditions": "Assignments exist with various positions",
        "steps": "1. Query DB: SELECT ta.id, ta.position, t.name FROM task_assignment ta JOIN task t ON t.id = ta.task WHERE ta.date=D ORDER BY ta.position, t.name\n2. Compare with API response order",
        "expected": "DB order matches API response order (repository uses ORDER BY ta.position, t.name).",
        "priority": "Low", "type": "Data Integrity",
        "req_ref": "", "module": "TaskAssignmentRepository",
        "notes": "Linked-list ignored for retrieval, only position+name used"
    },
    {
        "id": "TC-PLN-041", "title": "Sorting: alphabetical within same position",
        "preconditions": "Multiple assignments with same position value",
        "steps": "1. Create assignments for tasks 'Zebra' and 'Alpha' both with position=0\n2. GET assignments",
        "expected": "Assignments sorted alphabetically by task name within same position group.",
        "priority": "Low", "type": "Functional",
        "req_ref": "Confluence 130386435 (A-Z, then Cyrillic)", "module": "TaskAssignmentSorter",
        "notes": ""
    },
]

# ── TS-Planner-CloseTag (close-by-tag CRUD + permissions) ────

TS_CLOSETAG = [
    {
        "id": "TC-PLN-042", "title": "List close-tags for project",
        "preconditions": "Project {projectId} exists. User authenticated.",
        "steps": "1. GET /v1/projects/{projectId}/close-tags",
        "expected": "200 OK. Array of PlannerCloseTagDTO objects [{id, projectId, tag}, ...]",
        "priority": "High", "type": "Functional",
        "req_ref": "#2724", "module": "PlannerCloseTagController",
        "notes": "Any authenticated user can list tags"
    },
    {
        "id": "TC-PLN-043", "title": "Create close-tag as project manager",
        "preconditions": "User is project manager for project {projectId}",
        "steps": "1. POST /v1/projects/{projectId}/close-tags with body: {tag: '[closed]'}",
        "expected": "200 OK. Returns PlannerCloseTagDTO with generated id, projectId, and tag '[closed]'.",
        "priority": "High", "type": "Functional",
        "req_ref": "#2724", "module": "PlannerCloseTagController",
        "notes": ""
    },
    {
        "id": "TC-PLN-044", "title": "Create close-tag — idempotent (duplicate returns existing)",
        "preconditions": "Tag '[closed]' already exists for project",
        "steps": "1. POST /v1/projects/{projectId}/close-tags with body: {tag: '[closed]'} (same tag again)",
        "expected": "200 OK. Returns the existing tag with same id (get-or-create semantics, race-condition safe via REQUIRES_NEW transaction).",
        "priority": "High", "type": "Functional",
        "req_ref": "", "module": "PlannerCloseTagServiceImpl.create()",
        "notes": "Idempotent create prevents race condition duplicates"
    },
    {
        "id": "TC-PLN-045", "title": "Create close-tag — blank tag rejected",
        "preconditions": "User is project manager",
        "steps": "1. POST /v1/projects/{projectId}/close-tags with body: {tag: ''}\n2. POST with body: {tag: '   '}",
        "expected": "Both return 400 Bad Request. Error: 'Tag must not be blank' (@NotBlank validation).",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "PlannerCloseTagCreateRequestDTO",
        "notes": ""
    },
    {
        "id": "TC-PLN-046", "title": "Create close-tag — max length 255 characters",
        "preconditions": "User is project manager",
        "steps": "1. POST with tag of exactly 255 characters\n2. POST with tag of 256 characters",
        "expected": "Step 1: 200 OK (tag created).\nStep 2: 400 Bad Request or DB error (column length = 255).",
        "priority": "Medium", "type": "Boundary",
        "req_ref": "Confluence says 200 max, DB allows 255", "module": "PlannerCloseTag entity",
        "notes": "DISCREPANCY: requirements say max 200 chars but DB column is varchar(255)"
    },
    {
        "id": "TC-PLN-047", "title": "Update close-tag via PATCH",
        "preconditions": "Tag {tagId} exists for project",
        "steps": "1. PATCH /v1/projects/{projectId}/close-tags/{tagId} with body: {tag: '[done]'}",
        "expected": "200 OK. Tag string updated to '[done]'. Returns updated PlannerCloseTagDTO.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "#2724", "module": "PlannerCloseTagController",
        "notes": ""
    },
    {
        "id": "TC-PLN-048", "title": "Update close-tag — duplicate tag returns 400",
        "preconditions": "Two tags exist: '[closed]' and '[done]' for same project",
        "steps": "1. PATCH tag '[done]' to update its string to '[closed]'",
        "expected": "400 Bad Request (ValidationException). Duplicate tag within project not allowed.",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "PlannerCloseTagServiceImpl.update()",
        "notes": "Unlike create (idempotent), update throws on duplicate"
    },
    {
        "id": "TC-PLN-049", "title": "Update close-tag — no-op when same value",
        "preconditions": "Tag '[closed]' exists",
        "steps": "1. PATCH tag with body: {tag: '[closed]'} (same value)",
        "expected": "200 OK. Returns immediately without DB write (no-op optimization).",
        "priority": "Low", "type": "Functional",
        "req_ref": "", "module": "PlannerCloseTagServiceImpl.update()",
        "notes": ""
    },
    {
        "id": "TC-PLN-050", "title": "Delete close-tag",
        "preconditions": "Tag {tagId} exists for project {projectId}. User is admin.",
        "steps": "1. DELETE /v1/projects/{projectId}/close-tags/{tagId}\n2. GET /v1/projects/{projectId}/close-tags",
        "expected": "Step 1: 200 OK.\nStep 2: deleted tag no longer in list.",
        "priority": "High", "type": "Functional",
        "req_ref": "#2724", "module": "PlannerCloseTagController",
        "notes": ""
    },
    {
        "id": "TC-PLN-051", "title": "Close-tag permission — plain employee cannot create/update/delete",
        "preconditions": "User is a plain employee (not admin, PM, senior manager, or owner)",
        "steps": "1. GET /v1/projects/{projectId}/close-tags (should work)\n2. POST /v1/projects/{projectId}/close-tags with body: {tag: '[test]'}\n3. PATCH existing tag\n4. DELETE existing tag",
        "expected": "Step 1: 200 OK (list is allowed).\nSteps 2-4: 403 Forbidden (permission denied by PlannerCloseTagPermissionService).",
        "priority": "High", "type": "Security",
        "req_ref": "", "module": "PlannerCloseTagPermissionService",
        "notes": "Authorized: admin, PM, senior manager, owner. Denied: everyone else."
    },
    {
        "id": "TC-PLN-052", "title": "Close-tag permission — senior manager can manage tags",
        "preconditions": "User is senior manager of the project",
        "steps": "1. POST /v1/projects/{projectId}/close-tags with body: {tag: '[sm-tag]'}",
        "expected": "200 OK. Senior manager gets all 3 permissions (CREATE+EDIT+DELETE).",
        "priority": "Medium", "type": "Security",
        "req_ref": "", "module": "PlannerCloseTagPermissionService",
        "notes": "All-or-nothing permission grant"
    },
    {
        "id": "TC-PLN-053", "title": "Close-tag permission — project owner can manage tags",
        "preconditions": "User is project owner",
        "steps": "1. POST /v1/projects/{projectId}/close-tags with body: {tag: '[owner-tag]'}",
        "expected": "200 OK. Owner gets CREATE+EDIT+DELETE permissions.",
        "priority": "Medium", "type": "Security",
        "req_ref": "", "module": "PlannerCloseTagPermissionService",
        "notes": ""
    },
    {
        "id": "TC-PLN-054", "title": "Close-tag — cross-project manipulation rejected",
        "preconditions": "Tag belongs to project A. User tries to delete via project B endpoint.",
        "steps": "1. DELETE /v1/projects/{projectB_id}/close-tags/{tagFromProjectA_id}",
        "expected": "404 Not Found or 400 Bad Request. Cross-project validation prevents manipulation.",
        "priority": "Medium", "type": "Security",
        "req_ref": "", "module": "PlannerCloseTagServiceImpl",
        "notes": "Cross-project validation in delete/update"
    },
    {
        "id": "TC-PLN-055", "title": "Close-tag — non-existent project returns 404",
        "preconditions": "Valid API token",
        "steps": "1. GET /v1/projects/999999/close-tags",
        "expected": "404 Not Found. @ProjectIdExists validation on path variable.",
        "priority": "Low", "type": "Negative",
        "req_ref": "", "module": "PlannerCloseTagController",
        "notes": ""
    },
    {
        "id": "TC-PLN-056", "title": "Close-by-tag — auto-close during tracker sync",
        "preconditions": "Project has close-tag '[closed]'. Task has ticket with '[closed]' in name/info.",
        "steps": "1. Trigger tracker sync (Load from Tracker) for the project\n2. GET assignments for employee+date",
        "expected": "Assignments matching the tag are auto-set to closed=true. Closed assignments shown only if they have reported hours.",
        "priority": "High", "type": "Integration",
        "req_ref": "#2724, Confluence 130386435 sec 7.4", "module": "CloseByTagService.apply()",
        "notes": "267-line service + 760-line integration test"
    },
]

# ── TS-Planner-Locks (cell locking) ──────────────────────────

TS_LOCKS = [
    {
        "id": "TC-PLN-057", "title": "Create lock on assignment field",
        "preconditions": "User authenticated. Assignment exists.",
        "steps": "1. POST /v1/locks with body: Set of LockDTO [{cellKey: 'assignment-{id}-comment', employeeLogin: '{login}', taskId: {id}, field: 'comment'}]",
        "expected": "200 OK. Returns set of created LockDTO objects. WebSocket LOCK event emitted.",
        "priority": "High", "type": "Functional",
        "req_ref": "", "module": "LockController",
        "notes": "Lockable assignment fields: remainingEstimate, comment, internalComment, uiData"
    },
    {
        "id": "TC-PLN-058", "title": "Lock TTL — expires after 1 minute",
        "preconditions": "Lock created at time T",
        "steps": "1. POST /v1/locks to create lock\n2. Wait >60 seconds without refreshing\n3. Another user: PATCH the same assignment field",
        "expected": "Step 3: 200 OK (lock expired, field editable). No 423 error.",
        "priority": "High", "type": "Functional",
        "req_ref": "", "module": "LockService",
        "notes": "Locks held for 1 minute, must re-invoke POST to extend"
    },
    {
        "id": "TC-PLN-059", "title": "Lock refresh — re-POST extends TTL",
        "preconditions": "Lock exists, about to expire",
        "steps": "1. POST /v1/locks with same lock set\n2. Verify lock is still active after original TTL",
        "expected": "Lock extended. Subsequent PATCH by another user still returns 423.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "LockService",
        "notes": ""
    },
    {
        "id": "TC-PLN-060", "title": "Lock conflict — same field by different user returns 423",
        "preconditions": "User A holds lock on assignment field 'comment'",
        "steps": "1. User B: POST /v1/locks with same cellKey/field",
        "expected": "423 Locked. Error indicates lock held by User A.",
        "priority": "High", "type": "Negative",
        "req_ref": "", "module": "LockService",
        "notes": ""
    },
    {
        "id": "TC-PLN-061", "title": "Lock — POST replaces previous locks for same employee",
        "preconditions": "User holds locks on fields A and B",
        "steps": "1. POST /v1/locks with only field C\n2. GET /v1/locks",
        "expected": "Only field C is locked. Previous locks on A and B are released. WebSocket UNLOCK events for A and B.",
        "priority": "High", "type": "Functional",
        "req_ref": "", "module": "LockController",
        "notes": "POST is a 'replace all locks' operation, not additive"
    },
    {
        "id": "TC-PLN-062", "title": "Delete all locks for current employee",
        "preconditions": "User holds multiple locks",
        "steps": "1. DELETE /v1/locks\n2. GET /v1/locks\n3. Another user: PATCH previously locked field",
        "expected": "Step 2: no locks for this employee.\nStep 3: 200 OK (field now editable).\nWebSocket UNLOCK events emitted.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "LockController",
        "notes": ""
    },
    {
        "id": "TC-PLN-063", "title": "Search locks for employee/date",
        "preconditions": "Multiple users hold locks",
        "steps": "1. GET /v1/locks with search parameters (employeeLogin, dates)",
        "expected": "200 OK. Returns set of active LockDTO objects matching search criteria.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "LockController",
        "notes": ""
    },
    {
        "id": "TC-PLN-064", "title": "Lock on TaskReport field — effort",
        "preconditions": "Report exists for employee",
        "steps": "1. POST /v1/locks with lock for report field 'effort'",
        "expected": "200 OK. Lock created. Lockable report fields: effort, reportComment, state, stateComment.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "LockController",
        "notes": "Locks cover both assignments and reports"
    },
    {
        "id": "TC-PLN-065", "title": "WebSocket LOCK/UNLOCK events",
        "preconditions": "WebSocket client subscribed to /topic/employees/{login}/locks",
        "steps": "1. POST /v1/locks — create lock\n2. DELETE /v1/locks — release lock\n3. Observe WebSocket events",
        "expected": "Step 1: LOCK event received with lock details.\nStep 2: UNLOCK event received.",
        "priority": "Medium", "type": "Integration",
        "req_ref": "", "module": "WsLockEventListener",
        "notes": "Events are async (@Async, @EventListener)"
    },
]

# ── TS-Planner-History (assignment history tab) ──────────────

TS_HISTORY = [
    {
        "id": "TC-PLN-066", "title": "Get assignment history for employee+task",
        "preconditions": "Employee has assignment changes recorded (show_in_history=true)",
        "steps": "1. GET /v1/assignments/history?employeeLogin={login}&taskId={id}&startDate=2026-03-01&endDate=2026-03-15",
        "expected": "200 OK. Paginated response with TaskAssignmentHistoryItemDTO objects showing change log.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "Confluence 130386435 (History tab)", "module": "TaskAssignmentHistoryService",
        "notes": "Tab 3 in Planner UI"
    },
    {
        "id": "TC-PLN-067", "title": "History — pagination support",
        "preconditions": "Employee has many history records",
        "steps": "1. GET /v1/assignments/history?...&page=0&pageSize=10\n2. GET with page=1",
        "expected": "Step 1: first 10 records, totalCount reflects all records.\nStep 2: next 10 records.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentHistoryService",
        "notes": "PageableUtil.correct(request) normalizes pagination params"
    },
    {
        "id": "TC-PLN-068", "title": "History — missing required fields returns 400",
        "preconditions": "Valid API token",
        "steps": "1. GET /v1/assignments/history (no params)\n2. GET with only employeeLogin",
        "expected": "400 Bad Request. Required: employeeLogin (@NotBlank), taskId (@NotNull), startDate, endDate.",
        "priority": "Medium", "type": "Negative",
        "req_ref": "", "module": "TaskAssignmentController",
        "notes": ""
    },
    {
        "id": "TC-PLN-069", "title": "History — only show_in_history=true records appear",
        "preconditions": "Some assignments have show_in_history=false in DB",
        "steps": "1. GET history for a period containing both show_in_history=true and false records",
        "expected": "Only records with show_in_history=true appear in response.",
        "priority": "Low", "type": "Functional",
        "req_ref": "", "module": "TaskAssignmentHistoryService",
        "notes": "DB column controls visibility"
    },
]

# ── TS-Planner-WebSocket (real-time, selections) ─────────────

TS_WEBSOCKET = [
    {
        "id": "TC-PLN-070", "title": "WebSocket connection with JWT token",
        "preconditions": "Valid JWT token for authenticated user",
        "steps": "1. Connect via STOMP/WebSocket (SockJS fallback) with JWT in connection headers\n2. Subscribe to /topic/employees/{login}/assignments/{period}",
        "expected": "Connection established. Subscription confirmed. Events received on assignment changes.",
        "priority": "High", "type": "Integration",
        "req_ref": "", "module": "WebsocketConfig / WebsocketSecurityConfig",
        "notes": "Dual auth: JWT or API token in headers"
    },
    {
        "id": "TC-PLN-071", "title": "WebSocket — CRUD events for assignments",
        "preconditions": "WebSocket subscribed to assignments channel",
        "steps": "1. Create assignment via POST\n2. Patch assignment via PATCH\n3. Observe WebSocket events",
        "expected": "ADD event on create, PATCH event on update. Each event contains Event<T> envelope with EventType, initiatorLogin, timestamp, payload.",
        "priority": "Medium", "type": "Integration",
        "req_ref": "", "module": "WsTaskAssignmentEventListener",
        "notes": "Events are @TransactionalEventListener — fire after commit"
    },
    {
        "id": "TC-PLN-072", "title": "WebSocket — selection events for cursor awareness",
        "preconditions": "Two users viewing same planner. WebSocket subscribed to /topic/employees/{login}/selections",
        "steps": "1. User A selects a cell in planner\n2. User B observes selection event",
        "expected": "SELECT event received with cell selection details. User B can see User A's cursor/selection.",
        "priority": "Low", "type": "Integration",
        "req_ref": "", "module": "WsSelectionEventListener",
        "notes": "Immediate @EventListener (not transactional)"
    },
    {
        "id": "TC-PLN-073", "title": "WebSocket — task rename cascades to 3 channels",
        "preconditions": "Task used in planner has assignments and reports",
        "steps": "1. Rename task via API\n2. Observe WebSocket events on tasks, assignments, and reports channels",
        "expected": "TASK_RENAME event sent to /topic/projects/{id}/tasks, /topic/employees/{login}/assignments/{period}, and /topic/employees/{login}/reports/{period}.",
        "priority": "Medium", "type": "Integration",
        "req_ref": "", "module": "WsTaskEventListener",
        "notes": "Rename extracts sub-events and re-publishes to all 3 channels"
    },
    {
        "id": "TC-PLN-074", "title": "WebSocket — connection indicator (SocketManagerLed)",
        "preconditions": "Planner page open in browser",
        "steps": "1. Open planner page\n2. Verify connection indicator shows 'connected'\n3. Disconnect network briefly\n4. Reconnect",
        "expected": "Step 2: LED indicator green/connected.\nStep 3: LED shows disconnected.\nStep 4: SockJS reconnects, LED green again.",
        "priority": "Low", "type": "UI",
        "req_ref": "", "module": "SocketManagerLed (frontend)",
        "notes": "SockJS provides automatic reconnection"
    },
]

# ── TS-Planner-Bugs (known bug verification) ─────────────────

TS_BUGS = [
    {
        "id": "TC-PLN-075", "title": "BUG #3314: Order resets on 'Open for Editing'",
        "preconditions": "Employee has manually DnD-reordered assignments on a date",
        "steps": "1. Note current custom assignment order\n2. In planner UI, click 'Open for Editing' for the same date\n3. Observe assignment order",
        "expected": "KNOWN BUG (Open): Order resets. Backend returns correct order (confirmed by developer jsaidov) but frontend doesn't preserve it when switching to edit mode.\nExpected fix: frontend should maintain backend-provided order.",
        "priority": "High", "type": "Bug verification",
        "req_ref": "#3314", "module": "Frontend planner module",
        "notes": "Frontend bug — API returns correct order"
    },
    {
        "id": "TC-PLN-076", "title": "BUG #3332: Tasks duplicated after DnD reorder",
        "preconditions": "Planner open in Chrome or Firefox",
        "steps": "1. Open planner for an employee with multiple assignments\n2. Drag-drop an assignment to reorder\n3. Observe task list",
        "expected": "KNOWN BUG (Open): Duplicate entries appear in the task list after DnD. Reproducible in both Chrome and Firefox.\nExpected: no duplicates after DnD.",
        "priority": "High", "type": "Bug verification",
        "req_ref": "#3332 (originally #3255)", "module": "Frontend Redux/generateAssignments",
        "notes": "Pure frontend state management bug"
    },
    {
        "id": "TC-PLN-077", "title": "BUG #3375: Member order in project planner broken",
        "preconditions": "Project has custom employee order set via 'Project Settings' popup DnD",
        "steps": "1. Set custom employee order in Project Settings popup\n2. View project planner (Projects tab)\n3. Compare employee order with popup order",
        "expected": "KNOWN BUG (In Progress): After #3258 fix, employee order changed to alphabetical instead of matching Project Settings popup DnD order.\nExpected: employee order should match popup order.",
        "priority": "High", "type": "Bug verification",
        "req_ref": "#3375 (regression from #3258)", "module": "Frontend + backend",
        "notes": "Regression from #3258 fix"
    },
    {
        "id": "TC-PLN-078", "title": "BUG: System.out.println in production code",
        "preconditions": "Access to server logs during assignment move",
        "steps": "1. Move assignment via PATCH with nextAssignmentId\n2. Check server stdout/application logs",
        "expected": "KNOWN DEBT: System.out.println output visible in logs at line 406 of InternalTaskAssignmentService.moveFutureAssignmentsAccordingly(). Should be replaced with proper logging.",
        "priority": "Low", "type": "Bug verification",
        "req_ref": "", "module": "InternalTaskAssignmentService (line 406)",
        "notes": "Technical debt — debug code in production"
    },
    {
        "id": "TC-PLN-079", "title": "BUG: Generate destroys manual DnD ordering",
        "preconditions": "Employee has manually reordered assignments via DnD",
        "steps": "1. DnD-reorder assignments to custom order\n2. Navigate away from planner\n3. Return and click 'Open for Editing' (triggers generate)\n4. Compare order",
        "expected": "KNOWN BEHAVIOR: generate() overwrites all position and nextAssignmentId values based on current search results. Manual ordering is lost.\nRequirements say 'Opening for edit must NOT reorder' — this is violated.",
        "priority": "High", "type": "Bug verification",
        "req_ref": "#3314, Confluence 130386435 (point 8.3)", "module": "TaskAssignmentServiceImpl.generate()",
        "notes": "Requirements explicitly say verify this doesn't happen"
    },
    {
        "id": "TC-PLN-080", "title": "Verify #3258 fix: assignment order + add-task",
        "preconditions": "Release/2.1 deployed",
        "steps": "1. Open planner for employee\n2. DnD reorder assignments\n3. Add a new task to planner\n4. Verify order is preserved after add",
        "expected": "Assignment order preserved after adding new task (fix from #3258 applied).",
        "priority": "Medium", "type": "Bug verification",
        "req_ref": "#3258 (Closed)", "module": "Frontend + backend",
        "notes": "Verify regression fix is stable"
    },
    {
        "id": "TC-PLN-081", "title": "Verify #3308 fix: DnD order persisted across days",
        "preconditions": "Release/2.1 deployed",
        "steps": "1. DnD reorder assignments on day D\n2. Navigate to day D+1\n3. Verify same order applies",
        "expected": "DnD order propagated to future days (fix from #3308 applied).",
        "priority": "Medium", "type": "Bug verification",
        "req_ref": "#3308 (Closed)", "module": "InternalTaskAssignmentService.moveFutureAssignmentsAccordingly()",
        "notes": "moveFutureAssignmentsAccordingly() implementation"
    },
]

# ── TS-Planner-UI (frontend-specific) ────────────────────────

TS_UI = [
    {
        "id": "TC-PLN-082", "title": "Planner page — 3 tabs visible (Tasks, Reports, History)",
        "preconditions": "User logged in, planner page accessible",
        "steps": "1. Navigate to planner page\n2. Verify 3 tabs are visible",
        "expected": "Tab 1: Tasks (drag-drop assignment table). Tab 2: Reports (embedded report module). Tab 3: History (change log).",
        "priority": "Medium", "type": "UI",
        "req_ref": "Confluence 130386435", "module": "PlannerPage / PlannerTabs",
        "notes": ""
    },
    {
        "id": "TC-PLN-083", "title": "New task highlighted green for 5 seconds",
        "preconditions": "Planner open on Tasks tab",
        "steps": "1. Add a new task to planner\n2. Observe highlighting",
        "expected": "New task row highlighted green for 5 seconds, then returns to normal. Auto-scroll to new task if off-screen.",
        "priority": "Low", "type": "UI",
        "req_ref": "Confluence 130386435", "module": "Frontend planner module",
        "notes": ""
    },
    {
        "id": "TC-PLN-084", "title": "Project Settings popup — two tabs",
        "preconditions": "User is PM/admin for a project. Planner open.",
        "steps": "1. Click 'Project Settings' (or gear icon)\n2. Verify popup has 2 tabs: 'Project Members' and 'Tasks Closing'",
        "expected": "Tab 1 (Project Members): employee dropdown, role field, DnD reorder.\nTab 2 (Tasks Closing): close-by-tag management, max 200 chars per tag.",
        "priority": "Medium", "type": "UI",
        "req_ref": "Confluence 130386435 sec 7.3-7.4", "module": "Frontend planner module",
        "notes": "Renamed from 'Employees on project' to 'Project Settings'"
    },
    {
        "id": "TC-PLN-085", "title": "Project members — add/remove with notification",
        "preconditions": "User is PM/admin. Project Settings popup open on 'Project Members' tab.",
        "steps": "1. Add employee from dropdown\n2. Verify employee appears immediately\n3. Remove an employee\n4. Verify removal",
        "expected": "Add: immediate UI update, notification sent. Remove: immediate, notification sent. DnD reorder available for member list.",
        "priority": "Medium", "type": "Functional",
        "req_ref": "Confluence 130386435 sec 7.3", "module": "Frontend planner / WsProjectMemberEventListener",
        "notes": "WebSocket ADD/DELETE events for members"
    },
    {
        "id": "TC-PLN-086", "title": "Planner — localStorage persistence of plannerTasks",
        "preconditions": "Browser with localStorage enabled",
        "steps": "1. Open planner, search/add tasks\n2. Close browser tab\n3. Reopen planner page",
        "expected": "Previously searched/added tasks restored from localStorage (plannerTasks Redux slice auto-synced).",
        "priority": "Low", "type": "Functional",
        "req_ref": "", "module": "Frontend plannerTasks Redux slice",
        "notes": "Risk: stale data if not cleared on logout"
    },
    {
        "id": "TC-PLN-087", "title": "Planner — concurrent editing with cell locking UI",
        "preconditions": "Two users viewing same planner. Both logged in.",
        "steps": "1. User A clicks to edit a cell (comment field)\n2. User B sees lock indicator on that cell\n3. User B tries to edit same cell\n4. User A finishes editing",
        "expected": "Step 2: lock indicator visible. Step 3: edit prevented or warning shown. Step 4: lock released, User B can now edit.",
        "priority": "High", "type": "Functional",
        "req_ref": "", "module": "Frontend SocketManager + LockController",
        "notes": "Core collaborative editing UX"
    },
    {
        "id": "TC-PLN-088", "title": "Planner — DnD reorder assignments in Tasks tab",
        "preconditions": "Employee has multiple generated assignments",
        "steps": "1. Open planner Tasks tab\n2. Drag assignment from position 3 to position 1\n3. Verify order change persists",
        "expected": "Assignment moves to new position. PATCH sent to backend with nextAssignmentId. WebSocket PATCH event emitted. Order persists on page reload.",
        "priority": "High", "type": "Functional",
        "req_ref": "Confluence 130386435", "module": "Frontend + InternalTaskAssignmentService.move()",
        "notes": ""
    },
]

# ═══════════════════════════════════════════════════════════════
#  WORKBOOK GENERATION
# ═══════════════════════════════════════════════════════════════

ALL_SUITES = {
    "TS-Planner-Search": {"data": TS_SEARCH, "desc": "Assignment search API — parameters, validation, response structure"},
    "TS-Planner-CRUD": {"data": TS_CRUD, "desc": "Assignment create and patch — fields, validation, errors (409/423)"},
    "TS-Planner-Generate": {"data": TS_GENERATE, "desc": "Assignment generation — ordering reset, project filter, idempotency"},
    "TS-Planner-Ordering": {"data": TS_ORDERING, "desc": "Drag-drop ordering — move, future propagation, dual mechanism"},
    "TS-Planner-CloseTag": {"data": TS_CLOSETAG, "desc": "Close-by-tag CRUD — permissions, idempotent create, validation"},
    "TS-Planner-Locks": {"data": TS_LOCKS, "desc": "Cell locking — TTL, conflict, replace, WebSocket events"},
    "TS-Planner-History": {"data": TS_HISTORY, "desc": "Assignment history — pagination, filtering, show_in_history"},
    "TS-Planner-WebSocket": {"data": TS_WEBSOCKET, "desc": "Real-time WebSocket — STOMP, events, selections, rename cascade"},
    "TS-Planner-Bugs": {"data": TS_BUGS, "desc": "Known bug verification — #3314, #3332, #3375, ordering issues"},
    "TS-Planner-UI": {"data": TS_UI, "desc": "Frontend-specific — tabs, DnD UX, localStorage, concurrent editing"},
}


def create_plan_overview(wb):
    ws = wb.active
    ws.title = "Plan Overview"
    ws.sheet_properties.tabColor = TAB_COLOR_PLAN

    ws.cell(row=1, column=1, value="Planner Module — Test Plan").font = FONT_TITLE
    ws.cell(row=2, column=1, value=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}").font = FONT_SMALL
    ws.cell(row=3, column=1, value="Phase B — TTT Expert System, Session 68").font = FONT_SMALL

    row = 5
    ws.cell(row=row, column=1, value="Scope").font = FONT_SECTION
    ws.cell(row=row, column=1).fill = FILL_SECTION
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    row += 1
    scope_items = [
        "Assignment CRUD (search, create, patch) — REST API endpoints with validation",
        "Assignment generation ('Open for Editing') — from recent non-closed + task reports",
        "Drag-drop ordering — move with future propagation, dual ordering (position + linked-list)",
        "Close-by-tag — CRUD with object-level permissions (admin/PM/SM/owner)",
        "Cell locking — 1-minute TTL, conflict detection, WebSocket events",
        "Assignment history — paginated change log",
        "WebSocket real-time — STOMP/SockJS, 12 event types across 7 channels",
        "Known bugs — 5 interconnected ordering tickets (#3258, #3308, #3314, #3332, #3375)",
        "Frontend UX — 3 tabs, Project Settings popup, localStorage persistence",
    ]
    for item in scope_items:
        ws.cell(row=row, column=1, value=f"  - {item}").font = FONT_BODY
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="Environment Requirements").font = FONT_SECTION
    ws.cell(row=row, column=1).fill = FILL_SECTION
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    row += 1
    env_items = [
        "Testing environment: ttt-timemachine.noveogroup.com (primary), ttt-qa-1.noveogroup.com (secondary)",
        "Multiple user accounts: admin, PM, senior manager, owner, plain employee",
        "Projects with tracker integration configured (for close-by-tag testing)",
        "Employees with generated assignments across multiple dates",
        "WebSocket client (browser DevTools or Playwright) for real-time event verification",
        "Database access for data integrity checks (task_assignment, planner_close_tag tables)",
    ]
    for item in env_items:
        ws.cell(row=row, column=1, value=f"  - {item}").font = FONT_BODY
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="Test Suites").font = FONT_SECTION
    ws.cell(row=row, column=1).fill = FILL_SECTION
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    row += 1

    total = 0
    for suite_name, suite_info in ALL_SUITES.items():
        count = len(suite_info["data"])
        total += count
        cell = ws.cell(row=row, column=1, value=f"{suite_name} — {count} cases")
        cell.font = FONT_LINK_BOLD
        cell.hyperlink = f"#'{suite_name}'!A1"
        ws.cell(row=row, column=2, value=suite_info["desc"]).font = FONT_BODY
        row += 1

    row += 1
    ws.cell(row=row, column=1, value=f"TOTAL: {total} test cases across {len(ALL_SUITES)} suites").font = FONT_SECTION

    ws.column_dimensions["A"].width = 45
    ws.column_dimensions["B"].width = 70
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 20


def create_feature_matrix(wb):
    ws = wb.create_sheet("Feature Matrix")
    ws.sheet_properties.tabColor = TAB_COLOR_PLAN

    ws.cell(row=1, column=1, value="Feature x Test Type Matrix").font = FONT_TITLE
    add_back_link(ws, row=2)

    headers = ["Feature Area", "Functional", "Negative", "Boundary", "Security",
               "Integration", "Bug Verif.", "UI", "Data Integrity", "Edge Case", "Total", "Suite Link"]
    row = 4
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_GREEN_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    features = [
        ("Assignment Search", "TS-Planner-Search"),
        ("Assignment CRUD", "TS-Planner-CRUD"),
        ("Assignment Generation", "TS-Planner-Generate"),
        ("DnD Ordering", "TS-Planner-Ordering"),
        ("Close-by-Tag", "TS-Planner-CloseTag"),
        ("Cell Locking", "TS-Planner-Locks"),
        ("History", "TS-Planner-History"),
        ("WebSocket Events", "TS-Planner-WebSocket"),
        ("Known Bugs", "TS-Planner-Bugs"),
        ("Frontend UI", "TS-Planner-UI"),
    ]

    type_cols = ["Functional", "Negative", "Boundary", "Security",
                 "Integration", "Bug verification", "UI", "Data Integrity", "Edge Case"]

    for i, (feature, suite_key) in enumerate(features):
        r = row + 1 + i
        fill = FILL_ROW_EVEN if i % 2 == 0 else FILL_ROW_ODD
        ws.cell(row=r, column=1, value=feature).font = FONT_BODY
        ws.cell(row=r, column=1).fill = fill
        ws.cell(row=r, column=1).border = THIN_BORDER

        cases = ALL_SUITES[suite_key]["data"]
        total = 0
        for j, ttype in enumerate(type_cols, 2):
            count = sum(1 for c in cases if ttype.lower() in c["type"].lower())
            cell = ws.cell(row=r, column=j, value=count if count > 0 else "")
            cell.font = FONT_BODY
            cell.alignment = ALIGN_CENTER
            cell.fill = fill
            cell.border = THIN_BORDER
            total += count

        # Some cases might not match any type_col exactly; count total from data
        actual_total = len(cases)
        ws.cell(row=r, column=11, value=actual_total).font = Font(name="Arial", bold=True, size=10)
        ws.cell(row=r, column=11).alignment = ALIGN_CENTER
        ws.cell(row=r, column=11).fill = fill
        ws.cell(row=r, column=11).border = THIN_BORDER

        link_cell = ws.cell(row=r, column=12, value=suite_key)
        link_cell.font = FONT_LINK
        link_cell.hyperlink = f"#'{suite_key}'!A1"
        link_cell.fill = fill
        link_cell.border = THIN_BORDER

    # Totals row
    total_row = row + 1 + len(features)
    ws.cell(row=total_row, column=1, value="TOTAL").font = Font(name="Arial", bold=True, size=11)
    ws.cell(row=total_row, column=1).fill = FILL_SECTION
    ws.cell(row=total_row, column=1).border = THIN_BORDER
    grand_total = sum(len(s["data"]) for s in ALL_SUITES.values())
    ws.cell(row=total_row, column=11, value=grand_total).font = Font(name="Arial", bold=True, size=11)
    ws.cell(row=total_row, column=11).fill = FILL_SECTION
    ws.cell(row=total_row, column=11).border = THIN_BORDER

    for col in range(1, 13):
        ws.column_dimensions[get_column_letter(col)].width = 14
    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["L"].width = 22

    add_autofilter(ws, row, 12)


def create_risk_assessment(wb):
    ws = wb.create_sheet("Risk Assessment")
    ws.sheet_properties.tabColor = TAB_COLOR_PLAN

    ws.cell(row=1, column=1, value="Risk Assessment").font = FONT_TITLE
    add_back_link(ws, row=2)

    headers = ["Feature", "Risk", "Likelihood", "Impact", "Severity", "Mitigation / Test Focus"]
    row = 4
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_GREEN_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    risks = [
        ("DnD Ordering", "Dual ordering (position + linked-list) inconsistency causes wrong display order",
         "High", "High", "Critical", "TC-PLN-037: verify position↔linked-list consistency. TC-PLN-038: NULL position handling. TC-PLN-039: multiple position=0."),
        ("DnD Ordering", "Generate destroys manual ordering — user loses carefully arranged order",
         "High", "Medium", "High", "TC-PLN-026, TC-PLN-079: verify ordering is reset. Requirements say 'must NOT reorder' — violated by design."),
        ("Close-by-Tag", "Permission bypass: plain employee mutates tags via API",
         "Low", "High", "Medium", "TC-PLN-051: verify 403 for plain employee. TC-PLN-054: cross-project manipulation."),
        ("Cell Locking", "Stale locks after WebSocket disconnect block other users",
         "Medium", "Medium", "Medium", "TC-PLN-058: verify 1-minute TTL expiry. No heartbeat-based cleanup found."),
        ("Cell Locking", "Lock race condition: two users try to lock same cell simultaneously",
         "Medium", "Medium", "Medium", "TC-PLN-060: verify 423 on conflict."),
        ("Frontend DnD", "Task duplication bug (#3332) — phantom duplicates after DnD",
         "High", "Medium", "High", "TC-PLN-076: verify reproduction in Chrome/Firefox. Pure frontend state bug."),
        ("WebSocket", "Event loss on connection drop causes stale UI state",
         "Medium", "Medium", "Medium", "TC-PLN-074: SockJS reconnection. Lock cleanup after disconnect."),
        ("Close-by-Tag", "Tag max length discrepancy: requirements say 200, DB allows 255",
         "Low", "Low", "Low", "TC-PLN-046: test boundary at 255 chars. Document discrepancy."),
        ("Project Members", "Regression #3375: member order broken after #3258 fix",
         "High", "Medium", "High", "TC-PLN-077: verify employee order matches Project Settings popup."),
        ("Production Code", "System.out.println in production leaks debug info",
         "Low", "Low", "Low", "TC-PLN-078: verify in server logs. Technical debt to address."),
    ]

    for i, (feat, risk, like, impact, sev, mitigation) in enumerate(risks):
        r = row + 1 + i
        if sev == "Critical":
            fill = FILL_RISK_HIGH
        elif sev == "High":
            fill = FILL_RISK_HIGH
        elif sev == "Medium":
            fill = FILL_RISK_MED
        else:
            fill = FILL_RISK_LOW
        write_row(ws, r, [feat, risk, like, impact, sev, mitigation], fill=fill)

    add_autofilter(ws, row, len(headers))
    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 60


def main():
    wb = openpyxl.Workbook()

    create_plan_overview(wb)
    create_feature_matrix(wb)
    create_risk_assessment(wb)

    for suite_name, suite_info in ALL_SUITES.items():
        ws = wb.create_sheet(suite_name)
        ws.sheet_properties.tabColor = TAB_COLOR_TS
        write_ts_tab(ws, suite_name, suite_info["data"])

    out_path = "/home/v/Dev/ttt-expert-v1/expert-system/output/planner/planner.xlsx"
    wb.save(out_path)

    total = sum(len(s["data"]) for s in ALL_SUITES.values())
    print(f"Generated: {out_path}")
    print(f"  Tabs: {len(ALL_SUITES) + 3} (3 plan + {len(ALL_SUITES)} test suites)")
    print(f"  Test cases: {total}")
    for name, info in ALL_SUITES.items():
        print(f"    {name}: {len(info['data'])} cases")


if __name__ == "__main__":
    main()

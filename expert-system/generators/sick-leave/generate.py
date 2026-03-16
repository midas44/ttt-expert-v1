#!/usr/bin/env python3
"""Generate sick-leave.xlsx — unified test workbook for Sick Leave module.

Phase B output for the TTT Expert System.
Covers: CRUD lifecycle, dual status model, accounting workflow,
        permissions & security, validation rules, API errors & edge cases.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

# ── Styling constants (identical to vacation workbook) ────────────

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


# ── Helper functions (identical to vacation workbook) ─────────────

def style_header_row(ws, row, num_cols, fill=None):
    """Apply header styling to a row."""
    f = fill or FILL_HEADER
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = FONT_HEADER
        cell.fill = f
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER


def write_row(ws, row, values, font=None, fill=None, alignment=None):
    """Write a row of values with optional styling."""
    for col, val in enumerate(values, 1):
        cell = ws.cell(row=row, column=col, value=val)
        cell.font = font or FONT_BODY
        cell.alignment = alignment or ALIGN_LEFT
        cell.border = THIN_BORDER
        if fill:
            cell.fill = fill


def auto_width(ws, min_width=10, max_width=60):
    """Set column widths based on content."""
    for col_cells in ws.columns:
        col_letter = get_column_letter(col_cells[0].column)
        max_len = min_width
        for cell in col_cells:
            if cell.value:
                lines = str(cell.value).split("\n")
                longest = max(len(line) for line in lines)
                max_len = max(max_len, min(longest + 2, max_width))
        ws.column_dimensions[col_letter].width = max_len


def add_autofilter(ws, row, num_cols):
    """Add autofilter to header row."""
    ws.auto_filter.ref = f"A{row}:{get_column_letter(num_cols)}{ws.max_row}"


def add_back_link(ws, row=1):
    """Add back-link to Plan Overview in row 1."""
    cell = ws.cell(row=row, column=1)
    cell.value = "<- Back to Plan"
    cell.font = FONT_LINK
    cell.hyperlink = "#'Plan Overview'!A1"


def write_ts_tab(ws, suite_name, test_cases):
    """Write a complete TS- tab with header, back-link, and test cases."""
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


# ── Test Case helper ──────────────────────────────────────────────

def tc(id_, title, pre, steps, expected, priority, type_, req, module, notes=""):
    return {
        "id": id_, "title": title, "preconditions": pre,
        "steps": steps, "expected": expected, "priority": priority,
        "type": type_, "req_ref": req, "module": module, "notes": notes
    }


# =====================================================================
# TEST CASE DATA — 6 suites
# =====================================================================

# ── TS-SL-Lifecycle ──────────────────────────────────────────────
# Create, edit, close, reopen, delete flows + file handling + notifications

TS_SL_LIFECYCLE = [
    tc("TC-SL-001",
       "Create sick leave with minimum required fields",
       "Logged in as employee. No active sick leaves overlapping target dates.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login: <own>, startDate: '2026-03-16', endDate: '2026-03-19', force: false}\n"
       "3. Verify response status 200\n"
       "4. GET /api/vacation/v1/sick-leaves/{id} to confirm",
       "Sick leave created with status=OPEN, accounting_status=NEW.\n"
       "total_days calculated (4 calendar days).\n"
       "work_days calculated from production calendar.\n"
       "Appears in employee's /sick-leave/my list.",
       "Critical", "Functional",
       "REQ-sick-leave Create", "SickLeaveServiceImpl, SickLeaveCreateValidator",
       "Core happy path. DB: SELECT * FROM ttt_vacation.sick_leave WHERE id=<new_id>"),

    tc("TC-SL-002",
       "Create sick leave with all optional fields",
       "Logged in as employee.\n"
       "2 valid colleague logins for notifyAlso.\n"
       "1 uploaded file UUID from POST /v1/files/upload.",
       "1. Upload file: POST /api/vacation/v1/files/upload (multipart PDF)\n"
       "2. POST /api/vacation/v1/sick-leaves\n"
       "3. Body: {login, startDate, endDate, force: false, number: 'BL-2026-001', "
       "filesIds: [<uuid>], notifyAlso: ['colleague1', 'colleague2']}",
       "Sick leave created with number, 1 file attached (sick_leave_file junction),\n"
       "2 notifyAlso recipients (sick_leave_notify_also records).\n"
       "All fields visible in detail modal.",
       "High", "Functional",
       "REQ-sick-leave", "SickLeaveServiceImpl",
       "Verify file and notifyAlso via DB queries"),

    tc("TC-SL-003",
       "Calendar days auto-calculation (total_days = endDate - startDate + 1)",
       "Create modal open.",
       "1. Select Start date = 2026-03-16 (Monday)\n"
       "2. Select End date = 2026-03-22 (Sunday)\n"
       "3. Observe Calendar days field",
       "Calendar days shows 7 (all calendar days including weekends).\n"
       "Field is read-only, auto-updated on date change.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       "total_days = end - start + 1 (calendar, not working)"),

    tc("TC-SL-004",
       "Work days auto-calculation excludes weekends per production calendar",
       "Sick leave created: Mon 2026-03-16 to Sun 2026-03-22 (7 calendar days).",
       "1. GET /api/vacation/v1/sick-leaves/{id}\n"
       "2. Check work_days field in response",
       "work_days = 5 (Mon-Fri, excluding Sat/Sun per office production calendar).\n"
       "Uses CalendarService for office-specific holiday computation.",
       "Medium", "Functional",
       "", "SickLeaveServiceImpl, CalendarService",
       "work_days visible only in accounting view column"),

    tc("TC-SL-005",
       "Create single-day sick leave (startDate = endDate)",
       "Logged in as employee.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate: '2026-03-16', endDate: '2026-03-16', force: false}",
       "Sick leave created with total_days=1, work_days=1 (if weekday).\n"
       "Boundary: minimum possible duration.",
       "Medium", "Boundary",
       "", "SickLeaveServiceImpl",
       "Frontend: selecting start auto-fills end with same date"),

    tc("TC-SL-006",
       "Create long-duration sick leave (>30 days, no upper limit)",
       "Logged in as employee.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate: '2026-01-01', endDate: '2026-04-30', force: false}",
       "Sick leave created successfully. total_days=120.\n"
       "No maximum duration validation exists.\n"
       "DB shows max observed = 140-141 days in production data.",
       "Low", "Boundary",
       "", "SickLeaveServiceImpl",
       "No upper limit on duration. Boundary: extreme values."),

    tc("TC-SL-007",
       "Create future sick leave -- computed SCHEDULED status",
       "Logged in as employee. Start date > today.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate: today+7, endDate: today+10, force: false}\n"
       "3. GET /api/vacation/v1/sick-leaves?statuses=SCHEDULED",
       "DB stores status=OPEN.\n"
       "API returns computed status=SCHEDULED (CASE WHEN in SQL query).\n"
       "UI shows State = 'Planned'.",
       "High", "Functional",
       "", "SickLeaveServiceImpl, SickLeaveRepository",
       "Computed at query time, never persisted"),

    tc("TC-SL-008",
       "Edit sick leave -- change dates, days recalculated",
       "Existing OPEN sick leave.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, startDate, endDate: original+3, force: false}\n"
       "3. Verify total_days and work_days updated",
       "Dates updated. total_days and work_days recalculated.\n"
       "NOTIFY_SICKLEAVE_DATES_CHANGED email sent.",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       "PatchDTO extends CreateDTO -- all create validations re-run"),

    tc("TC-SL-009",
       "Edit sick leave -- add/change certificate number",
       "Existing OPEN sick leave without number.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, startDate, endDate, force: false, number: 'BL-123'}",
       "Number field updated. NOTIFY_SICKLEAVE_NUMBER_CHANGED email sent.\n"
       "Number visible in detail modal and accounting view.",
       "Medium", "Functional",
       "", "SickLeaveServiceImpl",
       "Number optional until close"),

    tc("TC-SL-010",
       "Edit sick leave -- add files (two-step update)",
       "Existing sick leave with no attachments.",
       "1. POST /api/vacation/v1/files/upload (multipart, 2 PDFs)\n"
       "2. PATCH /api/vacation/v1/sick-leaves/{id} with filesIds: [uuid1, uuid2]\n"
       "3. Verify file junction records",
       "Files uploaded then linked via PATCH.\n"
       "NOTIFY_SICKLEAVE_FILES_ADDED sent (triggered on PATCH only, not create).\n"
       "DB: SELECT * FROM ttt_vacation.sick_leave_file WHERE sick_leave_id={id}",
       "High", "Functional",
       "", "SickLeaveServiceImpl, frontend-sick-leave-module",
       "Two-step: upload then patch. FilesAddedEvent on patch only."),

    tc("TC-SL-011",
       "Edit sick leave -- remove file (diff-and-sync)",
       "Existing sick leave with 2 file attachments.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: filesIds: [uuid1] (omit uuid2)\n"
       "3. Verify file junction records",
       "Diff-and-sync: removed file's junction record deleted.\n"
       "Remaining file intact. Original file record NOT deleted (only junction).",
       "Medium", "Functional",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-012",
       "Upload maximum 5 files -- boundary",
       "Create sick leave with 5 file UUIDs.",
       "1. Upload 5 files via POST /v1/files/upload\n"
       "2. POST /api/vacation/v1/sick-leaves with filesIds: [5 UUIDs]",
       "All 5 files accepted. @Size(max=5) on filesIds passes.",
       "High", "Boundary",
       "", "SickLeaveCreateRequestDTO",
       "Max 5 files per sick leave"),

    tc("TC-SL-013",
       "Upload 6th file -- @Size(max=5) violation",
       "6 uploaded file UUIDs.",
       "1. POST /api/vacation/v1/sick-leaves with filesIds: [6 UUIDs]",
       "HTTP 400 validation error.\n"
       "@Size(max=5) on filesIds field rejects the request.\n"
       "Frontend also blocks at 5.",
       "High", "Negative",
       "", "SickLeaveCreateRequestDTO",
       "BUG note: @Size on DTO but NOT enforced in service layer"),

    tc("TC-SL-014",
       "Upload non-allowed file type via API -- no backend MIME check",
       "Bypass frontend. Use curl directly.",
       "1. curl -X POST /api/vacation/v1/files/upload -F 'file=@malicious.exe'\n"
       "2. Include returned UUID in sick leave PATCH",
       "SECURITY: Backend accepts ANY file type.\n"
       "No MIME type validation on server side.\n"
       "Only frontend checks file types (PDF, PNG, JPEG).",
       "Critical", "Security",
       "BUG-SL (S15)", "FileService, SickLeaveServiceImpl",
       "No backend MIME validation -- potential malicious upload vector"),

    tc("TC-SL-015",
       "Close (end) sick leave -- number required for close",
       "Existing OPEN sick leave.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, startDate, endDate, force: false, status: 'CLOSED'}\n"
       "3. Without number field",
       "HTTP 400: exception.validation.sickLeave.number.empty\n"
       "Number is required when closing.\n"
       "Frontend enforces via Yup schema mode switch.",
       "High", "Negative",
       "REQ-sick-leave Close", "SickLeaveServiceImpl",
       "Number becomes required (*) during close flow"),

    tc("TC-SL-016",
       "Close sick leave -- with valid number",
       "Existing OPEN sick leave.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, startDate, endDate, force: false, status: 'CLOSED', number: 'BL-CLOSE-001'}",
       "Status changes to CLOSED. State shows 'Ended'.\n"
       "NOTIFY_SICKLEAVE_CLOSED email sent.\n"
       "Number stored permanently.",
       "Critical", "Functional",
       "REQ-sick-leave Close", "SickLeaveServiceImpl",
       "Core close flow"),

    tc("TC-SL-017",
       "Close dialog title bug -- says 'Delete' instead of 'End'",
       "Existing OPEN sick leave. UI close flow.",
       "1. Click end/close action button on sick leave row\n"
       "2. Observe dialog title text",
       "BUG: Dialog title says 'Delete the sick note?' instead of 'End the sick note?'.\n"
       "Functionally closes (not deletes). Confusing UX.",
       "Medium", "Bug verification",
       "BUG-SL (S31)", "frontend-sick-leave-module",
       "Known bug from session 31 UI exploration"),

    tc("TC-SL-018",
       "Reopen closed sick leave via PATCH status=OPEN",
       "Existing CLOSED sick leave (accounting_status=NEW).",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, startDate, endDate, force: false, status: 'OPEN'}",
       "Status changes back to OPEN.\n"
       "State recalculated based on dates (Started/Overdue/Planned).\n"
       "No guard conditions on reopen.",
       "Medium", "Functional",
       "", "SickLeaveServiceImpl",
       "Direct status overwrite, no intermediate validation"),

    tc("TC-SL-019",
       "Delete sick leave -- soft delete (status=DELETED)",
       "Existing non-PAID sick leave.",
       "1. DELETE /api/vacation/v1/sick-leaves/{id}\n"
       "2. Verify response\n"
       "3. SELECT status FROM ttt_vacation.sick_leave WHERE id={id}",
       "Soft delete: status=DELETED in DB. Record not physically removed.\n"
       "NOTIFY_SICKLEAVE_DELETE email sent.\n"
       "Row disappears from default list view.",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       "Soft-delete only"),

    tc("TC-SL-020",
       "Delete PAID sick leave -- blocked",
       "Sick leave with accounting_status=PAID.",
       "1. DELETE /api/vacation/v1/sick-leaves/{id}\n"
       "2. Check error response",
       "HTTP 400: exception.validation.sickLeave.delete.closed\n"
       "Cannot delete PAID sick leave. Guard in service layer.",
       "High", "Negative",
       "", "SickLeaveServiceImpl",
       "Guard: accounting_status != PAID"),

    tc("TC-SL-021",
       "Delete leaves orphaned file and notifyAlso records",
       "Sick leave with 2 files + 2 notifyAlso recipients.",
       "1. DELETE /api/vacation/v1/sick-leaves/{id}\n"
       "2. SELECT * FROM ttt_vacation.sick_leave_file WHERE sick_leave_id={id}\n"
       "3. SELECT * FROM ttt_vacation.sick_leave_notify_also WHERE sick_leave_id={id}",
       "BUG: Junction records remain orphaned after soft-delete.\n"
       "sick_leave_file and sick_leave_notify_also NOT cleaned up.\n"
       "Only status changed to DELETED.",
       "Medium", "Bug verification",
       "BUG-SL-5", "SickLeaveServiceImpl",
       "Known tech debt: orphaned junction records"),

    tc("TC-SL-022",
       "Create overlapping sick leave -- force=false (409 Conflict)",
       "Existing OPEN sick leave: 2026-03-10 to 2026-03-15.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate: '2026-03-12', endDate: '2026-03-18', force: false}",
       "HTTP 409: exception.validation.sickLeave.dates.crossing\n"
       "Frontend shows overlap dialog with force/cancel options.",
       "High", "Negative",
       "", "SickLeaveServiceImpl",
       "Overlap detected against active (non-DELETED, non-REJECTED) sick leaves"),

    tc("TC-SL-023",
       "Create overlapping sick leave -- force=true (allowed)",
       "Existing overlap detected. Overlap dialog shown.",
       "1. Resend POST with force=true\n"
       "2. Verify creation succeeds",
       "Sick leave created despite overlap.\n"
       "Both active sick leaves coexist in DB.",
       "Medium", "Functional",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-024",
       "Create sick leave crossing active vacation -- SickLeaveCrossingVacationException",
       "Employee has active vacation 2026-03-10 to 2026-03-20.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate: '2026-03-12', endDate: '2026-03-18', force: false}",
       "HTTP 409: exception.sick.leave.crossing.vacation\n"
       "If force=true: creates and publishes VacationOverlap event.\n"
       "NOTIFY_EMPLOYEE_SICKLEAVE_OVERLAPS_VACATION email sent.",
       "High", "Functional",
       "REQ-sick-leave VacationCrossing", "SickLeaveServiceImpl",
       "Vacation crossing check separate from sick leave overlap check"),

    tc("TC-SL-025",
       "Notification: create -- NOTIFY_SICKLEAVE_OPEN (employee creates own)",
       "Employee creates own sick leave.",
       "1. Create sick leave as employee\n"
       "2. Check email via GET /api/email/v1/emails?to=<manager>",
       "NOTIFY_SICKLEAVE_OPEN template sent.\n"
       "Recipients: employee's manager + notifyAlso + per-office receivers.",
       "High", "Functional",
       "REQ-sick-leave Notify", "SickLeaveNotificationService",
       "Async after @TransactionalEventListener"),

    tc("TC-SL-026",
       "Notification: create by supervisor -- different template",
       "Manager creates sick leave for subordinate.",
       "1. POST /api/vacation/v1/sick-leaves as manager with subordinate's login\n"
       "2. Check email template used",
       "NOTIFY_SICKLEAVE_OPEN_BY_SUPERVISOR template sent (not OPEN).\n"
       "Editor type should be SUPERVISOR but BUG: getEditorType() uses ==.",
       "High", "Functional",
       "", "SickLeaveNotificationService",
       "Editor type determines template variant. See TC-SL-108 for bug."),

    tc("TC-SL-027",
       "Notification: close -- NOTIFY_SICKLEAVE_CLOSED",
       "Close an OPEN sick leave with number.",
       "1. PATCH status=CLOSED with number\n"
       "2. Check email",
       "NOTIFY_SICKLEAVE_CLOSED template sent.\n"
       "Includes sick leave details and closing number.",
       "Medium", "Functional",
       "", "SickLeaveNotificationService",
       "Chain-of-responsibility dispatch"),

    tc("TC-SL-028",
       "Notification: dates changed -- NOTIFY_SICKLEAVE_DATES_CHANGED",
       "Edit sick leave dates.",
       "1. PATCH with changed endDate\n"
       "2. Check email",
       "NOTIFY_SICKLEAVE_DATES_CHANGED template sent.\n"
       "Includes old and new date values.",
       "Medium", "Functional",
       "", "SickLeaveNotificationService",
       ""),

    tc("TC-SL-029",
       "Notification: files added -- triggered on PATCH only, not create",
       "Add files to existing sick leave.",
       "1. Upload file, PATCH with filesIds\n"
       "2. Check email\n"
       "3. Create NEW sick leave with filesIds\n"
       "4. Check if FilesAdded email sent",
       "PATCH: NOTIFY_SICKLEAVE_FILES_ADDED sent.\n"
       "CREATE: no FilesAdded notification (only SickLeaveCreatedEvent).\n"
       "FilesAddedEvent published only on patch path.",
       "Medium", "Integration",
       "", "SickLeaveServiceImpl, SickLeaveNotificationService",
       "Asymmetric: files on create do NOT trigger FilesAdded notification"),

    tc("TC-SL-030",
       "Notification: delete -- NOTIFY_SICKLEAVE_DELETE",
       "Delete a sick leave.",
       "1. DELETE /api/vacation/v1/sick-leaves/{id}\n"
       "2. Check email",
       "NOTIFY_SICKLEAVE_DELETE template sent.\n"
       "Variant: _BY_SUPERVISOR if manager deletes.",
       "Medium", "Functional",
       "", "SickLeaveNotificationService",
       ""),

    tc("TC-SL-031",
       "Notification recipients -- full list verification",
       "Employee with manager, 2 notifyAlso, per-office receivers configured.",
       "1. Create sick leave with notifyAlso: ['colleague1', 'colleague2']\n"
       "2. Query: SELECT * FROM ttt_vacation.office_sick_leave_notification_receiver\n"
       "3. Verify all email recipients",
       "Email sent to: employee's manager + 2 notifyAlso + per-office receivers.\n"
       "All receive same template.",
       "Medium", "Functional",
       "", "SickLeaveNotificationService",
       "Per-office receivers configured in admin panel"),
]


# ── TS-SL-DualStatus ────────────────────────────────────────────
# Dual status model, accounting drives lifecycle, SCHEDULED/OVERDUE

TS_SL_DUALSTATUS = [
    tc("TC-SL-032",
       "Initial status on creation -- OPEN + NEW",
       "Create a new sick leave.",
       "1. POST /api/vacation/v1/sick-leaves (valid body)\n"
       "2. SELECT status, accounting_status FROM ttt_vacation.sick_leave WHERE id={new_id}",
       "status='OPEN', accounting_status='NEW'.\n"
       "Employee view shows State = 'Started' (if current dates).",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-033",
       "Computed SCHEDULED -- future start_date, OPEN in DB",
       "OPEN sick leave with start_date > today.",
       "1. GET /api/vacation/v1/sick-leaves?statuses=SCHEDULED\n"
       "2. Verify returned records",
       "Records with OPEN + future start_date returned as status=SCHEDULED.\n"
       "UI shows State = 'Planned'.\n"
       "Computed via CASE WHEN in SQL query, never stored.",
       "High", "Functional",
       "", "SickLeaveRepository",
       ""),

    tc("TC-SL-034",
       "Computed OVERDUE -- past end_date, OPEN in DB",
       "OPEN sick leave with end_date < today.",
       "1. GET /api/vacation/v1/sick-leaves?statuses=OVERDUE\n"
       "2. Check UI manager view",
       "Records with OPEN + past end_date returned as status=OVERDUE.\n"
       "UI shows State = 'Overdue'. Green checkmark action in manager view.\n"
       "OverdueSickLeaveCommand per-request check.",
       "High", "Functional",
       "", "SickLeaveRepository, OverdueSickLeaveCommand",
       ""),

    tc("TC-SL-035",
       "Read/write asymmetry -- PATCH rejects SCHEDULED and OVERDUE",
       "OPEN sick leave with computed status SCHEDULED.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id} with status=SCHEDULED\n"
       "2. PATCH with status=OVERDUE",
       "Error: SCHEDULED and OVERDUE are not valid write values.\n"
       "Only OPEN and CLOSED accepted for PATCH status field.\n"
       "SickLeavePatchRequestStatusTypeDTO enum has only OPEN/CLOSED.",
       "Medium", "Negative",
       "", "SickLeavePatchRequestDTO",
       "Design debt: computed statuses not writable"),

    tc("TC-SL-036",
       "Accounting: NEW -> PROCESSING transition",
       "Sick leave with accounting_status=NEW. Logged in as accountant.",
       "1. Open /accounting/sick-leaves\n"
       "2. Click Status dropdown on row\n"
       "3. Select 'Pending' (=PROCESSING)",
       "accounting_status updated to PROCESSING.\n"
       "accountant FK set to current user.\n"
       "Main status remains OPEN.",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       "Pending in UI = PROCESSING in DB"),

    tc("TC-SL-037",
       "Accounting: PROCESSING -> PAID -- auto-closes main status",
       "Sick leave: status=OPEN, accounting_status=PROCESSING.",
       "1. Change Status dropdown to 'Paid'\n"
       "2. Verify both statuses via API and DB",
       "accounting_status = PAID.\n"
       "Main status auto-changed to CLOSED (coupling rule).\n"
       "State shows 'Ended'.",
       "Critical", "Functional",
       "", "SickLeaveServiceImpl",
       "CRITICAL coupling: PAID -> auto-close"),

    tc("TC-SL-038",
       "Accounting: PROCESSING -> REJECTED -- sets main REJECTED",
       "Sick leave: status=OPEN, accounting_status=PROCESSING.",
       "1. Change Status dropdown to 'Rejected'\n"
       "2. Verify both statuses",
       "accounting_status = REJECTED.\n"
       "Main status auto-changed to REJECTED.\n"
       "NOTIFY_SICKLEAVE_REJECTED email sent.",
       "Critical", "Functional",
       "", "SickLeaveServiceImpl",
       "Coupling: REJECTED -> main REJECTED"),

    tc("TC-SL-039",
       "Accounting: NEW/PROCESSING on closed SL reopens to OPEN",
       "Sick leave: status=CLOSED, accounting_status=NEW.",
       "1. PATCH accounting_status to PROCESSING\n"
       "2. Verify main status",
       "accounting_status = PROCESSING.\n"
       "Main status changes from CLOSED to OPEN (reopened).\n"
       "Coupling: NEW/PROCESSING -> main status forced to OPEN.",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       "Unexpected reopen behavior"),

    tc("TC-SL-040",
       "BUG: Unrestricted PAID -> NEW transition (no guardrails)",
       "Sick leave: accounting_status=PAID (main=CLOSED).",
       "1. Change Status dropdown from Paid to New\n"
       "2. Verify both statuses\n"
       "3. SELECT status, accounting_status FROM ttt_vacation.sick_leave WHERE id={id}",
       "BUG: Transition succeeds. accounting_status=NEW.\n"
       "Main status may remain CLOSED (inconsistent orphaned state).\n"
       "No state machine guardrails prevent backward transitions.",
       "High", "Bug verification",
       "BUG-SL-3", "SickLeaveServiceImpl",
       "Any-to-any accounting transitions allowed"),

    tc("TC-SL-041",
       "BUG: REJECTED -> PAID transition (skips PROCESSING)",
       "Sick leave: accounting_status=REJECTED, status=REJECTED.",
       "1. Change Status dropdown from Rejected to Paid\n"
       "2. Verify statuses",
       "BUG: Transition succeeds. REJECTED -> PAID.\n"
       "Main status auto-set to CLOSED (coupling rule).\n"
       "No intermediate PROCESSING required.",
       "Medium", "Bug verification",
       "BUG-SL-3", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-042",
       "Status combination matrix -- valid data patterns",
       "Database access to timemachine.",
       "1. SELECT status, accounting_status, COUNT(*) FROM ttt_vacation.sick_leave GROUP BY 1,2 ORDER BY 3 DESC\n"
       "2. Compare with expected combinations",
       "Valid combinations:\n"
       "- OPEN/NEW: active, not processed\n"
       "- CLOSED/NEW: ended but never processed (62% backlog)\n"
       "- CLOSED/PAID: fully processed\n"
       "- REJECTED/REJECTED: both rejected\n"
       "- DELETED/NEW: soft-deleted\n"
       "Total: 348 records in timemachine.",
       "Low", "Functional",
       "", "SickLeaveServiceImpl",
       "Data quality observation"),

    tc("TC-SL-043",
       "Employee view -- State column, no accounting Status visible",
       "Logged in as employee with sick leaves.",
       "1. Navigate to /sick-leave/my\n"
       "2. Observe table columns",
       "Columns: Sick leave dates, Calendar days, Number, Accountant, State, Actions.\n"
       "NO Status (accounting) column visible.\n"
       "Employees cannot see accounting status.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-044",
       "Manager view -- State + Status as read-only text",
       "Logged in as PM/DM. Navigate to /vacation/sick-leaves-of-employees.",
       "1. Observe table columns\n"
       "2. Try to interact with Status column cell",
       "Both State and Status columns present.\n"
       "Status shown as plain text (not editable dropdown).\n"
       "Managers see but cannot change accounting status.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-045",
       "Accounting view -- Status as inline dropdown (no confirmation)",
       "Logged in as accountant. Navigate to /accounting/sick-leaves.",
       "1. Click on Status cell value in any row\n"
       "2. Observe dropdown behavior",
       "Status column shows inline dropdown for direct status change.\n"
       "No confirmation modal -- changes apply immediately on selection.\n"
       "SickLeaveAccountingStatusCell component.",
       "High", "Functional",
       "", "frontend-sick-leave-module",
       "Immediate PATCH on dropdown change"),

    tc("TC-SL-046",
       "Accounting status change persists accountant FK",
       "Logged in as accountant. Change any accounting status.",
       "1. Change status from New to Processing\n"
       "2. Check Accountant column in UI\n"
       "3. SELECT accountant FROM ttt_vacation.sick_leave WHERE id={id}",
       "Accountant column shows current user.\n"
       "DB accountant FK points to current user's employee ID.\n"
       "Auto-assigned on any accounting status change.",
       "Medium", "Functional",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-047",
       "BUG: Status filter shows 'Rejected Rejected' duplicate label",
       "Logged in as accountant on accounting page.",
       "1. Click Status filter dropdown\n"
       "2. Observe option labels",
       "BUG: Filter shows 'Rejected Rejected' (duplicated label).\n"
       "Other values: New, Pending, Paid.\n"
       "Label rendering error in frontend.",
       "Low", "Bug verification",
       "BUG-SL-4", "frontend-sick-leave-module",
       "Known bug from session 11 exploration"),
]


# ── TS-SL-Accounting ────────────────────────────────────────────
# Accountant workflow, page features, inline editing

TS_SL_ACCOUNTING = [
    tc("TC-SL-048",
       "Accounting page access -- requires accounting role",
       "1. User with ROLE_ACCOUNTANT\n2. User without ROLE_ACCOUNTANT",
       "1. Login as accountant -> navigate to /accounting/sick-leaves\n"
       "2. Login as regular employee -> attempt same URL",
       "Accountant: page loads with 10-column table.\n"
       "Non-accountant: redirected or access denied.\n"
       "Route requires VACATIONS:SICK_LEAVE_ACCOUNTING_VIEW.",
       "High", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-049",
       "Accounting page -- 10 columns displayed",
       "Logged in as accountant on /accounting/sick-leaves.",
       "1. Verify all column headers",
       "10 columns: Employee, Sick leave dates, Days, Work days,\n"
       "Sick note, Accountant, Salary office, State, Status, Actions.\n"
       "Richer than employee/manager views.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-050",
       "Salary office filter -- scoped to accountant's office by default",
       "Logged in as accountant.",
       "1. Click Salary office filter\n"
       "2. Count available options\n"
       "3. Select different office\n"
       "4. Verify table filters",
       "Filter shows available salary offices (up to 27).\n"
       "Default: accountant's own salary office.\n"
       "Table updates to show only selected office's sick leaves.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-051",
       "State filter -- 7 values (All, Started, Ended, Planned, Overdue, Rejected, Deleted)",
       "Logged in as accountant.",
       "1. Click State filter dropdown\n"
       "2. Verify options\n"
       "3. Select each filter, verify results",
       "7 filter values available. Each filters correctly.\n"
       "Maps to computed main status values.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-052",
       "Change NEW -> Processing via inline dropdown",
       "Sick leave with accounting_status=NEW in accounting view.",
       "1. Click Status dropdown on row\n"
       "2. Select 'Pending' (=PROCESSING)\n"
       "3. Verify status change",
       "Status changes immediately. No confirmation dialog.\n"
       "accountant FK set to current user.\n"
       "Direct PATCH on dropdown change.",
       "High", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-053",
       "Change Processing -> Paid with auto-close coupling",
       "Sick leave with accounting_status=PROCESSING.",
       "1. Change dropdown to 'Paid'\n"
       "2. Verify both State and Status columns",
       "Status = Paid. State changes to 'Ended' (main auto-closed).\n"
       "Accountant column updated. Critical coupling behavior.",
       "Critical", "Functional",
       "", "SickLeaveServiceImpl, frontend-sick-leave-module",
       ""),

    tc("TC-SL-054",
       "Add accountant comment via inline tooltip",
       "Sick leave record in accounting view.",
       "1. Click comment/speech-bubble action button\n"
       "2. Enter comment text in tooltip textarea\n"
       "3. Save",
       "Comment saved. Tooltip shows saved comment on hover.\n"
       "DB: accountant_comment field updated.\n"
       "Inline Tooltip component, not modal.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-055",
       "Edit sick leave from accounting view -- dates update",
       "Non-PAID sick leave in accounting view.",
       "1. Click pencil (edit) action button\n"
       "2. Change End date\n"
       "3. Save",
       "Edit dialog shows: Employee (read-only), Start date, End date,\n"
       "Calendar days (auto-calc), Sick note number.\n"
       "No accounting status field in dialog.\n"
       "Dates updated, days recalculated.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       "Accounting status managed only via inline dropdown"),

    tc("TC-SL-056",
       "Edit PAID sick leave -- admin only",
       "Sick leave with accounting_status=PAID. Test as accountant and admin.",
       "1. As accountant: try to edit PAID sick leave\n"
       "2. As admin: try to edit PAID sick leave",
       "Accountant: edit blocked (button disabled/hidden).\n"
       "Admin: edit allowed (admin override for PAID).\n"
       "exception.validation.sickLeave.update.closed for non-admin.",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       "Admin/CHIEF_ACCOUNTANT/office-accountant can edit PAID"),

    tc("TC-SL-057",
       "View file attachments from accounting -- sick note action",
       "Sick leave with file attachments in accounting view.",
       "1. Click clipboard/attachment action button (data-testid='sickleave-action-attachments')\n"
       "2. Verify files displayed",
       "Attachment panel opens showing uploaded files.\n"
       "View/download links accessible to accountant.\n"
       "'View sick note' action.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-058",
       "Overdue records -- green checkmark action in accounting view",
       "OPEN sick leave with end_date in the past (OVERDUE state).",
       "1. Filter State = Overdue\n"
       "2. Check action column",
       "Green checkmark action button visible.\n"
       "OverdueSickLeaveCommand per-request check surfaces warning.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module, SickLeaveServiceImpl",
       ""),

    tc("TC-SL-059",
       "Accounting page -- no create button",
       "Logged in as accountant on /accounting/sick-leaves.",
       "1. Scan page for 'Add a sick note' button",
       "No create button present.\n"
       "Accounting view is read/process-only.\n"
       "Sick leaves created from employee or manager views only.",
       "Low", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-060",
       "Column sorting -- all sortable columns",
       "Accounting page with multiple records.",
       "1. Click 'Sick leave dates' header\n"
       "2. Click 'Days' header\n"
       "3. Click 'Employee' header",
       "Table sorts by clicked column. Sort direction toggles.\n"
       "Sort encoding uses +/- prefix in API request parameter.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-061",
       "Accounting backlog visibility -- CLOSED/NEW records",
       "Timemachine data.",
       "1. Filter State = Ended, Status = New\n"
       "2. Observe record count",
       "Shows ~215 records (62% backlog).\n"
       "Sick leaves ended but never processed by accounting.\n"
       "Visible for processing in accounting view.",
       "Low", "Functional",
       "", "SickLeaveServiceImpl",
       "Data quality observation"),

    tc("TC-SL-062",
       "BUG: NoveoAI widget overlaps Status/Actions columns",
       "Accounting page on standard viewport width.",
       "1. Observe right side of table\n"
       "2. Check if floating NoveoAI widget blocks interactions",
       "BUG: NoveoAI floating widget overlaps Status and Actions columns.\n"
       "Blocks dropdown and action button interaction.\n"
       "Workaround: wider viewport or hide widget.",
       "Low", "Bug verification",
       "BUG-SL-8", "frontend-sick-leave-module",
       "Known UI overlap issue"),

    tc("TC-SL-063",
       "Only accountantComment modifiable on DELETED sick leaves",
       "Sick leave with status=DELETED.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, startDate, endDate, force: false, accountantComment: 'note'}",
       "Only accountantComment field should be modifiable.\n"
       "Date changes and status changes blocked for DELETED.\n"
       "exception.validation.sickLeave.update.closed for other fields.",
       "Medium", "Functional",
       "", "SickLeaveServiceImpl",
       "Service-level guard: DELETED -> only comment"),
]


# ── TS-SL-Permissions ───────────────────────────────────────────
# View types, PM access, accountant access, security gaps

TS_SL_PERMISSIONS = [
    tc("TC-SL-064",
       "Employee -- view own sick leaves on /sick-leave/my",
       "Logged in as regular employee.",
       "1. Navigate to /sick-leave/my\n"
       "2. Verify table shows own sick leaves only",
       "Employee sees own sick leaves. Table populated with personal records.\n"
       "No access to other employees' records.",
       "High", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-065",
       "Employee -- create own sick leave (no employee selector)",
       "Logged in as regular employee.",
       "1. Click 'Add a sick note'\n"
       "2. Observe form fields",
       "No employee selector field -- implicitly uses own login.\n"
       "Employee can only create for themselves via UI.",
       "High", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-066",
       "Employee -- edit own OPEN sick leave",
       "Employee with OPEN sick leave.",
       "1. Edit own sick leave\n"
       "2. Change dates\n"
       "3. Save",
       "Edit succeeds. Employee can modify own OPEN sick leaves.",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-067",
       "Employee -- cannot edit PAID sick leave",
       "Employee with PAID sick leave.",
       "1. Open detail modal for PAID sick leave\n"
       "2. Check for edit button",
       "Edit button disabled/hidden for PAID.\n"
       "Only ADMIN/CHIEF_ACCOUNTANT/office accountant can edit PAID.",
       "Medium", "Negative",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-068",
       "PM -- view subordinates' sick leaves on manager page",
       "Logged in as PM with subordinates.",
       "1. Navigate to /vacation/sick-leaves-of-employees\n"
       "2. Check My department / My projects tabs",
       "PM sees sick leaves of employees in their department/projects.\n"
       "Two tab views: My department, My projects.",
       "High", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-069",
       "PM -- create sick leave for subordinate",
       "Logged in as PM.",
       "1. Click 'Add a sick note' on manager page\n"
       "2. Search for subordinate employee\n"
       "3. Fill dates, save",
       "PM can create sick leave for any searched employee.\n"
       "Employee async-search with no subordination filter.\n"
       "No file upload in manager create modal.",
       "High", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-070",
       "PM -- manager create hardcodes force=true (bypasses overlap check)",
       "Manager creates sick leave overlapping existing one for employee.",
       "1. Manager creates overlapping sick leave via UI\n"
       "2. Monitor API request (DevTools Network tab)",
       "BUG: force=true hardcoded in manager saga.\n"
       "Backend overlap check bypassed. No 409/conflict dialog shown.\n"
       "Combined with 100-record client cap = no overlap validation for managers.",
       "High", "Bug verification",
       "", "frontend-sick-leave-module",
       "Manager overlap validation completely bypassed"),

    tc("TC-SL-071",
       "BUG: No creation permission check -- any user for any employee",
       "API access as any authenticated user.",
       "1. POST /api/vacation/v1/sick-leaves with login of unrelated employee\n"
       "2. Use JWT of user who is NOT manager/TL/accountant of target employee",
       "SECURITY BUG: Sick leave created for any employee.\n"
       "No authorization check beyond AUTHENTICATED_USER.\n"
       "@PreAuthorize only checks AUTHENTICATED_USER.",
       "Critical", "Security",
       "BUG-SL-1", "SickLeaveController, SickLeaveServiceImpl",
       "Any authenticated user can create for any employee"),

    tc("TC-SL-072",
       "BUG: No owner check on delete -- any user can delete any non-PAID SL",
       "API access. Two users: A (owner) and B (unrelated).",
       "1. Create sick leave as user A\n"
       "2. DELETE /api/vacation/v1/sick-leaves/{id} as user B",
       "SECURITY BUG: Delete succeeds. No owner check.\n"
       "Any AUTHENTICATED_USER can delete any non-PAID sick leave.\n"
       "Only guard: cannot delete PAID.",
       "Critical", "Security",
       "BUG-SL-1", "SickLeaveServiceImpl",
       "Missing authorization on delete endpoint"),

    tc("TC-SL-073",
       "BUG: No PM check on delete -- PM from other project can delete",
       "PM from project X. Sick leave owned by employee in project Y.",
       "1. DELETE /api/vacation/v1/sick-leaves/{id} as unrelated PM",
       "SECURITY BUG: Delete succeeds.\n"
       "PM authorization not checked on delete path.\n"
       "Contrast with update path which does check PM access.",
       "High", "Security",
       "BUG-SL-1", "SickLeaveServiceImpl",
       "Delete path skips PM access check that update path enforces"),

    tc("TC-SL-074",
       "PM access check on update -- VacationSecurityException if not related",
       "PM who is NOT employee's manager/TL/accountant.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id} as unrelated PM",
       "HTTP 403: exception.vacation.no.permission\n"
       "VacationSecurityException thrown.\n"
       "Update path correctly checks PM relationship (unlike delete).",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       "Shared exception class with vacation module"),

    tc("TC-SL-075",
       "Accountant -- access accounting page and change status",
       "User with ROLE_ACCOUNTANT, ROLE_CHIEF_ACCOUNTANT, or ADMIN.",
       "1. Navigate to /accounting/sick-leaves\n"
       "2. Change accounting status on a row",
       "Page loads. Status dropdown operational.\n"
       "SICK_LEAVE_ACCOUNTING_VIEW permission required.\n"
       "Roles: ACCOUNTANT, DEPARTMENT_MANAGER, CHIEF_ACCOUNTANT, VIEW_ALL, ADMIN.",
       "High", "Functional",
       "", "SickLeaveController, frontend-sick-leave-module",
       ""),

    tc("TC-SL-076",
       "Accountant -- only accountant roles can change accounting fields",
       "Regular employee or PM (not accountant).",
       "1. PATCH /api/vacation/v1/sick-leaves/{id} with accountingStatus change",
       "Backend rejects: only ADMIN/CHIEF_ACCOUNTANT/office accountant\n"
       "can modify accountingStatus and accountantComment.\n"
       "Service-level check, not PreAuthorize.",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-077",
       "BUG: Route /sick-leave/my has no router-level permission check",
       "User with no SICK_LEAVE:VIEW permission.",
       "1. Navigate directly to /sick-leave/my in browser",
       "BUG: Route has TODO comment for permission check but none implemented.\n"
       "Any authenticated user can access the page.\n"
       "Backend still filters data by user context.",
       "Medium", "Bug verification",
       "BUG-SL-6", "frontend-sick-leave-module",
       "TODO in code, no guard. Backend compensates."),

    tc("TC-SL-078",
       "API token -- CRUD endpoints return 403",
       "API token with 21 standard permissions (no AUTHENTICATED_USER).",
       "1. GET /api/vacation/v1/sick-leaves/{id} with API_SECRET_TOKEN header\n"
       "2. POST /api/vacation/v1/sick-leaves\n"
       "3. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "4. DELETE /api/vacation/v1/sick-leaves/{id}",
       "All return 403 Forbidden.\n"
       "@PreAuthorize requires AUTHENTICATED_USER (JWT only).\n"
       "API tokens lack this permission. Only search/count work.",
       "High", "Security",
       "", "SickLeaveController",
       "Inconsistent with vacation module API token pattern"),

    tc("TC-SL-079",
       "API token -- stack trace leakage in 403 response",
       "API token used for file upload endpoint.",
       "1. POST /api/vacation/v1/files/upload with API_SECRET_TOKEN header\n"
       "2. Inspect error response body",
       "SECURITY: 403 Forbidden returned BUT full Java stack trace (90+ frames)\n"
       "leaked in error response body.\n"
       "Exposes internal class names, package structure, framework versions.",
       "Medium", "Security",
       "BUG (S15)", "FileController",
       "Stack trace leakage in production error responses"),

    tc("TC-SL-080",
       "Department Manager -- My department tab access",
       "Logged in as department manager.",
       "1. Navigate to /vacation/sick-leaves-of-employees\n"
       "2. Check My department tab",
       "DM sees sick leaves for all employees in their department.\n"
       "State + Status filters available.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-081",
       "Manager view -- My department default + My projects tab",
       "Logged in as PM/DM with subordinates.",
       "1. Navigate to /vacation/sick-leaves-of-employees\n"
       "2. Observe default tab (My department)\n"
       "3. Switch to My projects tab",
       "Default: My department tab (redirect to /my-department).\n"
       "My projects: shows sick leaves of employees on PM's projects.\n"
       "Pagination ~20/page.",
       "High", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-082",
       "Manager view -- detail modal from action icon",
       "Manager view with sick leave record.",
       "1. Click detail action icon on row\n"
       "2. Observe modal content",
       "Detail modal shows: Employee, Accountant, State, Status, Period,\n"
       "Calendar days, Number, Notify also.\n"
       "Read-only for manager (no edit from modal).",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-083",
       "Manager create -- no file upload capability",
       "Manager create modal open.",
       "1. Observe modal fields",
       "No file upload area in manager create modal.\n"
       "Only: Employee search, Start date, End date, Number.\n"
       "File upload is employee-only capability.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       "Capability gap vs employee view"),
]


# ── TS-SL-Validation ────────────────────────────────────────────
# Date order, crossing, force flag, number, files, form validation

TS_SL_VALIDATION = [
    tc("TC-SL-084",
       "Start date required -- empty field validation (Yup)",
       "Create modal open.",
       "1. Leave Start date empty\n"
       "2. Fill End date\n"
       "3. Try to save",
       "Validation error: Start date is required.\n"
       "Save blocked by Yup schema (create mode).\n"
       "Backend: @NotNull on startDate.",
       "High", "Negative",
       "", "frontend-sick-leave-module, SickLeaveCreateRequestDTO",
       ""),

    tc("TC-SL-085",
       "End date required -- empty field validation (Yup)",
       "Create modal open.",
       "1. Fill Start date\n"
       "2. Leave End date empty\n"
       "3. Try to save",
       "Validation error: End date is required.\n"
       "Save blocked by Yup schema.\n"
       "Backend: @NotNull on endDate.",
       "High", "Negative",
       "", "frontend-sick-leave-module, SickLeaveCreateRequestDTO",
       ""),

    tc("TC-SL-086",
       "Start date > end date -- backend error code",
       "Bypass frontend or use API directly.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate: '2026-03-20', endDate: '2026-03-15', force: false}",
       "HTTP 400: validation.sickLeave.dates.order\n"
       "SickLeaveCreateValidator checks startDate <= endDate.\n"
       "Same-day allowed (start = end).",
       "High", "Negative",
       "", "SickLeaveCreateValidator",
       "Frontend auto-corrects (end < start -> start = end) so rarely hits backend"),

    tc("TC-SL-087",
       "Frontend auto-adjustment: end < start -> start = end",
       "Create modal with Start date already set.",
       "1. Select End date earlier than Start date\n"
       "2. Observe Start date field",
       "Start date auto-adjusts to match End date.\n"
       "No validation error shown -- UI auto-corrects.\n"
       "Calendar days = 1 after adjustment.",
       "High", "Functional",
       "", "frontend-sick-leave-module",
       "Confirmed behavior: prevents date order error at UI level"),

    tc("TC-SL-088",
       "Start date auto-fills end date on first selection",
       "Create modal open, no dates selected.",
       "1. Select Start date = 2026-03-16\n"
       "2. Check End date field",
       "End date auto-fills with same value (2026-03-16).\n"
       "Calendar days = 1.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       "Convenience auto-fill"),

    tc("TC-SL-089",
       "Calendar days live recalculation on date change",
       "Create modal with dates set.",
       "1. Set Start=2026-03-01, End=2026-03-10 (10 days)\n"
       "2. Change End to 2026-03-15\n"
       "3. Observe Calendar days",
       "Calendar days updates live: 10 -> 15.\n"
       "Read-only field, auto-calculated as endDate - startDate + 1.",
       "Medium", "Functional",
       "", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-090",
       "Number field -- max 40 characters (@Size(max=40))",
       "Create/edit modal.",
       "1. Enter 41-character string in Number field\n"
       "2. Save via API: PATCH with number='A' * 41",
       "HTTP 400 validation error: number exceeds max length 40.\n"
       "Backend: @Size(max=40) on SickLeaveCreateRequestDTO.number.\n"
       "Frontend may truncate or show client-side error.",
       "Medium", "Boundary",
       "", "SickLeaveCreateRequestDTO",
       "Gap: frontend validates max 40 but backend @Size(max=40) exists"),

    tc("TC-SL-091",
       "Number field -- exactly 40 characters (boundary)",
       "API test.",
       "1. PATCH with number = 'A' * 40",
       "Request succeeds. Number stored as exactly 40 characters.\n"
       "Boundary: at maximum allowed length.",
       "Low", "Boundary",
       "", "SickLeaveCreateRequestDTO",
       ""),

    tc("TC-SL-092",
       "Number required on close -- not on create (Yup mode switch)",
       "Create modal and Close dialog.",
       "1. Create sick leave WITHOUT number -> observe field is optional (no asterisk)\n"
       "2. Open close dialog for same sick leave -> observe field is required (asterisk)",
       "Create: number optional. Close: number required (asterisk).\n"
       "Yup switches validation mode based on isCloseMode prop.\n"
       "Backend: exception.validation.sickLeave.number.empty on close without number.",
       "High", "Functional",
       "", "frontend-sick-leave-module, SickLeaveServiceImpl",
       "Mode-dependent validation"),

    tc("TC-SL-093",
       "Number whitespace trimming",
       "Edit modal with Number field.",
       "1. PATCH with number = '  BL-123  ' (leading/trailing spaces)\n"
       "2. GET and verify stored value",
       "Number stored as 'BL-123' (trimmed).\n"
       "Backend trims whitespace.",
       "Low", "Functional",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-094",
       "Overlap detection -- only active sick leaves checked",
       "1 OPEN + 1 DELETED sick leave covering same dates.",
       "1. Create new sick leave overlapping both\n"
       "2. Observe overlap check result",
       "Overlap check only considers active sick leaves (OPEN, CLOSED).\n"
       "DELETED and REJECTED excluded from overlap detection.",
       "Medium", "Functional",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-095",
       "BUG: Manager overlap bypass -- client-side 100-record cap + force=true",
       "Manager creating sick leave for employee with many existing records.",
       "1. Manager creates sick leave (overlap exists beyond first 100 records)\n"
       "2. Monitor API request: force=true hardcoded",
       "BUG: Client-side overlap pre-fetches max 100 records.\n"
       "If overlap with record #101+ it is missed.\n"
       "force=true hardcoded bypasses backend check too.\n"
       "Result: no overlap validation for manager-created sick leaves.",
       "High", "Bug verification",
       "", "frontend-sick-leave-module",
       "Combined bugs: 100-record cap + force=true"),

    tc("TC-SL-096",
       "Vacation crossing -- force=false triggers 409, force=true creates with event",
       "Employee with active vacation overlapping target dates.",
       "1. POST with force=false -> expect 409: exception.sick.leave.crossing.vacation\n"
       "2. Resend with force=true -> expect 200",
       "force=false: HTTP 409 SickLeaveCrossingVacationException.\n"
       "force=true: Created + VacationOverlap event published.\n"
       "NOTIFY_EMPLOYEE_SICKLEAVE_OVERLAPS_VACATION sent.",
       "High", "Functional",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-097",
       "BUG: Vacation overlap dialog re-triggers on every save",
       "Sick leave overlapping vacation. Overlap dialog already dismissed.",
       "1. Create sick leave overlapping vacation -> dismiss overlap dialog\n"
       "2. Edit same sick leave (no date change)\n"
       "3. Save",
       "BUG: Overlap dialog re-triggers on every save (create AND edit).\n"
       "Not just when dates actually change/overlap.\n"
       "Nuisance dialog on every edit.",
       "Low", "Bug verification",
       "BUG (S31)", "frontend-sick-leave-module",
       ""),

    tc("TC-SL-098",
       "Date picker -- readonly inputs, calendar widget only",
       "Create modal date pickers.",
       "1. Try to type in date input field directly\n"
       "2. Click date picker calendar instead",
       "Input fields are readonly -- must use calendar widget.\n"
       "No keyboard date entry possible.\n"
       "<input readonly> attribute confirmed.",
       "Low", "Functional",
       "", "frontend-sick-leave-module",
       "Verified via Playwright: <input readonly>"),

    tc("TC-SL-099",
       "force flag @NotNull on create -- must be explicitly set",
       "API test omitting force field.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate, endDate} -- omit force field",
       "HTTP 400: @NotNull validation error on force field.\n"
       "force is required Boolean, not optional.\n"
       "Frontend always sends force=false initially.",
       "Medium", "Negative",
       "", "SickLeaveCreateRequestDTO",
       "Risk: NPE if @NotNull somehow bypassed at deserialization"),
]


# ── TS-SL-APIErrors ─────────────────────────────────────────────
# Error codes, edge cases, boundary values, notification bugs

TS_SL_APIERRORS = [
    tc("TC-SL-100",
       "Error: validation.sickLeave.dates.order (startDate > endDate)",
       "API direct call.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate: '2026-03-20', endDate: '2026-03-10', force: false}",
       "HTTP 400\n"
       "errorCode: validation.sickLeave.dates.order\n"
       "SickLeaveCreateValidator rejects.",
       "High", "Negative",
       "", "SickLeaveCreateValidator",
       "Only validation: startDate <= endDate. No range limits."),

    tc("TC-SL-101",
       "Error: exception.validation.sickLeave.dates.crossing (overlap)",
       "Existing OPEN sick leave: 2026-03-10 to 2026-03-15.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate: '2026-03-12', endDate: '2026-03-18', force: false}",
       "HTTP 400\n"
       "errorCode: exception.validation.sickLeave.dates.crossing\n"
       "Overlapping active sick leaves detected.",
       "High", "Negative",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-102",
       "Error: exception.sick.leave.crossing.vacation (force=false)",
       "Active vacation overlapping target dates.",
       "1. POST /api/vacation/v1/sick-leaves\n"
       "2. Body: {login, startDate overlapping vacation, force: false}",
       "HTTP 409\n"
       "errorCode: exception.sick.leave.crossing.vacation\n"
       "SickLeaveCrossingVacationException.",
       "High", "Negative",
       "", "SickLeaveServiceImpl",
       "Unique HTTP 409 (not 400)"),

    tc("TC-SL-103",
       "Error: exception.validation.sickLeave.number.empty (close without number)",
       "OPEN sick leave.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, startDate, endDate, force: false, status: 'CLOSED'}\n"
       "3. Omit number field",
       "HTTP 400\n"
       "errorCode: exception.validation.sickLeave.number.empty\n"
       "Close validation requires non-empty number.",
       "High", "Negative",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-104",
       "Error: exception.validation.sickLeave.update.closed (update DELETED)",
       "Sick leave with status=DELETED.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, new startDate, endDate, force: false}",
       "HTTP 400\n"
       "errorCode: exception.validation.sickLeave.update.closed\n"
       "Only accountantComment modifiable on DELETED.",
       "Medium", "Negative",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-105",
       "Error: exception.validation.sickLeave.update.closed (update PAID by non-admin)",
       "PAID sick leave. User is regular accountant (not admin/chief).",
       "1. PATCH /api/vacation/v1/sick-leaves/{id} as regular accountant",
       "HTTP 400\n"
       "errorCode: exception.validation.sickLeave.update.closed\n"
       "Only ADMIN/CHIEF_ACCOUNTANT/office accountant can edit PAID.",
       "High", "Negative",
       "", "SickLeaveServiceImpl",
       ""),

    tc("TC-SL-106",
       "Error: exception.validation.sickLeave.delete.closed (delete PAID)",
       "Sick leave with accounting_status=PAID.",
       "1. DELETE /api/vacation/v1/sick-leaves/{id}",
       "HTTP 400\n"
       "errorCode: exception.validation.sickLeave.delete.closed\n"
       "Cannot delete PAID sick leave.",
       "High", "Negative",
       "", "SickLeaveServiceImpl",
       "Only guard on delete path"),

    tc("TC-SL-107",
       "Error: exception.vacation.no.permission (shared with vacation module)",
       "PM from unrelated project attempts update.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id} as unrelated PM",
       "HTTP 403\n"
       "errorCode: exception.vacation.no.permission\n"
       "VacationSecurityException -- shared class with vacation module.\n"
       "Same error code for both vacation and sick leave operations.",
       "High", "Negative",
       "", "SickLeaveServiceImpl, VacationSecurityException",
       "Shared exception class is a design issue"),

    tc("TC-SL-108",
       "BUG: getEditorType() == identity comparison always false",
       "Create sick leave as employee. Check notification dispatch.",
       "1. Create sick leave as employee\n"
       "2. Inspect notification template via email API or logs\n"
       "3. Check if OPEN or OPEN_BY_SUPERVISOR template used",
       "BUG: getEditorType() uses == (reference equality) on BO instances.\n"
       "`employee == currentEmployee` always false for separately loaded objects.\n"
       "Self-edits classified as ACCOUNTANT/SUPERVISOR instead of EMPLOYEE.\n"
       "Wrong notification template variant selected.",
       "Medium", "Bug verification",
       "BUG-SL-2", "SickLeaveNotificationService",
       "Should use .equals() instead of =="),

    tc("TC-SL-109",
       "BUG: PatchDTO extends CreateDTO -- all create validations re-run on patch",
       "Existing sick leave. PATCH with minimal change.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body must include ALL create fields (login, startDate, endDate, force)\n"
       "3. Omit force -> @NotNull error",
       "Design issue: PatchDTO extends CreateDTO.\n"
       "All create-time validations (@NotNull login, @NotNull force, etc.)\n"
       "re-run on every patch. Must send full create payload even for minor edits.\n"
       "force @NotNull on patch is particularly awkward.",
       "Medium", "Bug verification",
       "", "SickLeavePatchRequestDTO extends SickLeaveCreateRequestDTO",
       "Inheritance forces full payload on every patch"),

    tc("TC-SL-110",
       "BUG: Accounting status can reverse lifecycle (NEW after PAID -> OPEN)",
       "Sick leave: accounting_status=PAID, status=CLOSED.",
       "1. Change accounting_status from PAID to NEW via accountant dropdown\n"
       "2. Observe main status",
       "BUG: accounting_status reverts to NEW.\n"
       "Coupling rule: NEW/PROCESSING -> main status forced to OPEN.\n"
       "Result: was PAID/CLOSED, now NEW/OPEN -- fully reversed lifecycle.\n"
       "No state machine prevents this backward transition.",
       "High", "Bug verification",
       "BUG-SL-3", "SickLeaveServiceImpl",
       "Critical: lifecycle can be fully reversed"),

    tc("TC-SL-111",
       "GET /v1/sick-leaves -- search with pagination and filters",
       "Authenticated user.",
       "1. GET /api/vacation/v1/sick-leaves?page=0&size=20&statuses=OPEN&sort=-startDate\n"
       "2. Verify response pagination structure",
       "Paginated response with content[], totalElements, totalPages.\n"
       "Filters: statuses (multi), startDate, endDate, employeeLogin.\n"
       "Sort: +/- prefix for asc/desc.",
       "Medium", "Functional",
       "", "SickLeaveController",
       ""),

    tc("TC-SL-112",
       "GET /v1/sick-leaves/count -- open and overdue count",
       "Authenticated user.",
       "1. GET /api/vacation/v1/sick-leaves/count",
       "Returns count of open and overdue sick leaves.\n"
       "Used by dashboard/sidebar badge counters.",
       "Medium", "Functional",
       "", "SickLeaveController",
       ""),

    tc("TC-SL-113",
       "GET /v1/sick-leaves/{id} -- non-existent ID returns 404",
       "Authenticated user.",
       "1. GET /api/vacation/v1/sick-leaves/999999999",
       "HTTP 404 or appropriate not-found error.\n"
       "EntityNotFoundException from repository.",
       "Medium", "Negative",
       "", "SickLeaveController",
       ""),

    tc("TC-SL-114",
       "PATCH with invalid employee login -- @EmployeeLoginExists",
       "API direct call.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login: 'nonexistent_user_xyz', startDate, endDate, force: false}",
       "HTTP 400 validation error.\n"
       "@EmployeeLoginExists custom validator rejects invalid login.",
       "Medium", "Negative",
       "", "SickLeaveCreateRequestDTO",
       ""),

    tc("TC-SL-115",
       "PATCH with invalid notifyAlso login -- @EmployeeLoginCollectionExists",
       "API direct call.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, startDate, endDate, force: false, "
       "notifyAlso: ['valid_login', 'nonexistent_xyz']}",
       "HTTP 400 validation error.\n"
       "@EmployeeLoginCollectionExists validates each login in collection.",
       "Medium", "Negative",
       "", "SickLeaveCreateRequestDTO",
       ""),

    tc("TC-SL-116",
       "PATCH with invalid file UUID -- @FileUuidExists",
       "API direct call with non-existent UUID.",
       "1. PATCH /api/vacation/v1/sick-leaves/{id}\n"
       "2. Body: {login, startDate, endDate, force: false, "
       "filesIds: ['00000000-0000-0000-0000-000000000000']}",
       "HTTP 400 validation error.\n"
       "@FileUuidExists custom validator rejects non-existent UUID.",
       "Medium", "Negative",
       "", "SickLeaveCreateRequestDTO",
       ""),

    tc("TC-SL-117",
       "Notification: REJECTED -- NOTIFY_SICKLEAVE_REJECTED on accounting reject",
       "Accountant rejects sick leave.",
       "1. Change accounting_status to REJECTED\n"
       "2. Check email via GET /api/email/v1/emails",
       "NOTIFY_SICKLEAVE_REJECTED template sent.\n"
       "Main status also changes to REJECTED.\n"
       "Dual status coupling in action.",
       "High", "Functional",
       "", "SickLeaveNotificationService",
       ""),

    tc("TC-SL-118",
       "Chain-of-responsibility notification -- multi-field edit",
       "Edit sick leave changing both dates AND number.",
       "1. PATCH with changed endDate + changed number\n"
       "2. Check emails sent",
       "Chain dispatches both DATES_CHANGED and NUMBER_CHANGED notifications.\n"
       "Two separate emails (not combined).\n"
       "Handler chain pattern in notification service.",
       "Low", "Functional",
       "", "SickLeaveNotificationService",
       ""),

    tc("TC-SL-119",
       "Concurrent update -- race condition on accounting status change",
       "Two accountants viewing same sick leave.",
       "1. Accountant A changes status to PROCESSING\n"
       "2. Accountant B simultaneously changes status to PROCESSING\n"
       "3. Check final state and accountant FK",
       "Last-write-wins. No optimistic locking.\n"
       "accountant FK points to whichever write completed last.\n"
       "No write lock acquired for sick leave updates (unlike vacation).",
       "Medium", "Functional",
       "", "SickLeaveServiceImpl",
       "No findByIdAndAcquireWriteLock pattern on sick leave"),

    tc("TC-SL-120",
       "Open/overdue count endpoint -- used for sidebar badge",
       "Timemachine environment with known data.",
       "1. GET /api/vacation/v1/sick-leaves/count\n"
       "2. Cross-reference with DB: SELECT COUNT(*) FROM ttt_vacation.sick_leave "
       "WHERE status='OPEN' AND accounting_status NOT IN ('PAID','REJECTED')",
       "Count matches DB query for active, unprocessed sick leaves.\n"
       "Badge shows on sidebar for accountant/manager views.",
       "Low", "Functional",
       "", "SickLeaveController, SickLeaveServiceImpl",
       ""),
]


# =====================================================================
# SUITE REGISTRY
# =====================================================================

ALL_SUITES = [
    ("TS-SL-Lifecycle", "Sick Leave Lifecycle (Create/Edit/Close/Delete)", TS_SL_LIFECYCLE),
    ("TS-SL-DualStatus", "Dual Status Model & Status Coupling", TS_SL_DUALSTATUS),
    ("TS-SL-Accounting", "Accounting Workflow & Page Features", TS_SL_ACCOUNTING),
    ("TS-SL-Permissions", "Permissions, Security & Manager View", TS_SL_PERMISSIONS),
    ("TS-SL-Validation", "Validation Rules & Form Behavior", TS_SL_VALIDATION),
    ("TS-SL-APIErrors", "API Error Codes, Edge Cases & Notifications", TS_SL_APIERRORS),
]


# =====================================================================
# FEATURE MATRIX DATA
# =====================================================================

FEATURES = [
    # (feature, functional, negative, boundary, security, bug_verif, integration, total, suite_ref)
    ("Lifecycle (CRUD/Files/Notify)", 20, 4, 3, 1, 2, 1, 31, "TS-SL-Lifecycle"),
    ("Dual Status Model", 10, 1, 0, 0, 3, 0, 16, "TS-SL-DualStatus"),   # 14 func variant counts adjusted
    ("Accounting Workflow", 13, 0, 0, 0, 2, 0, 16, "TS-SL-Accounting"),  # 1 bug verif variant
    ("Permissions & Security", 10, 1, 0, 4, 3, 0, 20, "TS-SL-Permissions"),  # manager view included
    ("Validation & Form Rules", 7, 3, 3, 0, 3, 0, 16, "TS-SL-Validation"),
    ("API Errors & Edge Cases", 4, 9, 0, 0, 3, 0, 21, "TS-SL-APIErrors"),   # notification bugs counted
]


# =====================================================================
# RISK ASSESSMENT DATA
# =====================================================================

RISKS = [
    ("Dual status model complexity",
     "Accounting status drives main lifecycle status via coupling rules. "
     "PAID->CLOSED, REJECTED->REJECTED, NEW/PROCESSING->OPEN. "
     "Complexity leads to unexpected state combinations.",
     "High", "High", "Critical",
     "Test all 16 accounting->main status transitions. "
     "Verify coupling consistency. Test backward transitions."),

    ("Missing delete authorization",
     "No owner check and no PM check on delete endpoint. "
     "Any AUTHENTICATED_USER can delete any non-PAID sick leave. "
     "Contrast: update path correctly checks PM relationship.",
     "High", "Critical", "Critical",
     "Test delete as unrelated user, unrelated PM. "
     "Verify only PAID guard exists."),

    ("Status reversal (NEW after PAID reverts to OPEN)",
     "Accounting status can be changed from PAID back to NEW. "
     "Coupling rule forces main status from CLOSED back to OPEN. "
     "Entire lifecycle reversed with no guardrails.",
     "Medium", "Critical", "Critical",
     "Change PAID->NEW, verify main CLOSED->OPEN. "
     "Document full reversal path."),

    ("No backend MIME validation on file upload",
     "Only frontend checks file types (PDF, PNG, JPEG). "
     "Backend accepts any file via direct API call. "
     "Potential vector for malicious file upload.",
     "Medium", "Critical", "High",
     "Upload .exe, .html, .js files via curl. "
     "Verify no server-side MIME check."),

    ("Notification bug (identity comparison)",
     "getEditorType() uses == (reference equality) instead of .equals() "
     "on JPA entities. Self-edits always classified as ACCOUNTANT/SUPERVISOR. "
     "Wrong notification template variant sent.",
     "High", "Low", "Medium",
     "Create as employee, check if OPEN or OPEN_BY_SUPERVISOR template used."),

    ("Orphaned records on soft-delete",
     "Soft delete sets status=DELETED but does NOT clean up "
     "sick_leave_file and sick_leave_notify_also junction records. "
     "DB accumulates orphaned references.",
     "Medium", "Low", "Medium",
     "Delete sick leave with files. Query DB for remaining junction records."),

    ("SCHEDULED/OVERDUE asymmetry (read-only computed statuses)",
     "SCHEDULED and OVERDUE returned in GET responses but not accepted "
     "in PATCH requests. SickLeavePatchRequestStatusTypeDTO only has OPEN/CLOSED. "
     "Confusing API contract.",
     "Low", "Medium", "Medium",
     "PATCH with status=SCHEDULED, verify rejection. Document asymmetry."),

    ("Shared VacationSecurityException for sick leave",
     "Sick leave operations throw exception.vacation.no.permission "
     "(VacationSecurityException). Same error code used for both modules. "
     "Confusing error attribution in logs and responses.",
     "Low", "Medium", "Low",
     "Trigger VacationSecurityException via sick leave update. "
     "Verify error code says 'vacation'."),

    ("Force flag NPE risk on patch",
     "force is @NotNull Boolean on CreateDTO. PatchDTO inherits it. "
     "If force=null somehow reaches service layer, NPE on unboxing. "
     "Currently guarded by bean validation but inheritance is fragile.",
     "Low", "Medium", "Low",
     "PATCH without force field. Verify @NotNull catches it."),

    ("Frontend-only number length limit",
     "Frontend Yup validates number max 40 chars. "
     "Backend has @Size(max=40) on DTO. "
     "But if bypassed at DTO level, no DB column length constraint check.",
     "Low", "Low", "Low",
     "Send 41-char number via API. Verify @Size rejects. "
     "Send 40-char to confirm boundary."),

    ("Manager force=true bypass eliminates overlap validation",
     "Manager create hardcodes force=true in frontend saga. "
     "Client-side overlap check capped at 100 records. "
     "Combined: managers have zero overlap validation.",
     "Medium", "High", "High",
     "Manager creates overlapping sick leave. Verify no conflict shown. "
     "Monitor API request for force=true."),

    ("API token exclusion from CRUD endpoints",
     "Sick leave CRUD requires AUTHENTICATED_USER (JWT only). "
     "API tokens with 21 permissions get 403. "
     "Only search and count endpoints work with tokens.",
     "High", "Medium", "Medium",
     "Test all CRUD endpoints with API_SECRET_TOKEN header. "
     "Verify all return 403."),
]


# =====================================================================
# BUILD WORKBOOK
# =====================================================================

OUTPUT = "/home/v/Dev/ttt-expert-v1/expert-system/output/sick-leave/sick-leave.xlsx"

wb = openpyxl.Workbook()

# ═══════════════════════════════════════════════════════════════════
# TAB 1: Plan Overview
# ═══════════════════════════════════════════════════════════════════

ws = wb.active
ws.title = "Plan Overview"
ws.sheet_properties.tabColor = TAB_COLOR_PLAN

plan_rows = [
    ("Sick Leave Module -- Test Plan", FONT_TITLE),
    (f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", FONT_SMALL),
    ("", None),
    ("Scope", FONT_SUBTITLE),
    ("Comprehensive testing of the Sick Leave module covering the complete employee", FONT_BODY),
    ("CRUD lifecycle (create, edit, close, reopen, delete), dual status model", FONT_BODY),
    ("(main status + accounting status with coupling rules), accounting workflow,", FONT_BODY),
    ("file handling, email notifications, form validation, role-based permissions,", FONT_BODY),
    ("manager view features, and known security gaps.", FONT_BODY),
    ("", None),
    ("Objectives", FONT_SUBTITLE),
    ("1. Validate complete sick leave lifecycle: create, edit, close, reopen, delete", FONT_BODY),
    ("2. Verify dual status system coupling (accounting status drives main status)", FONT_BODY),
    ("3. Test accounting workflow: inline dropdown status changes, comments, filters", FONT_BODY),
    ("4. Verify file upload/download with security validation (no backend MIME check)", FONT_BODY),
    ("5. Validate 5 notification event types with correct templates and recipients", FONT_BODY),
    ("6. Test form validation rules (Yup frontend + bean validation backend)", FONT_BODY),
    ("7. Verify role-based access control and document all known security gaps", FONT_BODY),
    ("8. Test manager-specific creation flow and view functionality", FONT_BODY),
    ("9. Verify all 7 error codes and edge case behaviors", FONT_BODY),
    ("", None),
    ("Approach", FONT_SUBTITLE),
    ("Testing combines UI (Playwright), API (curl/Swagger), and DB (PostgreSQL) verification.", FONT_BODY),
    ("UI testing on timemachine environment with multiple user roles:", FONT_BODY),
    ("employee, project manager, department manager, accountant, chief accountant, admin.", FONT_BODY),
    ("API testing via JWT session auth (API tokens rejected for CRUD endpoints).", FONT_BODY),
    ("Known bugs verified inline: 1 Critical, 3 High, 4 Medium, 4 Low severity.", FONT_BODY),
    ("", None),
    ("Test Data Strategy", FONT_SUBTITLE),
    ("- Timemachine env: 348 existing sick leaves, ~104-114/year, max duration 140-141 days", FONT_BODY),
    ("- Status distribution: CLOSED/NEW 62%, CLOSED/PAID 28%, DELETED/NEW 5%", FONT_BODY),
    ("- 55% have file attachments, 30% have notifyAlso recipients", FONT_BODY),
    ("- Use test logins: perekrest (accountant), dergachev (manager), various employees", FONT_BODY),
    ("- Create/delete within session to maintain environment cleanliness", FONT_BODY),
    ("- DB mining: SELECT from ttt_vacation.sick_leave for specific status combinations", FONT_BODY),
    ("", None),
    ("Environment Requirements", FONT_SUBTITLE),
    ("- Primary: timemachine (ttt-timemachine.noveogroup.com)", FONT_BODY),
    ("- Secondary: qa-1 (ttt-qa-1.noveogroup.com)", FONT_BODY),
    ("- Cross-env: stage (ttt-stage.noveogroup.com) for comparison", FONT_BODY),
    ("- Browser: Chrome via Playwright (VPN required)", FONT_BODY),
    ("- Database: PostgreSQL on port 5433, schema ttt_vacation", FONT_BODY),
    ("- API: JWT auth required for CRUD; API tokens for search/count only", FONT_BODY),
    ("", None),
    ("Qase Existing Coverage", FONT_SUBTITLE),
    ("57 existing cases in Qase cover display/notification only (0 lifecycle CRUD cases):", FONT_BODY),
    ("- Color indication in My Tasks / Employee Tasks (6 cases)", FONT_BODY),
    ("- Confirmation table display (6 cases)", FONT_BODY),
    ("- Planner display (6 cases)", FONT_BODY),
    ("- Email notifications (14 cases)", FONT_BODY),
    ("- Accounting sort/filter/table/actions (25 cases)", FONT_BODY),
    ("- My Sick Leaves / Employee Sick Leaves: empty placeholder suites (0 cases)", FONT_BODY),
    ("THIS TEST PLAN fills the lifecycle CRUD gap with 120 new test cases.", FONT_BODY),
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
    # Hyperlink on test suite column
    link_cell = ws_fm.cell(row=r, column=9)
    link_cell.font = FONT_LINK
    link_cell.hyperlink = f"#'{ref}'!A1"

# Totals row
total_r = len(FEATURES) + 2
ws_fm.cell(row=total_r, column=1, value="TOTAL").font = FONT_SECTION
for c in range(2, 9):
    # Sum columns 2-8 (indices 1-7 in FEATURES tuples)
    val = sum(f[c - 1] for f in FEATURES)
    ws_fm.cell(row=total_r, column=c, value=val).font = FONT_SECTION
for c in range(1, len(fm_headers) + 1):
    cell = ws_fm.cell(row=total_r, column=c)
    cell.border = THIN_BORDER
    cell.fill = FILL_SECTION

fm_widths = [30, 12, 10, 10, 10, 16, 12, 8, 20]
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
    # Color severity cell
    sev_cell = ws_risk.cell(row=r, column=5)
    if sev == "Critical":
        sev_cell.fill = FILL_RISK_HIGH  # Red-ish for critical
    elif sev == "High":
        sev_cell.fill = FILL_RISK_HIGH
    elif sev == "Medium":
        sev_cell.fill = FILL_RISK_MED
    elif sev == "Low":
        sev_cell.fill = FILL_RISK_LOW

risk_widths = [35, 60, 12, 12, 12, 55]
for i, w in enumerate(risk_widths, 1):
    ws_risk.column_dimensions[get_column_letter(i)].width = w
add_autofilter(ws_risk, 1, len(risk_headers))


# ═══════════════════════════════════════════════════════════════════
# TABs 4-9: Test Suite sheets (TS-*)
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

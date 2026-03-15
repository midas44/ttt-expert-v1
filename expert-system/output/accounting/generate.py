#!/usr/bin/env python3
"""Generate accounting.xlsx — unified test workbook for Accounting module.

Phase B output for the TTT Expert System (Session 61 — regenerated with enriched knowledge).
Covers: Period management, vacation payment, day correction, accounting views/notifications,
        sick leave accounting, API errors & security.

Knowledge sources:
  - modules/accounting-service-deep-dive.md (13 design issues, full code analysis)
  - analysis/accounting-form-validation-rules.md (field-level validation)
  - exploration/api-findings/payment-flow-live-testing.md (6 bugs)
  - exploration/api-findings/vacation-day-correction-live-testing.md (drift bug)
  - exploration/ui-flows/accounting-pages.md (5 sub-pages)
  - exploration/api-findings/cron-job-live-verification.md (ShedLock verification)
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

# ── TS-ACC-Periods (Report & Approve Period Management) ──────

TS_ACC_PERIODS = [
    tc("TC-ACC-001",
       "Report period: advance one month forward",
       "Logged in as accountant with OFFICES_EDIT on target salary office.\n"
       "Current report period = March 2026.",
       "1. GET /api/ttt/v1/offices/{officeId}/periods/report — note current start\n"
       "2. PATCH /api/ttt/v1/offices/{officeId}/periods/report\n"
       "   Body: {\"start\": \"2026-04-01\"}\n"
       "3. GET period again to verify",
       "HTTP 200. Report period updated to 2026-04-01.\n"
       "OfficePeriodChangedApplicationEvent published.\n"
       "Period cache evicted (CACHE_OFFICE_PERIOD).\n"
       "Employees can no longer submit reports for March.",
       "Critical", "Functional",
       "REQ-period-management", "OfficePeriodController, OfficePeriodServiceImpl"),

    tc("TC-ACC-002",
       "Report period: non-first-day-of-month rejected",
       "Accountant with OFFICES_EDIT.",
       "1. PATCH /api/ttt/v1/offices/{officeId}/periods/report\n"
       "   Body: {\"start\": \"2026-04-15\"}\n"
       "2. Verify error response",
       "HTTP 400. Error code: exception.validation.period.not.first.day.of.month.\n"
       "Period unchanged.",
       "High", "Validation",
       "REQ-period-management", "OfficePeriodServiceImpl.patchReportPeriod",
       "Validation enforced at service level, not DTO — mid-month date passes DTO parsing"),

    tc("TC-ACC-003",
       "Report period: set before approve period rejected",
       "Report period = April 2026, Approve period = February 2026.",
       "1. PATCH /api/ttt/v1/offices/{officeId}/periods/report\n"
       "   Body: {\"start\": \"2026-01-01\"}\n"
       "2. Verify error",
       "HTTP 400. Error: exception.validation.period.report.before.approve.\n"
       "Invariant: APPROVE_PERIOD_START <= REPORT_PERIOD_START enforced.",
       "Critical", "Negative",
       "REQ-period-management", "OfficePeriodServiceImpl",
       "Key invariant — ensures approve period cannot exceed report period"),

    tc("TC-ACC-004",
       "Approve period: advance one month forward",
       "Accountant with OFFICES_EDIT. Current approve = Feb 2026.\n"
       "No employees have extended periods in this office.",
       "1. GET /api/ttt/v1/offices/{officeId}/periods/approve\n"
       "2. PATCH /api/ttt/v1/offices/{officeId}/periods/approve\n"
       "   Body: {\"start\": \"2026-03-01\"}\n"
       "3. GET period again",
       "HTTP 200. Approve period updated to 2026-03-01.\n"
       "OfficePeriodChangedApplicationEvent published.\n"
       "If TTT_VACATION_ASYNC enabled: RabbitMQ message to TTT_BACKEND_OFFICE_PERIOD_TOPIC.\n"
       "If disabled: synchronous vacationClient.recalculateAvailableDays() called.",
       "Critical", "Functional",
       "REQ-period-management", "OfficePeriodServiceImpl, InternalOfficePeriodService"),

    tc("TC-ACC-005",
       "Approve period: revert (move backward) triggers reopen event",
       "Approve period = March 2026.",
       "1. PATCH /api/ttt/v1/offices/{officeId}/periods/approve\n"
       "   Body: {\"start\": \"2026-02-01\"}\n"
       "2. Verify period changed\n"
       "3. Check RabbitMQ events (or vacation days recalculation reverse)",
       "HTTP 200. Approve period moved back to 2026-02-01.\n"
       "OfficePeriodReopenedApplicationEvent published.\n"
       "RabbitMQ: TTT_BACKEND_OFFICE_PERIOD_REOPENED_TOPIC.\n"
       "Vacation days recalculation reverse triggered (restores ConfirmationPeriodDays).",
       "Critical", "Functional",
       "REQ-period-management", "InternalOfficePeriodService.setPeriodStart",
       "Reopen vs change distinction: backward = reopen, forward = change"),

    tc("TC-ACC-006",
       "Approve period: 2-month backward limit enforced",
       "Today = March 2026. Approve period = March 2026.",
       "1. PATCH approve period to {\"start\": \"2025-12-01\"}\n"
       "   (3 months back — exceeds 2-month min)\n"
       "2. PATCH approve period to {\"start\": \"2026-01-01\"}\n"
       "   (2 months back — at limit)",
       "Step 1: HTTP 400. Error: exception.validation.period.approve.start.min.\n"
       "Min = today.minusMonths(2).withDayOfMonth(1) = 2026-01-01.\n"
       "Step 2: HTTP 200. At boundary — accepted.",
       "High", "Boundary",
       "REQ-period-management", "OfficePeriodServiceImpl.patchApprovePeriod"),

    tc("TC-ACC-007",
       "Approve period: max 1-month jump enforced",
       "Current approve = Feb 2026.",
       "1. PATCH approve to {\"start\": \"2026-04-01\"}\n"
       "   (2 months forward from current — exceeds 1-month limit)\n"
       "2. PATCH approve to {\"start\": \"2026-03-01\"}\n"
       "   (1 month forward — at limit)",
       "Step 1: HTTP 400. Error: exception.validation.period.approve.change.more.than.one.month.\n"
       "Step 2: HTTP 200. Within 1-month forward/backward change limit.",
       "High", "Boundary",
       "REQ-period-management", "OfficePeriodServiceImpl.patchApprovePeriod"),

    tc("TC-ACC-008",
       "Approve period: cannot exceed report period",
       "Report period = March 2026. Approve period = February 2026.",
       "1. PATCH approve to {\"start\": \"2026-04-01\"}\n"
       "   (exceeds report period)",
       "HTTP 400. Error: exception.validation.period.approve.start.max.\n"
       "Approve period cannot be after report period start.",
       "High", "Negative",
       "REQ-period-management", "OfficePeriodServiceImpl.patchApprovePeriod"),

    tc("TC-ACC-009",
       "Approve period: blocked when any employee has extended period",
       "Employee X has extended report period in this office.",
       "1. PATCH approve to advance one month\n"
       "2. Verify error",
       "HTTP 400. Error: approve.notAllowed.extendedPeriod (via MessageUtil).\n"
       "Entire office blocked by single employee with extension.",
       "High", "Negative",
       "REQ-period-management", "OfficePeriodServiceImpl.patchApprovePeriod",
       "Design issue: ANY employee blocks ALL. Must remove all extensions first."),

    tc("TC-ACC-010",
       "BUG: Approve period accepts non-first-day-of-month",
       "Accountant with OFFICES_EDIT.",
       "1. PATCH approve period to {\"start\": \"2026-03-15\"}\n"
       "2. Verify response",
       "BUG: HTTP 200 — mid-month date accepted.\n"
       "Report period enforces first-of-month check but approve period does NOT.\n"
       "Missing validation in patchApprovePeriod.",
       "Critical", "Bug verification",
       "BUG-PERIOD-1", "OfficePeriodServiceImpl.patchApprovePeriod",
       "Confirmed in S52 live testing. Report period has this check, approve does not."),

    tc("TC-ACC-011",
       "BUG: NPE on null start in PATCH body",
       "Accountant with OFFICES_EDIT.",
       "1. PATCH /api/ttt/v1/offices/{officeId}/periods/report\n"
       "   Body: {}\n"
       "2. Verify error response",
       "BUG: HTTP 500 NullPointerException.\n"
       "PeriodPatchRequestDTO has @NotNull on start field but NPE occurs before validation.\n"
       "Should return 400 with validation error.",
       "High", "Bug verification",
       "BUG-PERIOD-2", "OfficePeriodController",
       "Stack trace leakage — security issue"),

    tc("TC-ACC-012",
       "Period min/max cross-office aggregation",
       "Multiple salary offices exist with different period settings.",
       "1. GET /api/ttt/v1/offices/periods/report/min\n"
       "2. GET /api/ttt/v1/offices/periods/report/max\n"
       "3. GET /api/ttt/v1/offices/periods/approve/min\n"
       "4. GET /api/ttt/v1/offices/periods/approve/max",
       "Each returns the earliest/latest period start across all offices.\n"
       "Min returns the oldest open period.\n"
       "Max returns the most advanced period.",
       "Medium", "Functional",
       "REQ-period-management", "OfficePeriodController",
       "Used by frontend to determine date picker boundaries"),

    tc("TC-ACC-013",
       "Report period equals approve period: boundary",
       "Report = March 2026, Approve = March 2026 (same month).",
       "1. Verify both periods at same month\n"
       "2. PATCH report period to April (advance)\n"
       "3. Verify approve still at March",
       "Both periods can be at the same month.\n"
       "Report can advance independently.\n"
       "Report period must always >= approve period.",
       "Medium", "Boundary",
       "REQ-period-management", "OfficePeriodServiceImpl"),

    tc("TC-ACC-014",
       "Period advance triggers auto-reject of unapproved reports",
       "Reports exist in the period being closed.\n"
       "Some reports are unapproved (state=REPORTED).",
       "1. PATCH approve period to advance one month\n"
       "2. Check if unapproved reports are auto-rejected\n"
       "3. Verify email notifications sent to affected employees",
       "Unapproved reports in closed period are auto-rejected.\n"
       "Reject notifications sent via sendRejectNotifications scheduler.\n"
       "Auto-reject sets state to REJECTED with system comment.",
       "Critical", "Integration",
       "REQ-report-confirmation", "PeriodChangedApplicationEventListener",
       "Cascading effect — period change affects report states"),

    tc("TC-ACC-015",
       "Period advance triggers vacation day recalculation",
       "Approve period at February. Employees have time reports for February.",
       "1. PATCH approve period to March\n"
       "2. Check vacation day balances for affected employees\n"
       "3. Verify norm-based recalculation ran",
       "If office NormDeviationType != NONE and AV=true:\n"
       "AvailableDaysRecalculationServiceImpl recalculates.\n"
       "Difference = reported - personalNorm.\n"
       "daysDelta = difference / 8, scale 3, HALF_UP.\n"
       "ConfirmationPeriodDays records saved for potential reverse.",
       "High", "Integration",
       "REQ-norm-recalculation", "AvailableDaysRecalculationServiceImpl",
       "Only runs if NormDeviationType != NONE AND isAdvanceVacation == true"),

    tc("TC-ACC-016",
       "Period caching: eviction on PATCH, cache hit on GET",
       "Period already queried (cached).",
       "1. GET period — note response time\n"
       "2. GET period again — should be from cache\n"
       "3. PATCH period — evicts cache\n"
       "4. GET period — fresh from DB",
       "Cache key: CACHE_OFFICE_PERIOD.\n"
       "PATCH explicitly evicts cache entry.\n"
       "Subsequent GET fetches from database.",
       "Low", "Performance",
       "REQ-period-management", "OfficePeriodCacheConfiguration"),

    tc("TC-ACC-017",
       "BUG: AUTHENTICATED_USER permission on PATCH endpoints",
       "Regular employee (no OFFICES_EDIT permission).",
       "1. PATCH /api/ttt/v1/offices/{officeId}/periods/report\n"
       "   Body: {\"start\": \"2026-05-01\"}\n"
       "2. Verify response",
       "HTTP 403 Forbidden.\n"
       "Controller annotation uses AUTHENTICATED_USER (overly permissive),\n"
       "but OfficePeriodValidator.validateWriteAccess() provides real access control.\n"
       "Should still return 403 due to service-level guard.",
       "High", "Security",
       "BUG-PERIOD-3", "OfficePeriodController, OfficePeriodValidator",
       "Design issue: controller-level @PreAuthorize is too broad, relies on service-level check"),

    tc("TC-ACC-018",
       "BUG: Invalid office ID returns 200 with default data",
       "Valid authentication.",
       "1. GET /api/ttt/v1/offices/99999/periods/report\n"
       "2. GET /api/ttt/v1/offices/0/periods/report\n"
       "3. GET /api/ttt/v1/offices/-1/periods/report",
       "BUG: Returns 200 with default period = previous month 1st day.\n"
       "Should return 404 for nonexistent office.\n"
       "InternalOfficePeriodService.findPeriodStart defaults to previousMonthFirstDay.",
       "High", "Bug verification",
       "BUG-PERIOD-4", "InternalOfficePeriodService",
       "Design issue: default period for non-existent offices masks errors"),

    tc("TC-ACC-019",
       "Extended period: grant and verify employee can report in approve period",
       "Office with report period=April, approve period=March.\n"
       "Employee X is in this office.",
       "1. PUT extended period for employee X\n"
       "2. GET employee report period — should return approve period start (March)\n"
       "3. Verify employee can submit reports for March dates\n"
       "4. Verify notification sent about extension",
       "Employee X can report from March (approve period) instead of April (report period).\n"
       "getEmployeeReportPeriod returns approve period start when extension active.\n"
       "Email notification sent on grant.",
       "High", "Functional",
       "REQ-extended-period", "EmployeeExtendedPeriodServiceImpl"),

    tc("TC-ACC-020",
       "Extended period: remove and verify employee reverts to normal",
       "Employee X has active extended period.",
       "1. DELETE extended period for employee X\n"
       "2. GET employee report period — should return report period start\n"
       "3. Verify notification sent about removal",
       "Employee X can no longer report in approve period.\n"
       "getEmployeeReportPeriod returns report period start.\n"
       "Email notification sent on removal.",
       "High", "Functional",
       "REQ-extended-period", "EmployeeExtendedPeriodServiceImpl"),

    tc("TC-ACC-021",
       "Extended period: cron cleanup of expired extensions",
       "Extended periods exist with expired deadlines.",
       "1. Trigger ExtendedPeriodScheduler.cleanUp (cron: every 5min)\n"
       "2. Verify expired extensions removed\n"
       "3. Verify affected employees notified",
       "Expired extensions automatically cleaned up.\n"
       "ShedLock-protected: only one instance runs.\n"
       "Affected employees notified via email.",
       "Medium", "Functional",
       "REQ-extended-period", "ExtendedPeriodScheduler",
       "Runs every 5 minutes, ShedLock name: ExtendedPeriodScheduler.cleanUp"),

    tc("TC-ACC-022",
       "Concurrent period modifications by two accountants",
       "Two accountants have OFFICES_EDIT on same office.",
       "1. Accountant A sends PATCH to advance report period\n"
       "2. Accountant B sends PATCH to advance report period (simultaneously)\n"
       "3. Verify one succeeds and the other gets consistent state",
       "Both should succeed sequentially (no optimistic locking on periods).\n"
       "Final state should be consistent (last write wins).\n"
       "No 500 errors or corrupt state.",
       "Medium", "Concurrency",
       "REQ-period-management", "OfficePeriodServiceImpl"),
]

# ── TS-ACC-Payment (Vacation Payment Flow) ───────────────────

TS_ACC_PAYMENT = [
    tc("TC-ACC-023",
       "Pay vacation: APPROVED → PAID with correct day split",
       "APPROVED vacation (id=V, REGULAR, 10 days) for employee.\n"
       "Logged in as accountant/chief accountant.",
       "1. GET /api/vacation/v1/vacationdays/{login} — note current balance\n"
       "2. PUT /api/vacation/v1/vacations/pay/{V}\n"
       "   Body: {\"regularDaysPayed\": 10, \"administrativeDaysPayed\": 0}\n"
       "3. GET vacation — verify status=PAID\n"
       "4. GET vacation days — verify balance unchanged",
       "HTTP 200. Status transitions to PAID.\n"
       "VacationPaymentEntity created with regularDaysPayed=10.\n"
       "vacation_payment record linked.\n"
       "VacationStatusChangedEvent published.\n"
       "Vacation days balance UNCHANGED — deduction happens at approval, not payment.",
       "Critical", "Functional",
       "REQ-vacation-payment", "PayVacationServiceImpl.payVacation",
       "Key insight: days deducted at APPROVAL, payment is accounting-only status change"),

    tc("TC-ACC-024",
       "Payment days mismatch: regularDays + adminDays != vacation.days",
       "APPROVED vacation with 5 total days.",
       "1. PUT pay with {\"regularDaysPayed\": 3, \"administrativeDaysPayed\": 0}\n"
       "2. Verify error",
       "HTTP 400. Error: exception.vacation.pay.days.not.equal.\n"
       "checkForPayment validates: regularDaysPayed + administrativeDaysPayed == entity.getDays().\n"
       "Must submit exact total.",
       "Critical", "Validation",
       "REQ-vacation-payment", "PayVacationServiceImpl.checkForPayment"),

    tc("TC-ACC-025",
       "Payment rejected for non-APPROVED vacation",
       "Vacation in NEW status (not yet approved).",
       "1. PUT pay vacation in NEW status\n"
       "2. PUT pay vacation in CANCELED status\n"
       "3. PUT pay vacation in REJECTED status",
       "All return HTTP 400. Error: exception.vacation.status.notAllowed.\n"
       "Only APPROVED vacations can be paid.",
       "High", "Negative",
       "REQ-vacation-payment", "PayVacationServiceImpl.checkForPayment"),

    tc("TC-ACC-026",
       "Payment rejected for APPROXIMATE period type",
       "APPROVED vacation with periodType=APPROXIMATE (future dates uncertain).",
       "1. PUT pay this vacation\n"
       "2. Verify error",
       "HTTP 400. Error: exception.vacation.period.type.notAllowed.\n"
       "Only EXACT period vacations can be paid — dates must be finalized.",
       "High", "Negative",
       "REQ-vacation-payment", "PayVacationServiceImpl.checkForPayment"),

    tc("TC-ACC-027",
       "Payment rejected for already-PAID vacation",
       "Vacation already in PAID status.",
       "1. PUT pay this vacation again\n"
       "2. Verify error",
       "HTTP 400. Error: exception.vacation.status.notAllowed.\n"
       "Already-PAID vacation cannot be paid again (idempotency fail).",
       "High", "Negative",
       "REQ-vacation-payment", "PayVacationServiceImpl.checkForPayment"),

    tc("TC-ACC-028",
       "Payment: write lock prevents concurrent duplicate payments",
       "APPROVED vacation V.",
       "1. Send two simultaneous PUT /pay/{V} requests\n"
       "2. Verify one succeeds, other fails or is queued",
       "Write lock acquired via findByIdAndAcquireWriteLock.\n"
       "Second request blocks until first completes.\n"
       "If first succeeds, second gets 400 (already PAID).\n"
       "No duplicate payment records created.",
       "High", "Concurrency",
       "REQ-vacation-payment", "PayVacationServiceImpl",
       "Uses SELECT FOR UPDATE in repository"),

    tc("TC-ACC-029",
       "Payment validation: regularDaysPayed range 0-366",
       "APPROVED vacation.",
       "1. PUT pay with {\"regularDaysPayed\": -1, \"administrativeDaysPayed\": 0}\n"
       "2. PUT pay with {\"regularDaysPayed\": 367, \"administrativeDaysPayed\": 0}\n"
       "3. PUT pay with {\"regularDaysPayed\": 0, \"administrativeDaysPayed\": 0}",
       "Step 1: HTTP 400. @Range(0,366) violation.\n"
       "Step 2: HTTP 400. @Range(0,366) violation.\n"
       "Step 3: HTTP 400 (days mismatch unless vacation has 0 days).",
       "Medium", "Boundary",
       "REQ-vacation-payment", "VacationPaymentDTO"),

    tc("TC-ACC-030",
       "Payment: null/empty body rejected",
       "APPROVED vacation.",
       "1. PUT pay with empty body {}\n"
       "2. PUT pay with null body",
       "HTTP 400. regularDaysPayed and administrativeDaysPayed must not be null (@NotNull).",
       "Medium", "Validation",
       "REQ-vacation-payment", "VacationPaymentDTO"),

    tc("TC-ACC-031",
       "BUG: Payment type misalignment allowed",
       "ADMINISTRATIVE vacation (1 day).",
       "1. PUT pay with {\"regularDaysPayed\": 1, \"administrativeDaysPayed\": 0}\n"
       "   (paying admin vacation as regular)\n"
       "2. Verify response and DB",
       "BUG: HTTP 200 — payment accepted with wrong type split.\n"
       "checkForPayment validates only total (regular+admin==days),\n"
       "NOT that the split matches paymentType.\n"
       "Causes incorrect accounting classification.",
       "High", "Bug verification",
       "BUG-PAY-1", "PayVacationServiceImpl.checkForPayment",
       "Confirmed in live testing. ADMINISTRATIVE vac paid with regularDaysPayed=1."),

    tc("TC-ACC-032",
       "BUG: Same error code for 5 different payment failures",
       "Various invalid payment states.",
       "1. Pay non-APPROVED vacation → exception.vacation.status.notAllowed\n"
       "2. Pay APPROXIMATE period → same code\n"
       "3. Pay without accountant role → same code\n"
       "4. Observe that 3 distinct failures return identical error code",
       "BUG: All 4 scenarios return exception.vacation.status.notAllowed.\n"
       "Cannot distinguish cause from error response.\n"
       "Only days mismatch has distinct code: exception.vacation.pay.days.not.equal.",
       "Medium", "Bug verification",
       "BUG-PAY-2", "PayVacationServiceImpl.checkForPayment",
       "Design issue: impossible for frontend/user to know what went wrong"),

    tc("TC-ACC-033",
       "Partial payment: day return to balance",
       "REGULAR vacation for 5 days. Employee has 3 nextYear + 2 thisYear days used.",
       "1. PUT pay with {\"regularDaysPayed\": 3, \"administrativeDaysPayed\": 0}\n"
       "   (paying 3 of 5 days)\n"
       "2. GET vacation days — check balance change",
       "HTTP 200 (if total matches — but this is 3 != 5 → rejected).\n"
       "NOTE: partial payment is NOT supported by the current validation.\n"
       "regularDaysPayed + administrativeDaysPayed MUST equal vacation.getDays().\n"
       "The returnDaysToEmployeeIfPaidLess logic exists but is unreachable for partial.",
       "High", "Functional",
       "REQ-vacation-payment", "PayVacationServiceImpl",
       "Misleading: code has returnDaysToEmployeeIfPaidLess but validation prevents partial pay"),

    tc("TC-ACC-034",
       "Administrative vacation: skip day redistribution on payment",
       "APPROVED administrative vacation, 2 days.",
       "1. PUT pay with {\"regularDaysPayed\": 0, \"administrativeDaysPayed\": 2}\n"
       "2. GET vacation days before and after",
       "HTTP 200. Status → PAID.\n"
       "ADMINISTRATIVE vacations skip returnDaysToEmployeeIfPaidLess entirely.\n"
       "Day balance unchanged (admin days not deducted from regular balance).",
       "High", "Functional",
       "REQ-vacation-payment", "PayVacationServiceImpl"),

    tc("TC-ACC-035",
       "Auto-payment cron: payExpiredApproved",
       "APPROVED vacations older than 2 months exist.",
       "1. Trigger AutomaticallyPayApprovedTask (cron: daily 00:00 NSK)\n"
       "2. Check vacation statuses after\n"
       "3. Verify payment records created",
       "APPROVED vacations with endDate < today.minusMonths(2).withDayOfMonth(2) are auto-paid.\n"
       "Each auto-payment: regularDays or adminDays assigned based on paymentType.\n"
       "ShedLock name: CloseOutdatedTask.run.\n"
       "Status → PAID.",
       "High", "Functional",
       "REQ-vacation-payment", "PayVacationServiceImpl.payExpiredApproved",
       "Hardcoded 2-month threshold, Collections.singleton(0L) magic value"),

    tc("TC-ACC-036",
       "Payment dates endpoint: valid calculation",
       "Valid vacation dates.",
       "1. GET /api/vacation/v1/paymentdates?vacationStartDate=2026-06-01&vacationEndDate=2026-06-14\n"
       "2. Verify date list",
       "Returns set of 1st-of-month dates between:\n"
       "(vacStart - 2 months, bounded by report period) and (vacEnd + 6 months).\n"
       "E.g. 2026-04-01 through 2026-12-01 (array of LocalDate).",
       "Medium", "Functional",
       "REQ-vacation-payment", "VacationPaymentController"),

    tc("TC-ACC-037",
       "BUG: Payment dates accepts start > end",
       "Valid authentication.",
       "1. GET /api/vacation/v1/paymentdates?vacationStartDate=2026-04-01&vacationEndDate=2026-03-01\n"
       "   (start after end)",
       "BUG: HTTP 200 — returns valid results (same as normal range).\n"
       "No validation that vacationStartDate <= vacationEndDate.",
       "Medium", "Bug verification",
       "BUG-PAY-3", "VacationPaymentController",
       "Confirmed in live testing"),

    tc("TC-ACC-038",
       "Available paid days: binary search mode (newDays=0)",
       "Employee with vacation days balance.",
       "1. GET /api/vacation/v1/vacationdays/available\n"
       "   ?employeeLogin={login}&paymentDate=2026-06-01&newDays=0\n"
       "2. Verify response",
       "newDays=0 triggers binary search mode.\n"
       "Returns maximum safe days (availablePaidDays).\n"
       "daysNotEnough array lists future vacations that would be affected.",
       "Medium", "Functional",
       "REQ-vacation-payment", "EmployeeDaysServiceImpl",
       "Used by payment UI main page mode"),

    tc("TC-ACC-039",
       "BUG: Available paid days accepts negative newDays",
       "Valid employee login.",
       "1. GET /api/vacation/v1/vacationdays/available?...&newDays=-5\n"
       "2. Verify response",
       "BUG: Returns availablePaidDays=16.0 without error.\n"
       "Should reject non-positive newDays values.",
       "Low", "Bug verification",
       "BUG-PAY-4", "EmployeeDaysServiceImpl",
       "Confirmed in live testing"),

    tc("TC-ACC-040",
       "BUG: VacationStatusUpdateJob 2-hour orphan window",
       "Vacation payment creates NEW_FOR_PAID status_updates entry.",
       "1. Create vacation payment (triggers status update job entry)\n"
       "2. Wait >2 hours (or check DB for stuck entries)\n"
       "3. Query: SELECT * FROM status_updates WHERE status='NEW_FOR_PAID'\n"
       "   AND created < now() - interval '2 hours'",
       "BUG: VacationStatusUpdateJob queries findRecentNew(now.minusHours(2)).\n"
       "Entries older than 2 hours are permanently orphaned.\n"
       "Found 6 stuck entries for Saturn office (created 18:22-18:27, >19h old).\n"
       "No cleanup/retry mechanism exists.",
       "Critical", "Bug verification",
       "BUG-PAY-5", "VacationStatusUpdateJob",
       "Entries are lost forever — no retry, no alerting, no manual recovery"),

    tc("TC-ACC-041",
       "BUG: DB/API data representation inconsistency for ADMINISTRATIVE vacations",
       "ADMINISTRATIVE vacation in database.",
       "1. Query DB: SELECT regular_days, administrative_days FROM vacation WHERE id={V}\n"
       "2. GET /api/vacation/v1/vacations/{V}\n"
       "3. Compare DB vs API representation",
       "BUG: ADMINISTRATIVE vacations store days in DB regular_days column\n"
       "(e.g., regular_days=1, administrative_days=0),\n"
       "but API returns them swapped: regularDays=0, administrativeDays=1.\n"
       "DTO conversion transposes based on payment_type.\n"
       "DB queries for reporting give wrong day-type breakdowns.",
       "High", "Bug verification",
       "BUG-PAY-6", "VacationMapper / DTO conversion",
       "Confirmed in live testing"),

    tc("TC-ACC-042",
       "Payment timeline audit: VACATION_PAID event completeness",
       "Pay a vacation and check timeline.",
       "1. PUT pay vacation\n"
       "2. GET /api/vacation/v1/timelines/days-summary/{login}\n"
       "3. Check timeline events for VACATION_PAID",
       "Timeline event created with type=VACATION_PAID.\n"
       "BUG: days_used=0, administrative_days_used=0 — event doesn't record\n"
       "how many days were paid or the regular/admin split.\n"
       "previous_status=NULL. Audit trail incomplete.",
       "Medium", "Functional",
       "REQ-vacation-payment", "PayVacationServiceImpl",
       "Audit gap — cannot reconstruct payment details from timeline alone"),

    tc("TC-ACC-043",
       "Nonexistent vacation ID payment returns 400 not 404",
       "Valid accountant auth.",
       "1. PUT /api/vacation/v1/vacations/pay/99999999\n"
       "2. Verify error code and HTTP status",
       "HTTP 400. Error: 'Vacation id not found' (plain text, not standard error code).\n"
       "Should be 404 per REST conventions.",
       "Medium", "Negative",
       "REQ-vacation-payment", "PayVacationServiceImpl",
       "Error handling inconsistency — 400 vs 404"),

    tc("TC-ACC-044",
       "Bulk payment via UI: 'Pay all checked requests'",
       "Multiple APPROVED vacations visible on /vacation/payment page.",
       "1. Navigate to /vacation/payment\n"
       "2. Check multiple regular vacation checkboxes\n"
       "3. Click 'Pay all checked requests'\n"
       "4. Verify all selected become PAID",
       "All checked vacations paid in batch.\n"
       "Administrative vacations have no checkbox — excluded from bulk.\n"
       "Individual VacationPaymentEntity created per vacation.\n"
       "Page refreshes to show updated statuses.",
       "High", "UI",
       "REQ-vacation-payment", "Accounting Payment page",
       "UI observation: admin vacations have no checkbox, no status, no actions"),
]

# ── TS-ACC-DayCorrection (Vacation Day Correction & Recalculation) ──

TS_ACC_DAYCORRECTION = [
    tc("TC-ACC-045",
       "Manual correction: positive adjustment with comment",
       "Logged in as accountant. Employee in accountant's assigned office.\n"
       "Employee available days = 20.0, AV=true.",
       "1. PUT /api/vacation/v1/vacationdays/{login}\n"
       "   Body: {\"availableDays\": 21.0, \"comment\": \"Annual correction\"}\n"
       "2. GET vacation days — verify new balance\n"
       "3. Check timeline for DAYS_ADJUSTMENT event",
       "HTTP 200. availableDays updated to 21.0.\n"
       "DAYS_ADJUSTMENT timeline event with days_accrued=1.000.\n"
       "Comment 'Annual correction' stored in event.",
       "Critical", "Functional",
       "REQ-day-correction", "EmployeeDaysServiceImpl.manualAdjustment"),

    tc("TC-ACC-046",
       "Manual correction: negative adjustment (AV=true office)",
       "Employee in AV=true office. Available days = 20.0.",
       "1. PUT /api/vacation/v1/vacationdays/{login}\n"
       "   Body: {\"availableDays\": 18.0, \"comment\": \"Overpayment fix\"}\n"
       "2. Verify balance update",
       "HTTP 200. Days reduced by 2.\n"
       "Negative adjustment allowed for AV=true offices.\n"
       "Zeroes out previous years' balances, sets current year to correction value.\n"
       "DAYS_ADJUSTMENT event with negative delta.",
       "High", "Functional",
       "REQ-day-correction", "EmployeeDaysServiceImpl.manualAdjustForNegativeDaysChanged"),

    tc("TC-ACC-047",
       "Manual correction: negative adjustment rejected for AV=false office",
       "Employee in AV=false office (e.g., Venera). Available days = 88.0.",
       "1. PUT /api/vacation/v1/vacationdays/{login}\n"
       "   Body: {\"availableDays\": 83.0, \"comment\": \"Reduction\"}\n"
       "2. Verify error",
       "HTTP 400. InvalidVacationDaysCorrectionException.\n"
       "Error: exception.invalid.vacation.days.correction.\n"
       "AV=false offices cannot have negative corrections.",
       "Critical", "Negative",
       "REQ-day-correction", "EmployeeDaysServiceImpl.manualAdjustment",
       "Confirmed in live testing with abaymaganov on Venera"),

    tc("TC-ACC-048",
       "Manual correction: comment required (1-255 chars)",
       "Accountant with correct permissions.",
       "1. PUT with {\"availableDays\": 21, \"comment\": \"\"}\n"
       "2. PUT with {\"availableDays\": 21, \"comment\": null}\n"
       "3. PUT with {\"availableDays\": 21} (no comment field)\n"
       "4. PUT with comment of 256 characters",
       "Steps 1-3: HTTP 400 — comment @NotNull @Size(min=1).\n"
       "Step 4: HTTP 400 — @Size(max=255) exceeded.\n"
       "Comment is required for audit trail.",
       "High", "Validation",
       "REQ-day-correction", "UpdateVacationDaysDTO"),

    tc("TC-ACC-049",
       "Manual correction: no numeric limit on availableDays",
       "AV=true office employee.",
       "1. PUT with {\"availableDays\": 99999.999, \"comment\": \"test\"}\n"
       "2. PUT with {\"availableDays\": -100, \"comment\": \"test\"}\n"
       "3. PUT with {\"availableDays\": 0, \"comment\": \"test\"}",
       "All accepted (no @Range on availableDays in DTO).\n"
       "Step 2: accepted for AV=true (no range validation).\n"
       "Step 3: accepted (zero balance valid).\n"
       "Only AV=false blocks negative at service level, not DTO level.",
       "Medium", "Boundary",
       "REQ-day-correction", "UpdateVacationDaysDTO, EmployeeDaysServiceImpl",
       "No upper or lower bound validation in DTO — extreme values accepted"),

    tc("TC-ACC-050",
       "Manual correction: permission check — accountant for correct office only",
       "Accountant assigned to office A. Employee is in office B.",
       "1. PUT correction for employee in office B\n"
       "2. Verify error",
       "HTTP 403. VacationSecurityException.\n"
       "statusManager.isAccountant(getCurrent()) must be true AND\n"
       "employee's officeId must be in accountant's assigned offices.",
       "High", "Security",
       "REQ-day-correction", "EmployeeDaysServiceImpl.manualAdjustment"),

    tc("TC-ACC-051",
       "BUG: pastPeriodsAvailableDays drift on net-zero corrections",
       "Employee with pastPeriodsAvailableDays = 5.625.",
       "1. PUT correction +1 day\n"
       "2. PUT correction -1 day (back to original total)\n"
       "3. GET vacation days — check pastPeriodsAvailableDays",
       "BUG: pastPeriodsAvailableDays drifts downward.\n"
       "After net-zero cycle: 5.625 → 0.\n"
       "Root cause: increases don't add to sub-components,\n"
       "but decreases subtract from pastPeriodsAvailableDays first (oldest-first).\n"
       "Total availableDays correct but sub-component breakdown drifts.\n"
       "Bulk recalculate does NOT fix this.",
       "High", "Bug verification",
       "BUG-DAYS-1", "EmployeeDaysServiceImpl",
       "Confirmed in live testing: abpopov 5.625→0 after 4 net-zero corrections"),

    tc("TC-ACC-052",
       "BUG: double arithmetic for financial day calculations",
       "Positive adjustment where daysChangedByAccounting > availableDays.",
       "1. PUT correction with fractional value near floating point boundary\n"
       "   e.g., availableDays=0.1+0.2 (JavaScript: 0.30000000000000004)\n"
       "2. Verify storage precision",
       "Potential precision issue: code uses double arithmetic.\n"
       "daysToSubract variable uses doubleValue() for BigDecimal operations.\n"
       "Risk of floating point rounding errors in financial calculations.",
       "Medium", "Bug verification",
       "BUG-DAYS-2", "EmployeeDaysServiceImpl.manualAdjustForPositiveDaysChanged",
       "Design issue: double for financial math. Impact depends on specific values."),

    tc("TC-ACC-053",
       "Bulk recalculate for salary office",
       "Office with multiple employees.",
       "1. POST /api/vacation/v1/vacationdays/recalculate?officeId={id}&date={today}\n"
       "2. Check for DAYS_ADJUSTMENT events for affected employees",
       "HTTP 200. Recalculation runs for all employees in office.\n"
       "Creates DAYS_ADJUSTMENT events for employees with norm differences.\n"
       "Only affects employees who started before recalculation month.\n"
       "Only runs if NormDeviationType != NONE and AV=true.",
       "High", "Functional",
       "REQ-norm-recalculation", "AvailableDaysRecalculationServiceImpl",
       "Tested: POST recalculate created +1.313 days for amatiushin"),

    tc("TC-ACC-054",
       "Norm recalculation: skip conditions",
       "Office with NormDeviationType=NONE or AV=false.",
       "1. POST recalculate for office with NormDeviationType=NONE\n"
       "2. POST recalculate for office with AV=false\n"
       "3. POST recalculate for employee who started after recalculation month",
       "No DAYS_ADJUSTMENT events created.\n"
       "All three conditions must be met:\n"
       "1. NormDeviationType != NONE\n"
       "2. isAdvanceVacation == true\n"
       "3. Employee started before recalculation month.",
       "Medium", "Negative",
       "REQ-norm-recalculation", "AvailableDaysRecalculationServiceImpl"),

    tc("TC-ACC-055",
       "BUG: Norm recalculation double comparison (== 0) unreliable",
       "Employee with reported hours very close to personalNorm.",
       "1. Set reported hours = personalNorm (e.g., both 160.0)\n"
       "2. Trigger recalculation\n"
       "3. Check if recalculation is skipped",
       "Code uses: if (difference == 0) skip recalculation.\n"
       "BUG: double equality comparison. If difference is 1e-15 due to\n"
       "floating point, recalculation runs for effectively-zero difference.\n"
       "daysDelta = 1e-15 / 8 ≈ 0 but may create spurious events.",
       "Medium", "Bug verification",
       "BUG-DAYS-3", "AvailableDaysRecalculationServiceImpl.recalculateDays",
       "Design issue: should use epsilon comparison or BigDecimal"),

    tc("TC-ACC-056",
       "Recalculation reverse on period reopen",
       "Approve period advanced, norm recalculation ran, then period reopened (reverted).",
       "1. Advance approve period → norm recalculation runs, saves ConfirmationPeriodDays\n"
       "2. Revert approve period (move backward)\n"
       "3. Verify days restored from ConfirmationPeriodDays\n"
       "4. Verify MonthlyRecalculationReverseEvent published",
       "Days restored to pre-recalculation values.\n"
       "ConfirmationPeriodDays records deleted after restore.\n"
       "MonthlyRecalculationReverseEvent published if delta != 0.",
       "High", "Functional",
       "REQ-norm-recalculation", "AvailableDaysRecalculationServiceImpl.recalculationReverse"),

    tc("TC-ACC-057",
       "Days grouped by years breakdown",
       "Employee with multi-year vacation day balances.",
       "1. GET /api/vacation/v1/vacationdays/{login}/years\n"
       "2. Verify yearly breakdown",
       "Returns array: [{year: 2025, days: 6}, {year: 2026, days: 24}, ...].\n"
       "Shows how days are distributed across accrual years.\n"
       "Sum of yearly days = total availableDays.",
       "Medium", "Functional",
       "REQ-day-correction", "VacationDaysController"),

    tc("TC-ACC-058",
       "Days summary timeline: accrued vs used totals",
       "Employee with vacation history.",
       "1. GET /api/vacation/v1/timelines/days-summary/{login}\n"
       "2. Verify totalAccruedDays, totalUsedDays, totalAdministrativeDays",
       "Returns complete day accounting summary.\n"
       "totalAccruedDays: all accrued days across years.\n"
       "totalUsedDays: days consumed by approved/paid vacations.\n"
       "totalAdministrativeDays: admin-type days used.",
       "Medium", "Functional",
       "REQ-day-correction", "TimelineController"),

    tc("TC-ACC-059",
       "Probation limit: 3-month restriction on new employees",
       "Employee started less than 3 months ago.",
       "1. Check if employee can create regular vacation\n"
       "2. Calculate available days with DaysLimitationService",
       "Within first 3 months: vacation days limited to 0 (hardcoded).\n"
       "Limit: List.of(new Limit(3, BigDecimal.valueOf(0))).\n"
       "Uses FirstWorkingDayCalculator.calculateVeryFirstDay().\n"
       "After 3 months: normal accrual rules apply.",
       "Medium", "Boundary",
       "REQ-day-correction", "DaysLimitationService",
       "Design issue: hardcoded 3-month/0-day, not configurable"),

    tc("TC-ACC-060",
       "Cross-year balance redistribution (FIFO)",
       "Employee with days in multiple years: 2024=5, 2025=10, 2026=24.",
       "1. Create vacation consuming 30 days\n"
       "2. Verify day deduction order",
       "Days deducted oldest-first (FIFO):\n"
       "2024: 5→0, 2025: 10→0, 2026: 24→9.\n"
       "VacationDaysDistributor handles distribution.\n"
       "Non-AV: oldest first. AV: same for positive, current year can go negative.",
       "High", "Functional",
       "REQ-day-correction", "VacationDaysDistributor"),

    tc("TC-ACC-061",
       "Annual accruals cron job: new year day creation",
       "Employee active on January 1st.",
       "1. Trigger AnnualAccrualsTask (cron: Jan 1 00:00 NSK)\n"
       "2. Verify new year's vacation day accrual entry created",
       "Publishes EmployeeNewYearEvent for each active employee.\n"
       "Event handlers create new accrual entries for the new year.\n"
       "ShedLock-protected: AnnualAccrualsTask.\n"
       "Last run: 2025-12-31 17:00 UTC.",
       "Medium", "Functional",
       "REQ-day-correction", "AnnualAccrualsTask",
       "Runs once per year, verified in ShedLock"),
]

# ── TS-ACC-Views (Accounting Views & Notifications) ──────────

TS_ACC_VIEWS = [
    tc("TC-ACC-062",
       "Salary page: employee search and filter",
       "Logged in as chief accountant/accountant. Navigate to /admin/salary.",
       "1. Search by employee name\n"
       "2. Filter by salary office\n"
       "3. Set date range\n"
       "4. Toggle 'Show only leaving employees'",
       "Search: keyboard layout auto-correction (RU↔EN via SuggestionMappingUtil.correctLayout).\n"
       "SQL LIKE wrapping for employee search.\n"
       "Filter: salary office dropdown limits to accountant's assigned offices.\n"
       "Date range: period start/end pickers.\n"
       "Toggle: shows only employees with upcoming dismissal.",
       "Medium", "Functional",
       "REQ-accounting-views", "TaskReportAccountingServiceImpl, Salary page"),

    tc("TC-ACC-063",
       "Salary page: individual manager notification",
       "Unapproved reports exist for a manager.",
       "1. Navigate to /admin/salary\n"
       "2. Find row with unapproved hours\n"
       "3. Click envelope icon on that row\n"
       "4. Verify notification sent",
       "Email notification sent to the manager about unapproved reports.\n"
       "Envelope icon visible per row.\n"
       "Manager name shown in 'Managers who haven't confirmed' column.",
       "Medium", "Functional",
       "REQ-accounting-notifications", "TaskReportAccountingServiceImpl"),

    tc("TC-ACC-064",
       "Salary page: 'Notify all managers' bulk notification",
       "Multiple managers have unapproved reports.",
       "1. Navigate to /admin/salary\n"
       "2. Click 'Notify all managers' button\n"
       "3. Verify all affected managers notified",
       "Bulk notification sent to all managers with unapproved reports.\n"
       "Uses notifyManagers() method.\n"
       "Permission: ADMIN, CHIEF_ACCOUNTANT, or ACCOUNTANT.",
       "High", "Functional",
       "REQ-accounting-notifications", "TaskReportAccountingServiceImpl.notifyManagers",
       "Design issue: VIEW_ALL role cannot NOTIFY — permission gap"),

    tc("TC-ACC-065",
       "Budget notification: create with man-day limit",
       "Accountant on budget notification page.",
       "1. POST budget notification with:\n"
       "   startDate, endDate, projectId, employeeLogin, limit=100, repeatMonthly=false\n"
       "2. Verify notification created",
       "HTTP 200. Budget notification created.\n"
       "DTO: @NotNull startDate/endDate, @ProjectIdExists, @EmployeeLoginExists.\n"
       "@Min(0) on limit. @NotificationLimit: at least one of limit/limitPercent required.",
       "Medium", "Functional",
       "REQ-budget-notifications", "BudgetNotificationAddRequestDTO"),

    tc("TC-ACC-066",
       "Budget notification: percent mode requires exact month boundaries",
       "Accountant creating notification.",
       "1. POST with limitPercent=50, startDate=2026-03-01, endDate=2026-03-31\n"
       "   (exact month — valid)\n"
       "2. POST with limitPercent=50, startDate=2026-03-01, endDate=2026-04-15\n"
       "   (not exact month — invalid)",
       "Step 1: HTTP 200. Percent mode with exact month boundaries.\n"
       "Step 2: HTTP 400. @NotificationPeriod validation.\n"
       "If percent or repeatMonthly → period must be exactly one calendar month.",
       "Medium", "Validation",
       "REQ-budget-notifications", "BudgetNotificationAddRequestDTO",
       "@NotificationPeriod: 1st day to last day of same month"),

    tc("TC-ACC-067",
       "Budget notification: neither limit nor limitPercent provided",
       "Accountant creating notification.",
       "1. POST with no limit and no limitPercent\n"
       "2. Verify error",
       "HTTP 400. @NotificationLimit validation.\n"
       "At least one of limit or limitPercent must be provided.",
       "Medium", "Validation",
       "REQ-budget-notifications", "BudgetNotificationAddRequestDTO"),

    tc("TC-ACC-068",
       "Budget notification scheduler: BudgetNotificationScheduler",
       "Active budget notifications exist.",
       "1. Verify scheduler runs (cron: every 30 minutes)\n"
       "2. Check ShedLock for BudgetNotificationScheduler",
       "Scheduler checks all active notifications every 30 minutes.\n"
       "Sends email when budget threshold exceeded.\n"
       "ShedLock-protected.\n"
       "Last TM locked_at: 16:30 UTC.",
       "Medium", "Functional",
       "REQ-budget-notifications", "BudgetNotificationScheduler",
       "Verified running in ShedLock on both TM and Stage"),

    tc("TC-ACC-069",
       "Accounting permission: office scoping for ACCOUNTANT role",
       "Accountant assigned to office A only.",
       "1. GET /api/ttt/v1/reports/accounting?officeId={officeB}\n"
       "2. Verify error",
       "HTTP 403. TttSecurityException.\n"
       "ACCOUNTANT restricted to assigned offices.\n"
       "ADMIN/VIEW_ALL/CHIEF_ACCOUNTANT see all offices.",
       "High", "Security",
       "REQ-accounting-permissions", "AccountingPermissionProvider",
       "Office scoping is accountant-only restriction"),

    tc("TC-ACC-070",
       "Accounting permission: VIEW_ALL can view but cannot notify",
       "User with VIEW_ALL permission.",
       "1. GET /api/ttt/v1/reports/accounting — verify access\n"
       "2. POST notify managers — verify denied",
       "GET: allowed (VIEW_ALL in VIEW permissions).\n"
       "NOTIFY: denied (VIEW_ALL not in NOTIFY permissions).\n"
       "Design issue: VIEW_ALL can see data but can't trigger notifications.",
       "Medium", "Security",
       "REQ-accounting-permissions", "AccountingPermissionProvider",
       "Known gap: NOTIFY only for ADMIN, CHIEF_ACCOUNTANT, ACCOUNTANT"),

    tc("TC-ACC-071",
       "Forgotten report notification scheduler",
       "Employees have not submitted reports.",
       "1. Verify sendReportsForgotten runs (cron: MON/FRI 16:00 NSK)\n"
       "2. Verify sendReportsForgottenDelayed runs (cron: daily 16:30 NSK)\n"
       "3. Check ShedLock entries",
       "Two schedulers for forgotten reports:\n"
       "sendReportsForgotten: Monday+Friday 16:00 NSK.\n"
       "sendReportsForgottenDelayed: daily 16:30 NSK.\n"
       "Both verified running in ShedLock on TM and Stage.",
       "Medium", "Functional",
       "REQ-accounting-notifications", "Report notification schedulers",
       "85 INVALID emails found on TM — former employees with deactivated mailboxes"),

    tc("TC-ACC-072",
       "Reports changed notification scheduler",
       "Employee modified a previously confirmed report.",
       "1. Verify sendReportsChanged runs (cron: daily 07:50 NSK)\n"
       "2. Check notification content and recipients",
       "Scheduler: sendReportsChanged (daily 07:50 NSK, ShedLock-protected).\n"
       "Notifies managers when employees modify already-confirmed reports.\n"
       "Verified running: last TM locked_at 00:50 UTC.",
       "Medium", "Functional",
       "REQ-accounting-notifications", "Report notification schedulers"),

    tc("TC-ACC-073",
       "Vacation day correction UI: inline editing",
       "Navigate to /vacation/days-correction as accountant.",
       "1. Open /vacation/days-correction\n"
       "2. Find employee row\n"
       "3. Click vacation days cell — becomes editable\n"
       "4. Enter new value and comment\n"
       "5. Verify correction applied",
       "Cell becomes editable text field on click.\n"
       "Comment required (manual state check: comment !== '').\n"
       "No Yup/Formik — manual React state validation.\n"
       "Only comment validated client-side; numeric value accepted as-is.",
       "Medium", "UI",
       "REQ-day-correction", "CorrectVacationDaysModalContainer",
       "Frontend: no numeric validation — backend is sole guard"),

    tc("TC-ACC-074",
       "Events feed dialog: complete history display",
       "Employee with vacation history.",
       "1. Navigate to /vacation/days-correction\n"
       "2. Click events feed button for employee\n"
       "3. Verify dialog content",
       "Dialog shows: employee name, annual vacation days left, work dates.\n"
       "Events table: Date, Event, Paid/Unpaid days allowance/used.\n"
       "Total row at bottom. Shows DAYS_ADJUSTMENT, VACATION_APPROVED, VACATION_PAID events.",
       "Medium", "UI",
       "REQ-day-correction", "Days correction page"),

    tc("TC-ACC-075",
       "Show dismissed employees toggle",
       "Some employees in the office are dismissed.",
       "1. Navigate to /vacation/days-correction\n"
       "2. Toggle 'Show dismissed employees'\n"
       "3. Verify dismissed employees appear/disappear",
       "Toggle shows/hides dismissed employees in the list.\n"
       "Default: dismissed employees hidden.\n"
       "When shown: appear with same columns, may have zero balances.",
       "Low", "UI",
       "REQ-accounting-views", "Days correction page"),
]

# ── TS-ACC-SickLeave (Sick Leave Accounting Status) ──────────

TS_ACC_SICKLEAVE = [
    tc("TC-ACC-076",
       "Sick leave accounting: status workflow New → Pending → Paid",
       "Sick leave in database with accounting status = New.\n"
       "Logged in as accountant.",
       "1. Navigate to /accounting/sick-leaves\n"
       "2. Find sick leave with status 'New'\n"
       "3. Change status dropdown to 'Pending'\n"
       "4. Change status dropdown to 'Paid'\n"
       "5. Verify final status",
       "Status transitions: New → Pending → Paid.\n"
       "Each transition saves to database.\n"
       "Dropdown allows forward transitions only.",
       "High", "Functional",
       "REQ-sick-leave-accounting", "Sick leave accounting page"),

    tc("TC-ACC-077",
       "Sick leave accounting: reject from Pending",
       "Sick leave with accounting status = Pending.",
       "1. Find sick leave with status 'Pending'\n"
       "2. Change status to 'Rejected'\n"
       "3. Verify terminal state",
       "Status → Rejected (terminal state).\n"
       "No further status changes allowed for rejected sick leaves.\n"
       "Rejected sick leaves remain visible in table.",
       "High", "Functional",
       "REQ-sick-leave-accounting", "Sick leave accounting page"),

    tc("TC-ACC-078",
       "Sick leave accounting: overdue state display",
       "Sick leave with end date in the past, not yet processed.",
       "1. Navigate to /accounting/sick-leaves\n"
       "2. Filter by State: Overdue\n"
       "3. Verify overdue highlighting",
       "Overdue sick leaves highlighted in red.\n"
       "State=Overdue for unprocessed past sick leaves.\n"
       "Count of overdue sick leaves available via GET /open-overdue-sick-leave-count.",
       "Medium", "UI",
       "REQ-sick-leave-accounting", "Sick leave accounting page"),

    tc("TC-ACC-079",
       "Sick leave accounting: deleted state blocks status changes",
       "Deleted sick leave in the table.",
       "1. Find sick leave with State='Deleted'\n"
       "2. Attempt to change status dropdown\n"
       "3. Attempt edit/delete actions",
       "No status dropdown available for deleted sick leaves.\n"
       "No edit/delete actions available.\n"
       "Deleted entries are read-only in accounting view.",
       "Medium", "Negative",
       "REQ-sick-leave-accounting", "Sick leave accounting page"),

    tc("TC-ACC-080",
       "Sick leave accounting: filter and sort",
       "Multiple sick leaves in various states.",
       "1. Filter by salary office\n"
       "2. Filter by state (Planned/Overdue/Deleted/Ended)\n"
       "3. Sort by dates (default: descending)",
       "Salary office filter: dropdown with all offices.\n"
       "State filter: Planned, Overdue, Deleted, Ended.\n"
       "Date sort: descending by default.\n"
       "18 pages of data observed in testing.",
       "Low", "Functional",
       "REQ-sick-leave-accounting", "Sick leave accounting page"),

    tc("TC-ACC-081",
       "Sick leave accounting: download attachment",
       "Sick leave with uploaded sick note attachment.",
       "1. Find sick leave with attachment\n"
       "2. Click download action button\n"
       "3. Verify file downloads",
       "Attachment (sick note scan) downloads.\n"
       "Actions column shows: edit, download, delete buttons (2-3 depending on state).\n"
       "Download action available for all non-deleted sick leaves with attachments.",
       "Low", "Functional",
       "REQ-sick-leave-accounting", "Sick leave accounting page"),
]

# ── TS-ACC-APIErrors (API Errors, Security & Edge Cases) ─────

TS_ACC_APIERRORS = [
    tc("TC-ACC-082",
       "Stack trace leakage: invalid date format in period PATCH",
       "Valid accountant auth.",
       "1. PATCH period with {\"start\": \"not-a-date\"}\n"
       "2. PATCH period with {\"start\": \"2026-13-01\"} (invalid month)\n"
       "3. Verify response bodies",
       "BUG: Full Spring exception class and conversion details in response body.\n"
       "Should return 400 with sanitized error message.\n"
       "Security risk: exposes internal framework details.",
       "High", "Security",
       "BUG-SEC-1", "OfficePeriodController",
       "Also applies to payment date endpoint"),

    tc("TC-ACC-083",
       "Stack trace leakage: invalid payment date format",
       "Valid auth.",
       "1. GET /api/vacation/v1/paymentdates?vacationStartDate=2026-13-01&vacationEndDate=2026-06-01\n"
       "2. Verify response body",
       "BUG: Full Spring conversion exception in response.\n"
       "Should return 400 with sanitized message.",
       "High", "Security",
       "BUG-SEC-2", "VacationPaymentController",
       "Confirmed in live testing — invalid date leaks stack trace"),

    tc("TC-ACC-084",
       "Error response inconsistency: TTT vs Vacation service",
       "Various error scenarios across both services.",
       "1. Trigger 400 error in TTT service (e.g., invalid report)\n"
       "2. Trigger 400 error in Vacation service (e.g., invalid payment)\n"
       "3. Compare error response structures",
       "TTT: {errorCode, message, ...} structure.\n"
       "Vacation: different error format.\n"
       "Inconsistent error envelopes across services.\n"
       "Frontend must handle both formats.",
       "Medium", "Consistency",
       "REQ-api-standards", "Cross-service"),

    tc("TC-ACC-085",
       "BUG: status=ALL causes 500 NPE",
       "Valid accountant auth.",
       "1. GET /api/ttt/v1/reports/accounting?status=ALL\n"
       "2. Verify response",
       "BUG: HTTP 500 NullPointerException.\n"
       "Some status enum values cause NPE in query construction.\n"
       "Should either accept ALL as valid filter or return 400.",
       "High", "Bug verification",
       "BUG-API-1", "TaskReportAccountingServiceImpl",
       "Discovered in S52 live testing"),

    tc("TC-ACC-086",
       "Pagination inconsistency: v1 vs v2 endpoints",
       "Large dataset in accounting view.",
       "1. GET v1 accounting endpoint — check pagination format\n"
       "2. GET v2 equivalent — check pagination format\n"
       "3. Compare page/size/total conventions",
       "v1 and v2 use different pagination conventions.\n"
       "Inconsistent page numbering (0-based vs 1-based) or response structure.\n"
       "Frontend must handle both versions.",
       "Medium", "Consistency",
       "REQ-api-standards", "Accounting controllers"),

    tc("TC-ACC-087",
       "Accounting page: no pagination on vacation days list",
       "Many employees in office.",
       "1. GET /api/vacation/v1/vacationdays\n"
       "2. Check if pagination is supported\n"
       "3. Count returned records",
       "No pagination support on vacation days endpoint.\n"
       "Returns all employees at once.\n"
       "Performance concern for offices with many employees.\n"
       "UI: all rows loaded at once.",
       "Low", "Performance",
       "REQ-accounting-views", "VacationDaysController"),

    tc("TC-ACC-088",
       "Statistics search: per-element login validation",
       "Valid date range.",
       "1. POST /api/ttt/v1/statistics with:\n"
       "   {startDate, endDate, employeesLogins: [\"valid_login\", \"invalid_login\"]}\n"
       "2. Verify error handling",
       "Each login in employeesLogins validated individually via @EmployeeLoginExists.\n"
       "One invalid login should fail the entire request (400).\n"
       "Valid request returns statistics for specified employees.",
       "Medium", "Validation",
       "REQ-statistics", "StatisticRequestDTO"),

    tc("TC-ACC-089",
       "GET /v1/reports/accounting: 403 with valid VIEW_ALL permission",
       "User with VIEW_ALL role but no ACCOUNTANT/ADMIN role.",
       "1. Authenticate as user with VIEW_ALL only\n"
       "2. GET /api/ttt/v1/reports/accounting\n"
       "3. Verify access",
       "Should return 200 — VIEW_ALL is in VIEW permission set.\n"
       "If 403 returned despite VIEW_ALL: bug in permission check.\n"
       "Permission model: VIEW = ADMIN, VIEW_ALL, ACCOUNTANT, CHIEF_ACCOUNTANT.",
       "High", "Security",
       "REQ-accounting-permissions", "AccountingPermissionProvider",
       "Verify VIEW_ALL role actually grants access"),

    tc("TC-ACC-090",
       "Accounting search: RU↔EN keyboard layout auto-correction",
       "Search field on salary page.",
       "1. Type employee name with wrong keyboard layout\n"
       "   (e.g., 'Bdfyjd' instead of 'Иванов' in RU layout)\n"
       "2. Verify search still finds the employee",
       "SuggestionMappingUtil.correctLayout handles RU↔EN keyboard mapping.\n"
       "Both layouts searched simultaneously.\n"
       "Employee found regardless of keyboard layout error.",
       "Low", "Functional",
       "REQ-accounting-views", "TaskReportAccountingServiceImpl",
       "Same pattern used across TTT search fields"),

    tc("TC-ACC-091",
       "Payment page: month quick tabs navigation",
       "Navigate to /vacation/payment.",
       "1. Verify month tabs displayed (Jan-May 2026)\n"
       "2. Click different month tabs\n"
       "3. Verify table updates to show that month's payments",
       "Quick tabs allow fast month switching.\n"
       "Payments month picker for arbitrary month selection.\n"
       "Table filters by selected payment month.",
       "Low", "UI",
       "REQ-vacation-payment", "Payment page"),

    tc("TC-ACC-092",
       "Period UI: edit dialog with month pickers",
       "Navigate to /admin/offices as accountant.",
       "1. Click Edit on a salary office row\n"
       "2. Verify dialog shows two month pickers\n"
       "3. Change report period\n"
       "4. Change approve period\n"
       "5. Click Edit button to save",
       "Edit dialog: two month pickers for Report and Approve periods.\n"
       "Frontend validates: reportDate required, approveDate required (Yup schema).\n"
       "Gap: Frontend sends two separate dates; backend uses one 'start' field per endpoint.\n"
       "Cancel/Edit buttons.",
       "Medium", "UI",
       "REQ-period-management", "OfficeValidationSchema.js, /admin/offices"),
]


# =====================================================================
# SUITE METADATA
# =====================================================================

SUITES = [
    ("TS-ACC-Periods", "Period Management", TS_ACC_PERIODS,
     "Report/approve period CRUD, validation rules, extended periods, events, caching"),
    ("TS-ACC-Payment", "Vacation Payment", TS_ACC_PAYMENT,
     "Pay vacation, auto-payment, payment validation, day redistribution, known bugs"),
    ("TS-ACC-DayCorrection", "Day Correction & Recalculation", TS_ACC_DAYCORRECTION,
     "Manual correction, bulk recalculate, norm-based recalculation, distribution, probation"),
    ("TS-ACC-Views", "Accounting Views & Notifications", TS_ACC_VIEWS,
     "Salary page, budget notifications, correction UI, events feed, notification schedulers"),
    ("TS-ACC-SickLeave", "Sick Leave Accounting", TS_ACC_SICKLEAVE,
     "Accounting status workflow, overdue state, filters, attachments"),
    ("TS-ACC-APIErrors", "API Errors & Security", TS_ACC_APIERRORS,
     "Stack trace leakage, error consistency, permissions, search, pagination"),
]


# =====================================================================
# RISK DATA
# =====================================================================

RISKS = [
    ("Period advance cascading effects",
     "Approve period advance triggers auto-reject, norm recalculation, and RabbitMQ events. "
     "Failure in any downstream step can leave system in inconsistent state.",
     "High", "High", "Critical",
     "Test with real data in TM. Verify auto-reject + recalculation + events all fire."),
    ("VacationStatusUpdateJob 2-hour orphan window",
     "BUG-PAY-5: Entries older than 2h are permanently orphaned. "
     "6 stuck NEW_FOR_PAID entries found in Saturn office.",
     "High", "High", "Critical",
     "Monitor status_updates table. Create bug ticket for retry mechanism."),
    ("Payment type misalignment allowed",
     "BUG-PAY-1: ADMINISTRATIVE vacation can be paid as REGULAR. "
     "Incorrect accounting classification.",
     "Medium", "High", "High",
     "Test payment with mismatched type. Verify DB records."),
    ("DB/API representation inconsistency (ADMIN vacations)",
     "BUG-PAY-6: DB stores admin days in regular_days column, API transposes. "
     "Reports using DB queries will show wrong breakdown.",
     "Medium", "High", "High",
     "Compare DB and API for ADMINISTRATIVE vacations."),
    ("pastPeriodsAvailableDays drift on corrections",
     "BUG-DAYS-1: Net-zero correction cycles cause irreversible drift. "
     "Sub-component breakdown becomes incorrect.",
     "Medium", "Medium", "High",
     "Run multiple +/- corrections. Check pastPeriodsAvailableDays after."),
    ("Approve period accepts non-first-day-of-month",
     "BUG-PERIOD-1: Missing validation. Report period has it, approve does not.",
     "High", "Medium", "High",
     "PATCH approve with mid-month date. Should reject but doesn't."),
    ("NPE on null period PATCH body",
     "BUG-PERIOD-2: Null start causes 500 with stack trace leakage.",
     "Medium", "High", "High",
     "Send empty body PATCH. Should get 400, gets 500."),
    ("Double arithmetic for financial calculations",
     "BUG-DAYS-2: double used for day calculations. Floating point risk.",
     "Low", "High", "Medium",
     "Test with values near floating point boundaries."),
    ("Norm recalculation double equality check",
     "BUG-DAYS-3: difference == 0 with double. May skip or spuriously trigger.",
     "Low", "Medium", "Medium",
     "Test with very small norm differences."),
    ("Invalid office ID returns 200 with defaults",
     "BUG-PERIOD-4: Nonexistent office returns default period instead of 404.",
     "Medium", "Medium", "Medium",
     "GET period for office ID 99999. Should 404."),
    ("Extended period blocks entire office approve change",
     "Any employee with extension blocks all approve changes for the office.",
     "Medium", "Medium", "Medium",
     "Grant extension to one employee, try to advance approve period."),
    ("AUTHENTICATED_USER on period PATCH",
     "Controller allows any authenticated user, relies on service-level check. "
     "If service-level guard has a bug, all users can modify periods.",
     "Low", "High", "Medium",
     "Test period PATCH as non-accountant employee."),
    ("Payment dates accepts start > end",
     "BUG-PAY-3: No date order validation on payment dates endpoint.",
     "Medium", "Low", "Medium",
     "Send reversed dates. Should reject but doesn't."),
    ("Stack trace leakage on invalid dates",
     "BUG-SEC-1/2: Full Spring exception in response for invalid date formats.",
     "Medium", "Medium", "Medium",
     "Send invalid date formats. Check for framework details in response."),
    ("status=ALL causes 500 NPE in accounting",
     "BUG-API-1: Specific enum value triggers NPE.",
     "Medium", "Medium", "Medium",
     "GET accounting with status=ALL."),
]


# =====================================================================
# WORKBOOK GENERATION
# =====================================================================

def build_plan_overview(ws, suites_meta):
    ws.sheet_properties.tabColor = TAB_COLOR_PLAN
    ws.cell(row=1, column=1, value="Accounting Test Plan").font = FONT_TITLE
    ws.cell(row=2, column=1,
            value=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                  "Phase B Session 61 | Branch: release/2.1").font = FONT_SMALL

    # Scope
    ws.cell(row=4, column=1, value="Scope & Objectives").font = FONT_SECTION
    ws.cell(row=4, column=1).fill = FILL_SECTION
    scope_text = (
        "Comprehensive test coverage for TTT accounting operations:\n"
        "- Report/approve period management (dual period system, validation, events)\n"
        "- Vacation payment flow (APPROVED→PAID, auto-payment, write locks)\n"
        "- Vacation day correction (manual adjustment, bulk recalculation, norm-based)\n"
        "- Accounting views and notifications (salary page, budget alerts, schedulers)\n"
        "- Sick leave accounting status workflow (New→Pending→Paid/Rejected)\n"
        "- API errors, security, and edge cases (stack traces, permissions, consistency)\n\n"
        "Test data generation:\n"
        "- Period tests: use offices with known period settings on timemachine\n"
        "- Payment tests: create APPROVED vacations via API, then test payment flow\n"
        "- Day correction: use employees in AV=true and AV=false offices\n"
        "- Environment: timemachine (primary), qa-1 (secondary), stage (comparison)"
    )
    ws.cell(row=5, column=1, value=scope_text).font = FONT_BODY
    ws.cell(row=5, column=1).alignment = ALIGN_LEFT

    # Known bugs covered
    ws.cell(row=7, column=1, value="Known Bugs Covered").font = FONT_SECTION
    ws.cell(row=7, column=1).fill = FILL_SECTION
    bugs = (
        "BUG-PERIOD-1: Approve period accepts non-first-day-of-month\n"
        "BUG-PERIOD-2: NPE on null start in PATCH body\n"
        "BUG-PERIOD-3: AUTHENTICATED_USER permission on PATCH (design issue)\n"
        "BUG-PERIOD-4: Invalid office ID returns 200 with default data\n"
        "BUG-PAY-1: Payment type misalignment allowed\n"
        "BUG-PAY-2: Same error code for 5 different payment failures\n"
        "BUG-PAY-3: Payment dates accepts start > end\n"
        "BUG-PAY-4: Available paid days accepts negative newDays\n"
        "BUG-PAY-5: VacationStatusUpdateJob 2-hour orphan window (Critical)\n"
        "BUG-PAY-6: DB/API data representation inconsistency for ADMIN vacations\n"
        "BUG-DAYS-1: pastPeriodsAvailableDays drift on net-zero corrections\n"
        "BUG-DAYS-2: double arithmetic for financial day calculations\n"
        "BUG-DAYS-3: Norm recalculation double comparison (== 0) unreliable\n"
        "BUG-SEC-1: Stack trace leakage on invalid period date format\n"
        "BUG-SEC-2: Stack trace leakage on invalid payment date format\n"
        "BUG-API-1: status=ALL causes 500 NPE in accounting"
    )
    ws.cell(row=8, column=1, value=bugs).font = FONT_BODY
    ws.cell(row=8, column=1).alignment = ALIGN_LEFT

    # Suite links
    ws.cell(row=10, column=1, value="Test Suites").font = FONT_SECTION
    ws.cell(row=10, column=1).fill = FILL_SECTION
    headers = ["Suite", "Focus", "Cases", "Link"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=11, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_GREEN_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    for i, (tab_name, display_name, cases, description) in enumerate(suites_meta):
        row = 12 + i
        fill = FILL_ROW_EVEN if i % 2 == 0 else FILL_ROW_ODD
        write_row(ws, row, [tab_name, description, len(cases)], fill=fill)
        link_cell = ws.cell(row=row, column=4)
        link_cell.value = f"Go to {display_name}"
        link_cell.font = FONT_LINK_BOLD
        link_cell.hyperlink = f"#'{tab_name}'!A1"
        link_cell.border = THIN_BORDER
        if fill:
            link_cell.fill = fill

    total_row = 12 + len(suites_meta)
    total_cases = sum(len(s[2]) for s in suites_meta)
    ws.cell(row=total_row, column=1, value="TOTAL").font = FONT_SECTION
    ws.cell(row=total_row, column=3, value=total_cases).font = FONT_SECTION
    for col in range(1, 5):
        ws.cell(row=total_row, column=col).border = THIN_BORDER

    # Column widths
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 80
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 25


def build_feature_matrix(ws, suites_meta):
    ws.sheet_properties.tabColor = TAB_COLOR_PLAN
    ws.cell(row=1, column=1, value="Feature × Test Type Matrix").font = FONT_TITLE
    add_back_link(ws, row=2)

    types = ["Functional", "Validation", "Boundary", "Negative", "Bug verification",
             "Security", "Integration", "Concurrency", "UI", "Performance", "Consistency"]

    # Headers
    headers = ["Feature Area"] + types + ["Total", "Link"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    for i, (tab_name, display_name, cases, _) in enumerate(suites_meta):
        row = 5 + i
        fill = FILL_ROW_EVEN if i % 2 == 0 else FILL_ROW_ODD
        counts = {}
        for c in cases:
            t = c["type"]
            counts[t] = counts.get(t, 0) + 1

        values = [display_name] + [counts.get(t, 0) or "" for t in types] + [len(cases)]
        write_row(ws, row, values, fill=fill)

        link_cell = ws.cell(row=row, column=len(headers))
        link_cell.value = f"→ {tab_name}"
        link_cell.font = FONT_LINK
        link_cell.hyperlink = f"#'{tab_name}'!A1"
        link_cell.border = THIN_BORDER

    # Column widths
    ws.column_dimensions["A"].width = 30
    for col in range(2, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 14


def build_risk_assessment(ws, risks):
    ws.sheet_properties.tabColor = TAB_COLOR_PLAN
    ws.cell(row=1, column=1, value="Risk Assessment").font = FONT_TITLE
    add_back_link(ws, row=2)

    headers = ["Risk", "Description", "Likelihood", "Impact", "Severity", "Mitigation / Test Focus"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_HEADER
        cell.alignment = ALIGN_CENTER
        cell.border = THIN_BORDER

    severity_fills = {"Critical": FILL_RISK_HIGH, "High": FILL_RISK_HIGH,
                      "Medium": FILL_RISK_MED, "Low": FILL_RISK_LOW}

    for i, (risk, desc, likelihood, impact, severity, mitigation) in enumerate(risks):
        row = 5 + i
        fill = severity_fills.get(severity, FILL_ROW_ODD)
        write_row(ws, row, [risk, desc, likelihood, impact, severity, mitigation], fill=fill)

    add_autofilter(ws, 4, len(headers))
    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 12
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 55


def main():
    wb = openpyxl.Workbook()

    # Plan Overview
    ws_plan = wb.active
    ws_plan.title = "Plan Overview"
    build_plan_overview(ws_plan, SUITES)

    # Feature Matrix
    ws_matrix = wb.create_sheet("Feature Matrix")
    build_feature_matrix(ws_matrix, SUITES)

    # Risk Assessment
    ws_risk = wb.create_sheet("Risk Assessment")
    build_risk_assessment(ws_risk, RISKS)

    # Test Suite tabs
    total = 0
    for tab_name, display_name, cases, _ in SUITES:
        ws_ts = wb.create_sheet(tab_name)
        ws_ts.sheet_properties.tabColor = TAB_COLOR_TS
        count = write_ts_tab(ws_ts, display_name, cases)
        total += count
        print(f"  {tab_name}: {count} cases")

    output_path = "/home/v/Dev/ttt-expert-v1/expert-system/output/accounting/accounting.xlsx"
    wb.save(output_path)
    print(f"\nSaved: {output_path}")
    print(f"Total: {total} test cases across {len(SUITES)} suites")
    print(f"Tabs: Plan Overview, Feature Matrix, Risk Assessment + {len(SUITES)} TS- tabs")
    print(f"Risks: {len(RISKS)}")


if __name__ == "__main__":
    main()

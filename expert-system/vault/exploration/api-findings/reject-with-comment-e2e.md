---
type: exploration
tags:
  - confirmation
  - rejection
  - e2e
  - live-testing
  - timemachine
  - email
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[modules/ttt-report-confirmation-flow]]'
  - '[[exploration/ui-flows/confirmation-flow-live-testing]]'
  - '[[exploration/data-findings/email-templates-inventory]]'
---

# Reject with Comment — End-to-End Verification

Tested on timemachine. Report ID 3736713 (executor: imane.etteboudy, task: "Famoco - QA - ODC / Communication", date: 2026-04-03).

## Flow: REPORTED → REJECTED → REPORTED

1. **Reject**: PATCH /v1/reports/{id} with `state=REJECTED, stateComment="..."` → 200 OK
2. **DB**: `task_report.state=REJECTED`, `task_report.reject` FK points to new row in `ttt_backend.reject` table
3. **GET**: `stateComment` accessible via list endpoint (no GET-by-ID exists)
4. **Re-report**: PATCH with `state=REPORTED` → clears stateComment, approverLogin, **deletes** reject record

## Data Model: Separate `reject` Table

Rejections use `ttt_backend.reject` (id, rejector, description, created_time, executor_notified). The `task_report.reject` column is FK to this table. On re-report, the reject record is **fully deleted** — no rejection history survives.

## Key Findings

1. **API maps rejector as approver**: Response shows `approverLogin` for rejected reports, but DB `approver` column is NULL. API derives it from `reject.rejector`.

2. **No GET /v1/reports/{id}**: Returns 500 "method not supported". Must use list endpoint with filters.

3. **Reject record deletion on re-report**: Clean-slate — no audit trail of previous rejections preserved after employee re-reports. The 1,200+ reject records with `executor_notified=false` and `created_time=NULL` suggest historical data migration artifact.

4. **Email notification NOT sent (potential bug)**: Despite `executor_notified=false` and triggering `POST /v1/test/reports/notify-rejected` (200 OK), no email generated. Possible causes: timemachine clock mismatch with real `created_time`, batch aggregation requirement, or notification job date filtering. Total emails stayed at 1,014 throughout testing.

5. **Permissions inconsistency**: PATCH response after rejection shows `["EDIT","DELETE","APPROVE"]` but subsequent GET shows `["EDIT","DELETE"]` — APPROVE permission disappears in GET context.

## Connections
- [[modules/ttt-report-confirmation-flow]] — backend flow
- [[exploration/ui-flows/confirmation-flow-live-testing]] — prior UI testing
- [[exploration/data-findings/email-templates-inventory]] — APPROVE_REJECT template
- [[exploration/api-findings/report-crud-api-testing]] — report CRUD testing

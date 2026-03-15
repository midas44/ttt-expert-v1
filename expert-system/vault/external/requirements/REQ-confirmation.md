---
type: external
tags:
  - confirmation
  - requirements
  - confluence
  - over-reporting
  - notification
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-statistics]]'
  - '[[analysis/office-period-model]]'
branch: release/2.1
---
# Confirmation Requirements (Подтверждение)

Confluence page 130385094. Section for confirming employee hours by PMs. Child: "Over/under-reporting notification banner" (#2932).

## Notification Banner — Over/Under-Reporting

Non-dismissible banner on Confirmation page. Visible to: ADMIN, PM, SPM.

**Display conditions (any triggers banner):**
- Approval month = current month AND over-reporting exists today
- Approval month < current AND over-reporting existed at month end
- Approval month < current AND under-reporting existed at month end

**Configurable thresholds (Admin Panel > TTT Parameters):**
- `notification.reporting.over` = M% (default test: 10)
- `notification.reporting.under` = L% (default test: 30)

## "By Employees" Tab
- Over-report: employee reported > (norm + M%)
- Under-report: shown only when current month > approval month
- Norm uses `normForDate` (current month) or `personalNorm`/`reportingNorm` (past month per #3189)

## "By Projects" Tab
- Employee names highlighted: red = over-reporting, purple = under-reporting
- Clock icon in matching color, tooltip shows: deviation %, month, DM, projects with PM names
- Banner lists affected employees alphabetically

**Edge cases:** Same banner may show different months for different employees. Under-reporting only after period closes. Contractors/part-time may not calculate correctly.

Links: [[REQ-statistics]], [[analysis/office-period-model]], [[modules/ttt-service]], [[vacation-service-implementation]]
Figma: node 33112-18523. Tickets: #2932, #3195, #3189

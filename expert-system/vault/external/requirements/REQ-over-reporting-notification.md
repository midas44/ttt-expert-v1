---
type: external
tags:
  - requirements
  - notifications
  - reporting
  - confirmation
  - priority-2
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[office-period-model]]'
  - '[[ttt-service]]'
---
# REQ: Over-Reporting Notification Banner (#2932)

**Source**: Confluence 130385096 | **Figma**: node 33112-18523

Non-dismissible notification banners on Confirmation page for over/under-reporting.

## Visibility
ADMIN, PM, SPM roles only.

## Thresholds
From Admin > TTT Parameters:
- `notification.reporting.over` (M%, default 10%)
- `notification.reporting.under` (L%, default 30%)

## Display Triggers
1. approval_month = current AND over-reporting today
2. approval_month < current AND over-reporting at month end
3. approval_month < current AND under-reporting at month end

## By Employee Tab
- **Over-reporting**: shown if reported > norm + M%. Uses normForDate (current) or personalNorm/reportingNorm (#3189) for past months
- **Under-reporting**: only when approval_month < current month (avoids false positives)

## By Projects Tab
Employee names highlighted red (over) or purple (under) with clock icons. Summary banner above table lists all affected employees.

## References
#3189, #3195

## Related
- [[office-period-model]]
- [[roles-permissions]]
- [[ttt-service]]

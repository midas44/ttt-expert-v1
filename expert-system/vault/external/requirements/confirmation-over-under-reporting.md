---
type: external
tags:
  - confirmation
  - notification
  - over-reporting
  - under-reporting
  - requirements
  - confluence
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[modules/frontend-approve-module]]'
  - '[[modules/ttt-service]]'
  - '[[architecture/roles-permissions]]'
  - '[[exploration/ui-flows/confirmation-flow-live-testing]]'
branch: release/2.1
---
# Over/Under-Reporting Notification Banner

Confluence page ID 130385096. Bilingual spec (RU+EN), version 13. Linked ticket: GitLab #2932, Figma node 33112-18523.

## Overview
Notification banner on Confirmation page that alerts when employees report significantly more or less than their work norm. Visible to ADMIN, PM, SPM roles.

## Threshold Configuration
Configured in Admin > TTT Parameters:
- **Over-reporting**: M% = `notification.reporting.over` (test: 10%)
- **Under-reporting**: L% = `notification.reporting.under` (test: 30%)

## Banner Display Conditions

### Current Month (approval month = current month)
- Shows over-reporting ONLY (no under-reporting possible yet)
- Triggers when employee reported > (norm + M%) as of today

### Past Month (approval month < current month)
- Shows BOTH over and under-reporting
- Over: employee reported > (norm + M%) at end of approval month
- Under: employee reported < (norm - L%) at end of approval month

### Banner Behavior
- **Non-dismissible** — disappears only when approval month changes
- **"?" icon** shows tooltip with threshold values

## "By Employee" Tab Details

### Over-Reporting Banner (Section B)
Shows: approval month, over-reporting %, norm for date, actual reported hours
- Current month: uses `normForDate`
- Past months: uses `personalNorm`/`reportingNorm` (per #3189)

### Under-Reporting Banner (Section C)
Shows: approval month, under-reporting %, full-month norm, actual hours
- ONLY when current month > approval month

## "By Projects" Tab Details (Section D)

### Employee Highlighting
- **Red text + red clock icon**: over-reporting employees
- **Purple text + purple clock icon**: under-reporting employees

### Tooltip on Hover
Shows: percentage, month, DM name, projects with reports (alphabetical) with PM names

### Notification Banner Above Table
- Top row: over-reporters (alphabetical)
- Bottom row: under-reporters
- Empty rows hidden

## Edge Cases
- Mixed approval periods: on May 2, employees with April closed show May data, those with April open show April data
- Late reporters: detection delayed until hours submitted
- Contractors/part-time: acknowledged calculation limitations

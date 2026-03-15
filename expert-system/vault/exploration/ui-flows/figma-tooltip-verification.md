---
type: exploration
tags: [figma, tooltips, ui-verification, employee-reports, sick-leave, vacation, norm]
created: 2026-03-13
updated: 2026-03-13
status: active
related: ["[[figma-sprint-14-15-designs]]", "[[figma-vs-live-ui-comparison]]", "[[frontend-report-module]]", "[[sick-leave-service-implementation]]"]
branch: release/2.1
---

# Figma Tooltip Interactions Verification

Live verification of tooltip behaviors on timemachine Employee Reports page against Figma Design specs.

## Verified Tooltips

### 1. Vacation Tooltip (Design 4 — Palm Tree Icon)
**Status: MATCH**
- Employee: Alexander Smirnov, Feb 2026
- Format: "**Vacation** for the selected period **96 h:** • **96 h** (09.02.2026 – 25.02.2026, Paid)"
- Shows bold header with total hours, then bulleted list of individual entries
- Each entry: bold hours + (date range, status)
- Screenshot: `artefacts/sick-leave-tooltip-smirnov.png`

### 2. Sick Leave Tooltip — Single Entry (Design 4)
**Status: MATCH**
- Employee: Alexander Smirnov, Feb 2026 (icon class: `.icon-sick`)
- Format: "**Sick leave** for the selected period **16 h:** • **16 h** (01.02.2026 – 03.02.2026, New)"
- Same structure as vacation tooltip but with "Sick leave" header
- Screenshot: `artefacts/sick-leave-tooltip-smirnov.png`

### 3. Sick Leave Tooltip — Multi-Entry (Design 4)
**Status: MATCH**
- Employee: Andrew Laptev, Mar 2025 (4 entries in one month)
- Format header: "**Sick leave** for the selected period **95 h:**"
- 4 bullet items: 24h (01-05.03), 39h (06-12.03), 16h (13-14.03), 16h (15-18.03)
- All entries show status "New"
- Tooltip renders as scrollable list when multiple entries present
- Screenshot: `artefacts/sick-leave-tooltip-multi-entry.png`

### 4. Norm Counter Tooltip (Design 2 — Info Icon)
**Status: VERIFIED (Session 13)**
- 3-number format: reported/elapsed_norm/total_norm
- Info icon tooltip explains adjusted norm calculation
- Matches Figma "Individual norm" spec

### 5. Norm Column Info Tooltip
**Status: VERIFIED (Session 13)**
- Explains why norm is adjusted for absences
- Appears on hover over info icon in Norm column header

## Not Verified (Insufficient Test Data)
- **5+ sick leave scrollable tooltip**: Max found was 4 entries in a single month. No employee had 5+ sick leaves in one period to test scroll behavior.
- **Combined vacation + sick leave tooltip interaction**: Both icons show separate tooltips (verified both exist for Smirnov). They don't combine into a single tooltip — each icon has its own.
- **Norm tooltip with 4-number format** (Budget norm view): Requires specific page/view not accessed.

## Key Observations
1. Tooltip CSS class uses `.icon-sick` for sick leave, confirms separate icon types
2. Icon order in employee cell: sick leave icon appears BEFORE vacation icon
3. All statuses observed: "Paid" (vacation), "New" (sick leave), "Approved" (vacation from session 13)
4. Date format consistent: DD.MM.YYYY with en-dash separator
5. Hours shown as integer when whole, no decimal places for round numbers

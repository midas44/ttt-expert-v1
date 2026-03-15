---
type: exploration
tags:
  - production-calendar
  - admin
  - ui-flow
  - live-testing
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/calendar-service]]'
  - '[[exploration/api-findings/dayoff-calendar-conflict-code-analysis]]'
---
# Production Calendar Management UI

## Overview

Admin panel → Production calendars (`/admin/calendar`). Two-tab interface for managing country-specific holiday calendars and mapping them to salary offices (SOs).

## Tab 1: Setting up calendars (`/admin/calendar/0`)

### Controls
- **Year** picker (date input, e.g. 2026)
- **Calendar** dropdown — selects which country calendar to view/edit
- **Add a calendar** button — creates new calendar (name in Latin required)
- **Create a new event** button — adds holiday/event to selected calendar

### Events Table
Columns: Date (sortable ↑↓), Working hours, Reason, Actions

**Working hours options** (in Create event dialog):
- **0 hours** — full holiday (no work)
- **7 hours** — pre-holiday shortened day (предпраздничный день)
- **8 hours** — transferred working day (e.g. Saturday made a working day)

**Reason**: free text field. Displayed in Russian even when UI is in English mode. **Inline editable**: clicking the reason text converts it to a textbox for in-place editing with auto-save.

**Actions**: delete button (trash icon) — only shown for **future events**. Past events cannot be deleted through the UI.

### Russia Calendar 2026 (timemachine)
18 events: New Year (Jan 1-9), Defender of Fatherland (Feb 20), Women's Day (Mar 9), pre-holidays + Labor Day (Apr-May), Victory Day (May 11), Russia Day (Jun 12), National Unity Day (Nov 6), New Year's Eve (Dec 31). Pre-holidays have 7h, holidays have 0h.

### Create Event Dialog
- **Date*** — date picker (pre-filled with last table date)
- **Working hours*** — dropdown (0, 7, 8)
- **Reason*** — free text
- Cancel / Create buttons

### Add Calendar Dialog
- **Name*** — text input, placeholder "Please enter the calendar title in Latin"
- Cancel / Add buttons

## Tab 2: Calendars for SO (`/admin/calendar/1`)

Maps salary offices to production calendars. Table with columns: Salary office (sortable), Calendar, Actions (edit button).

### SO-Calendar Mappings (27 total on timemachine)
| Country | Count | Salary Offices |
|---------|-------|----------------|
| Russia | 15 | Altair, Andromeda, Feniks, Iupiter, Kassiopeia, Mars(Nsk), Mars(SPb), Pegas, Pluton RF, Saturn, Skorpion, Uran RF, Venera RF, + 2 more |
| Cyprus | 5 | Neptun, Pluton, Titan, Uran, Venera, Venera(Uz) |
| France | 2 | Sirius(Parizh), Venera France |
| Vietnam | 1 | GoldenStar |
| Armenia | 1 | Kallisto(Armeniia) |
| Germany | 1 | Persei |
| Georgia | 1 | Protei(Gruziia) |
| Uzbekistan | 1 | Ulugbek |
| None | 1 | Ne ukazano (no calendar!) |

### Edit SO Calendar Dialog ("Changing the calendar")
- **Salary office** — read-only display
- **Current calendar** — read-only display
- **Select a calendar** — dropdown with all 10 calendars
- Cancel / Change buttons

## Available Calendars (10 total, API-confirmed)
Armenia (id=4), Cyprus (6), Empty calendar (9), France (7), Georgia (3), Germany (2), Montenegro (8), Russia (1), Uzbekistan (10), Vietnam (5)

Note: "Montenegro" exists as calendar but no SO is mapped to it (only Titan with Cyprus).

## Findings

1. **Reason always Russian**: Holiday reasons display in Russian regardless of UI language setting — not localized
2. **"Ne ukazano" has no calendar**: One SO has no calendar assigned — could cause norm calculation issues for employees in this SO
3. **Montenegro unused**: Calendar exists but no SO is mapped to it
4. **Past event protection**: Delete button hidden for past events — good safety measure
5. **Inline edit auto-save**: Clicking reason converts to textbox; saving triggered even on no-change (misleading "Changes saved" toast)
6. **No bulk operations**: Events must be created one at a time — no import/sync from external calendar source
7. **Latin-only calendar names**: New calendars must have Latin names (enforced by placeholder hint)

## Related
- [[modules/calendar-service]] — backend service
- [[exploration/api-findings/dayoff-calendar-conflict-code-analysis]] — calendar interaction with day-offs
- [[exploration/data-findings/dayoff-calendar-conflict-live-test]] — conflict behavior
- [[database-schema]] — ttt_calendar schema

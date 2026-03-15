---
type: exploration
tags:
  - sick-leave
  - crud
  - ui-flows
  - validation
  - lifecycle
  - phase-b-prep
created: '2026-03-15'
updated: '2026-03-15'
status: active
branch: release/2.1
related:
  - '[[modules/sick-leave-service-implementation]]'
  - '[[exploration/api-findings/sick-leave-api-testing]]'
  - '[[exploration/ui-flows/sick-leave-ui-verification]]'
  - '[[analysis/sick-leave-dayoff-business-rules-reference]]'
---
# Sick Leave CRUD Lifecycle — Employee View

Full lifecycle testing via Playwright UI on timemachine (Build 2.1.26-SNAPSHOT.290209). User: Aleksei Smirnov (default session).

## Page Structure

**My Sick Leaves** (`/sick-leave/my`):
- Table columns: Sick leave dates | Calendar days | Number | Accountant | State | Actions
- Total row shows sum of calendar days
- "Add a sick note" button above table

## Create Dialog ("Adding sick note")

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Employee | Read-only link | — | Pre-filled, links to CS profile |
| Start date | Date picker (DD.MM.YYYY) | Yes (*) | Calendar picker, selecting also auto-fills End date |
| End date | Date picker (DD.MM.YYYY) | Yes (*) | Auto-set to same as Start date on first pick |
| Calendar days | Display only | — | Auto-calculated from date range |
| Number of the sick note | Text input | No | Hint: "To end your sick leave you will need the sick note number" |
| Add a scanned document | File upload | No | JPG, JPEG, PNG, PDF; max 5 files, max 5 MB each |
| Notify also | Combobox (multi-select) | No | Auto-notifies: manager, tech lead, accounting, PMs |
| Info text | — | — | "Sick pay will be paid after the sick leave is ended" |

### Validation Rules — Create
- Empty dates → "Mandatory field" under each date
- Selecting end date before start date → **start date auto-adjusts to match end date** (prevents inverted ranges at UI level)
- Number field: optional (can be saved empty)
- **Console warning**: "react-datetime: Invalid date passed" on every dialog open (minor bug)

### Post-Create Behavior
- **Success message**: "Sick leave has been successfully entered. Don't forget to end or extend your sick leave. We wish you a speedy recovery!"
- **Vacation overlap**: If sick leave dates cross existing vacation, dialog "Sick leave overlaps with vacation" appears with info about vacation pay timing and admin leave option. Triggers on every save, not just creation.
- **Status assignment**: "Started" if end date ≥ today; "Overdue" if end date < today
- **Banner**: "You have an expired sick leave. Please renew or end it" appears for Overdue sick leaves

## Table Row Actions (3 buttons for OPEN sick leave)

| Button | Test ID | Tooltip | Available When |
|--------|---------|---------|----------------|
| End sick leave | `sickleave-action-close` | End sick leave | State = Started/Overdue |
| Edit sick note | `sickleave-action-edit` | Edit sick note | Always |
| More about the sick leave | `sickleave-action-detail` | More about the sick leave | Always |

After ending: "End sick leave" button disappears, only Edit + Detail remain.

## Edit Dialog ("Editing sick note")

Same fields as Create, pre-filled with current values. All fields editable (dates, number, files, notify). Success message: "Changes have been saved".

## Detail Dialog ("More about the sick note")

Shows read-only fields:
- Employee, Accountant, **State**, **Status** (dual status model confirmed), Period, Calendar days, Number, Notify also
- **State** = employee-facing: Started → Ended
- **Status** = accounting: New (unchanged by employee actions)

**Buttons in detail view**: Delete, End sick leave (if not ended), Edit.
**Delete is ONLY accessible from detail view** — not shown in table row actions.

## End Sick Leave Dialog

- **BUG — Title says "Delete the sick note?"** but action is "End sick leave" — incorrect/misleading dialog title
- Text: "You are going to close the sick leave for the period [dates]"
- **Number field becomes REQUIRED (*)** — marked mandatory, unlike optional during creation
- Empty number → "Mandatory field" validation error
- Pre-filled if number was set earlier
- On success: State changes to "Ended", success message "Changes have been saved"

## Delete Flow

- Accessible only from Detail dialog
- Confirmation: "Delete the sick note?" → "You are going to delete the sick note for the period [dates]"
- No additional required fields
- On success: Row removed, "Changes have been saved"
- Can delete in any state (Started, Overdue, Ended)

## Status Lifecycle (employee perspective)

```
[Create] → Started (if end date ≥ today)
[Create] → Overdue (if end date < today)
[Edit extend end date] → Started (if new end date ≥ today)  
[End sick leave] → Ended
[Any state] → [Delete] (removes entirely)
```

Accounting Status stays "New" throughout — only changed by accountant.

## Bugs Found

1. **End dialog title**: "Delete the sick note?" shown for End action — should say "End the sick note?" (translation/localization bug)
2. **react-datetime console warning**: "Invalid date passed to react-datetime" fires on every dialog open (create/edit)
3. **Vacation overlap dialog re-fires**: Triggers on every save (create AND edit), not just when dates change — could be annoying for edits that don't change dates

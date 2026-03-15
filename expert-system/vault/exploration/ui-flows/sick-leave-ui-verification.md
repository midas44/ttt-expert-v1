---
type: exploration
tags:
  - sick-leave
  - ui-exploration
  - phase-b-prep
  - accounting
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[modules/sick-leave-service-implementation]]'
  - '[[modules/frontend-sick-leave-module]]'
  - '[[analysis/sick-leave-dayoff-business-rules-reference]]'
branch: release/2.1
---
# Sick Leave UI Verification (Session 29)

Live UI verification of sick leave pages across user roles on timemachine. Phase B preparation for Sick Leave lifecycle module (#2 generation priority, 0 lifecycle CRUD cases in Qase).

## My Sick Leaves Page (/sick-leave/my)

**User**: pvaynmaster (multi-role, 7 roles)

### Layout
- Title: "My sick leaves"
- **"Add a sick note"** button (blue, top-right)
- Table columns: Sick leave dates | Calendar days | Number | Accountant | State | Actions
- Total row at bottom (calendar days sum)
- Empty state: "No data" with 0 total

### Key Observations
- Button label "Add a sick note" (not "Add sick leave") — terminology difference
- No file upload control visible in table view — files are part of the create/edit modal
- No status filter visible on employee view — unlike accounting view
- 6 columns (simpler than accounting view's 10)

## Sick Leave Accounting Page (/accounting/sick-leaves)

**User**: pvaynmaster (has accountant permissions)

### Layout
- Title: "Sick leave records"
- 10 columns: Employee | Sick leave dates | Days | Work days | Sick note | Accountant | Salary office | State | Status | Actions
- **Inline status dropdown** visible on Status column — allows accounting status changes directly
- State column shows computed states (OPEN, CLOSED, OVERDUE, SCHEDULED)
- Salary office column with filter capability (27 offices per code analysis)
- State filter (7 values) and Status filter (4 values) available

### Records Visible
Multiple sick leave records spanning 2025-2026 with various states and accounting statuses. Confirms dual-status model working in production: main status (State column) + accounting status (Status column).

### Comparison: Employee vs Accounting View

| Feature | My Sick Leaves (Employee) | Sick Leave Records (Accounting) |
|---|---|---|
| Columns | 6 | 10 |
| Status filter | None | ✓ (State + Status) |
| Salary office filter | None | ✓ |
| Inline status edit | None | ✓ (accounting status dropdown) |
| Work days column | None | ✓ |
| Employee column | None (own only) | ✓ (all employees) |
| Create button | "Add a sick note" | None |
| File management | Via create/edit modal | None visible |

## Screenshots (artefacts/)

- `sick-leave-my-pvaynmaster.png` — Employee My Sick Leaves page (empty state)
- `sick-leave-accounting-pvaynmaster.png` — Accounting view with records

## Related

- [[modules/sick-leave-service-implementation]] — backend
- [[modules/frontend-sick-leave-module]] — frontend
- [[analysis/sick-leave-dayoff-business-rules-reference]] — business rules (A1-A11)
- [[exploration/ui-flows/sick-leave-accounting-workflow]] — previous accounting exploration

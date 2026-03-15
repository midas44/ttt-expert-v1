---
type: external
tags:
  - dismissal
  - employee
  - cross-system
  - requirements
  - google-doc
created: '2026-03-13'
updated: '2026-03-13'
status: active
related:
  - '[[modules/ttt-service]]'
  - '[[architecture/roles-permissions]]'
  - '[[external/requirements/google-docs-inventory]]'
---

# Employee Dismissal Process (Google Doc)

Source: docs.google.com/document/d/1gaLhuYGFgnPN3EUcQYUxtmZwnzB-pGJb0NWTdCT395Y
Cross-system: TTT + CompanyStaff (CS) + Salary Tracking Tool (STT)

## 8-Step Workflow
1. CS records dismissal date
2. Employee reports all hours through dismissal date
3. At dismissal date/12:00 → actual salary calculated from confirmed hours
4. Vacation fund = 9% of actual salary
5. Total = salary + vacation fund
6. Deduct prior payments (cards, vacations, loans, sick leave)
7. Remaining amount paid
8. Manual corrections after TTT period closure

## System Changes

### CompanyStaff
- New `being_dismissed` attribute on `/api/employee`
- Set `true` during initiation, `false` on cancellation/blocking

### TTT Backend
Three new employee attributes:
- `beingDismissed` (default: false)
- `lastDate` (default: null)
- `readOnly` (default: false)

Behaviors:
- Hourly API sync with CS
- Block unconfirmed hours and vacation requests for dismissed employees
- Admin can block/unblock via PATCH

### TTT Frontend
- Filter checkbox for dismissed employees
- Dismissal date indicator with tooltip
- Salary calculation button (enabled only when unconfirmed hours = 0)
- Confirmation popup before calculation

## Automation Scope (Phase 1)
Steps 3, 4, 5 targeted for automation. Steps 1-2 remain manual; steps 6-8 partially manual.

## Related
- [[modules/ttt-service]] — employee management
- [[architecture/roles-permissions]] — admin blocking
- [[external/requirements/google-docs-inventory]] — source catalog

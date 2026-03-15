---
type: external
tags:
  - requirements
  - confluence
  - sick-leave
  - absences
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[sick-leave-service-implementation]]'
  - '[[frontend-sick-leave-module]]'
---
# REQ: Sick Leave Requirements (Confluence)

Source: "TTT Больничные листы" (page ID 40207848, Confluence NOV space)

## Workflow Phases (as designed)
1. Employee screens + notifications (MVP)
2. Accountant page (MVP)
3. Manager page (MVP)
4. Integration with STT (Salary Tracking Tool)

## Roles and Permissions

| Role | Create | Close | View others | Special |
|------|--------|-------|-------------|---------|
| Employee | Own only | Own only | No | Via "My absences" calendar |
| PM / Manager | Own + subordinates | Own only | Subordinates | |
| HR | Same as PM | | | |
| Accountant | Same as PM | | All | Confirm payments, edit payable hours |

## Key Business Rules
- Employee MUST enter BL on the day it opens (timely notification to accounting/manager)
- BL entry required regardless of country
- BL overlapping vacation → employee chooses: extend vacation by BL days OR transfer vacation days to future
- Paid days limits: 30 days/year (240h) post-probation; 20 days/year (160h) during probation (**note: Confluence has copy-paste error — both rows say "post-probation"**)
- Payment: avg daily earnings = sum of last 2 years' salary / 730
- First 3 days: employer-paid. Day 4+: FSS (Social Insurance Fund)
- Accounting must send data to FSS within 3 days of BL opening

## Regional Availability
- All regions: view, enter, extend, close, view schedule
- RF + Montenegro only: full payment calculation and payout

## Sick Leave in Statistics
- Icons with tooltips on employee rows in statistics table
- Sick leave days reduce individual norm
- If norm=0 from sick leave + reported=0 → show 0%; if reported>0 → show N/A%

## Known Gaps in Documentation
- Dual status system (main + accounting) not documented
- No API-level permission specification (only UI-level role descriptions)
- No technical storage model description
- BL-vacation overlap choice mechanism status unclear (planned vs implemented)
- Paid days limits have copy-paste error making tier distinction unclear

## Discrepancies vs Implementation
| Confluence | Implementation |
|-----------|---------------|
| Employees create own BL, managers for subordinates | No creation permission check — any user can create for any employee |
| Single workflow status described | Dual status: main (OPEN/CLOSED/REJECTED/DELETED) + accounting (NEW/PROCESSING/PAID/REJECTED) |
| Payment calculation described | Payment not implemented in current codebase — accounting_status tracks it |

Links: [[sick-leave-service-implementation]], [[frontend-sick-leave-module]], [[REQ-vacations-master]]

---
type: external
tags: [testing, vacation, onboarding, regression, automation, google-docs]
created: 2026-03-13
updated: 2026-03-13
status: active
related: ["[[EXT-test-plan]]", "[[EXT-knowledge-transfer]]", "[[vacation-service-implementation]]", "[[architecture/roles-permissions]]"]
---

# Vacation Testing Notes (Google Doc)

Source: docs.google.com/document/d/1eiRaazUcLzO4erKHGHUJereIthAG3s-bhf06-L22GvQ

QA onboarding doc for TTT Vacations testing. Key content:

## Roles
- **Employee**: creates/edits/cancels/deletes vacation requests
- **Department Manager**: approves/rejects/redirects
- **Accountant**: pays requests, adjusts day counts

## Critical Regression Test Cases (14 total)
Cases 1-8 are automated, 9-14 manual-only (especially important):

1. Create request
2. Edit request
3. Cancel request
4. Delete request
5. Manager approve/reject
6. Accountant payment, partial payment
7. Delete cancelled/rejected request (balance must not change!)
8. Requests spanning year boundary (verify days for both years)
9. **Maternity leave enter/exit** (via CS olyunina, toggle Maternity Yes/No)
10. **Termination** (full multi-system process: CS → manager → accountant → admin → HR remove. Verify days zeroed)
11. **Employee creation** (via CS, verify day accrual, no vacation for first 6 months, CAS account needed)
12. **Reinstatement after termination** (via CS, similar to 11)
13. **New Year transition** (timemachine clock change, GitLab #832)
14. **Auto-deletion of PRELIMINARY request** (set period_type='PRELIMINARY' via DB, verify auto-delete)

## Test Users (key accounts)
| Login | ID | Role |
|---|---|---|
| perekrest | 41 | Chief accountant |
| bryz | 33 | Senior PM, Dept manager |
| ozharkova | 345 | Accountant (Piter) |
| max | 78 | Admin |
| ann | 24 | PM, Admin, Dept mgr, SPM, Observer |

## Integration Dependencies
- **CompanyStaff**: cs-dev sync every ~10 min. Office role assignments reset after CS prod sync
- **CAS**: cas-demo for all test envs. DB existence ≠ CAS account existence

## Insights for Test Generation
- Cases 9-14 are highest priority for new test documentation (manual, not automated)
- Year-boundary testing critical for vacation day calculations
- Maternity/termination/reinstatement involve cross-system workflows (TTT + CS)
- PRELIMINARY period type auto-deletion is DB-level test case

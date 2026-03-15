---
type: external
tags:
  - vacation
  - accounting
  - correction
  - requirements
  - confluence
  - advance-vacation
created: '2026-03-14'
updated: '2026-03-14'
status: active
related:
  - '[[modules/vacation-service]]'
  - '[[exploration/api-findings/vacation-day-correction-live-testing]]'
  - '[[modules/accounting-backend]]'
branch: release/2.1
---
# Vacation Day Correction Requirements

Confluence page ID 130387464. Under Accounting section. Linked ticket: GitLab #3283.

## Core Rule: advanceVacation Setting
Behavior depends on the `advanceVacation` (AV) setting of the employee's payment office (salary office):

### AV = false
- System PROHIBITS entering negative values (minus sign) in inline editing field
- Vacation days cannot go below zero

### AV = true
- Overtime/undertime affect vacation balance
- Available days CAN go negative
- System must:
  - Correctly display negative values in the table
  - Allow input of negative values during manual correction
  - Ensure correction accuracy (value matches requested; Event Feed reflects correction)

## Scenarios Causing Negative Balance (AV=true)
1. Undertime deductions
2. Vacation duration increase when user moves day-off from within vacation to outside
3. Vacation duration increase when admin deletes day-off from within vacation period
4. Vacation duration increase when admin adds working day within vacation period
5. Manual editing by accountant/admin

## Verification (Session 17)
Live testing confirmed on timemachine:
- AV=true (abpopov/Neptun): correctly accepts negative values ✓
- AV=false (abaymaganov/Venera): correctly rejects negatives with 400 error ✓
- **BUG**: pastPeriodsAvailableDays drifts after net-zero corrections
- See [[exploration/api-findings/vacation-day-correction-live-testing]]

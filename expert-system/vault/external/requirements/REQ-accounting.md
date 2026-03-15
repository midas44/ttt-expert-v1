---
type: external
tags:
  - accounting
  - requirements
  - confluence
  - vacation-correction
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-advance-vacation]]'
  - '[[REQ-accrued-vacation-days]]'
  - '[[vacation-service-implementation]]'
branch: release/2.1
---
# Accounting Requirements (Бухгалтерия)

Confluence page 130387462. Container page with one child: "Correction of vacation days" (#3283).

## Vacation Day Correction (Корректировка отпускных дней)

Behavior depends on `advanceVacation` office setting:

**advanceVacation = false (Russia):**
- MUST prohibit minus sign input in inline-editing field
- Negative balances never allowed

**advanceVacation = true (Cyprus/Germany):**
- Allow negative values in correction field
- Display negative values correctly in table
- Corrected value must equal requested value exactly
- Event Feed (Лента) must show correct correction value

## Scenarios Causing Negative Available Days (AV=true only)
1. Undertime accounting (учет недоработок)
2. Day-off moved from within vacation to outside it
3. Admin deletes day-off from within vacation period
4. Admin adds working Saturday/Sunday within vacation period
5. Manual editing of annual balance by accountant/admin

Links: [[REQ-advance-vacation]], [[REQ-accrued-vacation-days]], [[REQ-vacation-day-corrections]], [[vacation-service-implementation]], [[analysis/absence-data-model]]

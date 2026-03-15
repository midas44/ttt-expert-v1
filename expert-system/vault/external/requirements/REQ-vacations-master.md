---
type: external
tags:
  - vacation
  - requirements
  - confluence
  - advance-vacation
  - accrued-days
  - master-spec
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-accrued-vacation-days]]'
  - '[[REQ-advance-vacation]]'
  - '[[REQ-vacation-calendar-interaction]]'
  - '[[vacation-service-implementation]]'
branch: release/2.1
---
# Vacations Master Requirements (Отпуск)

Confluence page 130385085, version 31 (most iterated). Two children: #3014 (Accrued Days) and #3092 (Advance Vacation).

## Core Concept: Two Modes via `advanceVacation`

**advanceVacation = false (Russia):** No advance, no overtime/undertime accounting. Only accrued days available.
**advanceVacation = true (Cyprus/Germany):** Advance allowed, overtime AND undertime both counted.

## Feature Comparison (key differences)

| Feature | AV=false | AV=true |
|---------|----------|---------|
| Available days | Monthly accrual formula | Full year available immediately |
| Negative balance | Never (display 0 if < 0) | Allowed for current year |
| Overtime/undertime | N/A | Adjusts balance at month close |
| FIFO validation | #3067 | #3092-B-12 (same logic) |
| Insufficient days → | Convert to administrative | Deduct from earliest year, can go negative |
| Year-end negative | N/A | Rolls into next year's balance |
| Manual correction | Cannot go negative (#3283) | Can go negative (#3283) |

## #3014 — Accrued Days Form (AV=false)
- Removed: employee name, remaining days, request type, vacation type fields
- Preliminary requests eliminated entirely (#3053 migration)
- Payment month range: 2 months before start through end month
- **Accrued days formula:** X = (month_number × annual_norm/12) + year_remainder + prior_years − annual_norm + future_request_days + edited_days
- If Y > X: red error, blocks submission, suggests "Reduce duration or select unpaid"
- Orange warning for future request impact (#3015)

## #3092 — Advance Form (AV=true)
- "Available vacation days" with year label, max 3 decimal places, can be negative
- Year-by-year tooltip (current + next year; previous if balances exist)
- Day consumption: FIFO (earliest first)
- Undertime deducts from earliest year; if all exhausted, current goes negative
- No accrued days calculation display
- FIFO enforcement: #3347 (sprint 15) for cross-year validation

## Documented Bugs (QA1 experiments)
1. Day-off deletion: both requests become admin (should only affect later one)
2. Negative correction for AV=false: UI accepted but no effect
3. Insufficient accrued days after manual reduction: requests not affected (silent over-consumption)

Links: [[REQ-accrued-vacation-days]], [[REQ-advance-vacation]], [[REQ-vacation-calendar-interaction]], [[vacation-service-implementation]], [[vacation-day-calculation]], [[analysis/absence-data-model]]
Tickets: #3092, #3014, #3067, #3049, #3015, #3053, #3283, #2736, #3204, #3281, #3301, #3157, #3347

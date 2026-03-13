---
type: external
tags:
  - requirements
  - vacation
  - advance-vacation
  - FIFO
  - priority-1
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-accrued-vacation-days]]'
  - '[[vacation-service]]'
---
# REQ: Advance Vacation (#3092)

**Source**: Confluence 130385089 | **Figma**: node 38600-296992

Covers behavior when `advanceVacation=true`. Initially for Neptune RC (Cyprus) and Perseus RC (Germany).

## Core Rule
Employees can use ALL remaining days from prior years PLUS ALL current year days. FIFO consumption — older days used first.

## Available Days Display
Balance = current_year_remaining + prior_years. May be fractional (max 3 decimals). May be negative for current year only.

Info tooltip shows year-by-year breakdown (always current + next year; prior years if balances exist). Prior year balances CANNOT be negative. Negative current-year balance at year-end carries into new year.

## Overwork/Underwork Rules (#3204)
- Overwork in month X of year Y adds to year Y balance
- Underwork deducts from earliest year first up to current year
- Can produce negative current-year balance

## Form Differences from #3014
- "X of Y" payment availability notice is EXCLUDED entirely
- Simpler error 11.4 "Insufficient vacation days" replaces it

## FIFO Enforcement (#3067, #3347)
When creating current-year request while future-year request exists consuming current/prior days:
1. Validates enough current+prior days for new request
2. Validates enough future-year days for all future-year requests
3. If both pass, reallocates days FIFO

Sprint 14: simpler logic (0 = blocked). Sprint 15 (#3347): smart reallocation without converting to administrative.

## Key Config Toggle
`advanceVacation` per Payment Office in CompanyStaff — drives fundamentally different vacation calculation modes.

## References
#3067, #3157, #3204, #3303, #3347

## Related
- [[REQ-accrued-vacation-days]]
- [[REQ-vacation-day-corrections]]
- [[vacation-service]]

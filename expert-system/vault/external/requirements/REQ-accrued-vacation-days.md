---
type: external
tags:
  - requirements
  - vacation
  - accrued-days
  - priority-1
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-advance-vacation]]'
  - '[[vacation-service]]'
---
# REQ: Using Only Accrued Vacation Days (#3014)

**Source**: Confluence 130385087 | **Figma**: node 33810-213656

Covers vacation request form when `advanceVacation=false` (default for most offices).

## Core Rule
Advance vacation NOT permitted. Overtime/undertime do NOT affect vacation balance.

## Vacation Period Dates
- Available from today; regular requests blocked before employment_date + 3 months (#2558)
- Auto-populate paired date; min 1 day
- Date changes generate "Vacation period modified" events and reset OptionalApprover decisions
- Confirmed requests show non-blocking orange warning about status reset to "New" (#2197)

## Payment Month
- Defaults to start month; range: 2 months before start through end month
- Months in closed reporting periods disabled
- Auto-switches to end month if insufficient days in start month (#3015)

## Unpaid/Administrative Checkbox
- Toggles between Regular and Administrative vacation type
- Disables payment month when on
- State changes generate "Vacation type changed" events

## Available Days Calculation ("X of Y")
Complex formula:
```
X = (month_ordinal * annual_norm/12) + year_remainder + prior_years_remainder
    - annual_norm + days_in_later_requests + days_in_same_month_later_requests
```
For edits: adds back current request's saved days.
- Red error when Y > X blocks submission
- Orange warning about future requests becoming unpaid (#3015)
- Negative X displayed as 0

## References
#2197, #2252, #2306, #2558, #3014, #3015, #3053

## Related
- [[REQ-advance-vacation]]
- [[REQ-vacation-day-corrections]]
- [[vacation-service]]
- [[absence-data-model]]

---
type: external
tags:
  - requirements
  - vacation
  - corrections
  - priority-1
created: '2026-03-12'
updated: '2026-03-12'
status: active
related:
  - '[[REQ-advance-vacation]]'
---
# REQ: Correction of Vacation Days (#3283)

**Source**: Confluence 130387464

## Rules by Mode
- **advanceVacation=false**: PROHIBIT minus sign in inline editing field
- **advanceVacation=true**: ALLOW negative values

## Causes of Negative Days
- Underwork
- Day-off moves/deletions extending vacation
- Admin adding working days in vacation period
- Manual accountant/admin edits

Manual corrections must accept negative input, set value exactly as requested, reflect correctly in Event Feed.

## Related
- [[REQ-advance-vacation]]
- [[REQ-accrued-vacation-days]]
- [[vacation-service]]
